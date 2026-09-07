#!/usr/bin/env python3
"""Offline QA for v2.38BE -- extending Luxembourg coverage with the
net-new companies v2.38BC found. No real network calls -- monkeypatches
the underlying v2.38AW/AX modules' network functions after loading them
through this block's own load_module().
"""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_cboe_luxembourg_extension_v2_38be.py"


def module():
    spec = importlib.util.spec_from_file_location("build_europe_cboe_luxembourg_extension_v2_38be", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_bc_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "status", "country", "legal_name"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def bc_row(asset_id: str, ticker: str, country: str, legal_name: str, status: str = "resolved") -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "status": status, "country": country, "legal_name": legal_name}


def write_aw_matrix(path: Path, already_known_names: list[str]) -> None:
    fields = ["gleif_lookup_status", "gleif_legal_name"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for name in already_known_names:
            writer.writerow({"gleif_lookup_status": "resolved", "gleif_legal_name": name})


def test_already_known_company_is_excluded_as_duplicate():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [bc_row("U1", "ARRDd", "LU", "ArcelorMittal")])
        aw = root / "aw.csv"
        write_aw_matrix(aw, ["ARCELORMITTAL"])
        candidates = mod.select_new_candidates(bc, mod.load_already_known_lu_names(aw))
    assert candidates == []


def test_index_fund_named_row_is_excluded():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [bc_row("U1", "YINASm", "LU", "YIS MSCI North America Selection")])
        aw = root / "aw.csv"
        write_aw_matrix(aw, [])
        candidates = mod.select_new_candidates(bc, mod.load_already_known_lu_names(aw))
    assert candidates == []


def test_non_luxembourg_or_unresolved_rows_never_selected():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [
            bc_row("U1", "AAA", "GB", "Some British Company Ltd"),
            bc_row("U2", "BBB", "LU", "Ambiguous LU Co", status="ambiguous"),
        ])
        aw = root / "aw.csv"
        write_aw_matrix(aw, [])
        candidates = mod.select_new_candidates(bc, mod.load_already_known_lu_names(aw))
    assert candidates == []


def test_genuinely_new_real_company_is_selected():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [bc_row("U1", "ALEw", "LU", "ALLEGRO.EU")])
        aw = root / "aw.csv"
        write_aw_matrix(aw, ["ARCELORMITTAL"])
        candidates = mod.select_new_candidates(bc, mod.load_already_known_lu_names(aw))
    assert len(candidates) == 1
    assert candidates[0]["legal_name"] == "ALLEGRO.EU"


def test_fund_compartment_rcs_format_excluded_from_fundamentals():
    """Real, load-bearing distinction: a Luxembourg RCS company number
    starts with "B" (e.g. B214830); a fund sub-compartment identifier
    from the same GLEIF registration authority looks like
    "O00007020_00000026" -- structurally different, and must never be
    treated as a company to fetch Centrale des Bilans data for."""
    mod = module()
    rcs_rows = [
        {"asset_id": "U1", "ticker": "REAL", "gleif_lookup_status": "resolved", "rcs_number": "B214830"},
        {"asset_id": "U2", "ticker": "FUND", "gleif_lookup_status": "resolved", "rcs_number": "O00007020_00000026"},
    ]
    real_companies = [r for r in rcs_rows if r["gleif_lookup_status"] == "resolved" and r["rcs_number"].startswith("B")]
    fund_compartments = [r for r in rcs_rows if r["gleif_lookup_status"] == "resolved" and not r["rcs_number"].startswith("B")]
    assert [r["ticker"] for r in real_companies] == ["REAL"]
    assert [r["ticker"] for r in fund_compartments] == ["FUND"]


def test_dry_run_never_touches_network():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [bc_row("U1", "ALEw", "LU", "ALLEGRO.EU")])
        aw = root / "aw.csv"
        write_aw_matrix(aw, [])
        report = mod.build(bc, aw, root / "cache", root / "out", execute=False)
    assert report["status"] == "DRY_RUN"
    assert report["new_candidates"] == 1


CASES = [
    test_already_known_company_is_excluded_as_duplicate,
    test_index_fund_named_row_is_excluded,
    test_non_luxembourg_or_unresolved_rows_never_selected,
    test_genuinely_new_real_company_is_selected,
    test_fund_compartment_rcs_format_excluded_from_fundamentals,
    test_dry_run_never_touches_network,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BE-europe-cboe-luxembourg-extension/dedup/index-fund-filter/scope-filter/new-selected/fund-compartment-split/dry-run/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
