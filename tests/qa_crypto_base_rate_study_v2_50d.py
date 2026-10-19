#!/usr/bin/env python3
"""QA for the pure parts of the v2.50D study script: the stratified sample is deterministic and spans the bands, the daily-series
signals are computed from completed days only with the stated definitions, and the report states what it is (descriptive,
aggregates only). No network, no key."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd  # noqa: E402

import crypto_base_rate_study_v2_50d as study  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def synthetic_universe(n: int = 400) -> pd.DataFrame:
    caps = [5e6 * (1.011 ** i) * 40 / 40 for i in range(n)]  # 5 M$ upward, geometric
    return pd.DataFrame({"coin_id": [f"c{i}" for i in range(n)], "market_cap_usd": caps})


def test_the_sample_is_deterministic_spans_the_bands_and_never_exceeds_the_quota() -> None:
    frame = synthetic_universe()
    first = study.stratified_sample(frame, 10)
    second = study.stratified_sample(frame, 10)
    require(first["coin_id"].tolist() == second["coin_id"].tolist(), "same input, same sample (no randomness)")
    require(first["coin_id"].is_unique, "no coin twice")
    for label, low, high in study.SAMPLE_BANDS:
        in_band = frame[(frame["market_cap_usd"] >= low) & (frame["market_cap_usd"] < high)]
        taken = first[(first["market_cap_usd"] >= low) & (first["market_cap_usd"] < high)]
        require(len(taken) == min(10, len(in_band)), f"{label}: {len(taken)} taken of {len(in_band)} available")
    require(first["market_cap_usd"].min() >= 5e6, "coins under 5 M$ are not sampled")
    span = first.sort_values("market_cap_usd")
    require(span.iloc[0]["market_cap_usd"] < 1e7 and span.iloc[-1]["market_cap_usd"] > 2e8, "the sample spans small and large coins")


def series(volumes: list, closes: list) -> list[dict]:
    return [{"date": f"d{i}", "price_usd": c, "volume_usd": v, "market_cap_usd": None} for i, (v, c) in enumerate(zip(volumes, closes))]


def test_daily_signals_use_completed_days_and_the_stated_definitions() -> None:
    volumes = [100.0] * 30 + [300.0]  # 30 days of 100 then one completed day of 300
    closes = [10.0] * 30 + [10.0]
    row = pd.Series({"volume_24h_usd": 250.0, "price_usd": 10.5})
    out = study.daily_signals(row, series(volumes, closes))
    require(abs(out["rel_vol_rolling"] - 250.0 / ((100.0 * 29 + 300.0) / 30)) < 1e-9, f"rolling: 24 h volume / mean of the last 30 completed days: {out['rel_vol_rolling']}")
    require(abs(out["rel_vol_last_day"] - 3.0) < 1e-9, f"stable: last completed day / mean of the 30 before it: {out['rel_vol_last_day']}")
    require(out["breakout_30d"] is True, "price above the max of the last 30 closes")
    flat = study.daily_signals(pd.Series({"volume_24h_usd": 250.0, "price_usd": 10.0}), series(volumes, closes))
    require(flat["breakout_30d"] is False, "equal to the max is not a breakout")
    short = study.daily_signals(row, series([1.0] * 10, [1.0] * 10))
    require({k: short[k] for k in ("rel_vol_rolling", "rel_vol_last_day", "breakout_30d")} == {"rel_vol_rolling": None, "rel_vol_last_day": None, "breakout_30d": None}
            and short["history_days"] == 10 and short["history_capped"] is False, f"too little history gives no signal, not a guess (the history length is reported since v2.50I): {short}")
    zero = study.daily_signals(row, series([0.0] * 31, [1.0] * 31))
    require(zero["rel_vol_rolling"] is None and zero["rel_vol_last_day"] is None, "a zero baseline gives no ratio")
    missing = study.daily_signals(pd.Series({"volume_24h_usd": None, "price_usd": None}), series(volumes, closes))
    require(missing["rel_vol_rolling"] is None and missing["breakout_30d"] is None, "a missing current value gives no signal")


def test_helpers_and_the_report_say_what_they_are() -> None:
    require(study.pct(1, 4) == "1 (25.0 %)" and study.pct(0, 0) == "0", "pct")
    require(study.quantiles(pd.Series([float("nan")])) == "sin datos" and "p50" in study.quantiles(pd.Series([1.0, 2.0, 3.0])), "quantiles")
    frame = synthetic_universe()
    frame = frame.assign(volume_24h_usd=1e6, price_usd=1.0, turnover_24h=0.1, change_7d_pct=1.0, change_14d_pct=1.0, change_30d_pct=1.0,
                         circulating_supply=1.0, total_supply=2.0, fdv_usd=frame["market_cap_usd"] * 2, rel_vol_rolling=1.0, rel_vol_last_day=1.0, breakout_30d=False)
    result = {"universe": 450, "from_cache": True, "fetched_at": pd.Timestamp("2026-10-19T10:00:00Z").to_pydatetime(), "excluded": 50, "excluded_by": {"stablecoins": 50},
              "kept": frame, "sample": study.stratified_sample(frame, 5), "calls_used": 0, "usage": {"month": "2026-10", "calls": 1, "cap": 8000}}
    text = study.render(result)
    require("No predice nada" in text and "Solo agregados" in text, "the report states that it only describes and keeps aggregates")
    for needle in ("## A.", "## B.", "Composición por capitalización", "Rotación sospechosa", "Dilución"):
        require(needle in text, f"missing section: {needle}")


CASES = [
    test_the_sample_is_deterministic_spans_the_bands_and_never_exceeds_the_quota,
    test_daily_signals_use_completed_days_and_the_stated_definitions,
    test_helpers_and_the_report_say_what_they_are,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.50D crypto base-rate study QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
