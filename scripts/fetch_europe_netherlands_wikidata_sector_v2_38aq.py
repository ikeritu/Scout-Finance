#!/usr/bin/env python3
"""Block 9AQ: fetch a real industry classification for the 44 Netherlands
companies already identified by v2.38AB, continuing the attack on the
Europe sector-classification gap (v2.38AN GB, v2.38AO France, v2.38AP
Germany -- confirmed structurally non-public).

The Dutch KVK register does have a real SBI activity code per company,
but its production API requires a paid subscription (confirmed live,
2026-09-06: EUR 6.40/month base fee plus per-query cost on top) -- this
project does not spend money without the user's explicit authorization.
Presented with that real choice plus a free alternative, the user chose
the free alternative: Wikidata's public SPARQL endpoint
(query.wikidata.org/sparql), queried by ISIN (property P946) to find each
company's industry (property P452). No account, no API key, official
Wikimedia infrastructure, CC0-licensed data.

This is NOT an official government source -- it is a community-edited,
open, non-profit database, closer in kind to OffeneRegister.de (the
nonprofit civic reuse this project already considered acceptable in
principle in v2.38AC) than to Companies House or SIRENE. Live-verified
before this script was written: 35/44 real NL companies (79.5%) resolve
to at least one real English-language industry label via ISIN (e.g. ASML
Holding -> "semiconductor industry", Heineken -> "brewing industry").
Every row this script produces carries an explicit non-official-source
caveat, and it is fed into v2.38AM as a clearly attributed, separate
sector-text source -- never presented as equivalent-confidence to GB's
Companies House or France's SIRENE data.

Fail-closed: an ISIN matched by more than one distinct Wikidata item
(a genuine data-quality problem on Wikidata's side, not expected but
possible on a community-edited database) is left unresolved rather than
guessed. A single item with multiple industry values is not ambiguous --
all of its industries are captured.

Blocked by default; --execute is required (no credential needed, but
real network calls are still gated behind this explicit flag, matching
this project's convention for v2.38AD/v2.38AO).
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38ab_europe_full_identity_resolution/europe_full_identity_resolution_xetra_source_matrix_v2_38ab.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38aq_europe_netherlands_wikidata_sector"
PHASE = "v2.38AQ-europe-netherlands-wikidata-sector"
JURISDICTION_FILTER = "NL"
SPARQL_URL = "https://query.wikidata.org/sparql"
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 30.0
NON_OFFICIAL_SOURCE_CAVEAT = "Sourced from Wikidata (query.wikidata.org), a community-edited, non-profit open database -- NOT an official government registry like Companies House or SIRENE. Verify manually before relying on it for any conclusion."


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


def build_sparql_query(isins: list[str]) -> str:
    values = " ".join(f'"{isin}"' for isin in isins)
    return f"""
SELECT ?isin ?item ?itemLabel ?industryLabel WHERE {{
  VALUES ?isin {{ {values} }}
  ?item wdt:P946 ?isin.
  OPTIONAL {{ ?item wdt:P452 ?industry. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""


def query_wikidata(isins: list[str]) -> dict:
    query = build_sparql_query(isins)
    data = urllib.parse.urlencode({"query": query, "format": "json"}).encode("utf-8")
    request = urllib.request.Request(SPARQL_URL, data=data, headers={
        "User-Agent": "ScoutFinanceResearch/1.0 (+non-commercial research script)",
        "Accept": "application/sparql-results+json",
    })
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            raise
    raise RuntimeError("rate_limit_retries_exhausted")


def group_by_isin(payload: dict) -> dict[str, dict[str, Any]]:
    """Group SPARQL result rows by isin -> {qid -> {"label": str, "industries": set[str]}}.
    Keeping distinct items separate (never merged) is what makes the
    ambiguity check downstream possible."""
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for binding in payload.get("results", {}).get("bindings", []):
        isin = binding["isin"]["value"]
        qid = binding["item"]["value"].rsplit("/", 1)[-1]
        label = binding.get("itemLabel", {}).get("value", "")
        industry = binding.get("industryLabel", {}).get("value", "")
        entry = grouped[isin].setdefault(qid, {"label": label, "industries": set()})
        if industry:
            entry["industries"].add(industry)
    return grouped


def build_record(row: dict[str, str], status: str, reason: str, created_at: str, qid: str = "", industries: list[str] | None = None) -> dict[str, Any]:
    industries = industries or []
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["resolved_company_name"],
        "isin": row.get("isin", ""), "wikidata_qid": qid, "fetch_status": status, "fetch_reason": reason,
        "industries": ";".join(industries), "non_official_source_caveat": NON_OFFICIAL_SOURCE_CAVEAT,
        "phase": PHASE, "created_at_utc": created_at,
    }


FIELDS = ["asset_id", "ticker", "company_name", "isin", "wikidata_qid", "fetch_status", "fetch_reason", "industries", "non_official_source_caveat", "phase", "created_at_utc"]


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_sector_data_fetched": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def build(input_matrix: Path, output_dir: Path, execute: bool) -> dict[str, Any]:
    rows = [r for r in read_csv(input_matrix) if r.get("resolution_status") == "resolved" and r.get("home_country") == JURISDICTION_FILTER and r.get("isin")]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if not execute:
        return {"phase": PHASE, "status": "DRY_RUN", "eligible_companies": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}

    records: list[dict[str, Any]] = []
    try:
        payload = query_wikidata([r["isin"] for r in rows])
        grouped = group_by_isin(payload)
    except urllib.error.HTTPError as exc:
        grouped = None
        for row in rows:
            records.append(build_record(row, "error", f"http_error_{exc.code}", created_at))
    except (urllib.error.URLError, TimeoutError) as exc:
        grouped = None
        for row in rows:
            records.append(build_record(row, "error", type(exc).__name__, created_at))

    if grouped is not None:
        for row in rows:
            items = grouped.get(row["isin"], {})
            if not items:
                records.append(build_record(row, "no_wikidata_match", "isin_not_found_on_wikidata", created_at))
                continue
            if len(items) > 1:
                records.append(build_record(row, "ambiguous", "multiple_distinct_wikidata_items_share_isin", created_at))
                continue
            (qid, data), = items.items()
            if not data["industries"]:
                records.append(build_record(row, "no_industry", "wikidata_item_has_no_industry_property", created_at, qid=qid))
                continue
            records.append(build_record(row, "resolved", "single_wikidata_item_matched", created_at, qid=qid, industries=sorted(data["industries"])))

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_netherlands_wikidata_sector_v2_38aq.csv", records, FIELDS)
    resolved = sum(1 for r in records if r["fetch_status"] == "resolved")
    report = {
        "phase": PHASE, "status": "COMPLETED_EUROPE_NETHERLANDS_WIKIDATA_SECTOR",
        "eligible_companies": len(rows), "companies_fetched": len(records), "companies_with_industry": resolved,
        "companies_no_wikidata_match": sum(1 for r in records if r["fetch_status"] == "no_wikidata_match"),
        "companies_no_industry": sum(1 for r in records if r["fetch_status"] == "no_industry"),
        "companies_ambiguous": sum(1 for r in records if r["fetch_status"] == "ambiguous"),
        "companies_error": sum(1 for r in records if r["fetch_status"] == "error"),
        "network_used": True, "credentials_used": False, "raw_cache_published": False,
        "scoring_created": False, "ranking_created": False, "recommendations_created": False, "phase9c_authorized": False,
        "source_type": "NON_OFFICIAL_NONPROFIT_COMMUNITY_DATABASE",
        "note": "User-approved exception (2026-09-06, after KVK's real paid-subscription requirement was confirmed live) to use Wikidata instead of an official government source for Dutch sector classification. Every record carries a non_official_source_caveat field; v2.38AM's consumption of this data must never treat it as equivalent-confidence to Companies House (v2.38AN) or SIRENE (v2.38AO).",
    }
    write_text(output_dir / "europe_netherlands_wikidata_sector_report_v2_38aq.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help="perform the real Wikidata SPARQL query (no credential needed, but network calls are still gated behind this explicit flag)")
    args = parser.parse_args()

    if not args.execute:
        report = build(args.input_matrix, args.output_dir, False)
        print(json.dumps(report, sort_keys=True))
        return 0
    if not args.input_matrix.exists():
        return blocked("input_matrix_not_found")

    report = build(args.input_matrix, args.output_dir, True)
    print(json.dumps({k: report[k] for k in ("status", "eligible_companies", "companies_with_industry", "companies_error")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
