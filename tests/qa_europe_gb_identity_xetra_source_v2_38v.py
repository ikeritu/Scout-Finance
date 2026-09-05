#!/usr/bin/env python3
"""Offline QA for the corrected, Xetra-source-based GB identity resolver.
No network calls -- uses a small synthetic Xetra reference file fixture,
never the real, licensed Deutsche Boerse data. Covers the exact real bug
this resolver fixes: a mnemonic that happens to collide with an unrelated
company's real LSE ticker must never be resolved via that collision.
"""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_gb_identity_xetra_source_v2_38v.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_gb_identity_xetra_source_v2_38v", SCRIPT)
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
    fields = ["asset_id", "ticker", "company_name", "jurisdiction_code", "mic", "country"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def gb_row(asset_id: str, ticker: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": "UKI0", "jurisdiction_code": "GB", "mic": "XLON", "country": "GB"}


def test_exact_mnemonic_resolves_to_real_instrument_and_isin():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "DIAGEO PLC LS-,28935185", "ISIN": "GB0002374006", "Mnemonic": "GUI"}])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [gb_row("U1", "GUI")])
        report = mod.build(matrix, xetra, root / "out")
        rows = list(csv.DictReader((root / "out" / "europe_gb_identity_resolution_xetra_source_matrix_v2_38v.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["resolved_company_name"] == "DIAGEO PLC"
    assert rows[0]["resolved_company_name_raw"] == "DIAGEO PLC LS-,28935185"
    assert rows[0]["isin"] == "GB0002374006"


def test_ticker_collision_regression_never_uses_wrong_companys_ticker_match():
    """This is the exact real bug this resolver fixes: a Xetra mnemonic
    ("SCT") that happens to be a completely different real company's
    ("Softcat") actual LSE ticker must resolve to the company the Xetra
    reference file actually names for that mnemonic (SSE PLC), never to
    whatever an unrelated ticker-based search would have found."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "SSE PLC    LS-,50", "ISIN": "GB0007908733", "Mnemonic": "SCT"}])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [gb_row("U1", "SCT")])
        report = mod.build(matrix, xetra, root / "out")
        rows = list(csv.DictReader((root / "out" / "europe_gb_identity_resolution_xetra_source_matrix_v2_38v.csv").open(encoding="utf-8")))
    assert rows[0]["resolved_company_name"] == "SSE PLC"
    assert "SOFTCAT" not in rows[0]["resolved_company_name"].upper()
    assert rows[0]["isin"] == "GB0007908733"


def test_mnemonic_not_in_reference_file_is_unresolved():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "SOME OTHER CO PLC", "ISIN": "GB0000000001", "Mnemonic": "ZZZ"}])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [gb_row("U1", "NOTFOUND")])
        report = mod.build(matrix, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_reasons"] == {"mnemonic_not_found_in_xetra_reference_file": 1}


def test_ambiguous_mnemonic_with_conflicting_isins_stays_unresolved():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [
            {"Instrument": "COMPANY A PLC", "ISIN": "GB0000000001", "Mnemonic": "AMB"},
            {"Instrument": "COMPANY B PLC", "ISIN": "GB0000000002", "Mnemonic": "AMB"},
        ])
        matrix = root / "matrix.csv"
        write_matrix(matrix, [gb_row("U1", "AMB")])
        report = mod.build(matrix, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_reasons"] == {"ambiguous_multiple_distinct_isins_for_mnemonic": 1}


def test_clean_company_name_strips_denomination_suffix_without_losing_raw_value():
    mod = module()
    assert mod.clean_company_name("DIAGEO PLC LS-,28935185") == "DIAGEO PLC"
    assert mod.clean_company_name("KINGFISHER  LS-,157142857") == "KINGFISHER"
    assert mod.clean_company_name("PLAIN NAME WITH NO SUFFIX") == "PLAIN NAME WITH NO SUFFIX"


CASES = [
    test_exact_mnemonic_resolves_to_real_instrument_and_isin,
    test_ticker_collision_regression_never_uses_wrong_companys_ticker_match,
    test_mnemonic_not_in_reference_file_is_unresolved,
    test_ambiguous_mnemonic_with_conflicting_isins_stays_unresolved,
    test_clean_company_name_strips_denomination_suffix_without_losing_raw_value,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38V-gb-identity-xetra-source/ticker-collision-regression/ambiguous-isin/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
