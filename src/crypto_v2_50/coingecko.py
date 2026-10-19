"""CoinGecko Demo data layer (v2.50C): client, budget, normalisation and cached loaders. No Streamlit, no scoring.

What v2.50B established and this module enforces:
  * the Demo key goes in the `x-cg-demo-api-key` header (never in the URL) and is read from SCOUT_FINANCE_COINGECKO_API_KEY; it is
    never printed, logged, stored or put in an exception message;
  * the quota cannot be read from the API, so every request is counted (errors included) against a safety cap;
  * 100 calls a minute at most: calls are spaced out and a 429 is retried a bounded number of times;
  * history on the Demo plan is limited to one year; `days` above 90 returns daily points (2-90 gives hourly ones);
  * the last point of a daily series is the day in progress and is dropped, so a partial day never looks like a full one;
  * a field the API does not give stays None; nothing is invented or filled in;
  * raw data is cached for 24 hours at most, encrypted (see cache.py).
"""
from __future__ import annotations

import json
import math
import os
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlencode

from .cache import ProtectedCache
from .usage import UsageCounter

BASE_URL = "https://api.coingecko.com/api/v3"
KEY_ENV = "SCOUT_FINANCE_COINGECKO_API_KEY"
KEY_HEADER = "x-cg-demo-api-key"
ATTRIBUTION_TEXT = "Powered by CoinGecko"  # the API terms require it to be shown prominently (not smaller than size 10)
ATTRIBUTION_URL = "https://www.coingecko.com/"
PER_PAGE = 250
UNIVERSE_PAGES = 8  # about 2,000 coins
DAILY_DAYS = 365  # more than 90 days returns daily points; 365 is the Demo plan's history limit and the same one call as a shorter range (v2.50I: age)
MAX_DEMO_DAYS = 365
EXCLUSION_CATEGORIES = ("stablecoins", "wrapped-tokens", "liquid-staking")
EXCLUSION_MAX_PAGES = 4
MIN_INTERVAL_SECONDS = 0.65  # about 90 calls a minute, under the plan's 100
MAX_RETRY_AFTER_SECONDS = 60.0

Transport = Callable[[str, dict, float], tuple[int, dict, bytes]]


class CoinGeckoError(Exception):
    """Safe by construction: it carries a status and a CoinGecko error code, never a URL with a key, a header or a response body."""

    def __init__(self, message: str, status: int | None = None, code: int | None = None) -> None:
        super().__init__(message)
        self.status, self.code = status, code


class MissingApiKey(CoinGeckoError):
    pass


class BudgetExhausted(CoinGeckoError):
    pass


class RateLimited(CoinGeckoError):
    pass


class ProOnly(CoinGeckoError):
    pass


class RangeNotAllowed(CoinGeckoError):
    pass


def read_api_key(environ: dict | None = None) -> str | None:
    value = (environ if environ is not None else os.environ).get(KEY_ENV, "")
    value = value.strip() if isinstance(value, str) else ""
    return value or None


def default_transport(url: str, headers: dict, timeout: float) -> tuple[int, dict, bytes]:
    import certifi

    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()


def _error_code(body: bytes) -> int | None:
    try:
        data = json.loads(body)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    status = data.get("status")
    if not isinstance(status, dict):
        error = data.get("error")
        status = error.get("status") if isinstance(error, dict) else None
    code = status.get("error_code") if isinstance(status, dict) else None
    return code if isinstance(code, int) and not isinstance(code, bool) else None


class CoinGeckoClient:
    def __init__(self, api_key: str | None = None, *, usage: UsageCounter, transport: Transport | None = None,
                 sleep: Callable[[float], None] = time.sleep, monotonic: Callable[[], float] = time.monotonic,
                 min_interval: float = MIN_INTERVAL_SECONDS, max_retries: int = 2, timeout: float = 40.0) -> None:
        key = api_key.strip() if isinstance(api_key, str) else read_api_key()
        if not key:
            raise MissingApiKey(f"No CoinGecko API key: set the user environment variable {KEY_ENV}.")
        self._key = key
        self.usage = usage
        self._transport = transport or default_transport
        self._sleep, self._monotonic = sleep, monotonic
        self._min_interval, self._max_retries, self._timeout = min_interval, max_retries, timeout
        self._last_call: float | None = None

    def __repr__(self) -> str:
        return "CoinGeckoClient(key=<hidden>)"

    def require_budget(self, calls: int) -> None:
        """Refuse before starting anything that could not finish inside the cap."""
        if not self.usage.can_afford(calls):
            status = self.usage.status()
            raise BudgetExhausted(f"Not enough call budget: this needs about {calls} calls and {status['remaining']} remain of the {status['cap']} safety cap for {status['month']}.")

    def _pace(self) -> None:
        if self._last_call is not None:
            wait = self._min_interval - (self._monotonic() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._monotonic()

    def get_json(self, path: str, params: dict | None = None) -> Any:
        url = BASE_URL + path + (("?" + urlencode(sorted((params or {}).items()))) if params else "")
        headers = {KEY_HEADER: self._key, "accept": "application/json", "User-Agent": "scout-finance-local"}
        for attempt in range(self._max_retries + 1):
            self.require_budget(1)
            self._pace()
            self.usage.record(1)  # counted before it is sent: an error or a timeout still spends quota
            try:
                status, response_headers, body = self._transport(url, headers, self._timeout)
            except Exception as error:  # the message could contain the request; keep only the type
                raise CoinGeckoError(f"Network error ({type(error).__name__}).") from None
            if status == 200:
                try:
                    return json.loads(body)
                except ValueError:
                    raise CoinGeckoError("CoinGecko returned a response that is not JSON.", status) from None
            code = _error_code(body)
            retry_after = next((v for k, v in response_headers.items() if k.lower() == "retry-after"), None)
            if status == 429 or status >= 500:
                if attempt < self._max_retries:
                    try:
                        delay = min(MAX_RETRY_AFTER_SECONDS, float(retry_after)) if retry_after is not None else 5.0 * (2 ** attempt)
                    except ValueError:
                        delay = 5.0 * (2 ** attempt)
                    self._sleep(max(0.0, delay))
                    continue
                if status == 429:
                    raise RateLimited("CoinGecko rate limit reached (HTTP 429).", status, code)
                raise CoinGeckoError(f"CoinGecko server error (HTTP {status}).", status, code)
            if code == 10005:
                raise ProOnly("This CoinGecko endpoint is limited to paid plans (code 10005).", status, code)
            if code == 10012:
                raise RangeNotAllowed("The requested time range is not allowed on the Demo plan (code 10012); it allows 365 days.", status, code)
            if status in (401, 403):
                raise CoinGeckoError(f"CoinGecko rejected the request (HTTP {status}, code {code}); check the API key.", status, code)
            raise CoinGeckoError(f"CoinGecko request failed (HTTP {status}, code {code}).", status, code)
        raise CoinGeckoError("CoinGecko request failed.")  # unreachable: the loop always returns or raises


# ---------------------------------------------------------------------------------------------------------------- normalisation

def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def normalize_market_row(raw: Any) -> dict | None:
    """One `/coins/markets` row in the app's field names, or None when it lacks an identity. Missing numbers stay None."""
    if not isinstance(raw, dict):
        return None
    coin_id, symbol = raw.get("id"), raw.get("symbol")
    if not isinstance(coin_id, str) or not coin_id.strip() or not isinstance(symbol, str) or not symbol.strip():
        return None
    market_cap, volume = _number(raw.get("market_cap")), _number(raw.get("total_volume"))
    rank = _number(raw.get("market_cap_rank"))
    return {
        "coin_id": coin_id.strip(),
        "symbol": symbol.strip().upper(),
        "name": str(raw.get("name") or "").strip(),
        "market_cap_rank": int(rank) if rank is not None else None,
        "price_usd": _number(raw.get("current_price")),
        "market_cap_usd": market_cap if market_cap and market_cap > 0 else None,
        "fdv_usd": _number(raw.get("fully_diluted_valuation")),
        "volume_24h_usd": volume if volume is not None and volume >= 0 else None,
        "circulating_supply": _number(raw.get("circulating_supply")),
        "total_supply": _number(raw.get("total_supply")),
        "max_supply": _number(raw.get("max_supply")),
        "change_24h_pct": _number(raw.get("price_change_percentage_24h_in_currency", raw.get("price_change_percentage_24h"))),
        "change_7d_pct": _number(raw.get("price_change_percentage_7d_in_currency")),
        "change_14d_pct": _number(raw.get("price_change_percentage_14d_in_currency")),
        "change_30d_pct": _number(raw.get("price_change_percentage_30d_in_currency")),
        "last_updated": raw.get("last_updated") if isinstance(raw.get("last_updated"), str) else None,
        "turnover_24h": (volume / market_cap) if (volume is not None and volume >= 0 and market_cap and market_cap > 0) else None,
    }


def normalize_market_chart(payload: Any, now: datetime) -> list[dict]:
    """Daily points [{date, price_usd, market_cap_usd, volume_usd}] from `market_chart`. The point of the day in progress is
    dropped (it carries a partial volume). Malformed or mismatched series raise CoinGeckoError instead of being guessed."""
    if not isinstance(payload, dict) or not all(isinstance(payload.get(k), list) for k in ("prices", "market_caps", "total_volumes")):
        raise CoinGeckoError("market_chart response has an unexpected shape.")
    today = now.astimezone(timezone.utc).date()
    by_day: dict = {}
    for field, key in (("price_usd", "prices"), ("market_cap_usd", "market_caps"), ("volume_usd", "total_volumes")):
        for point in payload[key]:
            if not (isinstance(point, (list, tuple)) and len(point) == 2):
                raise CoinGeckoError("market_chart contains a malformed point.")
            stamp, value = _number(point[0]), _number(point[1])
            if stamp is None:
                raise CoinGeckoError("market_chart contains a point without a timestamp.")
            day = datetime.fromtimestamp(stamp / 1000, tz=timezone.utc).date()
            if day >= today:
                continue  # the day in progress (and anything in the future) is not a completed day
            by_day.setdefault(day, {})[field] = value  # a later point of the same day replaces an earlier one
    series = [{"date": day.isoformat(), "price_usd": v.get("price_usd"), "market_cap_usd": v.get("market_cap_usd"), "volume_usd": v.get("volume_usd")}
              for day, v in sorted(by_day.items())]
    return series


# -------------------------------------------------------------------------------------------------------------------- fetchers

@dataclass
class Loaded:
    data: Any
    fetched_at: datetime
    from_cache: bool


def fetch_markets_page(client: CoinGeckoClient, page: int, *, category: str | None = None) -> tuple[list[dict], int]:
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": PER_PAGE, "page": page, "price_change_percentage": "24h,7d,14d,30d"}
    if category:
        params["category"] = category
    raw = client.get_json("/coins/markets", params)
    if not isinstance(raw, list):
        raise CoinGeckoError("/coins/markets response has an unexpected shape.")
    rows = [row for row in (normalize_market_row(item) for item in raw) if row is not None]
    return rows, len(raw)


def fetch_universe(client: CoinGeckoClient, max_pages: int = UNIVERSE_PAGES) -> list[dict]:
    client.require_budget(max_pages)
    seen: set[str] = set()
    universe: list[dict] = []
    for page in range(1, max_pages + 1):
        rows, raw_count = fetch_markets_page(client, page)
        for row in rows:
            if row["coin_id"] not in seen:
                seen.add(row["coin_id"])
                universe.append(row)
        if raw_count < PER_PAGE:
            break
    return universe


def fetch_category_ids(client: CoinGeckoClient, category: str, max_pages: int = EXCLUSION_MAX_PAGES) -> list[str]:
    ids: list[str] = []
    for page in range(1, max_pages + 1):
        rows, raw_count = fetch_markets_page(client, page, category=category)
        ids.extend(row["coin_id"] for row in rows)
        if raw_count < PER_PAGE:
            break
    return sorted(set(ids))


def fetch_exclusion_sets(client: CoinGeckoClient, categories: tuple[str, ...] = EXCLUSION_CATEGORIES) -> dict[str, list[str]]:
    client.require_budget(len(categories) * EXCLUSION_MAX_PAGES)
    return {category: fetch_category_ids(client, category) for category in categories}


def fetch_daily_series(client: CoinGeckoClient, coin_id: str, days: int = DAILY_DAYS, now: datetime | None = None) -> list[dict]:
    if not (91 <= days <= MAX_DEMO_DAYS):
        raise CoinGeckoError(f"days must be between 91 (daily points) and {MAX_DEMO_DAYS} (the Demo plan's limit).")
    payload = client.get_json(f"/coins/{coin_id}/market_chart", {"vs_currency": "usd", "days": days})
    return normalize_market_chart(payload, now or datetime.now(timezone.utc))


SIMPLE_PRICE_CHUNK = 100


def fetch_fresh_prices(client: CoinGeckoClient, coin_ids: list[str]) -> dict[str, float]:
    """Current USD prices (not cached) for the given coin ids, `SIMPLE_PRICE_CHUNK` per call. A coin CoinGecko does not answer for is absent,
    never filled in. The budget for all the chunks is checked before the first call."""
    ids = sorted(set(coin_ids))
    chunks = [ids[i:i + SIMPLE_PRICE_CHUNK] for i in range(0, len(ids), SIMPLE_PRICE_CHUNK)]
    client.require_budget(len(chunks))
    prices: dict[str, float] = {}
    for chunk in chunks:
        raw = client.get_json("/simple/price", {"ids": ",".join(chunk), "vs_currencies": "usd"})
        if not isinstance(raw, dict):
            raise CoinGeckoError("/simple/price response has an unexpected shape.")
        for coin_id, entry in raw.items():
            price = _number(entry.get("usd")) if isinstance(entry, dict) else None
            if price is not None and price > 0:
                prices[coin_id] = price
    return prices


def apply_exclusions(rows: list[dict], exclusion_sets: dict[str, list[str]]) -> tuple[list[dict], list[dict]]:
    """(kept, excluded). Every excluded coin carries the categories that excluded it; nothing is dropped silently."""
    reasons: dict[str, list[str]] = {}
    for category, ids in exclusion_sets.items():
        for coin_id in ids:
            reasons.setdefault(coin_id, []).append(category)
    kept, excluded = [], []
    for row in rows:
        if row["coin_id"] in reasons:
            excluded.append(row | {"excluded_by": sorted(reasons[row["coin_id"]])})
        else:
            kept.append(row)
    return kept, excluded


def estimate_search_calls(universe_pages: int = UNIVERSE_PAGES, detail_coins: int = 100, exclusion_cached: bool = True) -> int:
    """Calls a full search needs: the universe pages, the exclusion pages when they are not cached, and one chart per candidate."""
    return universe_pages + (0 if exclusion_cached else len(EXCLUSION_CATEGORIES) * EXCLUSION_MAX_PAGES) + detail_coins


# ------------------------------------------------------------------------------------------------------------------------ cache

def _cached(cache: ProtectedCache, name: str, load: Callable[[], Any], clock: Callable[[], datetime], refresh: bool) -> Loaded:
    if not refresh:
        hit = cache.get(name)
        if hit is not None:
            return Loaded(hit[0], hit[1], True)
    data = load()
    cache.put(name, data)
    return Loaded(data, clock(), False)


def load_universe(client: CoinGeckoClient, cache: ProtectedCache, *, refresh: bool = False, max_pages: int = UNIVERSE_PAGES) -> Loaded:
    return _cached(cache, f"universe-{max_pages}", lambda: fetch_universe(client, max_pages), cache.clock, refresh)


def load_exclusion_sets(client: CoinGeckoClient, cache: ProtectedCache, *, refresh: bool = False) -> Loaded:
    return _cached(cache, "exclusions", lambda: fetch_exclusion_sets(client), cache.clock, refresh)


def load_daily_series(client: CoinGeckoClient, cache: ProtectedCache, coin_id: str, *, days: int = DAILY_DAYS, refresh: bool = False) -> Loaded:
    return _cached(cache, f"daily-{coin_id}-{days}", lambda: fetch_daily_series(client, coin_id, days, cache.clock()), cache.clock, refresh)
