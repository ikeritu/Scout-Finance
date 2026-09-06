#!/usr/bin/env python3
"""Offline QA for the v2.38AV mismatch-identity resolver -- the 25 census
rows v2.38N flagged COUNTRY_EXCHANGE_MISMATCH_REVIEW (a country tag that
conflicted with the mapped XETR/DE exchange) and that never flowed into
any later identity block. Same proven Xetra-source method as v2.38AB, now
selecting rows by resolution_status instead of taking a pre-filtered
matrix, and additionally deriving the real country from the ISIN prefix.
No network calls -- uses a small synthetic Xetra reference file fixture,
never the real, licensed Deutsche Boerse data.
"""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_mismatch_identity_xetra_source_v2_38av.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_mismatch_identity_xetra_source_v2_38av", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_xetra_fixture(path: Path, rows: list[dict[str, str]]) -> None:
    header = "Product Status;Instrument Status;Instrument;ISIN;Product ID;Instrument ID;WKN;Mnemonic;MIC Code;CCP eligible Code"
    lines = ["Market:;XETR", "Date Last Update:;01.01.2026", header]
    for r in rows:
        lines.append(f"Active;Active;{r['Instrument']};{r['ISIN']};1;1;WKN1;{r['Mnemonic']};XETR;Y")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def write_resolution(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "company_name", "country", "exchange", "mic", "home_country", "home_exchange", "resolution_status", "review_reason"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def mismatch_row(asset_id: str, ticker: str, placeholder: str, country: str) -> dict[str, str]:
    return {
        "asset_id": asset_id, "ticker": ticker, "company_name": placeholder, "country": country,
        "exchange": "XETR", "mic": "XETR", "home_country": "DE", "home_exchange": "XETRA",
        "resolution_status": "COUNTRY_EXCHANGE_MISMATCH_REVIEW",
        "review_reason": "Country and mapped exchange imply different home markets; manual validation required.",
    }


def resolved_row(asset_id: str, ticker: str, country: str) -> dict[str, str]:
    return {
        "asset_id": asset_id, "ticker": ticker, "company_name": "REAL CO AG", "country": country,
        "exchange": "XETR", "mic": "XETR", "home_country": country, "home_exchange": "XETRA",
        "resolution_status": "HOME_EXCHANGE_RESOLVED", "review_reason": "",
    }


def test_only_mismatch_status_rows_are_selected_others_are_ignored():
    """The input file (v2.38N's full 22,578-row resolution) carries many
    other statuses (already-resolved, out-of-scope, CBOE-secondary) -- this
    block must select ONLY the 25 flagged for manual review, never
    re-touch rows another block already closed."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "RTL GROUP", "ISIN": "LU0061462528", "Mnemonic": "RRTL"}])
        resolution = root / "resolution.csv"
        write_resolution(resolution, [
            mismatch_row("U1", "RRTL", "MDX1", "LU"),
            resolved_row("U2", "SAP", "DE"),
        ])
        report = mod.build(resolution, xetra, root / "out")
    assert report["input_assets"] == 1
    assert report["resolved"] == 1


def test_real_luxembourg_company_resolves_with_isin_country_overriding_de_exchange_flag():
    """Real case (RTL Group, ticker RRTL): the census tags it LU, the
    exchange mapping wrongly implies DE -- the ISIN prefix (LU) is what
    actually settles the conflict, not either of the two disagreeing
    fields v2.38N flagged for review."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "RTL GROUP", "ISIN": "LU0061462528", "Mnemonic": "RRTL"}])
        resolution = root / "resolution.csv"
        write_resolution(resolution, [mismatch_row("U37521", "RRTL", "MDX1", "LU")])
        report = mod.build(resolution, xetra, root / "out")
        rows = list(csv.DictReader((root / "out" / "europe_mismatch_identity_resolution_matrix_v2_38av.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["resolved_company_name"] == "RTL GROUP"
    assert rows[0]["isin_country_prefix"] == "LU"
    assert rows[0]["real_home_country_guess"] == "Luxembourg"
    assert report["confirmed_real_country_differs_from_de_home_exchange_flag"] == 1


def test_mnemonic_not_in_reference_file_is_unresolved():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "SOME OTHER CO", "ISIN": "LU0000000001", "Mnemonic": "ZZZ"}])
        resolution = root / "resolution.csv"
        write_resolution(resolution, [mismatch_row("U1", "NOTFOUND", "LUX0", "LU")])
        report = mod.build(resolution, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_reasons"] == {"mnemonic_not_found_in_xetra_reference_file": 1}


def test_ambiguous_mnemonic_stays_unresolved_never_guessed():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [
            {"Instrument": "COMPANY A SA", "ISIN": "LU0000000001", "Mnemonic": "AMB"},
            {"Instrument": "COMPANY B SA", "ISIN": "LU0000000002", "Mnemonic": "AMB"},
        ])
        resolution = root / "resolution.csv"
        write_resolution(resolution, [mismatch_row("U1", "AMB", "LUX0", "LU")])
        report = mod.build(resolution, xetra, root / "out")
    assert report["unresolved"] == 1
    assert report["unresolved_reasons"] == {"ambiguous_multiple_distinct_isins_for_mnemonic": 1}


def test_unmapped_isin_prefix_falls_back_to_the_raw_prefix_never_invented():
    """A country this project has never seen before (no entry in
    ISIN_PREFIX_COUNTRY) must surface as the raw 2-letter prefix, not a
    guessed or blank country name -- fail-visible, not fail-silent."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        xetra = root / "xetra.csv"
        write_xetra_fixture(xetra, [{"Instrument": "UNKNOWN JURISDICTION CO", "ISIN": "ZZ0000000001", "Mnemonic": "UNK"}])
        resolution = root / "resolution.csv"
        write_resolution(resolution, [mismatch_row("U1", "UNK", "LUX0", "LU")])
        report = mod.build(resolution, xetra, root / "out")
        rows = list(csv.DictReader((root / "out" / "europe_mismatch_identity_resolution_matrix_v2_38av.csv").open(encoding="utf-8")))
    assert rows[0]["real_home_country_guess"] == "ZZ"


CASES = [
    test_only_mismatch_status_rows_are_selected_others_are_ignored,
    test_real_luxembourg_company_resolves_with_isin_country_overriding_de_exchange_flag,
    test_mnemonic_not_in_reference_file_is_unresolved,
    test_ambiguous_mnemonic_stays_unresolved_never_guessed,
    test_unmapped_isin_prefix_falls_back_to_the_raw_prefix_never_invented,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AV-europe-mismatch-identity-xetra-source/status-filter/isin-country-override/ambiguous/unmapped-prefix/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
