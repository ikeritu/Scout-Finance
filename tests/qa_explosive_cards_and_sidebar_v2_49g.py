#!/usr/bin/env python3
"""QA for v2.49G (DG-05 and DG-07): each explosive candidate card is one bordered container whose footer button lines up per
row without a fixed height, and the sidebar uses one family of functional icons with the unicorn kept as the section identity,
no long counters in labels, and the technical status tucked into an expander while "Sin conexión a broker" stays visible.
Real app through AppTest (fake provider, temporary data folder). No network."""
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

import app_v2_37 as app  # noqa: E402
from qa_explosive_search_page_v2_49a import Sandbox, card_buttons, require, searched_page  # noqa: E402


def test_sidebar_uses_one_icon_family_and_keeps_the_unicorn() -> None:
    labels = app.SCREENS
    require(labels["global_unicorns"].startswith("🦄"), "the unicorn stays as the identity of the section")
    others = {k: v for k, v in labels.items() if k != "global_unicorns"}
    require(all(re.match(r":material/[a-z_]+: ", v) for v in others.values()), f"every other entry uses a Material icon: {others}")
    require(len({re.match(r":material/([a-z_]+):", v).group(1) for v in others.values()}) == len(others), "no icon is repeated")
    require(not any(re.search(r"\(\d[\d.]*\)", v) for v in labels.values()), "no counters inside navigation labels")
    require("Ranking global (experimental)" in labels["global_ranking"] and "Guía final y uso responsable" in labels["final_guide"], "the honesty wording of the labels stays")


def test_technical_status_is_in_an_expander_and_the_broker_line_stays_visible() -> None:
    with Sandbox():
        at = searched_page()
        sidebar = " ".join(c.value for c in at.sidebar.caption)
        require("Sin conexión a broker" in sidebar, "the no-broker line stays visible in the sidebar")
        expanders = [e for e in at.sidebar.expander]
        require(len(expanders) == 1 and expanders[0].label == "Estado técnico", [e.label for e in expanders])
        inside = " ".join(c.value for c in expanders[0].caption)
        require("Datos:" in inside and "Fase 7: INSUFFICIENT_EVIDENCE" in inside, "the technical lines moved inside the expander, text unchanged")


def test_each_card_is_one_container_with_the_button_as_its_footer() -> None:
    source = inspect.getsource(app.render_explosive_candidates_dashboard)
    require('border=True, key=card_key, height="stretch"' in source, "bordered container that stretches to the tallest card of its row")
    require("min-height" not in source, "no fixed height that could cut text")
    css = app.EXPLOSIVE_CARD_CSS
    require("margin-top: auto" in css and "flex-direction: column" in css, "the footer is pushed to the bottom of the card")
    with Sandbox():
        at = searched_page()
        buttons = card_buttons(at)
        require(len(buttons) == 9, f"nine cards, found {len(buttons)}")
        require(len({b.key for b in buttons}) == 9, "one button per card")
        cards = [m.value for m in at.markdown if "Señales detectadas:" in m.value]
        require(len(cards) == 9 and all("/100</span>" in c and "border-left: 6px solid" in c for c in cards), "each card keeps its score, level chip and level accent")
        buttons[0].click().run()
        require(not at.exception and [t.label for t in at.tabs] == ["Resumen", "Datos", "Gráfico"], "the button inside the card still opens the candidate page")


CASES = [
    test_sidebar_uses_one_icon_family_and_keeps_the_unicorn,
    test_technical_status_is_in_an_expander_and_the_broker_line_stays_visible,
    test_each_card_is_one_container_with_the_button_as_its_footer,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49G explosive cards and sidebar QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
