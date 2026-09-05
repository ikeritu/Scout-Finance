#!/usr/bin/env python3
"""Offline QA for the v2.38Y Companies House lookup runner (full 40-company
expansion, run against the corrected Xetra-source identity matrix). No
real network calls, no real credential -- FIXTURE_KEY is a throwaway
string, never the real SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY value.
"""
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
SCRIPT = ROOT / "scripts/run_europe_companies_house_lookup_v2_38y.py"
CREDENTIAL_ENV = "SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY"
FIXTURE_KEY = "test-fixture-key-not-real"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_resolved_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "resolved_company_name", "isin", "resolution_status"]
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
    mod = module("ch_lookup_y_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [{"asset_id": "U1", "ticker": "GUI", "resolved_company_name": "DIAGEO PLC", "isin": "GB0002374006", "resolution_status": "resolved"}])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")], {})
        assert code == 0 and urlopen.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_assets"] == 1


def test_execute_without_credential_is_blocked():
    mod = module("ch_lookup_y_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [{"asset_id": "U1", "ticker": "GUI", "resolved_company_name": "DIAGEO PLC", "isin": "GB0002374006", "resolution_status": "resolved"}])
        code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {})
        assert code == 2 and json.loads(out)["reason"] == "credential_missing"


def test_exact_active_match_resolves_and_ambiguous_does_not_at_scale():
    """Same fail-closed matching logic as v2.38V's lookup, exercised with
    more than a handful of rows to confirm it scales to the real 40-company
    input without special-casing a small N anywhere."""
    mod = module("ch_lookup_y_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        rows = [{"asset_id": f"U{i}", "ticker": f"T{i}", "resolved_company_name": f"COMPANY {i} PLC", "isin": f"GB000{i:07d}", "resolution_status": "resolved"} for i in range(12)]
        rows.append({"asset_id": "UAMB", "ticker": "AMB", "resolved_company_name": "AMBIGUOUS CO PLC", "isin": "GB0000000099", "resolution_status": "resolved"})
        write_resolved_matrix(matrix, rows)

        responses = {f"COMPANY {i} PLC": {"items": [{"title": f"COMPANY {i} PLC", "company_number": f"{1000 + i}", "company_status": "active", "date_of_creation": "2000-01-01", "sic_codes": ["62020"]}]} for i in range(12)}
        responses["AMBIGUOUS CO PLC"] = {"items": [{"title": "AMBIGUOUS CO PLC", "company_number": "111", "company_status": "active"}, {"title": "AMBIGUOUS CO PLC", "company_number": "222", "company_status": "active"}]}

        def side_effect(request, timeout=30):
            import urllib.parse
            query = request.full_url.split("q=")[1].split("&")[0]
            name = urllib.parse.unquote_plus(query)
            return fake_response(responses[name])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})

        report = json.loads(out.strip().splitlines()[-1])
        assert report["profiles_confirmed"] == 12 and report["unresolved_or_error"] == 1
        out_rows = list(csv.DictReader((root / "out" / "europe_companies_house_lookup_matrix_v2_38y.csv").open(encoding="utf-8")))
        assert len(out_rows) == 13
        by_ticker = {r["ticker"]: r for r in out_rows}
        assert by_ticker["T0"]["company_number"] == "1000" and by_ticker["T0"]["isin"] == "GB0000000000"
        assert by_ticker["AMB"]["lookup_status"] == "unresolved" and by_ticker["AMB"]["lookup_reason"] == "ambiguous_multiple_companies_match_name"
        assert not list((root / "out").glob("*.tmp"))
        assert FIXTURE_KEY not in json.dumps(report)


def test_http_error_continues_and_no_credential_leak_in_auth_header():
    mod = module("ch_lookup_y_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [
            {"asset_id": "U1", "ticker": "AAA", "resolved_company_name": "FAILS CO", "isin": "GB0000000001", "resolution_status": "resolved"},
            {"asset_id": "U2", "ticker": "BBB", "resolved_company_name": "WORKS CO PLC", "isin": "GB0000000002", "resolution_status": "resolved"},
        ])
        import urllib.error

        captured_auth_headers = []

        def side_effect(request, timeout=30):
            captured_auth_headers.append(request.get_header("Authorization"))
            if "FAILS" in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 500, "err", hdrs=None, fp=io.BytesIO(b"{}"))
            return fake_response({"items": [{"title": "WORKS CO PLC", "company_number": "999", "company_status": "active"}]})

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})
        report = json.loads(out.strip().splitlines()[-1])
        assert report["profiles_confirmed"] == 1 and report["unresolved_or_error"] == 1
        import base64
        expected_auth = "Basic " + base64.b64encode(f"{FIXTURE_KEY}:".encode()).decode()
        assert all(h == expected_auth for h in captured_auth_headers)
        assert FIXTURE_KEY not in json.dumps(report)


def test_normalize_handles_dotted_plc_suffix_real_companies_house_case():
    """Real bug found while running this script for real against the 40
    corrected GB identities: Companies House registers BP's legal name as
    "BP P.L.C." (dotted single letters), which the old punctuation-to-space
    substitution split into three separate one-letter words that never
    matched the plain "PLC" suffix token our query name normalizes to.
    Periods are now deleted outright instead of replaced with a space."""
    mod = module("ch_lookup_y_normalize")
    assert mod.normalize("BP P.L.C.") == "BP"
    assert mod.normalize("BP PLC") == "BP"
    assert mod.normalize("ROLLS-ROYCE HOLDINGS PLC") == "ROLLS ROYCE HOLDINGS"


CASES = [
    test_dry_run_reports_eligible_without_network,
    test_execute_without_credential_is_blocked,
    test_exact_active_match_resolves_and_ambiguous_does_not_at_scale,
    test_http_error_continues_and_no_credential_leak_in_auth_header,
    test_normalize_handles_dotted_plc_suffix_real_companies_house_case,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38Y-companies-house-lookup-full-expansion/blocked-by-default/fail-closed-name-match/at-scale/no-credential-leak")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
