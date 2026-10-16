#!/usr/bin/env python3
"""Regression QA for v2.47C: the Unicornios screen must actually RUN in every view and both discovery
modes. Unlike the source-text QA scripts, this executes the real Streamlit app headlessly (Streamlit's own
AppTest) and fails on any exception. It exists because two crashes shipped that no source-text check could
see: a NameError in "Fichas completas" (v2.46B) and a StreamlitDuplicateElementKey on the median chart (#4)
that hit most views of "Calidad fundamental". No network, no writes."""
from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

from streamlit.testing.v1 import AppTest  # noqa: E402


def fresh_unicorns_screen() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app_v2_37.py"), default_timeout=180)
    at.session_state["screen"] = "global_unicorns"
    at.run()
    return at


def errors(at: AppTest) -> list[str]:
    return [exc.value.splitlines()[0][:140] if exc.value else "exception" for exc in at.exception]


def radio(at: AppTest, label: str):
    return next(r for r in at.radio if r.label == label)


def test_every_view_of_calidad_fundamental_renders_without_exceptions() -> None:
    at = fresh_unicorns_screen()
    require(not errors(at), f"default view crashed: {errors(at)}")
    views = list(radio(at, "Vista").options)
    require(len(views) >= 6, f"expected the six views, found {views}")
    for view in views:
        radio(at, "Vista").set_value(view).run()
        require(not errors(at), f"view {view!r} crashed: {errors(at)}")


def test_unicornio_explosivo_renders_without_exceptions() -> None:
    at = fresh_unicorns_screen()
    radio(at, "Tipo de descubrimiento").set_value("Unicornio explosivo").run()
    require(not errors(at), f"explosive mode crashed: {errors(at)}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


CASES = [
    test_every_view_of_calidad_fundamental_renders_without_exceptions,
    test_unicornio_explosivo_renders_without_exceptions,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.47C unicorns screen runs in every view QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
