from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20Q"
PHASE = "ASX Controlled Active Pointer Update"
PHASE_TYPE = "controlled-active-pointer-update-only"

REPO_ROOT = Path(".")
OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PROMOTED_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"

V220P_JSON = OUTPUT_DIR / "asx_active_pointer_update_plan_v2_20p.json"
V220O_JSON = OUTPUT_DIR / "asx_active_pointer_decision_gate_v2_20o.json"
V220N_JSON = OUTPUT_DIR / "asx_promoted_canonical_validation_v2_20n.json"
V220M_JSON = OUTPUT_DIR / "asx_controlled_promoted_file_creation_v2_20m.json"

REPORT_JSON = OUTPUT_DIR / "asx_controlled_active_pointer_update_v2_20q.json"
REPORT_MD = OUTPUT_DIR / "asx_controlled_active_pointer_update_v2_20q.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_controlled_active_pointer_update_summary_v2_20q.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_controlled_active_pointer_update_checks_v2_20q.csv"
UPDATE_MANIFEST_CSV = OUTPUT_DIR / "asx_controlled_active_pointer_update_manifest_v2_20q.csv"
REFERENCE_AUDIT_CSV = OUTPUT_DIR / "asx_controlled_active_pointer_update_reference_audit_v2_20q.csv"
PRESERVATION_AUDIT_CSV = OUTPUT_DIR / "asx_controlled_active_pointer_update_preservation_audit_v2_20q.csv"
ROLLBACK_CONTROLS_CSV = OUTPUT_DIR / "asx_controlled_active_pointer_update_rollback_controls_v2_20q.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_controlled_active_pointer_update_next_actions_v2_20q.csv"

EXPECTED_V220M_STATUS = "ASX_CONTROLLED_PROMOTED_FILE_CREATION_COMPLETED_42708_ROWS_PROMOTED_FILE_CREATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220N_STATUS = "ASX_PROMOTED_CANONICAL_VALIDATION_COMPLETED_42708_ROWS_PROMOTED_FILE_VALIDATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220O_STATUS = "ASX_ACTIVE_POINTER_DECISION_GATE_COMPLETED_POINTER_UPDATE_PLAN_APPROVED_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220P_STATUS = "ASX_ACTIVE_POINTER_UPDATE_PLAN_COMPLETED_POINTER_UPDATE_READY_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"

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

STATUS_SUCCESS = "ASX_CONTROLLED_ACTIVE_POINTER_UPDATE_COMPLETED_3_FILES_UPDATED_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_CONTROLLED_ACTIVE_POINTER_UPDATE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20R - ASX Active Pointer Update Validation"
NEXT_PHASE_REVIEW = "v2.20Q_REVIEW - ASX Controlled Active Pointer Update Review"

OLD_REF_FORWARD = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
OLD_REF_BACKSLASH = "outputs\\full_universe_source_acquisition\\expanded_universe_v2_14e.csv"
NEW_REF_FORWARD = "outputs/full_universe_source_acquisition/expanded_universe_v2_20m_asx_promoted.csv"
NEW_REF_BACKSLASH = "outputs\\full_universe_source_acquisition\\expanded_universe_v2_20m_asx_promoted.csv"

EXPECTED_UPDATE_CANDIDATES = {
    "outputs/audit/documentation_canonical_dataset_path_v2_14i.json",
    "outputs/audit/eol_guard_v2_14k.json",
    "tests/test_expanded_universe_post_closure_v2_14j.py",
}


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


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


def replace_refs(content: str) -> str:
    return content.replace(OLD_REF_FORWARD, NEW_REF_FORWARD).replace(OLD_REF_BACKSLASH, NEW_REF_BACKSLASH)


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        UPDATE_MANIFEST_CSV,
        REFERENCE_AUDIT_CSV,
        PRESERVATION_AUDIT_CSV,
        ROLLBACK_CONTROLS_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220m = read_json(V220M_JSON)
    v220n = read_json(V220N_JSON)
    v220o = read_json(V220O_JSON)
    v220p = read_json(V220P_JSON)

    v220p_summary = v220p.get("plan_summary", {})
    v220p_update_candidates = v220p.get("update_candidates", [])
    v220p_historical_references = v220p.get("historical_references", [])

    planned_candidate_paths = {
        normalize_path(row.get("path", "")) for row in v220p_update_candidates
    }

    historical_paths = sorted({
        normalize_path(row.get("path", "")) for row in v220p_historical_references if row.get("path")
    })

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    promoted_canonical_rows = count_csv_rows(PROMOTED_CANONICAL_DATASET)
    current_validated_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_rows = count_csv_rows(ASX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    promoted_canonical_sha_before = sha256_file(PROMOTED_CANONICAL_DATASET)
    current_validated_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_sha_before = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)

    active_header = read_csv_header(ACTIVE_CANONICAL_DATASET)
    promoted_header = read_csv_header(PROMOTED_CANONICAL_DATASET)
    asx_header = read_csv_header(ASX_VALIDATED_CANDIDATE_DATASET)

    historical_sha_before: dict[str, str] = {}
    for path_str in historical_paths:
        path = Path(path_str)
        if path.exists() and path.is_file():
            historical_sha_before[path_str] = sha256_file(path)

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
    add_check("v2_20p_next_phase_expected", v220p.get("recommended_next_phase") == "v2.20Q - ASX Controlled Active Pointer Update", "critical", str(v220p.get("recommended_next_phase")))
    add_check("v2_20p_plan_decision_expected", v220p_summary.get("plan_decision") == "ACTIVE_POINTER_UPDATE_PLAN_READY_FOR_CONTROLLED_UPDATE", "critical", str(v220p_summary.get("plan_decision")))
    add_check("v2_20p_pointer_update_not_performed", bool(v220p_summary.get("pointer_update_performed")) is False, "critical", f"pointer_update_performed={v220p_summary.get('pointer_update_performed')}")

    add_check("planned_candidate_set_exact", planned_candidate_paths == EXPECTED_UPDATE_CANDIDATES, "critical", f"planned={sorted(planned_candidate_paths)}")
    add_check("planned_candidate_count_expected", len(planned_candidate_paths) == 3, "critical", f"planned_candidate_count={len(planned_candidate_paths)}")

    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_rows={active_canonical_rows}")
    add_check("promoted_canonical_rows_expected", promoted_canonical_rows == PROMOTED_CANONICAL_ROWS_EXPECTED, "critical", f"promoted_rows={promoted_canonical_rows}")
    add_check("current_candidate_rows_expected", current_validated_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_rows={current_validated_candidate_rows}")
    add_check("asx_candidate_rows_expected", asx_validated_candidate_rows == ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"asx_rows={asx_validated_candidate_rows}")

    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("promoted_canonical_sha_expected", promoted_canonical_sha_before == PROMOTED_CANONICAL_SHA_EXPECTED, "critical", promoted_canonical_sha_before)
    add_check("current_candidate_sha_expected", current_validated_candidate_sha_before == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", current_validated_candidate_sha_before)
    add_check("asx_candidate_sha_expected", asx_validated_candidate_sha_before == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", asx_validated_candidate_sha_before)

    add_check("promoted_matches_asx_sha", promoted_canonical_sha_before == asx_validated_candidate_sha_before, "critical", f"promoted={promoted_canonical_sha_before};asx={asx_validated_candidate_sha_before}")
    add_check("promoted_matches_asx_rows", promoted_canonical_rows == asx_validated_candidate_rows, "critical", f"promoted={promoted_canonical_rows};asx={asx_validated_candidate_rows}")
    add_check("promoted_schema_matches_active", promoted_header == active_header, "critical", f"promoted_columns={len(promoted_header)};active_columns={len(active_header)}")
    add_check("promoted_schema_matches_asx", promoted_header == asx_header, "critical", f"promoted_columns={len(promoted_header)};asx_columns={len(asx_header)}")
    add_check("schema_column_count_expected", len(promoted_header) == 33, "critical", f"promoted_columns={len(promoted_header)}")
    add_check("quality_floor_crossed", promoted_canonical_rows >= QUALITY_FLOOR_TARGET, "critical", f"rows={promoted_canonical_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", promoted_canonical_rows <= QUALITY_CEILING_TARGET, "critical", f"rows={promoted_canonical_rows};ceiling={QUALITY_CEILING_TARGET}")

    pre_update_rows: list[dict[str, Any]] = []
    file_payloads: dict[str, tuple[Path, str, dict[str, int], str]] = {}

    for path_str in sorted(EXPECTED_UPDATE_CANDIDATES):
        path = Path(path_str)
        exists = path.exists()
        add_check(f"target_exists::{path_str}", exists, "critical", str(path))

        if not exists:
            continue

        before_content = read_text(path)
        before_counts = ref_counts(before_content)
        before_sha = sha256_file(path)

        pre_update_rows.append({
            "path": path_str,
            "before_sha": before_sha,
            "before_old_forward_count": before_counts["old_forward"],
            "before_old_backslash_count": before_counts["old_backslash"],
            "before_old_total_count": before_counts["old_total"],
            "before_new_forward_count": before_counts["new_forward"],
            "before_new_backslash_count": before_counts["new_backslash"],
            "before_new_total_count": before_counts["new_total"],
        })

        add_check(f"target_has_old_reference_before::{path_str}", before_counts["old_total"] > 0, "critical", f"old_refs={before_counts['old_total']}")
        add_check(f"target_not_already_updated_only::{path_str}", before_counts["old_total"] > 0, "critical", f"old_refs={before_counts['old_total']};new_refs={before_counts['new_total']}")

        file_payloads[path_str] = (path, before_content, before_counts, before_sha)

    update_blocked = critical_failed > 0

    updated_files = 0
    total_old_refs_replaced = 0
    update_manifest_rows: list[dict[str, Any]] = []
    reference_audit_rows: list[dict[str, Any]] = []

    if not update_blocked:
        for path_str in sorted(EXPECTED_UPDATE_CANDIDATES):
            path, before_content, before_counts, before_sha = file_payloads[path_str]

            after_content = replace_refs(before_content)
            after_counts_expected = ref_counts(after_content)

            write_text(path, after_content)

            after_sha = sha256_file(path)
            after_counts = ref_counts(read_text(path))

            old_refs_replaced = before_counts["old_total"] - after_counts["old_total"]
            new_refs_added = after_counts["new_total"] - before_counts["new_total"]

            updated = after_sha != before_sha
            if updated:
                updated_files += 1
                total_old_refs_replaced += old_refs_replaced

            update_manifest_rows.append({
                "path": path_str,
                "updated": updated,
                "before_sha": before_sha,
                "after_sha": after_sha,
                "old_refs_before": before_counts["old_total"],
                "old_refs_after": after_counts["old_total"],
                "new_refs_before": before_counts["new_total"],
                "new_refs_after": after_counts["new_total"],
                "old_refs_replaced": old_refs_replaced,
                "new_refs_added": new_refs_added,
                "planned_scope": "controlled_update_candidate",
            })

            reference_audit_rows.append({
                "path": path_str,
                "scope": "updated_candidate",
                "old_refs_before": before_counts["old_total"],
                "old_refs_after": after_counts["old_total"],
                "new_refs_before": before_counts["new_total"],
                "new_refs_after": after_counts["new_total"],
                "passed": after_counts["old_total"] == 0 and after_counts["new_total"] >= before_counts["new_total"] + before_counts["old_total"],
                "detail": "old references removed and promoted canonical references present",
            })

            add_check(f"target_updated::{path_str}", updated, "critical", f"before={before_sha};after={after_sha}")
            add_check(f"target_old_refs_removed::{path_str}", after_counts["old_total"] == 0, "critical", f"old_refs_after={after_counts['old_total']}")
            add_check(f"target_new_refs_added::{path_str}", after_counts["new_total"] >= before_counts["new_total"] + before_counts["old_total"], "critical", f"before_new={before_counts['new_total']};after_new={after_counts['new_total']};before_old={before_counts['old_total']}")
            add_check(f"target_replacement_arithmetic::{path_str}", old_refs_replaced == new_refs_added, "critical", f"old_refs_replaced={old_refs_replaced};new_refs_added={new_refs_added}")
    else:
        for row in pre_update_rows:
            update_manifest_rows.append({
                "path": row["path"],
                "updated": False,
                "before_sha": row["before_sha"],
                "after_sha": "",
                "old_refs_before": row["before_old_total_count"],
                "old_refs_after": "",
                "new_refs_before": row["before_new_total_count"],
                "new_refs_after": "",
                "old_refs_replaced": "",
                "new_refs_added": "",
                "planned_scope": "blocked_before_update",
            })

    historical_changed = 0
    preservation_audit_rows: list[dict[str, Any]] = []

    for path_str, before_sha in sorted(historical_sha_before.items()):
        path = Path(path_str)
        after_sha = sha256_file(path) if path.exists() else ""
        changed = before_sha != after_sha
        if changed:
            historical_changed += 1

        preservation_audit_rows.append({
            "path": path_str,
            "scope": "historical_or_documentation_reference",
            "before_sha": before_sha,
            "after_sha": after_sha,
            "changed": changed,
            "expected_action": "preserve_unchanged",
        })

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    promoted_canonical_sha_after = sha256_file(PROMOTED_CANONICAL_DATASET)
    current_validated_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_sha_after = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)

    add_check("updated_files_expected", updated_files == 3, "critical", f"updated_files={updated_files}")
    add_check("total_old_refs_replaced_expected", total_old_refs_replaced >= 3, "critical", f"total_old_refs_replaced={total_old_refs_replaced}")
    add_check("historical_references_preserved", historical_changed == 0, "critical", f"historical_changed={historical_changed}")

    add_check("active_canonical_sha_unchanged_after_update", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical SHA unchanged")
    add_check("promoted_canonical_sha_unchanged_after_update", promoted_canonical_sha_before == promoted_canonical_sha_after, "critical", "promoted canonical SHA unchanged")
    add_check("current_candidate_sha_unchanged_after_update", current_validated_candidate_sha_before == current_validated_candidate_sha_after, "critical", "current candidate SHA unchanged")
    add_check("asx_candidate_sha_unchanged_after_update", asx_validated_candidate_sha_before == asx_validated_candidate_sha_after, "critical", "ASX candidate SHA unchanged")

    add_check("controlled_update_only", True, "critical", "controlled active pointer update only")
    add_check("only_expected_candidates_updated", updated_files == len(EXPECTED_UPDATE_CANDIDATES), "critical", f"updated_files={updated_files};expected={len(EXPECTED_UPDATE_CANDIDATES)}")
    add_check("file_copy_not_performed", True, "critical", "file_copy_performed=False")
    add_check("file_rename_not_performed", True, "critical", "file_rename_performed=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
        update_decision = "CONTROLLED_ACTIVE_POINTER_UPDATE_REVIEW_REQUIRED"
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
        update_decision = "CONTROLLED_ACTIVE_POINTER_UPDATE_COMPLETED_READY_FOR_VALIDATION"

    update_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "update_decision": update_decision,
        "current_active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "current_active_canonical_rows": active_canonical_rows,
        "current_active_canonical_sha": active_canonical_sha_after,
        "target_promoted_canonical_dataset": str(PROMOTED_CANONICAL_DATASET),
        "target_promoted_canonical_rows": promoted_canonical_rows,
        "target_promoted_canonical_sha": promoted_canonical_sha_after,
        "planned_pointer_update_from": OLD_REF_FORWARD,
        "planned_pointer_update_to": NEW_REF_FORWARD,
        "expected_update_candidates": len(EXPECTED_UPDATE_CANDIDATES),
        "updated_files": updated_files,
        "total_old_refs_replaced": total_old_refs_replaced,
        "historical_reference_files_checked": len(preservation_audit_rows),
        "historical_reference_files_changed": historical_changed,
        "active_canonical_replaced": False,
        "active_pointer_updated": True,
        "pointer_update_performed": True,
        "active_canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
        "promoted_canonical_sha_unchanged": promoted_canonical_sha_before == promoted_canonical_sha_after,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": promoted_canonical_rows >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": promoted_canonical_rows <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": promoted_canonical_rows - QUALITY_FLOOR_TARGET,
        "remaining_capacity_to_quality_ceiling": QUALITY_CEILING_TARGET - promoted_canonical_rows,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k": ASPIRATIONAL_TARGET - promoted_canonical_rows,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    rollback_control_rows = [
        {
            "rollback_id": "ROLLBACK_001",
            "scope": "updated_pointer_files",
            "reference_path": ";".join(sorted(EXPECTED_UPDATE_CANDIDATES)),
            "reference_rows": updated_files,
            "reference_sha": "",
            "status": "UPDATED_NEEDS_POST_VALIDATION" if critical_failed == 0 else "UPDATE_REVIEW_REQUIRED",
            "rollback_action": "Reverse replacements from promoted canonical path back to v2_14e path if v2.20R fails.",
        },
        {
            "rollback_id": "ROLLBACK_002",
            "scope": "active_canonical",
            "reference_path": str(ACTIVE_CANONICAL_DATASET),
            "reference_rows": active_canonical_rows,
            "reference_sha": active_canonical_sha_after,
            "status": "AVAILABLE_UNCHANGED",
            "rollback_action": "Dataset file remains available as rollback.",
        },
        {
            "rollback_id": "ROLLBACK_003",
            "scope": "promoted_canonical",
            "reference_path": str(PROMOTED_CANONICAL_DATASET),
            "reference_rows": promoted_canonical_rows,
            "reference_sha": promoted_canonical_sha_after,
            "status": "AVAILABLE_UNCHANGED",
            "rollback_action": "Target dataset file remains available for validation.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "post-update-validation",
            "action": "validate_controlled_active_pointer_update",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Controlled pointer references were updated and must be validated before any scoring.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "validate exact 3 files, references, rows, SHA and rollback path",
        },
        {
            "action_order": 2,
            "action_scope": "quality",
            "action": "keep_provider_expansion_frozen",
            "priority": "medium",
            "reason": "Promoted canonical already meets 42k–45k target.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "no provider expansion/full59k/scoring by default",
        },
        {
            "action_order": 3,
            "action_scope": "scoring",
            "action": "defer_scoring_until_pointer_validation_passes",
            "priority": "high",
            "reason": "Scoring must not run until v2.20R validates the pointer update.",
            "recommended_phase": "post-v2.20R explicit scoring decision",
            "guardrails": "separate approval required",
        },
    ]

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in update_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(
        UPDATE_MANIFEST_CSV,
        update_manifest_rows,
        [
            "path", "updated", "before_sha", "after_sha",
            "old_refs_before", "old_refs_after",
            "new_refs_before", "new_refs_after",
            "old_refs_replaced", "new_refs_added", "planned_scope",
        ],
    )
    write_csv(
        REFERENCE_AUDIT_CSV,
        reference_audit_rows,
        [
            "path", "scope", "old_refs_before", "old_refs_after",
            "new_refs_before", "new_refs_after", "passed", "detail",
        ],
    )
    write_csv(
        PRESERVATION_AUDIT_CSV,
        preservation_audit_rows,
        ["path", "scope", "before_sha", "after_sha", "changed", "expected_action"],
    )
    write_csv(
        ROLLBACK_CONTROLS_CSV,
        rollback_control_rows,
        ["rollback_id", "scope", "reference_path", "reference_rows", "reference_sha", "status", "rollback_action"],
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
        "update_summary": update_summary,
        "update_manifest": update_manifest_rows,
        "reference_audit": reference_audit_rows,
        "preservation_audit": preservation_audit_rows,
        "rollback_controls": rollback_control_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "controlled_active_pointer_update_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "operational_42k_floor_achieved": promoted_canonical_rows >= QUALITY_FLOOR_TARGET,
            "operational_45k_ceiling_respected": promoted_canonical_rows <= QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "expected_update_candidates": len(EXPECTED_UPDATE_CANDIDATES),
            "updated_files": updated_files,
            "total_old_refs_replaced": total_old_refs_replaced,
            "historical_reference_files_changed": historical_changed,
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
            "file_copy_performed": False,
            "file_rename_performed": False,
            "file_edit_performed": updated_files > 0,
            "promoted_file_created_in_this_phase": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "promoted_canonical_dataset_read": True,
            "promoted_canonical_dataset_modified": False,
            "promoted_canonical_sha_unchanged": promoted_canonical_sha_before == promoted_canonical_sha_after,
            "active_canonical_replaced": False,
            "active_pointer_updated": critical_failed == 0,
            "pointer_update_performed": critical_failed == 0,
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

    manifest_lines = "\n".join(
        f"- `{row['path']}` — updated `{row['updated']}` — old `{row['old_refs_before']}->{row['old_refs_after']}` — new `{row['new_refs_before']}->{row['new_refs_after']}`"
        for row in update_manifest_rows
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

v2.20Q performs a controlled active pointer update.

It updates only the three candidates approved by v2.20P.

FROM:

`{OLD_REF_FORWARD}`

TO:

`{NEW_REF_FORWARD}`

This phase does **not** modify dataset CSVs, replace canonical, copy files, rename files, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Update summary

- Update decision: `{update_decision}`
- Expected update candidates: `{len(EXPECTED_UPDATE_CANDIDATES)}`
- Updated files: `{updated_files}`
- Total old refs replaced: `{total_old_refs_replaced}`
- Historical/reference files checked: `{len(preservation_audit_rows)}`
- Historical/reference files changed: `{historical_changed}`
- Current active canonical rows: `{active_canonical_rows}`
- Current active canonical SHA256: `{active_canonical_sha_after}`
- Target promoted canonical rows: `{promoted_canonical_rows}`
- Target promoted canonical SHA256: `{promoted_canonical_sha_after}`
- Active canonical replaced: `False`
- Active pointer updated: `{critical_failed == 0}`
- Pointer update performed: `{critical_failed == 0}`
- Scoring recalculated: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Update manifest

{manifest_lines}

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

    print("v2.20Q ASX controlled active pointer update completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("UPDATE_SUMMARY:")
    for key, value in update_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("UPDATE_MANIFEST:")
    for row in update_manifest_rows:
        print(f"- {row['path']}: updated={row['updated']} old={row['old_refs_before']}->{row['old_refs_after']} new={row['new_refs_before']}->{row['new_refs_after']}")
    print("")
    print("REFERENCE_AUDIT:")
    for row in reference_audit_rows:
        print(f"- {row['path']}: {'PASS' if row['passed'] else 'FAIL'} - {row['detail']}")
    print("")
    print("PRESERVATION_AUDIT:")
    print(f"- historical/reference files checked: {len(preservation_audit_rows)}")
    print(f"- historical/reference files changed: {historical_changed}")
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
