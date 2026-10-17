#!/usr/bin/env python3
"""QA for v2.49D (frontend review FE-04, FE-09, FE-10): a broken market cache must not take the page down and an
interrupted write must not leave one behind; the candlestick band is labelled for what it is; every candidate's
button has its own name. Real app through AppTest with a fake market provider and a temporary data folder (the
helpers of the v2.49A QA); the atomic-write check is a direct unit test. No network."""
from __future__ import annotations

import logging
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
logging.disable(logging.CRITICAL)

import pandas as pd  # noqa: E402

import qa_explosive_search_page_v2_49a as base  # noqa: E402
from qa_explosive_search_page_v2_49a import Sandbox, button, card_buttons, open_explosive_page, require, searched_page  # noqa: E402

OVERLAY = "user_explosive_unicorn_market_overlay_v2_45b.csv"


def search_over_a_damaged_cache(content: bytes) -> None:
    with Sandbox() as box:
        (box.data_dir / OVERLAY).write_bytes(content)
        at = open_explosive_page()
        button(at, "explosive_search").click().run()
        require(not at.exception, f"a damaged cache must not crash the search: {[e.value.splitlines()[0][:100] for e in at.exception]}")
        require(len(card_buttons(at)) == 9, "the search still produces results")
        aside = list(box.data_dir.glob(OVERLAY + ".corrupt-*"))
        require(len(aside) == 1 and aside[0].read_bytes() == content, "the damaged file is set aside untouched, never silently overwritten")
        rebuilt = pd.read_csv(box.data_dir / OVERLAY)
        require(len(rebuilt) > 100, f"the cache is rebuilt by the search: {len(rebuilt)} rows")


def test_an_empty_cache_file_does_not_break_the_search() -> None:
    search_over_a_damaged_cache(b"")


def test_a_cache_file_with_bytes_that_are_not_utf8_does_not_break_the_search() -> None:
    search_over_a_damaged_cache(b"\xff\xfe\x00\x01\x80garbage\x00")


def test_a_header_only_cache_is_just_an_empty_cache() -> None:
    with Sandbox() as box:
        (box.data_dir / OVERLAY).write_text("asset_id,ticker\n", encoding="utf-8")
        at = open_explosive_page()
        button(at, "explosive_search").click().run()
        require(not at.exception and len(card_buttons(at)) == 9, "header-only file works")
        require(not list(box.data_dir.glob(OVERLAY + ".corrupt-*")), "a readable file is not set aside")


def test_an_interrupted_write_never_leaves_a_truncated_cache() -> None:
    import app_v2_37 as app

    saved_path = app.EXPLOSIVE_UNICORN_OVERLAY_PATH
    real_to_csv = pd.DataFrame.to_csv
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / OVERLAY
        app.EXPLOSIVE_UNICORN_OVERLAY_PATH = target
        try:
            good = pd.DataFrame({"asset_id": ["A", "B"], "ticker": ["AAA", "BBB"]})
            app.save_explosive_overlay(good)
            before = target.read_bytes()

            def dying_to_csv(self, path_or_buf=None, *args, **kwargs):
                Path(path_or_buf).write_bytes(b"asset_id,tic")  # half a file, then the process "dies"
                raise OSError("disk full")

            pd.DataFrame.to_csv = dying_to_csv
            try:
                app.save_explosive_overlay(pd.DataFrame({"asset_id": ["C"], "ticker": ["CCC"]}))
                raise AssertionError("the failure must surface")
            except OSError:
                pass
            finally:
                pd.DataFrame.to_csv = real_to_csv
            require(target.read_bytes() == before, "the previous cache is untouched after a failed save")
            require(not list(Path(tmp).glob("*.tmp")), "no temporary file is left behind")
            require(len(app.load_explosive_overlay()) == 2, "and it still loads")
        finally:
            app.EXPLOSIVE_UNICORN_OVERLAY_PATH = saved_path
            pd.DataFrame.to_csv = real_to_csv


def test_the_band_is_labelled_for_what_it_is() -> None:
    import app_v2_37 as app

    dates = pd.bdate_range("2026-08-01", periods=40)
    closes = [10 + i * 0.1 + (i % 4) * 0.2 for i in range(40)]
    ohlcv = pd.DataFrame({"Date": dates, "Open": closes, "High": [c + 0.5 for c in closes], "Low": [c - 0.5 for c in closes], "Close": closes, "Volume": 1000})
    names = [trace.name or "" for trace in app.explosive_candlestick_figure(ohlcv, "T").data]
    require(not any("95" in name for name in names), f"no trace may claim a 95% band: {names}")
    require(sum("desv. residuales" in name for name in names) == 2, f"both band lines say what they are: {names}")
    import inspect

    require("No es un intervalo de confianza ni de predicción" in inspect.getsource(app.render_explosive_candidate_candlestick), "the caption says it is descriptive")


def test_every_candidate_button_has_its_own_name() -> None:
    with Sandbox():
        at = searched_page()
        labels = [b.label for b in card_buttons(at)]
        require(len(labels) == 9 and len(set(labels)) == 9, f"nine different names expected: {labels}")
        require(all(label.startswith("Ver ficha completa · ") for label in labels), labels)


CASES = [
    test_an_empty_cache_file_does_not_break_the_search,
    test_a_cache_file_with_bytes_that_are_not_utf8_does_not_break_the_search,
    test_a_header_only_cache_is_just_an_empty_cache,
    test_an_interrupted_write_never_leaves_a_truncated_cache,
    test_the_band_is_labelled_for_what_it_is,
    test_every_candidate_button_has_its_own_name,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49D explosive hardening QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
