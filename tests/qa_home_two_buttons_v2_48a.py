#!/usr/bin/env python3
"""QA for v2.48A: the landing screen is two big click targets -- "Unicornios en bolsa" (goes to the
Unicornios screen) and "Unicornios Crypto" (visible but disabled, not implemented yet). Executes the real app
headlessly with Streamlit's AppTest. No network, no writes."""
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

from streamlit.testing.v1 import AppTest  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def home() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app_v2_37.py"), default_timeout=180)
    at.run()
    return at


def button(at: AppTest, key: str):
    return next(b for b in at.button if b.key == key)


def test_home_is_exactly_two_big_buttons() -> None:
    at = home()
    require(not at.exception, f"home crashed: {[e.value[:100] for e in at.exception]}")
    require(at.session_state["screen"] == "home", "the app opens on the home screen")
    keys = sorted(b.key for b in at.button)
    require(keys == ["home_crypto", "home_stocks"], f"the landing must offer exactly the two buttons, found {keys}")
    require(not at.metric, "the old KPI row must not be on the landing any more")
    require(button(at, "home_stocks").label == "🦄 Unicornios en bolsa", button(at, "home_stocks").label)
    require(button(at, "home_crypto").label == "🪙 Unicornios Crypto", button(at, "home_crypto").label)


def test_crypto_is_visible_but_disabled() -> None:
    at = home()
    require(button(at, "home_crypto").disabled is True, "not implemented yet: it must not be clickable")
    require(button(at, "home_stocks").disabled is False, "the stocks button must be clickable")
    require(any("Próximamente" in c.value for c in at.caption), "it must say it is coming soon")


def test_stocks_button_opens_the_unicornios_screen() -> None:
    at = home()
    button(at, "home_stocks").click().run()
    require(not at.exception, f"Unicornios crashed after the click: {[e.value[:100] for e in at.exception]}")
    require(at.session_state["screen"] == "global_unicorns", at.session_state["screen"])
    require(any(h.value == "Unicornios" for h in at.title), "the Unicornios screen is showing")
    mode = next(r for r in at.radio if r.label == "Tipo de descubrimiento")
    require(mode.value == "Unicornio explosivo", f"the button must open straight on the explosive view, found {mode.value!r}")
    require("Calidad fundamental" in mode.options, "the quality view must still be one click away on that screen")


def test_quality_view_is_still_reachable_and_a_second_visit_reopens_explosive() -> None:
    at = home()
    button(at, "home_stocks").click().run()
    next(r for r in at.radio if r.label == "Tipo de descubrimiento").set_value("Calidad fundamental").run()
    require(not at.exception, f"quality view crashed: {[e.value[:100] for e in at.exception]}")
    require(next(r for r in at.radio if r.label == "Tipo de descubrimiento").value == "Calidad fundamental", "the person can switch")
    at.session_state["screen"] = "home"
    at.run()
    button(at, "home_stocks").click().run()
    require(next(r for r in at.radio if r.label == "Tipo de descubrimiento").value == "Unicornio explosivo", "from the home it always opens on the explosive view again")


def test_blocked_data_path_still_uses_the_status_view() -> None:
    import app_v2_37 as app

    source = inspect.getsource(app.main)
    require("render_home_status(data); st.error(" in source, "when data is blocked the detailed status view is what explains why")
    require(callable(app.render_home_status), "the former home survives as the status view")


CASES = [
    test_home_is_exactly_two_big_buttons,
    test_crypto_is_visible_but_disabled,
    test_stocks_button_opens_the_unicornios_screen,
    test_quality_view_is_still_reachable_and_a_second_visit_reopens_explosive,
    test_blocked_data_path_still_uses_the_status_view,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.48A home two buttons QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
