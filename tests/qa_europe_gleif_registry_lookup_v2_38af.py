#!/usr/bin/env python3
"""Offline QA for the v2.38AF generalized GLEIF registry lookup -- the
same ISIN-keyed method already proven on the Netherlands (v2.38AE),
applied across multiple countries in one run instead of one country at a
time. No real network calls.
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
SCRIPT = ROOT / "scripts/run_europe_gleif_registry_lookup_v2_38af.py"


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


def fake_response(payload: dict):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__enter__.return_value.status = 200
    cm.__exit__.return_value = False
    return cm


def row(asset_id: str, ticker: str, name: str, isin: str, country: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "resolved_company_name": name, "isin": isin, "resolution_status": "resolved", "home_country": country}


def gleif_payload(lei: str, legal_name: str, ra_id: str, national_number: str) -> dict:
    return {"data": [{"id": lei, "attributes": {"entity": {
        "legalName": {"name": legal_name}, "registeredAt": {"id": ra_id}, "registeredAs": national_number, "status": "ACTIVE",
    }}}]}


def test_dry_run_reports_only_selected_countries_without_network():
    mod = module("gleif_af_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [
            row("U1", "NOV", "NOVARTIS", "CH0012005267", "CH"),
            row("U2", "GEN", "GENERALI", "IT0000062072", "IT"),
            row("U3", "GUI", "DIAGEO PLC", "GB0002374006", "GB"),  # not in the default country set
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--countries", "CH", "IT"])
        assert code == 0 and urlopen.call_count == 0
        report = json.loads(out)
        assert report["status"] == "DRY_RUN" and report["eligible_assets"] == 2
        assert report["by_country"] == {"CH": 1, "IT": 1}


def test_single_run_resolves_multiple_countries_at_once_no_credential():
    """The whole point of the generalization: Swiss, Italian, and Danish
    assets in the same input file must all resolve in one run, with no
    per-country jurisdiction filter or bespoke matching logic."""
    mod = module("gleif_af_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [
            row("U1", "NOV", "NOVARTIS", "CH0012005267", "CH"),
            row("U2", "GEN", "GENERALI", "IT0000062072", "IT"),
            row("U3", "CBGB", "CARLSBERG", "DK0010181759", "DK"),
        ])
        responses = {
            "CH0012005267": gleif_payload("LEI-NOVARTIS", "Novartis AG", "RA000123", "CH-002.3.000.001-2"),
            "IT0000062072": gleif_payload("LEI-GENERALI", "Assicurazioni Generali S.p.A.", "RA000456", "00409920584"),
            "DK0010181759": gleif_payload("LEI-CARLSBERG", "Carlsberg A/S", "RA000789", "61056416"),
        }

        def side_effect(request, timeout=30):
            isin = request.full_url.split("filter%5Bisin%5D=")[1]
            return fake_response(responses[isin])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--countries", "CH", "IT", "DK", "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["gleif_profiles_confirmed"] == 3
        assert report["credentials_used"] is False
        assert report["resolved_by_country"] == {"CH": 1, "DK": 1, "IT": 1}
        rows = {r["ticker"]: r for r in csv.DictReader((root / "out" / "europe_gleif_registry_lookup_matrix_v2_38af.csv").open(encoding="utf-8"))}
        assert rows["NOV"]["national_registration_number"] == "CH-002.3.000.001-2"
        assert rows["GEN"]["legal_name"] == "Assicurazioni Generali S.p.A."
        assert not list((root / "out").glob("*.tmp"))


def test_no_lei_record_stays_unresolved_never_guessed():
    mod = module("gleif_af_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [row("U1", "XXX", "UNKNOWN CO", "CH0000000000", "CH")])
        with mock.patch("urllib.request.urlopen", side_effect=lambda *a, **k: fake_response({"data": []})), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--countries", "CH", "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["gleif_profiles_confirmed"] == 0
        rows = list(csv.DictReader((root / "out" / "europe_gleif_registry_lookup_matrix_v2_38af.csv").open(encoding="utf-8")))
        assert rows[0]["gleif_lookup_status"] == "unresolved" and rows[0]["gleif_lookup_reason"] == "no_lei_record_for_isin"


CASES = [
    test_dry_run_reports_only_selected_countries_without_network,
    test_single_run_resolves_multiple_countries_at_once_no_credential,
    test_no_lei_record_stays_unresolved_never_guessed,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AF-gleif-registry-lookup/multi-country-single-run/isin-keyed/no-credential-needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
