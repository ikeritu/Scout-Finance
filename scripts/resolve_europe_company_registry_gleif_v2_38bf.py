#!/usr/bin/env python3
"""Block 9BF: generalize the Luxembourg name-based GLEIF resolver
(v2.38AW) plus the two extra real fixes found while scaling Cboe Europe
(v2.38BB) -- raw-word queries that preserve original punctuation, a
two-word fallback for over-generic first words -- into a country-
parameterized resolver, reused now for the new Austria (40) and Finland
(133) companies v2.38BC found under country=AT/FI.

Unlike Luxembourg, these Cboe rows have no ISIN (confirmed structurally
absent from this source since v2.38BC), so the ISIN-based GLEIF method
already used for the original Austria/Finland populations (v2.38AF)
cannot apply here -- this reuses the country-scoped name search instead,
identical in spirit to v2.38AW, generalized the same way v2.38AR
generalized the Wikidata fetcher after a second real case.

Imports v2.38BB's normalize_key/raw_words/find_exact_candidates
unmodified (the exact matching engine already refined across 4 real bug
fixes) -- this script only adds the country-scoped query variant, since
v2.38BB deliberately searches with no country filter (the country was
what it was trying to discover) while here the country is already known
from v2.38BC's own GLEIF-derived country field.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BB_SCRIPT = ROOT / "scripts/resolve_europe_cboe_secondary_identity_pilot_v2_38bb.py"
BC_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38bc_europe_cboe_secondary_identity_full/europe_cboe_secondary_identity_full_matrix_v2_38bc.csv"
PHASE = "v2.38BF-europe-company-registry-gleif"
GLEIF_URL = "https://api.gleif.org/api/v1/lei-records"
GLEIF_MIN_SECONDS_BETWEEN_CALLS = 0.3

MATRIX_FIELDS = ["asset_id", "ticker", "company_name", "country", "search_key", "gleif_lookup_status", "gleif_lookup_reason", "lei", "gleif_legal_name", "national_registration_number", "entity_status", "query_strategy", "phase", "created_at_utc"]


def load_bb_module():
    spec = importlib.util.spec_from_file_location("resolve_europe_cboe_secondary_identity_pilot_v2_38bb", BB_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def select_candidates(bc_matrix: Path, country: str, already_known_names: set[str], exclude_name_re) -> list[dict[str, str]]:
    candidates = []
    with bc_matrix.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") != "resolved" or row.get("country") != country:
                continue
            name = row.get("legal_name", "")
            if not name or name.strip().upper() in already_known_names:
                continue
            if exclude_name_re and exclude_name_re.search(name):
                continue
            candidates.append(row)
    return candidates


def gleif_query_country(bb_mod, query_string: str, country: str) -> tuple[list[dict], str]:
    query = urllib.parse.urlencode({"filter[entity.legalName]": query_string, "filter[entity.legalAddress.country]": country, "page[size]": "50"})
    status, payload = bb_mod.http_get_json(f"{GLEIF_URL}?{query}")
    if status != 200 or payload is None:
        return [], f"gleif_http_error_{status}"
    return payload.get("data", []), "queried"


def gleif_lookup_country_scoped(bb_mod, original_name: str, key: str, country: str) -> tuple[list[dict], str, str]:
    first = bb_mod.raw_words(original_name, 1)
    records, reason = gleif_query_country(bb_mod, first, country)
    if reason != "queried":
        return [], reason, "first_word"
    if bb_mod.find_exact_candidates(key, records):
        return records, "queried", "first_word"
    two = bb_mod.raw_words(original_name, 2)
    if two and two != first:
        more_records, reason2 = gleif_query_country(bb_mod, two, country)
        if reason2 == "queried" and bb_mod.find_exact_candidates(key, more_records):
            return more_records, "queried", "first_two_words"
    return records, "queried", "first_word"


def build(bc_matrix: Path, country: str, already_known_names: set[str], output_dir: Path, execute: bool, exclude_name_re=None) -> dict[str, Any]:
    bb_mod = load_bb_module()
    candidates = select_candidates(bc_matrix, country, already_known_names, exclude_name_re)

    if not execute:
        return {"phase": PHASE, "status": "DRY_RUN", "country": country, "new_candidates": len(candidates), "network_used": False, "phase9c_authorized": False}

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    matrix = []
    for i, row in enumerate(candidates):
        if i > 0:
            time.sleep(GLEIF_MIN_SECONDS_BETWEEN_CALLS)
        key = bb_mod.normalize_key(row["legal_name"])
        records, reason, query_strategy = gleif_lookup_country_scoped(bb_mod, row["legal_name"], key, country)
        if reason != "queried":
            matrix.append(_record(row, key, country, "unresolved", reason, created_at))
            continue
        exact = bb_mod.find_exact_candidates(key, records)
        if not exact:
            matrix.append(_record(row, key, country, "unresolved", "no_exact_normalized_name_match_gleif", created_at))
            continue
        if len(exact) > 1:
            matrix.append(_record(row, key, country, "ambiguous", "multiple_distinct_entities_match_normalized_name", created_at))
            continue
        entity = exact[0].get("attributes", {}).get("entity", {})
        matrix.append(_record(
            row, key, country, "resolved", "exact_single_gleif_match_country_scoped", created_at,
            lei=exact[0].get("id", ""), legal_name=(entity.get("legalName") or {}).get("name", ""),
            national_registration_number=entity.get("registeredAs", ""), entity_status=entity.get("status", ""),
            query_strategy=query_strategy,
        ))

    resolved = [r for r in matrix if r["gleif_lookup_status"] == "resolved"]
    report = {
        "phase": PHASE, "country": country, "new_candidates": len(candidates), "resolved": len(resolved),
        "ambiguous": sum(1 for r in matrix if r["gleif_lookup_status"] == "ambiguous"),
        "unresolved": sum(1 for r in matrix if r["gleif_lookup_status"] == "unresolved"),
        "network_used": True, "credentials_used": False, "phase9c_authorized": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = output_dir / f"europe_company_registry_gleif_matrix_v2_38bf_{country.lower()}.csv.tmp"
    final = output_dir / f"europe_company_registry_gleif_matrix_v2_38bf_{country.lower()}.csv"
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MATRIX_FIELDS, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(matrix)
    tmp.replace(final)
    return report


def _record(row: dict[str, str], key: str, country: str, status: str, reason: str, created_at: str, lei: str = "", legal_name: str = "", national_registration_number: str = "", entity_status: str = "", query_strategy: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["legal_name"], "country": country,
        "search_key": key, "gleif_lookup_status": status, "gleif_lookup_reason": reason, "lei": lei,
        "gleif_legal_name": legal_name, "national_registration_number": national_registration_number,
        "entity_status": entity_status, "query_strategy": query_strategy, "phase": PHASE, "created_at_utc": created_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bc-matrix", type=Path, default=BC_MATRIX)
    parser.add_argument("--country", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    report = build(args.bc_matrix, args.country, set(), args.output_dir, args.execute)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
