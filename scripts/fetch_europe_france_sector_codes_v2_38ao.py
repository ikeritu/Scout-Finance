#!/usr/bin/env python3
"""Block 9AO: fetch the real NAF/APE activity code (and its NACE section
letter) for the 18 French companies already confirmed by v2.38AD's
registry lookup, continuing the attack on the 0/689 real sector-theme-
match finding from v2.38AM.

Same free, no-key French government API already used and validated in
v2.38AD (recherche-entreprises.api.gouv.fr) -- confirmed live that
searching by SIREN returns `activite_principale` (the NAF Rev.2 code,
e.g. "70.10Z") and `section_activite_principale` (the one-letter NACE
section, e.g. "M") for the exact matched company. v2.38AD never captured
either field because sector classification was out of scope for that
block; this is a separate, narrowly-scoped follow-up, not a rerun.

Every NAF code and NACE section label used here was checked against
INSEE's own metadata pages (insee.fr/fr/metadonnees/nafr2/...) on
2026-09-06 and translated to English so it feeds the same v2.38AM
keyword matcher already used for the US and GB; the French original is
kept in a separate column for anyone who wants to verify it independently.

Blocked by default; --execute is required (no credential needed, same
convention as v2.38AD: real network calls are still gated behind an
explicit flag regardless of whether a credential is involved).
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
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38ad_europe_france_registry_lookup/europe_france_registry_lookup_matrix_v2_38ad.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ao_europe_france_sector_codes"
PHASE = "v2.38AO-europe-france-sector-codes"
SEARCH_URL = "https://recherche-entreprises.api.gouv.fr/search"
MIN_SECONDS_BETWEEN_CALLS = 0.4
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 20.0

# Every code here was verified against INSEE's own metadata pages
# (insee.fr/fr/metadonnees/nafr2/sousClasse/<code>) on 2026-09-06 -- these
# are exactly, and only, the 9 real codes that came back from this
# project's 18 real French companies. A code not yet verified stays
# honestly UNKNOWN_NAF_CODE rather than risking a wrong translation.
NAF_CODE_DESCRIPTIONS_EN: dict[str, str] = {
    "70.10Z": "Head office activities",
    "71.12B": "Engineering and technical studies",
    "73.11Z": "Advertising agency activities",
    "94.99Z": "Other membership organization activities",
    "64.20Z": "Holding company activities",
    "68.20A": "Residential real estate leasing",
    "35.23Z": "Trade in gaseous fuel via pipelines",
    "72.11Z": "Research and development in biotechnology",
    "26.11Z": "Manufacture of electronic components",
}
# The 21-letter NACE Rev.2 section scheme is a small, stable EU standard;
# only the 6 sections that actually appear in this project's 18 real
# companies are verified and included here (checked against INSEE's
# insee.fr/fr/metadonnees/nafr2/section/<letter> pages, 2026-09-06).
NACE_SECTION_DESCRIPTIONS_EN: dict[str, str] = {
    "C": "Manufacturing",
    "D": "Electricity, gas, steam and air conditioning supply",
    "K": "Financial and insurance activities",
    "L": "Real estate activities",
    "M": "Professional, scientific and technical activities",
    "S": "Other service activities",
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


def search_siren(siren: str) -> dict:
    query = urllib.parse.urlencode({"q": siren})
    request = urllib.request.Request(f"{SEARCH_URL}?{query}", headers={"User-Agent": "ScoutFinanceResearch/1.0 (+non-commercial research script)"})
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


def match_by_siren(siren: str, payload: dict) -> dict | None:
    for item in payload.get("results", []):
        if item.get("siren") == siren:
            return item
    return None


def describe(code: str, table: dict[str, str], unknown_prefix: str) -> tuple[str, bool]:
    if not code:
        return "", False
    description = table.get(code)
    if description is None:
        return f"{unknown_prefix}_{code}", True
    return description, False


def build_record(row: dict[str, str], status: str, reason: str, created_at: str, naf_code: str = "", nace_section: str = "") -> dict[str, Any]:
    naf_description, naf_unknown = describe(naf_code, NAF_CODE_DESCRIPTIONS_EN, "UNKNOWN_NAF_CODE")
    section_description, section_unknown = describe(nace_section, NACE_SECTION_DESCRIPTIONS_EN, "UNKNOWN_NACE_SECTION")
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["resolved_company_name"],
        "siren": row.get("siren", ""), "fetch_status": status, "fetch_reason": reason,
        "naf_code": naf_code, "naf_description_en": naf_description,
        "nace_section": nace_section, "nace_section_description_en": section_description,
        "unknown_naf_code": naf_code if naf_unknown else "", "unknown_nace_section": nace_section if section_unknown else "",
        "phase": PHASE, "created_at_utc": created_at,
    }


FIELDS = ["asset_id", "ticker", "company_name", "siren", "fetch_status", "fetch_reason", "naf_code", "naf_description_en", "nace_section", "nace_section_description_en", "unknown_naf_code", "unknown_nace_section", "phase", "created_at_utc"]


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_sector_codes_fetched": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def build(input_matrix: Path, output_dir: Path, execute: bool) -> dict[str, Any]:
    rows = [r for r in read_csv(input_matrix) if r.get("lookup_status") == "resolved" and r.get("siren")]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if not execute:
        return {"phase": PHASE, "status": "DRY_RUN", "eligible_companies": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}

    records: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        try:
            payload = search_siren(row["siren"])
        except urllib.error.HTTPError as exc:
            records.append(build_record(row, "error", f"http_error_{exc.code}", created_at))
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            records.append(build_record(row, "error", type(exc).__name__, created_at))
            continue
        match = match_by_siren(row["siren"], payload)
        if match is None:
            records.append(build_record(row, "no_siren_match", "siren_not_found_in_results", created_at))
            continue
        records.append(build_record(row, "resolved", "siren_matched", created_at, naf_code=match.get("activite_principale", ""), nace_section=match.get("section_activite_principale", "")))

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_france_sector_codes_v2_38ao.csv", records, FIELDS)
    resolved = sum(1 for r in records if r["fetch_status"] == "resolved")
    unknown_naf = sorted({r["unknown_naf_code"] for r in records if r["unknown_naf_code"]})
    unknown_section = sorted({r["unknown_nace_section"] for r in records if r["unknown_nace_section"]})
    report = {
        "phase": PHASE, "status": "COMPLETED_EUROPE_FRANCE_SECTOR_CODES",
        "eligible_companies": len(rows), "companies_fetched": len(records), "companies_with_sector_codes": resolved,
        "companies_no_siren_match": sum(1 for r in records if r["fetch_status"] == "no_siren_match"),
        "companies_error": sum(1 for r in records if r["fetch_status"] == "error"),
        "unknown_naf_codes_needing_translation": unknown_naf, "unknown_nace_sections_needing_translation": unknown_section,
        "network_used": True, "credentials_used": False, "raw_cache_published": False,
        "scoring_created": False, "ranking_created": False, "recommendations_created": False, "phase9c_authorized": False,
        "note": "Real, confirmed limitation carried over from Austria's individual-vs-consolidated caveat (v2.38AI): the SIREN queried is often the registered head-office/holding legal entity, not the operating business -- e.g. Sanofi, Danone, Pernod Ricard, L'Oreal-adjacent and others here all show NAF 70.10Z 'Head office activities' rather than their real operating sector, an artifact of French corporate registration structure, not a data-quality error in this script.",
    }
    write_text(output_dir / "europe_france_sector_codes_report_v2_38ao.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help="perform the real registry lookups (no credential needed, but network calls are still gated behind this explicit flag)")
    args = parser.parse_args()

    if not args.execute:
        report = build(args.input_matrix, args.output_dir, False)
        print(json.dumps(report, sort_keys=True))
        return 0
    if not args.input_matrix.exists():
        return blocked("input_matrix_not_found")

    report = build(args.input_matrix, args.output_dir, True)
    print(json.dumps({k: report[k] for k in ("status", "eligible_companies", "companies_with_sector_codes", "companies_error")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
