#!/usr/bin/env python3
"""QA for v2.49H: a damaged candle file (empty, not UTF-8, unterminated quote) no longer takes the explosive page down. The
app's own cache file is set aside as `.corrupt-<timestamp>` (never silently overwritten) and the screen says there is no local
history; files in the acquisition folders are left untouched; duplicate dates are collapsed; a file with no usable rows falls
through to the next source. The real app runs through AppTest (fake provider, temporary data folder). No network."""
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

import app_v2_37 as app  # noqa: E402
from qa_explosive_search_page_v2_49a import Sandbox, card_buttons, require, searched_page  # noqa: E402

DAMAGED = {"empty": b"", "not_utf8": b"\x00\x01\xff\xfe\x00garbage", "unterminated_quote": b'Date,Open\n"unterminated,1\n'}
GOOD = "date,open,high,low,close,volume\n" + "".join(f"2026-09-{day:02d},1,2,0.5,1.5,100\n" for day in range(1, 21))


class Roots:
    """Point the loader at temporary folders: first the app cache, then an acquisition-style folder."""

    def __enter__(self) -> "Roots":
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.cache, self.other = base / "cache", base / "acquisition"
        self.cache.mkdir(); self.other.mkdir()
        self.saved = (app.EXPLOSIVE_OHLCV_CACHE_DIR, app.EXPLOSIVE_OHLCV_LOCAL_ROOTS)
        app.EXPLOSIVE_OHLCV_CACHE_DIR, app.EXPLOSIVE_OHLCV_LOCAL_ROOTS = self.cache, [self.cache, self.other]
        return self

    def __exit__(self, *exc) -> None:
        app.EXPLOSIVE_OHLCV_CACHE_DIR, app.EXPLOSIVE_OHLCV_LOCAL_ROOTS = self.saved
        self.tmp.cleanup()


def test_a_damaged_cache_file_is_set_aside_and_never_crashes() -> None:
    for name, content in DAMAGED.items():
        with Roots() as box:
            (box.cache / "AAA.csv").write_bytes(content)
            frame = app.load_explosive_candidate_ohlcv({"asset_id": "AAA"})
            require(frame.empty, f"{name}: no history is returned")
            require(not (box.cache / "AAA.csv").exists() and len(list(box.cache.glob("AAA.csv.corrupt-*"))) == 1, f"{name}: the file is set aside, not deleted")
            require((next(box.cache.glob("AAA.csv.corrupt-*"))).read_bytes() == content, f"{name}: the damaged bytes are kept as they were")


def test_the_next_source_is_used_when_the_cache_file_is_damaged() -> None:
    with Roots() as box:
        (box.cache / "AAA.csv").write_bytes(b"")
        (box.other / "AAA.csv").write_text(GOOD, encoding="utf-8")
        require(len(app.load_explosive_candidate_ohlcv({"asset_id": "AAA"})) == 20, "falls through to the acquisition folder")


def test_files_outside_the_app_cache_are_never_renamed() -> None:
    with Roots() as box:
        (box.other / "BBB.csv").write_bytes(DAMAGED["not_utf8"])
        require(app.load_explosive_candidate_ohlcv({"asset_id": "BBB"}).empty, "a damaged acquisition file is skipped")
        require((box.other / "BBB.csv").exists() and not list(box.other.glob("*.corrupt-*")), "and left exactly where it was")


def test_duplicate_dates_are_collapsed_and_a_file_without_usable_rows_falls_through() -> None:
    with Roots() as box:
        (box.cache / "CCC.csv").write_text(GOOD + "2026-09-20,9,9,9,9,999\n", encoding="utf-8")
        frame = app.load_explosive_candidate_ohlcv({"asset_id": "CCC"})
        require(len(frame) == 20 and frame["Date"].is_unique and float(frame["Close"].iloc[-1]) == 9.0, "one bar per date, the last one wins")
        (box.cache / "DDD.csv").write_text("date,open,high,low,close\nnot-a-date,x,y,z,w\n", encoding="utf-8")
        (box.other / "DDD.csv").write_text(GOOD, encoding="utf-8")
        require(len(app.load_explosive_candidate_ohlcv({"asset_id": "DDD"})) == 20, "no usable rows: the next source is tried")


def test_the_real_page_survives_a_damaged_candle_file_on_the_dashboard_and_the_candidate_page() -> None:
    with Sandbox() as box:
        at = searched_page()
        cache = box.data_dir / "explosive_ohlcv_cache_v2_46a"
        files = sorted(cache.glob("*.csv"))
        require(len(files) >= 9, f"the search saved candle files: {len(files)}")
        kinds = list(DAMAGED.values())
        for index, path in enumerate(files):
            path.write_bytes(kinds[index % len(kinds)])  # every kind of damage, including the featured candidate and the first cards
        at.run()
        require(not at.exception, f"the dashboard crashed with damaged candle files: {[e.value[:120] for e in at.exception]}")
        require(any("No hay histórico OHLCV local" in i.value for i in at.info), "the screen says there is no local history for the featured candidate")
        card_buttons(at)[0].click().run()
        require(not at.exception, f"the candidate page crashed: {[e.value[:120] for e in at.exception]}")
        require([t.label for t in at.tabs] == ["Resumen", "Datos", "Gráfico"], "the candidate page still opens with its tabs")
        require(len(list(cache.glob("*.csv.corrupt-*"))) >= 1, "the damaged files were set aside")


CASES = [
    test_a_damaged_cache_file_is_set_aside_and_never_crashes,
    test_the_next_source_is_used_when_the_cache_file_is_damaged,
    test_files_outside_the_app_cache_are_never_renamed,
    test_duplicate_dates_are_collapsed_and_a_file_without_usable_rows_falls_through,
    test_the_real_page_survives_a_damaged_candle_file_on_the_dashboard_and_the_candidate_page,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49H explosive OHLCV hardening QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
