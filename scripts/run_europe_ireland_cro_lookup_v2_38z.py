#!/usr/bin/env python3
"""Block 9Z, part 2: look up the Irish Companies Registration Office (CRO)
profile (company number, status, type, registration date) for the 17
Ireland companies real-identified in part 1
(resolve_europe_ireland_identity_xetra_source_v2_38z.py).

Desk research confirmed before writing this script (see
outputs/full_universe_source_acquisition/v2_38z_europe_ireland_identity_resolution/EUROPE_IRELAND_IDENTITY_AND_REGISTRY_v2_38z.md
for the full writeup): the CRO's official Open Data Portal
(opendata.cro.ie) publishes a "Company Records" dataset -- 823,780 rows,
CC BY 4.0, updated daily -- via the standard CKAN Datastore API. This is
free, official, and requires **no account, no API key, no credential at
all** (simpler than UK Companies House, which at least needs a free
developer key). Queried via the plain (non-SQL) `datastore_search`
endpoint with a `q=` full-text parameter -- deliberately NOT the raw-SQL
`datastore_search_sql` endpoint, to avoid ever building a SQL string from
company-name text.

Fail-closed name matching: same normalize()/match logic already proven in
run_europe_companies_house_lookup_v2_38y.py (periods deleted, not turned
into spaces, so a dotted legal suffix like "P.L.C." still reduces to
"PLC"), with Irish company-type suffixes added ("PUBLIC LIMITED COMPANY",
"UNLIMITED COMPANY", "PLC", "ULC", "LIMITED", "LTD"). A Xetra-abbreviated
display name that doesn't exactly match the real registered name (e.g.
"RYANAIR HLDGS PLC" vs the real "RYANAIR HOLDINGS PUBLIC LIMITED COMPANY")
correctly stays unresolved rather than guessed -- same discipline that
caught the GB SCT/BMT collision.

Real financial figures are explicitly OUT OF SCOPE for this block: desk
research confirmed the CRO's "Financial Statements" open dataset is
100% PDF filings (230,410/230,410 rows checked in the 2024 resource,
including the exact filing for Ryanair Holdings, company number 249885)
-- no iXBRL, no structured figures, ever. This mirrors the "no OCR" wall
already hit for GB's large PLCs (Rio Tinto, Rentokil, SSE) in v2.38W/Y,
except here it is confirmed for the entire Irish register, not just this
project's 17 assets. No accounts-fetch or iXBRL-normalize script is built
for Ireland as a result.

Blocked by default; --execute is required (no credential needed, but the
project convention of a conscious, explicit real-network flag applies
regardless of whether a credential is involved).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38z_europe_ireland_identity_resolution/europe_ireland_identity_resolution_xetra_source_matrix_v2_38z.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38z_europe_ireland_identity_resolution"
PHASE = "v2.38Z-europe-ireland-cro-lookup"
CRO_DATASTORE_SEARCH_URL = "https://opendata.cro.ie/api/3/action/datastore_search"
COMPANY_RECORDS_RESOURCE_ID = "3fef41bc-b8f4-4b10-8434-ce51c29b1bba"
MIN_SECONDS_BETWEEN_CALLS = 0.5
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 30.0

LEGAL_SUFFIXES = ["PUBLIC LIMITED COMPANY", "UNLIMITED COMPANY", "PLC", "ULC", "LIMITED", "LTD"]

MATRIX_FIELDS = [
    "asset_id", "ticker", "resolved_company_name", "isin", "lookup_status", "lookup_reason", "company_number",
    "company_status", "company_type", "company_reg_date", "real_filings_downloaded", "real_fundamentals_present",
    "phase", "created_at_utc",
]


def normalize(name: str) -> str:
    text = name.upper()
    # Same fix as the GB lookup: periods are deleted outright, never
    # turned into a space, so a dotted legal suffix ("P.L.C.") still
    # reduces to the plain "PLC" token instead of splitting into letters.
    text = text.replace(".", "")
    text = re.sub(r"[,()\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split(" ")
    changed = True
    while changed and words:
        changed = False
        for suffix in LEGAL_SUFFIXES:
            suffix_words = suffix.split(" ")
            if words[-len(suffix_words):] == suffix_words:
                words = words[: -len(suffix_words)]
                changed = True
                break
    return " ".join(words).strip()


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def search_company(name: str) -> dict:
    query = urllib.parse.urlencode({"resource_id": COMPANY_RECORDS_RESOURCE_ID, "q": name, "limit": 20})
    request = urllib.request.Request(f"{CRO_DATASTORE_SEARCH_URL}?{query}")
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


def match_company(resolved_name: str, payload: dict) -> tuple[dict | None, str]:
    items = payload.get("result", {}).get("records", [])
    expected = normalize(resolved_name)
    candidates = [item for item in items if normalize(item.get("company_name", "")) == expected]
    active = [c for c in candidates if (c.get("company_status") or "").strip().lower() == "normal"]
    if not candidates:
        return None, "no_exact_normalized_name_match"
    if len(active) == 1:
        return active[0], "exact_normalized_name_match_single_active_company"
    if len(candidates) == 1:
        return candidates[0], "exact_normalized_name_match_single_company_not_marked_active"
    return None, "ambiguous_multiple_companies_match_name"


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_filings_downloaded": False, "real_fundamentals_present": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help="perform the real CRO lookups (no credential needed, but network calls are still gated behind this explicit flag)")
    args = parser.parse_args()

    if not args.execute:
        rows = [r for r in read_csv(args.input_matrix) if r["resolution_status"] == "resolved"] if args.input_matrix.exists() else []
        print(json.dumps({"status": "DRY_RUN", "eligible_assets": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}, sort_keys=True))
        return 0

    rows = [r for r in read_csv(args.input_matrix) if r["resolution_status"] == "resolved"]
    if not rows:
        return blocked("no_resolved_companies_in_input_matrix")

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    matrix = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        name = row["resolved_company_name"]
        try:
            payload = search_company(name)
        except urllib.error.HTTPError as exc:
            matrix.append(_lookup_record(row, "error", f"http_error_{exc.code}", created_at))
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            matrix.append(_lookup_record(row, "error", type(exc).__name__, created_at))
            continue

        match, reason = match_company(name, payload)
        if match is None:
            matrix.append(_lookup_record(row, "unresolved", reason, created_at))
            continue
        matrix.append(_lookup_record(
            row, "resolved", reason, created_at,
            company_number=str(match.get("company_num", "")), company_status=(match.get("company_status") or "").strip(),
            company_type=match.get("company_type", ""), company_reg_date=(match.get("company_reg_date") or "")[:10],
        ))

    resolved_count = sum(1 for r in matrix if r["lookup_status"] == "resolved")
    report = {
        "phase": PHASE, "input_resolved_assets": len(rows), "profiles_confirmed": resolved_count,
        "unresolved_or_error": len(matrix) - resolved_count, "real_filings_downloaded": False,
        "real_fundamentals_present": False, "credentials_used": False, "phase9c_authorized": False,
        "raw_cache_published": False,
        "note": "Profile confirmation only. Real accounts/iXBRL extraction is explicitly out of scope: the CRO's Financial Statements open dataset is confirmed 100% PDF filings (no structured or iXBRL data exists for any Irish company, verified project-wide and specifically for Ryanair Holdings).",
    }

    write_csv(args.output_dir / "europe_ireland_cro_lookup_matrix_v2_38z.csv", matrix, MATRIX_FIELDS)
    write_text(args.output_dir / "europe_ireland_cro_lookup_summary_v2_38z.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


def _lookup_record(row: dict[str, str], status: str, reason: str, created_at: str, company_number: str = "", company_status: str = "", company_type: str = "", company_reg_date: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "resolved_company_name": row["resolved_company_name"],
        "isin": row.get("isin", ""), "lookup_status": status, "lookup_reason": reason, "company_number": company_number,
        "company_status": company_status, "company_type": company_type, "company_reg_date": company_reg_date,
        "real_filings_downloaded": "false", "real_fundamentals_present": "false", "phase": PHASE, "created_at_utc": created_at,
    }


if __name__ == "__main__":
    raise SystemExit(main())
