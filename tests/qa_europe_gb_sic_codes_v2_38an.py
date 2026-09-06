#!/usr/bin/env python3
"""Offline QA for the v2.38AN GB SIC codes fetcher. No real network calls,
no real credential -- FIXTURE_KEY is a throwaway string, never the real
SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY value."""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/fetch_europe_gb_sic_codes_v2_38an.py"
CREDENTIAL_ENV = "SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY"
FIXTURE_KEY = "test-fixture-key-not-real"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_lookup_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "resolved_company_name", "isin", "lookup_status", "company_number"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


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


def fake_response(payload: dict):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_dry_run_reports_eligible_without_network():
    mod = module("gb_sic_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [{"asset_id": "U1", "ticker": "GUI", "resolved_company_name": "DIAGEO PLC", "isin": "GB0002374006", "lookup_status": "resolved", "company_number": "00023307"}])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")], {})
        assert code == 0 and urlopen.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_companies"] == 1


def test_execute_without_credential_is_blocked():
    mod = module("gb_sic_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [{"asset_id": "U1", "ticker": "GUI", "resolved_company_name": "DIAGEO PLC", "isin": "GB0002374006", "lookup_status": "resolved", "company_number": "00023307"}])
        code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {})
        assert code == 2 and json.loads(out)["reason"] == "credential_missing"


def test_calls_profile_endpoint_not_search_and_captures_real_sic_codes():
    """The whole point of this script: v2.38Y's search-endpoint approach
    never returns sic_codes -- confirmed live that only the PROFILE
    endpoint (/company/{number}) does. This must call that endpoint, keyed
    by company_number, and capture whatever codes come back."""
    mod = module("gb_sic_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [{"asset_id": "U1", "ticker": "GUI", "resolved_company_name": "DIAGEO PLC", "isin": "GB0002374006", "lookup_status": "resolved", "company_number": "00023307"}])

        captured_urls = []

        def side_effect(request, timeout=30):
            captured_urls.append(request.full_url)
            return fake_response({"company_name": "DIAGEO PLC", "sic_codes": ["70100"]})

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})

        assert captured_urls == ["https://api.company-information.service.gov.uk/company/00023307"]
        rows = list(csv.DictReader((root / "out" / "europe_gb_sic_codes_v2_38an.csv").open(encoding="utf-8")))
        assert rows[0]["sic_codes"] == "70100"
        assert rows[0]["sic_descriptions"] == "Activities of head offices"
        assert rows[0]["fetch_status"] == "resolved"


def test_unverified_code_stays_honestly_unknown_never_guessed():
    """A real code this project has not yet verified a description for
    must never be silently mapped to something plausible-looking -- it
    stays UNKNOWN_SIC_CODE_<code> and is listed separately for follow-up."""
    mod = module("gb_sic_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [{"asset_id": "U1", "ticker": "ZZZ", "resolved_company_name": "UNKNOWN CODE CO", "isin": "GB0000000009", "lookup_status": "resolved", "company_number": "00099999"}])

        with mock.patch("urllib.request.urlopen", side_effect=lambda request, timeout=30: fake_response({"sic_codes": ["99999"]})), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})

        report = json.loads(out.strip().splitlines()[-1])
        rows = list(csv.DictReader((root / "out" / "europe_gb_sic_codes_v2_38an.csv").open(encoding="utf-8")))
        assert rows[0]["sic_descriptions"] == "UNKNOWN_SIC_CODE_99999"
        full_report = json.loads((root / "out" / "europe_gb_sic_codes_report_v2_38an.json").read_text(encoding="utf-8"))
        assert "99999" in full_report["unknown_sic_codes_needing_description"]


def test_company_with_no_sic_codes_on_profile_is_reported_not_dropped():
    mod = module("gb_sic_5")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [{"asset_id": "U1", "ticker": "EMP", "resolved_company_name": "EMPTY SIC CO", "isin": "GB0000000008", "lookup_status": "resolved", "company_number": "00088888"}])
        with mock.patch("urllib.request.urlopen", side_effect=lambda request, timeout=30: fake_response({"sic_codes": []})), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})
        rows = list(csv.DictReader((root / "out" / "europe_gb_sic_codes_v2_38an.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "no_sic_codes_on_profile"
        assert rows[0]["sic_codes"] == ""


def test_http_error_continues_and_no_credential_leak():
    mod = module("gb_sic_6")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [
            {"asset_id": "U1", "ticker": "FAILS", "resolved_company_name": "FAILS CO", "isin": "GB0000000001", "lookup_status": "resolved", "company_number": "00000001"},
            {"asset_id": "U2", "ticker": "WORKS", "resolved_company_name": "WORKS CO", "isin": "GB0000000002", "lookup_status": "resolved", "company_number": "00000002"},
        ])
        import urllib.error

        def side_effect(request, timeout=30):
            if "00000001" in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 500, "err", hdrs=None, fp=io.BytesIO(b"{}"))
            return fake_response({"sic_codes": ["70100"]})

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})
        report = json.loads(out.strip().splitlines()[-1])
        assert report["companies_with_sic_codes"] == 1 and report["companies_error"] == 1
        assert FIXTURE_KEY not in json.dumps(report)
        assert not list((root / "out").glob("*.tmp"))


def test_only_resolved_companies_with_company_number_are_eligible():
    """A company v2.38Y never resolved (no company_number) must never be
    queried -- there is nothing to look up."""
    mod = module("gb_sic_7")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [
            {"asset_id": "U1", "ticker": "OK", "resolved_company_name": "OK CO", "isin": "GB0000000003", "lookup_status": "resolved", "company_number": "00000003"},
            {"asset_id": "U2", "ticker": "NO", "resolved_company_name": "UNRESOLVED CO", "isin": "GB0000000004", "lookup_status": "unresolved", "company_number": ""},
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")], {})
        assert json.loads(out)["eligible_companies"] == 1
        assert urlopen.call_count == 0


CASES = [
    test_dry_run_reports_eligible_without_network,
    test_execute_without_credential_is_blocked,
    test_calls_profile_endpoint_not_search_and_captures_real_sic_codes,
    test_unverified_code_stays_honestly_unknown_never_guessed,
    test_company_with_no_sic_codes_on_profile_is_reported_not_dropped,
    test_http_error_continues_and_no_credential_leak,
    test_only_resolved_companies_with_company_number_are_eligible,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AN-europe-gb-sic-codes/profile-endpoint-not-search/no-guessed-descriptions/blocked-by-default")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
