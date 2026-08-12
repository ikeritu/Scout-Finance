from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20N"
PHASE = "ASX Promoted Canonical Validation"
PHASE_TYPE = "promoted-canonical-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"
PROMOTED_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"

V220G_JSON = OUTPUT_DIR / "asx_expanded_rebuild_candidate_v2_20g.json"
V220H_JSON = OUTPUT_DIR / "asx_expanded_validation_v2_20h.json"
V220I_JSON = OUTPUT_DIR / "asx_closure_report_v2_20i.json"
V220J_JSON = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_v2_20j.json"
V220K_JSON = OUTPUT_DIR / "asx_canonical_promotion_plan_v2_20k.json"
V220L_JSON = OUTPUT_DIR / "asx_canonical_promotion_dry_run_v2_20l.json"
V220M_JSON = OUTPUT_DIR / "asx_controlled_promoted_file_creation_v2_20m.json"

REPORT_JSON = OUTPUT_DIR / "asx_promoted_canonical_validation_v2_20n.json"
REPORT_MD = OUTPUT_DIR / "asx_promoted_canonical_validation_v2_20n.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_promoted_canonical_validation_summary_v2_20n.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_promoted_canonical_validation_checks_v2_20n.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "asx_promoted_canonical_validation_artifact_manifest_v2_20n.csv"
SHA_CONTROLS_CSV = OUTPUT_DIR / "asx_promoted_canonical_validation_sha_controls_v2_20n.csv"
SCHEMA_CONTROLS_CSV = OUTPUT_DIR / "asx_promoted_canonical_validation_schema_controls_v2_20n.csv"
CONTENT_CONTROLS_CSV = OUTPUT_DIR / "asx_promoted_canonical_validation_content_controls_v2_20n.csv"
ROLLBACK_CONTROLS_CSV = OUTPUT_DIR / "asx_promoted_canonical_validation_rollback_controls_v2_20n.csv"
ACTIVATION_GATE_CSV = OUTPUT_DIR / "asx_promoted_canonical_validation_activation_gate_v2_20n.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_promoted_canonical_validation_next_actions_v2_20n.csv"

EXPECTED_V220G_STATUS = "ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220H_STATUS = "ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED"
EXPECTED_V220I_STATUS = "ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED"
EXPECTED_V220J_STATUS = "ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220K_STATUS = "ASX_CANONICAL_PROMOTION_PLAN_COMPLETED_DRY_RUN_READY_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220L_STATUS = "ASX_CANONICAL_PROMOTION_DRY_RUN_COMPLETED_PROMOTION_EXECUTION_READY_42708_ROWS_CANONICAL_UNCHANGED_PROMOTED_FILE_NOT_CREATED_FULL59K_DEPRECATED"
EXPECTED_V220M_STATUS = "ASX_CONTROLLED_PROMOTED_FILE_CREATION_COMPLETED_42708_ROWS_PROMOTED_FILE_CREATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392
ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED = 42708
PROMOTED_CANONICAL_ROWS_EXPECTED = 42708
ASX_NET_NEW_ROWS_EXPECTED = 1316
UPLIFT_VS_ACTIVE_CANONICAL_EXPECTED = 4421

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"
ASX_VALIDATED_CANDIDATE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
PROMOTED_CANONICAL_SHA_EXPECTED = ASX_VALIDATED_CANDIDATE_SHA_EXPECTED

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_ABOVE_QUALITY_FLOOR_EXPECTED = 708
REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED = 2292
ROWS_TO_ASPIRATIONAL_50K_EXPECTED = 7292

STATUS_SUCCESS = "ASX_PROMOTED_CANONICAL_VALIDATION_COMPLETED_42708_ROWS_PROMOTED_FILE_VALIDATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_PROMOTED_CANONICAL_VALIDATION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20O - ASX Active Pointer Decision Gate"
NEXT_PHASE_REVIEW = "v2.20N_REVIEW - ASX Promoted Canonical Validation Review"


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
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        SHA_CONTROLS_CSV,
        SCHEMA_CONTROLS_CSV,
        CONTENT_CONTROLS_CSV,
        ROLLBACK_CONTROLS_CSV,
        ACTIVATION_GATE_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220g = read_json(V220G_JSON)
    v220h = read_json(V220H_JSON)
    v220i = read_json(V220I_JSON)
    v220j = read_json(V220J_JSON)
    v220k = read_json(V220K_JSON)
    v220l = read_json(V220L_JSON)
    v220m = read_json(V220M_JSON)

    v220m_summary = v220m.get("creation_summary", {})

    active_canonical_exists = ACTIVE_CANONICAL_DATASET.exists()
    current_validated_candidate_exists = CURRENT_VALIDATED_CANDIDATE_DATASET.exists()
    asx_validated_candidate_exists = ASX_VALIDATED_CANDIDATE_DATASET.exists()
    promoted_canonical_exists = PROMOTED_CANONICAL_DATASET.exists()

    active_canonical_rows_before = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_validated_candidate_rows_before = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_rows_before = count_csv_rows(ASX_VALIDATED_CANDIDATE_DATASET)
    promoted_canonical_rows_before = count_csv_rows(PROMOTED_CANONICAL_DATASET)

    active_canonical_header = read_csv_header(ACTIVE_CANONICAL_DATASET)
    current_validated_candidate_header = read_csv_header(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_header = read_csv_header(ASX_VALIDATED_CANDIDATE_DATASET)
    promoted_canonical_header = read_csv_header(PROMOTED_CANONICAL_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_validated_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_sha_before = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)
    promoted_canonical_sha_before = sha256_file(PROMOTED_CANONICAL_DATASET)

    promoted_matches_asx_rows = promoted_canonical_rows_before == asx_validated_candidate_rows_before
    promoted_matches_asx_sha = promoted_canonical_sha_before == asx_validated_candidate_sha_before
    promoted_matches_asx_schema = promoted_canonical_header == asx_validated_candidate_header
    promoted_matches_active_schema = promoted_canonical_header == active_canonical_header
    promoted_matches_current_schema = promoted_canonical_header == current_validated_candidate_header

    asx_net_new_rows = asx_validated_candidate_rows_before - current_validated_candidate_rows_before
    uplift_vs_active_canonical_rows = promoted_canonical_rows_before - active_canonical_rows_before
    rows_above_quality_floor = promoted_canonical_rows_before - QUALITY_FLOOR_TARGET
    remaining_capacity_to_quality_ceiling = QUALITY_CEILING_TARGET - promoted_canonical_rows_before
    rows_to_aspirational_50k = ASPIRATIONAL_TARGET - promoted_canonical_rows_before

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_validated_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_sha_after = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)
    promoted_canonical_sha_after = sha256_file(PROMOTED_CANONICAL_DATASET)

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
    add_check("v2_20l_report_exists", V220L_JSON.exists(), "critical", str(V220L_JSON))
    add_check("v2_20m_report_exists", V220M_JSON.exists(), "critical", str(V220M_JSON))

    add_check("v2_20g_status_expected", v220g.get("status") == EXPECTED_V220G_STATUS, "critical", str(v220g.get("status")))
    add_check("v2_20h_status_expected", v220h.get("status") == EXPECTED_V220H_STATUS, "critical", str(v220h.get("status")))
    add_check("v2_20i_status_expected", v220i.get("status") == EXPECTED_V220I_STATUS, "critical", str(v220i.get("status")))
    add_check("v2_20j_status_expected", v220j.get("status") == EXPECTED_V220J_STATUS, "critical", str(v220j.get("status")))
    add_check("v2_20k_status_expected", v220k.get("status") == EXPECTED_V220K_STATUS, "critical", str(v220k.get("status")))
    add_check("v2_20l_status_expected", v220l.get("status") == EXPECTED_V220L_STATUS, "critical", str(v220l.get("status")))
    add_check("v2_20m_status_expected", v220m.get("status") == EXPECTED_V220M_STATUS, "critical", str(v220m.get("status")))
    add_check("v2_20m_next_phase_expected", v220m.get("recommended_next_phase") == "v2.20N - ASX Promoted Canonical Validation", "critical", str(v220m.get("recommended_next_phase")))

    add_check("v2_20m_creation_decision_expected", v220m_summary.get("creation_decision") == "PROMOTED_FILE_CREATED_READY_FOR_VALIDATION", "critical", str(v220m_summary.get("creation_decision")))
    add_check("v2_20m_copy_performed", bool(v220m_summary.get("copy_performed")) is True, "critical", f"copy_performed={v220m_summary.get('copy_performed')}")
    add_check("v2_20m_active_canonical_not_replaced", bool(v220m_summary.get("active_canonical_replaced")) is False, "critical", f"active_canonical_replaced={v220m_summary.get('active_canonical_replaced')}")
    add_check("v2_20m_active_pointer_not_updated", bool(v220m_summary.get("active_pointer_updated")) is False, "critical", f"active_pointer_updated={v220m_summary.get('active_pointer_updated')}")

    add_check("active_canonical_exists", active_canonical_exists, "critical", str(ACTIVE_CANONICAL_DATASET))
    add_check("current_validated_candidate_exists", current_validated_candidate_exists, "critical", str(CURRENT_VALIDATED_CANDIDATE_DATASET))
    add_check("asx_validated_candidate_exists", asx_validated_candidate_exists, "critical", str(ASX_VALIDATED_CANDIDATE_DATASET))
    add_check("promoted_canonical_exists", promoted_canonical_exists, "critical", str(PROMOTED_CANONICAL_DATASET))

    add_check("active_canonical_rows_expected", active_canonical_rows_before == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows_before}")
    add_check("current_validated_candidate_rows_expected", current_validated_candidate_rows_before == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_validated_rows={current_validated_candidate_rows_before}")
    add_check("asx_validated_candidate_rows_expected", asx_validated_candidate_rows_before == ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"asx_validated_rows={asx_validated_candidate_rows_before}")
    add_check("promoted_canonical_rows_expected", promoted_canonical_rows_before == PROMOTED_CANONICAL_ROWS_EXPECTED, "critical", f"promoted_rows={promoted_canonical_rows_before}")

    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("current_validated_candidate_sha_expected", current_validated_candidate_sha_before == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", current_validated_candidate_sha_before)
    add_check("asx_validated_candidate_sha_expected", asx_validated_candidate_sha_before == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", asx_validated_candidate_sha_before)
    add_check("promoted_canonical_sha_expected", promoted_canonical_sha_before == PROMOTED_CANONICAL_SHA_EXPECTED, "critical", promoted_canonical_sha_before)

    add_check("promoted_matches_asx_rows", promoted_matches_asx_rows, "critical", f"promoted={promoted_canonical_rows_before};asx={asx_validated_candidate_rows_before}")
    add_check("promoted_matches_asx_sha", promoted_matches_asx_sha, "critical", f"promoted={promoted_canonical_sha_before};asx={asx_validated_candidate_sha_before}")
    add_check("promoted_matches_asx_schema", promoted_matches_asx_schema, "critical", f"matches={promoted_matches_asx_schema}")
    add_check("promoted_matches_active_schema", promoted_matches_active_schema, "critical", f"matches={promoted_matches_active_schema}")
    add_check("promoted_matches_current_schema", promoted_matches_current_schema, "critical", f"matches={promoted_matches_current_schema}")
    add_check("promoted_column_count_expected", len(promoted_canonical_header) == 33, "critical", f"promoted_columns={len(promoted_canonical_header)}")

    add_check("active_canonical_sha_unchanged_during_validation", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical SHA unchanged")
    add_check("current_validated_candidate_sha_unchanged_during_validation", current_validated_candidate_sha_before == current_validated_candidate_sha_after, "critical", "current candidate SHA unchanged")
    add_check("asx_validated_candidate_sha_unchanged_during_validation", asx_validated_candidate_sha_before == asx_validated_candidate_sha_after, "critical", "ASX candidate SHA unchanged")
    add_check("promoted_canonical_sha_unchanged_during_validation", promoted_canonical_sha_before == promoted_canonical_sha_after, "critical", "promoted canonical SHA unchanged")

    add_check("asx_net_new_rows_expected", asx_net_new_rows == ASX_NET_NEW_ROWS_EXPECTED, "critical", f"asx_net_new_rows={asx_net_new_rows}")
    add_check("uplift_vs_active_canonical_expected", uplift_vs_active_canonical_rows == UPLIFT_VS_ACTIVE_CANONICAL_EXPECTED, "critical", f"uplift_vs_active_canonical={uplift_vs_active_canonical_rows}")
    add_check("quality_floor_crossed", promoted_canonical_rows_before >= QUALITY_FLOOR_TARGET, "critical", f"promoted_rows={promoted_canonical_rows_before};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", promoted_canonical_rows_before <= QUALITY_CEILING_TARGET, "critical", f"promoted_rows={promoted_canonical_rows_before};ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_above_quality_floor_expected", rows_above_quality_floor == ROWS_ABOVE_QUALITY_FLOOR_EXPECTED, "critical", f"rows_above_floor={rows_above_quality_floor}")
    add_check("remaining_capacity_to_quality_ceiling_expected", remaining_capacity_to_quality_ceiling == REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED, "critical", f"capacity_to_ceiling={remaining_capacity_to_quality_ceiling}")
    add_check("rows_to_aspirational_50k_expected", rows_to_aspirational_50k == ROWS_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_to_50k={rows_to_aspirational_50k}")

    add_check("validation_only", True, "critical", "promoted canonical validation only")
    add_check("file_copy_not_performed", True, "critical", "file_copy_performed=False")
    add_check("file_rename_not_performed", True, "critical", "file_rename_performed=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("active_pointer_not_updated", True, "critical", "active_pointer_updated=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
        validation_decision = "PROMOTED_CANONICAL_VALIDATION_BLOCKED_REVIEW_REQUIRED"
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
        validation_decision = "PROMOTED_CANONICAL_VALIDATED_READY_FOR_POINTER_DECISION_GATE"

    validation_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "validation_decision": validation_decision,
        "promotion_source_dataset": str(ASX_VALIDATED_CANDIDATE_DATASET),
        "promotion_source_rows": asx_validated_candidate_rows_before,
        "promotion_source_sha": asx_validated_candidate_sha_before,
        "promoted_canonical_dataset": str(PROMOTED_CANONICAL_DATASET),
        "promoted_canonical_rows": promoted_canonical_rows_before,
        "promoted_canonical_sha": promoted_canonical_sha_before,
        "promoted_matches_source_rows": promoted_matches_asx_rows,
        "promoted_matches_source_sha": promoted_matches_asx_sha,
        "promoted_matches_source_schema": promoted_matches_asx_schema,
        "promoted_matches_active_schema": promoted_matches_active_schema,
        "promoted_matches_current_schema": promoted_matches_current_schema,
        "schema_column_count": len(promoted_canonical_header),
        "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "active_canonical_rows": active_canonical_rows_before,
        "active_canonical_sha": active_canonical_sha_before,
        "active_canonical_replaced": False,
        "active_pointer_updated": False,
        "current_validated_candidate_rows": current_validated_candidate_rows_before,
        "asx_net_new_rows_vs_current_candidate": asx_net_new_rows,
        "uplift_vs_active_canonical_rows": uplift_vs_active_canonical_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": promoted_canonical_rows_before >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": promoted_canonical_rows_before <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": rows_above_quality_floor,
        "remaining_capacity_to_quality_ceiling": remaining_capacity_to_quality_ceiling,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k": rows_to_aspirational_50k,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    artifact_manifest_rows = [
        {
            "artifact": "promotion_source_asx_candidate",
            "path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "exists": asx_validated_candidate_exists,
            "rows": asx_validated_candidate_rows_before,
            "sha256": asx_validated_candidate_sha_before,
            "role": "immutable source used for promoted canonical file",
        },
        {
            "artifact": "promoted_canonical_versioned_file",
            "path": str(PROMOTED_CANONICAL_DATASET),
            "exists": promoted_canonical_exists,
            "rows": promoted_canonical_rows_before,
            "sha256": promoted_canonical_sha_before,
            "role": "validated promoted canonical file",
        },
        {
            "artifact": "active_canonical_rollback_reference",
            "path": str(ACTIVE_CANONICAL_DATASET),
            "exists": active_canonical_exists,
            "rows": active_canonical_rows_before,
            "sha256": active_canonical_sha_before,
            "role": "unchanged active canonical and rollback reference",
        },
        {
            "artifact": "current_validated_candidate_reference",
            "path": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "exists": current_validated_candidate_exists,
            "rows": current_validated_candidate_rows_before,
            "sha256": current_validated_candidate_sha_before,
            "role": "previous current candidate reference",
        },
    ]

    sha_control_rows = [
        {
            "control_id": "SHA_001",
            "artifact": "promoted_canonical",
            "expected_sha": PROMOTED_CANONICAL_SHA_EXPECTED,
            "actual_sha": promoted_canonical_sha_before,
            "matched": promoted_canonical_sha_before == PROMOTED_CANONICAL_SHA_EXPECTED,
            "detail": "Promoted file SHA must equal ASX source SHA.",
        },
        {
            "control_id": "SHA_002",
            "artifact": "asx_source",
            "expected_sha": ASX_VALIDATED_CANDIDATE_SHA_EXPECTED,
            "actual_sha": asx_validated_candidate_sha_before,
            "matched": asx_validated_candidate_sha_before == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED,
            "detail": "ASX source SHA must remain unchanged.",
        },
        {
            "control_id": "SHA_003",
            "artifact": "active_canonical",
            "expected_sha": ACTIVE_CANONICAL_SHA_EXPECTED,
            "actual_sha": active_canonical_sha_before,
            "matched": active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED,
            "detail": "Active canonical must remain unchanged.",
        },
        {
            "control_id": "SHA_004",
            "artifact": "promoted_vs_asx_source",
            "expected_sha": asx_validated_candidate_sha_before,
            "actual_sha": promoted_canonical_sha_before,
            "matched": promoted_matches_asx_sha,
            "detail": "Promoted file must be byte-identical to ASX source.",
        },
    ]

    schema_control_rows = [
        {
            "control_id": "SCHEMA_001",
            "artifact": "promoted_canonical",
            "column_count": len(promoted_canonical_header),
            "matches_asx_source": promoted_matches_asx_schema,
            "matches_active_canonical": promoted_matches_active_schema,
            "matches_current_candidate": promoted_matches_current_schema,
            "columns": ";".join(promoted_canonical_header),
        },
        {
            "control_id": "SCHEMA_002",
            "artifact": "asx_source",
            "column_count": len(asx_validated_candidate_header),
            "matches_asx_source": True,
            "matches_active_canonical": asx_validated_candidate_header == active_canonical_header,
            "matches_current_candidate": asx_validated_candidate_header == current_validated_candidate_header,
            "columns": ";".join(asx_validated_candidate_header),
        },
        {
            "control_id": "SCHEMA_003",
            "artifact": "active_canonical",
            "column_count": len(active_canonical_header),
            "matches_asx_source": active_canonical_header == asx_validated_candidate_header,
            "matches_active_canonical": True,
            "matches_current_candidate": active_canonical_header == current_validated_candidate_header,
            "columns": ";".join(active_canonical_header),
        },
    ]

    content_control_rows = [
        {
            "control_id": "CONTENT_001",
            "control": "promoted_rows_match_source",
            "passed": promoted_matches_asx_rows,
            "detail": f"promoted={promoted_canonical_rows_before};source={asx_validated_candidate_rows_before}",
        },
        {
            "control_id": "CONTENT_002",
            "control": "promoted_sha_match_source",
            "passed": promoted_matches_asx_sha,
            "detail": f"promoted={promoted_canonical_sha_before};source={asx_validated_candidate_sha_before}",
        },
        {
            "control_id": "CONTENT_003",
            "control": "promoted_schema_match_source",
            "passed": promoted_matches_asx_schema,
            "detail": f"promoted_columns={len(promoted_canonical_header)};source_columns={len(asx_validated_candidate_header)}",
        },
        {
            "control_id": "CONTENT_004",
            "control": "quality_floor_and_ceiling",
            "passed": promoted_canonical_rows_before >= QUALITY_FLOOR_TARGET and promoted_canonical_rows_before <= QUALITY_CEILING_TARGET,
            "detail": f"rows={promoted_canonical_rows_before};floor={QUALITY_FLOOR_TARGET};ceiling={QUALITY_CEILING_TARGET}",
        },
    ]

    rollback_control_rows = [
        {
            "rollback_id": "ROLLBACK_001",
            "scope": "active_canonical",
            "reference_path": str(ACTIVE_CANONICAL_DATASET),
            "reference_rows": active_canonical_rows_before,
            "reference_sha": active_canonical_sha_before,
            "status": "AVAILABLE_UNCHANGED" if active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED else "DRIFT_DETECTED",
            "rollback_action": "Continue using active canonical v2_14e if pointer decision is not approved.",
        },
        {
            "rollback_id": "ROLLBACK_002",
            "scope": "asx_validated_candidate",
            "reference_path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "reference_rows": asx_validated_candidate_rows_before,
            "reference_sha": asx_validated_candidate_sha_before,
            "status": "AVAILABLE_UNCHANGED" if asx_validated_candidate_sha_before == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED else "DRIFT_DETECTED",
            "rollback_action": "Regenerate promoted file from this exact source if promoted file is removed.",
        },
        {
            "rollback_id": "ROLLBACK_003",
            "scope": "promoted_canonical_file",
            "reference_path": str(PROMOTED_CANONICAL_DATASET),
            "reference_rows": promoted_canonical_rows_before,
            "reference_sha": promoted_canonical_sha_before,
            "status": "VALIDATED_READY_FOR_POINTER_DECISION" if critical_failed == 0 else "VALIDATION_FAILED",
            "rollback_action": "Do not update pointers unless explicit pointer decision gate approves activation.",
        },
    ]

    activation_gate_rows = [
        {
            "gate_id": "ACTIVATION_001",
            "gate": "promoted_file_validated",
            "passed": critical_failed == 0,
            "detail": f"critical_failed_checks={critical_failed};warning_failed_checks={warning_failed}",
            "required_before_pointer_update": True,
        },
        {
            "gate_id": "ACTIVATION_002",
            "gate": "active_canonical_still_rollback",
            "passed": active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED,
            "detail": active_canonical_sha_before,
            "required_before_pointer_update": True,
        },
        {
            "gate_id": "ACTIVATION_003",
            "gate": "pointer_update_not_yet_performed",
            "passed": True,
            "detail": "active_pointer_updated=False",
            "required_before_pointer_update": True,
        },
        {
            "gate_id": "ACTIVATION_004",
            "gate": "next_phase_must_be_decision_gate",
            "passed": recommended_next_phase == NEXT_PHASE,
            "detail": recommended_next_phase,
            "required_before_pointer_update": True,
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "pointer",
            "action": "run_active_pointer_decision_gate",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Promoted file has been validated; activation still requires an explicit decision gate.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "decision only; no silent pointer update; no scoring/OpenAI/broker/full59k",
        },
        {
            "action_order": 2,
            "action_scope": "rollback",
            "action": "preserve_active_canonical_rollback_reference",
            "priority": "high",
            "reason": "Active canonical remains unchanged and should remain available until pointer activation is explicitly approved.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "abort if active canonical SHA drifts",
        },
        {
            "action_order": 3,
            "action_scope": "quality",
            "action": "keep_provider_expansion_frozen",
            "priority": "medium",
            "reason": "Promoted file achieves 42k floor and respects 45k ceiling.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "50k aspirational only; full59k deprecated",
        },
    ]

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in validation_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "exists", "rows", "sha256", "role"])
    write_csv(SHA_CONTROLS_CSV, sha_control_rows, ["control_id", "artifact", "expected_sha", "actual_sha", "matched", "detail"])
    write_csv(SCHEMA_CONTROLS_CSV, schema_control_rows, ["control_id", "artifact", "column_count", "matches_asx_source", "matches_active_canonical", "matches_current_candidate", "columns"])
    write_csv(CONTENT_CONTROLS_CSV, content_control_rows, ["control_id", "control", "passed", "detail"])
    write_csv(ROLLBACK_CONTROLS_CSV, rollback_control_rows, ["rollback_id", "scope", "reference_path", "reference_rows", "reference_sha", "status", "rollback_action"])
    write_csv(ACTIVATION_GATE_CSV, activation_gate_rows, ["gate_id", "gate", "passed", "detail", "required_before_pointer_update"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "validation_summary": validation_summary,
        "artifact_manifest": artifact_manifest_rows,
        "sha_controls": sha_control_rows,
        "schema_controls": schema_control_rows,
        "content_controls": content_control_rows,
        "rollback_controls": rollback_control_rows,
        "activation_gate": activation_gate_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "promoted_canonical_validation_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "operational_42k_floor_achieved": promoted_canonical_rows_before >= QUALITY_FLOOR_TARGET,
            "operational_45k_ceiling_respected": promoted_canonical_rows_before <= QUALITY_CEILING_TARGET,
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
            "promotion_dry_run_performed": False,
            "controlled_promoted_file_creation_performed": False,
            "file_copy_performed": False,
            "file_rename_performed": False,
            "promoted_file_created_in_this_phase": False,
            "promoted_file_exists": promoted_canonical_exists,
            "promoted_file_validated": critical_failed == 0,
            "promoted_file_matches_source_sha": promoted_matches_asx_sha,
            "promoted_file_matches_source_rows": promoted_matches_asx_rows,
            "promoted_file_schema_matches_source": promoted_matches_asx_schema,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "active_canonical_replaced": False,
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

    artifact_lines = "\n".join(
        f"- `{row['artifact']}` — `{row['path']}` — exists `{row['exists']}` — rows `{row['rows']}` — SHA `{row['sha256']}`"
        for row in artifact_manifest_rows
    )

    sha_lines = "\n".join(
        f"- `{row['control_id']}` — {row['artifact']}: {'PASS' if row['matched'] else 'FAIL'} — {row['actual_sha']}"
        for row in sha_control_rows
    )

    schema_lines = "\n".join(
        f"- `{row['control_id']}` — {row['artifact']} — columns `{row['column_count']}` — matches ASX `{row['matches_asx_source']}`"
        for row in schema_control_rows
    )

    content_lines = "\n".join(
        f"- `{row['control_id']}` — {row['control']}: {'PASS' if row['passed'] else 'FAIL'} — {row['detail']}"
        for row in content_control_rows
    )

    activation_lines = "\n".join(
        f"- `{row['gate_id']}` — {row['gate']}: {'PASS' if row['passed'] else 'FAIL'} — {row['detail']}"
        for row in activation_gate_rows
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

v2.20N validates the promoted canonical file created in v2.20M.

Promoted canonical file:

`{PROMOTED_CANONICAL_DATASET}`

Promotion source:

`{ASX_VALIDATED_CANDIDATE_DATASET}`

The promoted file is validated against source rows, SHA and schema. This phase does **not** create files, copy files, rename files, overwrite canonical, update active pointers, recalculate scoring, call OpenAI, call brokers, or launch full59k.

## Validation summary

- Validation decision: `{validation_decision}`
- Promoted canonical rows: `{promoted_canonical_rows_before}`
- Promoted canonical SHA256: `{promoted_canonical_sha_before}`
- Promotion source rows: `{asx_validated_candidate_rows_before}`
- Promotion source SHA256: `{asx_validated_candidate_sha_before}`
- Promoted rows match source: `{promoted_matches_asx_rows}`
- Promoted SHA matches source: `{promoted_matches_asx_sha}`
- Promoted schema matches source: `{promoted_matches_asx_schema}`
- Promoted schema matches active canonical: `{promoted_matches_active_schema}`
- Schema column count: `{len(promoted_canonical_header)}`
- Active canonical rows: `{active_canonical_rows_before}`
- Active canonical SHA256: `{active_canonical_sha_before}`
- Active canonical replaced: `False`
- Active pointer updated: `False`
- ASX net-new rows vs current candidate: `{asx_net_new_rows}`
- Uplift vs active canonical rows: `{uplift_vs_active_canonical_rows}`
- Quality floor crossed: `{promoted_canonical_rows_before >= QUALITY_FLOOR_TARGET}`
- Quality ceiling respected: `{promoted_canonical_rows_before <= QUALITY_CEILING_TARGET}`
- Rows above 42k floor: `{rows_above_quality_floor}`
- Remaining capacity to 45k ceiling: `{remaining_capacity_to_quality_ceiling}`
- Rows to 50k aspirational: `{rows_to_aspirational_50k}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Artifact manifest

{artifact_lines}

## SHA controls

{sha_lines}

## Schema controls

{schema_lines}

## Content controls

{content_lines}

## Activation gate

{activation_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Promoted canonical validation only: true
- File copy performed: false
- File rename performed: false
- Promoted file created in this phase: false
- Promoted file exists: {promoted_canonical_exists}
- Promoted file validated: {critical_failed == 0}
- Canonical dataset modified: false
- Active canonical replaced: false
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

    print("v2.20N ASX promoted canonical validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in validation_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("ARTIFACT_MANIFEST:")
    for row in artifact_manifest_rows:
        print(f"- {row['artifact']}: exists={row['exists']} rows={row['rows']} sha={row['sha256']}")
    print("")
    print("SHA_CONTROLS:")
    for row in sha_control_rows:
        print(f"- {row['control_id']}: {row['artifact']} matched={row['matched']} sha={row['actual_sha']}")
    print("")
    print("SCHEMA_CONTROLS:")
    for row in schema_control_rows:
        print(f"- {row['control_id']}: {row['artifact']} columns={row['column_count']} matches_asx={row['matches_asx_source']}")
    print("")
    print("CONTENT_CONTROLS:")
    for row in content_control_rows:
        print(f"- {row['control_id']}: {row['control']} - {'PASS' if row['passed'] else 'FAIL'} - {row['detail']}")
    print("")
    print("ACTIVATION_GATE:")
    for row in activation_gate_rows:
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
