#!/usr/bin/env python3
"""Offline QA for the v2.38AD France registry lookup runner. No real
network calls. Like the CRO lookup, this endpoint needs no credential at
all -- confirmed via desk research and a live probe before writing the
script (recherche-entreprises.api.gouv.fr is fully public) -- so there is
no "blocked without credential" case, only the dry-run gate and the
fail-closed matching logic, including two real duplicate-active-company
cases confirmed live during development.
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
SCRIPT = ROOT / "scripts/run_europe_france_registry_lookup_v2_38ad.py"


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
    cm.__exit__.return_value = False
    return cm


def fr_row(asset_id: str, ticker: str, name: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "resolved_company_name": name, "isin": f"FR{asset_id}", "resolution_status": "resolved", "home_country": "FR"}


def test_dry_run_reports_only_france_eligible_without_network():
    mod = module("fr_lookup_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [
            fr_row("U1", "NXS", "NEXANS"),
            {"asset_id": "U2", "ticker": "GUI", "resolved_company_name": "DIAGEO PLC", "isin": "GB0002374006", "resolution_status": "resolved", "home_country": "GB"},
        ])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert code == 0 and urlopen.call_count == 0
        report = json.loads(out)
        assert report["status"] == "DRY_RUN" and report["eligible_assets"] == 1 and report["asset_ids"] == ["U1"]


def test_no_credential_needed_execute_runs_directly():
    mod = module("fr_lookup_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [fr_row("U1", "NXS", "NEXANS")])
        with mock.patch("urllib.request.urlopen", side_effect=lambda *a, **k: fake_response({"results": []})) as urlopen, mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        assert code == 0 and urlopen.call_count == 1
        report = json.loads(out.strip().splitlines()[-1])
        assert report["credentials_used"] is False


def test_exact_active_match_resolves_real_case_nexans():
    mod = module("fr_lookup_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [fr_row("U1", "NXS", "NEXANS")])
        responses = {"NEXANS": {"results": [
            {"siren": "393525852", "nom_complet": "NEXANS", "etat_administratif": "A", "nature_juridique": "5599"},
            {"siren": "428593230", "nom_complet": "NEXANS FRANCE", "etat_administratif": "A", "nature_juridique": "5710"},
        ]}}

        def side_effect(request, timeout=30):
            import urllib.parse
            name = urllib.parse.unquote_plus(request.full_url.split("q=")[1].split("&")[0])
            return fake_response(responses[name])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["profiles_confirmed"] == 1
        rows = list(csv.DictReader((root / "out" / "europe_france_registry_lookup_matrix_v2_38ad.csv").open(encoding="utf-8")))
        assert rows[0]["siren"] == "393525852"
        assert not list((root / "out").glob("*.tmp"))


def test_real_duplicate_active_company_case_stays_ambiguous_never_guessed():
    """Reproduces the exact real case found live while building this
    script: recherche-entreprises.api.gouv.fr genuinely returns two
    active SIREN both named exactly "HERMES INTERNATIONAL" (one a "grande
    entreprise" from 1957, nature_juridique 5308; one a "PME" from 1995,
    nature_juridique 5499). Fail-closed matching must leave this
    unresolved rather than guess based on size/category -- the same
    discipline that caught the GB SCT/BMT ticker collision. (A second
    real case, TotalEnergies SE, also has two active SIREN named
    "TOTALENERGIES SE" -- but one carries extra parenthetical text in its
    nom_complet, so after normalization only one candidate exactly
    matches and it resolves cleanly; that companion case is covered by
    the Nexans-style exact-match test above, not here.)"""
    mod = module("fr_lookup_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [fr_row("U1", "HMI", "HERMES INTERNATIONAL")])
        responses = {
            "HERMES INTERNATIONAL": {"results": [
                {"siren": "572076396", "nom_complet": "HERMES INTERNATIONAL", "etat_administratif": "A", "nature_juridique": "5308"},
                {"siren": "405362955", "nom_complet": "HERMES INTERNATIONAL", "etat_administratif": "A", "nature_juridique": "5499"},
            ]},
        }

        def side_effect(request, timeout=30):
            import urllib.parse
            name = urllib.parse.unquote_plus(request.full_url.split("q=")[1].split("&")[0])
            return fake_response(responses[name])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["profiles_confirmed"] == 0
        rows = list(csv.DictReader((root / "out" / "europe_france_registry_lookup_matrix_v2_38ad.csv").open(encoding="utf-8")))
        assert rows[0]["lookup_status"] == "unresolved" and rows[0]["lookup_reason"] == "ambiguous_multiple_active_companies_match_name"


def test_normalize_deletes_periods_and_apostrophes_strips_legal_suffix():
    mod = module("fr_lookup_5")
    assert mod.normalize("NEXANS SA") == "NEXANS"
    assert mod.normalize("TOTALENERGIES SE") == "TOTALENERGIES"
    assert mod.normalize("L'OREAL") == "L OREAL"
    assert mod.normalize("S.A. TEST CO SAS") == "SA TEST CO"  # leading "S.A." collapses to "SA" (periods deleted), only trailing legal-form token stripped


CASES = [
    test_dry_run_reports_only_france_eligible_without_network,
    test_no_credential_needed_execute_runs_directly,
    test_exact_active_match_resolves_real_case_nexans,
    test_real_duplicate_active_company_case_stays_ambiguous_never_guessed,
    test_normalize_deletes_periods_and_apostrophes_strips_legal_suffix,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AD-france-registry-lookup/dry-run-gate/no-credential-needed/fail-closed-name-match/real-duplicate-ambiguity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
