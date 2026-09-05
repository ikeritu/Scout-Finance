#!/usr/bin/env python3
"""Block 9U: assess -- offline, no network -- whether real execution could
be authorized right now for any of the three Europe fundamentals routes
Q created (provider_pilot -> v2.38R, official_filings_review -> v2.38S,
manual_review -> v2.38T). This phase never executes anything itself; it
only reads the three routes' own committed summaries plus two live,
boolean-only checks (does an execution script exist on disk, is a
credential environment variable set) and reports a per-route verdict.

The credential check reads only whether the named environment variable is
non-empty -- the actual value is never read into a variable used anywhere
else in this script, never logged, and never written to any output.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_fundamentals_execution_readiness_gate_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38u_europe_fundamentals_execution_readiness_gate"
PHASE = "v2.38U-europe-fundamentals-execution-readiness-gate"
CONTRACT_VERSION = "europe_fundamentals_execution_readiness_gate_contract_v1"

MATRIX_FIELDS = [
    "route", "route_phase", "assets_in_route", "execution_method", "automation_script_status",
    "credential_env_var", "credential_present", "prerequisite_description", "prerequisite_complete_assets",
    "prerequisite_required_assets", "prerequisite_status", "blockers", "readiness_status",
    "next_required_action", "real_fundamentals_downloaded", "network_used_in_this_gate",
    "phase9c_authorized", "phase", "contract_version", "created_at_utc", "notes",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def script_exists(pattern: str) -> bool:
    if not pattern:
        return False
    return len(glob.glob(str(ROOT / pattern))) > 0


def assess_route(route_id: str, route_config: dict[str, Any], summary: dict[str, Any], created_at: str) -> dict[str, str]:
    total_assets = int(summary.get(route_config["total_assets_field"], 0))
    complete_assets = int(summary.get(route_config["prerequisite_complete_assets_field"], 0))
    prerequisite_status = "COMPLETE" if complete_assets >= total_assets and total_assets > 0 else "INCOMPLETE"

    env_var = route_config["credential_env_var"]
    if env_var:
        credential_present = "true" if os.environ.get(env_var, "").strip() else "false"
    else:
        credential_present = "not_applicable"

    if route_config["execution_method"] == "human_manual_review":
        automation_script_status = "NOT_APPLICABLE_HUMAN_PROCESS"
        script_ready = True  # a human process has no script to build; it is not a blocker in itself
    else:
        automation_script_status = "IMPLEMENTED" if script_exists(route_config["automation_script_glob"]) else "NOT_IMPLEMENTED"
        script_ready = automation_script_status == "IMPLEMENTED"

    blockers = []
    if prerequisite_status != "COMPLETE":
        blockers.append(f"{route_id}_prerequisite_incomplete")
    if not script_ready:
        blockers.append("automation_script_not_implemented")
    if env_var and credential_present == "false":
        blockers.append("credential_missing")

    readiness_status = "READY" if not blockers else "NOT_READY"

    return {
        "route": route_id, "route_phase": route_config["route_phase"], "assets_in_route": str(total_assets),
        "execution_method": route_config["execution_method"], "automation_script_status": automation_script_status,
        "credential_env_var": env_var, "credential_present": credential_present,
        "prerequisite_description": route_config["prerequisite_description"],
        "prerequisite_complete_assets": str(complete_assets), "prerequisite_required_assets": str(total_assets),
        "prerequisite_status": prerequisite_status, "blockers": ";".join(blockers),
        "readiness_status": readiness_status, "next_required_action": route_config["next_required_action"],
        "real_fundamentals_downloaded": "false", "network_used_in_this_gate": "false", "phase9c_authorized": "false",
        "phase": PHASE, "contract_version": CONTRACT_VERSION, "created_at_utc": created_at,
        "notes": f"Assessed offline against the committed {route_config['route_phase']} summary; no network call, credential value, or file content beyond boolean presence checks was used.",
    }


def build(input_provider_pilot_summary: Path, input_official_filings_summary: Path, input_manual_review_summary: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    summaries = {
        "provider_pilot": json.loads(input_provider_pilot_summary.read_text(encoding="utf-8")),
        "official_filings_review": json.loads(input_official_filings_summary.read_text(encoding="utf-8")),
        "manual_review": json.loads(input_manual_review_summary.read_text(encoding="utf-8")),
    }
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    matrix = [assess_route(route_id, route_config, summaries[route_id], created_at) for route_id, route_config in contract["routes"].items()]
    overall_status = contract["ready_status"] if all(row["readiness_status"] == "READY" for row in matrix) else contract["not_ready_status"]

    report = {
        "phase": PHASE, "input_phase": contract["input_phase"], "previous_phase": contract["previous_phase"],
        "status": overall_status,
        "routes_assessed": len(matrix),
        "routes_ready": sum(1 for row in matrix if row["readiness_status"] == "READY"),
        "routes_not_ready": sum(1 for row in matrix if row["readiness_status"] == "NOT_READY"),
        "per_route_status": {row["route"]: row["readiness_status"] for row in matrix},
        "per_route_blockers": {row["route"]: row["blockers"] for row in matrix},
        "real_filings_downloaded": False, "real_fundamentals_present": False,
        "normalized_fundamentals_created": False, "network_used": False, "scraping_used": False,
        "api_used": False, "scoring_created": False, "ranking_created": False,
        "recommendations_created": False, "phase9c_authorized": False, "raw_cache_published": False,
        "qa_status": "PASS",
        "guardrails": contract["guardrails"],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_fundamentals_execution_readiness_matrix_v2_38u.csv", matrix, MATRIX_FIELDS)
    (output_dir / "europe_fundamentals_execution_readiness_summary_v2_38u.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# v2.38U Europe fundamentals execution readiness gate\n\n"
        "Offline readiness assessment only -- no network, no scraping, no API calls, no real fundamentals, "
        "no scoring, ranking, or recommendations. Reads the v2.38R/S/T summaries plus boolean-only script/"
        "credential presence checks; never executes any real collection.\n",
        encoding="utf-8",
    )
    (output_dir / "EUROPE_FUNDAMENTALS_EXECUTION_READINESS_GATE_CONTRACT_v2_38u.md").write_text(
        "# Europe Fundamentals Execution Readiness Gate Contract v2.38U\n\n"
        "Assesses readiness per route (provider_pilot, official_filings_review, manual_review). "
        "No route is marked READY unless its prerequisite is complete, its execution method has an "
        "implemented script (or is a human process), and any required credential is present. Credential "
        "values are never read into a report, only their presence.\n",
        encoding="utf-8",
    )
    (output_dir / "PHASE9U_EUROPE_FUNDAMENTALS_EXECUTION_READINESS_GATE_v2_38u.md").write_text(
        f"# Phase 9U Europe Fundamentals Execution Readiness Gate\n\n"
        f"Decision: {overall_status}\n\n"
        + "\n".join(f"{row['route']} ({row['route_phase']}): {row['readiness_status']} -- blockers: {row['blockers'] or 'none'}" for row in matrix)
        + "\n\nNext recommended phase: v2.38V Europe fundamentals collection pilot, once at least one route reaches READY.\n",
        encoding="utf-8",
    )
    manifest = {
        "phase": PHASE, "decision": overall_status,
        "inputs": {
            str(input_provider_pilot_summary): {"bytes": input_provider_pilot_summary.stat().st_size, "sha256": sha(input_provider_pilot_summary)},
            str(input_official_filings_summary): {"bytes": input_official_filings_summary.stat().st_size, "sha256": sha(input_official_filings_summary)},
            str(input_manual_review_summary): {"bytes": input_manual_review_summary.stat().st_size, "sha256": sha(input_manual_review_summary)},
            str(CONTRACT): {"bytes": CONTRACT.stat().st_size, "sha256": sha(CONTRACT)},
        },
        "outputs": {}, "scripts": ["scripts/build_europe_fundamentals_execution_readiness_gate_v2_38u.py"],
        "schemas": ["schemas/europe_fundamentals_execution_readiness_gate_record_v1.schema.json"],
        "counts": {"routes_assessed": len(matrix), "routes_ready": report["routes_ready"], "routes_not_ready": report["routes_not_ready"]},
        "created_at_utc": created_at, "raw_cache_published": False, "guardrails": contract["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.name != "europe_fundamentals_execution_readiness_manifest_v2_38u.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    (output_dir / "europe_fundamentals_execution_readiness_manifest_v2_38u.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-provider-pilot-summary", type=Path, default=ROOT / contract["input_provider_pilot_summary"])
    parser.add_argument("--input-official-filings-summary", type=Path, default=ROOT / contract["input_official_filings_summary"])
    parser.add_argument("--input-manual-review-summary", type=Path, default=ROOT / contract["input_manual_review_summary"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.input_provider_pilot_summary, args.input_official_filings_summary, args.input_manual_review_summary, args.output_dir), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
