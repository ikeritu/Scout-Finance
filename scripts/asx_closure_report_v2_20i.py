from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20I"
PHASE = "ASX Closure Report"
PHASE_TYPE = "closure-report-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PRE_HKEX_CURRENT_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
ASX_EXPANDED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"

V220G_JSON = OUTPUT_DIR / "asx_expanded_rebuild_candidate_v2_20g.json"
V220H_JSON = OUTPUT_DIR / "asx_expanded_validation_v2_20h.json"

REPORT_JSON = OUTPUT_DIR / "asx_closure_report_v2_20i.json"
REPORT_MD = OUTPUT_DIR / "asx_closure_report_v2_20i.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_closure_report_summary_v2_20i.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_closure_report_checks_v2_20i.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "asx_closure_report_decision_register_v2_20i.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_closure_report_next_actions_v2_20i.csv"

EXPECTED_V220G_STATUS = "ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220H_STATUS = "ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED = 40996
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392
ASX_EXPANDED_CANDIDATE_ROWS_EXPECTED = 42708
ASX_NET_NEW_ROWS_EXPECTED = 1316

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"
ASX_EXPANDED_CANDIDATE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_ABOVE_QUALITY_FLOOR_EXPECTED = 708
REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED = 2292
ROWS_TO_ASPIRATIONAL_50K_EXPECTED = 7292

STATUS_SUCCESS = "ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_CLOSURE_REPORT_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20J - ASX Candidate Promotion Decision Gate"
NEXT_PHASE_REVIEW = "v2.20I_REVIEW - ASX Closure Report Review"


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
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220g = read_json(V220G_JSON)
    v220h = read_json(V220H_JSON)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_rows = count_csv_rows(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_expanded_candidate_rows = count_csv_rows(ASX_EXPANDED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_before = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_expanded_candidate_sha_before = sha256_file(ASX_EXPANDED_CANDIDATE_DATASET)

    v220g_summary = v220g.get("rebuild_summary", {})
    v220h_summary = v220h.get("validation_summary", {})

    asx_net_new_rows = int(v220h_summary.get("asx_appended_rows", -1))
    rows_above_quality_floor = asx_expanded_candidate_rows - QUALITY_FLOOR_TARGET
    remaining_capacity_to_quality_ceiling = QUALITY_CEILING_TARGET - asx_expanded_candidate_rows
    rows_to_aspirational_50k = ASPIRATIONAL_TARGET - asx_expanded_candidate_rows

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_after = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    asx_expanded_candidate_sha_after = sha256_file(ASX_EXPANDED_CANDIDATE_DATASET)

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
    add_check("v2_20g_status_expected", v220g.get("status") == EXPECTED_V220G_STATUS, "critical", str(v220g.get("status")))
    add_check("v2_20h_status_expected", v220h.get("status") == EXPECTED_V220H_STATUS, "critical", str(v220h.get("status")))
    add_check("v2_20g_next_phase_expected", v220g.get("recommended_next_phase") == "v2.20H - ASX Expanded Validation", "critical", str(v220g.get("recommended_next_phase")))
    add_check("v2_20h_next_phase_expected", v220h.get("recommended_next_phase") == "v2.20I - ASX Closure Report", "critical", str(v220h.get("recommended_next_phase")))

    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("pre_hkex_current_candidate_rows_expected", pre_hkex_current_candidate_rows == PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED, "critical", f"pre_hkex_rows={pre_hkex_current_candidate_rows}")
    add_check("current_validated_candidate_rows_expected", current_validated_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_validated_rows={current_validated_candidate_rows}")
    add_check("asx_expanded_candidate_rows_expected", asx_expanded_candidate_rows == ASX_EXPANDED_CANDIDATE_ROWS_EXPECTED, "critical", f"asx_expanded_rows={asx_expanded_candidate_rows}")
    add_check("asx_net_new_rows_expected", asx_net_new_rows == ASX_NET_NEW_ROWS_EXPECTED, "critical", f"asx_net_new_rows={asx_net_new_rows}")
    add_check("row_arithmetic_expected", current_validated_candidate_rows + asx_net_new_rows == asx_expanded_candidate_rows, "critical", f"{current_validated_candidate_rows}+{asx_net_new_rows}={asx_expanded_candidate_rows}")

    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("pre_hkex_current_candidate_sha_expected", pre_hkex_current_candidate_sha_before == PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED, "critical", pre_hkex_current_candidate_sha_before)
    add_check("current_validated_candidate_sha_expected", current_validated_candidate_sha_before == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", current_validated_candidate_sha_before)
    add_check("asx_expanded_candidate_sha_expected", asx_expanded_candidate_sha_before == ASX_EXPANDED_CANDIDATE_SHA_EXPECTED, "critical", asx_expanded_candidate_sha_before)

    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("pre_hkex_current_candidate_sha_unchanged", pre_hkex_current_candidate_sha_before == pre_hkex_current_candidate_sha_after, "critical", "pre-HKEX current candidate sha unchanged")
    add_check("current_validated_candidate_sha_unchanged", current_validated_candidate_sha_before == current_validated_candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("asx_expanded_candidate_sha_unchanged", asx_expanded_candidate_sha_before == asx_expanded_candidate_sha_after, "critical", "ASX expanded candidate sha unchanged")

    add_check("quality_floor_crossed", asx_expanded_candidate_rows >= QUALITY_FLOOR_TARGET, "critical", f"asx_expanded_rows={asx_expanded_candidate_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", asx_expanded_candidate_rows <= QUALITY_CEILING_TARGET, "critical", f"asx_expanded_rows={asx_expanded_candidate_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_above_quality_floor_expected", rows_above_quality_floor == ROWS_ABOVE_QUALITY_FLOOR_EXPECTED, "critical", f"rows_above_floor={rows_above_quality_floor}")
    add_check("remaining_capacity_to_quality_ceiling_expected", remaining_capacity_to_quality_ceiling == REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED, "critical", f"capacity_to_ceiling={remaining_capacity_to_quality_ceiling}")
    add_check("rows_to_aspirational_50k_expected", rows_to_aspirational_50k == ROWS_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_to_50k={rows_to_aspirational_50k}")

    add_check("v2_20h_critical_failed_checks_zero", int(v220h_summary.get("critical_failed_checks", -1)) == 0, "critical", f"critical_failed_checks={v220h_summary.get('critical_failed_checks')}")
    add_check("v2_20h_warning_failed_checks_zero", int(v220h_summary.get("warning_failed_checks", -1)) == 0, "warning", f"warning_failed_checks={v220h_summary.get('warning_failed_checks')}")
    add_check("v2_20h_schema_preserved", bool(v220h_summary.get("schema_preserved")) is True, "critical", f"schema_preserved={v220h_summary.get('schema_preserved')}")
    add_check("v2_20h_current_prefix_preserved", bool(v220h_summary.get("current_prefix_preserved")) is True, "critical", f"current_prefix_preserved={v220h_summary.get('current_prefix_preserved')}")
    add_check("v2_20h_appended_tail_matches", bool(v220h_summary.get("appended_tail_matches_appended_rows")) is True, "critical", f"appended_tail_matches={v220h_summary.get('appended_tail_matches_appended_rows')}")
    add_check("v2_20h_duplicate_appended_tickers_zero", int(v220h_summary.get("duplicate_appended_tickers", -1)) == 0, "critical", f"duplicate_appended_tickers={v220h_summary.get('duplicate_appended_tickers')}")
    add_check("v2_20h_duplicate_appended_isins_zero", int(v220h_summary.get("duplicate_appended_isins", -1)) == 0, "warning", f"duplicate_appended_isins={v220h_summary.get('duplicate_appended_isins')}")
    add_check("v2_20h_appended_tickers_already_current_zero", int(v220h_summary.get("appended_tickers_already_current", -1)) == 0, "critical", f"appended_tickers_already_current={v220h_summary.get('appended_tickers_already_current')}")
    add_check("v2_20h_appended_isins_already_current_zero", int(v220h_summary.get("appended_isins_already_current", -1)) == 0, "warning", f"appended_isins_already_current={v220h_summary.get('appended_isins_already_current')}")

    add_check("closure_report_only", True, "critical", "closure report only")
    add_check("network_download_not_performed", True, "critical", "network_download_performed=False")
    add_check("raw_acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("raw_validation_not_performed", True, "critical", "raw_validation_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("candidate_validation_not_performed", True, "critical", "candidate_validation_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("expanded_validation_not_performed", True, "critical", "expanded_validation_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("pre_hkex_current_candidate_dataset_not_modified", True, "critical", "pre_hkex_current_candidate_dataset_modified=False")
    add_check("current_validated_candidate_dataset_not_modified", True, "critical", "current_validated_candidate_dataset_modified=False")
    add_check("asx_expanded_candidate_dataset_not_modified", True, "critical", "asx_expanded_candidate_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE

    closure_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "closure_decision": "ASX_PROVIDER_ROUTE_CLOSED_SUCCESSFULLY" if critical_failed == 0 else "ASX_PROVIDER_ROUTE_REVIEW_REQUIRED",
        "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "active_canonical_rows": active_canonical_rows,
        "active_canonical_sha": active_canonical_sha_after,
        "previous_current_candidate": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
        "previous_current_candidate_rows": current_validated_candidate_rows,
        "previous_current_candidate_sha": current_validated_candidate_sha_after,
        "validated_asx_candidate": str(ASX_EXPANDED_CANDIDATE_DATASET),
        "validated_asx_candidate_rows": asx_expanded_candidate_rows,
        "validated_asx_candidate_sha": asx_expanded_candidate_sha_after,
        "asx_net_new_rows": asx_net_new_rows,
        "row_arithmetic": f"{current_validated_candidate_rows}+{asx_net_new_rows}={asx_expanded_candidate_rows}",
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": asx_expanded_candidate_rows >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": asx_expanded_candidate_rows <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": rows_above_quality_floor,
        "remaining_capacity_to_quality_ceiling": remaining_capacity_to_quality_ceiling,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k": rows_to_aspirational_50k,
        "target_result": "OPERATIONAL_42K_FLOOR_ACHIEVED_WITHOUT_EXCEEDING_45K",
        "canonical_promotion_status": "NOT_PROMOTED_DECISION_GATE_READY",
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    decision_register_rows = [
        {
            "decision_id": "ASX_CLOSURE_001",
            "decision": "Close ASX provider route as successful",
            "status": "accepted" if critical_failed == 0 else "blocked",
            "evidence": "v2.20H validation passed with 42,708 rows, 1,316 ASX net-new rows, 0 critical failed checks.",
            "guardrail": "Closure report only; no canonical promotion in v2.20I.",
        },
        {
            "decision_id": "ASX_CLOSURE_002",
            "decision": "Record operational 42k floor achieved",
            "status": "accepted" if asx_expanded_candidate_rows >= QUALITY_FLOOR_TARGET else "blocked",
            "evidence": f"{asx_expanded_candidate_rows} rows >= {QUALITY_FLOOR_TARGET}; rows above floor = {rows_above_quality_floor}.",
            "guardrail": "Do not chase 50k for volume; 50k remains aspirational.",
        },
        {
            "decision_id": "ASX_CLOSURE_003",
            "decision": "Record 45k quality ceiling respected",
            "status": "accepted" if asx_expanded_candidate_rows <= QUALITY_CEILING_TARGET else "blocked",
            "evidence": f"{asx_expanded_candidate_rows} rows <= {QUALITY_CEILING_TARGET}; remaining capacity = {remaining_capacity_to_quality_ceiling}.",
            "guardrail": "Do not add more providers unless quality-first justification exists.",
        },
        {
            "decision_id": "ASX_CLOSURE_004",
            "decision": "Defer canonical promotion to explicit decision gate",
            "status": "accepted",
            "evidence": "v2.20I is closure-report-only; active canonical SHA remains unchanged.",
            "guardrail": "Promotion requires separate phase and explicit approval.",
        },
        {
            "decision_id": "ASX_CLOSURE_005",
            "decision": "Keep full59k deprecated",
            "status": "accepted",
            "evidence": "Quality-first 42k-45k operational band supersedes full59k route.",
            "guardrail": "Do not relaunch full59k unless explicitly reopened as a separate research branch.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "canonical",
            "action": "open_candidate_promotion_decision_gate",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "ASX candidate is validated and crosses the operational 42k floor; canonical promotion decision can now be evaluated explicitly.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "decision gate only unless explicit promotion is approved",
        },
        {
            "action_order": 2,
            "action_scope": "quality_target",
            "action": "freeze_provider_expansion_by_default",
            "priority": "high",
            "reason": "Operational 42k floor has been achieved and candidate remains below 45k.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "avoid adding rows for volume only",
        },
        {
            "action_order": 3,
            "action_scope": "full59k",
            "action": "keep_full59k_deprecated_deferred",
            "priority": "high",
            "reason": "Quality-first target reset is complete; 50k remains aspirational only.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "no full59k launch",
        },
    ]

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in closure_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "status", "evidence", "guardrail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "closure_summary": closure_summary,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "closure_report_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "operational_42k_floor_achieved": asx_expanded_candidate_rows >= QUALITY_FLOOR_TARGET,
            "operational_45k_ceiling_respected": asx_expanded_candidate_rows <= QUALITY_CEILING_TARGET,
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
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "pre_hkex_current_candidate_dataset_read": True,
            "pre_hkex_current_candidate_dataset_modified": False,
            "pre_hkex_current_candidate_sha_unchanged": pre_hkex_current_candidate_sha_before == pre_hkex_current_candidate_sha_after,
            "current_validated_candidate_dataset_read": True,
            "current_validated_candidate_dataset_modified": False,
            "current_validated_candidate_sha_unchanged": current_validated_candidate_sha_before == current_validated_candidate_sha_after,
            "asx_expanded_candidate_dataset_read": True,
            "asx_expanded_candidate_dataset_modified": False,
            "asx_expanded_candidate_sha_unchanged": asx_expanded_candidate_sha_before == asx_expanded_candidate_sha_after,
            "active_canonical_replaced": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "canonical_promotion_performed": False,
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

    decision_lines = "\n".join(
        f"- `{row['decision_id']}` — {row['decision']} — {row['status']}"
        for row in decision_register_rows
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

v2.20I closes the ASX provider route after successful expanded validation in v2.20H.

Validated ASX candidate:

`{ASX_EXPANDED_CANDIDATE_DATASET}`

The validated ASX candidate contains **{asx_expanded_candidate_rows:,}** rows. It adds **{asx_net_new_rows:,}** ASX net-new rows to the previous current candidate of **{current_validated_candidate_rows:,}** rows.

The operational quality-first floor of **{QUALITY_FLOOR_TARGET:,}** rows has been achieved, and the candidate remains below the operational ceiling of **{QUALITY_CEILING_TARGET:,}** rows.

This phase is a closure report only. It does **not** promote canonical, does **not** rebuild or validate again, does **not** run scoring, does **not** call OpenAI, does **not** call brokers, and does **not** launch full59k.

## Closure summary

- Active canonical rows: `{active_canonical_rows}`
- Active canonical SHA256: `{active_canonical_sha_after}`
- Previous current candidate rows: `{current_validated_candidate_rows}`
- Previous current candidate SHA256: `{current_validated_candidate_sha_after}`
- Validated ASX candidate rows: `{asx_expanded_candidate_rows}`
- Validated ASX candidate SHA256: `{asx_expanded_candidate_sha_after}`
- ASX net-new rows: `{asx_net_new_rows}`
- Row arithmetic: `{current_validated_candidate_rows}+{asx_net_new_rows}={asx_expanded_candidate_rows}`
- Quality floor crossed: `{asx_expanded_candidate_rows >= QUALITY_FLOOR_TARGET}`
- Quality ceiling respected: `{asx_expanded_candidate_rows <= QUALITY_CEILING_TARGET}`
- Rows above 42k floor: `{rows_above_quality_floor}`
- Remaining capacity to 45k ceiling: `{remaining_capacity_to_quality_ceiling}`
- Rows to 50k aspirational: `{rows_to_aspirational_50k}`
- Canonical promotion status: `NOT_PROMOTED_DECISION_GATE_READY`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Decision register

{decision_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Closure report only: true
- Canonical dataset modified: false
- Current validated candidate dataset modified: false
- ASX expanded candidate dataset modified: false
- Active canonical replaced: false
- Canonical promotion performed: false
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

    print("v2.20I ASX closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CLOSURE_SUMMARY:")
    for key, value in closure_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("DECISION_REGISTER:")
    for row in decision_register_rows:
        print(f"- {row['decision_id']}: {row['decision']} [{row['status']}]")
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
