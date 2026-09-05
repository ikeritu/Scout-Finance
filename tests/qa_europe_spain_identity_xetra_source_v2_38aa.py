#!/usr/bin/env python3
"""Offline QA for the v2.38AA Spain identity resolver -- the same proven
Xetra-source/ISIN method already validated on GB (40/40, v2.38V) and
Ireland (17/17, v2.38Z), applied to the 15 Bolsa de Madrid assets that
share the exact same root-cause placeholder issue (company_name="ESP0").
No network calls -- uses a small synthetic Xetra reference file fixture,
never the real, licensed Deutsche Boerse data.
"""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_spain_identity_xetra_source_v2_38aa.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_spain_identity_xetra_source_v2_38aa", SCRIPT)
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
    fields = ["asset_id", "ticker", "company_name", "mic", "country", "jurisdiction_code"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def es_row(asset_id: str, ticker: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": "ESP0", "mic": "XMAD", "country": "ES", "jurisdiction_code": "ES"}


def test_exact_mnemonic_resolves_to_real_instrument_and_isin():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "IBERDROLA SA EO-,75", "ISIN": "ES0144580Y14", "Mnemonic": "IBE1"}])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [es_row("U1", "IBE1")])
        report = mod.build(matrix, xetra, root / "out")
        rows = list(csv.DictReader((root / "out" / "europe_spain_identity_resolution_xetra_source_matrix_v2_38aa.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["resolved_company_name"] == "IBERDROLA SA"
    assert rows[0]["resolved_company_name_raw"] == "IBERDROLA SA EO-,75"
    assert rows[0]["isin"] == "ES0144580Y14"


def test_non_spain_rows_in_input_matrix_are_filtered_out():
    """The real input file (v2.38S's matrix) mixes GB and ES rows -- the
    filter on jurisdiction_code must exclude GB, never resolve it here."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [
            {"Instrument": "IBERDROLA SA EO-,75", "ISIN": "ES0144580Y14", "Mnemonic": "IBE1"},
            {"Instrument": "SOME GB CO PLC", "ISIN": "GB0000000001", "Mnemonic": "GBX"},
        ])
        matrix = root / "matrix.csv"
        gb_row = {"asset_id": "U2", "ticker": "GBX", "company_name": "UKI0", "mic": "XLON", "country": "GB", "jurisdiction_code": "GB"}
        write_matrix(matrix, [es_row("U1", "IBE1"), gb_row])
        report = mod.build(matrix, xetra, root / "out")
    assert report["input_assets"] == 1 and report["resolved"] == 1


def test_mnemonic_not_in_reference_file_is_unresolved():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "SOME OTHER CO SA", "ISIN": "ES0000000001", "Mnemonic": "ZZZ"}])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [es_row("U1", "NOTFOUND")])
        report = mod.build(matrix, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_reasons"] == {"mnemonic_not_found_in_xetra_reference_file": 1}


def test_ambiguous_mnemonic_with_conflicting_isins_stays_unresolved():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [
            {"Instrument": "COMPANY A SA", "ISIN": "ES0000000001", "Mnemonic": "AMB"},
            {"Instrument": "COMPANY B SA", "ISIN": "ES0000000002", "Mnemonic": "AMB"},
        ])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [es_row("U1", "AMB")])
        report = mod.build(matrix, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_reasons"] == {"ambiguous_multiple_distinct_isins_for_mnemonic": 1}


def test_clean_company_name_strips_denomination_suffix_without_losing_raw_value():
    mod = module()
    assert mod.clean_company_name("IBERDROLA SA EO-,75") == "IBERDROLA SA"
    assert mod.clean_company_name("REPSOL SA      EO-1") == "REPSOL SA"
    assert mod.clean_company_name("PLAIN NAME WITH NO SUFFIX") == "PLAIN NAME WITH NO SUFFIX"


CASES = [
    test_exact_mnemonic_resolves_to_real_instrument_and_isin,
    test_non_spain_rows_in_input_matrix_are_filtered_out,
    test_mnemonic_not_in_reference_file_is_unresolved,
    test_ambiguous_mnemonic_with_conflicting_isins_stays_unresolved,
    test_clean_company_name_strips_denomination_suffix_without_losing_raw_value,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AA-spain-identity-xetra-source/jurisdiction-filter/ambiguous-isin/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
