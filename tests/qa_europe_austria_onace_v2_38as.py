#!/usr/bin/env python3
"""Offline QA for the v2.38AS Austria ÖNACE fetcher. No real network calls,
no real credential -- FIXTURE_KEY is a throwaway string, never the real
SCOUT_FINANCE_FIRMENAKTE_API_KEY value."""
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
SCRIPT = ROOT / "scripts/fetch_europe_austria_onace_v2_38as.py"
CREDENTIAL_ENV = "SCOUT_FINANCE_FIRMENAKTE_API_KEY"
FIXTURE_KEY = "test-fixture-key-not-real"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_gleif_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "resolved_company_name", "home_country", "gleif_lookup_status", "national_registration_number"]
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


def fake_curl_result(body: dict | None, http_code: str = "200"):
    text = (json.dumps(body) if body is not None else "") + "\n" + http_code
    return mock.MagicMock(stdout=text.encode("utf-8"))


def test_dry_run_reports_eligible_without_network():
    mod = module("at_onace_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [{"asset_id": "U1", "ticker": "OMV", "resolved_company_name": "OMV AKTIENGESELLSCHAFT", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "93363z"}])
        with mock.patch("subprocess.run") as run_mock:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")], {})
        assert code == 0 and run_mock.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_companies"] == 1


def test_execute_without_credential_is_blocked():
    mod = module("at_onace_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [{"asset_id": "U1", "ticker": "OMV", "resolved_company_name": "OMV AKTIENGESELLSCHAFT", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "93363z"}])
        code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {})
        assert code == 2 and json.loads(out)["reason"] == "credential_missing"


def test_real_onace_and_purpose_captured_via_curl_subprocess():
    """The whole point of this script: reads oenaces + purpose from the
    same firmenakte.at response v2.38AI already fetches, using curl as a
    subprocess (documented real fix for a urllib-specific connectivity
    issue against this host, confirmed live 2026-09-06)."""
    mod = module("at_onace_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [{"asset_id": "U1", "ticker": "EBO", "resolved_company_name": "ERSTE GROUP BANK AG", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "33209m"}])

        captured_cmds = []

        def side_effect(cmd, capture_output, timeout):
            captured_cmds.append(cmd)
            return fake_curl_result({"name": "Erste Group Bank AG", "purpose": "Bankgeschäfte", "oenaces": [{"numericCode": "64190", "titel": "Kreditinstitute, ohne Spezialkreditinstitute"}]})

        with mock.patch("subprocess.run", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})

        rows = list(csv.DictReader((root / "out" / "europe_austria_onace_v2_38as.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"
        assert rows[0]["onace_code"] == "64190"
        assert rows[0]["onace_description_en"] == "Other monetary intermediation"
        assert rows[0]["purpose_de"] == "Bankgeschäfte"
        assert any(FIXTURE_KEY in str(part) for cmd in captured_cmds for part in cmd)
        assert FIXTURE_KEY not in out


def test_unverified_onace_code_stays_honestly_unknown_never_guessed():
    mod = module("at_onace_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [{"asset_id": "U1", "ticker": "ZZZ", "resolved_company_name": "UNKNOWN CODE CO", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "999999z"}])

        def side_effect(cmd, capture_output, timeout):
            return fake_curl_result({"oenaces": [{"numericCode": "99999", "titel": "Irgendwas"}]})

        with mock.patch("subprocess.run", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})

        rows = list(csv.DictReader((root / "out" / "europe_austria_onace_v2_38as.csv").open(encoding="utf-8")))
        assert rows[0]["onace_description_en"] == "UNKNOWN_ONACE_CODE_99999"
        report = json.loads((root / "out" / "europe_austria_onace_report_v2_38as.json").read_text(encoding="utf-8"))
        assert "99999" in report["unknown_onace_codes_needing_verification"]


def test_no_onace_on_record_reported_not_dropped():
    mod = module("at_onace_5")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [{"asset_id": "U1", "ticker": "EMP", "resolved_company_name": "EMPTY ONACE CO", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "888888z"}])

        def side_effect(cmd, capture_output, timeout):
            return fake_curl_result({"oenaces": [], "purpose": None})

        with mock.patch("subprocess.run", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})
        rows = list(csv.DictReader((root / "out" / "europe_austria_onace_v2_38as.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "no_onace_on_record"
        assert rows[0]["onace_code"] == ""


def test_http_error_continues_and_no_credential_leak():
    mod = module("at_onace_6")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [
            {"asset_id": "U1", "ticker": "FAILS", "resolved_company_name": "FAILS CO", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "111111z"},
            {"asset_id": "U2", "ticker": "WORKS", "resolved_company_name": "WORKS CO", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "222222z"},
        ])

        def side_effect(cmd, capture_output, timeout):
            if "111111z" in cmd[-1]:
                return fake_curl_result(None, http_code="500")
            return fake_curl_result({"oenaces": [{"numericCode": "70100", "titel": "x"}]})

        with mock.patch("subprocess.run", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})
        report = json.loads(out.strip().splitlines()[-1])
        assert report["companies_with_onace"] == 1 and report["companies_error"] == 1
        assert FIXTURE_KEY not in json.dumps(report)
        assert not list((root / "out").glob("*.tmp"))


def test_resumable_across_runs_never_loses_a_prior_real_success():
    """Real, confirmed behaviour of this provider (2026-09-06): connection
    flakiness means one run might resolve company A and fail on B, the
    next run might do the opposite -- a naive full-overwrite would erase
    the first run's real success. A second run must keep the first run's
    resolved row untouched and only retry what previously failed."""
    mod = module("at_onace_8")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [
            {"asset_id": "U1", "ticker": "AAA", "resolved_company_name": "AAA CO", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "111111a"},
            {"asset_id": "U2", "ticker": "BBB", "resolved_company_name": "BBB CO", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "222222b"},
        ])
        out_dir = root / "out"

        # Run 1: AAA succeeds, BBB fails (simulating real flakiness).
        def side_effect_1(cmd, capture_output, timeout):
            if "111111a" in cmd[-1]:
                return fake_curl_result({"oenaces": [{"numericCode": "70100", "titel": "x"}]})
            return fake_curl_result(None, http_code="000")

        with mock.patch("subprocess.run", side_effect=side_effect_1), mock.patch("time.sleep"):
            run(mod, ["--input-matrix", str(matrix), "--output-dir", str(out_dir), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})
        rows_after_1 = {r["asset_id"]: r for r in csv.DictReader((out_dir / "europe_austria_onace_v2_38as.csv").open(encoding="utf-8"))}
        assert rows_after_1["U1"]["fetch_status"] == "resolved" and rows_after_1["U2"]["fetch_status"] == "error"

        # Run 2: the API is now failing for AAA too (if it were re-fetched)
        # but succeeding for BBB -- AAA's real row from run 1 must survive.
        def side_effect_2(cmd, capture_output, timeout):
            assert "111111a" not in cmd[-1], "AAA was already resolved and must never be re-fetched"
            return fake_curl_result({"oenaces": [{"numericCode": "64190", "titel": "y"}]})

        with mock.patch("subprocess.run", side_effect=side_effect_2), mock.patch("time.sleep"):
            run(mod, ["--input-matrix", str(matrix), "--output-dir", str(out_dir), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})
        rows_after_2 = {r["asset_id"]: r for r in csv.DictReader((out_dir / "europe_austria_onace_v2_38as.csv").open(encoding="utf-8"))}
        assert rows_after_2["U1"]["fetch_status"] == "resolved" and rows_after_2["U1"]["onace_code"] == "70100"
        assert rows_after_2["U2"]["fetch_status"] == "resolved" and rows_after_2["U2"]["onace_code"] == "64190"


def test_only_austrian_resolved_companies_with_fn_are_eligible():
    mod = module("at_onace_7")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [
            {"asset_id": "U1", "ticker": "OK", "resolved_company_name": "OK CO", "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": "333333z"},
            {"asset_id": "U2", "ticker": "OTHER", "resolved_company_name": "OTHER COUNTRY CO", "home_country": "DE", "gleif_lookup_status": "resolved", "national_registration_number": "444444z"},
            {"asset_id": "U3", "ticker": "NORES", "resolved_company_name": "NOT RESOLVED CO", "home_country": "AT", "gleif_lookup_status": "unresolved", "national_registration_number": ""},
        ])
        with mock.patch("subprocess.run") as run_mock:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")], {})
        assert json.loads(out)["eligible_companies"] == 1
        assert run_mock.call_count == 0


CASES = [
    test_dry_run_reports_eligible_without_network,
    test_execute_without_credential_is_blocked,
    test_real_onace_and_purpose_captured_via_curl_subprocess,
    test_unverified_onace_code_stays_honestly_unknown_never_guessed,
    test_no_onace_on_record_reported_not_dropped,
    test_http_error_continues_and_no_credential_leak,
    test_resumable_across_runs_never_loses_a_prior_real_success,
    test_only_austrian_resolved_companies_with_fn_are_eligible,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AS-europe-austria-onace/curl-subprocess-fix/no-guessed-descriptions/blocked-by-default")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
