#!/usr/bin/env python3
"""Block 9AE: look up the Dutch official company registry profile (KVK
number, legal name, status) for the 44 Netherlands assets real-identified
in v2.38AB, then check whether their real annual accounts are available
via KVK's free structured-financials open dataset.

Desk research confirmed before writing this script (see
outputs/full_universe_source_acquisition/v2_38ae_europe_netherlands_registry_lookup/EUROPE_NETHERLANDS_REGISTRY_v2_38ae.md
for the full writeup):
- The official KVK "Zoeken" (search) API is paid (EUR 6.40/month + per-
  query fees) -- ruled out by this project's no-paid-data policy.
- OpenKvK.nl, the one plausible free alternative, is blocked by a real
  Cloudflare bot challenge (confirmed live via a plain curl request, not
  a tool artifact) -- a stop sign, not pursued further.
- KVK's own "HR Open Data Set" is free but explicitly ANONYMIZED: company
  names and KVK numbers are both stripped for privacy, making it useless
  for looking up a specific company.
- The breakthrough: GLEIF (Global Legal Entity Identifier Foundation), a
  free, CC0-licensed, no-key, no-account, real-time public API, resolves
  a security's ISIN directly to its Legal Entity Identifier record --
  which includes the entity's national registration authority and
  registration number. For a Dutch company this IS the KVK number,
  confirmed live for ASML Holding N.V. (ISIN NL0010273215 -> KVK
  17085815) and Heineken N.V. (ISIN NL0000009165 -> KVK 33011433). Since
  we already have a real, unique ISIN for every asset from v2.38AB, this
  sidesteps the whole "search by abbreviated Xetra name" ambiguity
  problem this project has hit in every other country (GB/Ireland/
  France) -- ISIN is a perfect key, no fuzzy matching needed at all.
- KVK's "Jaarrekeningen Open Dataset" (opendata.kvk.nl) then provides
  genuinely structured, extracted XBRL financial facts for free, keyed by
  KVK number -- but confirmed live, twice (ASML and Heineken), to return
  "IPD0001: Het gevraagde product voor Jaarrekeningen bestaat niet" (the
  requested product does not exist). This dataset only covers the
  simplified SBR/XBRL filings required of micro/small/medium entities
  since 2016/2017 -- large IFRS-reporting multinationals like our 44
  targets file through a different regime this open dataset does not
  cover, the same "large caps only have PDF/aren't in the simplified
  digital system" wall already hit for GB's Rio Tinto/Rentokil/SSE.

Given that documented, real negative pattern (confirmed for 2/2 tested),
this script checks the Jaarrekeningen dataset for only a representative
sample (default 8, --jaarrekeningen-sample controls it) rather than
exhaustively querying all resolved KVK numbers -- the API's own
documented rate limit (max 1 request/minute per IP) would make an
exhaustive run take the better part of an hour for a result whose
pattern is already well-evidenced, a poor use of that budget.

Blocked by default; --execute is required (no credential needed for
either API, but the project convention of a conscious, explicit
real-network flag applies regardless of whether a credential is
involved).
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
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38ab_europe_full_identity_resolution/europe_full_identity_resolution_xetra_source_matrix_v2_38ab.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ae_europe_netherlands_registry_lookup"
PHASE = "v2.38AE-europe-netherlands-registry-lookup"
JURISDICTION_FILTER = "NL"
GLEIF_URL = "https://api.gleif.org/api/v1/lei-records"
KVK_JAARREKENINGEN_URL = "https://opendata.kvk.nl/api/v1/hvds/jaarrekeningen"
KVK_REGISTRATION_AUTHORITY_ID = "RA000463"
GLEIF_MIN_SECONDS_BETWEEN_CALLS = 0.3
JAARREKENINGEN_MIN_SECONDS_BETWEEN_CALLS = 61.0  # documented real limit: max 1 request/minute per IP
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 65.0
DEFAULT_JAARREKENINGEN_SAMPLE = 8

REGISTRY_MATRIX_FIELDS = [
    "asset_id", "ticker", "resolved_company_name", "isin", "gleif_lookup_status", "gleif_lookup_reason",
    "lei", "legal_name", "registration_authority_id", "kvk_number", "entity_status", "phase", "created_at_utc",
]
JAARREKENINGEN_FIELDS = [
    "asset_id", "ticker", "kvk_number", "jaarrekeningen_status", "jaarrekeningen_reason", "phase", "created_at_utc",
]


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


def http_get_json(url: str) -> tuple[int, dict | None]:
    request = urllib.request.Request(url)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            body = exc.read().decode("utf-8") if exc.fp else "{}"
            try:
                return exc.code, json.loads(body)
            except json.JSONDecodeError:
                return exc.code, None
    raise RuntimeError("rate_limit_retries_exhausted")


def gleif_lookup(isin: str) -> tuple[dict | None, str]:
    query = urllib.parse.urlencode({"filter[isin]": isin})
    status, payload = http_get_json(f"{GLEIF_URL}?{query}")
    if status != 200 or payload is None:
        return None, f"gleif_http_error_{status}"
    records = payload.get("data", [])
    if not records:
        return None, "no_lei_record_for_isin"
    if len(records) > 1:
        return None, "ambiguous_multiple_lei_records_for_isin"
    return records[0], "exact_isin_match_single_lei_record"


def jaarrekeningen_check(kvk_number: str) -> tuple[str, str]:
    status, payload = http_get_json(f"{KVK_JAARREKENINGEN_URL}/{kvk_number}")
    if status == 200 and payload is not None:
        return "available", "structured_annual_accounts_found"
    if status == 404:
        return "not_available", "no_jaarrekening_in_open_dataset_likely_large_ifrs_filer_not_sbr"
    return "error", f"http_error_{status}"


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_filings_downloaded": False, "real_fundamentals_present": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--jaarrekeningen-sample", type=int, default=DEFAULT_JAARREKENINGEN_SAMPLE, help="how many resolved KVK numbers to check against the rate-limited (1/min) Jaarrekeningen Open Dataset -- representative sample, not exhaustive")
    parser.add_argument("--execute", action="store_true", help="perform the real GLEIF + KVK lookups (no credential needed, but network calls are still gated behind this explicit flag)")
    args = parser.parse_args()

    if not args.execute:
        rows = [r for r in read_csv(args.input_matrix) if r["resolution_status"] == "resolved" and r.get("home_country") == JURISDICTION_FILTER] if args.input_matrix.exists() else []
        print(json.dumps({"status": "DRY_RUN", "eligible_assets": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}, sort_keys=True))
        return 0

    rows = [r for r in read_csv(args.input_matrix) if r["resolution_status"] == "resolved" and r.get("home_country") == JURISDICTION_FILTER]
    if not rows:
        return blocked("no_resolved_companies_in_input_matrix")

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    registry_matrix = []
    kvk_numbers_resolved: list[tuple[str, str, str]] = []  # (asset_id, ticker, kvk_number)
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(GLEIF_MIN_SECONDS_BETWEEN_CALLS)
        record, reason = gleif_lookup(row["isin"])
        if record is None:
            registry_matrix.append(_registry_record(row, "unresolved", reason, created_at))
            continue
        entity = record.get("attributes", {}).get("entity", {})
        registered_at = (entity.get("registeredAt") or {}).get("id", "")
        registered_as = entity.get("registeredAs", "")
        legal_name = (entity.get("legalName") or {}).get("name", "")
        status = entity.get("status", "")
        kvk_number = registered_as if registered_at == KVK_REGISTRATION_AUTHORITY_ID else ""
        registry_matrix.append(_registry_record(
            row, "resolved", reason, created_at, lei=record.get("id", ""), legal_name=legal_name,
            registration_authority_id=registered_at, kvk_number=kvk_number, entity_status=status,
        ))
        if kvk_number:
            kvk_numbers_resolved.append((row["asset_id"], row["ticker"], kvk_number))

    jaarrekeningen_rows = []
    sample = kvk_numbers_resolved[: max(0, args.jaarrekeningen_sample)]
    for i, (asset_id, ticker, kvk_number) in enumerate(sample):
        if i > 0:
            time.sleep(JAARREKENINGEN_MIN_SECONDS_BETWEEN_CALLS)
        jstatus, jreason = jaarrekeningen_check(kvk_number)
        jaarrekeningen_rows.append({
            "asset_id": asset_id, "ticker": ticker, "kvk_number": kvk_number,
            "jaarrekeningen_status": jstatus, "jaarrekeningen_reason": jreason, "phase": PHASE, "created_at_utc": created_at,
        })

    resolved_count = sum(1 for r in registry_matrix if r["gleif_lookup_status"] == "resolved")
    kvk_confirmed = sum(1 for r in registry_matrix if r["kvk_number"])
    report = {
        "phase": PHASE, "input_resolved_assets": len(rows), "gleif_profiles_confirmed": resolved_count,
        "gleif_unresolved_or_error": len(registry_matrix) - resolved_count, "kvk_numbers_confirmed": kvk_confirmed,
        "jaarrekeningen_sample_checked": len(jaarrekeningen_rows),
        "jaarrekeningen_available_in_sample": sum(1 for r in jaarrekeningen_rows if r["jaarrekeningen_status"] == "available"),
        "real_filings_downloaded": False, "real_fundamentals_present": False, "credentials_used": False,
        "phase9c_authorized": False, "raw_cache_published": False,
        "note": "GLEIF gives real identity + national registration number for free via ISIN (no name-matching ambiguity). KVK's Jaarrekeningen Open Dataset is checked only for a representative sample due to its documented 1-request/minute rate limit -- the pattern (large IFRS filers absent from this SME-oriented dataset) is already well evidenced by the sample.",
    }

    write_csv(args.output_dir / "europe_netherlands_gleif_registry_matrix_v2_38ae.csv", registry_matrix, REGISTRY_MATRIX_FIELDS)
    write_csv(args.output_dir / "europe_netherlands_jaarrekeningen_sample_v2_38ae.csv", jaarrekeningen_rows, JAARREKENINGEN_FIELDS)
    write_text(args.output_dir / "europe_netherlands_registry_lookup_summary_v2_38ae.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


def _registry_record(row: dict[str, str], status: str, reason: str, created_at: str, lei: str = "", legal_name: str = "", registration_authority_id: str = "", kvk_number: str = "", entity_status: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "resolved_company_name": row["resolved_company_name"],
        "isin": row.get("isin", ""), "gleif_lookup_status": status, "gleif_lookup_reason": reason, "lei": lei,
        "legal_name": legal_name, "registration_authority_id": registration_authority_id, "kvk_number": kvk_number,
        "entity_status": entity_status, "phase": PHASE, "created_at_utc": created_at,
    }


if __name__ == "__main__":
    raise SystemExit(main())
