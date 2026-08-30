#!/usr/bin/env python3
"""Offline QA for the resumable EODHD price pilot downloader.

No network calls and no real credentials are used anywhere in this file: the
EODHD API is mocked out entirely via unittest.mock, and the "token" used is a
throwaway fixture string, never the real SCOUT_FINANCE_EODHD_API_TOKEN value.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/download_eodhd_price_pilot_v2_33d.py"
TOKEN_ENV = "SCOUT_FINANCE_EODHD_API_TOKEN"
FIXTURE_TOKEN = "test-fixture-token-not-real"  # never the real credential

FIELDS = ["pilot_id", "ticker", "exchange", "provider_symbol", "provider_symbol_status"]


def module():
    spec = importlib.util.spec_from_file_location("download_eodhd_price_pilot_v2_33d", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_sample(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run(mod, argv: list[str], env: dict[str, str]) -> tuple[int, str]:
    old_argv, old_environ = sys.argv, dict(os.environ)
    os.environ.clear()
    os.environ.update(env)
    sys.argv = ["download_eodhd_price_pilot_v2_33d.py", *argv]
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = mod.main()
    except SystemExit as exc:
        code = exc.code
    finally:
        sys.argv = old_argv
        os.environ.clear()
        os.environ.update(old_environ)
    return code, buf.getvalue()


def csv_payload(rows: list[tuple[str, ...]]) -> str:
    header = "Date,Open,High,Low,Close,Adjusted_close,Volume"
    body = "\n".join(",".join(row) for row in rows)
    return header + "\n" + body + "\n"


def fake_response(text: str):
    return io.BytesIO(text.encode("utf-8"))


def test_blocked_without_execute():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P001", "ticker": "AAA", "exchange": "NASDAQ", "provider_symbol": "AAA.US", "provider_symbol_status": "resolved_deterministic"}])
        code, out = run(mod, [str(sample), str(tmp_path / "out")], {TOKEN_ENV: FIXTURE_TOKEN})
    assert code == 2 and "BLOCKED" in out and "--execute" in out


def test_blocked_without_token():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P001", "ticker": "AAA", "exchange": "NASDAQ", "provider_symbol": "AAA.US", "provider_symbol_status": "resolved_deterministic"}])
        code, out = run(mod, [str(sample), str(tmp_path / "out"), "--execute"], {})
    assert code == 2 and "BLOCKED" in out and TOKEN_ENV in out


def test_blocked_on_ambiguous_symbols():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [
            {"pilot_id": "P001", "ticker": "AAA", "exchange": "NASDAQ", "provider_symbol": "AAA.US", "provider_symbol_status": "resolved_deterministic"},
            {"pilot_id": "P002", "ticker": "BBB", "exchange": "CBOE_EUROPE", "provider_symbol": "", "provider_symbol_status": "unresolved"},
        ])
        code, out = run(mod, [str(sample), str(tmp_path / "out"), "--execute"], {TOKEN_ENV: FIXTURE_TOKEN})
    payload = json.loads(out.strip().splitlines()[-1])
    assert code == 2 and payload["status"] == "BLOCKED" and payload["reason"] == "provider_symbols_unresolved" and payload["rows"] == 1


def test_accepts_resolved_and_resolved_deterministic_and_writes_atomically():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        sample = tmp_path / "sample.csv"
        write_sample(sample, [
            {"pilot_id": "P001", "ticker": "AAA", "exchange": "NASDAQ", "provider_symbol": "AAA.US", "provider_symbol_status": "resolved_deterministic"},
            {"pilot_id": "P002", "ticker": "BBB", "exchange": "NASDAQ", "provider_symbol": "BBB.US", "provider_symbol_status": "resolved"},
        ])
        payload = csv_payload([("2026-01-02", "1.0", "1.2", "0.9", "1.1", "1.1", "1000")])
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = payload.encode("utf-8")
            code, out = run(mod, [str(sample), str(out_dir), "--execute"], {TOKEN_ENV: FIXTURE_TOKEN})
        report = json.loads(out.strip().splitlines()[-1])
        assert code == 0
        assert report["status"] == "COMPLETED"
        assert report["collected"] == 2 and report["failed"] == 0
        assert (out_dir / "P001.json").exists() and (out_dir / "P002.json").exists()
        assert not list(out_dir.glob("*.tmp")) and not list(out_dir.glob("*.json.tmp"))
        written = json.loads((out_dir / "P001.json").read_text(encoding="utf-8"))
        assert written["pilot"]["pilot_id"] == "P001" and len(written["prices"]) == 1


def test_skips_existing_files():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        (out_dir / "P001.json").write_text(json.dumps({"pilot": {"pilot_id": "P001"}, "prices": []}), encoding="utf-8")
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P001", "ticker": "AAA", "exchange": "NASDAQ", "provider_symbol": "AAA.US", "provider_symbol_status": "resolved_deterministic"}])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, [str(sample), str(out_dir), "--execute"], {TOKEN_ENV: FIXTURE_TOKEN})
            assert not urlopen.called, "must not call the network for an existing file"
        report = json.loads(out.strip().splitlines()[-1])
        assert code == 0 and report["skipped_existing"] == 1 and report["collected"] == 0


def test_continues_after_http_error_and_omits_url_and_token():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        sample = tmp_path / "sample.csv"
        write_sample(sample, [
            {"pilot_id": "P001", "ticker": "AAA", "exchange": "NASDAQ", "provider_symbol": "AAA.US", "provider_symbol_status": "resolved_deterministic"},
            {"pilot_id": "P002", "ticker": "BBB", "exchange": "NASDAQ", "provider_symbol": "BBB.US", "provider_symbol_status": "resolved_deterministic"},
        ])
        good_payload = csv_payload([("2026-01-02", "1.0", "1.2", "0.9", "1.1", "1.1", "1000")])

        def side_effect(request, timeout=30):
            if "AAA" in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 404, "Not Found", hdrs=None, fp=None)
            return mock.MagicMock(__enter__=mock.MagicMock(return_value=mock.MagicMock(read=lambda: good_payload.encode("utf-8"))), __exit__=mock.MagicMock(return_value=False))

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, [str(sample), str(out_dir), "--execute"], {TOKEN_ENV: FIXTURE_TOKEN})
        report = json.loads(out.strip().splitlines()[-1])
        assert code == 1
        assert report["status"] == "COMPLETED_WITH_ERRORS"
        assert report["collected"] == 1 and report["failed"] == 1
        assert (out_dir / "P002.json").exists() and not (out_dir / "P001.json").exists()
        failure = report["failures"][0]
        assert failure["pilot_id"] == "P001" and failure["error_type"] == "HTTPError" and failure["http_status"] == 404
        raw_report_text = json.dumps(report)
        assert FIXTURE_TOKEN not in raw_report_text
        assert "http://" not in raw_report_text and "https://" not in raw_report_text


def test_continues_after_invalid_schema_response():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        sample = tmp_path / "sample.csv"
        write_sample(sample, [
            {"pilot_id": "P001", "ticker": "AAA", "exchange": "NASDAQ", "provider_symbol": "AAA.US", "provider_symbol_status": "resolved_deterministic"},
            {"pilot_id": "P002", "ticker": "BBB", "exchange": "NASDAQ", "provider_symbol": "BBB.US", "provider_symbol_status": "resolved_deterministic"},
        ])
        bad_payload = "not,the,expected,columns\n1,2,3,4\n"
        good_payload = csv_payload([("2026-01-02", "1.0", "1.2", "0.9", "1.1", "1.1", "1000")])

        def side_effect(request, timeout=30):
            payload = bad_payload if "AAA" in request.full_url else good_payload
            return mock.MagicMock(__enter__=mock.MagicMock(return_value=mock.MagicMock(read=lambda: payload.encode("utf-8"))), __exit__=mock.MagicMock(return_value=False))

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, [str(sample), str(out_dir), "--execute"], {TOKEN_ENV: FIXTURE_TOKEN})
        report = json.loads(out.strip().splitlines()[-1])
        assert code == 1 and report["status"] == "COMPLETED_WITH_ERRORS"
        assert report["collected"] == 1 and report["failed"] == 1
        assert report["failures"][0]["pilot_id"] == "P001" and report["failures"][0]["error_type"] == "ValueError"


def test_report_shape_has_no_ranking_or_scoring_fields():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P001", "ticker": "AAA", "exchange": "NASDAQ", "provider_symbol": "AAA.US", "provider_symbol_status": "resolved_deterministic"}])
        payload = csv_payload([("2026-01-02", "1.0", "1.2", "0.9", "1.1", "1.1", "1000")])
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = payload.encode("utf-8")
            code, out = run(mod, [str(sample), str(out_dir), "--execute"], {TOKEN_ENV: FIXTURE_TOKEN})
        report = json.loads(out.strip().splitlines()[-1])
        assert set(report) == {"status", "input_assets", "collected", "skipped_existing", "failed", "failures"}
        assert code == 0


CASES = [
    test_blocked_without_execute,
    test_blocked_without_token,
    test_blocked_on_ambiguous_symbols,
    test_accepts_resolved_and_resolved_deterministic_and_writes_atomically,
    test_skips_existing_files,
    test_continues_after_http_error_and_omits_url_and_token,
    test_continues_after_invalid_schema_response,
    test_report_shape_has_no_ranking_or_scoring_fields,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.33D1-downloader/fail-closed/resumable/atomic-write/no-network/no-real-token/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
