#!/usr/bin/env python3
"""Offline QA for the v2.38AT Ireland NACE fetcher. No real network calls
-- this API needs no credential, so there is nothing to leak, but every
response below is still a synthetic fixture."""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/fetch_europe_ireland_nace_v2_38at.py"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_cro_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "resolved_company_name", "isin", "lookup_status", "company_number"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
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


def fake_response(records: list[dict]):
    payload = {"result": {"records": records}}
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_dry_run_reports_eligible_without_network():
    mod = module("ie_nace_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_cro_matrix(matrix, [{"asset_id": "U1", "ticker": "N4U", "resolved_company_name": "SMURFIT WESTROCK", "isin": "IE00BDSFG982", "lookup_status": "resolved", "company_number": "607515"}])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert code == 0 and urlopen.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_companies"] == 1


def test_real_nace_code_captured_matched_strictly_by_company_number():
    """Real case confirmed live 2026-09-06: Smurfit Westrock's CRO record
    already carries nace_v2_code 6420 -- must match strictly by
    company_num, never the first search result blindly."""
    mod = module("ie_nace_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_cro_matrix(matrix, [{"asset_id": "U1", "ticker": "N4U", "resolved_company_name": "SMURFIT WESTROCK", "isin": "IE00BDSFG982", "lookup_status": "resolved", "company_number": "607515"}])

        def side_effect(request, timeout=30):
            return fake_response([
                {"company_num": 999999, "company_name": "UNRELATED CO", "nace_v2_code": 1234},
                {"company_num": 607515, "company_name": "SMURFIT WESTROCK PUBLIC LIMITED COMPANY", "nace_v2_code": 6420, "princ_object_code": ""},
            ])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_ireland_nace_v2_38at.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"
        assert rows[0]["nace_code"] == "6420" and rows[0]["nace_description_en"] == "Activities of holding companies"


def test_princ_object_code_captured_for_traceability_never_used_as_sector():
    """Real case confirmed live: Alkermes plc (a real pharmaceutical
    company) has princ_object_code '24.41' (basic metals manufacturing)
    -- demonstrably wrong. This field must be recorded for traceability
    but must never populate nace_code/nace_description_en."""
    mod = module("ie_nace_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_cro_matrix(matrix, [{"asset_id": "U1", "ticker": "8AK", "resolved_company_name": "ALKERMES PLC", "isin": "IE00BY9D5467", "lookup_status": "resolved", "company_number": "498284"}])

        def side_effect(request, timeout=30):
            return fake_response([{"company_num": 498284, "company_name": "ALKERMES PUBLIC LIMITED COMPANY", "nace_v2_code": None, "princ_object_code": "24.41"}])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_ireland_nace_v2_38at.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "no_nace_on_record"
        assert rows[0]["nace_code"] == "" and rows[0]["nace_description_en"] == ""
        assert rows[0]["princ_object_code_unverified_not_used"] == "24.41"


def test_wrong_company_number_in_results_never_matched_fail_closed():
    mod = module("ie_nace_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_cro_matrix(matrix, [{"asset_id": "U1", "ticker": "XXX", "resolved_company_name": "SOME CO", "isin": "IE0000000001", "lookup_status": "resolved", "company_number": "111111"}])

        def side_effect(request, timeout=30):
            return fake_response([{"company_num": 999999, "company_name": "DIFFERENT COMPANY", "nace_v2_code": 4620}])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_ireland_nace_v2_38at.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "no_company_number_match"


def test_unverified_nace_code_stays_honestly_unknown_never_guessed():
    mod = module("ie_nace_5")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_cro_matrix(matrix, [{"asset_id": "U1", "ticker": "YYY", "resolved_company_name": "UNKNOWN CODE CO", "isin": "IE0000000002", "lookup_status": "resolved", "company_number": "222222"}])

        def side_effect(request, timeout=30):
            return fake_response([{"company_num": 222222, "nace_v2_code": 9999, "princ_object_code": ""}])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_ireland_nace_v2_38at.csv").open(encoding="utf-8")))
        assert rows[0]["nace_description_en"] == "UNKNOWN_NACE_CODE_9999"
        report = json.loads((root / "out" / "europe_ireland_nace_report_v2_38at.json").read_text(encoding="utf-8"))
        assert "9999" in report["unknown_nace_codes_needing_verification"]


def test_only_resolved_companies_with_company_number_are_eligible():
    mod = module("ie_nace_6")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_cro_matrix(matrix, [
            {"asset_id": "U1", "ticker": "OK", "resolved_company_name": "OK CO", "isin": "IE0000000003", "lookup_status": "resolved", "company_number": "333333"},
            {"asset_id": "U2", "ticker": "NO", "resolved_company_name": "UNRESOLVED CO", "isin": "IE0000000004", "lookup_status": "unresolved", "company_number": ""},
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert json.loads(out)["eligible_companies"] == 1
        assert urlopen.call_count == 0


CASES = [
    test_dry_run_reports_eligible_without_network,
    test_real_nace_code_captured_matched_strictly_by_company_number,
    test_princ_object_code_captured_for_traceability_never_used_as_sector,
    test_wrong_company_number_in_results_never_matched_fail_closed,
    test_unverified_nace_code_stays_honestly_unknown_never_guessed,
    test_only_resolved_companies_with_company_number_are_eligible,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AT-europe-ireland-nace/strict-company-number-match/princ-object-code-not-trusted/blocked-by-default")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
