#!/usr/bin/env python3
"""Offline QA for the v2.38Z Ireland identity resolver -- the same proven
Xetra-source/ISIN method already validated on the 40 GB assets (v2.38V
correction, 40/40 resolved, 0 ambiguous), applied to the 17 Euronext
Dublin assets that share the exact same root-cause placeholder issue. No
network calls -- uses a small synthetic Xetra reference file fixture,
never the real, licensed Deutsche Boerse data.
"""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_ireland_identity_xetra_source_v2_38z.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_ireland_identity_xetra_source_v2_38z", SCRIPT)
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
    fields = ["asset_id", "ticker", "company_name_source_value", "home_mic", "home_country"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def ie_row(asset_id: str, ticker: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "company_name_source_value": "UKI0", "home_mic": "XDUB", "home_country": "IE"}


def test_exact_mnemonic_resolves_to_real_instrument_and_isin():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "LINDE PLC LS-,001", "ISIN": "IE00BZ12WP82", "Mnemonic": "LIN"}])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [ie_row("U1", "LIN")])
        report = mod.build(matrix, xetra, root / "out")
        rows = list(csv.DictReader((root / "out" / "europe_ireland_identity_resolution_xetra_source_matrix_v2_38z.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["resolved_company_name"] == "LINDE PLC"
    assert rows[0]["resolved_company_name_raw"] == "LINDE PLC LS-,001"
    assert rows[0]["isin"] == "IE00BZ12WP82"


def test_non_ireland_rows_in_input_matrix_are_filtered_out():
    """Same input file this resolver reads from (v2.38T's manual review
    pack matrix) is Ireland-only by construction, but the resolver still
    filters on home_country defensively -- a GB row accidentally present
    must never be resolved by this script."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [
            {"Instrument": "LINDE PLC LS-,001", "ISIN": "IE00BZ12WP82", "Mnemonic": "LIN"},
            {"Instrument": "SOME GB CO PLC", "ISIN": "GB0000000001", "Mnemonic": "GBX"},
        ])
        matrix = root / "matrix.csv"
        gb_row = {"asset_id": "U2", "ticker": "GBX", "company_name_source_value": "UKI0", "home_mic": "XLON", "home_country": "GB"}
        write_matrix(matrix, [ie_row("U1", "LIN"), gb_row])
        report = mod.build(matrix, xetra, root / "out")
    assert report["input_assets"] == 1 and report["resolved"] == 1


def test_mnemonic_not_in_reference_file_is_unresolved():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "SOME OTHER CO PLC", "ISIN": "IE0000000001", "Mnemonic": "ZZZ"}])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [ie_row("U1", "NOTFOUND")])
        report = mod.build(matrix, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_reasons"] == {"mnemonic_not_found_in_xetra_reference_file": 1}


def test_ambiguous_mnemonic_with_conflicting_isins_stays_unresolved():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [
            {"Instrument": "COMPANY A PLC", "ISIN": "IE0000000001", "Mnemonic": "AMB"},
            {"Instrument": "COMPANY B PLC", "ISIN": "IE0000000002", "Mnemonic": "AMB"},
        ])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [ie_row("U1", "AMB")])
        report = mod.build(matrix, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_reasons"] == {"ambiguous_multiple_distinct_isins_for_mnemonic": 1}


def test_clean_company_name_strips_denomination_suffix_without_losing_raw_value():
    mod = module()
    assert mod.clean_company_name("LINDE PLC LS-,001") == "LINDE PLC"
    assert mod.clean_company_name("KERRY GROUP PLC      LS 0,10") == "KERRY GROUP PLC"
    assert mod.clean_company_name("PLAIN NAME WITH NO SUFFIX") == "PLAIN NAME WITH NO SUFFIX"


CASES = [
    test_exact_mnemonic_resolves_to_real_instrument_and_isin,
    test_non_ireland_rows_in_input_matrix_are_filtered_out,
    test_mnemonic_not_in_reference_file_is_unresolved,
    test_ambiguous_mnemonic_with_conflicting_isins_stays_unresolved,
    test_clean_company_name_strips_denomination_suffix_without_losing_raw_value,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38Z-ireland-identity-xetra-source/jurisdiction-filter/ambiguous-isin/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
