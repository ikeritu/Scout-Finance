#!/usr/bin/env python3
"""Offline QA for the v2.38AO France NAF/NACE sector codes fetcher. No
real network calls -- this API needs no credential, so there is nothing
to leak, but every response below is still a synthetic fixture."""
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
SCRIPT = ROOT / "scripts/fetch_europe_france_sector_codes_v2_38ao.py"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_registry_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "resolved_company_name", "isin", "lookup_status", "siren"]
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


def fake_response(payload: dict):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_dry_run_reports_eligible_without_network():
    mod = module("fr_sector_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_registry_matrix(matrix, [{"asset_id": "U1", "ticker": "NXS", "resolved_company_name": "NEXANS", "isin": "FR0000044448", "lookup_status": "resolved", "siren": "393525852"}])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert code == 0 and urlopen.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_companies"] == 1


def test_real_naf_and_nace_section_captured_and_translated():
    """The whole point of this script: capture the real NAF code and NACE
    section from the same free API v2.38AD already validated, matched
    strictly by siren, and translate to English via the verified table."""
    mod = module("fr_sector_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_registry_matrix(matrix, [{"asset_id": "U1", "ticker": "SOH1", "resolved_company_name": "SOITEC S.A.", "isin": "FR0013227113", "lookup_status": "resolved", "siren": "384711909"}])

        def side_effect(request, timeout=30):
            return fake_response({"results": [{"siren": "384711909", "nom_complet": "SOITEC", "activite_principale": "26.11Z", "section_activite_principale": "C"}]})

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_france_sector_codes_v2_38ao.csv").open(encoding="utf-8")))
        assert rows[0]["naf_code"] == "26.11Z" and rows[0]["naf_description_en"] == "Manufacture of electronic components"
        assert rows[0]["nace_section"] == "C" and rows[0]["nace_section_description_en"] == "Manufacturing"
        assert rows[0]["fetch_status"] == "resolved"


def test_wrong_siren_in_results_never_matched_fail_closed():
    """A real risk with a free-text search API: the results list could
    contain other companies. Matching must require an exact siren match,
    never picking the first item blindly."""
    mod = module("fr_sector_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_registry_matrix(matrix, [{"asset_id": "U1", "ticker": "XXX", "resolved_company_name": "SOME CO", "isin": "FR0000000001", "lookup_status": "resolved", "siren": "111111111"}])

        def side_effect(request, timeout=30):
            return fake_response({"results": [{"siren": "999999999", "nom_complet": "DIFFERENT COMPANY", "activite_principale": "99.99Z"}]})

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_france_sector_codes_v2_38ao.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "no_siren_match"
        assert rows[0]["naf_code"] == ""


def test_unverified_naf_code_stays_honestly_unknown_never_guessed():
    mod = module("fr_sector_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_registry_matrix(matrix, [{"asset_id": "U1", "ticker": "YYY", "resolved_company_name": "UNKNOWN CODE CO", "isin": "FR0000000002", "lookup_status": "resolved", "siren": "222222222"}])

        def side_effect(request, timeout=30):
            return fake_response({"results": [{"siren": "222222222", "activite_principale": "12.34Z", "section_activite_principale": "Z"}]})

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_france_sector_codes_v2_38ao.csv").open(encoding="utf-8")))
        assert rows[0]["naf_description_en"] == "UNKNOWN_NAF_CODE_12.34Z"
        assert rows[0]["nace_section_description_en"] == "UNKNOWN_NACE_SECTION_Z"
        report = json.loads((root / "out" / "europe_france_sector_codes_report_v2_38ao.json").read_text(encoding="utf-8"))
        assert "12.34Z" in report["unknown_naf_codes_needing_translation"]
        assert "Z" in report["unknown_nace_sections_needing_translation"]


def test_http_error_continues_no_credential_to_leak():
    mod = module("fr_sector_5")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_registry_matrix(matrix, [
            {"asset_id": "U1", "ticker": "FAILS", "resolved_company_name": "FAILS CO", "isin": "FR0000000003", "lookup_status": "resolved", "siren": "333333333"},
            {"asset_id": "U2", "ticker": "WORKS", "resolved_company_name": "WORKS CO", "isin": "FR0000000004", "lookup_status": "resolved", "siren": "444444444"},
        ])
        import urllib.error

        def side_effect(request, timeout=30):
            if "333333333" in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 500, "err", hdrs=None, fp=io.BytesIO(b"{}"))
            return fake_response({"results": [{"siren": "444444444", "activite_principale": "70.10Z", "section_activite_principale": "M"}]})

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["companies_with_sector_codes"] == 1 and report["companies_error"] == 1
        assert not list((root / "out").glob("*.tmp"))


def test_only_resolved_companies_with_siren_are_eligible():
    mod = module("fr_sector_6")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_registry_matrix(matrix, [
            {"asset_id": "U1", "ticker": "OK", "resolved_company_name": "OK CO", "isin": "FR0000000005", "lookup_status": "resolved", "siren": "555555555"},
            {"asset_id": "U2", "ticker": "NO", "resolved_company_name": "UNRESOLVED CO", "isin": "FR0000000006", "lookup_status": "unresolved", "siren": ""},
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert json.loads(out)["eligible_companies"] == 1
        assert urlopen.call_count == 0


CASES = [
    test_dry_run_reports_eligible_without_network,
    test_real_naf_and_nace_section_captured_and_translated,
    test_wrong_siren_in_results_never_matched_fail_closed,
    test_unverified_naf_code_stays_honestly_unknown_never_guessed,
    test_http_error_continues_no_credential_to_leak,
    test_only_resolved_companies_with_siren_are_eligible,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AO-europe-france-sector-codes/siren-exact-match/verified-translations/blocked-by-default")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
