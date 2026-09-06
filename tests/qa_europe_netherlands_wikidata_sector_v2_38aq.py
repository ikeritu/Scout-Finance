#!/usr/bin/env python3
"""Offline QA for the v2.38AQ Netherlands Wikidata sector fetcher. No real
network calls -- this endpoint needs no credential, so there is nothing to
leak, but every response below is still a synthetic fixture."""
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
SCRIPT = ROOT / "scripts/fetch_europe_netherlands_wikidata_sector_v2_38aq.py"


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


def sparql_binding(isin: str, qid: str, label: str, industry: str = "") -> dict:
    row = {
        "isin": {"value": isin},
        "item": {"value": f"http://www.wikidata.org/entity/{qid}"},
        "itemLabel": {"value": label},
    }
    if industry:
        row["industryLabel"] = {"value": industry}
    return row


def fake_response(bindings: list[dict]):
    payload = {"results": {"bindings": bindings}}
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_dry_run_reports_eligible_without_network():
    mod = module("nl_wd_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "ASME", "resolved_company_name": "ASML HOLDING", "isin": "NL0010273215", "resolution_status": "resolved", "home_country": "NL"}])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert code == 0 and urlopen.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_companies"] == 1


def test_real_industry_captured_with_multiple_values_and_caveat():
    """Real case: ASML Holding has one Wikidata item with a single
    industry. Every row must carry the non-official-source caveat."""
    mod = module("nl_wd_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "ASME", "resolved_company_name": "ASML HOLDING", "isin": "NL0010273215", "resolution_status": "resolved", "home_country": "NL"}])

        def side_effect(request, timeout=60):
            return fake_response([sparql_binding("NL0010273215", "Q1234", "ASML Holding", "semiconductor industry")])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_netherlands_wikidata_sector_v2_38aq.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"
        assert rows[0]["industries"] == "semiconductor industry"
        assert rows[0]["wikidata_qid"] == "Q1234"
        assert "NOT an official government registry" in rows[0]["non_official_source_caveat"]


def test_multiple_industries_of_same_item_are_all_captured_not_ambiguous():
    """Real case: Airbus SE has one Wikidata item with several industry
    values (aviation, weapons industry, spaceflight...) -- that is NOT
    ambiguity, just a multi-valued property on one real item."""
    mod = module("nl_wd_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "AIR", "resolved_company_name": "AIRBUS SE", "isin": "NL0000235190", "resolution_status": "resolved", "home_country": "NL"}])

        def side_effect(request, timeout=60):
            return fake_response([
                sparql_binding("NL0000235190", "Q9999", "Airbus SE", "aviation"),
                sparql_binding("NL0000235190", "Q9999", "Airbus SE", "weapons industry"),
            ])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_netherlands_wikidata_sector_v2_38aq.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"
        assert set(rows[0]["industries"].split(";")) == {"aviation", "weapons industry"}


def test_two_distinct_items_sharing_isin_is_ambiguous_never_guessed():
    """A genuine data-quality problem on a community-edited database: two
    DIFFERENT Wikidata items both claiming the same ISIN. Must stay
    unresolved, never pick one arbitrarily."""
    mod = module("nl_wd_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "DUP", "resolved_company_name": "DUPLICATE CO", "isin": "NL0000000001", "resolution_status": "resolved", "home_country": "NL"}])

        def side_effect(request, timeout=60):
            return fake_response([
                sparql_binding("NL0000000001", "Q1111", "Duplicate Co A", "banking"),
                sparql_binding("NL0000000001", "Q2222", "Duplicate Co B", "retail"),
            ])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_netherlands_wikidata_sector_v2_38aq.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "ambiguous"
        assert rows[0]["industries"] == ""


def test_no_wikidata_match_and_matched_item_without_industry_are_distinct():
    mod = module("nl_wd_5")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [
            {"asset_id": "U1", "ticker": "NOM", "resolved_company_name": "NO MATCH CO", "isin": "NL0000000002", "resolution_status": "resolved", "home_country": "NL"},
            {"asset_id": "U2", "ticker": "NOI", "resolved_company_name": "NO INDUSTRY CO", "isin": "NL0000000003", "resolution_status": "resolved", "home_country": "NL"},
        ])

        def side_effect(request, timeout=60):
            return fake_response([sparql_binding("NL0000000003", "Q3333", "No Industry Co")])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = {r["asset_id"]: r for r in csv.DictReader((root / "out" / "europe_netherlands_wikidata_sector_v2_38aq.csv").open(encoding="utf-8"))}
        assert rows["U1"]["fetch_status"] == "no_wikidata_match"
        assert rows["U2"]["fetch_status"] == "no_industry" and rows["U2"]["wikidata_qid"] == "Q3333"


def test_query_error_reports_all_rows_as_error_not_silently_dropped():
    mod = module("nl_wd_6")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "AAA", "resolved_company_name": "AAA CO", "isin": "NL0000000004", "resolution_status": "resolved", "home_country": "NL"}])
        import urllib.error

        def side_effect(request, timeout=60):
            raise urllib.error.HTTPError(request.full_url, 500, "err", hdrs=None, fp=io.BytesIO(b"{}"))

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["companies_error"] == 1
        rows = list(csv.DictReader((root / "out" / "europe_netherlands_wikidata_sector_v2_38aq.csv").open(encoding="utf-8")))
        assert len(rows) == 1 and rows[0]["fetch_status"] == "error"
        assert not list((root / "out").glob("*.tmp"))


def test_only_netherlands_resolved_companies_with_isin_are_eligible():
    """A France or GB row in the same shared identity matrix must never
    be queried by this NL-specific script."""
    mod = module("nl_wd_7")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [
            {"asset_id": "U1", "ticker": "NL1", "resolved_company_name": "NL CO", "isin": "NL0000000005", "resolution_status": "resolved", "home_country": "NL"},
            {"asset_id": "U2", "ticker": "FR1", "resolved_company_name": "FR CO", "isin": "FR0000000005", "resolution_status": "resolved", "home_country": "FR"},
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert json.loads(out)["eligible_companies"] == 1
        assert urlopen.call_count == 0


CASES = [
    test_dry_run_reports_eligible_without_network,
    test_real_industry_captured_with_multiple_values_and_caveat,
    test_multiple_industries_of_same_item_are_all_captured_not_ambiguous,
    test_two_distinct_items_sharing_isin_is_ambiguous_never_guessed,
    test_no_wikidata_match_and_matched_item_without_industry_are_distinct,
    test_query_error_reports_all_rows_as_error_not_silently_dropped,
    test_only_netherlands_resolved_companies_with_isin_are_eligible,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AQ-europe-netherlands-wikidata-sector/fail-closed-ambiguity/non-official-caveat/blocked-by-default")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
