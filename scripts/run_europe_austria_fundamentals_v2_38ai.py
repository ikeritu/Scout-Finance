#!/usr/bin/env python3
"""Block 9AI: fetch real, structured Austrian annual-accounts figures
(Bilanz/GuV) for the 20 Austrian assets already identity/registry-
resolved via GLEIF in v2.38AF, using firmenakte.at -- a commercial
aggregator of Austria's official government registers (Firmenbuch via
justizonline.gv.at, GISA, Ediktsdatei, BMF-Liste), chosen explicitly by
the user after being told no official free API exists for the Austrian
Firmenbuch and that this is a for-profit product with a genuinely free
tier (100 requests/month, no credit card, no time limit), not an
official or non-profit source like GLEIF/CRO/OpenFIGI used elsewhere in
this project.

Real advantage confirmed live before writing this script: unlike GB/
Ireland's Companies House/CRO name-search lookups, this needs no name
matching at all -- GLEIF already gave us each company's real
Firmenbuchnummer (e.g. PORR AG -> "34853f") in v2.38AF, and
firmenakte.at's endpoint is keyed directly by that number
(GET /api/v1/businesses/{fnr}). No ambiguity is possible.

Real data confirmed live for PORR AG (fnr 34853f): the response includes
`parsedJahresabschluesse`, an array of up to 5 fiscal years, each with a
`bilanz` (balance sheet) and `guv` (income statement) object of already-
parsed numeric fields (not PDF, not raw XBRL tags to re-parse) -- e.g.
bilanzSumme (total assets) EUR 1,775,949,626.05, eigenkapital (equity)
EUR 589,899,666.58, umsatzerloese (revenue) EUR 212,437,331.95 for FY
ending 2025-12-31. This is the entity's own standalone (Einzelabschluss)
filing -- it can differ substantially from a group's consolidated IFRS
figures reported to investors, and this script records it as exactly
that, never relabeling it as "consolidated."

Only a fixed, closed list of target concepts is extracted (never every
field in the response) -- the same discipline as the GB/Ireland iXBRL
extractors. A concept absent from a given year's parsed statement is
recorded as not-tagged, never guessed or interpolated. Currency is
recorded as EUR (Austria's real currency; not present as an explicit
field in the API response, so treated as a documented assumption, not a
silently invented fact).

Blocked by default; --execute plus SCOUT_FINANCE_FIRMENAKTE_API_KEY are
both required. The credential is sent only as the x-api-key header,
never logged, never written to any output file. Given the free tier's
hard cap of 100 requests/month and 20 real target companies (well within
budget for one run), this script makes exactly one API call per company
-- no retries beyond real transient-error handling, to avoid needlessly
spending the monthly quota.
"""
from __future__ import annotations

import argparse
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
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38af_europe_gleif_registry_lookup/europe_gleif_registry_lookup_matrix_v2_38af.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ai_europe_austria_fundamentals"
PHASE = "v2.38AI-europe-austria-fundamentals"
JURISDICTION_FILTER = "AT"
API_BASE = "https://api.firmenakte.at/api/v1/businesses"
CREDENTIAL_ENV = "SCOUT_FINANCE_FIRMENAKTE_API_KEY"
MIN_SECONDS_BETWEEN_CALLS = 0.5
MAX_ATTEMPTS = 2

# Fixed, closed list of concepts extracted from `bilanz` (balance sheet,
# stock/instant) and `guv` (income statement, flow/period) -- never every
# field the API returns, the same targeted-extraction discipline as the
# GB/Ireland iXBRL scripts.
BILANZ_CONCEPTS = ["bilanzSumme", "anlageVermoegen", "umlaufvermoegen", "eigenkapital", "verbindlichkeiten", "rueckstellungen", "liquidesVermoegen"]
GUV_CONCEPTS = ["umsatzerloese", "betriebsErfolg", "ergebnisVorSteuern", "jahresueberschuss"]

PROFILE_FIELDS = [
    "asset_id", "ticker", "fnr", "resolved_company_name", "legal_name_firmenakte", "is_active",
    "legal_form", "court", "years_of_jahresabschluss_available", "fetch_status", "fetch_reason",
    "phase", "created_at_utc",
]
RECORD_FIELDS = [
    "asset_id", "ticker", "fnr", "concept", "statement_kind", "period_end", "value", "currency",
    "source_document_key", "normalized_fundamentals_present", "phase", "created_at_utc",
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


def fetch_business(fnr: str, api_key: str) -> dict:
    # A real HTTP 403 (Cloudflare error code 1010) was hit live using
    # Python's default "Python-urllib/x.x" User-Agent -- this is a
    # User-Agent-string blocklist rule, not a genuine bot challenge (no
    # JS/CAPTCHA involved, and the provider's own documentation
    # recommends calling this exact endpoint with curl). An honest,
    # descriptive User-Agent identifying this as a research script
    # (never impersonating a browser) resolves it, confirmed live.
    headers = {"x-api-key": api_key, "User-Agent": "ScoutFinanceResearch/1.0 (+non-commercial research script)"}
    request = urllib.request.Request(f"{API_BASE}/{fnr}", headers=headers)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                time.sleep(5.0)
                continue
            raise
    raise RuntimeError("retries_exhausted")


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_fundamentals_present": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def extract_records(row: dict[str, str], payload: dict, created_at: str) -> list[dict[str, Any]]:
    records = []
    for statement in payload.get("parsedJahresabschluesse", []):
        period_end = (statement.get("documentDate") or "")[:10]
        doc_key = statement.get("documentKey", "")
        bilanz = statement.get("bilanz") or {}
        guv = statement.get("guv") or {}
        for concept in BILANZ_CONCEPTS:
            value = bilanz.get(concept)
            records.append(_record(row, concept, "stock", period_end, value, doc_key, created_at))
        for concept in GUV_CONCEPTS:
            value = guv.get(concept)
            records.append(_record(row, concept, "flow", period_end, value, doc_key, created_at))
    return records


def _record(row: dict[str, str], concept: str, kind: str, period_end: str, value: float | None, doc_key: str, created_at: str) -> dict[str, Any]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "fnr": row["national_registration_number"],
        "concept": concept, "statement_kind": kind, "period_end": period_end, "value": value,
        "currency": "EUR", "source_document_key": doc_key, "normalized_fundamentals_present": value is not None,
        "phase": PHASE, "created_at_utc": created_at,
    }


def build(input_matrix: Path, output_dir: Path, records_output: Path, api_key: str) -> dict[str, Any]:
    rows = [r for r in read_csv(input_matrix) if r.get("home_country") == JURISDICTION_FILTER and r.get("gleif_lookup_status") == "resolved" and r.get("national_registration_number")]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    profiles = []
    all_records: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        fnr = row["national_registration_number"]
        try:
            payload = fetch_business(fnr, api_key)
        except urllib.error.HTTPError as exc:
            profiles.append(_profile(row, "error", f"http_error_{exc.code}", created_at))
            continue
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            profiles.append(_profile(row, "error", type(exc).__name__, created_at))
            continue

        statements = payload.get("parsedJahresabschluesse", [])
        profiles.append(_profile(
            row, "fetched", "business_profile_and_statements_retrieved", created_at,
            legal_name_firmenakte=payload.get("name", ""), is_active=payload.get("isActive"),
            legal_form=(payload.get("legalForm") or {}).get("text", ""), court=(payload.get("court") or {}).get("text", ""),
            years=len(statements),
        ))
        all_records.extend(extract_records(row, payload, created_at))

    records_output.parent.mkdir(parents=True, exist_ok=True)
    tmp = records_output.with_suffix(records_output.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(records_output)

    fetched = sum(1 for p in profiles if p["fetch_status"] == "fetched")
    extracted_values = sum(1 for r in all_records if r["normalized_fundamentals_present"])
    report = {
        "phase": PHASE, "input_resolved_assets": len(rows), "companies_fetched": fetched,
        "companies_error": len(profiles) - fetched, "total_records": len(all_records),
        "extracted_values": extracted_values, "not_tagged_values": len(all_records) - extracted_values,
        "credentials_used": True, "real_filings_downloaded": fetched > 0, "real_fundamentals_present": extracted_values > 0,
        "raw_cache_published": False, "phase9c_authorized": False, "data_source": "firmenakte.at (commercial aggregator of official Austrian government registers, user-approved exception, not an official/non-profit source)",
        "note": "Values are the entity's own standalone (Einzelabschluss) filed figures, not necessarily group-consolidated IFRS figures. Multi-year (up to 5 fiscal years per company) where available.",
    }

    write_csv(output_dir / "europe_austria_fundamentals_profile_matrix_v2_38ai.csv", profiles, PROFILE_FIELDS)
    write_text(output_dir / "europe_austria_fundamentals_summary_v2_38ai.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def _profile(row: dict[str, str], status: str, reason: str, created_at: str, legal_name_firmenakte: str = "", is_active: bool | None = None, legal_form: str = "", court: str = "", years: int = 0) -> dict[str, Any]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "fnr": row["national_registration_number"],
        "resolved_company_name": row.get("legal_name", ""), "legal_name_firmenakte": legal_name_firmenakte,
        "is_active": is_active, "legal_form": legal_form, "court": court, "years_of_jahresabschluss_available": years,
        "fetch_status": status, "fetch_reason": reason, "phase": PHASE, "created_at_utc": created_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--records-output", type=Path, default=OUT / "europe_austria_fundamental_records_v2_38ai.jsonl")
    parser.add_argument("--execute", action="store_true", help=f"perform the real firmenakte.at fetch (requires {CREDENTIAL_ENV})")
    args = parser.parse_args()

    if not args.execute:
        rows = [r for r in read_csv(args.input_matrix) if r.get("home_country") == JURISDICTION_FILTER and r.get("gleif_lookup_status") == "resolved"] if args.input_matrix.exists() else []
        print(json.dumps({"status": "DRY_RUN", "eligible_assets": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}, sort_keys=True))
        return 0

    api_key = os.environ.get(CREDENTIAL_ENV, "").strip()
    if not api_key:
        return blocked("credential_missing")

    report = build(args.input_matrix, args.output_dir, args.records_output, api_key)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
