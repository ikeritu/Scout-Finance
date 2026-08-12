from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20J"
PHASE = "ASX Candidate Promotion Decision Gate"
PHASE_TYPE = "promotion-decision-gate-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PRE_HKEX_CURRENT_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
ASX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"

V220I_JSON = OUTPUT_DIR / "asx_closure_report_v2_20i.json"
V220H_JSON = OUTPUT_DIR / "asx_expanded_validation_v2_20h.json"
V220G_JSON = OUTPUT_DIR / "asx_expanded_rebuild_candidate_v2_20g.json"

REPORT_JSON = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_v2_20j.json"
REPORT_MD = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_v2_20j.md"
SUMMARY_CSV = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_summary_v2_20j.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_checks_v2_20j.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_register_v2_20j.csv"
PROMOTION_READINESS_CSV = OUTPUT_DIR / "asx_candidate_promotion_readiness_v2_20j.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_candidate_promotion_decision_gate_next_actions_v2_20j.csv"

EXPECTED_V220G_STATUS = "ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
EXPECTED_V220H_STATUS = "ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED"
EXPECTED_V220I_STATUS = "ASX_CLOSURE_REPORT_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_42K_TARGET_ACHIEVED_45K_CEILING_RESPECTED_CANONICAL_PROMOTION_DECISION_READY_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED = 40996
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392
ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED = 42708
ASX_NET_NEW_ROWS_EXPECTED = 1316

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

STATUS_SUCCESS = "ASX_CANDIDATE_PROMOTION_DECISION_GATE_COMPLETED_PROMOTION_RECOMMENDED_42708_ROWS_42K_ACHIEVED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_CANDIDATE_PROMOTION_DECISION_GATE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20K - ASX Canonical Promotion Plan"
NEXT_PHASE_REVIEW = "v2.20J_REVIEW - ASX Candidate Promotion Decision Gate Review"


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
        PROMOTION_READINESS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220g = read_json(V220G_JSON)
    v220h = read_json(V220H_JSON)
    v220i = read_json(V220I_JSON)

    v220h_summary = v220h.get("validation_summary", {})
    v220i_summary = v220i.get("closure_summary", {})

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
    uplift_vs_current_candidate_rows = asx_validated_candidate_rows - current_validated_candidate_rows
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
    add_check("v2_20g_status_expected", v220g.get("status") == EXPECTED_V220G_STATUS, "critical", str(v220g.get("status")))
    add_check("v2_20h_status_expected", v220h.get("status") == EXPECTED_V220H_STATUS, "critical", str(v220h.get("status")))
    add_check("v2_20i_status_expected", v220i.get("status") == EXPECTED_V220I_STATUS, "critical", str(v220i.get("status")))
    add_check("v2_20i_next_phase_expected", v220i.get("recommended_next_phase") == "v2.20J - ASX Candidate Promotion Decision Gate", "critical", str(v220i.get("recommended_next_phase")))

    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("pre_hkex_current_candidate_rows_expected", pre_hkex_current_candidate_rows == PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED, "critical", f"pre_hkex_rows={pre_hkex_current_candidate_rows}")
    add_check("current_validated_candidate_rows_expected", current_validated_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_validated_rows={current_validated_candidate_rows}")
    add_check("asx_validated_candidate_rows_expected", asx_validated_candidate_rows == ASX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"asx_validated_rows={asx_validated_candidate_rows}")
    add_check("asx_net_new_rows_expected", asx_net_new_rows == ASX_NET_NEW_ROWS_EXPECTED, "critical", f"asx_net_new_rows={asx_net_new_rows}")

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

    add_check("v2_20h_validation_clean", int(v220h_summary.get("critical_failed_checks", -1)) == 0 and int(v220h_summary.get("warning_failed_checks", -1)) == 0, "critical", f"critical={v220h_summary.get('critical_failed_checks')};warning={v220h_summary.get('warning_failed_checks')}")
    add_check("v2_20i_closure_successful", v220i_summary.get("closure_decision") == "ASX_PROVIDER_ROUTE_CLOSED_SUCCESSFULLY", "critical", str(v220i_summary.get("closure_decision")))
    add_check("v2_20i_target_result_expected", v220i_summary.get("target_result") == "OPERATIONAL_42K_FLOOR_ACHIEVED_WITHOUT_EXCEEDING_45K", "critical", str(v220i_summary.get("target_result")))
    add_check("v2_20i_canonical_promotion_status_ready", v220i_summary.get("canonical_promotion_status") == "NOT_PROMOTED_DECISION_GATE_READY", "critical", str(v220i_summary.get("canonical_promotion_status")))
    add_check("promotion_decision_gate_only", True, "critical", "promotion decision gate only")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("canonical_promotion_not_performed", True, "critical", "canonical_promotion_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
        promotion_decision = "PROMOTION_BLOCKED_REVIEW_REQUIRED"
        promotion_recommendation = "DO_NOT_PROMOTE_UNTIL_REVIEW"
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
        promotion_decision = "PROMOTION_RECOMMENDED_READY_FOR_PLAN"
        promotion_recommendation = "PREPARE_CANONICAL_PROMOTION_PLAN"

    decision_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "promotion_decision": promotion_decision,
        "promotion_recommendation": promotion_recommendation,
        "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "active_canonical_rows": active_canonical_rows,
        "active_canonical_sha": active_canonical_sha_after,
        "current_validated_candidate": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
        "current_validated_candidate_rows": current_validated_candidate_rows,
        "current_validated_candidate_sha": current_validated_candidate_sha_after,
        "validated_asx_candidate": str(ASX_VALIDATED_CANDIDATE_DATASET),
        "validated_asx_candidate_rows": asx_validated_candidate_rows,
        "validated_asx_candidate_sha": asx_validated_candidate_sha_after,
        "asx_net_new_rows_vs_current_candidate": asx_net_new_rows,
        "uplift_vs_active_canonical_rows": uplift_vs_active_canonical_rows,
        "uplift_vs_current_candidate_rows": uplift_vs_current_candidate_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": asx_validated_candidate_rows >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": asx_validated_candidate_rows <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": rows_above_quality_floor,
        "remaining_capacity_to_quality_ceiling": remaining_capacity_to_quality_ceiling,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k": rows_to_aspirational_50k,
        "decision_gate_result": "APPROVE_PREPARATION_OF_CANONICAL_PROMOTION" if critical_failed == 0 else "REVIEW_REQUIRED",
        "canonical_promotion_performed": False,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    decision_register_rows = [
        {
            "decision_id": "ASX_PROMOTION_GATE_001",
            "decision": "Recommend preparing canonical promotion plan",
            "status": "accepted" if critical_failed == 0 else "blocked",
            "evidence": "ASX candidate is validated at 42,708 rows with 0 critical and 0 warning failed checks.",
            "guardrail": "Decision gate only; no canonical replacement in v2.20J.",
        },
        {
            "decision_id": "ASX_PROMOTION_GATE_002",
            "decision": "Prefer validated ASX candidate over current HKEX candidate as next operational base",
            "status": "accepted" if critical_failed == 0 else "blocked",
            "evidence": "ASX candidate adds 1,316 net-new rows over the 41,392-row HKEX candidate and reaches 42,708 rows.",
            "guardrail": "Promotion must preserve audit trail and original candidate files.",
        },
        {
            "decision_id": "ASX_PROMOTION_GATE_003",
            "decision": "Do not continue provider expansion by default",
            "status": "accepted",
            "evidence": "Operational 42k floor is achieved and 45k ceiling respected.",
            "guardrail": "No rows for volume only; 50k remains aspirational.",
        },
        {
            "decision_id": "ASX_PROMOTION_GATE_004",
            "decision": "Keep full59k deprecated",
            "status": "accepted",
            "evidence": "Quality-first 42k-45k route supersedes full59k expansion.",
            "guardrail": "Do not relaunch full59k unless explicitly opened as separate branch.",
        },
        {
            "decision_id": "ASX_PROMOTION_GATE_005",
            "decision": "Require separate promotion phase before replacing canonical",
            "status": "accepted",
            "evidence": "v2.20J does not modify active canonical; active canonical SHA remains unchanged.",
            "guardrail": "Canonical replacement requires explicit v2.20K+ phase.",
        },
    ]

    promotion_readiness_rows = [
        {"criterion": "v2.20G rebuild passed", "ready": v220g.get("status") == EXPECTED_V220G_STATUS, "evidence": str(v220g.get("status"))},
        {"criterion": "v2.20H validation passed", "ready": v220h.get("status") == EXPECTED_V220H_STATUS, "evidence": str(v220h.get("status"))},
        {"criterion": "v2.20I closure passed", "ready": v220i.get("status") == EXPECTED_V220I_STATUS, "evidence": str(v220i.get("status"))},
        {"criterion": "42k floor achieved", "ready": asx_validated_candidate_rows >= QUALITY_FLOOR_TARGET, "evidence": f"{asx_validated_candidate_rows} >= {QUALITY_FLOOR_TARGET}"},
        {"criterion": "45k ceiling respected", "ready": asx_validated_candidate_rows <= QUALITY_CEILING_TARGET, "evidence": f"{asx_validated_candidate_rows} <= {QUALITY_CEILING_TARGET}"},
        {"criterion": "canonical unchanged", "ready": active_canonical_sha_before == active_canonical_sha_after, "evidence": active_canonical_sha_after},
        {"criterion": "ASX candidate immutable during decision gate", "ready": asx_validated_candidate_sha_before == asx_validated_candidate_sha_after, "evidence": asx_validated_candidate_sha_after},
        {"criterion": "promotion decision ready", "ready": critical_failed == 0, "evidence": f"critical_failed_checks={critical_failed};warning_failed_checks={warning_failed}"},
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "canonical",
            "action": "prepare_asx_canonical_promotion_plan",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Decision gate recommends preparing a controlled promotion plan for the validated 42,708-row ASX candidate.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "plan first; no scoring/OpenAI/broker/full59k; preserve rollback path",
        },
        {
            "action_order": 2,
            "action_scope": "audit",
            "action": "define_rollback_and_sha_controls",
            "priority": "high",
            "reason": "Canonical promotion should have exact pre/post SHA checks and rollback references.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "do not overwrite without explicit copy/backup strategy",
        },
        {
            "action_order": 3,
            "action_scope": "quality_target",
            "action": "freeze_additional_provider_expansion",
            "priority": "high",
            "reason": "Operational target has been reached without exceeding the quality ceiling.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "avoid adding rows for volume only",
        },
    ]

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in decision_summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "status", "evidence", "guardrail"])
    write_csv(PROMOTION_READINESS_CSV, promotion_readiness_rows, ["criterion", "ready", "evidence"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "decision_summary": decision_summary,
        "decision_register": decision_register_rows,
        "promotion_readiness": promotion_readiness_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "promotion_decision_gate_only": True,
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

    readiness_lines = "\n".join(
        f"- {row['criterion']}: {'READY' if row['ready'] else 'NOT READY'} — {row['evidence']}"
        for row in promotion_readiness_rows
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

v2.20J is a promotion decision gate for the validated ASX candidate.

Validated ASX candidate:

`{ASX_VALIDATED_CANDIDATE_DATASET}`

The ASX candidate contains **{asx_validated_candidate_rows:,}** rows and is recommended as the next operational base for a controlled promotion plan.

This phase does **not** promote canonical. It only records that promotion preparation is recommended.

## Decision summary

- Promotion decision: `{promotion_decision}`
- Promotion recommendation: `{promotion_recommendation}`
- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_validated_candidate_rows}`
- Validated ASX candidate rows: `{asx_validated_candidate_rows}`
- ASX net-new rows vs current candidate: `{asx_net_new_rows}`
- Uplift vs active canonical rows: `{uplift_vs_active_canonical_rows}`
- Uplift vs current candidate rows: `{uplift_vs_current_candidate_rows}`
- Quality floor crossed: `{asx_validated_candidate_rows >= QUALITY_FLOOR_TARGET}`
- Quality ceiling respected: `{asx_validated_candidate_rows <= QUALITY_CEILING_TARGET}`
- Rows above 42k floor: `{rows_above_quality_floor}`
- Remaining capacity to 45k ceiling: `{remaining_capacity_to_quality_ceiling}`
- Rows to 50k aspirational: `{rows_to_aspirational_50k}`
- Canonical promotion performed: `False`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Promotion readiness

{readiness_lines}

## Decision register

{decision_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Promotion decision gate only: true
- Canonical dataset modified: false
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

    print("v2.20J ASX candidate promotion decision gate completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("DECISION_SUMMARY:")
    for key, value in decision_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("PROMOTION_READINESS:")
    for row in promotion_readiness_rows:
        print(f"- {row['criterion']}: {'READY' if row['ready'] else 'NOT_READY'} - {row['evidence']}")
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
