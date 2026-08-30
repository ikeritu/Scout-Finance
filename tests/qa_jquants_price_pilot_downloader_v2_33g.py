#!/usr/bin/env python3
"""Offline QA for the J-Quants resolve/download scripts (v2.33G JPX pilot).

No network calls and no real credentials: the J-Quants API is mocked via
unittest.mock, and the "key" used is a throwaway fixture string, never the
real SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN value. time.sleep is patched out so
the 429 backoff path is exercised without actually waiting.
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
RESOLVE_SCRIPT = ROOT / "scripts/resolve_jquants_price_pilot_v2_33g.py"
DOWNLOAD_SCRIPT = ROOT / "scripts/download_jquants_price_pilot_v2_33g.py"
API_KEY_ENV = "SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN"
FIXTURE_KEY = "test-fixture-key-not-real"

SAMPLE_FIELDS = ["pilot_id", "row_number", "ticker", "company_name", "exchange", "country", "source_provider",
                 "instrument_type", "type_bucket_v2_33a", "provider_symbol_status", "provider_symbol",
                 "eligibility_preflight_status", "eligibility_preflight_reasons", "price_collection_status",
                 "provider_symbol_reason"]


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_sample(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SAMPLE_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in SAMPLE_FIELDS})


def jpx_row(pilot_id: str, ticker: str, company_name: str) -> dict:
    return {"pilot_id": pilot_id, "ticker": ticker, "company_name": company_name, "exchange": "JPX"}


def run(mod, argv: list[str], env: dict[str, str]) -> tuple[int, str]:
    old_argv, old_environ = sys.argv, dict(os.environ)
    os.environ.clear()
    os.environ.update(env)
    sys.argv = [mod.__name__, *argv]
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


def http_error(code: int, body: str = "{}"):
    return urllib.error.HTTPError("https://api.jquants.com/v2/x", code, "err", hdrs=None, fp=io.BytesIO(body.encode()))


def extract_last_json(out: str) -> dict:
    text = out.split("PASS:")[0]
    start = text.rindex("\n{\n") + 1 if "\n{\n" in text else text.index("{")
    return json.loads(text[start:])


def fake_urlopen_response(payload: dict):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_resolve_blocked_without_key():
    mod = module(RESOLVE_SCRIPT, "resolve_jquants_v2_33g")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [jpx_row("P143", "1301", "KYOKUYO CO.,LTD.")])
        code, out = run(mod, [str(sample), str(tmp_path / "out")], {})
    assert code == 2 and "BLOCKED" in out and API_KEY_ENV in out


def test_resolve_exact_match_and_name_mismatch_and_atomic_write():
    mod = module(RESOLVE_SCRIPT, "resolve_jquants_v2_33g_2")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        sample = tmp_path / "sample.csv"
        write_sample(sample, [
            jpx_row("P143", "1301", "KYOKUYO CO.,LTD."),
            jpx_row("P999", "9999", "WRONG NAME CORP"),
        ])
        responses = {
            "1301": {"data": [{"Date": "2026-06-08", "Code": "13010", "CoNameEn": "KYOKUYO CO.,LTD."}]},
            "9999": {"data": [{"Date": "2026-06-08", "Code": "99990", "CoNameEn": "SOME OTHER COMPANY"}]},
        }

        def side_effect(request, timeout=20):
            code = request.full_url.split("code=")[1]
            return fake_urlopen_response(responses[code])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, [str(sample), str(out_dir)], {API_KEY_ENV: FIXTURE_KEY})
        report = extract_last_json(out)
        assert code == 0
        assert report["resolved"] == 1 and report["unresolved"] == 1
        csv_path = out_dir / "jquants_symbol_resolution_v2_33g.csv"
        assert csv_path.exists() and not list(out_dir.glob("*.csv.tmp"))
        rows = {r["pilot_id"]: r for r in csv.DictReader(csv_path.open(encoding="utf-8"))}
        assert rows["P143"]["provider_symbol"] == "13010"
        assert rows["P999"]["status"] == "unresolved" and rows["P999"]["reason"] == "name_mismatch_requires_manual_review"


def test_resolve_retries_on_429_then_succeeds():
    mod = module(RESOLVE_SCRIPT, "resolve_jquants_v2_33g_3")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [jpx_row("P143", "1301", "KYOKUYO CO.,LTD.")])
        calls = {"n": 0}

        def side_effect(request, timeout=20):
            calls["n"] += 1
            if calls["n"] == 1:
                raise http_error(429, '{"message": "Rate limit exceeded. Please try again later."}')
            return fake_urlopen_response({"data": [{"Date": "2026-06-08", "Code": "13010", "CoNameEn": "KYOKUYO CO.,LTD."}]})

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep") as sleep_mock:
            code, out = run(mod, [str(sample), str(tmp_path / "out")], {API_KEY_ENV: FIXTURE_KEY})
        report = extract_last_json(out)
        assert code == 0 and report["resolved"] == 1 and calls["n"] == 2
        assert any(c.args and c.args[0] == mod.RATE_LIMIT_BACKOFF_SECONDS for c in sleep_mock.call_args_list)


def test_download_blocked_without_execute_and_without_key():
    mod = module(DOWNLOAD_SCRIPT, "download_jquants_v2_33g")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        resolved_csv = tmp_path / "resolved.csv"
        with resolved_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["pilot_id", "status", "provider_symbol"])
            writer.writeheader()
            writer.writerow({"pilot_id": "P143", "status": "resolved_jquants_master_exact_match", "provider_symbol": "13010"})

        code, out = run(mod, [str(resolved_csv), str(tmp_path / "out")], {API_KEY_ENV: FIXTURE_KEY})
        assert code == 2 and "BLOCKED" in out and "--execute" in out

        code, out = run(mod, [str(resolved_csv), str(tmp_path / "out"), "--execute"], {})
        assert code == 2 and "BLOCKED" in out and API_KEY_ENV in out


def test_download_skips_existing_writes_atomically_and_omits_key():
    mod = module(DOWNLOAD_SCRIPT, "download_jquants_v2_33g_2")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        (out_dir / "P001.json").write_text(json.dumps({"pilot": {"pilot_id": "P001"}, "prices": []}), encoding="utf-8")

        resolved_csv = tmp_path / "resolved.csv"
        with resolved_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["pilot_id", "status", "provider_symbol"])
            writer.writeheader()
            writer.writerow({"pilot_id": "P001", "status": "resolved_jquants_master_exact_match", "provider_symbol": "11110"})
            writer.writerow({"pilot_id": "P002", "status": "resolved_jquants_master_exact_match", "provider_symbol": "22220"})

        bars_payload = {"data": [{"Date": "2026-06-08", "Code": "22220", "O": 100.0, "H": 101.0, "L": 99.0, "C": 100.5, "Vo": 1000}]}

        with mock.patch("urllib.request.urlopen") as urlopen, mock.patch("time.sleep"):
            urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(bars_payload).encode("utf-8")
            code, out = run(mod, [str(resolved_csv), str(out_dir), "--execute"], {API_KEY_ENV: FIXTURE_KEY})
        report = json.loads(out.strip().splitlines()[-1])
        assert code == 0 and report["collected"] == 1 and report["skipped_existing"] == 1
        assert not list(out_dir.glob("*.json.tmp"))
        assert FIXTURE_KEY not in json.dumps(report)
        assert "https://" not in json.dumps(report)


def test_download_continues_after_http_error_with_no_url_or_key_leak():
    mod = module(DOWNLOAD_SCRIPT, "download_jquants_v2_33g_3")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        resolved_csv = tmp_path / "resolved.csv"
        with resolved_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["pilot_id", "status", "provider_symbol"])
            writer.writeheader()
            writer.writerow({"pilot_id": "P001", "status": "resolved_jquants_master_exact_match", "provider_symbol": "11110"})
            writer.writerow({"pilot_id": "P002", "status": "resolved_jquants_master_exact_match", "provider_symbol": "22220"})

        good_payload = {"data": [{"Date": "2026-06-08", "Code": "22220", "O": 100.0, "H": 101.0, "L": 99.0, "C": 100.5, "Vo": 1000}]}

        def side_effect(request, timeout=30):
            if "11110" in request.full_url:
                raise http_error(404, "{}")
            return fake_urlopen_response(good_payload)

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, [str(resolved_csv), str(out_dir), "--execute"], {API_KEY_ENV: FIXTURE_KEY})
        report = json.loads(out.strip().splitlines()[-1])
        assert code == 1 and report["status"] == "COMPLETED_WITH_ERRORS"
        assert report["collected"] == 1 and report["failed"] == 1
        failure = report["failures"][0]
        assert failure["pilot_id"] == "P001" and failure["error_type"] == "HTTPError" and failure["http_status"] == 404
        raw = json.dumps(report)
        assert FIXTURE_KEY not in raw and "https://" not in raw


CASES = [
    test_resolve_blocked_without_key,
    test_resolve_exact_match_and_name_mismatch_and_atomic_write,
    test_resolve_retries_on_429_then_succeeds,
    test_download_blocked_without_execute_and_without_key,
    test_download_skips_existing_writes_atomically_and_omits_key,
    test_download_continues_after_http_error_with_no_url_or_key_leak,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.33G-jquants-downloader/fail-closed/exact-match-only/429-backoff/atomic-write/no-network/no-real-key")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
