#!/usr/bin/env python3
"""Block 9Y, part 1: look up the UK Companies House profile (company
number, status, incorporation date, SIC codes) for all 40 GB companies
now correctly identified in the post-v2.38V-correction Xetra-source
resolution (resolve_europe_gb_identity_xetra_source_v2_38v.py).

This is the same logic as run_europe_companies_house_lookup_v2_38v.py
(v2.38V, part 2) -- fail-closed exact-normalized-name matching, HTTP
Basic auth with the API key as username and an empty password, never
logging the credential -- run again at full scale (40 companies instead
of the 4 partially-wrong identities v2.38V had before the correction).
It is a separate script, not an in-place rerun of v2.38V's, so that
v2.38V's original (now-corrected-by-v2.38V's-own-follow-up) output stays
untouched as a historical record.

Blocked by default. --execute plus SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY
are both required.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_gb_full_expansion_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38y_europe_gb_full_expansion"
PHASE = "v2.38Y-europe-gb-companies-house-lookup-full-expansion"
CREDENTIAL_ENV = "SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY"
SEARCH_URL = "https://api.company-information.service.gov.uk/search/companies"
MIN_SECONDS_BETWEEN_CALLS = 0.6  # fair-use guidance: 600 requests / 5 minutes
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 65.0

LEGAL_SUFFIXES = ["PUBLIC LIMITED COMPANY", "PLC", "LIMITED", "LTD"]

MATRIX_FIELDS = [
    "asset_id", "ticker", "resolved_company_name", "isin", "lookup_status", "lookup_reason", "company_number",
    "company_status", "date_of_creation", "sic_codes", "real_filings_downloaded", "real_fundamentals_present",
    "normalized_fundamentals_present", "credential_used_value_never_logged", "phase", "created_at_utc",
]


def normalize(name: str) -> str:
    text = name.upper()
    # Periods are deleted outright (not turned into a space) because
    # Companies House sometimes registers the legal suffix as dotted
    # single letters -- e.g. real title "BP P.L.C." -- and a period-to-
    # space substitution would split that into three separate one-letter
    # words ("P", "L", "C") that never match the plain "PLC" suffix token,
    # a real mismatch confirmed live while running v2.38Y at full scale.
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


def search_company(name: str, api_key: str) -> dict:
    query = urllib.parse.urlencode({"q": name, "items_per_page": 5})
    auth = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(f"{SEARCH_URL}?{query}", headers={"Authorization": f"Basic {auth}"})
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
    items = payload.get("items", [])
    expected = normalize(resolved_name)
    candidates = [item for item in items if normalize(item.get("title", "")) == expected]
    active = [c for c in candidates if c.get("company_status") == "active"]
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
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=ROOT / contract["input_identity_matrix"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help=f"perform the real Companies House lookups (requires {CREDENTIAL_ENV})")
    args = parser.parse_args()

    if not args.execute:
        rows = [r for r in read_csv(args.input_matrix) if r["resolution_status"] == "resolved"] if args.input_matrix.exists() else []
        print(json.dumps({"status": "DRY_RUN", "eligible_assets": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}, sort_keys=True))
        return 0

    api_key = os.environ.get(CREDENTIAL_ENV, "").strip()
    if not api_key:
        return blocked("credential_missing")

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
            payload = search_company(name, api_key)
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
            company_number=match.get("company_number", ""), company_status=match.get("company_status", ""),
            date_of_creation=match.get("date_of_creation", ""), sic_codes=";".join(match.get("sic_codes") or []),
        ))

    resolved_count = sum(1 for r in matrix if r["lookup_status"] == "resolved")
    report = {
        "phase": PHASE, "input_resolved_assets": len(rows), "profiles_confirmed": resolved_count,
        "unresolved_or_error": len(matrix) - resolved_count, "real_filings_downloaded": False,
        "real_fundamentals_present": False, "normalized_fundamentals_created": False, "credentials_used": True,
        "phase9c_authorized": False, "raw_cache_published": False,
        "note": "Profile confirmation only (company_number/status/incorporation date/SIC). Accounts document download and iXBRL parsing happen in a following step of this same block.",
    }

    write_csv(args.output_dir / "europe_companies_house_lookup_matrix_v2_38y.csv", matrix, MATRIX_FIELDS)
    write_text(args.output_dir / "europe_companies_house_lookup_summary_v2_38y.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


def _lookup_record(row: dict[str, str], status: str, reason: str, created_at: str, company_number: str = "", company_status: str = "", date_of_creation: str = "", sic_codes: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "resolved_company_name": row["resolved_company_name"],
        "isin": row.get("isin", ""), "lookup_status": status, "lookup_reason": reason, "company_number": company_number,
        "company_status": company_status, "date_of_creation": date_of_creation, "sic_codes": sic_codes,
        "real_filings_downloaded": "false", "real_fundamentals_present": "false", "normalized_fundamentals_present": "false",
        "credential_used_value_never_logged": "true", "phase": PHASE, "created_at_utc": created_at,
    }


if __name__ == "__main__":
    raise SystemExit(main())
