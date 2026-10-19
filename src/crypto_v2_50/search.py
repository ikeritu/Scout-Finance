"""The crypto search as one pure function (v2.50F): universe -> exclusions -> gates -> pre-selection -> daily series -> score.

No Streamlit here, so the whole flow can be tested with a scripted transport. The interface only draws what this returns.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .cache import ProtectedCache
from .coingecko import (BudgetExhausted, CoinGeckoClient, CoinGeckoError, RateLimited, apply_exclusions, fetch_fresh_prices, load_daily_series,
                        load_exclusion_sets, load_universe)
from .scoring import (TIER_HIGH, TIER_LOW, TIER_MEDIUM, TIER_NO_DATA, TIER_NO_LIQUIDITY, TIER_WATCH, passes_gates, preselect, score_row, summarize)
from .derivatives import DerivativesError, fetch_perpetuals, match_perpetual
from .signals import daily_signals

DETAIL_LIMIT = 200  # today 155 coins can still reach the lowest tier (v2.50E); the limit leaves room for a livelier market
TIER_ORDER = {TIER_HIGH: 0, TIER_MEDIUM: 1, TIER_LOW: 2, TIER_WATCH: 3, TIER_NO_LIQUIDITY: 4, TIER_NO_DATA: 5}
CANDIDATE_TIERS = (TIER_HIGH, TIER_MEDIUM, TIER_LOW)

Progress = Callable[[int, int, str], None]


@dataclass
class SearchResult:
    scored: list[dict]
    summary: dict


def sort_key(item: dict) -> tuple:
    return (TIER_ORDER.get(item["tier"], 9), -int(item["score"]), -(item.get("turnover_24h") or 0.0), str(item["coin_id"]))


def run_search(client: CoinGeckoClient, cache: ProtectedCache, *, detail_limit: int = DETAIL_LIMIT, refresh: bool = False,
               progress: Progress | None = None, perps_transport=None) -> SearchResult:
    """Raises CoinGeckoError (missing key, budget, rate limit, ...) only when there is no universe to show. Trouble loading the daily
    series of some coins is tolerated and reported: those coins are scored without it, so their missing signals cap them."""
    calls_before = client.usage.calls_this_month()
    if progress:
        progress(0, 1, "lista de monedas")
    universe = load_universe(client, cache, refresh=refresh)
    exclusions = load_exclusion_sets(client, cache, refresh=refresh)
    kept, excluded = apply_exclusions(universe.data, exclusions.data)
    gated = [row for row in kept if passes_gates(row)]
    pool = preselect(kept, detail_limit)

    details: dict[str, dict] = {}
    failed = skipped = 0
    stopped = None
    for index, row in enumerate(pool, start=1):
        if progress:
            progress(index, len(pool), row["symbol"])
        if stopped:
            skipped += 1
            continue
        try:
            series = load_daily_series(client, cache, row["coin_id"], refresh=refresh)
        except BudgetExhausted:
            stopped, skipped = "budget", skipped + 1
            continue
        except RateLimited:
            stopped, skipped = "rate_limited", skipped + 1
            continue
        except CoinGeckoError:
            failed += 1
            continue
        details[row["coin_id"]] = daily_signals(row, series.data)

    perps_status, perps = "ok", {}
    try:  # one public call for every perpetual; trouble here never stops the search, it only leaves the derivatives out
        perps = fetch_perpetuals(perps_transport)
    except DerivativesError:
        perps_status = "unavailable"
    fresh: dict[str, float] = {}
    if perps:  # the identity check compares live prices: the cached market data may be hours old
        candidates = [row["coin_id"] for row in kept if str(row["symbol"]).upper() in perps]
        try:
            fresh = fetch_fresh_prices(client, candidates)
        except CoinGeckoError:
            perps_status = "unverified"  # no fresh prices (budget, rate limit, error): no link is made rather than a link on a stale price
    links = {row["coin_id"]: (match_perpetual(row, perps, price=fresh.get(row["coin_id"])) if perps_status == "ok" and row["coin_id"] in fresh else
                              (None, bool(perps) and str(row["symbol"]).upper() in perps)) for row in kept}
    scored = sorted((row | details.get(row["coin_id"], {}) | {"has_series": row["coin_id"] in details} | {"perp": links[row["coin_id"]][0], "perp_conflict": links[row["coin_id"]][1]}
                     | score_row(row, details.get(row["coin_id"])) for row in kept),
                    key=sort_key)  # the series-based signals and the verified perpetual travel with the coin so its page can show them
    counts = summarize(scored)
    excluded_by: dict[str, int] = {}
    for row in excluded:
        for category in row["excluded_by"]:
            excluded_by[category] = excluded_by.get(category, 0) + 1
    summary = {
        "universe": len(universe.data), "excluded": len(excluded), "excluded_by": excluded_by, "kept": len(kept), "gated": len(gated),
        "preselected": len(pool), "detail_loaded": len(details), "detail_failed": failed, "detail_skipped": skipped, "stopped": stopped,
        "tiers": counts, "candidates": sum(counts.get(t, 0) for t in CANDIDATE_TIERS), "fetched_at": universe.fetched_at.isoformat(),
        "from_cache": bool(universe.from_cache), "calls_used": client.usage.calls_this_month() - calls_before, "usage": client.usage.status(),
        "perps_status": perps_status, "with_perp": sum(1 for perp, _ in links.values() if perp), "perp_conflicts": sum(1 for _, conflict in links.values() if conflict),
    }
    return SearchResult(scored, summary)


def filter_results(scored: list[dict], needle: str = "", level: str = "scored") -> list[dict]:
    """`level`: scored (every coin that passed the gates) | candidates | watch | no_liquidity | all. The text matches name, symbol or id."""
    text = (needle or "").strip().casefold()
    allowed = {
        "scored": (TIER_HIGH, TIER_MEDIUM, TIER_LOW, TIER_WATCH), "candidates": CANDIDATE_TIERS, "watch": (TIER_WATCH,),
        "no_liquidity": (TIER_NO_LIQUIDITY, TIER_NO_DATA), "all": tuple(TIER_ORDER),
    }[level]
    rows = [r for r in scored if r["tier"] in allowed]
    if text:
        rows = [r for r in rows if text in str(r.get("name", "")).casefold() or text in str(r.get("symbol", "")).casefold() or text in str(r.get("coin_id", "")).casefold()]
    return rows


def paginate(rows: list, page: int, per_page: int) -> tuple[list, int, int]:
    """(the page's rows, the page actually shown, the number of pages): an out-of-range page is clamped, never an error."""
    per_page = max(1, per_page)
    pages = max(1, -(-len(rows) // per_page))
    page = min(max(1, page), pages)
    start = (page - 1) * per_page
    return rows[start:start + per_page], page, pages
