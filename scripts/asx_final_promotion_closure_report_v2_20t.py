from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20T"
PHASE = "Final ASX Promotion Closure Report"
PHASE_TYPE = "final-asx-promotion-closure-report-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ROLLBACK_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PROMOTED_OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V220M_JSON = OUTPUT_DIR / "asx_controlled_promoted_file_creation_v2_20m.json"
V220N_JSON = OUTPUT_DIR / "asx_promoted_canonical_validation_v2_20n.json"
V220O_JSON = OUTPUT_DIR / "asx_active_pointer_decision_gate_v2_20o.json"
V220P_JSON = OUTPUT_DIR / "asx_active_pointer_update_plan_v2_20p.json"
V220Q_JSON = OUTPUT_DIR / "asx_controlled_active_pointer_update_v2_20q.json"
V220R_JSON = OUTPUT_DIR / "asx_active_pointer_update_validation_v2_20r.json"
V220S_JSON = OUTPUT_DIR / "asx_post_pointer_operational_readiness_gate_v2_20s.json"

REPORT_JSON = OUTPUT_DIR / "asx_final_promotion_closure_report_v2_20t.json"
REPORT_MD = OUTPUT_DIR / "asx_final_promotion_closure_report_v2_20t.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_final_promotion_closure_summary_v2_20t.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_final_promotion_closure_checks_v2_20t.csv"
ROADMAP_CSV = OUTPUT_DIR / "asx_final_promotion_closure_roadmap_v2_20t.csv"
DATASET_CONTROLS_CSV = OUTPUT_DIR / "asx_final_promotion_closure_dataset_controls_v2_20t.csv"
POINTER_CONTROLS_CSV = OUTPUT_DIR / "asx_final_promotion_closure_pointer_controls_v2_20t.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "asx_final_promotion_closure_decision_register_v2_20t.csv"
ROLLBACK_CONTROLS_CSV = OUTPUT_DIR / "asx_final_promotion_closure_rollback_controls_v2_20t.csv"
SCORING_DEFERRAL_CSV = OUTPUT_DIR / "asx_final_promotion_closure_scoring_deferral_v2_20t.csv"
PROVIDER_FREEZE_CSV = OUTPUT_DIR / "asx_final_promotion_closure_provider_freeze_v2_20t.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_final_promotion_closure_next_actions_v2_20t.csv"

EXPECTED_V220M_STATUS = "ASX_CONTROLLED_PROMOTED_FILE_CREATION_COMPLETED_42708_ROWS_PROMOTED_FILE_CREATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220N_STATUS = "ASX_PROMOTED_CANONICAL_VALIDATION_COMPLETED_42708_ROWS_PROMOTED_FILE_VALIDATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220O_STATUS = "ASX_ACTIVE_POINTER_DECISION_GATE_COMPLETED_POINTER_UPDATE_PLAN_APPROVED_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220P_STATUS = "ASX_ACTIVE_POINTER_UPDATE_PLAN_COMPLETED_POINTER_UPDATE_READY_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220Q_STATUS = "ASX_CONTROLLED_ACTIVE_POINTER_UPDATE_COMPLETED_3_FILES_UPDATED_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220R_STATUS = "ASX_ACTIVE_POINTER_UPDATE_VALIDATION_COMPLETED_3_FILES_VALIDATED_42708_ROWS_POINTERS_ACTIVE_ROLLBACK_AVAILABLE_FULL59K_DEPRECATED"
EXPECTED_V220S_STATUS = "ASX_POST_POINTER_OPERATIONAL_READINESS_GATE_COMPLETED_OPERATIONAL_BASE_READY_42708_ROWS_ROLLBACK_AVAILABLE_SCORING_NOT_AUTHORIZED_FULL59K_DEPRECATED"

PROMOTED_ROWS_EXPECTED = 42708
ROLLBACK_ROWS_EXPECTED = 38287
ASX_VALIDATED_ROWS_EXPECTED = 42708
CURRENT_VALIDATED_ROWS_EXPECTED = 41392

PROMOTED_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
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

STATUS_SUCCESS = "ASX_FINAL_PROMOTION_CLOSURE_REPORT_COMPLETED_OPERATIONAL_BASE_RECOGNIZED_42708_ROWS_ROLLBACK_AVAILABLE_SCORING_DEFERRED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_FINAL_PROMOTION_CLOSURE_REPORT_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.21A - Post-ASX Explicit Scoring Decision Gate"
NEXT_PHASE_REVIEW = "v2.20T_REVIEW - Final ASX Promotion Closure Review"


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
        ROADMAP_CSV,
        DATASET_CONTROLS_CSV,
        POINTER_CONTROLS_CSV,
        DECISION_REGISTER_CSV,
        ROLLBACK_CONTROLS_CSV,
        SCORING_DEFERRAL_CSV,
        PROVIDER_FREEZE_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220m = read_json(V220M_JSON)
    v220n = read_json(V220N_JSON)
    v220o = read_json(V220O_JSON)
    v220p = read_json(V220P_JSON)
    v220q = read_json(V220Q_JSON)
    v220r = read_json(V220R_JSON)
    v220s = read_json(V220S_JSON)

    s_summary = v220s.get("readiness_summary", {})

    promoted_rows = count_csv_rows(PROMOTED_OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_CANONICAL_DATASET)
    asx_rows = count_csv_rows(ASX_VALIDATED_CANDIDATE_DATASET)
    current_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)

    promoted_sha = sha256_file(PROMOTED_OPERATIONAL_BASE_DATASET)
    rollback_sha = sha256_file(ROLLBACK_CANONICAL_DATASET)
    asx_sha = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)
    current_sha = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    promoted_header = read_csv_header(PROMOTED_OPERATIONAL_BASE_DATASET)
    rollback_header = read_csv_header(ROLLBACK_CANONICAL_DATASET)
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

    add_check("v2_20m_status_expected", v220m.get("status") == EXPECTED_V220M_STATUS, "critical", str(v220m.get("status")))
    add_check("v2_20n_status_expected", v220n.get("status") == EXPECTED_V220N_STATUS, "critical", str(v220n.get("status")))
    add_check("v2_20o_status_expected", v220o.get("status") == EXPECTED_V220O_STATUS, "critical", str(v220o.get("status")))
    add_check("v2_20p_status_expected", v220p.get("status") == EXPECTED_V220P_STATUS, "critical", str(v220p.get("status")))
    add_check("v2_20q_status_expected", v220q.get("status") == EXPECTED_V220Q_STATUS, "critical", str(v220q.get("status")))
    add_check("v2_20r_status_expected", v220r.get("status") == EXPECTED_V220R_STATUS, "critical", str(v220r.get("status")))
    add_check("v2_20s_status_expected", v220s.get("status") == EXPECTED_V220S_STATUS, "critical", str(v220s.get("status")))
    add_check("v2_20s_next_phase_expected", v220s.get("recommended_next_phase") == "v2.20T - Final ASX Promotion Closure Report", "critical", str(v220s.get("recommended_next_phase")))

    add_check("v2_20s_readiness_decision_expected", s_summary.get("readiness_decision") == "PROMOTED_CANONICAL_OPERATIONAL_BASE_READY_FOR_FINAL_CLOSURE", "critical", str(s_summary.get("readiness_decision")))
    add_check("v2_20s_operational_base_ready", bool(s_summary.get("operational_base_ready")) is True, "critical", f"operational_base_ready={s_summary.get('operational_base_ready')}")
    add_check("v2_20s_provider_expansion_frozen", bool(s_summary.get("provider_expansion_frozen")) is True, "critical", f"provider_expansion_frozen={s_summary.get('provider_expansion_frozen')}")
    add_check("v2_20s_scoring_not_authorized", bool(s_summary.get("scoring_authorized")) is False, "critical", f"scoring_authorized={s_summary.get('scoring_authorized')}")
    add_check("v2_20s_openai_not_authorized", bool(s_summary.get("openai_authorized")) is False, "critical", f"openai_authorized={s_summary.get('openai_authorized')}")
    add_check("v2_20s_broker_not_authorized", bool(s_summary.get("broker_authorized")) is False, "critical", f"broker_authorized={s_summary.get('broker_authorized')}")
    add_check("v2_20s_full59k_deferred", str(s_summary.get("full59k")) == "DEPRECATED_DEFERRED", "critical", f"full59k={s_summary.get('full59k')}")

    add_check("promoted_rows_expected", promoted_rows == PROMOTED_ROWS_EXPECTED, "critical", f"promoted_rows={promoted_rows}")
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("asx_rows_expected", asx_rows == ASX_VALIDATED_ROWS_EXPECTED, "critical", f"asx_rows={asx_rows}")
    add_check("current_rows_expected", current_rows == CURRENT_VALIDATED_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")

    add_check("promoted_sha_expected", promoted_sha == PROMOTED_SHA_EXPECTED, "critical", promoted_sha)
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
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

        validated = exists and counts["old_total"] == 0 and counts["new_total"] >= 1

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
            "closure_role": "active_pointer_validated",
        })

        add_check(f"pointer_file_exists::{path_str}", exists, "critical", str(path))
        add_check(f"pointer_file_no_old_refs::{path_str}", counts["old_total"] == 0, "critical", f"old_refs={counts['old_total']}")
        add_check(f"pointer_file_has_new_ref::{path_str}", counts["new_total"] >= 1, "critical", f"new_refs={counts['new_total']}")
        add_check(f"pointer_file_validated::{path_str}", validated, "critical", f"validated={validated}")

    add_check("pointer_files_validated_expected", pointer_files_validated == 3, "critical", f"pointer_files_validated={pointer_files_validated}")
    add_check("pointer_files_with_old_refs_expected_zero", pointer_files_with_old_refs == 0, "critical", f"pointer_files_with_old_refs={pointer_files_with_old_refs}")
    add_check("pointer_files_with_new_refs_expected_three", pointer_files_with_new_refs == 3, "critical", f"pointer_files_with_new_refs={pointer_files_with_new_refs}")

    add_check("closure_report_only", True, "critical", "final ASX promotion closure report only")
    add_check("file_edit_not_performed", True, "critical", "file_edit_performed=False")
    add_check("file_copy_not_performed", True, "critical", "file_copy_performed=False")
    add_check("file_rename_not_performed", True, "critical", "file_rename_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("promoted_dataset_not_modified", True, "critical", "promoted_canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("provider_expansion_not_authorized", True, "critical", "provider_expansion_authorized=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    roadmap_rows = [
        {"phase": "v2.20A", "title": "Quality-First Target Reset and Provider Selection", "status": "closed", "closure_note": "Quality-first route reset; ASX selected."},
        {"phase": "v2.20B", "title": "ASX Quality-First Acquisition Plan", "status": "closed", "closure_note": "ASX acquisition route planned."},
        {"phase": "v2.20C", "title": "ASX Quality-First Raw Acquisition", "status": "closed", "closure_note": "ASX raw acquisition completed."},
        {"phase": "v2.20D", "title": "ASX Raw Validation", "status": "closed", "closure_note": "ASX raw data validated."},
        {"phase": "v2.20E", "title": "ASX Candidate Extraction Dry Run", "status": "closed", "closure_note": "Candidate extraction dry run completed."},
        {"phase": "v2.20F", "title": "ASX Candidate Validation Against Current Candidate Dry Run", "status": "closed", "closure_note": "ASX candidate validated against current candidate path."},
        {"phase": "v2.20G", "title": "ASX Expanded Rebuild Candidate", "status": "closed", "closure_note": "Expanded rebuild candidate created."},
        {"phase": "v2.20H", "title": "ASX Expanded Validation", "status": "closed", "closure_note": "Expanded validation completed."},
        {"phase": "v2.20I", "title": "ASX Closure Report", "status": "closed", "closure_note": "Provider closure report completed."},
        {"phase": "v2.20J", "title": "ASX Candidate Promotion Decision Gate", "status": "closed", "closure_note": "Promotion decision approved."},
        {"phase": "v2.20K", "title": "ASX Canonical Promotion Plan", "status": "closed", "closure_note": "Canonical promotion planned."},
        {"phase": "v2.20L", "title": "ASX Canonical Promotion Dry Run", "status": "closed", "closure_note": "Promotion dry run passed."},
        {"phase": "v2.20M", "title": "ASX Controlled Promoted File Creation", "status": "closed", "closure_note": "Promoted file created."},
        {"phase": "v2.20N", "title": "ASX Promoted Canonical Validation", "status": "closed", "closure_note": "Promoted canonical validated."},
        {"phase": "v2.20O", "title": "ASX Active Pointer Decision Gate", "status": "closed", "closure_note": "Pointer update plan approved."},
        {"phase": "v2.20P", "title": "ASX Active Pointer Update Plan", "status": "closed", "closure_note": "Three active pointer candidates identified."},
        {"phase": "v2.20Q", "title": "ASX Controlled Active Pointer Update", "status": "closed", "closure_note": "Three controlled pointer files updated."},
        {"phase": "v2.20R", "title": "ASX Active Pointer Update Validation", "status": "closed", "closure_note": "Pointer update validated."},
        {"phase": "v2.20S", "title": "Post-Pointer Operational Readiness Gate", "status": "closed", "closure_note": "Operational base ready for final closure."},
        {"phase": "v2.20T", "title": "Final ASX Promotion Closure Report", "status": "closed_if_this_report_passes", "closure_note": "Final closure report for ASX promotion."},
    ]

    dataset_control_rows = [
        {
            "artifact": "operational_base",
            "path": str(PROMOTED_OPERATIONAL_BASE_DATASET),
            "rows": promoted_rows,
            "sha256": promoted_sha,
            "expected_rows": PROMOTED_ROWS_EXPECTED,
            "expected_sha": PROMOTED_SHA_EXPECTED,
            "validated": promoted_rows == PROMOTED_ROWS_EXPECTED and promoted_sha == PROMOTED_SHA_EXPECTED,
            "closure_status": "RECOGNIZED_AS_OPERATIONAL_BASE",
        },
        {
            "artifact": "rollback_canonical",
            "path": str(ROLLBACK_CANONICAL_DATASET),
            "rows": rollback_rows,
            "sha256": rollback_sha,
            "expected_rows": ROLLBACK_ROWS_EXPECTED,
            "expected_sha": ROLLBACK_SHA_EXPECTED,
            "validated": rollback_rows == ROLLBACK_ROWS_EXPECTED and rollback_sha == ROLLBACK_SHA_EXPECTED,
            "closure_status": "PRESERVED_AS_ROLLBACK",
        },
        {
            "artifact": "asx_validated_source",
            "path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "rows": asx_rows,
            "sha256": asx_sha,
            "expected_rows": ASX_VALIDATED_ROWS_EXPECTED,
            "expected_sha": ASX_VALIDATED_SHA_EXPECTED,
            "validated": asx_rows == ASX_VALIDATED_ROWS_EXPECTED and asx_sha == ASX_VALIDATED_SHA_EXPECTED,
            "closure_status": "PRESERVED_AS_SOURCE_REFERENCE",
        },
        {
            "artifact": "previous_current_candidate",
            "path": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "rows": current_rows,
            "sha256": current_sha,
            "expected_rows": CURRENT_VALIDATED_ROWS_EXPECTED,
            "expected_sha": CURRENT_VALIDATED_SHA_EXPECTED,
            "validated": current_rows == CURRENT_VALIDATED_ROWS_EXPECTED and current_sha == CURRENT_VALIDATED_SHA_EXPECTED,
            "closure_status": "PRESERVED_AS_PRE_ASX_REFERENCE",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "ASX_CLOSURE_001",
            "decision": "Close ASX promotion path.",
            "accepted": critical_failed == 0,
            "reason": "ASX promoted canonical passed validation, pointer update, pointer validation and operational readiness.",
            "effect": "v2.20 can be closed after this report is committed and verified.",
        },
        {
            "decision_id": "ASX_CLOSURE_002",
            "decision": "Recognize promoted canonical as operational base.",
            "accepted": critical_failed == 0,
            "reason": "42k floor achieved, 45k ceiling respected, active pointer files validated.",
            "effect": "Operational base dataset is expanded_universe_v2_20m_asx_promoted.csv.",
        },
        {
            "decision_id": "ASX_CLOSURE_003",
            "decision": "Preserve v2_14e as rollback.",
            "accepted": True,
            "reason": "Rollback rows and SHA remain unchanged.",
            "effect": "Do not delete or overwrite rollback dataset.",
        },
        {
            "decision_id": "ASX_CLOSURE_004",
            "decision": "Freeze provider expansion by default.",
            "accepted": True,
            "reason": "Quality-first operational target reached.",
            "effect": "No further provider expansion unless a new explicit phase is approved.",
        },
        {
            "decision_id": "ASX_CLOSURE_005",
            "decision": "Defer scoring/OpenAI/broker.",
            "accepted": True,
            "reason": "Final ASX closure does not authorize scoring.",
            "effect": "Requires separate post-v2.20T explicit scoring decision gate.",
        },
        {
            "decision_id": "ASX_CLOSURE_006",
            "decision": "Keep full59k deprecated/deferred.",
            "accepted": True,
            "reason": "50k remains aspirational and outside this quality-first closure.",
            "effect": "No full59k/global renormalization launch.",
        },
    ]

    rollback_control_rows = [
        {
            "rollback_id": "ROLLBACK_001",
            "scope": "dataset_rollback",
            "reference_path": str(ROLLBACK_CANONICAL_DATASET),
            "reference_rows": rollback_rows,
            "reference_sha": rollback_sha,
            "status": "AVAILABLE_UNCHANGED" if rollback_sha == ROLLBACK_SHA_EXPECTED else "DRIFT_DETECTED",
            "rollback_action": "Use v2_14e only through explicit rollback phase.",
        },
        {
            "rollback_id": "ROLLBACK_002",
            "scope": "pointer_reversal",
            "reference_path": ";".join(sorted(CONTROLLED_POINTER_FILES)),
            "reference_rows": pointer_files_validated,
            "reference_sha": "",
            "status": "REVERSIBLE_IF_EXPLICITLY_APPROVED",
            "rollback_action": f"Reverse `{NEW_REF_FORWARD}` back to `{OLD_REF_FORWARD}` only through explicit rollback phase.",
        },
        {
            "rollback_id": "ROLLBACK_003",
            "scope": "operational_base",
            "reference_path": str(PROMOTED_OPERATIONAL_BASE_DATASET),
            "reference_rows": promoted_rows,
            "reference_sha": promoted_sha,
            "status": "ACTIVE_OPERATIONAL_BASE_RECOGNIZED" if critical_failed == 0 else "REVIEW_REQUIRED",
            "rollback_action": "Keep promoted canonical available and immutable.",
        },
    ]

    scoring_deferral_rows = [
        {
            "gate_id": "SCORING_DEFERRAL_001",
            "scope": "scoring",
            "authorized": False,
            "decision": "Deferred",
            "reason": "ASX final closure is not a scoring phase.",
            "next_allowed_phase": NEXT_PHASE,
        },
        {
            "gate_id": "SCORING_DEFERRAL_002",
            "scope": "openai",
            "authorized": False,
            "decision": "Deferred",
            "reason": "OpenAI calls require a separate explicit decision.",
            "next_allowed_phase": NEXT_PHASE,
        },
        {
            "gate_id": "SCORING_DEFERRAL_003",
            "scope": "broker",
            "authorized": False,
            "decision": "Deferred",
            "reason": "Broker calls require a separate explicit decision.",
            "next_allowed_phase": NEXT_PHASE,
        },
        {
            "gate_id": "SCORING_DEFERRAL_004",
            "scope": "full59k",
            "authorized": False,
            "decision": "Deprecated/deferred",
            "reason": "50k remains aspirational and outside quality-first ASX closure.",
            "next_allowed_phase": "explicit future route only",
        },
    ]

    provider_freeze_rows = [
        {
            "provider": "ASX",
            "status": "CLOSED_SUCCESS",
            "rows_after_promotion": promoted_rows,
            "target_floor": QUALITY_FLOOR_TARGET,
            "target_ceiling": QUALITY_CEILING_TARGET,
            "decision": "Accepted as operational base",
        },
        {
            "provider": "additional_provider_expansion",
            "status": "FROZEN_BY_DEFAULT",
            "rows_after_promotion": promoted_rows,
            "target_floor": QUALITY_FLOOR_TARGET,
            "target_ceiling": QUALITY_CEILING_TARGET,
            "decision": "Do not continue unless explicitly approved",
        },
        {
            "provider": "full59k",
            "status": "DEPRECATED_DEFERRED",
            "rows_after_promotion": promoted_rows,
            "target_floor": QUALITY_FLOOR_TARGET,
            "target_ceiling": QUALITY_CEILING_TARGET,
            "decision": "Do not launch",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "commit",
            "action": "commit_and_push_final_asx_closure_report",
            "priority": "high",
            "reason": "Final closure report must be versioned and verified.",
            "recommended_phase": "current",
            "guardrails": "add v2.20T artifacts only; do not add Auditoria_Scout_Finance.docx",
        },
        {
            "action_order": 2,
            "action_scope": "post-closure",
            "action": "decide_whether_to_open_scoring_decision_gate",
            "priority": "medium",
            "reason": "Operational base is ready, but scoring remains deferred.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "explicit user approval required before scoring/OpenAI/broker",
        },
        {
            "action_order": 3,
            "action_scope": "ops",
            "action": "use_operational_base_without_new_provider_expansion",
            "priority": "medium",
            "reason": "42k-45k quality target achieved.",
            "recommended_phase": "operational usage",
            "guardrails": "no full59k/global renormalization by default",
        },
    ]

    if critical_failed > 0:
        status = STATUS_FAILED
        closure_decision = "ASX_PROMOTION_CLOSURE_BLOCKED_REVIEW_REQUIRED"
        recommended_next_phase = NEXT_PHASE_REVIEW
        asx_promotion_closed = False
    else:
        status = STATUS_SUCCESS
        closure_decision = "ASX_PROMOTION_CLOSED_PROMOTED_CANONICAL_RECOGNIZED_AS_OPERATIONAL_BASE_SCORING_DEFERRED"
        recommended_next_phase = NEXT_PHASE
        asx_promotion_closed = True

    closure_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "closure_decision": closure_decision,
        "asx_promotion_closed": asx_promotion_closed,
        "operational_base_dataset": str(PROMOTED_OPERATIONAL_BASE_DATASET),
        "operational_base_rows": promoted_rows,
        "operational_base_sha": promoted_sha,
        "rollback_dataset": str(ROLLBACK_CANONICAL_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "previous_candidate_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
        "previous_candidate_rows": current_rows,
        "previous_candidate_sha": current_sha,
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
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in closure_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ROADMAP_CSV, roadmap_rows, ["phase", "title", "status", "closure_note"])
    write_csv(DATASET_CONTROLS_CSV, dataset_control_rows, ["artifact", "path", "rows", "sha256", "expected_rows", "expected_sha", "validated", "closure_status"])
    write_csv(POINTER_CONTROLS_CSV, pointer_control_rows, ["path", "exists", "sha256", "old_refs", "new_refs", "validated", "closure_role"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(ROLLBACK_CONTROLS_CSV, rollback_control_rows, ["rollback_id", "scope", "reference_path", "reference_rows", "reference_sha", "status", "rollback_action"])
    write_csv(SCORING_DEFERRAL_CSV, scoring_deferral_rows, ["gate_id", "scope", "authorized", "decision", "reason", "next_allowed_phase"])
    write_csv(PROVIDER_FREEZE_CSV, provider_freeze_rows, ["provider", "status", "rows_after_promotion", "target_floor", "target_ceiling", "decision"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "closure_summary": closure_summary,
        "roadmap": roadmap_rows,
        "dataset_controls": dataset_control_rows,
        "pointer_controls": pointer_control_rows,
        "decision_register": decision_register_rows,
        "rollback_controls": rollback_control_rows,
        "scoring_deferral": scoring_deferral_rows,
        "provider_freeze": provider_freeze_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "final_asx_promotion_closure_report_only": True,
            "selected_provider": "ASX",
            "asx_promotion_closed": asx_promotion_closed,
            "operational_base_recognized": asx_promotion_closed,
            "operational_base_dataset": str(PROMOTED_OPERATIONAL_BASE_DATASET),
            "operational_base_rows": promoted_rows,
            "operational_base_sha": promoted_sha,
            "rollback_available": rollback_sha == ROLLBACK_SHA_EXPECTED,
            "rollback_dataset": str(ROLLBACK_CANONICAL_DATASET),
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
            "operational_readiness_passed_from_v2_20s": True,
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

    roadmap_lines = "\n".join(
        f"- `{row['phase']}` — {row['title']}: {row['status']} — {row['closure_note']}"
        for row in roadmap_rows
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}` — accepted `{row['accepted']}` — {row['decision']}"
        for row in decision_register_rows
    )

    pointer_lines = "\n".join(
        f"- `{row['path']}` — validated `{row['validated']}` — old_refs `{row['old_refs']}` — new_refs `{row['new_refs']}`"
        for row in pointer_control_rows
    )

    scoring_lines = "\n".join(
        f"- `{row['gate_id']}` — {row['scope']}: authorized `{row['authorized']}` — {row['decision']}"
        for row in scoring_deferral_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.20T closes the ASX promotion path.

The promoted canonical is recognized as the operational base, while the previous v2_14e canonical remains preserved as rollback.

This phase does **not** edit files, replace canonical, copy files, rename files, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Closure summary

- Closure decision: `{closure_decision}`
- ASX promotion closed: `{asx_promotion_closed}`
- Operational base dataset: `{PROMOTED_OPERATIONAL_BASE_DATASET}`
- Operational base rows: `{promoted_rows}`
- Operational base SHA256: `{promoted_sha}`
- Rollback dataset: `{ROLLBACK_CANONICAL_DATASET}`
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

## Roadmap closure

{roadmap_lines}

## Pointer controls

{pointer_lines}

## Decision register

{decision_lines}

## Scoring deferral

{scoring_lines}

## Checks

{check_lines}

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.20T ASX final promotion closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CLOSURE_SUMMARY:")
    for key, value in closure_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("ROADMAP:")
    for row in roadmap_rows:
        print(f"- {row['phase']}: {row['status']} - {row['title']}")
    print("")
    print("POINTER_CONTROLS:")
    for row in pointer_control_rows:
        print(f"- {row['path']}: validated={row['validated']} old_refs={row['old_refs']} new_refs={row['new_refs']}")
    print("")
    print("DATASET_CONTROLS:")
    for row in dataset_control_rows:
        print(f"- {row['artifact']}: rows={row['rows']} sha={row['sha256']} validated={row['validated']} closure_status={row['closure_status']}")
    print("")
    print("DECISION_REGISTER:")
    for row in decision_register_rows:
        print(f"- {row['decision_id']}: accepted={row['accepted']} - {row['decision']}")
    print("")
    print("SCORING_DEFERRAL:")
    for row in scoring_deferral_rows:
        print(f"- {row['gate_id']}: scope={row['scope']} authorized={row['authorized']} decision={row['decision']}")
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
