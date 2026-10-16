#!/usr/bin/env python3
"""Regression QA for v2.47B: the explosive candidate's three blocks (why it scores, professional file,
price and candles) are tabs on the candidate's own page, as in the quality-mode ficha, instead of three
expanders repeated on every card; an open candidate page hides the overview. Runs the real functions of
app_v2_37.py on synthetic rows -- no network, no writes."""
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

import streamlit as st  # noqa: E402

import app_v2_37 as app  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def row(asset_id: str, **extra) -> dict:
    return {"asset_id": asset_id, "ticker": asset_id, "company_name": f"{asset_id} Inc"} | extra


def test_candidate_page_uses_three_tabs_with_the_same_labels_the_expanders_had() -> None:
    source = inspect.getsource(app.render_explosive_candidate_fullpage)
    require('st.tabs(["Por qué puntúa así", "Ficha explosiva profesional", "Precio y velas OHLCV"])' in source, "three tabs")
    require("with why_tab:" in source and "with ficha_tab:" in source and "with price_tab:" in source, "each block lives in its tab")
    require('key_prefix="explosive_candles_fullpage"' in source, "page chart keeps its own unique key")


def test_cards_no_longer_repeat_the_three_blocks_in_expanders() -> None:
    source = inspect.getsource(app.render_explosive_candidates_dashboard)
    require("col.expander(" not in source, "no per-card expanders")
    require("Ver ficha completa" in source and "explosive_fullpage_select_" in source, "the only way in is the card button")
    require("render_explosive_candidate_candlestick(row)" not in source, "no nine hidden charts per page")


def test_open_page_is_found_among_all_scored_rows_and_unknown_ids_are_ignored() -> None:
    rows = [row("A"), row("B")]
    state = st.session_state
    try:
        state["explosive_fullpage_asset_id"] = "B"
        require(app.explosive_fullpage_row(rows)["asset_id"] == "B", "selected candidate found")
        state["explosive_fullpage_asset_id"] = "ZZZ"
        require(app.explosive_fullpage_row(rows) is None, "an id that is no longer scored must fall back to the dashboard, never crash")
        state.pop("explosive_fullpage_asset_id", None)
        require(app.explosive_fullpage_row(rows) is None, "nothing selected, no page")
    finally:
        state.pop("explosive_fullpage_asset_id", None)


def test_filters_stay_alive_while_the_page_is_open_and_overview_is_hidden() -> None:
    dashboard = inspect.getsource(app.render_explosive_candidates_dashboard)
    require("for key in EXPLOSIVE_FILTER_KEYS" in dashboard and "st.session_state[key] = st.session_state[key]" in dashboard, "filter widget state kept alive")
    require(set(app.EXPLOSIVE_FILTER_KEYS) == {"explosive_dashboard_tier_filter", "explosive_dashboard_signal_filter", "explosive_dashboard_cards"}, "all three filter widgets covered")
    for key in app.EXPLOSIVE_FILTER_KEYS:
        require(f'key="{key}"' in dashboard, f"{key} must be a real widget key of the dashboard")
    page = inspect.getsource(app.render_explosive_search_page)
    require("explosive_fullpage_row(scored) is not None" in page, "an open candidate page is detected before drawing anything else")
    require("render_explosive_candidates_dashboard(scored)  # the candidate's own page and nothing else" in page, "header, search button, summary and warning are skipped on an open page")


CASES = [
    test_candidate_page_uses_three_tabs_with_the_same_labels_the_expanders_had,
    test_cards_no_longer_repeat_the_three_blocks_in_expanders,
    test_open_page_is_found_among_all_scored_rows_and_unknown_ids_are_ignored,
    test_filters_stay_alive_while_the_page_is_open_and_overview_is_hidden,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.47B explosive candidate tabs QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
