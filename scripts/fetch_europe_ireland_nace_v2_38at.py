#!/usr/bin/env python3
"""Block 9AT: fetch the real NACE Rev.2 code for the 8 Irish companies
already confirmed by v2.38Z's CRO lookup, continuing the attack on the
Europe sector-classification gap. No new policy decision needed: this
reuses the exact same free, no-key, official CRO open-data endpoint
(opendata.cro.ie) already used for identity in v2.38Z -- confirmed live
that every real record already carries a `nace_v2_code` field, never
captured before (v2.38Z only extracted company_status/type/reg_date).

A second field, `princ_object_code`, also exists on these records but is
deliberately NOT used here. Confirmed live for a real, concrete case:
Alkermes plc (company number 498284) shows `princ_object_code: "24.41"`
("Manufacture of basic precious and non-ferrous metals") -- Alkermes is
a real, well-known pharmaceutical company; this code cannot be its real
activity. Alkermes plc was a newly-incorporated Irish holding entity
formed for the 2011 Alkermes/Elan Drug Technologies merger (confirmed via
Alkermes' own investor-relations press release), so this is not stale
data left over from a repurposed shell -- the "principal object" field
most likely reflects boilerplate objects-clause text from the entity's
memorandum of association rather than any real operating classification.
Given a confirmed wrong value on a well-known company, `princ_object_code`
is not trustworthy enough to feed into a sector-matching engine and is
recorded here only for traceability, never used as sector-matching text.

Blocked by default; --execute is required (no credential needed, but
real network calls stay gated behind this explicit flag, matching this
project's convention for every free no-key registry lookup).
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38z_europe_ireland_identity_resolution/europe_ireland_cro_lookup_matrix_v2_38z.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38at_europe_ireland_nace"
PHASE = "v2.38AT-europe-ireland-nace"
CRO_DATASTORE_SEARCH_URL = "https://opendata.cro.ie/api/3/action/datastore_search"
COMPANY_RECORDS_RESOURCE_ID = "3fef41bc-b8f4-4b10-8434-ce51c29b1bba"
MIN_SECONDS_BETWEEN_CALLS = 0.5
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 30.0

# NACE Rev.2 4-digit code -> English description, verified against the
# INSPIRE registry / Eurostat-derived class descriptions. Only the real
# codes observed among these 8 real Irish companies are listed --
# extend only after checking a new code against an official source.
NACE_DESCRIPTIONS_EN: dict[str, str] = {
    "6420": "Activities of holding companies",
}


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def search_company(company_num: str) -> dict:
    query = urllib.parse.urlencode({"resource_id": COMPANY_RECORDS_RESOURCE_ID, "q": company_num, "limit": 5})
    request = urllib.request.Request(f"{CRO_DATASTORE_SEARCH_URL}?{query}", headers={"User-Agent": "ScoutFinanceResearch/1.0 (+non-commercial research script)"})
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            raise
    raise RuntimeError("rate_limit_retries_exhausted")


def match_by_company_num(company_num: str, payload: dict) -> dict | None:
    for record in payload.get("result", {}).get("records", []):
        if str(record.get("company_num")) == str(company_num):
            return record
    return None


def describe(nace_code: str) -> tuple[str, bool]:
    if not nace_code:
        return "", False
    description = NACE_DESCRIPTIONS_EN.get(nace_code)
    if description is None:
        return f"UNKNOWN_NACE_CODE_{nace_code}", True
    return description, False


def build_record(row: dict[str, str], status: str, reason: str, created_at: str, nace_code: str = "", princ_object_code: str = "") -> dict[str, Any]:
    description, unknown = describe(nace_code)
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["resolved_company_name"],
        "company_number": row.get("company_number", ""), "fetch_status": status, "fetch_reason": reason,
        "nace_code": nace_code, "nace_description_en": description,
        "princ_object_code_unverified_not_used": princ_object_code,
        "unknown_nace_code": nace_code if unknown else "", "phase": PHASE, "created_at_utc": created_at,
    }


FIELDS = ["asset_id", "ticker", "company_name", "company_number", "fetch_status", "fetch_reason", "nace_code", "nace_description_en", "princ_object_code_unverified_not_used", "unknown_nace_code", "phase", "created_at_utc"]


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_nace_codes_fetched": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def build(input_matrix: Path, output_dir: Path, execute: bool) -> dict[str, Any]:
    rows = [r for r in read_csv(input_matrix) if r.get("lookup_status") == "resolved" and r.get("company_number")]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if not execute:
        return {"phase": PHASE, "status": "DRY_RUN", "eligible_companies": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}

    records: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        try:
            payload = search_company(row["company_number"])
        except urllib.error.HTTPError as exc:
            records.append(build_record(row, "error", f"http_error_{exc.code}", created_at))
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            records.append(build_record(row, "error", type(exc).__name__, created_at))
            continue
        match = match_by_company_num(row["company_number"], payload)
        if match is None:
            records.append(build_record(row, "no_company_number_match", "company_number_not_found_in_results", created_at))
            continue
        nace_code = str(match.get("nace_v2_code") or "")
        princ_object = str(match.get("princ_object_code") or "")
        if not nace_code:
            records.append(build_record(row, "no_nace_on_record", "nace_v2_code_absent", created_at, princ_object_code=princ_object))
            continue
        records.append(build_record(row, "resolved", "nace_v2_code_present", created_at, nace_code=nace_code, princ_object_code=princ_object))

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_ireland_nace_v2_38at.csv", records, FIELDS)
    resolved = sum(1 for r in records if r["fetch_status"] == "resolved")
    unknown_codes = sorted({r["unknown_nace_code"] for r in records if r["unknown_nace_code"]})
    report = {
        "phase": PHASE, "status": "COMPLETED_EUROPE_IRELAND_NACE",
        "eligible_companies": len(rows), "companies_fetched": len(records), "companies_with_nace": resolved,
        "companies_no_nace_on_record": sum(1 for r in records if r["fetch_status"] == "no_nace_on_record"),
        "companies_no_match": sum(1 for r in records if r["fetch_status"] == "no_company_number_match"),
        "companies_error": sum(1 for r in records if r["fetch_status"] == "error"),
        "unknown_nace_codes_needing_verification": unknown_codes,
        "network_used": True, "credentials_used": False, "raw_cache_published": False,
        "scoring_created": False, "ranking_created": False, "recommendations_created": False, "phase9c_authorized": False,
        "note": "Reuses the already-approved free CRO open-data endpoint from v2.38Z -- no new policy decision needed. princ_object_code is captured for traceability only, never used as sector-matching text: confirmed live that Alkermes plc (a real, well-known pharmaceutical company) shows princ_object_code '24.41' (manufacture of basic precious and non-ferrous metals), which cannot be its real activity -- likely boilerplate objects-clause text from the memorandum of association of a newly-incorporated Irish holding entity, not a reliable classification. Same real, confirmed limitation as every other country attacked so far: companies with a real nace_v2_code (Smurfit Westrock, TE Connectivity, Linde) all show 6420 'Activities of holding companies' -- the Irish-registered entity is the group's holding vehicle, not its real global operating business.",
    }
    write_text(output_dir / "europe_ireland_nace_report_v2_38at.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help="perform the real CRO open-data lookups (no credential needed, but network calls are still gated behind this explicit flag)")
    args = parser.parse_args()

    if not args.execute:
        report = build(args.input_matrix, args.output_dir, False)
        print(json.dumps(report, sort_keys=True))
        return 0
    if not args.input_matrix.exists():
        return blocked("input_matrix_not_found")

    report = build(args.input_matrix, args.output_dir, True)
    print(json.dumps({k: report[k] for k in ("status", "eligible_companies", "companies_with_nace", "companies_error")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
