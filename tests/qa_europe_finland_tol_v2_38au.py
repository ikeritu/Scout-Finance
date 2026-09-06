#!/usr/bin/env python3
"""Offline QA for the v2.38AU Finland TOL fetcher. No real network calls
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
SCRIPT = ROOT / "scripts/fetch_europe_finland_tol_v2_38au.py"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_identity_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "resolved_company_name", "isin", "resolution_status", "home_country"]
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


def fake_response(companies: list[dict]):
    payload = {"totalResults": len(companies), "companies": companies}
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def company(business_id: str, names: list[str], tol_code: str = "", descriptions: list[dict] | None = None, auxiliary_names: list[str] | None = None) -> dict:
    """`names` are real, current registered names (PRH type "1"/"2" --
    the only types this script matches against); `auxiliary_names` are
    trade-name-only entries (type "4") that must never be used to match,
    reproducing the real Nordea/Merita brand-name collision risk."""
    name_entries = [{"name": n, "type": "1"} for n in names]
    name_entries += [{"name": n, "type": "4"} for n in (auxiliary_names or [])]
    return {
        "businessId": {"value": business_id},
        "names": name_entries,
        "mainBusinessLine": {"type": tol_code, "descriptions": descriptions or []} if tol_code else None,
    }


def test_dry_run_reports_eligible_without_network():
    mod = module("fi_tol_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "NOA3", "resolved_company_name": "NOKIA OYJ", "isin": "FI0009000681", "resolution_status": "resolved", "home_country": "FI"}])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert code == 0 and urlopen.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_companies"] == 1


def test_real_tol_and_english_description_captured():
    """Real case confirmed live 2026-09-06: Nokia Oyj's real record shows
    TOL 70100 with an English description already provided by the API --
    no translation table needed."""
    mod = module("fi_tol_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "NOA3", "resolved_company_name": "NOKIA OYJ", "isin": "FI0009000681", "resolution_status": "resolved", "home_country": "FI"}])

        def side_effect(request, timeout=30):
            return fake_response([company("0112038-9", ["Nokia Oyj", "Oy Nokia Ab"], "70100", [
                {"languageCode": "1", "description": "Pääkonttorien toiminta"},
                {"languageCode": "3", "description": "Activities of head offices"},
            ])])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_finland_tol_v2_38au.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"
        assert rows[0]["tol_code"] == "70100"
        assert rows[0]["tol_description_en"] == "Activities of head offices"
        assert rows[0]["business_id"] == "0112038-9"


def test_normalize_reverses_xetra_oe_transliteration_and_strips_share_class():
    """Real case: Xetra's ASCII transliteration renders SRV Yhtiot's real
    name 'SRV Yhtiöt Oyj' as 'SRV YHTIOET OYJ' (o-umlaut -> 'OE', the same
    digraph convention already seen for German/Austrian/Swiss names).
    Also real: 'SAMPO OYJ A' carries a Xetra share-class letter that is
    not part of the real registered name."""
    mod = module("fi_tol_normalize")
    assert mod.normalize("SRV YHTIOET OYJ") == mod.normalize("SRV Yhtiöt Oyj") == "SRV YHTIÖT"
    assert mod.normalize("SAMPO OYJ A") == "SAMPO"
    assert mod.normalize("UPM KYMMENE CORP.") == mod.normalize("UPM-Kymmene Oyj") == "UPM KYMMENE"


def test_real_suffix_disambiguates_oy_from_oyj_same_core_name():
    """Real case confirmed live 2026-09-06: 'SRV Yhtiöt Oy' (private) and
    'SRV Yhtiöt Oyj' (public) are two distinct, currently active Finnish
    companies differing only by legal form. Collapsing both suffixes to
    the same core name would make them collide; matching at full-suffix
    specificity first must resolve to the correct one (Oyj, matching
    Xetra's own recorded suffix) without any ambiguity."""
    mod = module("fi_tol_suffix")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "B7J1", "resolved_company_name": "SRV YHTIOET OYJ", "isin": "FI4000523675", "resolution_status": "resolved", "home_country": "FI"}])

        def side_effect(request, timeout=30):
            return fake_response([
                company("0767727-6", ["SRV Yhtiöt Oy"]),
                company("1707186-8", ["SRV Yhtiöt Oyj"], "41000", [{"languageCode": "3", "description": "Construction of residential and non-residential buildings"}]),
            ])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_finland_tol_v2_38au.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"
        assert rows[0]["business_id"] == "1707186-8"
        assert rows[0]["tol_code"] == "41000"


def test_core_fallback_used_only_when_xetra_suffix_is_wrong():
    """Real case: Xetra wrote 'Corp.' for UPM-Kymmene's real 'Oyj' suffix
    -- the full-suffix match finds nothing, so the core (suffix-stripped)
    fallback must resolve it, and must be reported with the fallback
    reason so the distinction stays traceable."""
    mod = module("fi_tol_core_fallback")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "RPL", "resolved_company_name": "UPM KYMMENE CORP.", "isin": "FI0009005987", "resolution_status": "resolved", "home_country": "FI"}])

        def side_effect(request, timeout=30):
            return fake_response([company("1041090-0", ["UPM-Kymmene Oyj"], "17120", [{"languageCode": "3", "description": "Manufacture of paper and paperboard"}])])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_finland_tol_v2_38au.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"
        assert rows[0]["fetch_reason"] == "exact_normalized_name_match_core_fallback_wrong_xetra_suffix"


def test_search_uses_first_word_and_scans_all_pages():
    """Real cases confirmed live: querying the full Xetra-derived name
    with a space where the real name has a hyphen ('UPM KYMMENE') finds
    nothing, but the first word ('UPM') does; and a single common word
    can span multiple result pages (991 total for 'NOKIA' alone) that
    must all be scanned before concluding no match exists."""
    mod = module("fi_tol_paginate")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "RPL", "resolved_company_name": "UPM KYMMENE CORP.", "isin": "FI0009005987", "resolution_status": "resolved", "home_country": "FI"}])

        queries_seen = []
        page1 = [company(f"000000{i}-0", [f"Unrelated UPM Co {i}"]) for i in range(3)]
        page2 = [company("1041090-0", ["UPM-Kymmene Oyj", "UPM-Kymmene Oy"], "17120", [{"languageCode": "3", "description": "Manufacture of paper and paperboard"}])]

        def side_effect(request, timeout=30):
            queries_seen.append(request.full_url)
            if "page=2" in request.full_url:
                return fake_response(page2)
            payload = {"totalResults": 4, "companies": page1}
            cm = mock.MagicMock()
            cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
            cm.__exit__.return_value = False
            return cm

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        assert any("name=UPM" in q and "page" not in q for q in queries_seen)
        assert any("page=2" in q for q in queries_seen)
        rows = list(csv.DictReader((root / "out" / "europe_finland_tol_v2_38au.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved" and rows[0]["tol_code"] == "17120"


def test_matches_across_any_registered_name_variant():
    """Real case: PRH records carry multiple registered names (main,
    parallel, auxiliary) -- a match against any variant is real, not
    just the first one listed."""
    mod = module("fi_tol_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "NOA3", "resolved_company_name": "NOKIA OYJ", "isin": "FI0009000681", "resolution_status": "resolved", "home_country": "FI"}])

        def side_effect(request, timeout=30):
            return fake_response([company("0112038-9", ["Oy Nokia Ab", "Nokia Oyj"], "70100", [{"languageCode": "3", "description": "Activities of head offices"}])])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        rows = list(csv.DictReader((root / "out" / "europe_finland_tol_v2_38au.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"


def test_auxiliary_trade_names_never_used_for_matching():
    """Real case confirmed live 2026-09-06: Nordea Bank Abp's search
    results include several unrelated business IDs (from the historical
    Merita/Nordea bank mergers) that each carry a bare "Nordea Bank"
    AUXILIARY trade name (PRH type 4, decades-old, no legal suffix) --
    which collides with the real "Nordea Bank Abp" once suffix-stripping
    normalizes both to "NORDEA BANK". Matching must use only the primary/
    parallel registered name (type 1/2), never an auxiliary trade name,
    so this must resolve cleanly, not fall into false ambiguity."""
    mod = module("fi_tol_aux")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "04Q", "resolved_company_name": "NORDEA BANK ABP", "isin": "FI4000297767", "resolution_status": "resolved", "home_country": "FI"}])

        def side_effect(request, timeout=30):
            return fake_response([
                company("0844052-9", ["Merita Bank Abp", "Merita Bank Plc"], auxiliary_names=["Nordea Bank", "Nordea Bank"]),
                company("1445044-0", ["Nordea Bank Finland Abp"], auxiliary_names=["Nordea Bank"]),
                company("2858394-9", ["Nordea Bank Abp", "Nordea Holding Abp"], "66190", [{"languageCode": "3", "description": "Other activities auxiliary to financial services, except insurance and pension funding"}], auxiliary_names=["Nordea", "Merita Bank"]),
            ])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_finland_tol_v2_38au.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"
        assert rows[0]["business_id"] == "2858394-9"
        assert rows[0]["tol_code"] == "66190"


def test_ambiguous_two_distinct_business_ids_never_guessed():
    mod = module("fi_tol_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "AMB", "resolved_company_name": "AMBIGUOUS OYJ", "isin": "FI0000000001", "resolution_status": "resolved", "home_country": "FI"}])

        def side_effect(request, timeout=30):
            return fake_response([company("1111111-1", ["Ambiguous Oyj"], "70100"), company("2222222-2", ["Ambiguous Oyj"], "64210")])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        rows = list(csv.DictReader((root / "out" / "europe_finland_tol_v2_38au.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "unresolved" and rows[0]["fetch_reason"] == "ambiguous_multiple_distinct_business_ids_match_name"


def test_no_match_and_http_error_handled_distinctly():
    mod = module("fi_tol_5")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [
            {"asset_id": "U1", "ticker": "NOM", "resolved_company_name": "NO MATCH OYJ", "isin": "FI0000000002", "resolution_status": "resolved", "home_country": "FI"},
            {"asset_id": "U2", "ticker": "ERR", "resolved_company_name": "ERROR CO OYJ", "isin": "FI0000000003", "resolution_status": "resolved", "home_country": "FI"},
        ])
        import urllib.error

        def side_effect(request, timeout=30):
            if "ERROR" in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 500, "err", hdrs=None, fp=io.BytesIO(b"{}"))
            return fake_response([])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["companies_error"] == 1
        rows = {r["asset_id"]: r for r in csv.DictReader((root / "out" / "europe_finland_tol_v2_38au.csv").open(encoding="utf-8"))}
        assert rows["U1"]["fetch_status"] == "unresolved" and rows["U1"]["fetch_reason"] == "no_exact_normalized_name_match"
        assert rows["U2"]["fetch_status"] == "error"
        assert not list((root / "out").glob("*.tmp"))


def test_only_finland_resolved_companies_are_eligible():
    mod = module("fi_tol_6")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [
            {"asset_id": "U1", "ticker": "OK", "resolved_company_name": "OK OYJ", "isin": "FI0000000004", "resolution_status": "resolved", "home_country": "FI"},
            {"asset_id": "U2", "ticker": "OTHER", "resolved_company_name": "OTHER CO", "isin": "SE0000000004", "resolution_status": "resolved", "home_country": "SE"},
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert json.loads(out)["eligible_companies"] == 1
        assert urlopen.call_count == 0


CASES = [
    test_dry_run_reports_eligible_without_network,
    test_real_tol_and_english_description_captured,
    test_normalize_reverses_xetra_oe_transliteration_and_strips_share_class,
    test_real_suffix_disambiguates_oy_from_oyj_same_core_name,
    test_core_fallback_used_only_when_xetra_suffix_is_wrong,
    test_search_uses_first_word_and_scans_all_pages,
    test_matches_across_any_registered_name_variant,
    test_auxiliary_trade_names_never_used_for_matching,
    test_ambiguous_two_distinct_business_ids_never_guessed,
    test_no_match_and_http_error_handled_distinctly,
    test_only_finland_resolved_companies_are_eligible,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AU-europe-finland-tol/oe-transliteration-fix/english-description-native/blocked-by-default")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
