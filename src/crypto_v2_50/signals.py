"""Signals that need the daily series (v2.50E). Pure functions: no network, no cache.

Definitions (stated, because the stock screen taught that a vague "relative volume" hides a partial-day effect):
  * rel_vol_rolling: the 24 h rolling volume of `/coins/markets` divided by the mean volume of the last 30 COMPLETED days. The
    markets figure covers the last 24 hours and the last completed day is a UTC day, so the two windows overlap; that is stated, not
    hidden. Crypto does not close, so there is no partial trading day to warn about.
  * rel_vol_last_day: the last completed day divided by the mean of the 30 days before it (the stable alternative).
  * breakout_30d: the current price is strictly above the highest close of the last 30 completed days.
A signal that cannot be computed (too little history, a zero baseline, a missing current value) is None, never a guess.
"""
from __future__ import annotations

import math
from typing import Any, Mapping


def finite(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def daily_signals(row: Mapping, series: list[dict]) -> dict:
    volumes = [v for v in (finite(p.get("volume_usd")) for p in series) if v is not None]
    closes = [c for c in (finite(p.get("price_usd")) for p in series) if c is not None]
    volume_now, price_now = finite(row.get("volume_24h_usd")), finite(row.get("price_usd"))
    out: dict = {"rel_vol_rolling": None, "rel_vol_last_day": None, "breakout_30d": None}
    if len(volumes) >= 31:
        base = sum(volumes[-30:]) / 30
        if volume_now is not None and base > 0:
            out["rel_vol_rolling"] = volume_now / base
        previous = sum(volumes[-31:-1]) / 30
        if previous > 0:
            out["rel_vol_last_day"] = volumes[-1] / previous
    if len(closes) >= 30 and price_now is not None:
        out["breakout_30d"] = bool(price_now > max(closes[-30:]))
    return out
