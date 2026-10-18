#!/usr/bin/env python3
"""QA for v2.49J (found in a 375px check of v2.49I): the chart title is a line of text above the chart instead of a title inside
the figure (the hover toolbar covered it on a phone), and the card text keeps a minimum gap above its footer button at every width.
Real app through AppTest (fake provider, temporary data folder). No network."""
from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
logging.disable(logging.CRITICAL)

import app_v2_37 as app  # noqa: E402
from qa_explosive_search_page_v2_49a import Sandbox, card_buttons, require, searched_page  # noqa: E402
from qa_explosive_visual_system_v2_49f import demo_ohlcv  # noqa: E402


def test_the_figure_has_no_title_inside_and_keeps_a_strip_for_the_toolbar() -> None:
    figure = app.explosive_candlestick_figure(demo_ohlcv(), "T · velas locales")
    require(not figure.layout.title.text, f"no title inside the figure: {figure.layout.title.text!r}")
    require(figure.layout.meta == "T · velas locales", "the name stays on the figure as metadata")
    require(30 <= figure.layout.margin.t <= 48, f"a strip for the toolbar, not a reserved header: {figure.layout.margin.t}")


def test_the_title_is_text_above_the_chart_on_the_dashboard_and_the_candidate_page() -> None:
    with Sandbox():
        at = searched_page()
        titles = [m.value for m in at.markdown if "velas locales</div>" in m.value]
        require(len(titles) == 1 and "font-weight:700" in titles[0], f"the featured chart has its title line: {titles}")
        card_buttons(at)[0].click().run()
        require(not at.exception, f"crashed: {[e.value[:100] for e in at.exception]}")
        require(any("velas locales</div>" in m.value for m in at.markdown), "the candidate page chart has its title line")


def test_the_title_line_is_escaped_before_it_becomes_markup() -> None:
    import inspect

    source = inspect.getsource(app.render_explosive_candidate_candlestick)
    require("escape(title)" in source, "the ticker-derived title goes through escape() before it is written as HTML")


def test_card_footer_keeps_a_minimum_gap() -> None:
    require("padding-top: 12px" in app.EXPLOSIVE_CARD_CSS and "margin-top: auto" in app.EXPLOSIVE_CARD_CSS, "gap above the footer button, and the button still sits at the bottom of the row")


CASES = [
    test_the_figure_has_no_title_inside_and_keeps_a_strip_for_the_toolbar,
    test_the_title_is_text_above_the_chart_on_the_dashboard_and_the_candidate_page,
    test_the_title_line_is_escaped_before_it_becomes_markup,
    test_card_footer_keeps_a_minimum_gap,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49J explosive mobile polish QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
