#!/usr/bin/env python3
"""Block 9AX: fetch real annual-accounts fundamentals for the 18 Luxembourg
companies resolved to a real RCS number in v2.38AW, from the Centrale des
Bilans (STATEC) quarterly bulk XML files -- a genuinely free, official,
CC-BY-SA open dataset on data.public.lu, no account, no CAPTCHA (confirmed
live: direct HTTPS download from download.data.public.lu, unlike Belgium's
CAPTCHA-gated bulk file or Italy's reCAPTCHA-gated portal).

Real structure confirmed live via byte-range samples of the actual 2026 Q1
file before writing this script: every filing is a <Declarer> element
keyed by <RcsNumber> (the same "B" number GLEIF returns), containing one or
more <Declaration type="CA_BILAN|CA_BILANABR|CA_COMPP|CA_COMPPABR"> (balance
sheet / abbreviated balance sheet / profit-and-loss / abbreviated P&L) with
a <FormData> tree of <Field id=... ecdf=...><Label/><Data/><PreviousData/>
children, arbitrarily nested.

Real, load-bearing finding about confidentiality: the dataset's own
description says companies can tick a box marking their balance sheet
and/or P&L as confidential at filing time. Live sampling never found any
"confidential" marker field anywhere in the XML -- the mechanism is
simpler and more absolute: a confidential statement is not included in the
public file at all. This script therefore records, per company, WHICH
declaration types were actually found (never assumes a missing type means
"zero" -- it means "not disclosed publicly", exactly the same fail-closed
discipline already used across every other country in this project for a
missing accounting concept).

Bulk files are large (100-800MB per quarter, 58 quarters total = ~7GB) --
downloading all of them for 18 companies would be wasteful. This script
scans quarters NEWEST-FIRST and stops as soon as every target RCS number
has been found at least once (a hit in a newer quarter can only be more
recent than any hit in an older one, so once found there is nothing further
to look for), falling back to older quarters only for companies still
missing. Each quarter is downloaded once into a local raw cache (gitignored,
same convention as every other provider's raw bulk data in this project)
and re-used on any later re-run -- resumable, atomic writes throughout.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
INPUT_RCS_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38aw_europe_luxembourg_rcs_gleif/europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ax_europe_luxembourg_fundamentals"
RAW_CACHE = OUT / "raw_quarterly_xml_cache_v2_38ax"
PHASE = "v2.38AX-europe-luxembourg-fundamentals"

# Newest-first: the dataset's own resource list, confirmed live via the
# data.public.lu REST API (https://data.public.lu/api/1/datasets/donnees-comptes-annuels/).
QUARTER_URLS = [
    ("2026q2", "https://download.data.public.lu/resources/donnees-comptes-annuels/20260630-075458/deposit-2026q2.xml"),
    ("2026q1", "https://download.data.public.lu/resources/donnees-comptes-annuels/20260401-075415/deposit-2026q1.xml"),
    ("2025q4", "https://download.data.public.lu/resources/donnees-comptes-annuels/20251231-100029/deposit-2025q4.xml"),
    ("2025q3", "https://download.data.public.lu/resources/donnees-comptes-annuels/20251003-073530/work03.gouv.etat.lu-statec-talend-data-prod-talend-cdb-cdb-diffusion-data-upload-deposit-2025q3.xml"),
    ("2025q2", "https://download.data.public.lu/resources/donnees-comptes-annuels/20250701-093948/deposit-2025q2.xml"),
    ("2025q1", "https://download.data.public.lu/resources/donnees-comptes-annuels/20250401-094627/deposit-2025q1.xml"),
    ("2024q4", "https://download.data.public.lu/resources/donnees-comptes-annuels/20241231-094209/deposit-2024q4.xml"),
    ("2024q3", "https://download.data.public.lu/resources/donnees-comptes-annuels/20241001-095832/deposit-2024q3.xml"),
]

# Real Luxembourg standard chart-of-accounts (eCDF) labels, confirmed live
# from the actual 2026 Q1 file, used to pick out the handful of aggregate
# concepts this project tracks everywhere else (revenue, net_profit,
# total_assets, equity) out of the much larger nested FormData tree. Label
# text match only (case/accent-insensitive substring), never an assumed
# fixed "id" or "ecdf" code -- those were not documented anywhere public
# this project could verify, so trusting label text (already this
# project's fallback method for Austria/Germany-vocabulary concepts) is
# the safer, fail-visible choice.
CONCEPT_LABEL_MARKERS = {
    "total_assets": ["total du bilan (actif)", "total de l'actif"],
    "equity": ["capitaux propres"],
    "revenue": ["chiffre d'affaires net", "montant net du chiffre d'affaires"],
    "net_profit": ["resultat de l'exercice", "résultat de l'exercice"],
}
BALANCE_SHEET_TYPES = {"CA_BILAN", "CA_BILANABR"}
PROFIT_LOSS_TYPES = {"CA_COMPP", "CA_COMPPABR"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def target_rcs_numbers(rcs_matrix: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {r["rcs_number"]: r for r in rcs_matrix if r.get("gleif_lookup_status") == "resolved" and r.get("rcs_number")}


def download_quarter(url: str, dest: Path) -> None:
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    request = urllib.request.Request(url, headers={"User-Agent": "ScoutFinanceResearch/1.0 (+non-commercial research)"})
    with urllib.request.urlopen(request, timeout=300) as response, tmp.open("wb") as f:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dest)


def normalize_label(label: str) -> str:
    return (label or "").strip().lower().replace("é", "e").replace("è", "e")


def match_concept(label: str) -> str | None:
    normalized = normalize_label(label)
    for concept, markers in CONCEPT_LABEL_MARKERS.items():
        for marker in markers:
            if normalize_label(marker) in normalized:
                return concept
    return None


def walk_fields(field_elem: ET.Element, sink: dict[str, dict[str, str]]) -> None:
    """Recurse the arbitrarily-nested <Field> tree, collecting every field
    whose label matches one of our tracked concepts. A field can appear
    more than once at different nesting depths across BILAN vs BILANABR
    variants -- last one found wins, since within a single declaration
    they are the same real reported figure."""
    label_elem = field_elem.find("Label")
    data_elem = field_elem.find("Data")
    concept = match_concept(label_elem.text if label_elem is not None else "")
    if concept and data_elem is not None and data_elem.text:
        sink[concept] = {"label": label_elem.text.strip(), "value": data_elem.text.strip(), "field_id": field_elem.get("id", "")}
    for child in field_elem.findall("Field"):
        walk_fields(child, sink)


def extract_declarer(declarer_elem: ET.Element, quarter: str) -> dict[str, Any]:
    rcs_elem = declarer_elem.find("RcsNumber")
    name_elem = declarer_elem.find("LegalUnitName")
    rcs_number = rcs_elem.text.strip() if rcs_elem is not None and rcs_elem.text else ""
    legal_unit_name = name_elem.text.strip() if name_elem is not None and name_elem.text else ""

    declarations_found = []
    concepts: dict[str, dict[str, str]] = {}
    best_end_date = ""
    for decl in declarer_elem.findall("Declaration"):
        decl_type = decl.get("type", "")
        end_date_elem = decl.find("EndDate")
        year_ref_elem = decl.find("YearRef")
        end_date = end_date_elem.text.strip() if end_date_elem is not None and end_date_elem.text else ""
        declarations_found.append({"type": decl_type, "end_date": end_date, "year_ref": year_ref_elem.text.strip() if year_ref_elem is not None and year_ref_elem.text else ""})
        if end_date > best_end_date:
            best_end_date = end_date
        for form_data in decl.findall("FormData"):
            for field in form_data.findall("Field"):
                walk_fields(field, concepts)

    return {
        "rcs_number": rcs_number, "legal_unit_name": legal_unit_name, "quarter_found_in": quarter,
        "declaration_types_found": sorted({d["type"] for d in declarations_found}),
        "most_recent_period_end_date": best_end_date, "declarations": declarations_found,
        "concepts": concepts,
        "balance_sheet_disclosed": bool(BALANCE_SHEET_TYPES & {d["type"] for d in declarations_found}),
        "profit_loss_disclosed": bool(PROFIT_LOSS_TYPES & {d["type"] for d in declarations_found}),
    }


def scan_quarter_file(path: Path, targets_remaining: set[str], quarter: str) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    context = ET.iterparse(str(path), events=("end",))
    for _event, elem in context:
        if elem.tag != "Declarer":
            continue
        rcs_elem = elem.find("RcsNumber")
        rcs_number = rcs_elem.text.strip() if rcs_elem is not None and rcs_elem.text else ""
        if rcs_number in targets_remaining:
            found[rcs_number] = extract_declarer(elem, quarter)
        elem.clear()
    return found


def build(input_rcs_matrix: Path, output_dir: Path, raw_cache: Path, quarters: list[tuple[str, str]], execute: bool) -> dict[str, Any]:
    rcs_rows = read_csv(input_rcs_matrix)
    targets = target_rcs_numbers(rcs_rows)
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if not execute:
        return {"status": "DRY_RUN", "target_companies": len(targets), "quarters_available": len(quarters), "network_used": False, "phase9c_authorized": False}

    remaining = set(targets.keys())
    all_found: dict[str, dict[str, Any]] = {}
    quarters_scanned = []
    for quarter, url in quarters:
        if not remaining:
            break
        dest = raw_cache / f"deposit-{quarter}.xml"
        download_quarter(url, dest)
        hits = scan_quarter_file(dest, remaining, quarter)
        all_found.update(hits)
        remaining -= set(hits.keys())
        quarters_scanned.append({"quarter": quarter, "new_matches": len(hits), "still_remaining_after": len(remaining)})

    records = []
    for rcs_number, meta in targets.items():
        if rcs_number in all_found:
            hit = all_found[rcs_number]
            records.append({**hit, "asset_id": meta["asset_id"], "ticker": meta["ticker"], "isin": meta["isin"], "fetch_status": "resolved", "phase": PHASE, "created_at_utc": created_at})
        else:
            records.append({"rcs_number": rcs_number, "legal_unit_name": "", "quarter_found_in": "", "declaration_types_found": [], "most_recent_period_end_date": "", "declarations": [], "concepts": {}, "balance_sheet_disclosed": False, "profit_loss_disclosed": False, "asset_id": meta["asset_id"], "ticker": meta["ticker"], "isin": meta["isin"], "fetch_status": "unresolved_not_found_in_scanned_quarters", "phase": PHASE, "created_at_utc": created_at})

    resolved_records = [r for r in records if r["fetch_status"] == "resolved"]
    concept_coverage = {c: sum(1 for r in resolved_records if c in r["concepts"]) for c in CONCEPT_LABEL_MARKERS}
    report = {
        "phase": PHASE, "target_companies": len(targets), "found": len(resolved_records), "not_found": len(records) - len(resolved_records),
        "quarters_scanned": quarters_scanned, "concept_coverage_among_found": concept_coverage,
        "balance_sheet_disclosed_count": sum(1 for r in resolved_records if r["balance_sheet_disclosed"]),
        "profit_loss_disclosed_count": sum(1 for r in resolved_records if r["profit_loss_disclosed"]),
        "note": "A company found with balance_sheet_disclosed=false or profit_loss_disclosed=false did file that quarter but marked that specific statement confidential at deposit time (Art.70/71 of the 2002 law) -- the public bulk file simply omits it. This is never treated as zero.",
        "credentials_used": False, "network_used": True, "phase9c_authorized": False,
    }
    write_jsonl(output_dir / "europe_luxembourg_fundamental_records_v2_38ax.jsonl", records)
    write_text(output_dir / "europe_luxembourg_fundamentals_summary_v2_38ax.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rcs-matrix", type=Path, default=INPUT_RCS_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--raw-cache", type=Path, default=RAW_CACHE)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    report = build(args.input_rcs_matrix, args.output_dir, args.raw_cache, QUARTER_URLS, args.execute)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
