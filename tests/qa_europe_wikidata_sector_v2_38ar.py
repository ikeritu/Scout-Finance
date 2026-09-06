#!/usr/bin/env python3
"""Offline QA for the v2.38AR generalized Wikidata sector fetcher. No real
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
SCRIPT = ROOT / "scripts/fetch_europe_wikidata_sector_v2_38ar.py"


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
    row = {"isin": {"value": isin}, "item": {"value": f"http://www.wikidata.org/entity/{qid}"}, "itemLabel": {"value": label}}
    if industry:
        row["industryLabel"] = {"value": industry}
    return row


def fake_response(bindings: list[dict]):
    payload = {"results": {"bindings": bindings}}
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_dry_run_defaults_to_switzerland_without_network():
    mod = module("ch_wd_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [
            {"asset_id": "U1", "ticker": "NOT", "resolved_company_name": "NOVARTIS", "isin": "CH0012005267", "resolution_status": "resolved", "home_country": "CH"},
            {"asset_id": "U2", "ticker": "ASME", "resolved_company_name": "ASML HOLDING", "isin": "NL0010273215", "resolution_status": "resolved", "home_country": "NL"},
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert code == 0 and urlopen.call_count == 0
        report = json.loads(out)
        assert report["status"] == "DRY_RUN" and report["countries"] == ["CH"] and report["eligible_companies"] == 1


def test_explicit_countries_argument_selects_the_right_subset():
    mod = module("ch_wd_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [
            {"asset_id": "U1", "ticker": "NOT", "resolved_company_name": "NOVARTIS", "isin": "CH0012005267", "resolution_status": "resolved", "home_country": "CH"},
            {"asset_id": "U2", "ticker": "ASME", "resolved_company_name": "ASML HOLDING", "isin": "NL0010273215", "resolution_status": "resolved", "home_country": "NL"},
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--countries", "CH", "NL"])
        report = json.loads(out)
        assert report["eligible_companies"] == 2


def test_real_swiss_industry_captured_with_caveat_and_country_column():
    """Real case confirmed live 2026-09-06: the Swiss UID register's
    PublicServices tier never exposes NOGACode -- Wikidata is the
    approved fallback. Novartis's real Wikidata industry must be
    captured with the country column populated."""
    mod = module("ch_wd_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "NOT", "resolved_company_name": "NOVARTIS", "isin": "CH0012005267", "resolution_status": "resolved", "home_country": "CH"}])

        def side_effect(request, timeout=60):
            return fake_response([sparql_binding("CH0012005267", "Q159082", "Novartis", "pharmaceutical industry")])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_wikidata_sector_v2_38ar.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "resolved"
        assert rows[0]["country"] == "CH"
        assert rows[0]["industries"] == "pharmaceutical industry"
        assert "NOT an official government registry" in rows[0]["non_official_source_caveat"]


def test_two_distinct_items_sharing_isin_is_ambiguous_never_guessed():
    mod = module("ch_wd_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "DUP", "resolved_company_name": "DUPLICATE CO", "isin": "CH0000000001", "resolution_status": "resolved", "home_country": "CH"}])

        def side_effect(request, timeout=60):
            return fake_response([
                sparql_binding("CH0000000001", "Q1111", "Duplicate Co A", "banking"),
                sparql_binding("CH0000000001", "Q2222", "Duplicate Co B", "retail"),
            ])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])

        rows = list(csv.DictReader((root / "out" / "europe_wikidata_sector_v2_38ar.csv").open(encoding="utf-8")))
        assert rows[0]["fetch_status"] == "ambiguous" and rows[0]["industries"] == ""


def test_report_breaks_down_by_country():
    mod = module("ch_wd_5")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [
            {"asset_id": "U1", "ticker": "AAA", "resolved_company_name": "AAA CO", "isin": "CH0000000002", "resolution_status": "resolved", "home_country": "CH"},
            {"asset_id": "U2", "ticker": "BBB", "resolved_company_name": "BBB CO", "isin": "CH0000000003", "resolution_status": "resolved", "home_country": "CH"},
        ])

        def side_effect(request, timeout=60):
            return fake_response([sparql_binding("CH0000000002", "Q3333", "AAA CO", "banking")])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        full_report = json.loads((root / "out" / "europe_wikidata_sector_report_v2_38ar.json").read_text(encoding="utf-8"))
        assert full_report["by_country"]["CH"] == {"resolved": 1, "total": 2}


def test_query_error_reports_all_rows_as_error_not_silently_dropped():
    mod = module("ch_wd_6")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_identity_matrix(matrix, [{"asset_id": "U1", "ticker": "AAA", "resolved_company_name": "AAA CO", "isin": "CH0000000004", "resolution_status": "resolved", "home_country": "CH"}])
        import urllib.error

        def side_effect(request, timeout=60):
            raise urllib.error.HTTPError(request.full_url, 500, "err", hdrs=None, fp=io.BytesIO(b"{}"))

        with mock.patch("urllib.request.urlopen", side_effect=side_effect):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["companies_error"] == 1
        assert not list((root / "out").glob("*.tmp"))


CASES = [
    test_dry_run_defaults_to_switzerland_without_network,
    test_explicit_countries_argument_selects_the_right_subset,
    test_real_swiss_industry_captured_with_caveat_and_country_column,
    test_two_distinct_items_sharing_isin_is_ambiguous_never_guessed,
    test_report_breaks_down_by_country,
    test_query_error_reports_all_rows_as_error_not_silently_dropped,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AR-europe-wikidata-sector/generalized-country-selection/fail-closed-ambiguity/blocked-by-default")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
