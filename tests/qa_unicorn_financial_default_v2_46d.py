#!/usr/bin/env python3
"""Regression QA for hiding financial institutions from the default unicorn list (v2.46D).
Checks the real screen source and helpers -- no network, no writes."""
from __future__ import annotations

import inspect
import logging
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

import app_v2_37 as app  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_financials_are_hidden_by_default_but_never_lost() -> None:
    screen = inspect.getsource(app.render_global_unicorns)
    require('st.session_state.get("global_unicorn_include_financials", False)' in screen, "hidden by default")
    require("not unicorn_needs_financial_review(row)" in screen, "default list excludes financial institutions")
    require('key="global_unicorn_include_financials"' in screen, "opt-in checkbox with a stable key")
    require('base_rows = all_unicorn_rows if quick_filter == "Revisión requerida" else unicorn_rows' in screen, "the review filter still shows them")
    require("de {len(base_rows):,} unicornios" in screen, "count denominators match the base set")


def test_the_two_detection_paths_both_count() -> None:
    require(app.unicorn_needs_financial_review({"eligibility_tier": "REVIEW_REQUIRED_FINANCIAL_INSTITUTION"}), "tier path")
    require(app.unicorn_needs_financial_review({"is_financial_sic": "true"}), "SIC path")
    require(not app.unicorn_needs_financial_review({"eligibility_tier": "ELIGIBLE_FULL", "is_financial_sic": "false"}), "industrial company stays")


def test_search_finds_the_real_us_ticker() -> None:
    require('"us_ticker")))' in inspect.getsource(app.render_global_unicorns), "searching PLTR must find the Cboe-only row")


CASES = [test_financials_are_hidden_by_default_but_never_lost, test_the_two_detection_paths_both_count, test_search_finds_the_real_us_ticker]


def main() -> int:
    for case in CASES:
        case()
    print("v2.46D unicorn financial default QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
