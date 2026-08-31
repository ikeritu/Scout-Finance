#!/usr/bin/env python3
"""Offline QA for the TWSE official STOCK_DAY downloader (v2.33I). No
network calls: the endpoint is mocked. TWSE requires no account or API key
for this public endpoint, so there is no credential to protect -- these
tests verify the fail-closed gate, ROC-date conversion, number parsing,
resumability, atomic writes, and month-level error continuation.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
import tempfile
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/download_twse_opendata_price_pilot_v2_33i.py"
SAMPLE_FIELDS = ["pilot_id", "ticker", "company_name", "exchange"]


def module():
    spec = importlib.util.spec_from_file_location("download_twse_opendata_price_pilot_v2_33i", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_sample(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SAMPLE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run(mod, argv: list[str]) -> tuple[int, str]:
    old_argv = sys.argv
    sys.argv = [mod.__name__, *argv]
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = mod.main()
    except SystemExit as exc:
        code = exc.code
    finally:
        sys.argv = old_argv
    return code, buf.getvalue()


def month_payload(rows: list[list[str]]) -> dict:
    return {"stat": "OK", "data": rows}


def fake_response(payload: dict):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_roc_date_and_number_parsing():
    mod = module()
    assert mod.roc_to_iso(" 99/01/04") == "2010-01-04"
    assert mod.roc_to_iso("115/06/01") == "2026-06-01"
    assert mod.parse_number("35,557,711") == 35557711.0
    assert mod.parse_number("--") is None
    assert mod.parse_number("") is None


def test_blocked_without_execute():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P016", "ticker": "1101.TW", "company_name": "X", "exchange": "TWSE"}])
        code, out = run(mod, [str(sample), str(tmp_path / "out")])
        assert code == 2 and "BLOCKED" in out and "--execute" in out


def test_collects_writes_atomically_and_skips_existing():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P016", "ticker": "1101.TW", "company_name": "X", "exchange": "TWSE"}])
        month = month_payload([["115/06/01", "35,557,711", "869,509,013", "24.40", "24.70", "24.20", "24.55", "+0.15", "10,973", ""]])
        with mock.patch("urllib.request.urlopen", return_value=fake_response(month)), mock.patch("time.sleep"):
            code, out = run(mod, [str(sample), str(out_dir), "--execute", "--from-date", "2026-06-01"])
        report = json.loads(out.strip())
        assert code == 0 and report["collected"] == 1 and report["failed"] == 0
        written = json.loads((out_dir / "P016.json").read_text(encoding="utf-8"))
        assert written["prices"][0]["Date"] == "2026-06-01" and written["prices"][0]["Open"] == 24.4
        assert not list(out_dir.glob("*.json.tmp"))

        # second run: must skip without calling the network again
        with mock.patch("urllib.request.urlopen") as urlopen2, mock.patch("time.sleep"):
            code2, out2 = run(mod, [str(sample), str(out_dir), "--execute", "--from-date", "2026-06-01"])
            assert not urlopen2.called
        report2 = json.loads(out2.strip())
        assert code2 == 0 and report2["skipped_existing"] == 1


def test_continues_after_single_month_http_error():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P016", "ticker": "1101.TW", "company_name": "X", "exchange": "TWSE"}])
        good_month = month_payload([["115/07/01", "1,000", "10,000", "10.0", "10.5", "9.5", "10.2", "+0.1", "5", ""]])

        def side_effect(request, timeout=30, context=None):
            if "date=20260701" in request.full_url:
                return fake_response(good_month)
            raise urllib.error.HTTPError(request.full_url, 500, "err", hdrs=None, fp=None)

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, [str(sample), str(out_dir), "--execute", "--from-date", "2026-06-01"])
        report = json.loads(out.strip())
        assert code == 1 and report["status"] == "COMPLETED_WITH_ERRORS"
        assert report["collected"] == 1  # the asset still got written from the months that succeeded
        assert any(f["error_type"] == "HTTPError" for f in report["failures"])
        written = json.loads((out_dir / "P016.json").read_text(encoding="utf-8"))
        assert len(written["prices"]) == 1 and written["prices"][0]["Date"] == "2026-07-01"


CASES = [
    test_roc_date_and_number_parsing,
    test_blocked_without_execute,
    test_collects_writes_atomically_and_skips_existing,
    test_continues_after_single_month_http_error,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.33I-twse-downloader/fail-closed/resumable/atomic-write/no-network/roc-date-parsing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
