#!/usr/bin/env python3
"""Offline QA for the v2.38AE Netherlands registry lookup runner. No real
network calls. Unlike every prior country in this project, this lookup
is keyed by ISIN via GLEIF (a perfect, unambiguous identifier -- no
fuzzy name matching at all), then samples KVK's rate-limited financial
dataset. Real facts reproduced here (verified live before writing the
script): ASML Holding (ISIN NL0010273215) resolves to KVK 17085815, and
neither ASML nor Heineken (KVK 33011433) have any entry in the
Jaarrekeningen Open Dataset.
"""
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
SCRIPT = ROOT / "scripts/run_europe_netherlands_registry_lookup_v2_38ae.py"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_resolved_matrix(path: Path, rows: list[dict[str, str]]) -> None:
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


def fake_response(payload: dict, status: int = 200):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__enter__.return_value.status = status
    cm.__exit__.return_value = False
    return cm


def nl_row(asset_id: str, ticker: str, name: str, isin: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "resolved_company_name": name, "isin": isin, "resolution_status": "resolved", "home_country": "NL"}


def gleif_payload(lei: str, legal_name: str, kvk_number: str) -> dict:
    return {"data": [{"id": lei, "attributes": {"entity": {
        "legalName": {"name": legal_name}, "registeredAt": {"id": "RA000463"}, "registeredAs": kvk_number, "status": "ACTIVE",
    }}}]}


def test_dry_run_reports_only_netherlands_eligible_without_network():
    mod = module("nl_lookup_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [
            nl_row("U1", "ASML", "ASML HOLDING NV", "NL0010273215"),
            {"asset_id": "U2", "ticker": "GUI", "resolved_company_name": "DIAGEO PLC", "isin": "GB0002374006", "resolution_status": "resolved", "home_country": "GB"},
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert code == 0 and urlopen.call_count == 0
        report = json.loads(out)
        assert report["status"] == "DRY_RUN" and report["eligible_assets"] == 1 and report["asset_ids"] == ["U1"]


def test_isin_keyed_lookup_resolves_real_asml_case_no_credential():
    """Reproduces the exact real case confirmed live: ASML's ISIN
    resolves via GLEIF to KVK number 17085815, with no name-matching
    ambiguity at all -- ISIN is a perfect key, unlike every prior
    country's name-based fail-closed matching."""
    mod = module("nl_lookup_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [nl_row("U1", "ASML", "ASML HOLDING NV", "NL0010273215")])

        def side_effect(request, timeout=30):
            if "gleif.org" in request.full_url:
                return fake_response(gleif_payload("724500Y6DUVHQD6OXN27", "ASML Holding N.V.", "17085815"))
            raise AssertionError(f"unexpected URL in this test: {request.full_url}")

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--jaarrekeningen-sample", "0", "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["gleif_profiles_confirmed"] == 1 and report["kvk_numbers_confirmed"] == 1
        assert report["credentials_used"] is False
        rows = list(csv.DictReader((root / "out" / "europe_netherlands_gleif_registry_matrix_v2_38ae.csv").open(encoding="utf-8")))
        assert rows[0]["kvk_number"] == "17085815" and rows[0]["legal_name"] == "ASML Holding N.V."
        assert not list((root / "out").glob("*.tmp"))


def test_no_lei_record_stays_unresolved_never_guessed():
    mod = module("nl_lookup_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [nl_row("U1", "XXX", "UNKNOWN CO", "NL0000000000")])
        with mock.patch("urllib.request.urlopen", side_effect=lambda *a, **k: fake_response({"data": []})), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--jaarrekeningen-sample", "0", "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["gleif_profiles_confirmed"] == 0
        rows = list(csv.DictReader((root / "out" / "europe_netherlands_gleif_registry_matrix_v2_38ae.csv").open(encoding="utf-8")))
        assert rows[0]["gleif_lookup_status"] == "unresolved" and rows[0]["gleif_lookup_reason"] == "no_lei_record_for_isin"


def test_jaarrekeningen_sample_reproduces_real_not_found_case():
    """Reproduces the exact real case confirmed live twice (ASML and
    Heineken): the Jaarrekeningen Open Dataset returns HTTP 404 with
    "product does not exist" for large IFRS-reporting multinationals --
    recorded honestly as not_available, never treated as a script error."""
    mod = module("nl_lookup_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [nl_row("U1", "ASML", "ASML HOLDING NV", "NL0010273215")])

        import urllib.error

        def side_effect(request, timeout=30):
            if "gleif.org" in request.full_url:
                return fake_response(gleif_payload("724500Y6DUVHQD6OXN27", "ASML Holding N.V.", "17085815"))
            if "opendata.kvk.nl" in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 404, "not found", hdrs=None, fp=io.BytesIO(b'{"code":"IPD0001","omschrijving":"Het gevraagde product voor Jaarrekeningen bestaat niet."}'))
            raise AssertionError(f"unexpected URL: {request.full_url}")

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--jaarrekeningen-sample", "1", "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["jaarrekeningen_sample_checked"] == 1 and report["jaarrekeningen_available_in_sample"] == 0
        rows = list(csv.DictReader((root / "out" / "europe_netherlands_jaarrekeningen_sample_v2_38ae.csv").open(encoding="utf-8")))
        assert rows[0]["jaarrekeningen_status"] == "not_available"


CASES = [
    test_dry_run_reports_only_netherlands_eligible_without_network,
    test_isin_keyed_lookup_resolves_real_asml_case_no_credential,
    test_no_lei_record_stays_unresolved_never_guessed,
    test_jaarrekeningen_sample_reproduces_real_not_found_case,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AE-netherlands-registry-lookup/dry-run-gate/isin-keyed-gleif-lookup/jaarrekeningen-sample-not-found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
