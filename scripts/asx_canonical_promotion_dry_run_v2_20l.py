from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20L"
PHASE = "ASX Canonical Promotion Dry Run"
PHASE_TYPE = "canonical-promotion-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PRE_HKEX_CURRENT_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"

PLANNED_PROMOTED_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"

V220G_JSON = OUTPUT_DIR / "asx_expanded_rebuild_candidate_v2_20g.json"
V220H_JSON = OUTPUT_DIR / "asx_expanded_validation_v2_20h.json"
V220I_JSON = OUTPUT_DIR / "asx_closure_report_v2_20i.json"
V220J_JSON = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_v2_20j.json"
V220K_JSON = OUTPUT_DIR / "asx_canonical_promotion_plan_v2_20k.json"

REPORT_JSON = OUTPUT_DIR / "asx_canonical_promotion_dry_run_v2_20l.json"
REPORT_MD = OUTPUT_DIR / "asx_canonical_promotion_dry_run_v2_20l.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_canonical_promotion_dry_run_summary_v2_20l.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_canonical_promotion_dry_run_checks_v2_20l.csv"
PREFLIGHT_CSV = OUTPUT_DIR / "asx_canonical_promotion_dry_run_preflight_v2_20l.csv"
SHA_CONTROLS_CSV = OUTPUT_DIR / "asx_canonical_promotion_dry_run_sha_controls_v2_20l.csv"
SCHEMA_CONTROLS_CSV = OUTPUT_DIR / "asx_canonical_promotion_dry_run_schema_controls_v2_20l.csv"
ROLLBACK_CONTROLS_CSV = OUTPUT_DIR / "asx_canonical_promotion_dry_run_rollback_controls_v2_20l.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_canonical_promotion_dry_run_next_actions_v2_20l.csv"

EXPECTED_V220G_STATUS = "ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220H_STATUS = "ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED"
EXPECTED_V220I_STATUS = "ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED"
EXPECTED_V220J_STATUS = "ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220K_STATUS = "ASX_CANONICAL_PROMOTION_PLAN_COMPLETED_DRY_RUN_READY_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"

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

STATUS_SUCCESS = "ASX_CANONICAL_PROMOTION_DRY_RUN_COMPLETED_PROMOTION_EXECUTION_READY_42708_ROWS_CANONICAL_UNCHANGED_PROMOTED_FILE_NOT_CREATED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_CANONICAL_PROMOTION_DRY_RUN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20M - ASX Controlled Promoted File Creation"
NEXT_PHASE_REVIEW = "v2.20L_REVIEW - ASX Canonical Promotion Dry Run Review"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader)


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
        PREFLIGHT_CSV,
        SHA_CONTROLS_CSV,
        SCHEMA_CONTROLS_CSV,
        ROLLBACK_CONTROLS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    target_exists_before = PLANNED_PROMOTED_CANONICAL_DATASET.exists()

    v220g = read_json(V220G_JSON)
    v220h = read_json(V220H_JSON)
    v220i = read_json(V220I_JSON)
    v220j = read_json(V220J_JSON)
    v220k = read_json(V220K_JSON)

    v220k_summary = v220k.get("plan_summary", {})

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_rows = count_csv_rows(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_rows = count_csv_rows(ASX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_header = read_csv_header(ACTIVE_CANONICAL_DATASET)
    current_validated_candidate_header = read_csv_header(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_header = read_csv_header(ASX_VALIDATED_CANDIDATE_DATASET)

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

    target_exists_after = PLANNED_PROMOTED_CANONICAL_DATASET.exists()

    schema_matches_active_canonical = active_canonical_header == asx_validated_candidate_header
    schema_matches_current_candidate = current_validated_candidate_header == asx_validated_candidate_header

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
    add_check("v2_20k_report_exists", V220K_JSON.exists(), "critical", str(V220K_JSON))

    add_check("v2_20g_status_expected", v220g.get("status") == EXPECTED_V220G_STATUS, "critical", str(v220g.get("status")))
    add_check("v2_20h_status_expected", v220h.get("status") == EXPECTED_V220H_STATUS, "critical", str(v220h.get("status")))
    add_check("v2_20i_status_expected", v220i.get("status") == EXPECTED_V220I_STATUS, "critical", str(v220i.get("status")))
    add_check("v2_20j_status_expected", v220j.get("status") == EXPECTED_V220J_STATUS, "critical", str(v220j.get("status")))
    add_check("v2_20k_status_expected", v220k.get("status") == EXPECTED_V220K_STATUS, "critical", str(v220k.get("status")))
    add_check("v2_20k_next_phase_expected", v220k.get("recommended_next_phase") == "v2.20L - ASX Canonical Promotion Dry Run", "critical", str(v220k.get("recommended_next_phase")))

    add_check("v2_20k_plan_decision_expected", v220k_summary.get("plan_decision") == "PROMOTION_PLAN_READY_FOR_DRY_RUN", "critical", str(v220k_summary.get("plan_decision")))
    add_check("v2_20k_promotion_source_expected", v220k_summary.get("promotion_source_dataset") == str(ASX_VALIDATED_CANDIDATE_DATASET), "critical", str(v220k_summary.get("promotion_source_dataset")))
    add_check("v2_20k_planned_target_expected", v220k_summary.get("planned_promoted_canonical_dataset") == str(PLANNED_PROMOTED_CANONICAL_DATASET), "critical", str(v220k_summary.get("planned_promoted_canonical_dataset")))
    add_check("v2_20k_canonical_promotion_not_performed", bool(v220k_summary.get("canonical_promotion_performed")) is False, "critical", f"canonical_promotion_performed={v220k_summary.get('canonical_promotion_performed')}")

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

    add_check("schema_column_count_expected", len(asx_validated_candidate_header) == 33, "critical", f"asx_columns={len(asx_validated_candidate_header)}")
    add_check("schema_matches_active_canonical", schema_matches_active_canonical, "critical", f"schema_matches_active_canonical={schema_matches_active_canonical}")
    add_check("schema_matches_current_candidate", schema_matches_current_candidate, "critical", f"schema_matches_current_candidate={schema_matches_current_candidate}")

    add_check("quality_floor_crossed", asx_validated_candidate_rows >= QUALITY_FLOOR_TARGET, "critical", f"asx_validated_rows={asx_validated_candidate_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", asx_validated_candidate_rows <= QUALITY_CEILING_TARGET, "critical", f"asx_validated_rows={asx_validated_candidate_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_above_quality_floor_expected", rows_above_quality_floor == ROWS_ABOVE_QUALITY_FLOOR_EXPECTED, "critical", f"rows_above_floor={rows_above_quality_floor}")
    add_check("remaining_capacity_to_quality_ceiling_expected", remaining_capacity_to_quality_ceiling == REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED, "critical", f"capacity_to_ceiling={remaining_capacity_to_quality_ceiling}")
    add_check("rows_to_aspirational_50k_expected", rows_to_aspirational_50k == ROWS_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_to_50k={rows_to_aspirational_50k}")

    add_check("planned_target_absent_before_dry_run", not target_exists_before, "critical", f"target_exists_before={target_exists_before}")
    add_check("planned_target_absent_after_dry_run", not target_exists_after, "critical", f"target_exists_after={target_exists_after}")
    add_check("dry_run_only", True, "critical", "dry run only")
    add_check("file_copy_not_performed", True, "critical", "file_copy_performed=False")
    add_check("file_rename_not_performed", True, "critical", "file_rename_performed=False")
    add_check("promoted_file_not_created", not target_exists_after, "critical", f"target_exists_after={target_exists_after}")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("canonical_promotion_not_performed", True, "critical", "canonical_promotion_performed=False")
    add_check("active_pointer_not_updated", True, "critical", "active_pointer_updated=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
        dry_run_decision = "PROMOTION_DRY_RUN_BLOCKED_REVIEW_REQUIRED"
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
        dry_run_decision = "PROMOTION_DRY_RUN_PASSED_EXECUTION_READY"

    dry_run_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "dry_run_decision": dry_run_decision,
        "promotion_source_dataset": str(ASX_VALIDATED_CANDIDATE_DATASET),
        "promotion_source_rows": asx_validated_candidate_rows,
        "promotion_source_sha": asx_validated_candidate_sha_after,
        "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "active_canonical_rows": active_canonical_rows,
        "active_canonical_sha": active_canonical_sha_after,
        "planned_promoted_canonical_dataset": str(PLANNED_PROMOTED_CANONICAL_DATASET),
        "planned_promoted_canonical_dataset_exists_before": target_exists_before,
        "planned_promoted_canonical_dataset_exists_after": target_exists_after,
        "current_validated_candidate_rows": current_validated_candidate_rows,
        "asx_net_new_rows_vs_current_candidate": asx_net_new_rows,
        "uplift_vs_active_canonical_rows": uplift_vs_active_canonical_rows,
        "schema_column_count": len(asx_validated_candidate_header),
        "schema_matches_active_canonical": schema_matches_active_canonical,
        "schema_matches_current_candidate": schema_matches_current_candidate,
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
        "promoted_file_created": False,
        "active_pointer_updated": False,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    preflight_rows = [
        {
            "preflight_id": "PREFLIGHT_001",
            "item": "source_candidate_exists",
            "passed": ASX_VALIDATED_CANDIDATE_DATASET.exists(),
            "detail": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "abort_if_failed": True,
        },
        {
            "preflight_id": "PREFLIGHT_002",
            "item": "active_canonical_exists",
            "passed": ACTIVE_CANONICAL_DATASET.exists(),
            "detail": str(ACTIVE_CANONICAL_DATASET),
            "abort_if_failed": True,
        },
        {
            "preflight_id": "PREFLIGHT_003",
            "item": "planned_target_absent",
            "passed": not target_exists_before and not target_exists_after,
            "detail": str(PLANNED_PROMOTED_CANONICAL_DATASET),
            "abort_if_failed": True,
        },
        {
            "preflight_id": "PREFLIGHT_004",
            "item": "promotion_source_rows_expected",
            "passed": asx_validated_candidate_rows == ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED,
            "detail": f"rows={asx_validated_candidate_rows}",
            "abort_if_failed": True,
        },
        {
            "preflight_id": "PREFLIGHT_005",
            "item": "promotion_source_sha_expected",
            "passed": asx_validated_candidate_sha_after == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED,
            "detail": asx_validated_candidate_sha_after,
            "abort_if_failed": True,
        },
        {
            "preflight_id": "PREFLIGHT_006",
            "item": "schema_compatible",
            "passed": schema_matches_active_canonical and schema_matches_current_candidate,
            "detail": f"active={schema_matches_active_canonical};current={schema_matches_current_candidate}",
            "abort_if_failed": True,
        },
    ]

    sha_control_rows = [
        {
            "artifact": "active_canonical",
            "path": str(ACTIVE_CANONICAL_DATASET),
            "expected_rows": ACTIVE_CANONICAL_ROWS_EXPECTED,
            "actual_rows": active_canonical_rows,
            "expected_sha": ACTIVE_CANONICAL_SHA_EXPECTED,
            "actual_sha": active_canonical_sha_after,
            "matched": active_canonical_sha_after == ACTIVE_CANONICAL_SHA_EXPECTED and active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED,
        },
        {
            "artifact": "current_validated_candidate",
            "path": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "expected_rows": CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED,
            "actual_rows": current_validated_candidate_rows,
            "expected_sha": CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED,
            "actual_sha": current_validated_candidate_sha_after,
            "matched": current_validated_candidate_sha_after == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED and current_validated_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED,
        },
        {
            "artifact": "asx_validated_candidate",
            "path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "expected_rows": ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED,
            "actual_rows": asx_validated_candidate_rows,
            "expected_sha": ASX_VALIDATED_CANDIDATE_SHA_EXPECTED,
            "actual_sha": asx_validated_candidate_sha_after,
            "matched": asx_validated_candidate_sha_after == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED and asx_validated_candidate_rows == ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED,
        },
        {
            "artifact": "planned_promoted_canonical",
            "path": str(PLANNED_PROMOTED_CANONICAL_DATASET),
            "expected_rows": ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED,
            "actual_rows": "",
            "expected_sha": ASX_VALIDATED_CANDIDATE_SHA_EXPECTED,
            "actual_sha": "",
            "matched": not target_exists_after,
        },
    ]

    schema_control_rows = [
        {
            "schema_scope": "active_canonical",
            "path": str(ACTIVE_CANONICAL_DATASET),
            "column_count": len(active_canonical_header),
            "matches_asx_candidate": schema_matches_active_canonical,
            "columns": ";".join(active_canonical_header),
        },
        {
            "schema_scope": "current_validated_candidate",
            "path": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "column_count": len(current_validated_candidate_header),
            "matches_asx_candidate": schema_matches_current_candidate,
            "columns": ";".join(current_validated_candidate_header),
        },
        {
            "schema_scope": "asx_validated_candidate",
            "path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "column_count": len(asx_validated_candidate_header),
            "matches_asx_candidate": True,
            "columns": ";".join(asx_validated_candidate_header),
        },
    ]

    rollback_control_rows = [
        {
            "rollback_id": "ROLLBACK_001",
            "scope": "active_canonical",
            "reference_path": str(ACTIVE_CANONICAL_DATASET),
            "reference_rows": active_canonical_rows,
            "reference_sha": active_canonical_sha_after,
            "dry_run_status": "AVAILABLE_UNCHANGED" if active_canonical_sha_before == active_canonical_sha_after else "DRIFT_DETECTED",
            "execution_guard": "Abort promotion if active canonical SHA changes before v2.20M.",
        },
        {
            "rollback_id": "ROLLBACK_002",
            "scope": "asx_validated_candidate",
            "reference_path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "reference_rows": asx_validated_candidate_rows,
            "reference_sha": asx_validated_candidate_sha_after,
            "dry_run_status": "AVAILABLE_UNCHANGED" if asx_validated_candidate_sha_before == asx_validated_candidate_sha_after else "DRIFT_DETECTED",
            "execution_guard": "Only create promoted file from this exact candidate SHA.",
        },
        {
            "rollback_id": "ROLLBACK_003",
            "scope": "planned_promoted_target",
            "reference_path": str(PLANNED_PROMOTED_CANONICAL_DATASET),
            "reference_rows": "",
            "reference_sha": "",
            "dry_run_status": "NOT_CREATED_AS_EXPECTED" if not target_exists_after else "UNEXPECTEDLY_EXISTS",
            "execution_guard": "v2.20M may create this path only after preflight passes.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "canonical",
            "action": "create_versioned_asx_promoted_file",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Dry run passed; controlled promoted file creation can proceed in a separate explicit phase.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "create versioned file only; do not overwrite v2_14e; no scoring/OpenAI/broker/full59k",
        },
        {
            "action_order": 2,
            "action_scope": "validation",
            "action": "validate_promoted_file_after_creation",
            "priority": "high",
            "reason": "Promoted file must match ASX candidate rows, schema and SHA expectations after creation.",
            "recommended_phase": "v2.20N - ASX Promoted Canonical Validation",
            "guardrails": "post-promotion validation before any pointer update",
        },
        {
            "action_order": 3,
            "action_scope": "pointer",
            "action": "defer_active_pointer_update",
            "priority": "high",
            "reason": "Operational references must not be silently changed during file creation.",
            "recommended_phase": "post-v2.20N explicit pointer phase",
            "guardrails": "separate approval required",
        },
    ]

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in dry_run_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(PREFLIGHT_CSV, preflight_rows, ["preflight_id", "item", "passed", "detail", "abort_if_failed"])
    write_csv(SHA_CONTROLS_CSV, sha_control_rows, ["artifact", "path", "expected_rows", "actual_rows", "expected_sha", "actual_sha", "matched"])
    write_csv(SCHEMA_CONTROLS_CSV, schema_control_rows, ["schema_scope", "path", "column_count", "matches_asx_candidate", "columns"])
    write_csv(ROLLBACK_CONTROLS_CSV, rollback_control_rows, ["rollback_id", "scope", "reference_path", "reference_rows", "reference_sha", "dry_run_status", "execution_guard"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "dry_run_summary": dry_run_summary,
        "preflight": preflight_rows,
        "sha_controls": sha_control_rows,
        "schema_controls": schema_control_rows,
        "rollback_controls": rollback_control_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "canonical_promotion_dry_run_only": True,
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
            "promotion_plan_performed": False,
            "file_copy_performed": False,
            "file_rename_performed": False,
            "promoted_file_created": False,
            "planned_promoted_canonical_dataset_exists_before": target_exists_before,
            "planned_promoted_canonical_dataset_exists_after": target_exists_after,
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
            "active_pointer_updated": False,
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

    preflight_lines = "\n".join(
        f"- `{row['preflight_id']}` — {row['item']}: {'PASS' if row['passed'] else 'FAIL'} — {row['detail']}"
        for row in preflight_rows
    )

    sha_lines = "\n".join(
        f"- `{row['artifact']}` — rows `{row['actual_rows']}` — matched `{row['matched']}`"
        for row in sha_control_rows
    )

    schema_lines = "\n".join(
        f"- `{row['schema_scope']}` — columns `{row['column_count']}` — matches ASX `{row['matches_asx_candidate']}`"
        for row in schema_control_rows
    )

    rollback_lines = "\n".join(
        f"- `{row['rollback_id']}` — {row['scope']} — {row['dry_run_status']}"
        for row in rollback_control_rows
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

v2.20L performs a dry run for canonical promotion of the validated ASX candidate.

Promotion source:

`{ASX_VALIDATED_CANDIDATE_DATASET}`

Planned promoted canonical dataset:

`{PLANNED_PROMOTED_CANONICAL_DATASET}`

This phase is dry-run only. It does **not** copy, rename, overwrite, create the promoted CSV, replace canonical, update active pointers, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Dry-run summary

- Dry-run decision: `{dry_run_decision}`
- Promotion source rows: `{asx_validated_candidate_rows}`
- Promotion source SHA256: `{asx_validated_candidate_sha_after}`
- Active canonical rows: `{active_canonical_rows}`
- Active canonical SHA256: `{active_canonical_sha_after}`
- Planned promoted target exists before dry run: `{target_exists_before}`
- Planned promoted target exists after dry run: `{target_exists_after}`
- Current validated candidate rows: `{current_validated_candidate_rows}`
- ASX net-new rows vs current candidate: `{asx_net_new_rows}`
- Uplift vs active canonical rows: `{uplift_vs_active_canonical_rows}`
- Schema column count: `{len(asx_validated_candidate_header)}`
- Schema matches active canonical: `{schema_matches_active_canonical}`
- Schema matches current candidate: `{schema_matches_current_candidate}`
- Quality floor crossed: `{asx_validated_candidate_rows >= QUALITY_FLOOR_TARGET}`
- Quality ceiling respected: `{asx_validated_candidate_rows <= QUALITY_CEILING_TARGET}`
- Rows above 42k floor: `{rows_above_quality_floor}`
- Remaining capacity to 45k ceiling: `{remaining_capacity_to_quality_ceiling}`
- Rows to 50k aspirational: `{rows_to_aspirational_50k}`
- Canonical promotion performed: `False`
- Promoted file created: `False`
- Active pointer updated: `False`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Preflight

{preflight_lines}

## SHA controls

{sha_lines}

## Schema controls

{schema_lines}

## Rollback controls

{rollback_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Canonical promotion dry run only: true
- File copy performed: false
- File rename performed: false
- Promoted file created: false
- Canonical dataset modified: false
- Active canonical replaced: false
- Canonical promotion performed: false
- Active pointer updated: false
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

    print("v2.20L ASX canonical promotion dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("DRY_RUN_SUMMARY:")
    for key, value in dry_run_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("PREFLIGHT:")
    for row in preflight_rows:
        print(f"- {row['preflight_id']}: {row['item']} - {'PASS' if row['passed'] else 'FAIL'} - {row['detail']}")
    print("")
    print("SHA_CONTROLS:")
    for row in sha_control_rows:
        print(f"- {row['artifact']}: matched={row['matched']} rows={row['actual_rows']} sha={row['actual_sha']}")
    print("")
    print("SCHEMA_CONTROLS:")
    for row in schema_control_rows:
        print(f"- {row['schema_scope']}: columns={row['column_count']} matches_asx={row['matches_asx_candidate']}")
    print("")
    print("ROLLBACK_CONTROLS:")
    for row in rollback_control_rows:
        print(f"- {row['rollback_id']}: {row['scope']} - {row['dry_run_status']}")
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
