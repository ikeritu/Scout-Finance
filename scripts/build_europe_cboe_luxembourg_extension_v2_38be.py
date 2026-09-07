#!/usr/bin/env python3
"""Block 9BE: extend Luxembourg coverage with the net-new companies the
v2.38BC Cboe Europe identity resolution found under country=LU (25 raw
matches), after removing what is NOT genuinely new: 8 real duplicates of
companies already resolved in v2.38AW/AX under a different Cboe listing
(ArcelorMittal, CPI Property Group, H2APEX Group SCA, Marley Spoon Group
SE, Logwin AG, and 3 "YIS MSCI ..." index-tracking products the original
ETF name-filter did not catch) -- leaving 17 real candidates.

This block reuses, unmodified, the exact same functions already proven in
v2.38AW (Luxembourg RCS resolution via GLEIF) and v2.38AX (Centrale des
Bilans fundamentals extraction) -- no new identity or extraction logic,
only a new candidate list and, for v2.38AX, reuse of the raw quarterly
XML cache already downloaded (no new bulk downloads needed unless a
target is only findable in a quarter not yet cached).

Real, load-bearing finding from resolving these 17: 6 of them turned out
to be Luxembourg INVESTMENT FUND compartments, not operating companies --
confirmed by their RCS-equivalent identifier format ("O" + digits +
underscore + sub-fund number, e.g. O00007020_00000026), structurally
different from a real company's "B" + digits RCS number. Generic-sounding
names ("Energy", "Renewable Energy", "Total", "DGA") were exactly the
tell -- fund sub-compartments are frequently named after their thematic
mandate, not a real legal entity name. These 6 are excluded from
fundamentals extraction entirely: a fund's regulatory filing (NAV,
prospectus) is not the balance-sheet/P&L data this project tracks, and
attempting to fetch Centrale des Bilans data for a fund identifier would
be a category error, not a data gap.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BC_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38bc_europe_cboe_secondary_identity_full/europe_cboe_secondary_identity_full_matrix_v2_38bc.csv"
AW_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38aw_europe_luxembourg_rcs_gleif/europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv"
AX_RAW_CACHE = ROOT / "outputs/full_universe_source_acquisition/v2_38ax_europe_luxembourg_fundamentals/raw_quarterly_xml_cache_v2_38ax"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38be_europe_cboe_luxembourg_extension"
PHASE = "v2.38BE-europe-cboe-luxembourg-extension"

# Real fund-compartment naming patterns confirmed live (index trackers
# with country/theme names in their legal name) that the original v2.38BB
# ETF_RE did not anticipate, because Cboe Europe's own naming for these
# is closer to a real company name ("Zabka Group") than an obvious ETF
# ticker suffix.
INDEX_FUND_RE = re.compile(r"MSCI |SELECTION|UNIVERSAL|INDEX| ETF|ETC|ETP|FUND|TRUST UNIT", re.IGNORECASE)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_already_known_lu_names(aw_matrix: Path) -> set[str]:
    names = set()
    with aw_matrix.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("gleif_lookup_status") == "resolved":
                names.add(row["gleif_legal_name"].strip().upper())
    return names


def select_new_candidates(bc_matrix: Path, already_known: set[str]) -> list[dict[str, str]]:
    candidates = []
    with bc_matrix.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") != "resolved" or row.get("country") != "LU":
                continue
            name = row.get("legal_name", "")
            if not name or name.strip().upper() in already_known or INDEX_FUND_RE.search(name):
                continue
            candidates.append(row)
    return candidates


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def build(bc_matrix: Path, aw_matrix: Path, ax_raw_cache: Path, output_dir: Path, execute: bool) -> dict[str, Any]:
    already_known = load_already_known_lu_names(aw_matrix)
    candidates = select_new_candidates(bc_matrix, already_known)

    if not execute:
        return {"phase": PHASE, "status": "DRY_RUN", "new_candidates": len(candidates), "network_used": False, "phase9c_authorized": False}

    v38aw = load_module("resolve_europe_luxembourg_rcs_gleif_v2_38aw", ROOT / "scripts/resolve_europe_luxembourg_rcs_gleif_v2_38aw.py")
    v38ax = load_module("fetch_europe_luxembourg_fundamentals_v2_38ax", ROOT / "scripts/fetch_europe_luxembourg_fundamentals_v2_38ax.py")

    rcs_input_rows = [
        {"asset_id": r["asset_id"], "ticker": r["ticker"], "resolved_company_name": r["legal_name"], "isin": "", "real_home_country_guess": "Luxembourg", "resolution_status": "resolved"}
        for r in candidates
    ]
    tmp_rcs_input = output_dir / "_tmp_rcs_input_v2_38be.csv"
    write_csv(tmp_rcs_input, rcs_input_rows, ["asset_id", "ticker", "resolved_company_name", "isin", "real_home_country_guess", "resolution_status"])
    rcs_report = v38aw.build(tmp_rcs_input, output_dir, execute=True)
    rcs_matrix_rows = list(csv.DictReader((output_dir / "europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv").open(encoding="utf-8")))
    tmp_rcs_input.unlink(missing_ok=True)

    real_companies = [r for r in rcs_matrix_rows if r["gleif_lookup_status"] == "resolved" and r["rcs_number"].startswith("B")]
    fund_compartments = [r for r in rcs_matrix_rows if r["gleif_lookup_status"] == "resolved" and not r["rcs_number"].startswith("B")]
    unresolved_rcs = [r for r in rcs_matrix_rows if r["gleif_lookup_status"] != "resolved"]

    fundamentals_input_rows = [{"asset_id": r["asset_id"], "ticker": r["ticker"], "isin": "", "gleif_lookup_status": "resolved", "rcs_number": r["rcs_number"]} for r in real_companies]
    tmp_fund_input = output_dir / "_tmp_fundamentals_input_v2_38be.csv"
    write_csv(tmp_fund_input, fundamentals_input_rows, ["asset_id", "ticker", "isin", "gleif_lookup_status", "rcs_number"])
    fund_report = v38ax.build(tmp_fund_input, output_dir, ax_raw_cache, v38ax.QUARTER_URLS, execute=True) if real_companies else {"found": 0, "not_found": 0}
    tmp_fund_input.unlink(missing_ok=True)

    # Rename v2.38AX's generic output filenames to this block's own, and
    # move the RCS matrix + fund-compartment record to their final names.
    for src_name, dst_name in [
        ("europe_luxembourg_fundamental_records_v2_38ax.jsonl", "europe_cboe_luxembourg_extension_fundamental_records_v2_38be.jsonl"),
        ("europe_luxembourg_fundamentals_summary_v2_38ax.json", "europe_cboe_luxembourg_extension_fundamentals_summary_v2_38be.json"),
        ("europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv", "europe_cboe_luxembourg_extension_rcs_matrix_v2_38be.csv"),
    ]:
        src = output_dir / src_name
        if src.exists():
            src.replace(output_dir / dst_name)
    for stale in ("europe_luxembourg_rcs_gleif_summary_v2_38aw.json",):
        (output_dir / stale).unlink(missing_ok=True)

    write_jsonl(output_dir / "europe_cboe_luxembourg_extension_fund_compartments_excluded_v2_38be.jsonl", fund_compartments)

    report = {
        "phase": PHASE, "new_candidates": len(candidates),
        "rcs_resolved_real_companies": len(real_companies), "rcs_resolved_fund_compartments_excluded": len(fund_compartments),
        "rcs_unresolved": len(unresolved_rcs),
        "fundamentals_found": fund_report.get("found", 0), "fundamentals_not_found": fund_report.get("not_found", 0),
        "note": "Fund compartments (RCS-equivalent identifier does not start with 'B') are real GLEIF-registered entities but are investment fund sub-funds, not operating companies -- excluded from fundamentals extraction as a category error, not a data gap.",
        "network_used": True, "credentials_used": False, "phase9c_authorized": False,
    }
    write_text(output_dir / "europe_cboe_luxembourg_extension_summary_v2_38be.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bc-matrix", type=Path, default=BC_MATRIX)
    parser.add_argument("--aw-matrix", type=Path, default=AW_MATRIX)
    parser.add_argument("--ax-raw-cache", type=Path, default=AX_RAW_CACHE)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    report = build(args.bc_matrix, args.aw_matrix, args.ax_raw_cache, args.output_dir, args.execute)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
