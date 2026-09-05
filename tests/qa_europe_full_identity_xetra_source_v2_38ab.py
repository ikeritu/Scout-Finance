#!/usr/bin/env python3
"""Offline QA for the v2.38AB generalized Xetra-source/ISIN identity
resolver -- the same proven method from GB (v2.38V), Ireland (v2.38Z) and
Spain (v2.38AA), now applied to the full 689-asset in-scope Europe
universe instead of one jurisdiction at a time. No network calls -- uses
a small synthetic Xetra reference file fixture, never the real, licensed
Deutsche Boerse data.
"""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_full_identity_xetra_source_v2_38ab.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_full_identity_xetra_source_v2_38ab", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_xetra_fixture(path: Path, rows: list[dict[str, str]]) -> None:
    header = "Product Status;Instrument Status;Instrument;ISIN;Product ID;Instrument ID;WKN;Mnemonic;MIC Code;CCP eligible Code"
    lines = ["Market:;XETR", "Date Last Update:;01.01.2026", header]
    for r in rows:
        lines.append(f"Active;Active;{r['Instrument']};{r['ISIN']};1;1;WKN1;{r['Mnemonic']};XETR;Y")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def write_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "company_name", "home_mic", "home_country", "primary_fundamental_route"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def asset_row(asset_id: str, ticker: str, mic: str, country: str, route: str = "eodhd_fundamentals") -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": "GER0", "home_mic": mic, "home_country": country, "primary_fundamental_route": route}


def test_no_jurisdiction_filter_resolves_across_every_country_in_one_pass():
    """The whole point of the generalization: unlike the per-country
    scripts, this one takes every row in the input matrix regardless of
    home_country -- a German, a Dutch and a Danish asset in the same
    input file must all resolve in a single run."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [
            {"Instrument": "SAP SE", "ISIN": "DE0007164600", "Mnemonic": "SAP"},
            {"Instrument": "ASML HOLDING NV", "ISIN": "NL0010273215", "Mnemonic": "ASML"},
            {"Instrument": "NOVO NORDISK A-S", "ISIN": "DK0060534915", "Mnemonic": "NOVO"},
        ])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [
            asset_row("U1", "SAP", "XETR", "DE"),
            asset_row("U2", "ASML", "XAMS", "NL"),
            asset_row("U3", "NOVO", "XCSE", "DK"),
        ])
        report = mod.build(matrix, xetra, root / "out")
        rows = list(csv.DictReader((root / "out" / "europe_full_identity_resolution_xetra_source_matrix_v2_38ab.csv").open(encoding="utf-8")))
    assert report["resolved"] == 3
    by_asset = {r["asset_id"]: r for r in rows}
    assert by_asset["U1"]["resolved_company_name"] == "SAP SE"
    assert by_asset["U2"]["resolved_company_name"] == "ASML HOLDING NV"
    assert by_asset["U3"]["resolved_company_name"] == "NOVO NORDISK A-S"
    assert report["resolved_by_country"] == {"DE": 1, "NL": 1, "DK": 1}


def test_regression_reproduces_already_published_gb_result_exactly():
    """Real regression: this generalized script must reproduce the exact
    same result already published for the GB assets in v2.38V's
    correction (e.g. ticker "GUI" -> DIAGEO PLC) -- it is a superset of
    that work, not a different algorithm that happens to overlap."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "DIAGEO PLC LS-,28935185", "ISIN": "GB0002374006", "Mnemonic": "GUI"}])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [asset_row("U37439", "GUI", "XLON", "GB", "uk_companies_house_filings")])
        report = mod.build(matrix, xetra, root / "out")
        rows = list(csv.DictReader((root / "out" / "europe_full_identity_resolution_xetra_source_matrix_v2_38ab.csv").open(encoding="utf-8")))
    assert rows[0]["resolved_company_name"] == "DIAGEO PLC"
    assert rows[0]["isin"] == "GB0002374006"
    assert report["by_fundamental_route_and_status"] == {"uk_companies_house_filings:resolved": 1}


def test_mnemonic_not_in_reference_file_is_unresolved():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "SOME OTHER CO AG", "ISIN": "DE0000000001", "Mnemonic": "ZZZ"}])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [asset_row("U1", "NOTFOUND", "XETR", "DE")])
        report = mod.build(matrix, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_by_country"] == {"DE": 1}


def test_ambiguous_mnemonic_with_conflicting_isins_stays_unresolved():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [
            {"Instrument": "COMPANY A AG", "ISIN": "DE0000000001", "Mnemonic": "AMB"},
            {"Instrument": "COMPANY B AG", "ISIN": "DE0000000002", "Mnemonic": "AMB"},
        ])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [asset_row("U1", "AMB", "XETR", "DE")])
        report = mod.build(matrix, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_reasons"] == {"ambiguous_multiple_distinct_isins_for_mnemonic": 1}


def test_clean_company_name_strips_share_type_markers_alongside_denomination():
    """Real cases confirmed while building the France registry lookup:
    Xetra appends a share-type marker (bearer/registered/no-par-value)
    independently of the denomination notation, and the two can stack in
    either order. Genuinely abbreviated real-world tokens (e.g. "BNK" for
    "Bank") must stay untouched -- this only strips the closed set of
    share-type/denomination markers, never guesses at abbreviations."""
    mod = module()
    assert mod.clean_company_name("NEXANS INH.") == "NEXANS"
    assert mod.clean_company_name("SANOFI SA INHABER") == "SANOFI SA"
    assert mod.clean_company_name("HERMES INTERNATIONAL O.N.") == "HERMES INTERNATIONAL"
    assert mod.clean_company_name("MICHELIN  NOM.") == "MICHELIN"
    assert mod.clean_company_name("NOVARTIS NAM.     SF 0,49") == "NOVARTIS"  # share-type AND denomination stacked
    assert mod.clean_company_name("ERSTE GROUP BNK INH. O.N.") == "ERSTE GROUP BNK"  # two share-type markers stacked
    assert mod.clean_company_name("ZURICH INSUR.GR.NA.SF0,10") == "ZURICH INSUR.GR."  # "GR." (Gruppe) is a separate, genuine abbreviation left untouched -- only NA/SF0,10 are share-type/denomination noise


CASES = [
    test_no_jurisdiction_filter_resolves_across_every_country_in_one_pass,
    test_regression_reproduces_already_published_gb_result_exactly,
    test_mnemonic_not_in_reference_file_is_unresolved,
    test_ambiguous_mnemonic_with_conflicting_isins_stays_unresolved,
    test_clean_company_name_strips_share_type_markers_alongside_denomination,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AB-europe-full-identity-xetra-source/no-jurisdiction-filter/regression-vs-gb/ambiguous-isin/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
