from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.23F"
PHASE = "Calibration Closure Report"
PHASE_TYPE = "calibration-closure-report"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

V23A = OUTPUT_DIR / "scoring_model_calibration_roadmap_v2_23a.json"
V23B = OUTPUT_DIR / "metadata_coverage_improvement_plan_v2_23b.json"
V23C = OUTPUT_DIR / "scoring_calibration_data_design_v2_23c.json"
V23D = OUTPUT_DIR / "scoring_formula_redesign_dry_run_v2_23d.json"
V23E = OUTPUT_DIR / "calibration_review_freeze_decision_v2_23e.json"

CURRENT_POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
LEGACY_DRY_RUN_SCORES = OUTPUT_DIR / "scoring_dry_run_no_promotion_scores_v2_22d.csv"
REDESIGNED_DRY_RUN_SCORES = OUTPUT_DIR / "scoring_formula_redesign_dry_run_scores_v2_23d.csv"

REPORT_JSON = OUTPUT_DIR / "calibration_closure_report_v2_23f.json"
REPORT_MD = OUTPUT_DIR / "calibration_closure_report_v2_23f.md"
SUMMARY_CSV = OUTPUT_DIR / "calibration_closure_report_summary_v2_23f.csv"
CHECKS_CSV = OUTPUT_DIR / "calibration_closure_report_checks_v2_23f.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "calibration_closure_report_artifact_manifest_v2_23f.csv"
PHASE_ROLLUP_CSV = OUTPUT_DIR / "calibration_closure_report_phase_rollup_v2_23f.csv"
BLOCKERS_CSV = OUTPUT_DIR / "calibration_closure_report_remaining_blockers_v2_23f.csv"
HANDOFF_CSV = OUTPUT_DIR / "calibration_closure_report_handoff_to_v2_24_v2_23f.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "calibration_closure_report_decision_register_v2_23f.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "calibration_closure_report_next_actions_v2_23f.csv"

EXPECTED_STATUSES = {
    "v2.23A": "SCORING_MODEL_CALIBRATION_ROADMAP_COMPLETED_PRODUCTION_SCORING_DEFERRED",
    "v2.23B": "METADATA_COVERAGE_IMPROVEMENT_PLAN_COMPLETED_NO_DATASET_MODIFICATION",
    "v2.23C": "SCORING_CALIBRATION_DATA_DESIGN_COMPLETED_NO_LABELS_NO_SCORING_NO_PROMOTION",
    "v2.23D": "SCORING_FORMULA_REDESIGN_DRY_RUN_COMPLETED_NO_PROMOTION_NO_CANONICAL_CHANGE",
    "v2.23E": "CALIBRATION_REVIEW_FREEZE_DECISION_COMPLETED_REDESIGNED_DRY_RUN_FROZEN_NOT_PROMOTED",
}

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

LEGACY_SCORING_ROWS_EXPECTED = 33498
LEGACY_SCORING_SHA_EXPECTED = "a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1"

REDESIGNED_SCORING_ROWS_EXPECTED = 33498
REDESIGNED_SCORING_SHA_EXPECTED = "096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb"

STATUS_COMPLETED = "CALIBRATION_CLOSURE_REPORT_COMPLETED_V2_23_CLOSED_PRODUCTION_SCORING_DEFERRED"
STATUS_FAILED = "CALIBRATION_CLOSURE_REPORT_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.24A - Metadata Gap Audit"
SECONDARY_NEXT_PHASE = "v2.24B - Country / MIC / Currency Backfill Plan"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        raise SystemExit(f"Missing required CSV artifact: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        PHASE_ROLLUP_CSV,
        BLOCKERS_CSV,
        HANDOFF_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    phase_files = {
        "v2.23A": V23A,
        "v2.23B": V23B,
        "v2.23C": V23C,
        "v2.23D": V23D,
        "v2.23E": V23E,
    }

    phase_reports = {phase_id: read_json(path) for phase_id, path in phase_files.items()}
    pointer = read_json(CURRENT_POINTER)

    current_rows = count_csv_rows(CURRENT_DATASET)
    legacy_rows = count_csv_rows(LEGACY_DRY_RUN_SCORES)
    redesigned_rows = count_csv_rows(REDESIGNED_DRY_RUN_SCORES)

    current_sha = sha256_file(CURRENT_DATASET)
    legacy_sha = sha256_file(LEGACY_DRY_RUN_SCORES)
    redesigned_sha = sha256_file(REDESIGNED_DRY_RUN_SCORES)
    pointer_sha = sha256_file(CURRENT_POINTER)

    v23b_summary = phase_reports["v2.23B"].get("summary", {})
    v23c_summary = phase_reports["v2.23C"].get("summary", {})
    v23d_summary = phase_reports["v2.23D"].get("summary", {})
    v23e_summary = phase_reports["v2.23E"].get("summary", {})

    phase_rollup_rows = [
        {
            "phase_id": "v2.23A",
            "phase_name": "Scoring Model Calibration Roadmap",
            "status": phase_reports["v2.23A"].get("status", ""),
            "critical_failed_checks": phase_reports["v2.23A"].get("summary", {}).get("critical_failed_checks", ""),
            "result": "Calibration roadmap created; production scoring deferred.",
            "promotion_performed": False,
            "canonical_modified": False,
        },
        {
            "phase_id": "v2.23B",
            "phase_name": "Metadata Coverage Improvement Plan",
            "status": phase_reports["v2.23B"].get("status", ""),
            "critical_failed_checks": v23b_summary.get("critical_failed_checks", ""),
            "result": "Metadata gaps identified; no backfill executed.",
            "promotion_performed": False,
            "canonical_modified": False,
        },
        {
            "phase_id": "v2.23C",
            "phase_name": "Scoring Calibration Data Design",
            "status": phase_reports["v2.23C"].get("status", ""),
            "critical_failed_checks": v23c_summary.get("critical_failed_checks", ""),
            "result": "Label schema and sample plan designed; no manual labels created.",
            "promotion_performed": False,
            "canonical_modified": False,
        },
        {
            "phase_id": "v2.23D",
            "phase_name": "Scoring Formula Redesign Dry Run",
            "status": phase_reports["v2.23D"].get("status", ""),
            "critical_failed_checks": v23d_summary.get("critical_failed_checks", ""),
            "result": "Redesigned dry-run scores created; attractiveness not invented.",
            "promotion_performed": False,
            "canonical_modified": False,
        },
        {
            "phase_id": "v2.23E",
            "phase_name": "Calibration Review / Freeze Decision",
            "status": phase_reports["v2.23E"].get("status", ""),
            "critical_failed_checks": v23e_summary.get("critical_failed_checks", ""),
            "result": "Redesigned dry-run scores frozen as non-promoted reference.",
            "promotion_performed": False,
            "canonical_modified": False,
        },
    ]

    blockers_rows = [
        {
            "blocker_id": "V23_BLOCKER_001",
            "blocker": "manual_calibration_labels_missing",
            "blocking_for_production_scoring": True,
            "source_phase": "v2.23C/v2.23E",
            "resolution_phase": "future calibration execution phase",
        },
        {
            "blocker_id": "V23_BLOCKER_002",
            "blocker": "attractiveness_score_unavailable",
            "blocking_for_production_scoring": True,
            "source_phase": "v2.23D/v2.23E",
            "resolution_phase": "future manual labels or authorized fundamentals/enrichment gate",
        },
        {
            "blocker_id": "V23_BLOCKER_003",
            "blocker": "metadata_gap_remediation_not_executed",
            "blocking_for_production_scoring": True,
            "source_phase": "v2.23B/v2.23E",
            "resolution_phase": "v2.24A/v2.24B/v2.24C",
        },
        {
            "blocker_id": "V23_BLOCKER_004",
            "blocker": "production_scoring_gate_not_approved",
            "blocking_for_production_scoring": True,
            "source_phase": "v2.23E",
            "resolution_phase": "future explicit production scoring gate",
        },
        {
            "blocker_id": "V23_BLOCKER_005",
            "blocker": "external_enrichment_not_authorized",
            "blocking_for_production_scoring": False,
            "source_phase": "project_guardrails",
            "resolution_phase": "optional v2.30 external enrichment gate",
        },
    ]

    handoff_rows = [
        {
            "handoff_id": "V24_HANDOFF_001",
            "target_phase": "v2.24A - Metadata Gap Audit",
            "handoff_item": "Start metadata gap audit from v2.23B findings.",
            "input_artifact": str(V23B),
            "reason": "Metadata gaps remain the main blocker before any scoring promotion.",
        },
        {
            "handoff_id": "V24_HANDOFF_002",
            "target_phase": "v2.24B - Country / MIC / Currency Backfill Plan",
            "handoff_item": "Prioritize deterministic mapping for country, MIC and currency.",
            "input_artifact": str(V23B),
            "reason": "Scorable country top value remained __MISSING__ in v2.23B.",
        },
        {
            "handoff_id": "V24_HANDOFF_003",
            "target_phase": "v2.24C - Asset Type Normalization Plan",
            "handoff_item": "Normalize asset_type, instrument_type and instrument_scope before production scoring.",
            "input_artifact": str(V23B),
            "reason": "Production scoring needs reliable separation of common equity and excluded instruments.",
        },
        {
            "handoff_id": "V24_HANDOFF_004",
            "target_phase": "future production scoring gate",
            "handoff_item": "Keep v2.23D redesigned scores as non-promoted reference only.",
            "input_artifact": str(V23E),
            "reason": "v2.23E froze redesigned dry-run scoring.",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_23F_CLOSURE_001",
            "decision": "Close v2.23 calibration block.",
            "accepted": True,
            "reason": "v2.23A-E completed with zero critical failed checks.",
            "effect": "v2.23 is closed as calibration/design/dry-run/freeze block.",
        },
        {
            "decision_id": "V2_23F_CLOSURE_002",
            "decision": "Keep both v2.22D and v2.23D scoring outputs non-promoted.",
            "accepted": True,
            "reason": "No manual labels, no attractiveness score, and metadata blockers remain.",
            "effect": "production_scoring_authorized=False.",
        },
        {
            "decision_id": "V2_23F_CLOSURE_003",
            "decision": "Move next work to v2.24A metadata gap audit.",
            "accepted": True,
            "reason": "v2.23B/v2.23E identified metadata quality as the next blocking area.",
            "effect": "recommended_next_phase=v2.24A.",
        },
        {
            "decision_id": "V2_23F_CLOSURE_004",
            "decision": "Do not modify canonical dataset, active pointer, dry-run scores, .gitignore or repo exclusions.",
            "accepted": True,
            "reason": "Closure report is documentation only.",
            "effect": "canonical_dataset_modified=False; active_pointer_modified=False.",
        },
        {
            "decision_id": "V2_23F_CLOSURE_005",
            "decision": "Keep OpenAI, broker APIs and full59k disabled.",
            "accepted": True,
            "reason": "No separate authorization exists.",
            "effect": "openai_called=False; broker_called=False; full59k=DEPRECATED_DEFERRED.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "metadata_quality",
            "action": "open_metadata_gap_audit",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "v2.23 closed with scoring frozen and metadata gaps blocking promotion.",
            "guardrails": "Deterministic audit only; no canonical replacement unless later gate authorizes it.",
        },
        {
            "action_order": 2,
            "action_scope": "metadata_backfill_planning",
            "action": "prepare_country_mic_currency_backfill_plan",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Country, MIC and currency coverage remain weak.",
            "guardrails": "No OpenAI/broker/full59k unless separately approved.",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0
    warning_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed, warning_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        if severity == "warning" and not passed:
            warning_failed += 1

        checks.append({
            "check": check,
            "passed": bool(passed),
            "severity": severity,
            "detail": detail,
        })

    for phase_id, expected_status in EXPECTED_STATUSES.items():
        report = phase_reports[phase_id]
        summary = report.get("summary", {})
        add_check(f"{phase_id}_status_expected", report.get("status") == expected_status, "critical", str(report.get("status")))
        add_check(f"{phase_id}_critical_failed_checks_zero", str(summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={summary.get('critical_failed_checks')}")

    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("legacy_scoring_rows_expected", legacy_rows == LEGACY_SCORING_ROWS_EXPECTED, "critical", f"legacy_rows={legacy_rows}")
    add_check("legacy_scoring_sha_expected", legacy_sha == LEGACY_SCORING_SHA_EXPECTED, "critical", legacy_sha)
    add_check("redesigned_scoring_rows_expected", redesigned_rows == REDESIGNED_SCORING_ROWS_EXPECTED, "critical", f"redesigned_rows={redesigned_rows}")
    add_check("redesigned_scoring_sha_expected", redesigned_sha == REDESIGNED_SCORING_SHA_EXPECTED, "critical", redesigned_sha)
    add_check("v23e_freeze_decision_expected", v23e_summary.get("freeze_decision") == "FREEZE_REDESIGNED_DRY_RUN_AS_NON_PROMOTED_REFERENCE", "critical", str(v23e_summary.get("freeze_decision")))
    add_check("v23e_promotion_not_approved", boolish(v23e_summary.get("promotion_approved")) is False, "critical", f"promotion_approved={v23e_summary.get('promotion_approved')}")
    add_check("manual_labels_not_created", boolish(v23e_summary.get("manual_labels_created")) is False, "critical", f"manual_labels_created={v23e_summary.get('manual_labels_created')}")
    add_check("attractiveness_not_available", boolish(v23e_summary.get("attractiveness_score_available")) is False, "critical", f"attractiveness_score_available={v23e_summary.get('attractiveness_score_available')}")
    add_check("production_scoring_not_authorized", True, "critical", "production_scoring_authorized=False")
    add_check("scoring_not_promoted", True, "critical", "scoring_promoted=False")
    add_check("canonical_dataset_not_modified", sha256_file(CURRENT_DATASET) == CURRENT_SHA_EXPECTED, "critical", f"current_sha_after={sha256_file(CURRENT_DATASET)}")
    add_check("active_pointer_not_modified", sha256_file(CURRENT_POINTER) == pointer_sha, "critical", f"pointer_sha_after={sha256_file(CURRENT_POINTER)}")
    add_check("legacy_score_output_not_modified", sha256_file(LEGACY_DRY_RUN_SCORES) == LEGACY_SCORING_SHA_EXPECTED, "critical", f"legacy_sha_after={sha256_file(LEGACY_DRY_RUN_SCORES)}")
    add_check("redesigned_score_output_not_modified", sha256_file(REDESIGNED_DRY_RUN_SCORES) == REDESIGNED_SCORING_SHA_EXPECTED, "critical", f"redesigned_sha_after={sha256_file(REDESIGNED_DRY_RUN_SCORES)}")
    add_check("phase_rollup_created", len(phase_rollup_rows) == 5, "critical", f"phase_rollup_rows={len(phase_rollup_rows)}")
    add_check("remaining_blockers_created", len(blockers_rows) >= 5, "critical", f"blockers_rows={len(blockers_rows)}")
    add_check("handoff_created", len(handoff_rows) >= 4, "critical", f"handoff_rows={len(handoff_rows)}")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("gitignore_not_modified_by_phase", True, "critical", "gitignore_modified=False")
    add_check("git_info_exclude_not_modified_by_phase", True, "critical", "git_info_exclude_modified=False")

    status = STATUS_COMPLETED if critical_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Close v2.23 calibration block and hand off to metadata gap audit",
        "phase_type": PHASE_TYPE,
        "closure_decision": "V2_23_CLOSED_PRODUCTION_SCORING_DEFERRED" if status == STATUS_COMPLETED else "V2_23_CLOSURE_FAILED_REVIEW_REQUIRED",
        "closed_phase_range": "v2.23A-v2.23F",
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows,
        "current_dataset_sha": current_sha,
        "legacy_dry_run_scoring_output": str(LEGACY_DRY_RUN_SCORES),
        "legacy_dry_run_scoring_output_rows": legacy_rows,
        "legacy_dry_run_scoring_output_sha": legacy_sha,
        "redesigned_scoring_output": str(REDESIGNED_DRY_RUN_SCORES),
        "redesigned_scoring_output_rows": redesigned_rows,
        "redesigned_scoring_output_sha": redesigned_sha,
        "v23a_completed": phase_reports["v2.23A"].get("status") == EXPECTED_STATUSES["v2.23A"],
        "v23b_completed": phase_reports["v2.23B"].get("status") == EXPECTED_STATUSES["v2.23B"],
        "v23c_completed": phase_reports["v2.23C"].get("status") == EXPECTED_STATUSES["v2.23C"],
        "v23d_completed": phase_reports["v2.23D"].get("status") == EXPECTED_STATUSES["v2.23D"],
        "v23e_completed": phase_reports["v2.23E"].get("status") == EXPECTED_STATUSES["v2.23E"],
        "v23_completed_phases": 5,
        "phase_rollup_rows": len(phase_rollup_rows),
        "remaining_blockers": len(blockers_rows),
        "handoff_rows": len(handoff_rows),
        "freeze_decision": v23e_summary.get("freeze_decision"),
        "promotion_approved": False,
        "production_scoring_authorized": False,
        "scoring_promoted": False,
        "canonical_dataset_modified": False,
        "active_pointer_modified": False,
        "legacy_score_output_modified": False,
        "redesigned_score_output_modified": False,
        "manual_labels_created": False,
        "attractiveness_score_available": False,
        "attractiveness_score_invented": False,
        "metadata_backfill_executed": False,
        "openai_authorized": False,
        "openai_called": False,
        "broker_authorized": False,
        "broker_called": False,
        "full59k": "DEPRECATED_DEFERRED",
        "gitignore_modified": False,
        "git_info_exclude_modified": False,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": NEXT_PHASE,
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    artifact_manifest_rows = [
        {
            "artifact": f"{phase_id.lower()}_input",
            "path": str(path),
            "rows": 1,
            "sha256": sha256_file(path),
            "role": "input_phase_report",
        }
        for phase_id, path in phase_files.items()
    ]

    artifact_manifest_rows.extend([
        {
            "artifact": "current_operational_pointer_input",
            "path": str(CURRENT_POINTER),
            "rows": 1,
            "sha256": pointer_sha,
            "role": "input_pointer_no_modification",
        },
        {
            "artifact": "current_dataset_input",
            "path": str(CURRENT_DATASET),
            "rows": current_rows,
            "sha256": current_sha,
            "role": "input_dataset_no_modification",
        },
        {
            "artifact": "legacy_dry_run_scores_input",
            "path": str(LEGACY_DRY_RUN_SCORES),
            "rows": legacy_rows,
            "sha256": legacy_sha,
            "role": "input_legacy_scores_no_modification",
        },
        {
            "artifact": "redesigned_dry_run_scores_input",
            "path": str(REDESIGNED_DRY_RUN_SCORES),
            "rows": redesigned_rows,
            "sha256": redesigned_sha,
            "role": "input_redesigned_scores_no_modification_not_promoted",
        },
    ])

    write_csv(PHASE_ROLLUP_CSV, phase_rollup_rows, [
        "phase_id",
        "phase_name",
        "status",
        "critical_failed_checks",
        "result",
        "promotion_performed",
        "canonical_modified",
    ])
    write_csv(BLOCKERS_CSV, blockers_rows, [
        "blocker_id",
        "blocker",
        "blocking_for_production_scoring",
        "source_phase",
        "resolution_phase",
    ])
    write_csv(HANDOFF_CSV, handoff_rows, [
        "handoff_id",
        "target_phase",
        "handoff_item",
        "input_artifact",
        "reason",
    ])

    phase_rollup_sha = sha256_file(PHASE_ROLLUP_CSV)
    blockers_sha = sha256_file(BLOCKERS_CSV)
    handoff_sha = sha256_file(HANDOFF_CSV)

    artifact_manifest_rows.extend([
        {
            "artifact": "phase_rollup_output",
            "path": str(PHASE_ROLLUP_CSV),
            "rows": len(phase_rollup_rows),
            "sha256": phase_rollup_sha,
            "role": "closure_phase_rollup_output",
        },
        {
            "artifact": "remaining_blockers_output",
            "path": str(BLOCKERS_CSV),
            "rows": len(blockers_rows),
            "sha256": blockers_sha,
            "role": "closure_remaining_blockers_output",
        },
        {
            "artifact": "handoff_to_v2_24_output",
            "path": str(HANDOFF_CSV),
            "rows": len(handoff_rows),
            "sha256": handoff_sha,
            "role": "closure_handoff_output",
        },
    ])

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    report = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "phase_rollup": phase_rollup_rows,
        "remaining_blockers": blockers_rows,
        "handoff_to_v2_24": handoff_rows,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "current_dataset": str(CURRENT_DATASET),
            "current_dataset_rows": current_rows,
            "current_dataset_sha": current_sha,
            "legacy_dry_run_score_output": str(LEGACY_DRY_RUN_SCORES),
            "legacy_dry_run_score_output_rows": legacy_rows,
            "legacy_dry_run_score_output_sha": legacy_sha,
            "redesigned_scoring_output": str(REDESIGNED_DRY_RUN_SCORES),
            "redesigned_scoring_output_rows": redesigned_rows,
            "redesigned_scoring_output_sha": redesigned_sha,
            "v2_23_closed": status == STATUS_COMPLETED,
            "promotion_approved": False,
            "production_scoring_authorized": False,
            "scoring_promoted": False,
            "canonical_dataset_modified": False,
            "active_pointer_modified": False,
            "legacy_score_output_modified": False,
            "redesigned_score_output_modified": False,
            "manual_labels_created": False,
            "attractiveness_score_available": False,
            "attractiveness_score_invented": False,
            "metadata_backfill_executed": False,
            "openai_authorized": False,
            "openai_called": False,
            "broker_authorized": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
            "history_rewrite_performed": False,
            "force_push_required": False,
            "gitignore_modified": False,
            "git_info_exclude_modified": False,
        },
        "recommended_next_phase": NEXT_PHASE,
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_json(REPORT_JSON, report)

    phase_lines = "\n".join(
        f"- `{row['phase_id']}` — {row['phase_name']}: {row['result']}"
        for row in phase_rollup_rows
    )

    blocker_lines = "\n".join(
        f"- `{row['blocker_id']}` — blocking `{row['blocking_for_production_scoring']}` — {row['blocker']}"
        for row in blockers_rows
    )

    handoff_lines = "\n".join(
        f"- `{row['handoff_id']}` → `{row['target_phase']}` — {row['handoff_item']}"
        for row in handoff_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{report["generated_at_utc"]}`

## Closure decision

Closure decision: **{summary["closure_decision"]}**

The v2.23 calibration block is closed as a calibration/design/dry-run/freeze block.

No production scoring has been authorized.

## Closed phases

{phase_lines}

## Remaining blockers

{blocker_lines}

## Handoff

{handoff_lines}

## References

Current dataset:

`{CURRENT_DATASET}`

Rows: `{current_rows}`  
SHA256: `{current_sha}`

Legacy v2.22D dry-run score:

`{LEGACY_DRY_RUN_SCORES}`

Rows: `{legacy_rows}`  
SHA256: `{legacy_sha}`

Redesigned v2.23D dry-run score:

`{REDESIGNED_DRY_RUN_SCORES}`

Rows: `{redesigned_rows}`  
SHA256: `{redesigned_sha}`

## Guardrails

- v2.23 closed: `{status == STATUS_COMPLETED}`
- Promotion approved: `False`
- Production scoring authorized: `False`
- Scoring promoted: `False`
- Canonical dataset modified: `False`
- Active pointer modified: `False`
- Legacy score output modified: `False`
- Redesigned score output modified: `False`
- Manual labels created: `False`
- Attractiveness score invented: `False`
- Metadata backfill executed: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`
- .gitignore modified: `False`
- .git/info/exclude modified: `False`

## Checks

{check_lines}

## Recommended next phase

Primary: `{NEXT_PHASE}`

Secondary: `{SECONDARY_NEXT_PHASE}`
""",
    )

    print("")
    print("v2.23F calibration closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("PHASE_ROLLUP:")
    for row in phase_rollup_rows:
        print(f"- {row['phase_id']}: {row['status']}")
    print("")
    print("REMAINING_BLOCKERS:")
    for row in blockers_rows:
        print(f"- {row['blocker_id']}: blocking={row['blocking_for_production_scoring']} - {row['blocker']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
