#!/usr/bin/env python3
"""Regression QA for the explosive-view redesign (v2.47A): one unified overview panel
replaces the old duplicated pair (a light "cockpit" card immediately followed by a dark
"trading desk" hero repeating 4 of its own 5 numbers). Runs the real functions of
app_v2_37.py on synthetic rows -- no network, no writes."""
from __future__ import annotations

import inspect
import logging
import sys
import warnings
from collections import Counter
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

import app_v2_37 as app  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def candidate_row(asset_id, score, tier, **extra) -> dict:
    base = {
        "asset_id": asset_id, "ticker": asset_id, "company_name": f"{asset_id} Inc", "country": "USA",
        "explosive_score_0_100": score, "tier": tier, "drivers": ["micro-cap real"], "missing_signals": [],
    }
    return base | extra


def test_old_dark_trading_desk_functions_and_duplication_are_gone() -> None:
    source = (ROOT / "app_v2_37.py").read_text(encoding="utf-8")
    require("def render_explosive_trading_desk_skin(" not in source, "the dark skin function must stay removed")
    require("def render_explosive_trading_desk_hero(" not in source, "the dark hero function must stay removed")
    require("def render_explosive_cockpit_summary(" not in source, "the old light cockpit must be folded into the unified overview")
    require("sf-trading-hero" not in source and "sf-radar-core" not in source and "#07111f" not in source, "no leftover dark-theme markup")
    require(source.count("Cockpit de candidatos explosivos") == 0, "no leftover duplicated headline text")


def test_render_explosive_overview_shows_every_number_exactly_once() -> None:
    """The old pair showed High/Medium/Low/Watch in BOTH the cockpit and the hero -- the new
    single panel must build that HTML only once per call."""
    source = inspect.getsource(app.render_explosive_overview)
    for label in ("High", "Medium", "Low", "Watch", "Sin datos"):
        require(source.count(f"<span>{label}</span>") + source.count(f'>{label}</span>') <= 1, f"{label} must be rendered by a single markup site")
    require("st.markdown(overview_html" in source, "must build one HTML block and render it once")


def test_overview_uses_a_light_amber_accent_not_a_dark_theme() -> None:
    source = inspect.getsource(app.render_explosive_overview)
    require("#d97706" in source, "amber left-border accent distinguishes the explosive lens (semantic, not a full theme)")
    require("#fff8ec" in source or "#fffaf0" in source, "background stays light, consistent with the rest of the screen")
    require("#07111f" not in source and "rgba(255,255,255,.10)" not in source, "no dark-panel remnants")


def test_overview_reflects_real_counts_and_top3() -> None:
    rows = [
        candidate_row("A", 82, "EXPLOSIVE_CANDIDATE_HIGH"),
        candidate_row("B", 70, "EXPLOSIVE_CANDIDATE_MEDIUM"),
        candidate_row("C", 55, "EXPLOSIVE_CANDIDATE_LOW"),
        candidate_row("D", 20, "WATCH_ONLY"),
        candidate_row("E", 0, "NO_DATA"),
    ]
    tier_counts = Counter(row["tier"] for row in rows)
    summary = {"explosive": 3, "partial_market": 1, "blocked": 1}
    html_calls = []
    import streamlit as st
    original = st.markdown
    st.markdown = lambda html, **kw: html_calls.append(html)
    try:
        app.render_explosive_overview(rows, summary, tier_counts)
    finally:
        st.markdown = original
    require(len(html_calls) == 1, "must render exactly one markdown block")
    html = html_calls[0]
    require("3 candidatos explosivos" in html, html[:200])
    require("4 empresas con datos de mercado" in html, "4 = 5 rows - 1 NO_DATA")
    require("A Inc" in html and "Top 1" in html and "82" in html, "top-3 must include the highest scorer")


def test_tier_count_grid_wraps_on_narrow_screens() -> None:
    """Live finding: a fixed repeat(5, minmax(84px,1fr)) grid overflowed the page on a 375px
    viewport. auto-fit lets the five boxes wrap onto two rows instead."""
    source = inspect.getsource(app.render_explosive_overview)
    require("repeat(auto-fit,minmax(74px,1fr))" in source, "tier grid must use auto-fit so it wraps on mobile")
    require("repeat(5,minmax(84px,1fr))" not in source, "the old fixed 5-column grid must not come back")


def test_filters_expander_no_longer_repeats_tier_counts() -> None:
    source = inspect.getsource(app.render_explosive_candidates_dashboard)
    require("Filtros de exploración" in source and "y métricas técnicas" not in source, "renamed: metrics moved to the overview above")
    require("tier.replace(\"_\", \" \")" not in source, "the duplicated tier metric loop must stay removed")
    require("render_explosive_trading_desk_skin()" not in source and "render_explosive_trading_desk_hero(" not in source, "dashboard must not call the removed dark-hero functions")


CASES = [
    test_old_dark_trading_desk_functions_and_duplication_are_gone,
    test_render_explosive_overview_shows_every_number_exactly_once,
    test_overview_uses_a_light_amber_accent_not_a_dark_theme,
    test_overview_reflects_real_counts_and_top3,
    test_tier_count_grid_wraps_on_narrow_screens,
    test_filters_expander_no_longer_repeats_tier_counts,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.47A explosive unified overview QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
