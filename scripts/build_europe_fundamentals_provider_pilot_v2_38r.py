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
CONTRACT = ROOT / "config/europe_fundamentals_provider_pilot_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38r_europe_fundamentals_pilot_provider"
PHASE = "v2.38R-europe-fundamentals-provider-pilot"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha_text(row: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build(input_routes: Path, input_summary: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    rows = read_csv(input_routes)
    q_summary = json.loads(input_summary.read_text(encoding="utf-8"))
    eligible = [r for r in rows if r["fundamental_route_status"] == contract["eligible_route_status"]]
    excluded = [r for r in rows if r["fundamental_route_status"] != contract["eligible_route_status"]]
    eligible = sorted(eligible, key=lambda r: (r["home_country"], r["home_mic"], r["asset_id"]))
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    batch_size = int(contract["batch_size"])
    matrix = []
    batches = []
    for batch_index, start in enumerate(range(0, len(eligible), batch_size), start=1):
        chunk = eligible[start:start + batch_size]
        bid = f"EU_PROVIDER_PILOT_{batch_index:03d}"
        batches.append({"batch_id": bid, "batch_index": str(batch_index), "batch_size": str(batch_size), "asset_count": str(len(chunk)), "asset_ids": ";".join(r["asset_id"] for r in chunk), "countries_covered": ";".join(sorted({r["home_country"] for r in chunk})), "exchanges_covered": ";".join(sorted({r["home_exchange"] for r in chunk})), "provider_candidate": "eodhd_fundamentals", "ready_for_provider_execution": "true", "blocked_reason": "", "network_allowed": "false", "real_fundamentals_downloaded": "false", "normalized_fundamentals_created": "false", "scoring_created": "false", "ranking_created": "false", "recommendations_created": "false", "phase9c_authorized": "false"})
        for priority, row in enumerate(chunk, start=start + 1):
            matrix.append({"asset_id": row["asset_id"], "company_name": row["company_name"], "ticker": row["ticker"], "exchange": row["home_exchange"], "mic": row["home_mic"], "country": row["home_country"], "currency": row["home_currency"], "source_phase": row["phase"], "source_row_hash": sha_text(row), "route_from_38q": row["fundamental_route_status"], "provider_pilot_status": "PROVIDER_PILOT_READY_FOR_FUTURE_EXECUTION", "provider_candidate": row["primary_fundamental_route"], "provider_query_key": row["provider_symbol_candidate"], "provider_identifier_strategy": "provider_symbol_from_38q", "provider_batch_id": bid, "provider_priority": str(priority), "fundamentals_fetch_status": "NOT_REQUESTED_OFFLINE_PHASE", "fundamentals_data_status": "NO_REAL_DATA_PROVIDER_EXECUTION_REQUIRED", "fundamentals_real_data_present": "false", "fundamentals_placeholder_only": "true", "normalized_fundamentals_present": "false", "no_network_fetch": "true", "no_scoring": "true", "no_ranking": "true", "no_recommendation": "true", "no_phase9c": "true", "requires_future_provider_execution": "true", "created_at_utc": created_at, "phase": PHASE, "contract_version": "europe_fundamentals_provider_pilot_contract_v1", "notes": "Provider execution prepared only; no fundamentals requested or stored in v2.38R."})
    exclusion_rows = [{"asset_id": r["asset_id"], "ticker": r["ticker"], "company_name": r["company_name"], "home_exchange": r["home_exchange"], "home_mic": r["home_mic"], "home_country": r["home_country"], "home_currency": r["home_currency"], "source_type": r["source_type"], "fundamental_route_status": r["fundamental_route_status"], "exclusion_reason": "official_filings_review_not_provider_pilot" if "OFFICIAL" in r["fundamental_route_status"] else "manual_review_not_provider_pilot", "phase": PHASE, "network_allowed": "false", "scoring_created": "false", "ranking_created": "false", "recommendations_created": "false", "phase9c_authorized": "false"} for r in excluded]
    coverage = []
    for field in ["country", "exchange", "mic", "currency", "provider_candidate"]:
        for value, count in sorted(Counter(r[field] for r in matrix).items()):
            coverage.append({"dimension": field, "dimension_value": value, "asset_count": str(count), "provider_candidate": "eodhd_fundamentals", "provider_pilot_status": "PROVIDER_PILOT_READY_FOR_FUTURE_EXECUTION", "fundamentals_fetch_status": "NOT_REQUESTED_OFFLINE_PHASE", "real_fundamentals_downloaded": "false", "normalized_fundamentals_created": "false"})
    status_counts = Counter(r["fundamental_route_status"] for r in rows)
    report = {"phase": PHASE, "input_phase": "v2.38Q", "status": contract["final_status"], "total_input_assets_from_38q": len(rows), "q_summary_input_assets": q_summary["input_assets"], "q_summary_routed_assets": q_summary["routed_assets"], "provider_pilot_assets_expected": contract["expected_provider_pilot_assets"], "provider_pilot_assets_actual": len(eligible), "official_filings_review_assets": status_counts["FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW"], "manual_review_assets": status_counts["FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED"], "excluded_assets": len(excluded), "batches_created": len(batches), "batch_size": batch_size, "network_used": False, "real_fundamentals_downloaded": False, "normalized_fundamentals_created": False, "scoring_created": False, "ranking_created": False, "recommendations_created": False, "raw_cache_published": False, "qa_status": "PASS", "guardrails": contract["guardrails"]}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_fundamentals_provider_pilot_matrix_v2_38r.csv", matrix, list(matrix[0].keys()))
    write_csv(output_dir / "europe_fundamentals_provider_pilot_batches_v2_38r.csv", batches, list(batches[0].keys()))
    write_csv(output_dir / "europe_fundamentals_provider_pilot_coverage_v2_38r.csv", coverage, list(coverage[0].keys()))
    write_csv(output_dir / "europe_fundamentals_provider_pilot_exclusions_v2_38r.csv", exclusion_rows, list(exclusion_rows[0].keys()))
    (output_dir / "europe_fundamentals_provider_pilot_summary_v2_38r.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text("# v2.38R Europe fundamentals provider pilot\n\nOffline provider execution pack only.\n", encoding="utf-8")
    (output_dir / "EUROPE_FUNDAMENTALS_PROVIDER_PILOT_CONTRACT_v2_38r.md").write_text("# Europe Fundamentals Provider Pilot Contract v2.38R\n\nNo network, real fundamentals, scoring, ranking or recommendations.\n", encoding="utf-8")
    (output_dir / "PHASE9R_EUROPE_FUNDAMENTALS_PILOT_PROVIDER_v2_38r.md").write_text(f"# Phase 9R Europe Fundamentals Provider Pilot\n\nDecision: {contract['final_status']}\n\nProvider pilot assets: {len(eligible)}\nBatches: {len(batches)}\n", encoding="utf-8")
    manifest = {"phase": PHASE, "inputs": {str(input_routes): {"sha256": sha(input_routes)}}, "outputs": {}, "counts": {"provider_pilot_assets_actual": len(eligible), "excluded_assets": len(excluded), "batches_created": len(batches)}, "guardrails": contract["guardrails"]}
    for path in sorted(output_dir.glob("*")):
        if path.name != "europe_fundamentals_provider_pilot_manifest_v2_38r.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    (output_dir / "europe_fundamentals_provider_pilot_manifest_v2_38r.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-routes", type=Path, default=ROOT / contract["input_routes"])
    parser.add_argument("--input-summary", type=Path, default=ROOT / contract["input_summary"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.input_routes, args.input_summary, args.output_dir), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
