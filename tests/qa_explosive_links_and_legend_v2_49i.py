#!/usr/bin/env python3
"""QA for v2.49I: every explosive candidate with a verified US ticker links to Yahoo Finance and Google Finance (cards and candidate
page); no ticker means no link; hrefs are escaped and open safely in a new tab; the link colour is legible. The chart key is a
caption under the chart (it wraps at any width) instead of a legend inside it. Real app through AppTest (fake provider,
temporary data folder). No network."""
from __future__ import annotations

import logging
import re
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
from qa_explosive_visual_system_v2_49f import contrast, demo_ohlcv  # noqa: E402


def urls(row: dict) -> dict[str, str]:
    return dict(app.explosive_external_links(row))


def test_links_follow_the_ticker_the_search_uses_and_fail_closed() -> None:
    nasdaq = urls({"ticker": "PLTR", "exchange": "NASDAQ", "country": "USA"})
    require(nasdaq == {"Yahoo Finance": "https://finance.yahoo.com/quote/PLTR", "Google Finance": "https://www.google.com/finance/?q=PLTR"}, str(nasdaq))
    cboe = urls({"ticker": "1PLTRm", "us_ticker": "PLTR", "exchange": "CBOE_EUROPE", "country": "USA"})
    require("quote/PLTR" in cboe["Yahoo Finance"] and cboe["Google Finance"].endswith("q=PLTR"), "a Cboe Europe listing links through its real US ticker, never the local symbol")
    dotted = urls({"ticker": "BRK.B", "exchange": "NYSE", "country": "USA"})
    require(dotted["Yahoo Finance"].endswith("quote/BRK-B") and dotted["Google Finance"].endswith("q=BRK.B"), f"Yahoo writes the class with a dash, Google keeps the dot: {dotted}")
    require(app.explosive_external_links({"ticker": "AMDd", "exchange": "CBOE_EUROPE", "country": "USA"}) == [], "a local Cboe symbol with no US ticker gets no link")
    require(app.explosive_external_links({"ticker": "ABC", "exchange": "XETR", "country": "AT"}) == [], "a non-US listing gets no link")
    require(app.explosive_external_links({"exchange": "NASDAQ", "country": "USA"}) == [] and app.explosive_links_html({}) == "", "no ticker, no link, no empty markup")


def test_hrefs_are_escaped_and_open_safely() -> None:
    hostile = {"ticker": 'X"><script>alert(1)</script>', "exchange": "NASDAQ", "country": "USA"}
    html = app.explosive_links_html(hostile)
    require("<script" not in html and '"><' not in html.replace('"><a', "").replace('↗</a>', ""), f"the ticker cannot break out of the attribute: {html[:200]}")
    for href in re.findall(r'href="([^"]*)"', html):
        require(" " not in href and "<" not in href and '"' not in href, f"unsafe href {href}")
    good = app.explosive_links_html({"ticker": "PLTR", "exchange": "NASDAQ", "country": "USA"})
    require(good.count('target="_blank"') == 2 and good.count('rel="noopener noreferrer"') == 2, "both links open in a new tab without handing over the opener")


def test_link_colour_is_legible_on_every_surface_it_sits_on() -> None:
    for surface in ("#ffffff", app.EXPLOSIVE_SURFACE_AMBER):
        require(contrast(app.EXPLOSIVE_LINK, surface) >= 4.5, f"link colour {app.EXPLOSIVE_LINK} on {surface}: {contrast(app.EXPLOSIVE_LINK, surface):.2f}")


def test_every_card_and_the_candidate_page_carry_both_links() -> None:
    with Sandbox():
        at = searched_page()
        cards = [m.value for m in at.markdown if "Señales detectadas:" in m.value]
        require(len(cards) == 9, f"nine cards, found {len(cards)}")
        for html in cards:
            require("Yahoo Finance ↗" in html and "Google Finance ↗" in html, "each card links to both sites")
        require(any("Yahoo Finance" in c.value and "comprueba que el nombre" in c.value for c in at.caption), "the list says the links search by ticker and asks to check the name")
        card_buttons(at)[0].click().run()
        require(not at.exception, f"crashed: {[e.value[:100] for e in at.exception]}")
        header = " ".join(m.value for m in at.markdown)
        require("Yahoo Finance ↗" in header and "Google Finance ↗" in header, "the candidate page header links to both sites")


def test_the_chart_key_is_a_caption_not_a_legend_inside_the_figure() -> None:
    figure = app.explosive_candlestick_figure(demo_ohlcv(), "T")
    require(figure.layout.showlegend is False, "no legend inside the figure")
    require(figure.layout.margin.t <= 56, f"no reserved header space: {figure.layout.margin.t}")
    full = app.explosive_chart_legend(has_volume=True, show_regression=True)
    require("Velas verdes" in full and "recta de regresión lineal" in full and "±1,96 desviaciones residuales" in full and "volumen" in full, full)
    require("regresión" not in app.explosive_chart_legend(has_volume=True, show_regression=False), "the fitted-line key goes away with the layer")
    require("volumen" not in app.explosive_chart_legend(has_volume=False, show_regression=True), "no volume key without volume")
    with Sandbox():
        at = searched_page()
        require(any(c.value.startswith("Velas verdes") for c in at.caption), "the dashboard's featured chart shows its key under it")
        card_buttons(at)[0].click().run()
        require(sum(c.value.startswith("Velas verdes") for c in at.caption) >= 1, "the candidate page chart shows its key under it")


CASES = [
    test_links_follow_the_ticker_the_search_uses_and_fail_closed,
    test_hrefs_are_escaped_and_open_safely,
    test_link_colour_is_legible_on_every_surface_it_sits_on,
    test_every_card_and_the_candidate_page_carry_both_links,
    test_the_chart_key_is_a_caption_not_a_legend_inside_the_figure,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49I explosive links and legend QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
