#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_manual_review_pack_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38t_europe_manual_review_pack"
PHASE = "v2.38T-europe-manual-review-pack"
CONTRACT_VERSION = "europe_manual_review_pack_contract_v1"

MATRIX_FIELDS = [
    "asset_id", "company_name_source_value", "identity_verified", "ticker", "home_exchange", "home_mic",
    "home_country", "home_currency", "source_phase", "source_row_hash", "route_from_38q",
    "manual_review_status", "identity_review_required", "registry_review_required", "provider_review_required",
    "candidate_registry_note", "required_human_actions", "real_filings_downloaded", "real_fundamentals_present",
    "normalized_fundamentals_present", "no_network_fetch", "no_scraping", "no_api_call", "no_scoring",
    "no_ranking", "no_recommendation", "no_phase9c", "created_at_utc", "phase", "contract_version", "notes",
]
CHECKLIST_FIELDS = [
    "asset_id", "ticker", "action_sequence", "required_action", "action_description",
    "action_status", "network_allowed", "scraping_allowed", "api_allowed",
]
EXCLUSION_FIELDS = [
    "asset_id", "ticker", "company_name", "home_exchange", "home_mic", "home_country", "home_currency",
    "source_type", "fundamental_route_status", "exclusion_reason", "phase",
    "network_allowed", "scraping_allowed", "api_allowed", "scoring_created", "ranking_created",
    "recommendations_created", "phase9c_authorized",
]

ACTION_DESCRIPTIONS = {
    "confirm_real_company_identity": (
        "company_name_source_value is inherited from the Deutsche Boerse Xetra all-tradable-instruments "
        "feed used since v2.38C/v2.38N and is a known placeholder, not a verified company name. Confirm "
        "the real legal entity name from an authoritative source before any further action."
    ),
    "confirm_isin_or_national_registration_number": (
        "No ISIN or Irish company registration number has been resolved for this asset in any prior phase. "
        "Confirm one from an authoritative source before selecting a fundamentals route."
    ),
    "determine_fundamentals_route_registry_or_provider": (
        "Euronext Dublin (XDUB) has no confirmed official-registry route (unlike XLON/GB or XMAD/ES, see "
        "v2.38S) or provider-API route (unlike XETR/XPAR/etc., see v2.38Q) in this project yet. Once "
        "identity is confirmed, decide whether to route this asset to an official registry (e.g. Ireland's "
        "Companies Registration Office) or to the existing provider-API pilot."
    ),
}


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


def exclusion_reason(row: dict[str, str], eligible_status: str) -> str:
    status = row.get("fundamental_route_status", "")
    if status == "FUNDAMENTALS_ROUTE_READY_FOR_PROVIDER_PILOT":
        return "provider_pilot_not_manual_review"
    if status == "FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW":
        return "official_filings_review_not_manual_review"
    if status == eligible_status:
        return ""
    return "blocked_or_out_of_scope_not_manual_review"


def build(input_routes: Path, input_route_summary: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    rows = read_csv(input_routes)
    q_summary = json.loads(input_route_summary.read_text(encoding="utf-8"))
    eligible_status = contract["eligible_route_status"]
    placeholders = set(contract["known_placeholder_company_names"])
    required_actions = contract["required_human_actions"]

    eligible = sorted([row for row in rows if row.get("fundamental_route_status") == eligible_status], key=lambda r: (r.get("home_country", ""), r.get("home_mic", ""), r.get("asset_id", "")))
    excluded = [row for row in rows if row.get("fundamental_route_status") != eligible_status]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    matrix: list[dict[str, str]] = []
    checklist: list[dict[str, str]] = []
    for row in eligible:
        company_name = row.get("company_name", "")
        is_placeholder = company_name in placeholders
        notes = (
            f"company_name_source_value ('{company_name}') matches a known upstream placeholder pattern; "
            "not a verified company name."
        ) if is_placeholder else "company_name_source_value has not been independently verified in this phase."

        matrix.append({
            "asset_id": row["asset_id"], "company_name_source_value": company_name, "identity_verified": "false",
            "ticker": row["ticker"], "home_exchange": row["home_exchange"], "home_mic": row["home_mic"],
            "home_country": row["home_country"], "home_currency": row["home_currency"],
            "source_phase": row["phase"], "source_row_hash": row_hash(row),
            "route_from_38q": row["fundamental_route_status"],
            "manual_review_status": "EUROPE_MANUAL_REVIEW_PACK_PENDING_HUMAN_ACTION",
            "identity_review_required": "true", "registry_review_required": "true", "provider_review_required": "true",
            "candidate_registry_note": "No official registry or provider route confirmed for this home MIC yet; human decision required.",
            "required_human_actions": ";".join(required_actions),
            "real_filings_downloaded": "false", "real_fundamentals_present": "false", "normalized_fundamentals_present": "false",
            "no_network_fetch": "true", "no_scraping": "true", "no_api_call": "true", "no_scoring": "true",
            "no_ranking": "true", "no_recommendation": "true", "no_phase9c": "true",
            "created_at_utc": created_at, "phase": PHASE, "contract_version": CONTRACT_VERSION, "notes": notes,
        })
        for sequence, action in enumerate(required_actions, start=1):
            checklist.append({
                "asset_id": row["asset_id"], "ticker": row["ticker"], "action_sequence": str(sequence),
                "required_action": action, "action_description": ACTION_DESCRIPTIONS[action],
                "action_status": "PENDING_HUMAN_ACTION", "network_allowed": "false",
                "scraping_allowed": "false", "api_allowed": "false",
            })

    exclusion_rows = []
    for row in excluded:
        exclusion_rows.append({
            "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["company_name"],
            "home_exchange": row["home_exchange"], "home_mic": row["home_mic"], "home_country": row["home_country"],
            "home_currency": row["home_currency"], "source_type": row["source_type"],
            "fundamental_route_status": row["fundamental_route_status"],
            "exclusion_reason": exclusion_reason(row, eligible_status), "phase": PHASE,
            "network_allowed": "false", "scraping_allowed": "false", "api_allowed": "false",
            "scoring_created": "false", "ranking_created": "false", "recommendations_created": "false",
            "phase9c_authorized": "false",
        })

    status_counts = Counter(row["fundamental_route_status"] for row in rows)
    placeholder_identity_count = sum(1 for row in matrix if row["company_name_source_value"] in placeholders)
    report = {
        "phase": PHASE, "input_phase": contract["input_phase"], "previous_phase": contract["previous_phase"],
        "status": contract["final_status"], "total_input_assets_from_38q": len(rows),
        "q_summary_input_assets": q_summary.get("input_assets"), "q_summary_routed_assets": q_summary.get("routed_assets"),
        "manual_review_pack_assets_expected": contract["expected_manual_review_assets"],
        "manual_review_pack_assets_actual": len(matrix),
        "provider_pilot_assets_excluded": status_counts["FUNDAMENTALS_ROUTE_READY_FOR_PROVIDER_PILOT"],
        "official_filings_review_assets_excluded": status_counts["FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW"],
        "total_excluded_assets": len(exclusion_rows),
        "assets_with_placeholder_identity": placeholder_identity_count,
        "checklist_actions_total": len(checklist),
        "identifier_resolution_required_assets": len(matrix),
        "ready_for_future_manual_review_execution_assets": 0,
        "real_filings_downloaded": False, "real_fundamentals_present": False,
        "normalized_fundamentals_created": False, "network_used": False, "scraping_used": False,
        "api_used": False, "scoring_created": False, "ranking_created": False,
        "recommendations_created": False, "phase9c_authorized": False, "raw_cache_published": False,
        "qa_status": "PASS" if len(matrix) == contract["expected_manual_review_assets"] else "FAIL_EXPECTED_MANUAL_REVIEW_COUNT_CHANGED",
        "guardrails": contract["guardrails"],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_manual_review_pack_matrix_v2_38t.csv", matrix, MATRIX_FIELDS)
    write_csv(output_dir / "europe_manual_review_pack_checklist_v2_38t.csv", checklist, CHECKLIST_FIELDS)
    write_csv(output_dir / "europe_manual_review_pack_exclusions_v2_38t.csv", exclusion_rows, EXCLUSION_FIELDS)
    (output_dir / "europe_manual_review_pack_summary_v2_38t.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# v2.38T Europe manual review pack\n\n"
        "Offline manual review pack for the assets v2.38Q routed to FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED "
        "(Euronext Dublin / Ireland). No network, scraping, API calls, filings download, fundamentals, "
        "scoring, ranking or recommendations. Every asset's company_name is an unverified upstream "
        "placeholder -- identity confirmation is the first required human action, before any registry "
        "or provider decision.\n",
        encoding="utf-8",
    )
    (output_dir / "EUROPE_MANUAL_REVIEW_PACK_CONTRACT_v2_38t.md").write_text(
        "# Europe Manual Review Pack Contract v2.38T\n\n"
        "Only FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED rows enter this phase. No identity, registry, or "
        "provider decision is invented here -- every asset is left PENDING_HUMAN_ACTION.\n",
        encoding="utf-8",
    )
    (output_dir / "PHASE9T_EUROPE_MANUAL_REVIEW_PACK_v2_38t.md").write_text(
        f"# Phase 9T Europe Manual Review Pack\n\n"
        f"Decision: {contract['final_status']}\n\n"
        f"Manual review pack assets: {len(matrix)}\n"
        f"Assets with unverified placeholder identity: {placeholder_identity_count}\n"
        f"Provider pilot excluded: {report['provider_pilot_assets_excluded']}\n"
        f"Official filings review excluded: {report['official_filings_review_assets_excluded']}\n"
        f"Checklist actions total: {len(checklist)}\n\n"
        f"Next recommended phase: v2.38U Europe fundamentals execution readiness gate.\n",
        encoding="utf-8",
    )
    manifest = {
        "phase": PHASE, "decision": contract["final_status"],
        "inputs": {
            str(input_routes): {"bytes": input_routes.stat().st_size, "sha256": sha(input_routes)},
            str(input_route_summary): {"bytes": input_route_summary.stat().st_size, "sha256": sha(input_route_summary)},
            str(CONTRACT): {"bytes": CONTRACT.stat().st_size, "sha256": sha(CONTRACT)},
        },
        "outputs": {}, "scripts": ["scripts/build_europe_manual_review_pack_v2_38t.py"],
        "schemas": ["schemas/europe_manual_review_pack_record_v1.schema.json"],
        "counts": {
            "manual_review_pack_assets_actual": len(matrix),
            "provider_pilot_assets_excluded": report["provider_pilot_assets_excluded"],
            "official_filings_review_assets_excluded": report["official_filings_review_assets_excluded"],
            "total_excluded_assets": len(exclusion_rows),
            "checklist_actions_total": len(checklist),
        },
        "created_at_utc": created_at, "raw_cache_published": False, "guardrails": contract["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.name != "europe_manual_review_pack_manifest_v2_38t.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    (output_dir / "europe_manual_review_pack_manifest_v2_38t.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-routes", type=Path, default=ROOT / contract["input_routes"])
    parser.add_argument("--input-route-summary", type=Path, default=ROOT / contract["input_route_summary"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.input_routes, args.input_route_summary, args.output_dir), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
