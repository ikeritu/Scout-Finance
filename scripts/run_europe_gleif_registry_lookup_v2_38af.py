#!/usr/bin/env python3
"""Block 9AF: generalize the GLEIF-based, ISIN-keyed registry lookup
already proven on the Netherlands (v2.38AE: 36/44, no name-matching
ambiguity at all) to every remaining country in the 689-asset Europe
universe that has not yet had ANY registry work done -- Switzerland (29),
Italy (22), Denmark (21), Austria (20), Belgium (6), Finland (5), Sweden
(4); 107 assets total -- in a single run, instead of repeating a
bespoke, country-by-country script for each.

Why GLEIF generalizes cleanly where the earlier per-country name-search
approach did not: every prior country (GB, Ireland, France) needed its
own fail-closed NAME-matching logic against that country's own registry
search API (and hit real, country-specific ambiguity problems doing it:
abbreviated Xetra names, duplicate active companies). GLEIF sidesteps all
of that -- every asset here already has a real, unique ISIN from
v2.38AB, and GLEIF resolves ISIN -> LEI record -> national registration
authority + number directly, with no text matching at all. The same
script and matching logic already works identically across every
jurisdiction that has LEI-registered issuers (which is effectively all
regulated European securities), because GLEIF's API and data model are
themselves country-agnostic.

This block resolves registry identity (registration authority + national
number, legal name, status) only. It deliberately does NOT attempt to
check any per-country annual-accounts open dataset (unlike v2.38AE's
Netherlands-specific Jaarrekeningen sample) -- confirming whether each of
these 7 countries has a free, structured, accessible financial-statement
source is real desk research per country, left for future blocks, the
same disciplined pattern already used for every prior country in this
project.

Blocked by default; --execute is required (no credential needed for
GLEIF, but the project convention of a conscious, explicit real-network
flag applies regardless of whether a credential is involved).
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
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38af_europe_gleif_registry_lookup"
PHASE = "v2.38AF-europe-gleif-registry-lookup"
GLEIF_URL = "https://api.gleif.org/api/v1/lei-records"
GLEIF_MIN_SECONDS_BETWEEN_CALLS = 0.3
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 65.0
DEFAULT_COUNTRIES = ["CH", "IT", "DK", "AT", "BE", "FI", "SE"]

# GLEIF registration-authority codes confirmed directly against real
# live lookups in this project (for readability in the output only --
# never used to decide anything, purely descriptive). Left blank for any
# code not yet directly confirmed; the raw code is always preserved
# regardless, so nothing is ever lost to an incomplete label.
KNOWN_REGISTRATION_AUTHORITIES = {
    "RA000463": "KVK (Netherlands, confirmed v2.38AE)",
}

MATRIX_FIELDS = [
    "asset_id", "ticker", "resolved_company_name", "isin", "home_country", "gleif_lookup_status",
    "gleif_lookup_reason", "lei", "legal_name", "registration_authority_id", "registration_authority_name",
    "national_registration_number", "entity_status", "phase", "created_at_utc",
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


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "phase9c_authorized": False}, sort_keys=True))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--countries", nargs="+", default=DEFAULT_COUNTRIES, help="home_country codes to look up in this run (defaults to the 7 countries with no registry work done yet)")
    parser.add_argument("--execute", action="store_true", help="perform the real GLEIF lookups (no credential needed, but network calls are still gated behind this explicit flag)")
    args = parser.parse_args()
    countries = set(args.countries)

    if not args.execute:
        rows = [r for r in read_csv(args.input_matrix) if r["resolution_status"] == "resolved" and r.get("home_country") in countries] if args.input_matrix.exists() else []
        from collections import Counter
        print(json.dumps({"status": "DRY_RUN", "eligible_assets": len(rows), "by_country": dict(Counter(r["home_country"] for r in rows)), "network_used": False, "phase9c_authorized": False}, sort_keys=True))
        return 0

    rows = [r for r in read_csv(args.input_matrix) if r["resolution_status"] == "resolved" and r.get("home_country") in countries]
    if not rows:
        return blocked("no_resolved_companies_in_input_matrix_for_selected_countries")

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    matrix = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(GLEIF_MIN_SECONDS_BETWEEN_CALLS)
        record, reason = gleif_lookup(row["isin"])
        if record is None:
            matrix.append(_record(row, "unresolved", reason, created_at))
            continue
        entity = record.get("attributes", {}).get("entity", {})
        registered_at = (entity.get("registeredAt") or {}).get("id", "")
        registered_as = entity.get("registeredAs", "")
        legal_name = (entity.get("legalName") or {}).get("name", "")
        status = entity.get("status", "")
        matrix.append(_record(
            row, "resolved", reason, created_at, lei=record.get("id", ""), legal_name=legal_name,
            registration_authority_id=registered_at, national_registration_number=registered_as, entity_status=status,
        ))

    resolved_count = sum(1 for r in matrix if r["gleif_lookup_status"] == "resolved")
    from collections import Counter
    by_country_resolved = Counter(r["home_country"] for r in matrix if r["gleif_lookup_status"] == "resolved")
    by_country_total = Counter(r["home_country"] for r in matrix)
    by_registration_authority = Counter(r["registration_authority_id"] for r in matrix if r["registration_authority_id"])
    report = {
        "phase": PHASE, "countries_covered": sorted(countries), "input_resolved_assets": len(rows),
        "gleif_profiles_confirmed": resolved_count, "gleif_unresolved_or_error": len(matrix) - resolved_count,
        "resolved_by_country": {c: by_country_resolved.get(c, 0) for c in sorted(by_country_total)},
        "total_by_country": dict(sorted(by_country_total.items())),
        "by_registration_authority": dict(by_registration_authority),
        "credentials_used": False, "network_used": True, "phase9c_authorized": False,
        "note": "Registry identity confirmation only (registration authority + national number via GLEIF, ISIN-keyed, no name-matching ambiguity). Per-country financial-statement source research is deliberately out of scope for this block -- left for future, country-specific investigation the same way GB/Ireland/France/Netherlands were each investigated individually.",
    }

    write_csv(args.output_dir / "europe_gleif_registry_lookup_matrix_v2_38af.csv", matrix, MATRIX_FIELDS)
    write_text(args.output_dir / "europe_gleif_registry_lookup_summary_v2_38af.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


def _record(row: dict[str, str], status: str, reason: str, created_at: str, lei: str = "", legal_name: str = "", registration_authority_id: str = "", national_registration_number: str = "", entity_status: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "resolved_company_name": row["resolved_company_name"],
        "isin": row.get("isin", ""), "home_country": row.get("home_country", ""), "gleif_lookup_status": status,
        "gleif_lookup_reason": reason, "lei": lei, "legal_name": legal_name,
        "registration_authority_id": registration_authority_id,
        "registration_authority_name": KNOWN_REGISTRATION_AUTHORITIES.get(registration_authority_id, ""),
        "national_registration_number": national_registration_number, "entity_status": entity_status,
        "phase": PHASE, "created_at_utc": created_at,
    }


if __name__ == "__main__":
    raise SystemExit(main())
