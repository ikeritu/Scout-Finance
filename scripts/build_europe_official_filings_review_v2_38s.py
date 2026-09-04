#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_official_filings_review_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38s_europe_official_filings_review"
PHASE = "v2.38S-europe-official-filings-review"
CONTRACT_VERSION = "europe_official_filings_review_contract_v1"

MATRIX_FIELDS = [
    "asset_id", "company_name", "ticker", "exchange", "mic", "country", "currency", "isin",
    "source_phase", "source_row_hash", "route_from_38q", "official_review_status",
    "official_registry_candidate", "official_registry_name", "filing_route_type",
    "filing_identifier_required", "filing_identifier_present", "filing_identifier_value",
    "identifier_confidence", "jurisdiction_code", "jurisdiction_review_priority",
    "official_filings_fetch_status", "official_filings_data_status", "real_filings_downloaded",
    "real_fundamentals_present", "normalized_fundamentals_present",
    "requires_future_official_execution", "requires_identifier_resolution",
    "no_network_fetch", "no_scraping", "no_api_call", "no_scoring", "no_ranking",
    "no_recommendation", "no_phase9c", "created_at_utc", "phase", "contract_version", "notes",
]
JURISDICTION_FIELDS = [
    "jurisdiction_code", "country", "mic", "exchange", "official_registry_name",
    "official_registry_candidate", "expected_identifier", "identifier_resolution_required",
    "assets", "ready_for_future_execution", "blocked_reason", "network_allowed",
    "scraping_allowed", "api_allowed", "phase9c_authorized",
]
IDENTIFIER_FIELDS = [
    "asset_id", "ticker", "company_name", "country", "mic", "expected_identifier",
    "identifier_present", "identifier_value", "identifier_confidence", "resolution_status",
    "required_next_action", "can_execute_official_collection_now", "blocker_reason",
]
EXCLUSION_FIELDS = [
    "asset_id", "ticker", "company_name", "home_exchange", "home_mic", "home_country",
    "home_currency", "source_type", "fundamental_route_status", "exclusion_reason",
    "phase", "network_allowed", "scraping_allowed", "api_allowed", "scoring_created",
    "ranking_created", "recommendations_created", "phase9c_authorized",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_hash(row: dict[str, str]) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def registry_for(row: dict[str, str], contract: dict[str, Any]) -> dict[str, str]:
    registries = contract["official_registries"]
    country = row.get("home_country", "")
    if country in registries:
        return registries[country]
    return {
        "mic": row.get("home_mic", ""),
        "official_registry_name": "OFFICIAL_ROUTE_REVIEW_REQUIRED",
        "official_registry_candidate": row.get("primary_fundamental_route", "official_registry_review_required"),
        "expected_identifier": row.get("expected_identifier", "UNKNOWN_REVIEW"),
    }


def exclusion_reason(row: dict[str, str]) -> str:
    status = row.get("fundamental_route_status", "")
    if status == "FUNDAMENTALS_ROUTE_READY_FOR_PROVIDER_PILOT":
        return "provider_pilot_not_official_review"
    if status == "FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED":
        return "manual_review_not_official_review"
    return "blocked_or_out_of_scope_not_official_review"


def build(input_routes: Path, input_route_summary: Path, input_provider_summary: Path, input_provider_exclusions: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    rows = read_csv(input_routes)
    q_summary = json.loads(input_route_summary.read_text(encoding="utf-8"))
    r_summary = json.loads(input_provider_summary.read_text(encoding="utf-8"))
    r_exclusions = read_csv(input_provider_exclusions)
    eligible_status = contract["eligible_route_status"]
    official = sorted([row for row in rows if row.get("fundamental_route_status") == eligible_status], key=lambda r: (r.get("home_country", ""), r.get("home_mic", ""), r.get("asset_id", "")))
    excluded = [row for row in rows if row.get("fundamental_route_status") != eligible_status]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    matrix: list[dict[str, str]] = []
    identifiers: list[dict[str, str]] = []
    for priority, row in enumerate(official, start=1):
        registry = registry_for(row, contract)
        expected = registry["expected_identifier"]
        matrix.append({
            "asset_id": row["asset_id"], "company_name": row["company_name"], "ticker": row["ticker"],
            "exchange": row["home_exchange"], "mic": row["home_mic"], "country": row["home_country"],
            "currency": row["home_currency"], "isin": "", "source_phase": row["phase"],
            "source_row_hash": row_hash(row), "route_from_38q": row["fundamental_route_status"],
            "official_review_status": "OFFICIAL_FILINGS_IDENTIFIER_RESOLUTION_REQUIRED",
            "official_registry_candidate": registry["official_registry_candidate"],
            "official_registry_name": registry["official_registry_name"], "filing_route_type": "official_registry_review",
            "filing_identifier_required": expected, "filing_identifier_present": "false",
            "filing_identifier_value": "", "identifier_confidence": "NONE",
            "jurisdiction_code": row["home_country"], "jurisdiction_review_priority": str(priority),
            "official_filings_fetch_status": "NOT_REQUESTED_OFFLINE_PHASE",
            "official_filings_data_status": "NO_REAL_FILINGS_OFFICIAL_EXECUTION_REQUIRED",
            "real_filings_downloaded": "false", "real_fundamentals_present": "false",
            "normalized_fundamentals_present": "false", "requires_future_official_execution": "true",
            "requires_identifier_resolution": "true", "no_network_fetch": "true", "no_scraping": "true",
            "no_api_call": "true", "no_scoring": "true", "no_ranking": "true",
            "no_recommendation": "true", "no_phase9c": "true", "created_at_utc": created_at,
            "phase": PHASE, "contract_version": CONTRACT_VERSION,
            "notes": "Official filing route prepared only; identifier resolution is required before any collection.",
        })
        identifiers.append({
            "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["company_name"],
            "country": row["home_country"], "mic": row["home_mic"], "expected_identifier": expected,
            "identifier_present": "false", "identifier_value": "", "identifier_confidence": "NONE",
            "resolution_status": "IDENTIFIER_RESOLUTION_REQUIRED",
            "required_next_action": "resolve_official_identifier_from_authoritative_source",
            "can_execute_official_collection_now": "false",
            "blocker_reason": "official_identifier_missing_in_current_inputs",
        })

    jurisdiction_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in matrix:
        jurisdiction_groups[(row["jurisdiction_code"], row["country"], row["mic"], row["official_registry_candidate"])].append(row)
    jurisdiction_plan = []
    for (jurisdiction, country, mic, candidate), grouped in sorted(jurisdiction_groups.items()):
        registry = registry_for({"home_country": country, "home_mic": mic, "primary_fundamental_route": candidate}, contract)
        jurisdiction_plan.append({
            "jurisdiction_code": jurisdiction, "country": country, "mic": mic,
            "exchange": sorted({row["exchange"] for row in grouped})[0],
            "official_registry_name": registry["official_registry_name"],
            "official_registry_candidate": candidate,
            "expected_identifier": registry["expected_identifier"],
            "identifier_resolution_required": "true", "assets": str(len(grouped)),
            "ready_for_future_execution": "false",
            "blocked_reason": "identifier_resolution_required_before_official_collection",
            "network_allowed": "false", "scraping_allowed": "false", "api_allowed": "false",
            "phase9c_authorized": "false",
        })

    exclusion_rows = []
    for row in excluded:
        exclusion_rows.append({
            "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["company_name"],
            "home_exchange": row["home_exchange"], "home_mic": row["home_mic"], "home_country": row["home_country"],
            "home_currency": row["home_currency"], "source_type": row["source_type"],
            "fundamental_route_status": row["fundamental_route_status"], "exclusion_reason": exclusion_reason(row),
            "phase": PHASE, "network_allowed": "false", "scraping_allowed": "false", "api_allowed": "false",
            "scoring_created": "false", "ranking_created": "false", "recommendations_created": "false",
            "phase9c_authorized": "false",
        })

    status_counts = Counter(row["fundamental_route_status"] for row in rows)
    jurisdiction_counts = Counter(row["jurisdiction_code"] for row in matrix)
    report = {
        "phase": PHASE, "input_phase": contract["input_phase"], "previous_phase": contract["previous_phase"],
        "status": contract["final_status"], "total_input_assets_from_38q": len(rows),
        "q_summary_input_assets": q_summary.get("input_assets"), "q_summary_routed_assets": q_summary.get("routed_assets"),
        "r_provider_pilot_assets": r_summary.get("provider_pilot_assets_actual"),
        "r_provider_exclusions_rows": len(r_exclusions),
        "official_filings_review_assets_expected": contract["expected_official_filings_review_assets"],
        "official_filings_review_assets_actual": len(matrix),
        "provider_pilot_assets_excluded": status_counts["FUNDAMENTALS_ROUTE_READY_FOR_PROVIDER_PILOT"],
        "manual_review_assets_excluded": status_counts["FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED"],
        "total_excluded_assets": len(exclusion_rows), "jurisdictions_detected": sorted(jurisdiction_counts),
        "jurisdiction_counts": dict(sorted(jurisdiction_counts.items())),
        "identifier_resolution_required_assets": len(identifiers),
        "ready_for_future_official_execution_assets": 0,
        "real_filings_downloaded": False, "real_fundamentals_present": False,
        "normalized_fundamentals_created": False, "network_used": False, "scraping_used": False,
        "api_used": False, "scoring_created": False, "ranking_created": False,
        "recommendations_created": False, "phase9c_authorized": False, "raw_cache_published": False,
        "qa_status": "PASS" if len(matrix) == contract["expected_official_filings_review_assets"] else "FAIL_EXPECTED_OFFICIAL_REVIEW_COUNT_CHANGED",
        "guardrails": contract["guardrails"],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_official_filings_review_matrix_v2_38s.csv", matrix, MATRIX_FIELDS)
    write_csv(output_dir / "europe_official_filings_jurisdiction_plan_v2_38s.csv", jurisdiction_plan, JURISDICTION_FIELDS)
    write_csv(output_dir / "europe_official_filings_identifier_requirements_v2_38s.csv", identifiers, IDENTIFIER_FIELDS)
    write_csv(output_dir / "europe_official_filings_review_exclusions_v2_38s.csv", exclusion_rows, EXCLUSION_FIELDS)
    (output_dir / "europe_official_filings_review_summary_v2_38s.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text("# v2.38S Europe official filings review\n\nOffline official filings review pack. No network, scraping, API calls, filings download, fundamentals, scoring, ranking or recommendations.\n", encoding="utf-8")
    (output_dir / "EUROPE_OFFICIAL_FILINGS_REVIEW_CONTRACT_v2_38s.md").write_text("# Europe Official Filings Review Contract v2.38S\n\nOnly FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW rows enter this phase. Official identifiers are not invented.\n", encoding="utf-8")
    (output_dir / "PHASE9S_EUROPE_OFFICIAL_FILINGS_REVIEW_v2_38s.md").write_text(f"# Phase 9S Europe Official Filings Review\n\nDecision: {contract['final_status']}\n\nOfficial filings review assets: {len(matrix)}\nProvider pilot excluded: {report['provider_pilot_assets_excluded']}\nManual review excluded: {report['manual_review_assets_excluded']}\nIdentifier resolution required: {len(identifiers)}\n\nNext recommended phase: v2.38T Europe manual review pack.\n", encoding="utf-8")
    manifest = {
        "phase": PHASE, "decision": contract["final_status"],
        "inputs": {
            str(input_routes): {"bytes": input_routes.stat().st_size, "sha256": sha(input_routes)},
            str(input_route_summary): {"bytes": input_route_summary.stat().st_size, "sha256": sha(input_route_summary)},
            str(input_provider_summary): {"bytes": input_provider_summary.stat().st_size, "sha256": sha(input_provider_summary)},
            str(input_provider_exclusions): {"bytes": input_provider_exclusions.stat().st_size, "sha256": sha(input_provider_exclusions)},
            str(CONTRACT): {"bytes": CONTRACT.stat().st_size, "sha256": sha(CONTRACT)},
        },
        "outputs": {}, "scripts": ["scripts/build_europe_official_filings_review_v2_38s.py"],
        "schemas": ["schemas/europe_official_filings_review_record_v1.schema.json"],
        "counts": {
            "official_filings_review_assets_actual": len(matrix),
            "provider_pilot_assets_excluded": report["provider_pilot_assets_excluded"],
            "manual_review_assets_excluded": report["manual_review_assets_excluded"],
            "total_excluded_assets": len(exclusion_rows),
            "identifier_resolution_required_assets": len(identifiers),
        },
        "created_at_utc": created_at, "raw_cache_published": False, "guardrails": contract["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.name != "europe_official_filings_review_manifest_v2_38s.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    (output_dir / "europe_official_filings_review_manifest_v2_38s.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-routes", type=Path, default=ROOT / contract["input_routes"])
    parser.add_argument("--input-route-summary", type=Path, default=ROOT / contract["input_route_summary"])
    parser.add_argument("--input-provider-summary", type=Path, default=ROOT / contract["input_provider_summary"])
    parser.add_argument("--input-provider-exclusions", type=Path, default=ROOT / contract["input_provider_exclusions"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.input_routes, args.input_route_summary, args.input_provider_summary, args.input_provider_exclusions, args.output_dir), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
