#!/usr/bin/env python3
"""QA for v2.49E: the screen warns when a search would read a partial trading day, and says so when the data on screen
was saved during the US session. The session clock is unit-tested on exact boundaries (summer and winter time, weekends,
the March/November changes); the screen is the real app through AppTest with a fake market provider, a temporary data
folder and a fake clock (SCOUT_FINANCE_FAKE_NOW_UTC), so nothing depends on when this runs. No network."""
from __future__ import annotations

import logging
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
logging.disable(logging.CRITICAL)

from qa_explosive_search_page_v2_49a import Sandbox, button, open_explosive_page, require  # noqa: E402

OVERLAY = "user_explosive_unicorn_market_overlay_v2_45b.csv"


def utc(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


def test_session_clock_boundaries_in_summer_time() -> None:
    import app_v2_37 as app

    cases = {
        "2026-10-16T13:29": False,  # Friday 09:29 EDT
        "2026-10-16T13:30": True,   # 09:30
        "2026-10-16T19:34": True,   # 15:34: the search that read a partial day
        "2026-10-16T19:59": True,
        "2026-10-16T20:00": False,  # 16:00 closes
        "2026-10-16T22:44": False,  # 18:44: after the close
        "2026-10-17T15:00": False,  # Saturday
        "2026-10-18T15:00": False,  # Sunday
        "2026-10-19T14:00": True,   # Monday 10:00
    }
    for stamp, expected in cases.items():
        require(app.us_market_session_open(utc(stamp)) is expected, f"{stamp}Z should be {expected}")


def test_session_clock_boundaries_in_winter_time() -> None:
    import app_v2_37 as app

    cases = {"2026-12-07T14:29": False, "2026-12-07T14:30": True, "2026-12-07T20:59": True, "2026-12-07T21:00": False}
    for stamp, expected in cases.items():
        require(app.us_market_session_open(utc(stamp)) is expected, f"{stamp}Z (EST) should be {expected}")


def test_daylight_saving_changes_on_the_right_second_sunday_and_first_sunday() -> None:
    import app_v2_37 as app

    require(app.us_eastern_offset_hours(utc("2026-03-08T06:59")) == -5, "just before 2:00 EST on the second Sunday of March")
    require(app.us_eastern_offset_hours(utc("2026-03-08T07:00")) == -4, "at 2:00 EST it becomes EDT")
    require(app.us_eastern_offset_hours(utc("2026-11-01T05:59")) == -4, "just before 2:00 EDT on the first Sunday of November")
    require(app.us_eastern_offset_hours(utc("2026-11-01T06:00")) == -5, "at 2:00 EDT it becomes EST")
    require(app.us_eastern_offset_hours(utc("2027-03-14T07:00")) == -4, "2027: second Sunday of March is the 14th")


def test_the_warning_is_worded_as_a_possibility_and_names_the_close() -> None:
    import app_v2_37 as app

    text = app.us_session_warning(utc("2026-10-16T19:34"))
    require("puede estar en sesión" in text and "volumen de hoy es parcial" in text and "festivos" in text, text)
    require("a partir de las " in text and "hora de este equipo" in text, "it tells when to search instead")


def test_the_warning_shows_only_during_the_session() -> None:
    with Sandbox():
        os.environ["SCOUT_FINANCE_FAKE_NOW_UTC"] = "2026-10-16T19:34:00+00:00"  # Friday 15:34 New York
        at = open_explosive_page()
        require(not at.exception, f"crashed: {[e.value[:100] for e in at.exception]}")
        require(any("puede estar en sesión" in w.value for w in at.warning), [w.value[:60] for w in at.warning])
        require("explosive_search" in [b.key for b in at.button], "the search stays available: it is a warning, not a block")
        os.environ["SCOUT_FINANCE_FAKE_NOW_UTC"] = "2026-10-17T12:00:00+00:00"  # Saturday
        at = open_explosive_page()
        require(not any("puede estar en sesión" in w.value for w in at.warning), "no warning when the market is closed")


def test_the_data_label_says_when_it_was_saved_during_the_session() -> None:
    with Sandbox() as box:
        at = open_explosive_page()
        button(at, "explosive_search").click().run()
        overlay = box.data_dir / OVERLAY
        require(overlay.exists(), "the search saved the cache")

        def label_after_touching(stamp: str) -> str:
            moment = utc(stamp).timestamp()
            os.utime(overlay, (moment, moment))
            at.run()
            require(not at.exception, f"crashed: {[e.value[:100] for e in at.exception]}")
            return " ".join(m.value for m in at.markdown)

        during = label_after_touching("2026-10-16T19:34")
        require("Datos de mercado: Yahoo Finance, guardados el" in during and "con el mercado de EE. UU. en sesión" in during, "a save made at 15:34 New York is flagged as partial-day data")
        after = label_after_touching("2026-10-16T22:44")
        require("Datos de mercado: Yahoo Finance, guardados el" in after and "con el mercado de EE. UU. en sesión" not in after, "a save made after the close is not flagged")


CASES = [
    test_session_clock_boundaries_in_summer_time,
    test_session_clock_boundaries_in_winter_time,
    test_daylight_saving_changes_on_the_right_second_sunday_and_first_sunday,
    test_the_warning_is_worded_as_a_possibility_and_names_the_close,
    test_the_warning_shows_only_during_the_session,
    test_the_data_label_says_when_it_was_saved_during_the_session,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49E US session warning QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
