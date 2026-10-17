#!/usr/bin/env python3
"""QA for the v2.49E comparison script (scripts/compare_relative_volume_v2_49e.py): the alternative relative volume
excludes the session being measured, needs a full baseline, and re-scores through the live scoring without changing it.
Synthetic series only; no network, no local data needed."""
from __future__ import annotations

import importlib.util
import logging
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

import pandas as pd  # noqa: E402

spec = importlib.util.spec_from_file_location("compare_relative_volume_v2_49e", ROOT / "scripts" / "compare_relative_volume_v2_49e.py")
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_the_measured_session_is_excluded_from_its_own_baseline() -> None:
    volumes = pd.Series([100.0] * 60 + [200.0])
    require(compare.alternative_relative_volume(volumes, 60) == 2.0, "200 against a baseline of 60 sessions of 100 is exactly 2")
    spike_then_normal = pd.Series([100.0] * 59 + [1000.0, 100.0])
    require(round(compare.alternative_relative_volume(spike_then_normal, 60), 3) == round(100 / ((59 * 100 + 1000) / 60), 3), "an earlier spike stays in the baseline")


def test_it_needs_a_full_baseline_and_a_positive_one() -> None:
    require(compare.alternative_relative_volume(pd.Series([100.0] * 60), 60) is None, "60 sessions are not enough for a 60-session baseline plus the measured one")
    require(compare.alternative_relative_volume(pd.Series([0.0] * 60 + [5.0]), 60) is None, "a zero baseline gives no ratio")
    require(compare.alternative_relative_volume(pd.Series(["x"] * 3 + [None] * 3), 2) is None, "non-numeric volumes give no ratio")


def test_rescoring_uses_the_live_scoring_and_the_breakout_rule() -> None:
    base = {"asset_id": "T1", "ticker": "TST", "company_name": "Test", "market_cap_usd": 120_000_000, "last_price": 2.4, "price_change_20d": 25.0,
            "float_shares": 9_000_000, "short_float_pct": 21.0, "catalyst_note": "yfinance_real_market_snapshot_v2_45c"}
    low = compare.rescored(base, 1.4)
    breakout = compare.rescored(base, 2.5)
    require("breakout detectado" not in low["drivers"] and "breakout detectado" in breakout["drivers"], "breakout needs relative volume >= 2 and a 20-day change >= 20 %")
    require(breakout["explosive_score_0_100"] > low["explosive_score_0_100"], "a higher relative volume raises the score")
    no_move = compare.rescored(base | {"price_change_20d": 5.0}, 2.5)
    require("breakout detectado" not in no_move["drivers"], "high relative volume alone is not a breakout")


def test_the_summary_reports_the_agreement_and_what_moves() -> None:
    frame = pd.DataFrame([
        {"ticker": "AAA", "current": 2.03, "alt": 1.64, "score_now": 63, "tier_now": "EXPLOSIVE_CANDIDATE_LOW", "score_alt": 44, "tier_alt": "WATCH_ONLY"},
        {"ticker": "BBB", "current": 1.0, "alt": 1.0, "score_now": 10, "tier_now": "WATCH_ONLY", "score_alt": 10, "tier_alt": "WATCH_ONLY"},
    ])
    result = {"window": 20, "population": 2, "with_market_data": 2, "compared": 2, "skipped": 0, "frame": frame, "spearman": 1.0,
              "ratio_quantiles": {0.05: 0.8, 0.25: 0.9, 0.5: 1.0, 0.75: 1.0, 0.95: 1.0}, "cut_flips": {2.0: 1, 3.0: 0}, "at_or_above": {2.0: (1, 0), 3.0: (0, 0)},
              "tier_now": {"EXPLOSIVE_CANDIDATE_LOW": 1, "WATCH_ONLY": 1}, "tier_alt": {"WATCH_ONLY": 2}, "tier_changed": 1, "score_changed": 1, "max_score_move": 19}
    text = compare.render_markdown(result)
    require("ventana 20" in text and "Spearman" in text and "63 → 44" in text and "AAA" in text, text)
    require("BBB" not in text, "companies that do not move are not listed")
    require(compare.render_markdown({**result, "frame": frame.iloc[0:0]}).count("No hay barras diarias suficientes") == 1, "an empty comparison says why")


CASES = [
    test_the_measured_session_is_excluded_from_its_own_baseline,
    test_it_needs_a_full_baseline_and_a_positive_one,
    test_rescoring_uses_the_live_scoring_and_the_breakout_rule,
    test_the_summary_reports_the_agreement_and_what_moves,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49E relative volume comparison QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
