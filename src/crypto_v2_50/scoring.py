"""Crypto explosive score v1 (v2.50E). Pure functions: no network, no cache, no Streamlit.

The thresholds are the ones the user approved on 2026-10-19 after the descriptive study of v2.50D. They are hypotheses chosen to be
selective over the real universe, not results about the future: the score is a local research heuristic, it does not predict returns
and it is not a recommendation.

Layers, as in the stock screen: gates (no points) -> points per signal -> caps for missing data and for risk -> tier.
"""
from __future__ import annotations

from typing import Any, Mapping

from .signals import finite

# Gates: below them a coin is not scored (it is listed as "no liquidity", counted, never hidden).
MIN_MARKET_CAP_USD = 5_000_000
MIN_VOLUME_24H_USD = 500_000

# (strong threshold, strong points, partial threshold, partial points)
TURNOVER = (0.25, 20, 0.10, 10)
REL_VOLUME = (3.0, 22, 2.0, 12)
MOMENTUM_30D = (60.0, 16, 25.0, 8)
MOMENTUM_7D = (30.0, 12, 15.0, 6)
BREAKOUT_POINTS = 14
BREAKOUT_MIN_REL_VOLUME = 2.0
SMALL_CAP_USD = 100_000_000
SMALL_CAP_POINTS = 6
MAX_SCORE = 90  # 20 + 22 + 16 + 12 + 14 + 6

SUSPICIOUS_TURNOVER = 1.0  # a day's volume at or above the market cap
DILUTION_CIRCULATING_RATIO = 0.3  # circulating / total supply below this
DILUTION_FDV_RATIO = 3.0  # FDV / market cap at or above this

YOUNG_FLAG_DAYS = 90  # fewer days of history than this: "moneda reciente" (a tag)
YOUNG_CAP_DAYS = 30  # fewer than this: capped as well (implied already by the missing 30-day volume baseline, but stated)
CAP_YOUNG = 44
CAP_MISSING = 44
CAP_SUSPICIOUS = 44
CAP_DILUTION = 69
CAP_FEWER_THAN_3 = 59
CAP_EXACTLY_3 = 74
CAP_4_WITHOUT_BREAKOUT = 84

TIER_HIGH, TIER_MEDIUM, TIER_LOW = "CRYPTO_CANDIDATE_HIGH", "CRYPTO_CANDIDATE_MEDIUM", "CRYPTO_CANDIDATE_LOW"
TIER_WATCH, TIER_NO_LIQUIDITY, TIER_NO_DATA = "WATCH_ONLY", "NO_LIQUIDITY", "NO_DATA"
TIER_LABELS = {
    TIER_HIGH: "Candidato explosivo · alto", TIER_MEDIUM: "Candidato explosivo · medio", TIER_LOW: "Candidato explosivo · bajo",
    TIER_WATCH: "En vigilancia", TIER_NO_LIQUIDITY: "Sin liquidez suficiente", TIER_NO_DATA: "Sin datos de mercado",
}
GUARDRAIL_TEXT = "No es una recomendación financiera ni predice rentabilidad."


def tier_label(tier: Any) -> str:
    return TIER_LABELS.get(str(tier or ""), str(tier or "N/D"))


def _graded(value: float | None, rule: tuple) -> tuple[int, bool]:
    """(points, strong) for a signal graded strong / partial / none."""
    if value is None:
        return 0, False
    strong_at, strong_points, partial_at, partial_points = rule
    if value >= strong_at:
        return strong_points, True
    if value >= partial_at:
        return partial_points, False
    return 0, False


def passes_gates(row: Mapping) -> bool:
    cap, volume = finite(row.get("market_cap_usd")), finite(row.get("volume_24h_usd"))
    return cap is not None and volume is not None and cap >= MIN_MARKET_CAP_USD and volume >= MIN_VOLUME_24H_USD


def is_young(history_days: Any, history_capped: Any, limit: int) -> bool:
    """True only when the age is KNOWN to be under `limit` days: an unknown age, or a series as long as the plan allows, is never young."""
    days = finite(history_days)
    return days is not None and history_capped is not True and days < limit


def _risk_flags(row: Mapping, turnover: float | None, detail: Mapping | None = None) -> list[str]:
    flags = []
    if turnover is not None and turnover >= SUSPICIOUS_TURNOVER:
        flags.append("rotación sospechosa")
    circulating, total = finite(row.get("circulating_supply")), finite(row.get("total_supply"))
    fdv, cap = finite(row.get("fdv_usd")), finite(row.get("market_cap_usd"))
    ratio_low = circulating is not None and total is not None and total > 0 and circulating / total < DILUTION_CIRCULATING_RATIO
    fdv_high = fdv is not None and cap is not None and cap > 0 and fdv / cap >= DILUTION_FDV_RATIO
    if ratio_low or fdv_high:
        flags.append("dilución alta")
    detail = detail or {}
    if is_young(detail.get("history_days"), detail.get("history_capped"), YOUNG_FLAG_DAYS):
        flags.append("moneda reciente")
    return flags


def score_row(row: Mapping, detail: Mapping | None = None) -> dict:
    """`row` is a normalised `/coins/markets` row; `detail` the output of `signals.daily_signals` (or None when no series was loaded)."""
    detail = detail or {}
    cap, volume = finite(row.get("market_cap_usd")), finite(row.get("volume_24h_usd"))
    base = {"coin_id": row.get("coin_id"), "symbol": row.get("symbol"), "guardrail_text": GUARDRAIL_TEXT}
    if cap is None or cap <= 0 or volume is None or volume < 0:
        return base | {"score": 0, "tier": TIER_NO_DATA, "strong_signals": 0, "drivers": [], "missing_signals": ["capitalización o volumen"], "risk_flags": [],
                           "breakdown": [], "points_before_caps": 0, "caps_applied": []}
    if cap < MIN_MARKET_CAP_USD or volume < MIN_VOLUME_24H_USD:
        return base | {"score": 0, "tier": TIER_NO_LIQUIDITY, "strong_signals": 0, "drivers": [], "missing_signals": [], "risk_flags": [],
                           "breakdown": [], "points_before_caps": 0, "caps_applied": []}

    turnover = volume / cap
    rel_volume, breakout_flag = finite(detail.get("rel_vol_rolling")), detail.get("breakout_30d")
    change_30d, change_7d = finite(row.get("change_30d_pct")), finite(row.get("change_7d_pct"))
    flags = _risk_flags(row, turnover, detail)
    suspicious, dilution = "rotación sospechosa" in flags, "dilución alta" in flags
    young_capped = is_young(detail.get("history_days"), detail.get("history_capped"), YOUNG_CAP_DAYS)
    breakout = breakout_flag is True and rel_volume is not None and rel_volume >= BREAKOUT_MIN_REL_VOLUME

    points, strong, drivers, breakdown = 0, 0, [], []
    for label, value, rule, excluded in (
        ("rotación de volumen", turnover, TURNOVER, suspicious),  # a suspicious turnover earns nothing
        ("volumen relativo", rel_volume, REL_VOLUME, False),
        ("momentum 30 d", change_30d, MOMENTUM_30D, False),
        ("momentum 7 d", change_7d, MOMENTUM_7D, False),
    ):
        gained, is_strong = (0, False) if excluded else _graded(value, rule)
        breakdown.append({"signal": label, "value": value, "points": gained, "strong": is_strong})
        if gained:
            points += gained
            drivers.append(f"{label} {'muy elevado' if is_strong else 'elevado'}")
        strong += int(is_strong)
    breakdown.append({"signal": "ruptura del máximo de 30 días con volumen", "value": breakout_flag if isinstance(breakout_flag, bool) else None,
                      "points": BREAKOUT_POINTS if breakout else 0, "strong": breakout})
    if breakout:
        points += BREAKOUT_POINTS
        strong += 1
        drivers.append("ruptura del máximo de 30 días con volumen")
    small = cap <= SMALL_CAP_USD
    breakdown.append({"signal": "capitalización pequeña", "value": cap, "points": SMALL_CAP_POINTS if small else 0, "strong": False})
    if small:
        points += SMALL_CAP_POINTS
        drivers.append("capitalización pequeña")
    points_before_caps = points

    caps: list[dict] = []

    def cap_to(limit: int, reason: str) -> None:
        nonlocal points
        if points > limit:
            caps.append({"reason": reason, "max": limit})
            points = limit

    missing = [name for name, value in (("volumen relativo", rel_volume), ("momentum 30 d", change_30d)) if value is None]
    if young_capped:
        cap_to(CAP_YOUNG, f"moneda reciente (menos de {YOUNG_CAP_DAYS} días de historial)")
    if missing:
        cap_to(CAP_MISSING, "dato crítico ausente: " + ", ".join(missing))
    if strong < 3:
        cap_to(CAP_FEWER_THAN_3, "menos de 3 señales fuertes")
    elif strong == 3:
        cap_to(CAP_EXACTLY_3, "exactamente 3 señales fuertes")
    elif strong == 4 and not breakout:
        cap_to(CAP_4_WITHOUT_BREAKOUT, "4 señales fuertes sin ruptura")
    if suspicious:
        cap_to(CAP_SUSPICIOUS, "rotación sospechosa")
    if dilution:
        cap_to(CAP_DILUTION, "dilución alta")

    if missing:
        tier = TIER_WATCH
    elif points >= 88 and strong >= 5 and breakout:
        tier = TIER_HIGH
    elif points >= 72 and strong >= 4:
        tier = TIER_MEDIUM
    elif points >= 55 and strong >= 3:
        tier = TIER_LOW
    else:
        tier = TIER_WATCH
    return base | {"score": int(points), "tier": tier, "strong_signals": strong, "drivers": drivers or ["sin señales explosivas suficientes"],
                   "missing_signals": missing, "risk_flags": flags, "breakdown": breakdown, "points_before_caps": int(points_before_caps), "caps_applied": caps}


def _markets_only_points(row: Mapping) -> tuple[int, int]:
    """Points and strong signals from `/coins/markets` fields alone (rotation, momentum, size); no volume history needed."""
    cap, volume = finite(row.get("market_cap_usd")), finite(row.get("volume_24h_usd"))
    if cap is None or volume is None or cap <= 0:
        return 0, 0
    turnover = volume / cap
    points = strong = 0
    if turnover < SUSPICIOUS_TURNOVER:
        gained, is_strong = _graded(turnover, TURNOVER)
        points, strong = points + gained, strong + int(is_strong)
    for value, rule in ((finite(row.get("change_30d_pct")), MOMENTUM_30D), (finite(row.get("change_7d_pct")), MOMENTUM_7D)):
        gained, is_strong = _graded(value, rule)
        points, strong = points + gained, strong + int(is_strong)
    if cap <= SMALL_CAP_USD:
        points += SMALL_CAP_POINTS
    return points, strong


def can_reach_low(row: Mapping) -> bool:
    """True when the coin could still reach the lowest candidate tier if its daily-series signals were the best possible (volume
    relative at the strong level and a breakout). A coin that cannot even then is not worth a call for its daily series."""
    if not passes_gates(row):
        return False
    points, strong = _markets_only_points(row)
    best = points + REL_VOLUME[1] + BREAKOUT_POINTS
    best_strong = strong + 2  # relative volume and breakout, the two signals the series can still add
    flags = _risk_flags(row, finite(row["volume_24h_usd"]) / finite(row["market_cap_usd"]))
    if "rotación sospechosa" in flags:
        best = min(best, CAP_SUSPICIOUS)
    if "dilución alta" in flags:
        best = min(best, CAP_DILUTION)
    if finite(row.get("change_30d_pct")) is None:
        best = min(best, CAP_MISSING)  # the 30-day momentum is a markets field: the series can never supply it
    return best >= 55 and best_strong >= 3


def preselect(rows: list[dict], limit: int = 100) -> list[dict]:
    """The coins worth loading a daily series for: those that could still reach the lowest candidate tier, the most promising first
    (markets-only points, then rotation), at most `limit`. The rule is exact: no coin that could become a candidate is left out
    unless the limit cuts it."""
    pool = [row for row in rows if can_reach_low(row)]
    pool.sort(key=lambda r: (-_markets_only_points(r)[0], -(finite(r.get("turnover_24h")) or 0.0), str(r.get("coin_id"))))
    return pool[:limit]


def summarize(scored: list[dict]) -> dict:
    counts = {tier: 0 for tier in TIER_LABELS}
    for item in scored:
        counts[item["tier"]] = counts.get(item["tier"], 0) + 1
    return counts
