#!/usr/bin/env python3
"""Regression QA for the two-column unicorn layout and the growth/sector filters (v2.46C).
Runs the real helpers of app_v2_37.py on synthetic rows -- no network, no writes."""
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

INF = float("inf")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_sector_comes_from_sec_sic_and_missing_is_explicit() -> None:
    require(app.unicorn_sector({"sic_description": "SERVICES-PREPACKAGED SOFTWARE"}) == "Services-Prepackaged Software", "title case")
    for empty in ({}, {"sic_description": ""}, {"sic_description": float("nan")}):
        require(app.unicorn_sector(empty) == app.NO_SECTOR_LABEL, f"missing sector must be explicit: {empty}")


def test_growth_range_filter_semantics() -> None:
    row = {"revenue_yoy_growth": "0.35"}
    full = (app.UNICORN_GROWTH_STEPS[0], app.UNICORN_GROWTH_STEPS[-1])
    require(full == (0, INF), full)
    require(app.unicorn_growth_in_range(row, 30, 50), "35 % is inside 30-50")
    require(not app.unicorn_growth_in_range(row, 50, INF), "35 % is outside 50+")
    require(app.unicorn_growth_in_range({}, 0, INF), "untouched range must not hide rows without a figure")
    require(not app.unicorn_growth_in_range({}, 10, INF), "a narrowed range hides rows without a figure (documented in the help text)")
    require(app.unicorn_growth_in_range({"revenue_yoy_growth": "232.58"}, 500, INF) and app.unicorn_growth_in_range({"revenue_yoy_growth": "232.58"}, 0, INF), "extreme real outliers stay reachable with the open-ended top")


def test_growth_steps_are_usable_not_linear() -> None:
    steps = app.UNICORN_GROWTH_STEPS
    require(list(steps) == sorted(steps) and len(steps) >= 6 and steps[-1] == INF, "fixed ascending steps with an open top")
    require(app.unicorn_growth_step_label(INF) == "Sin tope" and app.unicorn_growth_step_label(30) == "30 %", "labels")


def test_filters_are_wired_into_the_screen_and_layout_is_two_columns() -> None:
    screen = inspect.getsource(app.render_global_unicorns)
    require("unicorn_growth_in_range(row, growth_low, growth_high, growth_bounds)" in screen and "unicorn_sector(row) in sector_filter" in screen, "filters applied to the list")
    require('key="global_unicorn_growth_range"' in screen and 'key="global_unicorn_sector"' in screen, "stable widget keys")
    visual = inspect.getsource(app.render_unicorn_visual_analytics)
    require("list_col, detail_col = st.columns([1, 2]" in visual and "render_unicorn_ficha(selected" in visual, "list left, detail right")
    require("ficha-unicornio" not in visual and "st.toast" not in visual, "no scroll-to-detail workaround is needed any more")
    require(callable(app.render_unicorn_ficha), "detail is its own renderer")


CASES = [
    test_sector_comes_from_sec_sic_and_missing_is_explicit,
    test_growth_range_filter_semantics,
    test_growth_steps_are_usable_not_linear,
    test_filters_are_wired_into_the_screen_and_layout_is_two_columns,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.46C unicorn layout and filters QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
