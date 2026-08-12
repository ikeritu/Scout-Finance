from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20P"
PHASE = "ASX Active Pointer Update Plan"
PHASE_TYPE = "active-pointer-update-plan-only"

REPO_ROOT = Path(".")
OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PROMOTED_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"

V220O_JSON = OUTPUT_DIR / "asx_active_pointer_decision_gate_v2_20o.json"
V220N_JSON = OUTPUT_DIR / "asx_promoted_canonical_validation_v2_20n.json"
V220M_JSON = OUTPUT_DIR / "asx_controlled_promoted_file_creation_v2_20m.json"

REPORT_JSON = OUTPUT_DIR / "asx_active_pointer_update_plan_v2_20p.json"
REPORT_MD = OUTPUT_DIR / "asx_active_pointer_update_plan_v2_20p.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_active_pointer_update_plan_summary_v2_20p.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_active_pointer_update_plan_checks_v2_20p.csv"
REFERENCE_INVENTORY_CSV = OUTPUT_DIR / "asx_active_pointer_update_plan_reference_inventory_v2_20p.csv"
UPDATE_CANDIDATES_CSV = OUTPUT_DIR / "asx_active_pointer_update_plan_update_candidates_v2_20p.csv"
HISTORICAL_REFERENCES_CSV = OUTPUT_DIR / "asx_active_pointer_update_plan_historical_references_v2_20p.csv"
PLAN_CONTROLS_CSV = OUTPUT_DIR / "asx_active_pointer_update_plan_controls_v2_20p.csv"
ROLLBACK_CONTROLS_CSV = OUTPUT_DIR / "asx_active_pointer_update_plan_rollback_controls_v2_20p.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_active_pointer_update_plan_next_actions_v2_20p.csv"

EXPECTED_V220O_STATUS = "ASX_ACTIVE_POINTER_DECISION_GATE_COMPLETED_POINTER_UPDATE_PLAN_APPROVED_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220N_STATUS = "ASX_PROMOTED_CANONICAL_VALIDATION_COMPLETED_42708_ROWS_PROMOTED_FILE_VALIDATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220M_STATUS = "ASX_CONTROLLED_PROMOTED_FILE_CREATION_COMPLETED_42708_ROWS_PROMOTED_FILE_CREATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"

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

STATUS_SUCCESS = "ASX_ACTIVE_POINTER_UPDATE_PLAN_COMPLETED_POINTER_UPDATE_READY_42708_ROWS_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_ACTIVE_POINTER_UPDATE_PLAN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20Q - ASX Controlled Active Pointer Update"
NEXT_PHASE_REVIEW = "v2.20P_REVIEW - ASX Active Pointer Update Plan Review"

OLD_REF_FORWARD = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
OLD_REF_BACKSLASH = "outputs\\full_universe_source_acquisition\\expanded_universe_v2_14e.csv"
NEW_REF_FORWARD = "outputs/full_universe_source_acquisition/expanded_universe_v2_20m_asx_promoted.csv"
NEW_REF_BACKSLASH = "outputs\\full_universe_source_acquisition\\expanded_universe_v2_20m_asx_promoted.csv"

TEXT_SUFFIXES = {
    ".py", ".json", ".md", ".csv", ".txt", ".yml", ".yaml", ".toml",
    ".ps1", ".bat", ".sh", ".html", ".js", ".ts", ".tsx", ".jsx",
}

EXCLUDED_DIR_PARTS = {
    ".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", ".next", "dist", "build",
}

MAX_SCAN_BYTES = 20_000_000


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


def is_scan_candidate(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_DIR_PARTS:
        return False
    if path == Path("Auditoria_Scout_Finance.docx"):
        return False
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    try:
        if path.stat().st_size > MAX_SCAN_BYTES:
            return False
    except OSError:
        return False
    return True


def classify_reference(path: Path) -> str:
    path_str = str(path).replace("\\", "/")
    name = path.name.lower()

    if path_str.startswith("outputs/full_universe_source_acquisition/"):
        return "historical_phase_artifact"

    if path_str.startswith("scripts/") and "_v2_" in name:
        return "historical_phase_script"

    if path_str.startswith("docs/") or path.suffix.lower() in {".md", ".txt"}:
        return "documentation_reference"

    if path_str.startswith("scripts/"):
        return "operational_script_candidate"

    if path.suffix.lower() in {".json", ".yml", ".yaml", ".toml", ".ps1", ".bat", ".sh"}:
        return "config_or_runtime_candidate"

    return "review_candidate"


def recommended_action_for_category(category: str, old_count: int, new_count: int) -> str:
    if old_count <= 0:
        return "no_old_pointer_reference_detected"

    if category in {"historical_phase_artifact", "historical_phase_script"}:
        return "do_not_update_historical_reference"

    if category == "documentation_reference":
        return "review_documentation_reference_before_update"

    return "review_for_controlled_pointer_update"


def scan_references() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    inventory: list[dict[str, Any]] = []
    update_candidates: list[dict[str, Any]] = []
    historical_refs: list[dict[str, Any]] = []

    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue

        if not is_scan_candidate(path):
            continue

        rel = path.relative_to(REPO_ROOT)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        old_forward_count = content.count(OLD_REF_FORWARD)
        old_backslash_count = content.count(OLD_REF_BACKSLASH)
        new_forward_count = content.count(NEW_REF_FORWARD)
        new_backslash_count = content.count(NEW_REF_BACKSLASH)

        old_count = old_forward_count + old_backslash_count
        new_count = new_forward_count + new_backslash_count

        if old_count == 0 and new_count == 0:
            continue

        category = classify_reference(rel)
        action = recommended_action_for_category(category, old_count, new_count)

        row = {
            "path": str(rel),
            "category": category,
            "old_ref_forward_count": old_forward_count,
            "old_ref_backslash_count": old_backslash_count,
            "old_ref_total_count": old_count,
            "new_ref_forward_count": new_forward_count,
            "new_ref_backslash_count": new_backslash_count,
            "new_ref_total_count": new_count,
            "recommended_action": action,
            "planned_update_in_v220p": False,
        }

        inventory.append(row)

        if action == "review_for_controlled_pointer_update":
            update_candidates.append(row)
        else:
            historical_refs.append(row)

    return inventory, update_candidates, historical_refs


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        REFERENCE_INVENTORY_CSV,
        UPDATE_CANDIDATES_CSV,
        HISTORICAL_REFERENCES_CSV,
        PLAN_CONTROLS_CSV,
        ROLLBACK_CONTROLS_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220m = read_json(V220M_JSON)
    v220n = read_json(V220N_JSON)
    v220o = read_json(V220O_JSON)

    v220o_summary = v220o.get("decision_summary", {})

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

    inventory_rows, update_candidate_rows, historical_reference_rows = scan_references()

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    promoted_canonical_sha_after = sha256_file(PROMOTED_CANONICAL_DATASET)

    old_ref_files_total = sum(1 for row in inventory_rows if int(row["old_ref_total_count"]) > 0)
    new_ref_files_total = sum(1 for row in inventory_rows if int(row["new_ref_total_count"]) > 0)
    update_candidate_files_total = len(update_candidate_rows)
    historical_reference_files_total = len(historical_reference_rows)

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
    add_check("v2_20o_next_phase_expected", v220o.get("recommended_next_phase") == "v2.20P - ASX Active Pointer Update Plan", "critical", str(v220o.get("recommended_next_phase")))
    add_check("v2_20o_pointer_decision_expected", v220o_summary.get("pointer_decision") == "PREPARE_ACTIVE_POINTER_UPDATE_PLAN", "critical", str(v220o_summary.get("pointer_decision")))
    add_check("v2_20o_pointer_update_not_performed", bool(v220o_summary.get("pointer_update_performed")) is False, "critical", f"pointer_update_performed={v220o_summary.get('pointer_update_performed')}")

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

    add_check("reference_inventory_completed", len(inventory_rows) >= 1, "critical", f"inventory_rows={len(inventory_rows)}")
    add_check("old_reference_files_detected", old_ref_files_total >= 1, "warning", f"old_ref_files_total={old_ref_files_total}")
    add_check("update_candidates_inventory_created", True, "critical", f"update_candidate_files_total={update_candidate_files_total}")
    add_check("historical_references_inventory_created", True, "critical", f"historical_reference_files_total={historical_reference_files_total}")

    add_check("active_canonical_sha_unchanged_during_plan", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical SHA unchanged")
    add_check("promoted_canonical_sha_unchanged_during_plan", promoted_canonical_sha_before == promoted_canonical_sha_after, "critical", "promoted canonical SHA unchanged")

    add_check("plan_only", True, "critical", "active pointer update plan only")
    add_check("pointer_update_not_performed", True, "critical", "active_pointer_updated=False")
    add_check("files_not_modified", True, "critical", "no target files modified in this phase")
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
        plan_decision = "ACTIVE_POINTER_UPDATE_PLAN_BLOCKED_REVIEW_REQUIRED"
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
        plan_decision = "ACTIVE_POINTER_UPDATE_PLAN_READY_FOR_CONTROLLED_UPDATE"

    plan_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "plan_decision": plan_decision,
        "current_active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "current_active_canonical_rows": active_canonical_rows,
        "current_active_canonical_sha": active_canonical_sha_before,
        "target_promoted_canonical_dataset": str(PROMOTED_CANONICAL_DATASET),
        "target_promoted_canonical_rows": promoted_canonical_rows,
        "target_promoted_canonical_sha": promoted_canonical_sha_before,
        "target_matches_asx_source_rows": promoted_canonical_rows == asx_validated_candidate_rows,
        "target_matches_asx_source_sha": promoted_canonical_sha_before == asx_validated_candidate_sha_before,
        "target_schema_matches_active": promoted_header == active_header,
        "schema_column_count": len(promoted_header),
        "old_reference_files_total": old_ref_files_total,
        "new_reference_files_total": new_ref_files_total,
        "update_candidate_files_total": update_candidate_files_total,
        "historical_reference_files_total": historical_reference_files_total,
        "planned_pointer_update_from": OLD_REF_FORWARD,
        "planned_pointer_update_to": NEW_REF_FORWARD,
        "pointer_update_performed": False,
        "active_pointer_updated": False,
        "active_canonical_replaced": False,
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

    plan_control_rows = [
        {
            "control_id": "PLAN_001",
            "control": "decision_gate_approved_plan",
            "passed": v220o_summary.get("pointer_decision") == "PREPARE_ACTIVE_POINTER_UPDATE_PLAN",
            "detail": str(v220o_summary.get("pointer_decision")),
        },
        {
            "control_id": "PLAN_002",
            "control": "promoted_file_validated",
            "passed": promoted_canonical_sha_before == PROMOTED_CANONICAL_SHA_EXPECTED and promoted_canonical_rows == PROMOTED_CANONICAL_ROWS_EXPECTED,
            "detail": f"rows={promoted_canonical_rows};sha={promoted_canonical_sha_before}",
        },
        {
            "control_id": "PLAN_003",
            "control": "active_canonical_available_as_rollback",
            "passed": active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED,
            "detail": f"rows={active_canonical_rows};sha={active_canonical_sha_before}",
        },
        {
            "control_id": "PLAN_004",
            "control": "reference_inventory_completed",
            "passed": len(inventory_rows) >= 1,
            "detail": f"inventory_rows={len(inventory_rows)}",
        },
        {
            "control_id": "PLAN_005",
            "control": "no_pointer_update_in_this_phase",
            "passed": True,
            "detail": "active_pointer_updated=False",
        },
    ]

    rollback_control_rows = [
        {
            "rollback_id": "ROLLBACK_001",
            "scope": "active_canonical",
            "reference_path": str(ACTIVE_CANONICAL_DATASET),
            "reference_rows": active_canonical_rows,
            "reference_sha": active_canonical_sha_before,
            "status": "AVAILABLE_UNCHANGED",
            "rollback_action": "Keep v2_14e as rollback if controlled pointer update is not executed or fails validation.",
        },
        {
            "rollback_id": "ROLLBACK_002",
            "scope": "promoted_canonical",
            "reference_path": str(PROMOTED_CANONICAL_DATASET),
            "reference_rows": promoted_canonical_rows,
            "reference_sha": promoted_canonical_sha_before,
            "status": "VALIDATED_TARGET_FOR_POINTER_UPDATE",
            "rollback_action": "Do not activate unless v2.20Q controlled pointer update is explicitly executed and validated.",
        },
        {
            "rollback_id": "ROLLBACK_003",
            "scope": "pointer_update_plan",
            "reference_path": str(UPDATE_CANDIDATES_CSV),
            "reference_rows": update_candidate_files_total,
            "reference_sha": "",
            "status": "PLAN_ONLY_NO_RUNTIME_CHANGE",
            "rollback_action": "No runtime rollback required because v2.20P does not change references.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "pointer-update",
            "action": "execute_controlled_active_pointer_update",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Plan completed; exact reference inventory and candidates are available.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "update only reviewed candidates; preserve historical artifacts; no scoring/OpenAI/broker/full59k",
        },
        {
            "action_order": 2,
            "action_scope": "post-update-validation",
            "action": "validate_active_pointer_update",
            "priority": "high",
            "reason": "Any pointer update must be validated before operational scoring.",
            "recommended_phase": "v2.20R - ASX Active Pointer Update Validation",
            "guardrails": "verify references, SHA, rows and rollback path",
        },
        {
            "action_order": 3,
            "action_scope": "quality",
            "action": "keep_provider_expansion_frozen",
            "priority": "medium",
            "reason": "Promoted canonical already meets 42k–45k operating target.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "50k aspirational only; full59k deprecated",
        },
    ]

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in plan_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(
        REFERENCE_INVENTORY_CSV,
        inventory_rows,
        [
            "path", "category", "old_ref_forward_count", "old_ref_backslash_count",
            "old_ref_total_count", "new_ref_forward_count", "new_ref_backslash_count",
            "new_ref_total_count", "recommended_action", "planned_update_in_v220p",
        ],
    )
    write_csv(
        UPDATE_CANDIDATES_CSV,
        update_candidate_rows,
        [
            "path", "category", "old_ref_forward_count", "old_ref_backslash_count",
            "old_ref_total_count", "new_ref_forward_count", "new_ref_backslash_count",
            "new_ref_total_count", "recommended_action", "planned_update_in_v220p",
        ],
    )
    write_csv(
        HISTORICAL_REFERENCES_CSV,
        historical_reference_rows,
        [
            "path", "category", "old_ref_forward_count", "old_ref_backslash_count",
            "old_ref_total_count", "new_ref_forward_count", "new_ref_backslash_count",
            "new_ref_total_count", "recommended_action", "planned_update_in_v220p",
        ],
    )
    write_csv(PLAN_CONTROLS_CSV, plan_control_rows, ["control_id", "control", "passed", "detail"])
    write_csv(ROLLBACK_CONTROLS_CSV, rollback_control_rows, ["rollback_id", "scope", "reference_path", "reference_rows", "reference_sha", "status", "rollback_action"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "plan_summary": plan_summary,
        "reference_inventory": inventory_rows,
        "update_candidates": update_candidate_rows,
        "historical_references": historical_reference_rows,
        "plan_controls": plan_control_rows,
        "rollback_controls": rollback_control_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "active_pointer_update_plan_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "operational_42k_floor_achieved": promoted_canonical_rows >= QUALITY_FLOOR_TARGET,
            "operational_45k_ceiling_respected": promoted_canonical_rows <= QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "reference_inventory_performed": True,
            "update_candidate_files_total": update_candidate_files_total,
            "historical_reference_files_total": historical_reference_files_total,
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
            "file_copy_performed": False,
            "file_rename_performed": False,
            "file_edit_performed": False,
            "promoted_file_created_in_this_phase": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "promoted_canonical_dataset_read": True,
            "promoted_canonical_dataset_modified": False,
            "promoted_canonical_sha_unchanged": promoted_canonical_sha_before == promoted_canonical_sha_after,
            "active_canonical_replaced": False,
            "active_pointer_update_plan_created": critical_failed == 0,
            "active_pointer_updated": False,
            "pointer_update_performed": False,
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

    plan_control_lines = "\n".join(
        f"- `{row['control_id']}` — {row['control']}: {'PASS' if row['passed'] else 'FAIL'} — {row['detail']}"
        for row in plan_control_rows
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

v2.20P prepares the active pointer update plan.

It inventories references from:

`{OLD_REF_FORWARD}`

to:

`{NEW_REF_FORWARD}`

This phase is plan-only. It does **not** modify files, update pointers, replace canonical, copy files, rename files, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Plan summary

- Plan decision: `{plan_decision}`
- Current active canonical: `{ACTIVE_CANONICAL_DATASET}`
- Current active canonical rows: `{active_canonical_rows}`
- Current active canonical SHA256: `{active_canonical_sha_before}`
- Target promoted canonical: `{PROMOTED_CANONICAL_DATASET}`
- Target promoted canonical rows: `{promoted_canonical_rows}`
- Target promoted canonical SHA256: `{promoted_canonical_sha_before}`
- Target matches ASX source rows: `{promoted_canonical_rows == asx_validated_candidate_rows}`
- Target matches ASX source SHA: `{promoted_canonical_sha_before == asx_validated_candidate_sha_before}`
- Target schema matches active canonical: `{promoted_header == active_header}`
- Reference inventory rows: `{len(inventory_rows)}`
- Old reference files total: `{old_ref_files_total}`
- New reference files total: `{new_ref_files_total}`
- Update candidate files total: `{update_candidate_files_total}`
- Historical/reference files total: `{historical_reference_files_total}`
- Pointer update performed: `False`
- Active pointer updated: `False`
- Active canonical replaced: `False`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Plan controls

{plan_control_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Active pointer update plan only: true
- Reference inventory performed: true
- File edit performed: false
- Active pointer updated: false
- Pointer update performed: false
- Canonical dataset modified: false
- Active canonical replaced: false
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

    print("v2.20P ASX active pointer update plan completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("PLAN_SUMMARY:")
    for key, value in plan_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("PLAN_CONTROLS:")
    for row in plan_control_rows:
        print(f"- {row['control_id']}: {row['control']} - {'PASS' if row['passed'] else 'FAIL'} - {row['detail']}")
    print("")
    print("REFERENCE_INVENTORY:")
    print(f"- inventory_rows: {len(inventory_rows)}")
    print(f"- old_ref_files_total: {old_ref_files_total}")
    print(f"- new_ref_files_total: {new_ref_files_total}")
    print(f"- update_candidate_files_total: {update_candidate_files_total}")
    print(f"- historical_reference_files_total: {historical_reference_files_total}")
    print("")
    print("UPDATE_CANDIDATES:")
    for row in update_candidate_rows[:50]:
        print(f"- {row['path']} | category={row['category']} | old_refs={row['old_ref_total_count']} | action={row['recommended_action']}")
    if len(update_candidate_rows) > 50:
        print(f"- ... truncated {len(update_candidate_rows) - 50} more update candidates")
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
