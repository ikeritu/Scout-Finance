from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20R"
PHASE = "ASX Active Pointer Update Validation"
PHASE_TYPE = "active-pointer-update-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PROMOTED_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"

V220M_JSON = OUTPUT_DIR / "asx_controlled_promoted_file_creation_v2_20m.json"
V220N_JSON = OUTPUT_DIR / "asx_promoted_canonical_validation_v2_20n.json"
V220O_JSON = OUTPUT_DIR / "asx_active_pointer_decision_gate_v2_20o.json"
V220P_JSON = OUTPUT_DIR / "asx_active_pointer_update_plan_v2_20p.json"
V220Q_JSON = OUTPUT_DIR / "asx_controlled_active_pointer_update_v2_20q.json"

REPORT_JSON = OUTPUT_DIR / "asx_active_pointer_update_validation_v2_20r.json"
REPORT_MD = OUTPUT_DIR / "asx_active_pointer_update_validation_v2_20r.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_active_pointer_update_validation_summary_v2_20r.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_active_pointer_update_validation_checks_v2_20r.csv"
TARGET_FILE_VALIDATION_CSV = OUTPUT_DIR / "asx_active_pointer_update_validation_target_files_v2_20r.csv"
HISTORICAL_PRESERVATION_CSV = OUTPUT_DIR / "asx_active_pointer_update_validation_historical_preservation_v2_20r.csv"
DATASET_CONTROLS_CSV = OUTPUT_DIR / "asx_active_pointer_update_validation_dataset_controls_v2_20r.csv"
ROLLBACK_CONTROLS_CSV = OUTPUT_DIR / "asx_active_pointer_update_validation_rollback_controls_v2_20r.csv"
READINESS_GATE_CSV = OUTPUT_DIR / "asx_active_pointer_update_validation_readiness_gate_v2_20r.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_active_pointer_update_validation_next_actions_v2_20r.csv"

EXPECTED_V220M_STATUS = "ASX_CONTROLLED_PROMOTED_FILE_CREATION_COMPLETED_42708_ROWS_PROMOTED_FILE_CREATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220N_STATUS = "ASX_PROMOTED_CANONICAL_VALIDATION_COMPLETED_42708_ROWS_PROMOTED_FILE_VALIDATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220O_STATUS = "ASX_ACTIVE_POINTER_DECISION_GATE_COMPLETED_POINTER_UPDATE_PLAN_APPROVED_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220P_STATUS = "ASX_ACTIVE_POINTER_UPDATE_PLAN_COMPLETED_POINTER_UPDATE_READY_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220Q_STATUS = "ASX_CONTROLLED_ACTIVE_POINTER_UPDATE_COMPLETED_3_FILES_UPDATED_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
PROMOTED_CANONICAL_ROWS_EXPECTED = 42708
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392
ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED = 42708

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
PROMOTED_CANONICAL_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"
ASX_VALIDATED_CANDIDATE_SHA_EXPECTED = PROMOTED_CANONICAL_SHA_EXPECTED

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

OLD_REF_FORWARD = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
OLD_REF_BACKSLASH = "outputs\\full_universe_source_acquisition\\expanded_universe_v2_14e.csv"
NEW_REF_FORWARD = "outputs/full_universe_source_acquisition/expanded_universe_v2_20m_asx_promoted.csv"
NEW_REF_BACKSLASH = "outputs\\full_universe_source_acquisition\\expanded_universe_v2_20m_asx_promoted.csv"

EXPECTED_UPDATED_FILES = {
    "outputs/audit/documentation_canonical_dataset_path_v2_14i.json",
    "outputs/audit/eol_guard_v2_14k.json",
    "tests/test_expanded_universe_post_closure_v2_14j.py",
}

STATUS_SUCCESS = "ASX_ACTIVE_POINTER_UPDATE_VALIDATION_COMPLETED_3_FILES_VALIDATED_42708_ROWS_POINTERS_ACTIVE_ROLLBACK_AVAILABLE_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_ACTIVE_POINTER_UPDATE_VALIDATION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20S - Post-Pointer Operational Readiness Gate"
NEXT_PHASE_REVIEW = "v2.20R_REVIEW - ASX Active Pointer Update Validation Review"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


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
        TARGET_FILE_VALIDATION_CSV,
        HISTORICAL_PRESERVATION_CSV,
        DATASET_CONTROLS_CSV,
        ROLLBACK_CONTROLS_CSV,
        READINESS_GATE_CSV,
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

    q_summary = v220q.get("update_summary", {})
    q_manifest = v220q.get("update_manifest", [])
    q_preservation = v220q.get("preservation_audit", [])

    q_manifest_paths = {normalize_path(row.get("path", "")) for row in q_manifest}
    q_manifest_by_path = {normalize_path(row.get("path", "")): row for row in q_manifest if row.get("path")}

    active_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    promoted_rows = count_csv_rows(PROMOTED_CANONICAL_DATASET)
    current_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_rows = count_csv_rows(ASX_VALIDATED_CANDIDATE_DATASET)

    active_sha = sha256_file(ACTIVE_CANONICAL_DATASET)
    promoted_sha = sha256_file(PROMOTED_CANONICAL_DATASET)
    current_sha = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_sha = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)

    active_header = read_csv_header(ACTIVE_CANONICAL_DATASET)
    promoted_header = read_csv_header(PROMOTED_CANONICAL_DATASET)
    asx_header = read_csv_header(ASX_VALIDATED_CANDIDATE_DATASET)

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
    add_check("v2_20q_next_phase_expected", v220q.get("recommended_next_phase") == "v2.20R - ASX Active Pointer Update Validation", "critical", str(v220q.get("recommended_next_phase")))

    add_check("v2_20q_update_decision_expected", q_summary.get("update_decision") == "CONTROLLED_ACTIVE_POINTER_UPDATE_COMPLETED_READY_FOR_VALIDATION", "critical", str(q_summary.get("update_decision")))
    add_check("v2_20q_updated_files_expected", int(q_summary.get("updated_files", -1)) == 3, "critical", f"updated_files={q_summary.get('updated_files')}")
    add_check("v2_20q_old_refs_replaced_expected", int(q_summary.get("total_old_refs_replaced", -1)) == 3, "critical", f"total_old_refs_replaced={q_summary.get('total_old_refs_replaced')}")
    add_check("v2_20q_historical_references_unchanged", int(q_summary.get("historical_reference_files_changed", -1)) == 0, "critical", f"historical_changed={q_summary.get('historical_reference_files_changed')}")
    add_check("v2_20q_pointer_update_performed", bool(q_summary.get("pointer_update_performed")) is True, "critical", f"pointer_update_performed={q_summary.get('pointer_update_performed')}")
    add_check("v2_20q_active_pointer_updated", bool(q_summary.get("active_pointer_updated")) is True, "critical", f"active_pointer_updated={q_summary.get('active_pointer_updated')}")
    add_check("v2_20q_active_canonical_not_replaced", bool(q_summary.get("active_canonical_replaced")) is False, "critical", f"active_canonical_replaced={q_summary.get('active_canonical_replaced')}")

    add_check("q_manifest_candidate_set_exact", q_manifest_paths == EXPECTED_UPDATED_FILES, "critical", f"q_manifest_paths={sorted(q_manifest_paths)}")
    add_check("q_manifest_count_expected", len(q_manifest) == 3, "critical", f"manifest_rows={len(q_manifest)}")

    add_check("active_rows_expected", active_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_rows={active_rows}")
    add_check("promoted_rows_expected", promoted_rows == PROMOTED_CANONICAL_ROWS_EXPECTED, "critical", f"promoted_rows={promoted_rows}")
    add_check("current_candidate_rows_expected", current_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("asx_candidate_rows_expected", asx_rows == ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"asx_rows={asx_rows}")

    add_check("active_sha_expected", active_sha == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_sha)
    add_check("promoted_sha_expected", promoted_sha == PROMOTED_CANONICAL_SHA_EXPECTED, "critical", promoted_sha)
    add_check("current_candidate_sha_expected", current_sha == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", current_sha)
    add_check("asx_candidate_sha_expected", asx_sha == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", asx_sha)

    add_check("promoted_matches_asx_rows", promoted_rows == asx_rows, "critical", f"promoted={promoted_rows};asx={asx_rows}")
    add_check("promoted_matches_asx_sha", promoted_sha == asx_sha, "critical", f"promoted={promoted_sha};asx={asx_sha}")
    add_check("promoted_schema_matches_active", promoted_header == active_header, "critical", f"promoted_columns={len(promoted_header)};active_columns={len(active_header)}")
    add_check("promoted_schema_matches_asx", promoted_header == asx_header, "critical", f"promoted_columns={len(promoted_header)};asx_columns={len(asx_header)}")
    add_check("schema_column_count_expected", len(promoted_header) == 33, "critical", f"promoted_columns={len(promoted_header)}")

    add_check("quality_floor_crossed", promoted_rows >= QUALITY_FLOOR_TARGET, "critical", f"rows={promoted_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", promoted_rows <= QUALITY_CEILING_TARGET, "critical", f"rows={promoted_rows};ceiling={QUALITY_CEILING_TARGET}")

    target_validation_rows: list[dict[str, Any]] = []
    validated_target_files = 0
    target_files_with_old_refs = 0
    target_files_with_new_refs = 0
    target_files_with_sha_drift = 0

    for path_str in sorted(EXPECTED_UPDATED_FILES):
        path = Path(path_str)
        q_row = q_manifest_by_path.get(path_str, {})
        expected_after_sha = str(q_row.get("after_sha", ""))

        exists = path.exists()
        current_file_sha = sha256_file(path) if exists else ""
        content = read_text(path) if exists else ""
        counts = ref_counts(content)

        old_refs_removed = counts["old_total"] == 0
        new_refs_present = counts["new_total"] >= 1
        sha_matches_q_after = current_file_sha == expected_after_sha
        validated = exists and old_refs_removed and new_refs_present and sha_matches_q_after

        if validated:
            validated_target_files += 1
        if counts["old_total"] > 0:
            target_files_with_old_refs += 1
        if counts["new_total"] > 0:
            target_files_with_new_refs += 1
        if not sha_matches_q_after:
            target_files_with_sha_drift += 1

        target_validation_rows.append({
            "path": path_str,
            "exists": exists,
            "expected_after_sha_from_v220q": expected_after_sha,
            "current_sha": current_file_sha,
            "sha_matches_v220q_after": sha_matches_q_after,
            "old_refs_current": counts["old_total"],
            "new_refs_current": counts["new_total"],
            "old_refs_removed": old_refs_removed,
            "new_refs_present": new_refs_present,
            "validated": validated,
        })

        add_check(f"target_file_exists::{path_str}", exists, "critical", str(path))
        add_check(f"target_file_sha_matches_v2_20q_after::{path_str}", sha_matches_q_after, "critical", f"expected={expected_after_sha};current={current_file_sha}")
        add_check(f"target_file_old_refs_removed::{path_str}", old_refs_removed, "critical", f"old_refs_current={counts['old_total']}")
        add_check(f"target_file_new_refs_present::{path_str}", new_refs_present, "critical", f"new_refs_current={counts['new_total']}")
        add_check(f"target_file_validated::{path_str}", validated, "critical", f"validated={validated}")

    historical_validation_rows: list[dict[str, Any]] = []
    historical_checked = 0
    historical_changed = 0
    historical_missing = 0

    for row in q_preservation:
        path_str = normalize_path(row.get("path", ""))
        if not path_str:
            continue

        expected_after_sha = str(row.get("after_sha", ""))
        expected_changed = str(row.get("changed", "")).lower() == "true"

        path = Path(path_str)
        exists = path.exists()
        current_file_sha = sha256_file(path) if exists else ""

        historical_checked += 1

        sha_matches = exists and current_file_sha == expected_after_sha
        changed_now = not sha_matches

        if changed_now:
            historical_changed += 1
        if not exists:
            historical_missing += 1

        historical_validation_rows.append({
            "path": path_str,
            "exists": exists,
            "expected_after_sha_from_v220q": expected_after_sha,
            "current_sha": current_file_sha,
            "changed_in_v220q": expected_changed,
            "changed_since_v220q": changed_now,
            "preserved": sha_matches,
        })

    add_check("all_target_files_validated", validated_target_files == 3, "critical", f"validated_target_files={validated_target_files}")
    add_check("no_old_refs_in_target_files", target_files_with_old_refs == 0, "critical", f"target_files_with_old_refs={target_files_with_old_refs}")
    add_check("new_refs_present_in_all_target_files", target_files_with_new_refs == 3, "critical", f"target_files_with_new_refs={target_files_with_new_refs}")
    add_check("no_target_file_sha_drift_since_v2_20q", target_files_with_sha_drift == 0, "critical", f"target_files_with_sha_drift={target_files_with_sha_drift}")

    add_check("historical_preservation_checked", historical_checked >= 1, "critical", f"historical_checked={historical_checked}")
    add_check("historical_references_preserved_since_v2_20q", historical_changed == 0, "critical", f"historical_changed={historical_changed}")
    add_check("historical_references_not_missing", historical_missing == 0, "critical", f"historical_missing={historical_missing}")

    add_check("validation_only", True, "critical", "active pointer update validation only")
    add_check("file_edit_not_performed", True, "critical", "file_edit_performed=False")
    add_check("file_copy_not_performed", True, "critical", "file_copy_performed=False")
    add_check("file_rename_not_performed", True, "critical", "file_rename_performed=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
        validation_decision = "ACTIVE_POINTER_UPDATE_VALIDATION_BLOCKED_REVIEW_REQUIRED"
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
        validation_decision = "ACTIVE_POINTER_UPDATE_VALIDATED_READY_FOR_OPERATIONAL_READINESS_GATE"

    dataset_control_rows = [
        {
            "artifact": "active_canonical_rollback",
            "path": str(ACTIVE_CANONICAL_DATASET),
            "rows": active_rows,
            "sha256": active_sha,
            "expected_rows": ACTIVE_CANONICAL_ROWS_EXPECTED,
            "expected_sha": ACTIVE_CANONICAL_SHA_EXPECTED,
            "validated": active_rows == ACTIVE_CANONICAL_ROWS_EXPECTED and active_sha == ACTIVE_CANONICAL_SHA_EXPECTED,
            "role": "rollback_reference_preserved",
        },
        {
            "artifact": "promoted_canonical_active_target",
            "path": str(PROMOTED_CANONICAL_DATASET),
            "rows": promoted_rows,
            "sha256": promoted_sha,
            "expected_rows": PROMOTED_CANONICAL_ROWS_EXPECTED,
            "expected_sha": PROMOTED_CANONICAL_SHA_EXPECTED,
            "validated": promoted_rows == PROMOTED_CANONICAL_ROWS_EXPECTED and promoted_sha == PROMOTED_CANONICAL_SHA_EXPECTED,
            "role": "active_pointer_target",
        },
        {
            "artifact": "asx_validated_candidate_source",
            "path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "rows": asx_rows,
            "sha256": asx_sha,
            "expected_rows": ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED,
            "expected_sha": ASX_VALIDATED_CANDIDATE_SHA_EXPECTED,
            "validated": asx_rows == ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED and asx_sha == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED,
            "role": "immutable_source_reference",
        },
    ]

    rollback_control_rows = [
        {
            "rollback_id": "ROLLBACK_001",
            "scope": "active_canonical_rollback",
            "reference_path": str(ACTIVE_CANONICAL_DATASET),
            "reference_rows": active_rows,
            "reference_sha": active_sha,
            "status": "AVAILABLE_UNCHANGED" if active_sha == ACTIVE_CANONICAL_SHA_EXPECTED else "DRIFT_DETECTED",
            "rollback_action": "Use v2_14e if active pointer validation fails or operational readiness is not approved.",
        },
        {
            "rollback_id": "ROLLBACK_002",
            "scope": "pointer_update_reverse_path",
            "reference_path": ";".join(sorted(EXPECTED_UPDATED_FILES)),
            "reference_rows": validated_target_files,
            "reference_sha": "",
            "status": "REVERSIBLE_REFERENCES_VALIDATED" if validated_target_files == 3 else "REVIEW_REQUIRED",
            "rollback_action": f"Reverse `{NEW_REF_FORWARD}` back to `{OLD_REF_FORWARD}` only through an explicit rollback phase.",
        },
        {
            "rollback_id": "ROLLBACK_003",
            "scope": "promoted_canonical_target",
            "reference_path": str(PROMOTED_CANONICAL_DATASET),
            "reference_rows": promoted_rows,
            "reference_sha": promoted_sha,
            "status": "AVAILABLE_VALIDATED" if promoted_sha == PROMOTED_CANONICAL_SHA_EXPECTED else "DRIFT_DETECTED",
            "rollback_action": "Keep as active target only if operational readiness gate passes.",
        },
    ]

    readiness_gate_rows = [
        {
            "gate_id": "READINESS_001",
            "gate": "controlled_pointer_files_validated",
            "passed": validated_target_files == 3,
            "detail": f"validated_target_files={validated_target_files}",
            "required_for_v220s": True,
        },
        {
            "gate_id": "READINESS_002",
            "gate": "no_old_refs_in_active_pointer_files",
            "passed": target_files_with_old_refs == 0,
            "detail": f"target_files_with_old_refs={target_files_with_old_refs}",
            "required_for_v220s": True,
        },
        {
            "gate_id": "READINESS_003",
            "gate": "promoted_canonical_available",
            "passed": promoted_rows == PROMOTED_CANONICAL_ROWS_EXPECTED and promoted_sha == PROMOTED_CANONICAL_SHA_EXPECTED,
            "detail": f"rows={promoted_rows};sha={promoted_sha}",
            "required_for_v220s": True,
        },
        {
            "gate_id": "READINESS_004",
            "gate": "rollback_canonical_available",
            "passed": active_rows == ACTIVE_CANONICAL_ROWS_EXPECTED and active_sha == ACTIVE_CANONICAL_SHA_EXPECTED,
            "detail": f"rows={active_rows};sha={active_sha}",
            "required_for_v220s": True,
        },
        {
            "gate_id": "READINESS_005",
            "gate": "historical_references_preserved",
            "passed": historical_changed == 0,
            "detail": f"historical_changed={historical_changed}",
            "required_for_v220s": True,
        },
        {
            "gate_id": "READINESS_006",
            "gate": "no_scoring_or_external_calls",
            "passed": True,
            "detail": "scoring=False;openai=False;broker=False;full59k=False",
            "required_for_v220s": True,
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "operational-readiness",
            "action": "run_post_pointer_operational_readiness_gate",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Pointer update validated; operational readiness must approve using promoted canonical as operational base.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "decision/readiness only; no scoring/OpenAI/broker/full59k",
        },
        {
            "action_order": 2,
            "action_scope": "rollback",
            "action": "preserve_v2_14e_rollback_reference",
            "priority": "high",
            "reason": "Previous active canonical remains intact and must remain available through final closure.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "do not delete or overwrite rollback dataset",
        },
        {
            "action_order": 3,
            "action_scope": "scoring",
            "action": "defer_scoring_until_readiness_gate_and_closure",
            "priority": "medium",
            "reason": "Pointer validation does not authorize scoring.",
            "recommended_phase": "post-v2.20S/v2.20T explicit decision",
            "guardrails": "separate approval required",
        },
    ]

    validation_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "validation_decision": validation_decision,
        "active_pointer_target_dataset": str(PROMOTED_CANONICAL_DATASET),
        "active_pointer_target_rows": promoted_rows,
        "active_pointer_target_sha": promoted_sha,
        "rollback_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "rollback_canonical_rows": active_rows,
        "rollback_canonical_sha": active_sha,
        "validated_target_files": validated_target_files,
        "target_files_with_old_refs": target_files_with_old_refs,
        "target_files_with_new_refs": target_files_with_new_refs,
        "target_files_with_sha_drift": target_files_with_sha_drift,
        "historical_reference_files_checked": historical_checked,
        "historical_reference_files_changed": historical_changed,
        "historical_reference_files_missing": historical_missing,
        "active_pointer_updated_from_v2_20q": True,
        "pointer_update_validated": critical_failed == 0,
        "active_canonical_replaced": False,
        "canonical_dataset_modified": False,
        "file_edit_performed": False,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": promoted_rows >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": promoted_rows <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": promoted_rows - QUALITY_FLOOR_TARGET,
        "remaining_capacity_to_quality_ceiling": QUALITY_CEILING_TARGET - promoted_rows,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k": ASPIRATIONAL_TARGET - promoted_rows,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in validation_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(
        TARGET_FILE_VALIDATION_CSV,
        target_validation_rows,
        [
            "path", "exists", "expected_after_sha_from_v220q", "current_sha",
            "sha_matches_v220q_after", "old_refs_current", "new_refs_current",
            "old_refs_removed", "new_refs_present", "validated",
        ],
    )
    write_csv(
        HISTORICAL_PRESERVATION_CSV,
        historical_validation_rows,
        [
            "path", "exists", "expected_after_sha_from_v220q", "current_sha",
            "changed_in_v220q", "changed_since_v220q", "preserved",
        ],
    )
    write_csv(
        DATASET_CONTROLS_CSV,
        dataset_control_rows,
        ["artifact", "path", "rows", "sha256", "expected_rows", "expected_sha", "validated", "role"],
    )
    write_csv(
        ROLLBACK_CONTROLS_CSV,
        rollback_control_rows,
        ["rollback_id", "scope", "reference_path", "reference_rows", "reference_sha", "status", "rollback_action"],
    )
    write_csv(
        READINESS_GATE_CSV,
        readiness_gate_rows,
        ["gate_id", "gate", "passed", "detail", "required_for_v220s"],
    )
    write_csv(
        NEXT_ACTIONS_CSV,
        next_actions_rows,
        ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"],
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "validation_summary": validation_summary,
        "target_file_validation": target_validation_rows,
        "historical_preservation_validation": historical_validation_rows,
        "dataset_controls": dataset_control_rows,
        "rollback_controls": rollback_control_rows,
        "readiness_gate": readiness_gate_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "active_pointer_update_validation_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "operational_42k_floor_achieved": promoted_rows >= QUALITY_FLOOR_TARGET,
            "operational_45k_ceiling_respected": promoted_rows <= QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "target_files_validated": validated_target_files,
            "target_files_with_old_refs": target_files_with_old_refs,
            "target_files_with_new_refs": target_files_with_new_refs,
            "historical_reference_files_changed": historical_changed,
            "rollback_canonical_available": active_sha == ACTIVE_CANONICAL_SHA_EXPECTED,
            "promoted_canonical_available": promoted_sha == PROMOTED_CANONICAL_SHA_EXPECTED,
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
            "promotion_dry_run_performed": False,
            "controlled_promoted_file_creation_performed": False,
            "promoted_canonical_validation_performed": False,
            "active_pointer_decision_gate_performed": False,
            "active_pointer_update_plan_performed": False,
            "controlled_active_pointer_update_performed": False,
            "file_edit_performed": False,
            "file_copy_performed": False,
            "file_rename_performed": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "promoted_canonical_dataset_read": True,
            "promoted_canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "active_pointer_updated_from_v2_20q": True,
            "pointer_update_validated": critical_failed == 0,
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

    target_lines = "\n".join(
        f"- `{row['path']}` — validated `{row['validated']}` — old_refs `{row['old_refs_current']}` — new_refs `{row['new_refs_current']}`"
        for row in target_validation_rows
    )

    readiness_lines = "\n".join(
        f"- `{row['gate_id']}` — {row['gate']}: {'PASS' if row['passed'] else 'FAIL'} — {row['detail']}"
        for row in readiness_gate_rows
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

v2.20R validates the controlled active pointer update performed in v2.20Q.

This phase is validation-only. It does **not** modify files, update pointers, replace canonical, copy files, rename files, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Validation summary

- Validation decision: `{validation_decision}`
- Active pointer target dataset: `{PROMOTED_CANONICAL_DATASET}`
- Active pointer target rows: `{promoted_rows}`
- Active pointer target SHA256: `{promoted_sha}`
- Rollback canonical dataset: `{ACTIVE_CANONICAL_DATASET}`
- Rollback canonical rows: `{active_rows}`
- Rollback canonical SHA256: `{active_sha}`
- Validated target files: `{validated_target_files}`
- Target files with old refs: `{target_files_with_old_refs}`
- Target files with new refs: `{target_files_with_new_refs}`
- Target files with SHA drift: `{target_files_with_sha_drift}`
- Historical/reference files checked: `{historical_checked}`
- Historical/reference files changed: `{historical_changed}`
- Active canonical replaced: `False`
- Canonical dataset modified: `False`
- File edit performed: `False`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Target file validation

{target_lines}

## Readiness gate for v2.20S

{readiness_lines}

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

    print("v2.20R ASX active pointer update validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in validation_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("TARGET_FILE_VALIDATION:")
    for row in target_validation_rows:
        print(f"- {row['path']}: validated={row['validated']} old_refs={row['old_refs_current']} new_refs={row['new_refs_current']} sha_matches={row['sha_matches_v220q_after']}")
    print("")
    print("HISTORICAL_PRESERVATION:")
    print(f"- historical_checked: {historical_checked}")
    print(f"- historical_changed: {historical_changed}")
    print(f"- historical_missing: {historical_missing}")
    print("")
    print("DATASET_CONTROLS:")
    for row in dataset_control_rows:
        print(f"- {row['artifact']}: rows={row['rows']} sha={row['sha256']} validated={row['validated']}")
    print("")
    print("READINESS_GATE:")
    for row in readiness_gate_rows:
        print(f"- {row['gate_id']}: {row['gate']} - {'PASS' if row['passed'] else 'FAIL'} - {row['detail']}")
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
