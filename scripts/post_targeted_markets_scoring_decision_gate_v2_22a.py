from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.22A"
PHASE = "Post-Targeted-Markets Explicit Scoring Decision Gate"
PHASE_TYPE = "post-targeted-markets-explicit-scoring-decision-gate"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVATION_REPORT = OUTPUT_DIR / "final_reference_activation_gate_v2_21h.json"
ACTIVATED_OPERATIONAL_REFERENCE = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"

PREVIOUS_OPERATIONAL_BASE = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
FINAL_REFERENCE_DATASET = OUTPUT_DIR / "expanded_universe_v2_21g_final_reference.csv"

REPORT_JSON = OUTPUT_DIR / "post_targeted_markets_scoring_decision_gate_v2_22a.json"
REPORT_MD = OUTPUT_DIR / "post_targeted_markets_scoring_decision_gate_v2_22a.md"
SUMMARY_CSV = OUTPUT_DIR / "post_targeted_markets_scoring_decision_gate_summary_v2_22a.csv"
CHECKS_CSV = OUTPUT_DIR / "post_targeted_markets_scoring_decision_gate_checks_v2_22a.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "post_targeted_markets_scoring_decision_gate_artifact_manifest_v2_22a.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "post_targeted_markets_scoring_decision_gate_decision_register_v2_22a.csv"
REQUIREMENTS_REGISTER_CSV = OUTPUT_DIR / "post_targeted_markets_scoring_decision_gate_requirements_v2_22a.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "post_targeted_markets_scoring_decision_gate_next_actions_v2_22a.csv"

EXPECTED_ACTIVATION_STATUS = "FINAL_REFERENCE_ACTIVATION_GATE_COMPLETED_OPERATIONAL_REFERENCE_ARTIFACT_READY_EXISTING_POINTERS_UNCHANGED_SCORING_DEFERRED"

ACTIVATED_ROWS_EXPECTED = 43089
ACTIVATED_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

PREVIOUS_OPERATIONAL_ROWS_EXPECTED = 42708
PREVIOUS_OPERATIONAL_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

FINAL_REFERENCE_ROWS_EXPECTED = 43089
FINAL_REFERENCE_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_DEFERRED = "POST_TARGETED_MARKETS_SCORING_DECISION_GATE_COMPLETED_SCORING_DEFERRED_POINTER_HARDENING_AND_PRE_SCORING_AUDIT_REQUIRED"
STATUS_FAILED = "POST_TARGETED_MARKETS_SCORING_DECISION_GATE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.22B - Operational Pointer Convention Hardening"
SECONDARY_NEXT_PHASE = "v2.22C - Pre-Scoring Data Quality Audit"
CONDITIONAL_NEXT_PHASE = "v2.22D - Scoring Dry Run / No Promotion"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        DECISION_REGISTER_CSV,
        REQUIREMENTS_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    activation_report = read_json(ACTIVATION_REPORT)
    activation_summary = activation_report.get("summary", {})
    activation_hard_guards = activation_report.get("hard_guards", {})

    activated_rows = count_csv_rows(ACTIVATED_OPERATIONAL_REFERENCE)
    activated_sha = sha256_file(ACTIVATED_OPERATIONAL_REFERENCE)

    previous_operational_rows = count_csv_rows(PREVIOUS_OPERATIONAL_BASE)
    previous_operational_sha = sha256_file(PREVIOUS_OPERATIONAL_BASE)

    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)

    final_reference_rows = count_csv_rows(FINAL_REFERENCE_DATASET)
    final_reference_sha = sha256_file(FINAL_REFERENCE_DATASET)

    activated_header = read_csv_header(ACTIVATED_OPERATIONAL_REFERENCE)
    previous_header = read_csv_header(PREVIOUS_OPERATIONAL_BASE)
    final_reference_header = read_csv_header(FINAL_REFERENCE_DATASET)

    activated_sha_after_read = sha256_file(ACTIVATED_OPERATIONAL_REFERENCE)
    previous_operational_sha_after_read = sha256_file(PREVIOUS_OPERATIONAL_BASE)
    rollback_sha_after_read = sha256_file(ROLLBACK_DATASET)
    final_reference_sha_after_read = sha256_file(FINAL_REFERENCE_DATASET)

    artifact_manifest_rows = [
        {
            "artifact": "activated_operational_reference_input",
            "path": str(ACTIVATED_OPERATIONAL_REFERENCE),
            "rows": activated_rows,
            "sha256": activated_sha,
            "role": "scoring_decision_input_no_scoring_executed",
        },
        {
            "artifact": "previous_operational_base_reference",
            "path": str(PREVIOUS_OPERATIONAL_BASE),
            "rows": previous_operational_rows,
            "sha256": previous_operational_sha,
            "role": "comparison_reference_unchanged",
        },
        {
            "artifact": "rollback_reference",
            "path": str(ROLLBACK_DATASET),
            "rows": rollback_rows,
            "sha256": rollback_sha,
            "role": "rollback_reference_unchanged",
        },
        {
            "artifact": "final_v2_21_reference",
            "path": str(FINAL_REFERENCE_DATASET),
            "rows": final_reference_rows,
            "sha256": final_reference_sha,
            "role": "source_reference_unchanged",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_22A_SCORING_001",
            "decision": "Do not run scoring in v2.22A.",
            "accepted": True,
            "reason": "v2.22A is an explicit decision gate, not an execution phase.",
            "effect": "No scoring output is created.",
        },
        {
            "decision_id": "V2_22A_SCORING_002",
            "decision": "Require operational pointer convention hardening before scoring.",
            "accepted": True,
            "reason": "v2.21H created an activated operational reference artifact without mutating unknown pointer files.",
            "effect": "Next phase is v2.22B.",
        },
        {
            "decision_id": "V2_22A_SCORING_003",
            "decision": "Require pre-scoring data quality audit before scoring dry run.",
            "accepted": True,
            "reason": "The expanded universe contains new Singapore and Colombia rows and needs targeted quality review before ranking.",
            "effect": "v2.22C must pass before v2.22D scoring dry run.",
        },
        {
            "decision_id": "V2_22A_SCORING_004",
            "decision": "Keep OpenAI, broker, and full59k blocked.",
            "accepted": True,
            "reason": "No explicit authorization has been given for OpenAI enrichment, broker data, or full59k expansion.",
            "effect": "No external enrichment or full59k workflow is launched.",
        },
    ]

    requirements_register_rows = [
        {
            "requirement_id": "REQ_POINTER_CONVENTION",
            "requirement": "Define single operational pointer/canonical convention.",
            "required_before_scoring_dry_run": True,
            "current_status": "pending",
            "recommended_phase": NEXT_PHASE,
            "reason": "Avoid ambiguity between previous base, final reference, and activated operational reference.",
        },
        {
            "requirement_id": "REQ_PRE_SCORING_AUDIT",
            "requirement": "Run pre-scoring data quality audit.",
            "required_before_scoring_dry_run": True,
            "current_status": "pending",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Validate duplicates, identifiers, country/exchange/MIC/currency, and instrument suitability before ranking.",
        },
        {
            "requirement_id": "REQ_SCORING_CONFIG",
            "requirement": "Confirm local scoring configuration and output naming.",
            "required_before_scoring_dry_run": True,
            "current_status": "pending",
            "recommended_phase": CONDITIONAL_NEXT_PHASE,
            "reason": "Prevent accidental overwrites, renormalization, or historical mutation.",
        },
        {
            "requirement_id": "REQ_EXTERNAL_CALLS",
            "requirement": "Keep OpenAI/broker/external enrichment unauthorized unless separately approved.",
            "required_before_scoring_dry_run": True,
            "current_status": "blocked_by_default",
            "recommended_phase": "none",
            "reason": "The user has not authorized external enrichment.",
        },
        {
            "requirement_id": "REQ_FULL59K",
            "requirement": "Keep full59k deprecated/deferred.",
            "required_before_scoring_dry_run": True,
            "current_status": "blocked_by_default",
            "recommended_phase": "none",
            "reason": "The quality target remains 42k-45k.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "pointer_convention",
            "action": "define_and_harden_single_live_operational_pointer_convention",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Scoring should target one explicit operational reference.",
            "guardrails": "No scoring; no OpenAI; no broker; no full59k.",
        },
        {
            "action_order": 2,
            "action_scope": "pre_scoring_audit",
            "action": "audit_activated_operational_reference_before_scoring",
            "priority": "high",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Validate the 43,089-row activated universe before scoring.",
            "guardrails": "Audit only; no score promotion; no external enrichment.",
        },
        {
            "action_order": 3,
            "action_scope": "scoring_dry_run",
            "action": "prepare_scoring_dry_run_only_after_pointer_and_audit_pass",
            "priority": "medium",
            "recommended_phase": CONDITIONAL_NEXT_PHASE,
            "reason": "Scoring dry run should be conditional on prior gates.",
            "guardrails": "No promotion in dry run; no canonical replacement.",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0
    warning_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed, warning_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        if severity == "warning" and not passed:
            warning_failed += 1
        checks.append({
            "check": check,
            "passed": bool(passed),
            "severity": severity,
            "detail": detail,
        })

    add_check("activation_status_expected", activation_report.get("status") == EXPECTED_ACTIVATION_STATUS, "critical", str(activation_report.get("status")))
    add_check("activation_zero_critical_failed_checks", str(activation_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={activation_summary.get('critical_failed_checks')}")
    add_check("activation_zero_warning_failed_checks", str(activation_summary.get("warning_failed_checks")) == "0", "critical", f"warning_failed_checks={activation_summary.get('warning_failed_checks')}")
    add_check("activation_approved_operational_reference", as_bool(activation_summary.get("approved_as_current_operational_reference_artifact")) is True, "critical", f"approved_as_current_operational_reference_artifact={activation_summary.get('approved_as_current_operational_reference_artifact')}")
    add_check("activated_rows_expected", activated_rows == ACTIVATED_ROWS_EXPECTED, "critical", f"activated_rows={activated_rows}")
    add_check("activated_sha_expected", activated_sha == ACTIVATED_SHA_EXPECTED, "critical", activated_sha)
    add_check("previous_operational_rows_expected", previous_operational_rows == PREVIOUS_OPERATIONAL_ROWS_EXPECTED, "critical", f"previous_operational_rows={previous_operational_rows}")
    add_check("previous_operational_sha_expected", previous_operational_sha == PREVIOUS_OPERATIONAL_SHA_EXPECTED, "critical", previous_operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("final_reference_rows_expected", final_reference_rows == FINAL_REFERENCE_ROWS_EXPECTED, "critical", f"final_reference_rows={final_reference_rows}")
    add_check("final_reference_sha_expected", final_reference_sha == FINAL_REFERENCE_SHA_EXPECTED, "critical", final_reference_sha)
    add_check("activated_matches_final_reference", activated_sha == final_reference_sha and activated_rows == final_reference_rows, "critical", f"activated={activated_rows}/{activated_sha};final={final_reference_rows}/{final_reference_sha}")
    add_check("headers_consistent", activated_header == previous_header == final_reference_header, "critical", f"activated_columns={len(activated_header)};previous_columns={len(previous_header)};final_columns={len(final_reference_header)}")
    add_check("within_quality_floor", activated_rows >= QUALITY_FLOOR_TARGET, "critical", f"activated_rows={activated_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("within_quality_ceiling", activated_rows <= QUALITY_CEILING_TARGET, "critical", f"activated_rows={activated_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("remaining_capacity_non_negative", QUALITY_CEILING_TARGET - activated_rows >= 0, "critical", f"remaining_capacity={QUALITY_CEILING_TARGET - activated_rows}")
    add_check("scoring_not_executed", True, "critical", "scoring_executed=False")
    add_check("scoring_not_authorized_in_gate", True, "critical", "scoring_authorized=False")
    add_check("openai_not_authorized", True, "critical", "openai_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_authorized", True, "critical", "broker_authorized=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("no_canonical_mutation", True, "critical", "canonical_dataset_modified=False")
    add_check("no_pointer_mutation", True, "critical", "pointer_update_performed=False")
    add_check("activated_reference_not_modified", activated_sha_after_read == ACTIVATED_SHA_EXPECTED, "critical", f"activated_sha_after_read={activated_sha_after_read}")
    add_check("previous_operational_not_modified", previous_operational_sha_after_read == PREVIOUS_OPERATIONAL_SHA_EXPECTED, "critical", f"previous_operational_sha_after_read={previous_operational_sha_after_read}")
    add_check("rollback_not_modified", rollback_sha_after_read == ROLLBACK_SHA_EXPECTED, "critical", f"rollback_sha_after_read={rollback_sha_after_read}")
    add_check("final_reference_not_modified", final_reference_sha_after_read == FINAL_REFERENCE_SHA_EXPECTED, "critical", f"final_reference_sha_after_read={final_reference_sha_after_read}")
    add_check("pre_scoring_requirements_defined", len(requirements_register_rows) >= 5, "critical", f"requirements={len(requirements_register_rows)}")

    status = STATUS_DEFERRED if critical_failed == 0 and warning_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Post-targeted-markets explicit scoring decision gate",
        "phase_type": PHASE_TYPE,
        "scoring_decision": "SCORING_DEFERRED_POINTER_HARDENING_AND_PRE_SCORING_AUDIT_REQUIRED" if status == STATUS_DEFERRED else "SCORING_DECISION_BLOCKED_REVIEW_REQUIRED",
        "activated_operational_reference_dataset": str(ACTIVATED_OPERATIONAL_REFERENCE),
        "activated_operational_reference_rows": activated_rows,
        "activated_operational_reference_sha": activated_sha,
        "previous_operational_base_dataset": str(PREVIOUS_OPERATIONAL_BASE),
        "previous_operational_base_rows": previous_operational_rows,
        "previous_operational_base_sha": previous_operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "final_reference_dataset": str(FINAL_REFERENCE_DATASET),
        "final_reference_rows": final_reference_rows,
        "final_reference_sha": final_reference_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity": QUALITY_CEILING_TARGET - activated_rows,
        "total_added_rows_vs_previous_operational_base": activated_rows - previous_operational_rows,
        "approved_for_pointer_convention_hardening": status == STATUS_DEFERRED,
        "approved_for_pre_scoring_data_quality_audit": status == STATUS_DEFERRED,
        "approved_for_scoring_dry_run": False,
        "scoring_authorized": False,
        "scoring_executed": False,
        "scoring_output_created": False,
        "scoring_promotion_authorized": False,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "pointer_update_performed": False,
        "openai_authorized": False,
        "openai_called": False,
        "broker_authorized": False,
        "broker_called": False,
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": NEXT_PHASE,
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
        "conditional_next_phase": CONDITIONAL_NEXT_PHASE,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(REQUIREMENTS_REGISTER_CSV, requirements_register_rows, [
        "requirement_id",
        "requirement",
        "required_before_scoring_dry_run",
        "current_status",
        "recommended_phase",
        "reason",
    ])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, [
        "action_order",
        "action_scope",
        "action",
        "priority",
        "recommended_phase",
        "reason",
        "guardrails",
    ])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "requirements_register": requirements_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Explicit scoring decision gate after v2.21 targeted markets",
            "activated_operational_reference_dataset": str(ACTIVATED_OPERATIONAL_REFERENCE),
            "activated_operational_reference_rows": activated_rows,
            "activated_operational_reference_sha": activated_sha,
            "approved_for_pointer_convention_hardening": status == STATUS_DEFERRED,
            "approved_for_pre_scoring_data_quality_audit": status == STATUS_DEFERRED,
            "approved_for_scoring_dry_run": False,
            "scoring_authorized": False,
            "scoring_executed": False,
            "scoring_output_created": False,
            "scoring_promotion_authorized": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "openai_authorized": False,
            "openai_called": False,
            "broker_authorized": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
            "history_rewrite_performed": False,
            "force_push_required": False,
        },
        "recommended_next_phase": NEXT_PHASE,
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
        "conditional_next_phase": CONDITIONAL_NEXT_PHASE,
    }

    write_json(REPORT_JSON, payload)

    artifact_lines = "\n".join(
        f"- `{row['artifact']}` — rows `{row['rows']}` — SHA `{row['sha256']}` — {row['role']}"
        for row in artifact_manifest_rows
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}` — accepted `{row['accepted']}` — {row['decision']}"
        for row in decision_register_rows
    )

    requirement_lines = "\n".join(
        f"- `{row['requirement_id']}` — required `{row['required_before_scoring_dry_run']}` — {row['requirement']} — status `{row['current_status']}`"
        for row in requirements_register_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.22A is an explicit scoring decision gate after the targeted Colombia + Singapore expansion.

No scoring is executed in this phase.

The activated operational reference is accepted as the future scoring input, but scoring remains deferred until pointer convention hardening and pre-scoring data quality audit are completed.

## Scoring input

`{ACTIVATED_OPERATIONAL_REFERENCE}`

Rows: `{activated_rows}`  
SHA256: `{activated_sha}`

## Decision

Scoring decision: `{summary["scoring_decision"]}`

Approved for scoring dry run: `False`

Approved for pointer convention hardening: `{summary["approved_for_pointer_convention_hardening"]}`

Approved for pre-scoring data quality audit: `{summary["approved_for_pre_scoring_data_quality_audit"]}`

## Artifact manifest

{artifact_lines}

## Decisions

{decision_lines}

## Requirements before scoring dry run

{requirement_lines}

## Checks

{check_lines}

## Recommended next phases

Primary: `{NEXT_PHASE}`

Secondary: `{SECONDARY_NEXT_PHASE}`

Conditional after both pass: `{CONDITIONAL_NEXT_PHASE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.22A post-targeted-markets scoring decision gate completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")
    print("")
    print("SECONDARY_NEXT_PHASE:")
    print(f"- {SECONDARY_NEXT_PHASE}")
    print("")
    print("CONDITIONAL_NEXT_PHASE:")
    print(f"- {CONDITIONAL_NEXT_PHASE}")


if __name__ == "__main__":
    main()
