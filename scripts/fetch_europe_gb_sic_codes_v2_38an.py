#!/usr/bin/env python3
"""Block 9AN: fetch real UK SIC 2007 codes for the GB companies already
confirmed by v2.38Y's Companies House lookup, attacking the 0/689 real
sector-theme-match finding from v2.38AM head-on for the GB subset.

Real bug found and fixed here, not worked around: v2.38Y's lookup matrix
already has a `sic_codes` column, but it was always empty -- because
v2.38Y's `search_company()` calls the Companies House SEARCH endpoint
(`/search/companies`), whose result items never carry a `sic_codes` field
at all (confirmed live: `match.get("sic_codes")` was always None). SIC
codes only exist on the full company PROFILE endpoint
(`/company/{company_number}`), confirmed live for Diageo plc (company
number 00023307): a real call returns `sic_codes: ["70100"]`. This script
calls that correct endpoint for each of v2.38Y's 29 resolved companies,
using the same credential and rate-limit discipline as v2.38Y.

Blocked by default. --execute plus SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY
are both required, exactly like v2.38Y.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38y_europe_gb_full_expansion/europe_companies_house_lookup_matrix_v2_38y.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38an_europe_gb_sic_codes"
PHASE = "v2.38AN-europe-gb-sic-codes"
CREDENTIAL_ENV = "SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY"
PROFILE_URL = "https://api.company-information.service.gov.uk/company/{company_number}"
MIN_SECONDS_BETWEEN_CALLS = 0.6  # same fair-use pacing as v2.38Y: 600 requests / 5 minutes
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 65.0

# UK SIC 2007 is the official government industry classification. Every
# entry here was checked against the official Companies House condensed
# SIC 2007 list (resources.companieshouse.gov.uk/sic/) -- these are
# exactly, and only, the 23 real codes that came back from this project's
# 29 real GB companies (fetched 2026-09-06). Deliberately not a guessed
# full ~730-entry table: a code this project has not verified stays
# honestly UNKNOWN_SIC_CODE rather than risking a wrong label. Add a new
# entry here only after checking it against that same official source.
UK_SIC_2007_DESCRIPTIONS: dict[str, str] = {
    "70100": "Activities of head offices",
    "25400": "Manufacture of weapons and ammunition",
    "29100": "Manufacture of motor vehicles",
    "30110": "Building of ships and floating structures",
    "30300": "Manufacture of air and spacecraft and related machinery",
    "58190": "Other publishing activities",
    "64191": "Banks",
    "27900": "Manufacture of other electrical equipment",
    "82990": "Other business support service activities n.e.c",
    "96090": "Other service activities n.e.c.",
    "66110": "Administration of financial markets",
    "58110": "Book publishing",
    "58142": "Publishing of consumer and business journals and periodicals",
    "58290": "Other software publishing",
    "09100": "Support activities for petroleum and natural gas mining",
    "25110": "Manufacture of metal structures and parts of structures",
    "71129": "Other engineering activities",
    "61900": "Other telecommunications activities",
    "47110": "Retail sale in non-specialised stores with food, beverages or tobacco predominating",
    "74909": "Other professional, scientific and technical activities n.e.c.",
    "64209": "Activities of other holding companies n.e.c.",
    "08990": "Other mining and quarrying n.e.c.",
    "72110": "Research and experimental development on biotechnology",
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


def fetch_profile(company_number: str, api_key: str) -> dict:
    auth = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(PROFILE_URL.format(company_number=company_number), headers={"Authorization": f"Basic {auth}"})
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


def describe_codes(codes: list[str]) -> tuple[str, list[str]]:
    descriptions = []
    unknown = []
    for code in codes:
        description = UK_SIC_2007_DESCRIPTIONS.get(code)
        if description is None:
            unknown.append(code)
            descriptions.append(f"UNKNOWN_SIC_CODE_{code}")
        else:
            descriptions.append(description)
    return ";".join(descriptions), unknown


def build_record(row: dict[str, str], status: str, reason: str, created_at: str, sic_codes: list[str] | None = None) -> dict[str, Any]:
    sic_codes = sic_codes or []
    descriptions, unknown = describe_codes(sic_codes)
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["resolved_company_name"],
        "company_number": row.get("company_number", ""), "fetch_status": status, "fetch_reason": reason,
        "sic_codes": ";".join(sic_codes), "sic_descriptions": descriptions,
        "unknown_sic_codes": ";".join(unknown), "phase": PHASE, "created_at_utc": created_at,
    }


FIELDS = ["asset_id", "ticker", "company_name", "company_number", "fetch_status", "fetch_reason", "sic_codes", "sic_descriptions", "unknown_sic_codes", "phase", "created_at_utc"]


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_sic_codes_fetched": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def build(input_matrix: Path, output_dir: Path, api_key: str, execute: bool) -> dict[str, Any]:
    rows = [r for r in read_csv(input_matrix) if r.get("lookup_status") == "resolved" and r.get("company_number")]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    records: list[dict[str, Any]] = []
    if not execute:
        report = {"phase": PHASE, "status": "DRY_RUN", "eligible_companies": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}
        return report

    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        try:
            profile = fetch_profile(row["company_number"], api_key)
        except urllib.error.HTTPError as exc:
            records.append(build_record(row, "error", f"http_error_{exc.code}", created_at))
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            records.append(build_record(row, "error", type(exc).__name__, created_at))
            continue
        codes = profile.get("sic_codes") or []
        records.append(build_record(row, "resolved" if codes else "no_sic_codes_on_profile", "profile_fetched", created_at, codes))

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_gb_sic_codes_v2_38an.csv", records, FIELDS)
    resolved = sum(1 for r in records if r["fetch_status"] == "resolved")
    all_unknown = sorted({code for r in records for code in r["unknown_sic_codes"].split(";") if code})
    report = {
        "phase": PHASE, "status": "COMPLETED_EUROPE_GB_SIC_CODES",
        "eligible_companies": len(rows), "companies_fetched": len(records), "companies_with_sic_codes": resolved,
        "companies_no_sic_codes": sum(1 for r in records if r["fetch_status"] == "no_sic_codes_on_profile"),
        "companies_error": sum(1 for r in records if r["fetch_status"] == "error"),
        "unknown_sic_codes_needing_description": all_unknown,
        "network_used": True, "credentials_used": True, "raw_cache_published": False,
        "scoring_created": False, "ranking_created": False, "recommendations_created": False, "phase9c_authorized": False,
    }
    write_text(output_dir / "europe_gb_sic_codes_report_v2_38an.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help=f"perform the real Companies House profile lookups (requires {CREDENTIAL_ENV})")
    args = parser.parse_args()

    if not args.execute:
        report = build(args.input_matrix, args.output_dir, "", False)
        print(json.dumps(report, sort_keys=True))
        return 0

    api_key = os.environ.get(CREDENTIAL_ENV, "").strip()
    if not api_key:
        return blocked("credential_missing")
    if not args.input_matrix.exists():
        return blocked("input_matrix_not_found")

    report = build(args.input_matrix, args.output_dir, api_key, True)
    print(json.dumps({k: report[k] for k in ("status", "eligible_companies", "companies_with_sic_codes", "companies_error")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
