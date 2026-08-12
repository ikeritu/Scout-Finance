from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20M"
PHASE = "ASX Controlled Promoted File Creation"
PHASE_TYPE = "controlled-promoted-file-creation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PRE_HKEX_CURRENT_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"

PROMOTED_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"

V220G_JSON = OUTPUT_DIR / "asx_expanded_rebuild_candidate_v2_20g.json"
V220H_JSON = OUTPUT_DIR / "asx_expanded_validation_v2_20h.json"
V220I_JSON = OUTPUT_DIR / "asx_closure_report_v2_20i.json"
V220J_JSON = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_v2_20j.json"
V220K_JSON = OUTPUT_DIR / "asx_canonical_promotion_plan_v2_20k.json"
V220L_JSON = OUTPUT_DIR / "asx_canonical_promotion_dry_run_v2_20l.json"

REPORT_JSON = OUTPUT_DIR / "asx_controlled_promoted_file_creation_v2_20m.json"
REPORT_MD = OUTPUT_DIR / "asx_controlled_promoted_file_creation_v2_20m.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_controlled_promoted_file_creation_summary_v2_20m.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_controlled_promoted_file_creation_checks_v2_20m.csv"
MANIFEST_CSV = OUTPUT_DIR / "asx_controlled_promoted_file_creation_manifest_v2_20m.csv"
COPY_CONTROLS_CSV = OUTPUT_DIR / "asx_controlled_promoted_file_creation_copy_controls_v2_20m.csv"
ROLLBACK_CONTROLS_CSV = OUTPUT_DIR / "asx_controlled_promoted_file_creation_rollback_controls_v2_20m.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_controlled_promoted_file_creation_next_actions_v2_20m.csv"

EXPECTED_V220G_STATUS = "ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220H_STATUS = "ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED"
EXPECTED_V220I_STATUS = "ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED"
EXPECTED_V220J_STATUS = "ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220K_STATUS = "ASX_CANONICAL_PROMOTION_PLAN_COMPLETED_DRY_RUN_READY_42708_ROWS_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220L_STATUS = "ASX_CANONICAL_PROMOTION_DRY_RUN_COMPLETED_PROMOTION_EXECUTION_READY_42708_ROWS_CANONICAL_UNCHANGED_PROMOTED_FILE_NOT_CREATED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED = 40996
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392
ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED = 42708
PROMOTED_CANONICAL_ROWS_EXPECTED = 42708
ASX_NET_NEW_ROWS_EXPECTED = 1316
UPLIFT_VS_ACTIVE_CANONICAL_EXPECTED = 4421

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"
ASX_VALIDATED_CANDIDATE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
PROMOTED_CANONICAL_SHA_EXPECTED = ASX_VALIDATED_CANDIDATE_SHA_EXPECTED

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_ABOVE_QUALITY_FLOOR_EXPECTED = 708
REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED = 2292
ROWS_TO_ASPIRATIONAL_50K_EXPECTED = 7292

STATUS_SUCCESS = "ASX_CONTROLLED_PROMOTED_FILE_CREATION_COMPLETED_42708_ROWS_PROMOTED_FILE_CREATED_CANONICAL_UNCHANGED_POINTER_UNCHANGED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_CONTROLLED_PROMOTED_FILE_CREATION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20N - ASX Promoted Canonical Validation"
NEXT_PHASE_REVIEW = "v2.20M_REVIEW - ASX Controlled Promoted File Creation Review"


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
    report_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        MANIFEST_CSV,
        COPY_CONTROLS_CSV,
        ROLLBACK_CONTROLS_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in report_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if PROMOTED_CANONICAL_DATASET.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: promoted target already exists: {PROMOTED_CANONICAL_DATASET}")

    target_exists_before = PROMOTED_CANONICAL_DATASET.exists()

    v220g = read_json(V220G_JSON)
    v220h = read_json(V220H_JSON)
    v220i = read_json(V220I_JSON)
    v220j = read_json(V220J_JSON)
    v220k = read_json(V220K_JSON)
    v220l = read_json(V220L_JSON)

    v220l_summary = v220l.get("dry_run_summary", {})

    active_canonical_rows_before = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_rows_before = count_csv_rows(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_rows_before = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_rows_before = count_csv_rows(ASX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_header_before = read_csv_header(ACTIVE_CANONICAL_DATASET)
    current_validated_candidate_header_before = read_csv_header(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_header_before = read_csv_header(ASX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_before = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_sha_before = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)

    schema_matches_active_canonical_before = active_canonical_header_before == asx_validated_candidate_header_before
    schema_matches_current_candidate_before = current_validated_candidate_header_before == asx_validated_candidate_header_before

    preflight_checks: list[dict[str, Any]] = []
    critical_failed = 0
    warning_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed, warning_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        if severity == "warning" and not passed:
            warning_failed += 1
        preflight_checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_20g_report_exists", V220G_JSON.exists(), "critical", str(V220G_JSON))
    add_check("v2_20h_report_exists", V220H_JSON.exists(), "critical", str(V220H_JSON))
    add_check("v2_20i_report_exists", V220I_JSON.exists(), "critical", str(V220I_JSON))
    add_check("v2_20j_report_exists", V220J_JSON.exists(), "critical", str(V220J_JSON))
    add_check("v2_20k_report_exists", V220K_JSON.exists(), "critical", str(V220K_JSON))
    add_check("v2_20l_report_exists", V220L_JSON.exists(), "critical", str(V220L_JSON))

    add_check("v2_20g_status_expected", v220g.get("status") == EXPECTED_V220G_STATUS, "critical", str(v220g.get("status")))
    add_check("v2_20h_status_expected", v220h.get("status") == EXPECTED_V220H_STATUS, "critical", str(v220h.get("status")))
    add_check("v2_20i_status_expected", v220i.get("status") == EXPECTED_V220I_STATUS, "critical", str(v220i.get("status")))
    add_check("v2_20j_status_expected", v220j.get("status") == EXPECTED_V220J_STATUS, "critical", str(v220j.get("status")))
    add_check("v2_20k_status_expected", v220k.get("status") == EXPECTED_V220K_STATUS, "critical", str(v220k.get("status")))
    add_check("v2_20l_status_expected", v220l.get("status") == EXPECTED_V220L_STATUS, "critical", str(v220l.get("status")))
    add_check("v2_20l_next_phase_expected", v220l.get("recommended_next_phase") == "v2.20M - ASX Controlled Promoted File Creation", "critical", str(v220l.get("recommended_next_phase")))

    add_check("v2_20l_dry_run_decision_expected", v220l_summary.get("dry_run_decision") == "PROMOTION_DRY_RUN_PASSED_EXECUTION_READY", "critical", str(v220l_summary.get("dry_run_decision")))
    add_check("v2_20l_promoted_file_not_created", bool(v220l_summary.get("promoted_file_created")) is False, "critical", f"promoted_file_created={v220l_summary.get('promoted_file_created')}")
    add_check("v2_20l_active_pointer_not_updated", bool(v220l_summary.get("active_pointer_updated")) is False, "critical", f"active_pointer_updated={v220l_summary.get('active_pointer_updated')}")

    add_check("source_candidate_exists", ASX_VALIDATED_CANDIDATE_DATASET.exists(), "critical", str(ASX_VALIDATED_CANDIDATE_DATASET))
    add_check("active_canonical_exists", ACTIVE_CANONICAL_DATASET.exists(), "critical", str(ACTIVE_CANONICAL_DATASET))
    add_check("promoted_target_absent_before_creation", not target_exists_before, "critical", f"target_exists_before={target_exists_before}")

    add_check("active_canonical_rows_expected_before", active_canonical_rows_before == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows_before}")
    add_check("pre_hkex_current_candidate_rows_expected_before", pre_hkex_current_candidate_rows_before == PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED, "critical", f"pre_hkex_rows={pre_hkex_current_candidate_rows_before}")
    add_check("current_validated_candidate_rows_expected_before", current_validated_candidate_rows_before == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_validated_rows={current_validated_candidate_rows_before}")
    add_check("asx_validated_candidate_rows_expected_before", asx_validated_candidate_rows_before == ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"asx_validated_rows={asx_validated_candidate_rows_before}")

    add_check("active_canonical_sha_expected_before", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("pre_hkex_current_candidate_sha_expected_before", pre_hkex_current_candidate_sha_before == PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED, "critical", pre_hkex_current_candidate_sha_before)
    add_check("current_validated_candidate_sha_expected_before", current_validated_candidate_sha_before == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", current_validated_candidate_sha_before)
    add_check("asx_validated_candidate_sha_expected_before", asx_validated_candidate_sha_before == ASX_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", asx_validated_candidate_sha_before)

    add_check("schema_column_count_expected_before", len(asx_validated_candidate_header_before) == 33, "critical", f"asx_columns={len(asx_validated_candidate_header_before)}")
    add_check("schema_matches_active_canonical_before", schema_matches_active_canonical_before, "critical", f"schema_matches_active_canonical={schema_matches_active_canonical_before}")
    add_check("schema_matches_current_candidate_before", schema_matches_current_candidate_before, "critical", f"schema_matches_current_candidate={schema_matches_current_candidate_before}")

    copy_performed = False
    copy_blocked = critical_failed > 0

    if not copy_blocked:
        shutil.copyfile(ASX_VALIDATED_CANDIDATE_DATASET, PROMOTED_CANONICAL_DATASET)
        copy_performed = True

    target_exists_after = PROMOTED_CANONICAL_DATASET.exists()

    active_canonical_rows_after = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_rows_after = count_csv_rows(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_rows_after = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_rows_after = count_csv_rows(ASX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_after = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_validated_candidate_sha_after = sha256_file(ASX_VALIDATED_CANDIDATE_DATASET)

    promoted_canonical_rows = count_csv_rows(PROMOTED_CANONICAL_DATASET) if target_exists_after else 0
    promoted_canonical_sha = sha256_file(PROMOTED_CANONICAL_DATASET) if target_exists_after else ""
    promoted_canonical_header = read_csv_header(PROMOTED_CANONICAL_DATASET) if target_exists_after else []

    schema_matches_source_after = promoted_canonical_header == asx_validated_candidate_header_before if target_exists_after else False
    promoted_matches_source_sha = promoted_canonical_sha == asx_validated_candidate_sha_after if target_exists_after else False
    promoted_matches_source_rows = promoted_canonical_rows == asx_validated_candidate_rows_after if target_exists_after else False

    asx_net_new_rows = asx_validated_candidate_rows_after - current_validated_candidate_rows_after
    uplift_vs_active_canonical_rows = asx_validated_candidate_rows_after - active_canonical_rows_after
    rows_above_quality_floor = promoted_canonical_rows - QUALITY_FLOOR_TARGET
    remaining_capacity_to_quality_ceiling = QUALITY_CEILING_TARGET - promoted_canonical_rows
    rows_to_aspirational_50k = ASPIRATIONAL_TARGET - promoted_canonical_rows

    add_check("copy_performed", copy_performed, "critical", f"copy_performed={copy_performed}")
    add_check("promoted_target_exists_after_creation", target_exists_after, "critical", f"target_exists_after={target_exists_after}")
    add_check("promoted_rows_expected", promoted_canonical_rows == PROMOTED_CANONICAL_ROWS_EXPECTED, "critical", f"promoted_rows={promoted_canonical_rows}")
    add_check("promoted_sha_expected", promoted_canonical_sha == PROMOTED_CANONICAL_SHA_EXPECTED, "critical", promoted_canonical_sha)
    add_check("promoted_rows_match_source", promoted_matches_source_rows, "critical", f"promoted={promoted_canonical_rows};source={asx_validated_candidate_rows_after}")
    add_check("promoted_sha_matches_source", promoted_matches_source_sha, "critical", f"promoted={promoted_canonical_sha};source={asx_validated_candidate_sha_after}")
    add_check("promoted_schema_matches_source", schema_matches_source_after, "critical", f"schema_matches_source={schema_matches_source_after}")
    add_check("promoted_column_count_expected", len(promoted_canonical_header) == 33, "critical", f"promoted_columns={len(promoted_canonical_header)}")

    add_check("active_canonical_rows_unchanged", active_canonical_rows_before == active_canonical_rows_after, "critical", f"before={active_canonical_rows_before};after={active_canonical_rows_after}")
    add_check("pre_hkex_current_candidate_rows_unchanged", pre_hkex_current_candidate_rows_before == pre_hkex_current_candidate_rows_after, "critical", f"before={pre_hkex_current_candidate_rows_before};after={pre_hkex_current_candidate_rows_after}")
    add_check("current_validated_candidate_rows_unchanged", current_validated_candidate_rows_before == current_validated_candidate_rows_after, "critical", f"before={current_validated_candidate_rows_before};after={current_validated_candidate_rows_after}")
    add_check("asx_validated_candidate_rows_unchanged", asx_validated_candidate_rows_before == asx_validated_candidate_rows_after, "critical", f"before={asx_validated_candidate_rows_before};after={asx_validated_candidate_rows_after}")

    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("pre_hkex_current_candidate_sha_unchanged", pre_hkex_current_candidate_sha_before == pre_hkex_current_candidate_sha_after, "critical", "pre-HKEX current candidate sha unchanged")
    add_check("current_validated_candidate_sha_unchanged", current_validated_candidate_sha_before == current_validated_candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("asx_validated_candidate_sha_unchanged", asx_validated_candidate_sha_before == asx_validated_candidate_sha_after, "critical", "ASX validated candidate sha unchanged")

    add_check("asx_net_new_rows_expected", asx_net_new_rows == ASX_NET_NEW_ROWS_EXPECTED, "critical", f"asx_net_new_rows={asx_net_new_rows}")
    add_check("uplift_vs_active_canonical_expected", uplift_vs_active_canonical_rows == UPLIFT_VS_ACTIVE_CANONICAL_EXPECTED, "critical", f"uplift_vs_active_canonical={uplift_vs_active_canonical_rows}")
    add_check("quality_floor_crossed", promoted_canonical_rows >= QUALITY_FLOOR_TARGET, "critical", f"promoted_rows={promoted_canonical_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", promoted_canonical_rows <= QUALITY_CEILING_TARGET, "critical", f"promoted_rows={promoted_canonical_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_above_quality_floor_expected", rows_above_quality_floor == ROWS_ABOVE_QUALITY_FLOOR_EXPECTED, "critical", f"rows_above_floor={rows_above_quality_floor}")
    add_check("remaining_capacity_to_quality_ceiling_expected", remaining_capacity_to_quality_ceiling == REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED, "critical", f"capacity_to_ceiling={remaining_capacity_to_quality_ceiling}")
    add_check("rows_to_aspirational_50k_expected", rows_to_aspirational_50k == ROWS_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_to_50k={rows_to_aspirational_50k}")

    add_check("controlled_file_creation_only", True, "critical", "controlled promoted file creation only")
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
        creation_decision = "PROMOTED_FILE_CREATION_REVIEW_REQUIRED"
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
        creation_decision = "PROMOTED_FILE_CREATED_READY_FOR_VALIDATION"

    creation_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "creation_decision": creation_decision,
        "promotion_source_dataset": str(ASX_VALIDATED_CANDIDATE_DATASET),
        "promotion_source_rows": asx_validated_candidate_rows_after,
        "promotion_source_sha": asx_validated_candidate_sha_after,
        "promoted_canonical_dataset": str(PROMOTED_CANONICAL_DATASET),
        "promoted_canonical_rows": promoted_canonical_rows,
        "promoted_canonical_sha": promoted_canonical_sha,
        "promoted_matches_source_rows": promoted_matches_source_rows,
        "promoted_matches_source_sha": promoted_matches_source_sha,
        "promoted_schema_matches_source": schema_matches_source_after,
        "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "active_canonical_rows": active_canonical_rows_after,
        "active_canonical_sha": active_canonical_sha_after,
        "active_canonical_replaced": False,
        "active_pointer_updated": False,
        "target_exists_before": target_exists_before,
        "target_exists_after": target_exists_after,
        "copy_performed": copy_performed,
        "current_validated_candidate_rows": current_validated_candidate_rows_after,
        "asx_net_new_rows_vs_current_candidate": asx_net_new_rows,
        "uplift_vs_active_canonical_rows": uplift_vs_active_canonical_rows,
        "schema_column_count": len(promoted_canonical_header),
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": promoted_canonical_rows >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": promoted_canonical_rows <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": rows_above_quality_floor,
        "remaining_capacity_to_quality_ceiling": remaining_capacity_to_quality_ceiling,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k": rows_to_aspirational_50k,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    manifest_rows = [
        {
            "artifact": "promotion_source_asx_candidate",
            "path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "rows": asx_validated_candidate_rows_after,
            "sha256": asx_validated_candidate_sha_after,
            "role": "immutable source for promoted file",
        },
        {
            "artifact": "promoted_canonical_versioned_file",
            "path": str(PROMOTED_CANONICAL_DATASET),
            "rows": promoted_canonical_rows,
            "sha256": promoted_canonical_sha,
            "role": "new versioned promoted canonical file",
        },
        {
            "artifact": "active_canonical_rollback_reference",
            "path": str(ACTIVE_CANONICAL_DATASET),
            "rows": active_canonical_rows_after,
            "sha256": active_canonical_sha_after,
            "role": "unchanged rollback source",
        },
        {
            "artifact": "current_validated_candidate_reference",
            "path": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "rows": current_validated_candidate_rows_after,
            "sha256": current_validated_candidate_sha_after,
            "role": "previous current candidate reference",
        },
    ]

    copy_control_rows = [
        {
            "control_id": "COPY_001",
            "control": "target_absent_before_creation",
            "passed": not target_exists_before,
            "detail": str(PROMOTED_CANONICAL_DATASET),
        },
        {
            "control_id": "COPY_002",
            "control": "copyfile_executed",
            "passed": copy_performed,
            "detail": f"{ASX_VALIDATED_CANDIDATE_DATASET} -> {PROMOTED_CANONICAL_DATASET}",
        },
        {
            "control_id": "COPY_003",
            "control": "target_exists_after_creation",
            "passed": target_exists_after,
            "detail": str(PROMOTED_CANONICAL_DATASET),
        },
        {
            "control_id": "COPY_004",
            "control": "target_sha_matches_source",
            "passed": promoted_matches_source_sha,
            "detail": f"target={promoted_canonical_sha};source={asx_validated_candidate_sha_after}",
        },
        {
            "control_id": "COPY_005",
            "control": "target_rows_match_source",
            "passed": promoted_matches_source_rows,
            "detail": f"target={promoted_canonical_rows};source={asx_validated_candidate_rows_after}",
        },
        {
            "control_id": "COPY_006",
            "control": "target_schema_matches_source",
            "passed": schema_matches_source_after,
            "detail": f"columns={len(promoted_canonical_header)}",
        },
    ]

    rollback_control_rows = [
        {
            "rollback_id": "ROLLBACK_001",
            "scope": "active_canonical",
            "reference_path": str(ACTIVE_CANONICAL_DATASET),
            "reference_rows": active_canonical_rows_after,
            "reference_sha": active_canonical_sha_after,
            "status": "AVAILABLE_UNCHANGED" if active_canonical_sha_before == active_canonical_sha_after else "DRIFT_DETECTED",
            "rollback_action": "Continue to use active canonical v2_14e if promoted file validation fails.",
        },
        {
            "rollback_id": "ROLLBACK_002",
            "scope": "asx_validated_candidate",
            "reference_path": str(ASX_VALIDATED_CANDIDATE_DATASET),
            "reference_rows": asx_validated_candidate_rows_after,
            "reference_sha": asx_validated_candidate_sha_after,
            "status": "AVAILABLE_UNCHANGED" if asx_validated_candidate_sha_before == asx_validated_candidate_sha_after else "DRIFT_DETECTED",
            "rollback_action": "Regenerate promoted file from this exact source if needed.",
        },
        {
            "rollback_id": "ROLLBACK_003",
            "scope": "promoted_canonical_file",
            "reference_path": str(PROMOTED_CANONICAL_DATASET),
            "reference_rows": promoted_canonical_rows,
            "reference_sha": promoted_canonical_sha,
            "status": "CREATED_NEEDS_POST_VALIDATION" if target_exists_after else "NOT_CREATED",
            "rollback_action": "Delete or ignore promoted file if v2.20N validation fails; do not update pointers.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "validation",
            "action": "validate_promoted_canonical_file",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Promoted file was created and must be validated against the ASX source before any pointer decision.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "validate rows/SHA/schema; no scoring/OpenAI/broker/full59k",
        },
        {
            "action_order": 2,
            "action_scope": "pointer",
            "action": "keep_active_pointer_unchanged",
            "priority": "high",
            "reason": "File creation does not imply operational activation.",
            "recommended_phase": "post-v2.20N explicit pointer phase",
            "guardrails": "separate approval required",
        },
        {
            "action_order": 3,
            "action_scope": "rollback",
            "action": "preserve_v2_14e_as_rollback_reference",
            "priority": "high",
            "reason": "Active canonical remains unchanged and available as rollback source.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "abort if active canonical SHA changes unexpectedly",
        },
    ]

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in creation_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, preflight_checks, ["check", "passed", "severity", "detail"])
    write_csv(MANIFEST_CSV, manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(COPY_CONTROLS_CSV, copy_control_rows, ["control_id", "control", "passed", "detail"])
    write_csv(ROLLBACK_CONTROLS_CSV, rollback_control_rows, ["rollback_id", "scope", "reference_path", "reference_rows", "reference_sha", "status", "rollback_action"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "creation_summary": creation_summary,
        "artifact_manifest": manifest_rows,
        "copy_controls": copy_control_rows,
        "rollback_controls": rollback_control_rows,
        "checks": preflight_checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "controlled_promoted_file_creation_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "operational_42k_floor_achieved": promoted_canonical_rows >= QUALITY_FLOOR_TARGET,
            "operational_45k_ceiling_respected": promoted_canonical_rows <= QUALITY_CEILING_TARGET,
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
            "file_copy_performed": copy_performed,
            "file_rename_performed": False,
            "promoted_file_created": target_exists_after,
            "promoted_file_matches_source_sha": promoted_matches_source_sha,
            "promoted_file_matches_source_rows": promoted_matches_source_rows,
            "promoted_file_schema_matches_source": schema_matches_source_after,
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
            "canonical_promotion_performed": True,
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
        for row in preflight_checks
    )

    manifest_lines = "\n".join(
        f"- `{row['artifact']}` — `{row['path']}` — rows `{row['rows']}` — SHA `{row['sha256']}`"
        for row in manifest_rows
    )

    copy_lines = "\n".join(
        f"- `{row['control_id']}` — {row['control']}: {'PASS' if row['passed'] else 'FAIL'} — {row['detail']}"
        for row in copy_control_rows
    )

    rollback_lines = "\n".join(
        f"- `{row['rollback_id']}` — {row['scope']} — {row['status']} — {row['rollback_action']}"
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

v2.20M creates the versioned promoted canonical file from the validated ASX candidate.

Promotion source:

`{ASX_VALIDATED_CANDIDATE_DATASET}`

Promoted canonical file created:

`{PROMOTED_CANONICAL_DATASET}`

This phase creates a versioned promoted file only. It does **not** overwrite `expanded_universe_v2_14e.csv`, does **not** update active pointers, does **not** recalculate scoring, does **not** call OpenAI, does **not** call brokers, and does **not** launch full59k.

## Creation summary

- Creation decision: `{creation_decision}`
- Copy performed: `{copy_performed}`
- Target existed before: `{target_exists_before}`
- Target exists after: `{target_exists_after}`
- Promotion source rows: `{asx_validated_candidate_rows_after}`
- Promotion source SHA256: `{asx_validated_candidate_sha_after}`
- Promoted canonical rows: `{promoted_canonical_rows}`
- Promoted canonical SHA256: `{promoted_canonical_sha}`
- Promoted rows match source: `{promoted_matches_source_rows}`
- Promoted SHA matches source: `{promoted_matches_source_sha}`
- Promoted schema matches source: `{schema_matches_source_after}`
- Active canonical rows: `{active_canonical_rows_after}`
- Active canonical SHA256: `{active_canonical_sha_after}`
- Active canonical replaced: `False`
- Active pointer updated: `False`
- ASX net-new rows vs current candidate: `{asx_net_new_rows}`
- Uplift vs active canonical rows: `{uplift_vs_active_canonical_rows}`
- Quality floor crossed: `{promoted_canonical_rows >= QUALITY_FLOOR_TARGET}`
- Quality ceiling respected: `{promoted_canonical_rows <= QUALITY_CEILING_TARGET}`
- Rows above 42k floor: `{rows_above_quality_floor}`
- Remaining capacity to 45k ceiling: `{remaining_capacity_to_quality_ceiling}`
- Rows to 50k aspirational: `{rows_to_aspirational_50k}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Artifact manifest

{manifest_lines}

## Copy controls

{copy_lines}

## Rollback controls

{rollback_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Controlled promoted file creation only: true
- File copy performed: {copy_performed}
- File rename performed: false
- Promoted file created: {target_exists_after}
- Promoted file matches source SHA: {promoted_matches_source_sha}
- Promoted file matches source rows: {promoted_matches_source_rows}
- Promoted file schema matches source: {schema_matches_source_after}
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

    print("v2.20M ASX controlled promoted file creation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CREATION_SUMMARY:")
    for key, value in creation_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("ARTIFACT_MANIFEST:")
    for row in manifest_rows:
        print(f"- {row['artifact']}: {row['path']} rows={row['rows']} sha={row['sha256']}")
    print("")
    print("COPY_CONTROLS:")
    for row in copy_control_rows:
        print(f"- {row['control_id']}: {row['control']} - {'PASS' if row['passed'] else 'FAIL'} - {row['detail']}")
    print("")
    print("ROLLBACK_CONTROLS:")
    for row in rollback_control_rows:
        print(f"- {row['rollback_id']}: {row['scope']} - {row['status']}")
    print("")
    print("CHECKS:")
    for row in preflight_checks:
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
