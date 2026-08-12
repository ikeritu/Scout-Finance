from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20K"
PHASE = "ASX Canonical Promotion Plan"
PHASE_TYPE = "canonical-promotion-plan-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PRE_HKEX_CURRENT_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"

V220G_JSON = OUTPUT_DIR / "asx_expanded_rebuild_candidate_v2_20g.json"
V220H_JSON = OUTPUT_DIR / "asx_expanded_validation_v2_20h.json"
V220I_JSON = OUTPUT_DIR / "asx_closure_report_v2_20i.json"
V220J_JSON = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_v2_20j.json"

REPORT_JSON = OUTPUT_DIR / "asx_canonical_promotion_plan_v2_20k.json"
REPORT_MD = OUTPUT_DIR / "asx_canonical_promotion_plan_v2_20k.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_canonical_promotion_plan_summary_v2_20k.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_canonical_promotion_plan_checks_v2_20k.csv"
ROLLBACK_PLAN_CSV = OUTPUT_DIR / "asx_canonical_promotion_rollback_plan_v2_20k.csv"
EXECUTION_PLAN_CSV = OUTPUT_DIR / "asx_canonical_promotion_execution_plan_v2_20k.csv"
RISK_REGISTER_CSV = OUTPUT_DIR / "asx_canonical_promotion_risk_register_v2_20k.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_canonical_promotion_plan_next_actions_v2_20k.csv"

EXPECTED_V220G_STATUS = "ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220H_STATUS = "ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED"
EXPECTED_V220I_STATUS = "ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED"
EXPECTED_V220J_STATUS = "ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED = 40996
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392
ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED = 42708
ASX_NET_NEW_ROWS_EXPECTED = 1316
UPLIFT_VS_ACTIVE_CANONICAL_EXPECTED = 4421

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"
ASX_VALIDATED_CANDIDATE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_ABOVE_QUALITY_FLOOR_EXPECTED = 708
REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED = 2292
ROWS_TO_ASPIRATIONAL_50K_EXPECTED = 7292

PLANNED_PROMOTION_SOURCE = ASX_VALIDATED_CANDIDATE_DATASET
PLANNED_PROMOTED_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
PLANNED_BACKUP_REFERENCE = ACTIVE_CANONICAL_DATASET

STATUS_SUCCESS = "ASX_CANONICAL_PROMOTION_PLAN_COMPLETED_DRY_RUN_READY_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_CANONICAL_PROMOTION_PLAN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20L - ASX Canonical Promotion Dry Run"
NEXT_PHASE_REVIEW = "v2.20K_REVIEW - ASX Canonical Promotion Plan Review"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ROLLBACK_PLAN_CSV,
        EXECUTION_PLAN_CSV,
        RISK_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220g = read_json(V220G_JSON)
    v220h = read_json(V220H_JSON)
    v220i = read_json(V220I_JSON)
    v220j = read_json(V220J_JSON)

    v220j_summary = v220j.get("decision_summary", {})

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_rows = count_csv_rows(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_rows = count_csv_rows(ASX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_before = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_sha_before = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)

    asx_net_new_rows = asx_validated_candidate_rows - current_validated_candidate_rows
    uplift_vs_active_canonical_rows = asx_validated_candidate_rows - active_canonical_rows
    rows_above_quality_floor = asx_validated_candidate_rows - QUALITY_FLOOR_TARGET
    remaining_capacity_to_quality_ceiling = QUALITY_CEILING_TARGET - asx_validated_candidate_rows
    rows_to_aspirational_50k = ASPIRATIONAL_TARGET - asx_validated_candidate_rows

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_after = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_sha_after = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)

    checks: list[dict[str, Any]] = []
    critical_failed = 0
    warning_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed, warning_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        if severity == "warning" and not passed:
            warning_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_20g_report_exists", V220G_JSON.exists(), "critical", str(V220G_JSON))
    add_check("v2_20h_report_exists", V220H_JSON.exists(), "critical", str(V220H_JSON))
    add_check("v2_20i_report_exists", V220I_JSON.exists(), "critical", str(V220I_JSON))
    add_check("v2_20j_report_exists", V220J_JSON.exists(), "critical", str(V220J_JSON))

    add_check("v2_20g_status_expected", v220g.get("status") == EXPECTED_V220G_STATUS, "critical", str(v220g.get("status")))
    add_check("v2_20h_status_expected", v220h.get("status") == EXPECTED_V220H_STATUS, "critical", str(v220h.get("status")))
    add_check("v2_20i_status_expected", v220i.get("status") == EXPECTED_V220I_STATUS, "critical", str(v220i.get("status")))
    add_check("v2_20j_status_expected", v220j.get("status") == EXPECTED_V220J_STATUS, "critical", str(v220j.get("status")))
    add_check("v2_20j_next_phase_expected", v220j.get("recommended_next_phase") == "v2.20K - ASX Canonical Promotion Plan", "critical", str(v220j.get("recommended_next_phase")))

    add_check("v2_20j_promotion_decision_expected", v220j_summary.get("promotion_decision") == "PROMOTION_RECOMMENDED_READY_FOR_PLAN", "critical", str(v220j_summary.get("promotion_decision")))
    add_check("v2_20j_promotion_recommendation_expected", v220j_summary.get("promotion_recommendation") == "PREPARE_CANONICAL_PROMOTION_PLAN", "critical", str(v220j_summary.get("promotion_recommendation")))
    add_check("v2_20j_decision_gate_result_expected", v220j_summary.get("decision_gate_result") == "APPROVE_PREPARATION_OF_CANONICAL_PROMOTION", "critical", str(v220j_summary.get("decision_gate_result")))
    add_check("v2_20j_canonical_promotion_not_performed", bool(v220j_summary.get("canonical_promotion_performed")) is False, "critical", f"canonical_promotion_performed={v220j_summary.get('canonical_promotion_performed')}")

    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("pre_hkex_current_candidate_rows_expected", pre_hkex_current_candidate_rows == PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED, "critical", f"pre_hkex_rows={pre_hkex_current_candidate_rows}")
    add_check("current_validated_candidate_rows_expected", current_validated_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_validated_rows={current_validated_candidate_rows}")
    add_check("asx_validated_candidate_rows_expected", asx_validated_candidate_rows == ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"asx_validated_rows={asx_validated_candidate_rows}")
    add_check("asx_net_new_rows_expected", asx_net_new_rows == ASX_NET_NEW_ROWS_EXPECTED, "critical", f"asx_net_new_rows={asx_net_new_rows}")
    add_check("uplift_vs_active_canonical_expected", uplift_vs_active_canonical_rows == UPLIFT_VS_ACTIVE_CANONICAL_EXPECTED, "critical", f"uplift_vs_active_canonical={uplift_vs_active_canonical_rows}")

    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("pre_hkex_current_candidate_sha_expected", pre_hkex_current_candidate_sha_before == PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED, "critical", pre_hkex_current_candidate_sha_before)
    add_check("current_validated_candidate_sha_expected", current_validated_candidate_sha_before == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", current_validated_candidate_sha_before)
    add_check("asx_validated_candidate_sha_expected", asx_validated_candidate_sha_before == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", asx_validated_candidate_sha_before)

    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("pre_hkex_current_candidate_sha_unchanged", pre_hkex_current_candidate_sha_before == pre_hkex_current_candidate_sha_after, "critical", "pre-HKEX current candidate sha unchanged")
    add_check("current_validated_candidate_sha_unchanged", current_validated_candidate_sha_before == current_validated_candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("asx_validated_candidate_sha_unchanged", asx_validated_candidate_sha_before == asx_validated_candidate_sha_after, "critical", "ASX validated candidate sha unchanged")

    add_check("quality_floor_crossed", asx_validated_candidate_rows >= QUALITY_FLOOR_TARGET, "critical", f"asx_validated_rows={asx_validated_candidate_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", asx_validated_candidate_rows <= QUALITY_CEILING_TARGET, "critical", f"asx_validated_rows={asx_validated_candidate_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_above_quality_floor_expected", rows_above_quality_floor == ROWS_ABOVE_QUALITY_FLOOR_EXPECTED, "critical", f"rows_above_floor={rows_above_quality_floor}")
    add_check("remaining_capacity_to_quality_ceiling_expected", remaining_capacity_to_quality_ceiling == REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED, "critical", f"capacity_to_ceiling={remaining_capacity_to_quality_ceiling}")
    add_check("rows_to_aspirational_50k_expected", rows_to_aspirational_50k == ROWS_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_to_50k={rows_to_aspirational_50k}")

    add_check("planned_promotion_source_is_asx_candidate", PLANNED_PROMOTION_SOURCE == ASX_VALIDATED_CANDIDATE_DATASET, "critical", str(PLANNED_PROMOTION_SOURCE))
    add_check("planned_promotion_target_is_versioned_new_file", PLANNED_PROMOTED_CANONICAL_DATASET.name == "expanded_universe_v2_20m_asx_promoted.csv", "critical", str(PLANNED_PROMOTED_CANONICAL_DATASET))
    add_check("planned_target_does_not_exist_yet", not PLANNED_PROMOTED_CANONICAL_DATASET.exists(), "warning", f"target_exists={PLANNED_PROMOTED_CANONICAL_DATASET.exists()}")
    add_check("promotion_plan_only", True, "critical", "promotion plan only")
    add_check("no_file_copy_performed", True, "critical", "file_copy_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("canonical_promotion_not_performed", True, "critical", "canonical_promotion_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
        plan_decision = "PROMOTION_PLAN_BLOCKED_REVIEW_REQUIRED"
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
        plan_decision = "PROMOTION_PLAN_READY_FOR_DRY_RUN"

    plan_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "plan_decision": plan_decision,
        "promotion_source_dataset": str(PLANNED_PROMOTION_SOURCE),
        "promotion_source_rows": asx_validated_candidate_rows,
        "promotion_source_sha": asx_validated_candidate_sha_after,
        "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "active_canonical_rows": active_canonical_rows,
        "active_canonical_sha": active_canonical_sha_after,
        "planned_promoted_canonical_dataset": str(PLANNED_PROMOTED_CANONICAL_DATASET),
        "planned_backup_reference": str(PLANNED_BACKUP_REFERENCE),
        "current_validated_candidate_rows": current_validated_candidate_rows,
        "asx_net_new_rows_vs_current_candidate": asx_net_new_rows,
        "uplift_vs_active_canonical_rows": uplift_vs_active_canonical_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": asx_validated_candidate_rows >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": asx_validated_candidate_rows <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": rows_above_quality_floor,
        "remaining_capacity_to_quality_ceiling": remaining_capacity_to_quality_ceiling,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k": rows_to_aspirational_50k,
        "promotion_strategy": "VERSIONED_CANONICAL_FILE_FIRST_WITH_EXPLICIT_POINTER_UPDATE_LATER",
        "canonical_promotion_performed": False,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    execution_plan_rows = [
        {
            "step_order": 1,
            "phase": "v2.20L",
            "step": "dry_run_copy_plan",
            "action": "Simulate promotion from ASX validated candidate to planned promoted canonical path.",
            "input": str(PLANNED_PROMOTION_SOURCE),
            "output": str(PLANNED_PROMOTED_CANONICAL_DATASET),
            "guardrail": "Dry run only; no copy/write in v2.20L unless explicitly designed as dry-run artifact.",
        },
        {
            "step_order": 2,
            "phase": "v2.20L",
            "step": "preflight_sha_and_row_controls",
            "action": "Validate source rows/SHA, current canonical rows/SHA, schema and target non-existence.",
            "input": "v2.20G/v2.20H/v2.20I/v2.20J reports",
            "output": "promotion dry-run report",
            "guardrail": "Abort on any SHA/row mismatch.",
        },
        {
            "step_order": 3,
            "phase": "v2.20M",
            "step": "controlled_promoted_file_creation",
            "action": "Create versioned promoted canonical dataset from ASX validated candidate.",
            "input": str(PLANNED_PROMOTION_SOURCE),
            "output": str(PLANNED_PROMOTED_CANONICAL_DATASET),
            "guardrail": "Do not overwrite active v2_14e file; preserve rollback reference.",
        },
        {
            "step_order": 4,
            "phase": "v2.20N",
            "step": "post_promotion_validation",
            "action": "Validate promoted canonical file rows/SHA/schema against ASX validated candidate.",
            "input": str(PLANNED_PROMOTED_CANONICAL_DATASET),
            "output": "post-promotion validation report",
            "guardrail": "No scoring/OpenAI/broker/full59k.",
        },
        {
            "step_order": 5,
            "phase": "post-v2.20N",
            "step": "explicit_active_pointer_decision",
            "action": "Decide whether app/scripts should reference the new promoted canonical file.",
            "input": "validated promoted file",
            "output": "separate pointer/update phase if needed",
            "guardrail": "Do not silently change operational references.",
        },
    ]

    rollback_plan_rows = [
        {
            "rollback_id": "ROLLBACK_001",
            "scope": "active_canonical",
            "reference_path": str(ACTIVE_CANONICAL_DATASET),
            "reference_rows": active_canonical_rows,
            "reference_sha": active_canonical_sha_after,
            "rollback_action": "Keep current active canonical as untouched rollback source.",
            "trigger": "Any promotion mismatch, row drift, schema drift, SHA drift or downstream failure.",
        },
        {
            "rollback_id": "ROLLBACK_002",
            "scope": "validated_asx_candidate",
            "reference_path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "reference_rows": asx_validated_candidate_rows,
            "reference_sha": asx_validated_candidate_sha_after,
            "rollback_action": "Treat ASX candidate as immutable source; regenerate promoted file from this only if needed.",
            "trigger": "Promoted output does not match ASX candidate SHA/rows/schema.",
        },
        {
            "rollback_id": "ROLLBACK_003",
            "scope": "promotion_target",
            "reference_path": str(PLANNED_PROMOTED_CANONICAL_DATASET),
            "reference_rows": "",
            "reference_sha": "",
            "rollback_action": "Delete or ignore promoted versioned file if validation fails; do not alter active canonical.",
            "trigger": "Post-promotion validation fails.",
        },
    ]

    risk_register_rows = [
        {
            "risk_id": "RISK_001",
            "risk": "Accidental overwrite of active canonical dataset",
            "severity": "high",
            "mitigation": "Use versioned promoted output path; keep v2_14e unchanged; require SHA pre/post checks.",
            "status": "controlled_by_plan",
        },
        {
            "risk_id": "RISK_002",
            "risk": "Promotion source drift",
            "severity": "high",
            "mitigation": "Abort if ASX candidate SHA is not exactly 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127.",
            "status": "controlled_by_plan",
        },
        {
            "risk_id": "RISK_003",
            "risk": "Operational references still point to old canonical after promoted file creation",
            "severity": "medium",
            "mitigation": "Separate pointer/update decision phase after promoted file validation.",
            "status": "deferred_explicitly",
        },
        {
            "risk_id": "RISK_004",
            "risk": "Chasing 50k volume after 42k target achieved",
            "severity": "medium",
            "mitigation": "Freeze additional provider expansion by default; keep 50k aspirational only.",
            "status": "controlled_by_plan",
        },
        {
            "risk_id": "RISK_005",
            "risk": "Unexpected scoring or broker side effects",
            "severity": "high",
            "mitigation": "Promotion plan forbids scoring, OpenAI calls, broker calls and full59k launch.",
            "status": "controlled_by_plan",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "canonical",
            "action": "run_asx_canonical_promotion_dry_run",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Promotion plan is ready; next phase should simulate exact promotion controls before creating a promoted canonical file.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "dry run first; no canonical replacement; no scoring/OpenAI/broker/full59k",
        },
        {
            "action_order": 2,
            "action_scope": "rollback",
            "action": "verify_rollback_reference_before_execution",
            "priority": "high",
            "reason": "Active canonical v2_14e must remain available as rollback source.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "abort on active canonical SHA mismatch",
        },
        {
            "action_order": 3,
            "action_scope": "provider_expansion",
            "action": "keep_provider_expansion_frozen_by_default",
            "priority": "medium",
            "reason": "42k operational floor is achieved and 45k ceiling respected.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "50k aspirational only; full59k deprecated",
        },
    ]

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in plan_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ROLLBACK_PLAN_CSV, rollback_plan_rows, ["rollback_id", "scope", "reference_path", "reference_rows", "reference_sha", "rollback_action", "trigger"])
    write_csv(EXECUTION_PLAN_CSV, execution_plan_rows, ["step_order", "phase", "step", "action", "input", "output", "guardrail"])
    write_csv(RISK_REGISTER_CSV, risk_register_rows, ["risk_id", "risk", "severity", "mitigation", "status"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "plan_summary": plan_summary,
        "execution_plan": execution_plan_rows,
        "rollback_plan": rollback_plan_rows,
        "risk_register": risk_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "promotion_plan_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "operational_42k_floor_achieved": asx_validated_candidate_rows >= QUALITY_FLOOR_TARGET,
            "operational_45k_ceiling_respected": asx_validated_candidate_rows <= QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_current_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "closure_report_performed": False,
            "promotion_decision_gate_performed": False,
            "file_copy_performed": False,
            "file_rename_performed": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "current_validated_candidate_dataset_read": True,
            "current_validated_candidate_dataset_modified": False,
            "current_validated_candidate_sha_unchanged": current_validated_candidate_sha_before == current_validated_candidate_sha_after,
            "asx_validated_candidate_dataset_read": True,
            "asx_validated_candidate_dataset_modified": False,
            "asx_validated_candidate_sha_unchanged": asx_validated_candidate_sha_before == asx_validated_candidate_sha_after,
            "active_canonical_replaced": False,
            "canonical_promotion_performed": False,
            "planned_promoted_canonical_dataset_created": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    execution_lines = "\n".join(
        f"- Step {row['step_order']} `{row['phase']}` — {row['step']}: {row['action']}"
        for row in execution_plan_rows
    )

    rollback_lines = "\n".join(
        f"- `{row['rollback_id']}` — {row['scope']} — {row['rollback_action']}"
        for row in rollback_plan_rows
    )

    risk_lines = "\n".join(
        f"- `{row['risk_id']}` — {row['risk']} — {row['severity']} — {row['status']}"
        for row in risk_register_rows
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.20K prepares the controlled canonical promotion plan for the validated ASX candidate.

Promotion source:

`{PLANNED_PROMOTION_SOURCE}`

Planned promoted canonical dataset:

`{PLANNED_PROMOTED_CANONICAL_DATASET}`

This phase is planning only. It does **not** copy, rename, overwrite, replace canonical, update pointers, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Plan summary

- Plan decision: `{plan_decision}`
- Promotion source rows: `{asx_validated_candidate_rows}`
- Promotion source SHA256: `{asx_validated_candidate_sha_after}`
- Active canonical rows: `{active_canonical_rows}`
- Active canonical SHA256: `{active_canonical_sha_after}`
- Current validated candidate rows: `{current_validated_candidate_rows}`
- ASX net-new rows vs current candidate: `{asx_net_new_rows}`
- Uplift vs active canonical rows: `{uplift_vs_active_canonical_rows}`
- Quality floor crossed: `{asx_validated_candidate_rows >= QUALITY_FLOOR_TARGET}`
- Quality ceiling respected: `{asx_validated_candidate_rows <= QUALITY_CEILING_TARGET}`
- Rows above 42k floor: `{rows_above_quality_floor}`
- Remaining capacity to 45k ceiling: `{remaining_capacity_to_quality_ceiling}`
- Rows to 50k aspirational: `{rows_to_aspirational_50k}`
- Promotion strategy: `VERSIONED_CANONICAL_FILE_FIRST_WITH_EXPLICIT_POINTER_UPDATE_LATER`
- Canonical promotion performed: `False`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Execution plan

{execution_lines}

## Rollback plan

{rollback_lines}

## Risk register

{risk_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Promotion plan only: true
- File copy performed: false
- File rename performed: false
- Canonical dataset modified: false
- Active canonical replaced: false
- Canonical promotion performed: false
- Planned promoted canonical dataset created: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.20K ASX canonical promotion plan completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("PLAN_SUMMARY:")
    for key, value in plan_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("EXECUTION_PLAN:")
    for row in execution_plan_rows:
        print(f"- {row['step_order']}: {row['phase']} - {row['step']} - {row['action']}")
    print("")
    print("ROLLBACK_PLAN:")
    for row in rollback_plan_rows:
        print(f"- {row['rollback_id']}: {row['scope']} - {row['rollback_action']}")
    print("")
    print("RISK_REGISTER:")
    for row in risk_register_rows:
        print(f"- {row['risk_id']}: {row['risk']} [{row['severity']}] - {row['status']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
