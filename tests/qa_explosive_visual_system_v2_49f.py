#!/usr/bin/env python3
"""QA for v2.49F (graphic design review DG-01..DG-08 for the explosive screen): the text colours meet WCAG AA contrast on
the surface they sit on, geometry and weights come from a small set of tokens, amber is the section identity and never a
level, the score always carries /100, the search button shrinks once there are results, the podium is gone, and the chart
keeps volume in its own panel with the fitted line as an optional layer. Static checks on the real source, direct checks on
the real functions, and the real app through AppTest (fake provider, temporary data folder). No network."""
from __future__ import annotations

import inspect
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

import pandas as pd  # noqa: E402

import app_v2_37 as app  # noqa: E402
from qa_explosive_search_page_v2_49a import Sandbox, button, card_buttons, open_explosive_page, require, searched_page  # noqa: E402

SOURCE = (ROOT / "app_v2_37.py").read_text(encoding="utf-8")
BLOCK = SOURCE[SOURCE.index("# Visual tokens of the explosive screen."):SOURCE.index("def render_unicorn_semantic_split")]


def luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_every_text_colour_meets_aa_on_the_surfaces_it_sits_on() -> None:
    """Colours that carry text in the explosive block: 4.5:1 for normal text, 3:1 for large (>= 24px) text."""
    surfaces = ["#ffffff", app.EXPLOSIVE_SURFACE_AMBER]
    failures = []
    for style in re.findall(r'style="([^"]*)"|style=\\"([^\\"]*)\\"', BLOCK):
        css = style[0] or style[1]
        colour = re.search(r"(?<![-\w])color:(#[0-9a-fA-F]{6})", css)
        if not colour:
            continue
        size = re.search(r"font-size:(\d+)px", css)
        threshold = 3.0 if size and int(size.group(1)) >= 24 else 4.5
        for surface in surfaces:
            if contrast(colour.group(1), surface) < threshold:
                failures.append((colour.group(1), surface, round(contrast(colour.group(1), surface), 2), css[:60]))
    require(not failures, f"text below WCAG AA: {failures}")
    for token in (app.EXPLOSIVE_INK, app.EXPLOSIVE_TEXT, app.EXPLOSIVE_TEXT_SECONDARY, app.EXPLOSIVE_ACCENT_TEXT):
        for surface in surfaces:
            require(contrast(token, surface) >= 4.5, f"token {token} on {surface}: {contrast(token, surface):.2f}")
    require("#94a3b8" not in re.sub(r'"border": "#94a3b8"', "", BLOCK).replace('marker_color="#94a3b8"', ""), "the old 2.5:1 grey must not carry text any more")


def test_every_tier_chip_is_legible_on_its_own_background() -> None:
    for tier, style in app.EXPLOSIVE_TIER_STYLES.items():
        require(contrast(style["chip_fg"], style["chip_bg"]) >= 4.5, f"{tier} chip {contrast(style['chip_fg'], style['chip_bg']):.2f}:1")


def test_geometry_and_weights_come_from_few_values() -> None:
    radii = {int(x) for x in re.findall(r"border-radius:(\d+)px", BLOCK)} | {app.EXPLOSIVE_RADIUS, app.EXPLOSIVE_RADIUS_SMALL}
    require(radii <= {8, 12, 18, 999}, f"radii in the explosive block: {sorted(radii)}")
    require(re.findall(r"font-weight:(\d+)", BLOCK) and set(re.findall(r"font-weight:(\d+)", BLOCK)) <= {"600", "700", "800"}, f"weights: {set(re.findall(r'font-weight:(\d+)', BLOCK))}")
    sizes = [int(x) for x in re.findall(r"font-size:(\d+)px", BLOCK)]
    require(min(sizes) >= 12, f"no text under 12px (found {min(sizes)})")


def test_amber_is_the_section_identity_and_never_a_level() -> None:
    for tier, style in app.EXPLOSIVE_TIER_STYLES.items():
        require("d97706" not in " ".join(style.values()).lower() and "b45309" not in " ".join(style.values()).lower(), f"{tier} must not use the identity amber")
    require(app.explosive_tier_style("something-unknown") == app.EXPLOSIVE_TIER_STYLES["NO_DATA"], "an unknown level falls back to the neutral style")
    require("#d97706" not in inspect.getsource(app.render_explosive_candidates_dashboard) and "#d97706" not in inspect.getsource(app.render_explosive_candidate_fullpage), "cards and candidate page take their colour from the level style, not from amber")


def test_the_score_always_carries_out_of_100_and_the_level_is_a_text_chip() -> None:
    with Sandbox():
        at = searched_page()
        cards = [m.value for m in at.markdown if "Señales detectadas:" in m.value]
        require(len(cards) == 9, f"nine cards expected, found {len(cards)}")
        for html in cards:
            require("/100</span>" in html, "every card shows the score out of 100")
            require("border-radius:999px" in html and "Vigilancia" not in html or "En vigilancia" in html or "Candidato explosivo" in html, "the level is a text chip")
        card_buttons(at)[0].click().run()
        header = " ".join(m.value for m in at.markdown)
        require("/100</span>" in header and "border-radius:999px" in header, "the candidate page header uses the same score and chip")


def test_the_podium_is_gone_and_the_first_row_of_the_list_is_what_it_showed() -> None:
    with Sandbox():
        at = searched_page()
        text = " ".join(m.value for m in at.markdown)
        require("Top 3" not in text and "Top 1" not in text, "no podium")
        require("Mayor puntuación disponible" not in text, "the old podium note is gone")


def test_the_search_button_is_big_until_there_are_results_and_compact_after() -> None:
    with Sandbox():
        at = open_explosive_page()
        before = " ".join(m.value for m in at.markdown)
        require("min-height: 150px" in before, "big button on the clean page")
        button(at, "explosive_search").click().run()
        require(not at.exception, f"crashed: {[e.value[:100] for e in at.exception]}")
        after = " ".join(m.value for m in at.markdown)
        require("min-height: 64px" in after, "compact button once the results are there")
        require(len(card_buttons(at)) == 9, "and the results are in their final layout after the redraw")


def demo_ohlcv(days: int = 40) -> pd.DataFrame:
    dates = pd.bdate_range("2026-08-01", periods=days)
    closes = [10 + i * 0.1 + (i % 4) * 0.2 for i in range(days)]
    return pd.DataFrame({"Date": dates, "Open": closes, "High": [c + 0.5 for c in closes], "Low": [c - 0.5 for c in closes], "Close": closes, "Volume": [1000 + i * 10 for i in range(days)]})


def test_volume_has_its_own_panel_and_the_fitted_line_is_an_optional_layer() -> None:
    figure = app.explosive_candlestick_figure(demo_ohlcv(), "T")
    kinds = [t.type for t in figure.data]
    require("candlestick" in kinds and "bar" in kinds and kinds.count("scatter") == 3, kinds)
    volume = next(t for t in figure.data if t.type == "bar")
    price = next(t for t in figure.data if t.type == "candlestick")
    require(volume.yaxis != price.yaxis and volume.yaxis == "y2", f"volume on its own axis: {volume.yaxis} vs {price.yaxis}")
    require(figure.layout.yaxis2.overlaying is None, "the volume axis must not overlay the price axis")
    price_domain, volume_domain = figure.layout.yaxis.domain, figure.layout.yaxis2.domain
    require(volume_domain[1] <= price_domain[0], f"separate panels: {price_domain} vs {volume_domain}")
    require(figure.layout.yaxis.title.text == "Precio" and figure.layout.yaxis2.title.text == "Volumen", "both axes are titled")
    shown_band = [t for t in figure.data if t.type == "scatter" and "desv. residuales" in (t.name or "") and t.showlegend is not False]
    require(len(shown_band) == 1, "the two band lines share one legend entry (still the hover name)")
    require(figure.layout.showlegend is False, "the key is a caption under the chart, not a legend inside it (v2.49I)")
    bare = app.explosive_candlestick_figure(demo_ohlcv(), "T", show_regression=False)
    require([t.type for t in bare.data].count("scatter") == 0, "without the layer there is no fitted line or band")
    price_only = app.explosive_candlestick_figure(demo_ohlcv().drop(columns=["Volume"]), "T")
    require(not any(t.type == "bar" for t in price_only.data), "no volume, no volume panel")


def test_the_regression_layer_has_a_switch_on_the_candidate_page() -> None:
    with Sandbox():
        at = searched_page()
        card_buttons(at)[0].click().run()
        require(not at.exception, f"crashed: {[e.value[:100] for e in at.exception]}")
        switches = [c for c in at.checkbox if (c.key or "").startswith("explosive_candles_fullpage_layers_")]
        require(len(switches) == 1 and switches[0].value is True, "one switch, on by default")
        switches[0].uncheck().run()
        require(not at.exception, f"crashed after switching the layer off: {[e.value[:100] for e in at.exception]}")


CASES = [
    test_every_text_colour_meets_aa_on_the_surfaces_it_sits_on,
    test_every_tier_chip_is_legible_on_its_own_background,
    test_geometry_and_weights_come_from_few_values,
    test_amber_is_the_section_identity_and_never_a_level,
    test_the_score_always_carries_out_of_100_and_the_level_is_a_text_chip,
    test_the_podium_is_gone_and_the_first_row_of_the_list_is_what_it_showed,
    test_the_search_button_is_big_until_there_are_results_and_compact_after,
    test_volume_has_its_own_panel_and_the_fitted_line_is_an_optional_layer,
    test_the_regression_layer_has_a_switch_on_the_candidate_page,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49F explosive visual system QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
