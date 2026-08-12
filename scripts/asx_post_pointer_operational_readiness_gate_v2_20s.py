from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20S"
PHASE = "Post-Pointer Operational Readiness Gate"
PHASE_TYPE = "post-pointer-operational-readiness-gate-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PROMOTED_CANONICAL_ACTIVE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V220N_JSON = OUTPUT_DIR / "asx_promoted_canonical_validation_v2_20n.json"
V220O_JSON = OUTPUT_DIR / "asx_active_pointer_decision_gate_v2_20o.json"
V220P_JSON = OUTPUT_DIR / "asx_active_pointer_update_plan_v2_20p.json"
V220Q_JSON = OUTPUT_DIR / "asx_controlled_active_pointer_update_v2_20q.json"
V220R_JSON = OUTPUT_DIR / "asx_active_pointer_update_validation_v2_20r.json"

REPORT_JSON = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_v2_20s.json"
REPORT_MD = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_v2_20s.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_summary_v2_20s.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_checks_v2_20s.csv"
READINESS_GATE_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_readiness_v2_20s.csv"
OPERATIONAL_DECISION_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_decision_register_v2_20s.csv"
DATASET_CONTROLS_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_dataset_controls_v2_20s.csv"
POINTER_CONTROLS_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_pointer_controls_v2_20s.csv"
ROLLBACK_CONTROLS_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_rollback_controls_v2_20s.csv"
SCORING_GATE_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_scoring_gate_v2_20s.csv"
FINAL_CLOSURE_PLAN_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_final_closure_plan_v2_20s.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_next_actions_v2_20s.csv"

EXPECTED_V220N_STATUS = "ASX_PROMOTED_CANONICAL_VALIDATION_COMPLETED_42708_ROWS_PROMOTED_FILE_VALIDATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220O_STATUS = "ASX_ACTIVE_POINTER_DECISION_GATE_COMPLETED_POINTER_UPDATE_PLAN_APPROVED_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220P_STATUS = "ASX_ACTIVE_POINTER_UPDATE_PLAN_COMPLETED_POINTER_UPDATE_READY_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220Q_STATUS = "ASX_CONTROLLED_ACTIVE_POINTER_UPDATE_COMPLETED_3_FILES_UPDATED_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220R_STATUS = "ASX_ACTIVE_POINTER_UPDATE_VALIDATION_COMPLETED_3_FILES_VALIDATED_42708_ROWS_POINTERS_ACTIVE_ROLLBACK_AVAILABLE_FULL59K_DEPRECATED"

ROLLBACK_ROWS_EXPECTED = 38287
PROMOTED_ROWS_EXPECTED = 42708
ASX_VALIDATED_ROWS_EXPECTED = 42708
CURRENT_VALIDATED_ROWS_EXPECTED = 41392

ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
PROMOTED_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ASX_VALIDATED_SHA_EXPECTED = PROMOTED_SHA_EXPECTED
CURRENT_VALIDATED_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

OLD_REF_FORWARD = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
OLD_REF_BACKSLASH = "outputs\\full_universe_source_acquisition\\expanded_universe_v2_14e.csv"
NEW_REF_FORWARD = "outputs/full_universe_source_acquisition/expanded_universe_v2_20m_asx_promoted.csv"
NEW_REF_BACKSLASH = "outputs\\full_universe_source_acquisition\\expanded_universe_v2_20m_asx_promoted.csv"

CONTROLLED_POINTER_FILES = {
    "outputs/audit/documentation_canonical_dataset_path_v2_14i.json",
    "outputs/audit/eol_guard_v2_14k.json",
    "tests/test_expanded_universe_post_closure_v2_14j.py",
}

STATUS_SUCCESS = "ASX_POST_POINTER_OPERATIONAL_READINESS_GATE_COMPLETED_OPERATIONAL_BASE_READY_42708_ROWS_ROLLBACK_AVAILABLE_SCORING_NOT_AUTHORIZED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_POST_POINTER_OPERATIONAL_READINESS_GATE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20T - Final ASX Promotion Closure Report"
NEXT_PHASE_REVIEW = "v2.20S_REVIEW - Post-Pointer Operational Readiness Gate Review"


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ref_counts(content: str) -> dict[str, int]:
    old_forward = content.count(OLD_REF_FORWARD)
    old_backslash = content.count(OLD_REF_BACKSLASH)
    new_forward = content.count(NEW_REF_FORWARD)
    new_backslash = content.count(NEW_REF_BACKSLASH)

    return {
        "old_forward": old_forward,
        "old_backslash": old_backslash,
        "old_total": old_forward + old_backslash,
        "new_forward": new_forward,
        "new_backslash": new_backslash,
        "new_total": new_forward + new_backslash,
    }


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        READINESS_GATE_CSV,
        OPERATIONAL_DECISION_CSV,
        DATASET_CONTROLS_CSV,
        POINTER_CONTROLS_CSV,
        ROLLBACK_CONTROLS_CSV,
        SCORING_GATE_CSV,
        FINAL_CLOSURE_PLAN_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220n = read_json(V220N_JSON)
    v220o = read_json(V220O_JSON)
    v220p = read_json(V220P_JSON)
    v220q = read_json(V220Q_JSON)
    v220r = read_json(V220R_JSON)

    r_summary = v220r.get("validation_summary", {})

    rollback_rows = count_csv_rows(ACTIVE_CANONICAL_ROLLBACK_DATASET)
    promoted_rows = count_csv_rows(PROMOTED_CANONICAL_ACTIVE_DATASET)
    asx_rows = count_csv_rows(ASX_VALIDATED_CANDIDATE_DATASET)
    current_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)

    rollback_sha = sha256_file(ACTIVE_CANONICAL_ROLLBACK_DATASET)
    promoted_sha = sha256_file(PROMOTED_CANONICAL_ACTIVE_DATASET)
    asx_sha = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)
    current_sha = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    rollback_header = read_csv_header(ACTIVE_CANONICAL_ROLLBACK_DATASET)
    promoted_header = read_csv_header(PROMOTED_CANONICAL_ACTIVE_DATASET)
    asx_header = read_csv_header(ASX_VALIDATED_CANDIDATE_DATASET)
    current_header = read_csv_header(CURRENT_VALIDATED_CANDIDATE_DATASET)

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

    add_check("v2_20n_status_expected", v220n.get("status") == EXPECTED_V220N_STATUS, "critical", str(v220n.get("status")))
    add_check("v2_20o_status_expected", v220o.get("status") == EXPECTED_V220O_STATUS, "critical", str(v220o.get("status")))
    add_check("v2_20p_status_expected", v220p.get("status") == EXPECTED_V220P_STATUS, "critical", str(v220p.get("status")))
    add_check("v2_20q_status_expected", v220q.get("status") == EXPECTED_V220Q_STATUS, "critical", str(v220q.get("status")))
    add_check("v2_20r_status_expected", v220r.get("status") == EXPECTED_V220R_STATUS, "critical", str(v220r.get("status")))
    add_check("v2_20r_next_phase_expected", v220r.get("recommended_next_phase") == "v2.20S - Post-Pointer Operational Readiness Gate", "critical", str(v220r.get("recommended_next_phase")))

    add_check("v2_20r_validation_decision_expected", r_summary.get("validation_decision") == "ACTIVE_POINTER_UPDATE_VALIDATED_READY_FOR_OPERATIONAL_READINESS_GATE", "critical", str(r_summary.get("validation_decision")))
    add_check("v2_20r_pointer_update_validated", bool(r_summary.get("pointer_update_validated")) is True, "critical", f"pointer_update_validated={r_summary.get('pointer_update_validated')}")
    add_check("v2_20r_validated_target_files_expected", int(r_summary.get("validated_target_files", -1)) == 3, "critical", f"validated_target_files={r_summary.get('validated_target_files')}")
    add_check("v2_20r_no_old_refs_in_targets", int(r_summary.get("target_files_with_old_refs", -1)) == 0, "critical", f"target_files_with_old_refs={r_summary.get('target_files_with_old_refs')}")
    add_check("v2_20r_new_refs_in_targets", int(r_summary.get("target_files_with_new_refs", -1)) == 3, "critical", f"target_files_with_new_refs={r_summary.get('target_files_with_new_refs')}")
    add_check("v2_20r_no_target_sha_drift", int(r_summary.get("target_files_with_sha_drift", -1)) == 0, "critical", f"target_files_with_sha_drift={r_summary.get('target_files_with_sha_drift')}")
    add_check("v2_20r_historical_preserved", int(r_summary.get("historical_reference_files_changed", -1)) == 0, "critical", f"historical_changed={r_summary.get('historical_reference_files_changed')}")

    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("promoted_rows_expected", promoted_rows == PROMOTED_ROWS_EXPECTED, "critical", f"promoted_rows={promoted_rows}")
    add_check("asx_rows_expected", asx_rows == ASX_VALIDATED_ROWS_EXPECTED, "critical", f"asx_rows={asx_rows}")
    add_check("current_rows_expected", current_rows == CURRENT_VALIDATED_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")

    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("promoted_sha_expected", promoted_sha == PROMOTED_SHA_EXPECTED, "critical", promoted_sha)
    add_check("asx_sha_expected", asx_sha == ASX_VALIDATED_SHA_EXPECTED, "critical", asx_sha)
    add_check("current_sha_expected", current_sha == CURRENT_VALIDATED_SHA_EXPECTED, "critical", current_sha)

    add_check("promoted_matches_asx_rows", promoted_rows == asx_rows, "critical", f"promoted={promoted_rows};asx={asx_rows}")
    add_check("promoted_matches_asx_sha", promoted_sha == asx_sha, "critical", f"promoted={promoted_sha};asx={asx_sha}")
    add_check("promoted_schema_matches_rollback", promoted_header == rollback_header, "critical", f"promoted_columns={len(promoted_header)};rollback_columns={len(rollback_header)}")
    add_check("promoted_schema_matches_asx", promoted_header == asx_header, "critical", f"promoted_columns={len(promoted_header)};asx_columns={len(asx_header)}")
    add_check("promoted_schema_matches_current_candidate", promoted_header == current_header, "critical", f"promoted_columns={len(promoted_header)};current_columns={len(current_header)}")
    add_check("schema_column_count_expected", len(promoted_header) == 33, "critical", f"promoted_columns={len(promoted_header)}")

    add_check("quality_floor_crossed", promoted_rows >= QUALITY_FLOOR_TARGET, "critical", f"rows={promoted_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", promoted_rows <= QUALITY_CEILING_TARGET, "critical", f"rows={promoted_rows};ceiling={QUALITY_CEILING_TARGET}")

    pointer_control_rows: list[dict[str, Any]] = []
    pointer_files_validated = 0
    pointer_files_with_old_refs = 0
    pointer_files_with_new_refs = 0

    for path_str in sorted(CONTROLLED_POINTER_FILES):
        path = Path(path_str)
        exists = path.exists()
        content = read_text(path) if exists else ""
        counts = ref_counts(content)
        sha = sha256_file(path) if exists else ""

        old_refs_ok = counts["old_total"] == 0
        new_refs_ok = counts["new_total"] >= 1
        validated = exists and old_refs_ok and new_refs_ok

        if validated:
            pointer_files_validated += 1
        if counts["old_total"] > 0:
            pointer_files_with_old_refs += 1
        if counts["new_total"] > 0:
            pointer_files_with_new_refs += 1

        pointer_control_rows.append({
            "path": path_str,
            "exists": exists,
            "sha256": sha,
            "old_refs": counts["old_total"],
            "new_refs": counts["new_total"],
            "validated": validated,
            "role": "controlled_active_pointer_file",
        })

        add_check(f"pointer_file_exists::{path_str}", exists, "critical", str(path))
        add_check(f"pointer_file_no_old_refs::{path_str}", old_refs_ok, "critical", f"old_refs={counts['old_total']}")
        add_check(f"pointer_file_has_new_ref::{path_str}", new_refs_ok, "critical", f"new_refs={counts['new_total']}")
        add_check(f"pointer_file_validated::{path_str}", validated, "critical", f"validated={validated}")

    add_check("pointer_files_validated_expected", pointer_files_validated == 3, "critical", f"pointer_files_validated={pointer_files_validated}")
    add_check("pointer_files_with_old_refs_expected_zero", pointer_files_with_old_refs == 0, "critical", f"pointer_files_with_old_refs={pointer_files_with_old_refs}")
    add_check("pointer_files_with_new_refs_expected_three", pointer_files_with_new_refs == 3, "critical", f"pointer_files_with_new_refs={pointer_files_with_new_refs}")

    dataset_control_rows = [
        {
            "artifact": "promoted_canonical_operational_base",
            "path": str(PROMOTED_CANONICAL_ACTIVE_DATASET),
            "rows": promoted_rows,
            "sha256": promoted_sha,
            "expected_rows": PROMOTED_ROWS_EXPECTED,
            "expected_sha": PROMOTED_SHA_EXPECTED,
            "validated": promoted_rows == PROMOTED_ROWS_EXPECTED and promoted_sha == PROMOTED_SHA_EXPECTED,
            "role": "operational_base_candidate",
        },
        {
            "artifact": "rollback_canonical_preserved",
            "path": str(ACTIVE_CANONICAL_ROLLBACK_DATASET),
            "rows": rollback_rows,
            "sha256": rollback_sha,
            "expected_rows": ROLLBACK_ROWS_EXPECTED,
            "expected_sha": ROLLBACK_SHA_EXPECTED,
            "validated": rollback_rows == ROLLBACK_ROWS_EXPECTED and rollback_sha == ROLLBACK_SHA_EXPECTED,
            "role": "rollback_reference",
        },
        {
            "artifact": "asx_validated_source",
            "path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "rows": asx_rows,
            "sha256": asx_sha,
            "expected_rows": ASX_VALIDATED_ROWS_EXPECTED,
            "expected_sha": ASX_VALIDATED_SHA_EXPECTED,
            "validated": asx_rows == ASX_VALIDATED_ROWS_EXPECTED and asx_sha == ASX_VALIDATED_SHA_EXPECTED,
            "role": "immutable_source_reference",
        },
    ]

    readiness_gate_rows = [
        {
            "gate_id": "OP_READY_001",
            "gate": "v2_20r_pointer_validation_passed",
            "passed": bool(r_summary.get("pointer_update_validated")) is True,
            "detail": f"pointer_update_validated={r_summary.get('pointer_update_validated')}",
            "required_for_operational_base": True,
        },
        {
            "gate_id": "OP_READY_002",
            "gate": "controlled_pointer_files_validated",
            "passed": pointer_files_validated == 3,
            "detail": f"pointer_files_validated={pointer_files_validated}",
            "required_for_operational_base": True,
        },
        {
            "gate_id": "OP_READY_003",
            "gate": "no_old_refs_in_active_pointer_files",
            "passed": pointer_files_with_old_refs == 0,
            "detail": f"pointer_files_with_old_refs={pointer_files_with_old_refs}",
            "required_for_operational_base": True,
        },
        {
            "gate_id": "OP_READY_004",
            "gate": "promoted_canonical_available_and_quality_target_met",
            "passed": promoted_rows == PROMOTED_ROWS_EXPECTED and promoted_sha == PROMOTED_SHA_EXPECTED and promoted_rows >= QUALITY_FLOOR_TARGET and promoted_rows <= QUALITY_CEILING_TARGET,
            "detail": f"rows={promoted_rows};sha={promoted_sha};floor={QUALITY_FLOOR_TARGET};ceiling={QUALITY_CEILING_TARGET}",
            "required_for_operational_base": True,
        },
        {
            "gate_id": "OP_READY_005",
            "gate": "rollback_canonical_available",
            "passed": rollback_rows == ROLLBACK_ROWS_EXPECTED and rollback_sha == ROLLBACK_SHA_EXPECTED,
            "detail": f"rows={rollback_rows};sha={rollback_sha}",
            "required_for_operational_base": True,
        },
        {
            "gate_id": "OP_READY_006",
            "gate": "provider_expansion_frozen",
            "passed": True,
            "detail": "42k floor achieved; 45k ceiling respected; no new provider expansion authorized",
            "required_for_operational_base": True,
        },
        {
            "gate_id": "OP_READY_007",
            "gate": "scoring_not_authorized",
            "passed": True,
            "detail": "scoring requires separate post-closure decision",
            "required_for_operational_base": True,
        },
        {
            "gate_id": "OP_READY_008",
            "gate": "external_calls_not_authorized",
            "passed": True,
            "detail": "OpenAI=False;broker=False;full59k=False",
            "required_for_operational_base": True,
        },
    ]

    readiness_failed = sum(1 for row in readiness_gate_rows if not bool(row["passed"]))

    add_check("operational_readiness_gate_all_passed", readiness_failed == 0, "critical", f"readiness_failed={readiness_failed}")

    operational_decision_rows = [
        {
            "decision_id": "OP_READY_DECISION_001",
            "decision": "Recognize promoted canonical as operational base candidate.",
            "accepted": readiness_failed == 0,
            "reason": "Pointers validated, promoted canonical available, rollback available, quality target met.",
            "effect": "Allows final ASX closure report; does not launch scoring.",
        },
        {
            "decision_id": "OP_READY_DECISION_002",
            "decision": "Keep v2_14e as rollback reference through final closure.",
            "accepted": True,
            "reason": "Rollback canonical SHA and rows remain unchanged.",
            "effect": "Rollback remains available if final closure blocks activation.",
        },
        {
            "decision_id": "OP_READY_DECISION_003",
            "decision": "Do not continue provider expansion by default.",
            "accepted": True,
            "reason": "42k operational floor achieved and 45k quality ceiling respected.",
            "effect": "No additional provider acquisition before closure.",
        },
        {
            "decision_id": "OP_READY_DECISION_004",
            "decision": "Do not authorize scoring in v2.20S.",
            "accepted": True,
            "reason": "Scoring requires a separate explicit phase after final closure.",
            "effect": "No scoring, OpenAI or broker execution.",
        },
        {
            "decision_id": "OP_READY_DECISION_005",
            "decision": "Keep full59k deprecated/deferred.",
            "accepted": True,
            "reason": "50k remains aspirational and outside the quality-first closure path.",
            "effect": "No full59k/global renormalization launch.",
        },
    ]

    scoring_gate_rows = [
        {
            "gate_id": "SCORING_001",
            "gate": "scoring_authorized",
            "passed": False,
            "detail": "scoring is not authorized by v2.20S",
            "blocking_reason": "Requires separate post-v2.20T explicit decision.",
        },
        {
            "gate_id": "SCORING_002",
            "gate": "openai_authorized",
            "passed": False,
            "detail": "OpenAI calls are not authorized by v2.20S",
            "blocking_reason": "Requires separate explicit decision.",
        },
        {
            "gate_id": "SCORING_003",
            "gate": "broker_authorized",
            "passed": False,
            "detail": "Broker calls are not authorized by v2.20S",
            "blocking_reason": "Requires separate explicit decision.",
        },
        {
            "gate_id": "SCORING_004",
            "gate": "full59k_authorized",
            "passed": False,
            "detail": "full59k remains DEPRECATED_DEFERRED",
            "blocking_reason": "Outside quality-first closure scope.",
        },
    ]

    rollback_control_rows = [
        {
            "rollback_id": "ROLLBACK_001",
            "scope": "canonical_rollback",
            "reference_path": str(ACTIVE_CANONICAL_ROLLBACK_DATASET),
            "reference_rows": rollback_rows,
            "reference_sha": rollback_sha,
            "status": "AVAILABLE_UNCHANGED" if rollback_sha == ROLLBACK_SHA_EXPECTED else "DRIFT_DETECTED",
            "rollback_action": "Use v2_14e if final closure does not approve operational recognition.",
        },
        {
            "rollback_id": "ROLLBACK_002",
            "scope": "pointer_reversal",
            "reference_path": ";".join(sorted(CONTROLLED_POINTER_FILES)),
            "reference_rows": pointer_files_validated,
            "reference_sha": "",
            "status": "REVERSIBLE_IF_EXPLICITLY_APPROVED",
            "rollback_action": f"Reverse `{NEW_REF_FORWARD}` back to `{OLD_REF_FORWARD}` only in explicit rollback phase.",
        },
        {
            "rollback_id": "ROLLBACK_003",
            "scope": "promoted_operational_base_candidate",
            "reference_path": str(PROMOTED_CANONICAL_ACTIVE_DATASET),
            "reference_rows": promoted_rows,
            "reference_sha": promoted_sha,
            "status": "READY_FOR_FINAL_CLOSURE" if readiness_failed == 0 else "READINESS_REVIEW_REQUIRED",
            "rollback_action": "Keep available; do not delete or overwrite.",
        },
    ]

    final_closure_plan_rows = [
        {
            "closure_step": 1,
            "scope": "document_operational_base",
            "planned_action": "Record promoted canonical as operational base after pointer validation.",
            "target_phase": "v2.20T",
            "allowed_in_v220s": False,
        },
        {
            "closure_step": 2,
            "scope": "record_rollback",
            "planned_action": "Record v2_14e as rollback reference.",
            "target_phase": "v2.20T",
            "allowed_in_v220s": False,
        },
        {
            "closure_step": 3,
            "scope": "freeze_expansion",
            "planned_action": "Confirm provider expansion frozen by default.",
            "target_phase": "v2.20T",
            "allowed_in_v220s": False,
        },
        {
            "closure_step": 4,
            "scope": "scoring_decision",
            "planned_action": "Keep scoring deferred unless a separate post-closure phase is explicitly approved.",
            "target_phase": "post-v2.20T",
            "allowed_in_v220s": False,
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "final-closure",
            "action": "run_final_asx_promotion_closure_report",
            "priority": "high" if readiness_failed == 0 else "blocked",
            "reason": "Operational readiness gate passed; final closure should document the promoted base and rollback.",
            "recommended_phase": NEXT_PHASE if readiness_failed == 0 else NEXT_PHASE_REVIEW,
            "guardrails": "closure report only; no scoring/OpenAI/broker/full59k",
        },
        {
            "action_order": 2,
            "action_scope": "rollback",
            "action": "preserve_v2_14e_rollback_reference",
            "priority": "high",
            "reason": "Rollback remains required until final closure is committed and verified.",
            "recommended_phase": NEXT_PHASE if readiness_failed == 0 else NEXT_PHASE_REVIEW,
            "guardrails": "do not delete or overwrite rollback dataset",
        },
        {
            "action_order": 3,
            "action_scope": "scoring",
            "action": "keep_scoring_deferred",
            "priority": "medium",
            "reason": "Readiness gate does not authorize scoring.",
            "recommended_phase": "post-v2.20T explicit decision",
            "guardrails": "separate approval required",
        },
    ]

    add_check("readiness_gate_only", True, "critical", "post-pointer operational readiness gate only")
    add_check("file_edit_not_performed", True, "critical", "file_edit_performed=False")
    add_check("file_copy_not_performed", True, "critical", "file_copy_performed=False")
    add_check("file_rename_not_performed", True, "critical", "file_rename_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
        readiness_decision = "OPERATIONAL_READINESS_BLOCKED_REVIEW_REQUIRED"
        operational_base_ready = False
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
        readiness_decision = "PROMOTED_CANONICAL_OPERATIONAL_BASE_READY_FOR_FINAL_CLOSURE"
        operational_base_ready = True

    readiness_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "readiness_decision": readiness_decision,
        "operational_base_ready": operational_base_ready,
        "operational_base_dataset": str(PROMOTED_CANONICAL_ACTIVE_DATASET),
        "operational_base_rows": promoted_rows,
        "operational_base_sha": promoted_sha,
        "rollback_dataset": str(ACTIVE_CANONICAL_ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "controlled_pointer_files_validated": pointer_files_validated,
        "controlled_pointer_files_with_old_refs": pointer_files_with_old_refs,
        "controlled_pointer_files_with_new_refs": pointer_files_with_new_refs,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": promoted_rows >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": promoted_rows <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": promoted_rows - QUALITY_FLOOR_TARGET,
        "remaining_capacity_to_quality_ceiling": QUALITY_CEILING_TARGET - promoted_rows,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k": ASPIRATIONAL_TARGET - promoted_rows,
        "provider_expansion_frozen": True,
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in readiness_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(READINESS_GATE_CSV, readiness_gate_rows, ["gate_id", "gate", "passed", "detail", "required_for_operational_base"])
    write_csv(OPERATIONAL_DECISION_CSV, operational_decision_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(DATASET_CONTROLS_CSV, dataset_control_rows, ["artifact", "path", "rows", "sha256", "expected_rows", "expected_sha", "validated", "role"])
    write_csv(POINTER_CONTROLS_CSV, pointer_control_rows, ["path", "exists", "sha256", "old_refs", "new_refs", "validated", "role"])
    write_csv(ROLLBACK_CONTROLS_CSV, rollback_control_rows, ["rollback_id", "scope", "reference_path", "reference_rows", "reference_sha", "status", "rollback_action"])
    write_csv(SCORING_GATE_CSV, scoring_gate_rows, ["gate_id", "gate", "passed", "detail", "blocking_reason"])
    write_csv(FINAL_CLOSURE_PLAN_CSV, final_closure_plan_rows, ["closure_step", "scope", "planned_action", "target_phase", "allowed_in_v220s"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "readiness_summary": readiness_summary,
        "readiness_gate": readiness_gate_rows,
        "operational_decisions": operational_decision_rows,
        "dataset_controls": dataset_control_rows,
        "pointer_controls": pointer_control_rows,
        "rollback_controls": rollback_control_rows,
        "scoring_gate": scoring_gate_rows,
        "final_closure_plan": final_closure_plan_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "post_pointer_operational_readiness_gate_only": True,
            "selected_provider": "ASX",
            "operational_base_ready": operational_base_ready,
            "operational_base_dataset": str(PROMOTED_CANONICAL_ACTIVE_DATASET),
            "operational_base_rows": promoted_rows,
            "operational_base_sha": promoted_sha,
            "rollback_available": rollback_sha == ROLLBACK_SHA_EXPECTED,
            "rollback_dataset": str(ACTIVE_CANONICAL_ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "operational_42k_floor_achieved": promoted_rows >= QUALITY_FLOOR_TARGET,
            "operational_45k_ceiling_respected": promoted_rows <= QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "provider_expansion_frozen": True,
            "controlled_pointer_files_validated": pointer_files_validated,
            "controlled_pointer_files_with_old_refs": pointer_files_with_old_refs,
            "controlled_pointer_files_with_new_refs": pointer_files_with_new_refs,
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
            "file_edit_performed": False,
            "file_copy_performed": False,
            "file_rename_performed": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "promoted_canonical_dataset_read": True,
            "promoted_canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "active_pointer_updated_from_v2_20q": True,
            "pointer_update_validated_from_v2_20r": True,
            "scoring_authorized": False,
            "scoring_recalculated": False,
            "openai_authorized": False,
            "openai_called": False,
            "broker_authorized": False,
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

    readiness_lines = "\n".join(
        f"- `{row['gate_id']}` — {row['gate']}: {'PASS' if row['passed'] else 'FAIL'} — {row['detail']}"
        for row in readiness_gate_rows
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}` — accepted `{row['accepted']}` — {row['decision']}"
        for row in operational_decision_rows
    )

    scoring_lines = "\n".join(
        f"- `{row['gate_id']}` — {row['gate']}: authorized `{row['passed']}` — {row['blocking_reason']}"
        for row in scoring_gate_rows
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

v2.20S is the post-pointer operational readiness gate.

It recognizes whether the promoted canonical can be treated as operational-base-ready for final closure.

This phase does **not** edit files, replace canonical, copy files, rename files, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Readiness summary

- Readiness decision: `{readiness_decision}`
- Operational base ready: `{operational_base_ready}`
- Operational base dataset: `{PROMOTED_CANONICAL_ACTIVE_DATASET}`
- Operational base rows: `{promoted_rows}`
- Operational base SHA256: `{promoted_sha}`
- Rollback dataset: `{ACTIVE_CANONICAL_ROLLBACK_DATASET}`
- Rollback rows: `{rollback_rows}`
- Rollback SHA256: `{rollback_sha}`
- Controlled pointer files validated: `{pointer_files_validated}`
- Controlled pointer files with old refs: `{pointer_files_with_old_refs}`
- Controlled pointer files with new refs: `{pointer_files_with_new_refs}`
- Quality floor crossed: `{promoted_rows >= QUALITY_FLOOR_TARGET}`
- Quality ceiling respected: `{promoted_rows <= QUALITY_CEILING_TARGET}`
- Provider expansion frozen: `True`
- Scoring authorized: `False`
- OpenAI authorized: `False`
- Broker authorized: `False`
- full59k: `DEPRECATED_DEFERRED`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Readiness gate

{readiness_lines}

## Operational decisions

{decision_lines}

## Scoring gate

{scoring_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.20S ASX post-pointer operational readiness gate completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("READINESS_SUMMARY:")
    for key, value in readiness_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("READINESS_GATE:")
    for row in readiness_gate_rows:
        print(f"- {row['gate_id']}: {row['gate']} - {'PASS' if row['passed'] else 'FAIL'} - {row['detail']}")
    print("")
    print("OPERATIONAL_DECISIONS:")
    for row in operational_decision_rows:
        print(f"- {row['decision_id']}: accepted={row['accepted']} - {row['decision']}")
    print("")
    print("POINTER_CONTROLS:")
    for row in pointer_control_rows:
        print(f"- {row['path']}: validated={row['validated']} old_refs={row['old_refs']} new_refs={row['new_refs']}")
    print("")
    print("DATASET_CONTROLS:")
    for row in dataset_control_rows:
        print(f"- {row['artifact']}: rows={row['rows']} sha={row['sha256']} validated={row['validated']}")
    print("")
    print("SCORING_GATE:")
    for row in scoring_gate_rows:
        print(f"- {row['gate_id']}: {row['gate']} - authorized={row['passed']} - {row['blocking_reason']}")
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
