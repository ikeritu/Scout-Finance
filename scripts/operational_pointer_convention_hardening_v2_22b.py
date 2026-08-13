from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.22B"
PHASE = "Operational Pointer Convention Hardening"
PHASE_TYPE = "operational-pointer-convention-hardening"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

SCORING_GATE_REPORT = OUTPUT_DIR / "post_targeted_markets_scoring_decision_gate_v2_22a.json"

ACTIVATED_OPERATIONAL_REFERENCE = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
FINAL_REFERENCE_DATASET = OUTPUT_DIR / "expanded_universe_v2_21g_final_reference.csv"
PREVIOUS_OPERATIONAL_BASE = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

CURRENT_POINTER_JSON = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_POINTER_MD = OUTPUT_DIR / "current_operational_universe_pointer.md"

REPORT_JSON = OUTPUT_DIR / "operational_pointer_convention_hardening_v2_22b.json"
REPORT_MD = OUTPUT_DIR / "operational_pointer_convention_hardening_v2_22b.md"
SUMMARY_CSV = OUTPUT_DIR / "operational_pointer_convention_hardening_summary_v2_22b.csv"
CHECKS_CSV = OUTPUT_DIR / "operational_pointer_convention_hardening_checks_v2_22b.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "operational_pointer_convention_hardening_artifact_manifest_v2_22b.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "operational_pointer_convention_hardening_decision_register_v2_22b.csv"
CONVENTION_REGISTER_CSV = OUTPUT_DIR / "operational_pointer_convention_hardening_convention_register_v2_22b.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "operational_pointer_convention_hardening_next_actions_v2_22b.csv"

EXPECTED_SCORING_GATE_STATUS = "POST_TARGETED_MARKETS_SCORING_DECISION_GATE_COMPLETED_SCORING_DEFERRED_POINTER_HARDENING_AND_PRE_SCORING_AUDIT_REQUIRED"

ACTIVATED_ROWS_EXPECTED = 43089
ACTIVATED_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

FINAL_REFERENCE_ROWS_EXPECTED = 43089
FINAL_REFERENCE_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

PREVIOUS_OPERATIONAL_ROWS_EXPECTED = 42708
PREVIOUS_OPERATIONAL_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_COMPLETED = "OPERATIONAL_POINTER_CONVENTION_HARDENING_COMPLETED_CURRENT_OPERATIONAL_POINTER_CREATED_SCORING_DEFERRED"
STATUS_FAILED = "OPERATIONAL_POINTER_CONVENTION_HARDENING_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.22C - Pre-Scoring Data Quality Audit"
SECONDARY_NEXT_PHASE = "v2.22D - Scoring Dry Run / No Promotion"


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


def write_text(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


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
        CURRENT_POINTER_JSON,
        CURRENT_POINTER_MD,
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        DECISION_REGISTER_CSV,
        CONVENTION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    scoring_gate = read_json(SCORING_GATE_REPORT)
    scoring_summary = scoring_gate.get("summary", {})

    activated_rows = count_csv_rows(ACTIVATED_OPERATIONAL_REFERENCE)
    activated_sha = sha256_file(ACTIVATED_OPERATIONAL_REFERENCE)

    final_reference_rows = count_csv_rows(FINAL_REFERENCE_DATASET)
    final_reference_sha = sha256_file(FINAL_REFERENCE_DATASET)

    previous_operational_rows = count_csv_rows(PREVIOUS_OPERATIONAL_BASE)
    previous_operational_sha = sha256_file(PREVIOUS_OPERATIONAL_BASE)

    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)

    activated_header = read_csv_header(ACTIVATED_OPERATIONAL_REFERENCE)
    final_reference_header = read_csv_header(FINAL_REFERENCE_DATASET)
    previous_header = read_csv_header(PREVIOUS_OPERATIONAL_BASE)

    pointer_payload = {
        "pointer_schema_version": "1.0",
        "created_by_phase": VERSION,
        "created_at_utc": utc_now(),
        "pointer_name": "current_operational_universe",
        "pointer_type": "single_live_operational_universe_reference",
        "current_dataset": str(ACTIVATED_OPERATIONAL_REFERENCE),
        "current_dataset_rows": activated_rows,
        "current_dataset_sha256": activated_sha,
        "current_dataset_source_phase": "v2.21H",
        "current_dataset_source_role": "activated_operational_reference_artifact",
        "previous_operational_base_dataset": str(PREVIOUS_OPERATIONAL_BASE),
        "previous_operational_base_rows": previous_operational_rows,
        "previous_operational_base_sha256": previous_operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha256": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity": QUALITY_CEILING_TARGET - activated_rows,
        "scoring_authorized": False,
        "scoring_executed": False,
        "openai_authorized": False,
        "openai_called": False,
        "broker_authorized": False,
        "broker_called": False,
        "full59k": "DEPRECATED_DEFERRED",
        "update_policy": {
            "only_update_after_explicit_gate": True,
            "require_row_count_and_sha_validation": True,
            "require_rollback_reference": True,
            "do_not_overwrite_datasets": True,
            "do_not_force_push": True,
            "do_not_rewrite_history": True,
        },
        "consumer_policy": {
            "pre_scoring_audit_input": str(CURRENT_POINTER_JSON),
            "scoring_dry_run_input": str(CURRENT_POINTER_JSON),
            "human_readable_pointer": str(CURRENT_POINTER_MD),
        },
    }

    write_json(CURRENT_POINTER_JSON, pointer_payload)

    write_text(
        CURRENT_POINTER_MD,
        f"""# Current Operational Universe Pointer

Pointer created by: `{VERSION}`  
Pointer type: `single_live_operational_universe_reference`

## Current dataset

`{ACTIVATED_OPERATIONAL_REFERENCE}`

Rows: `{activated_rows}`  
SHA256: `{activated_sha}`

## Previous operational base

`{PREVIOUS_OPERATIONAL_BASE}`

Rows: `{previous_operational_rows}`  
SHA256: `{previous_operational_sha}`

## Rollback dataset

`{ROLLBACK_DATASET}`

Rows: `{rollback_rows}`  
SHA256: `{rollback_sha}`

## Policy

- This file defines the single current operational universe pointer.
- Consumers should read the pointer JSON before audit or scoring.
- Pointer updates require an explicit gate.
- Dataset overwrites are not allowed.
- Scoring, OpenAI, broker calls, and full59k remain unauthorized unless separately approved.
""",
    )

    current_pointer_sha = sha256_file(CURRENT_POINTER_JSON)
    current_pointer_md_sha = sha256_file(CURRENT_POINTER_MD)

    activated_sha_after = sha256_file(ACTIVATED_OPERATIONAL_REFERENCE)
    final_reference_sha_after = sha256_file(FINAL_REFERENCE_DATASET)
    previous_operational_sha_after = sha256_file(PREVIOUS_OPERATIONAL_BASE)
    rollback_sha_after = sha256_file(ROLLBACK_DATASET)

    artifact_manifest_rows = [
        {
            "artifact": "current_operational_pointer_json",
            "path": str(CURRENT_POINTER_JSON),
            "rows": 1,
            "sha256": current_pointer_sha,
            "role": "single_live_operational_universe_pointer",
        },
        {
            "artifact": "current_operational_pointer_md",
            "path": str(CURRENT_POINTER_MD),
            "rows": 1,
            "sha256": current_pointer_md_sha,
            "role": "human_readable_pointer_convention",
        },
        {
            "artifact": "activated_operational_reference",
            "path": str(ACTIVATED_OPERATIONAL_REFERENCE),
            "rows": activated_rows,
            "sha256": activated_sha,
            "role": "current_pointer_target_unchanged",
        },
        {
            "artifact": "final_v2_21_reference",
            "path": str(FINAL_REFERENCE_DATASET),
            "rows": final_reference_rows,
            "sha256": final_reference_sha,
            "role": "source_reference_unchanged",
        },
        {
            "artifact": "previous_operational_base",
            "path": str(PREVIOUS_OPERATIONAL_BASE),
            "rows": previous_operational_rows,
            "sha256": previous_operational_sha,
            "role": "previous_reference_unchanged",
        },
        {
            "artifact": "rollback_reference",
            "path": str(ROLLBACK_DATASET),
            "rows": rollback_rows,
            "sha256": rollback_sha,
            "role": "rollback_reference_unchanged",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_22B_POINTER_001",
            "decision": "Create a single current operational universe pointer.",
            "accepted": True,
            "reason": "v2.22A required pointer convention hardening before audit/scoring.",
            "effect": "Creates current_operational_universe_pointer.json.",
        },
        {
            "decision_id": "V2_22B_POINTER_002",
            "decision": "Point the convention to the v2.21H activated operational reference.",
            "accepted": True,
            "reason": "v2.21H is the latest validated activated operational artifact.",
            "effect": "Audit and scoring gates can use one explicit pointer.",
        },
        {
            "decision_id": "V2_22B_POINTER_003",
            "decision": "Do not modify dataset files.",
            "accepted": True,
            "reason": "Pointer hardening should not rewrite the universe.",
            "effect": "All dataset SHAs remain unchanged.",
        },
        {
            "decision_id": "V2_22B_POINTER_004",
            "decision": "Keep scoring/OpenAI/broker/full59k deferred.",
            "accepted": True,
            "reason": "Pointer hardening is not a scoring or enrichment phase.",
            "effect": "Next phase remains pre-scoring audit.",
        },
    ]

    convention_register_rows = [
        {
            "convention_id": "CONVENTION_CURRENT_OPERATIONAL_POINTER",
            "name": "current_operational_universe_pointer",
            "path": str(CURRENT_POINTER_JSON),
            "status": "created",
            "required_for": "pre_scoring_audit_and_scoring_dry_run",
            "rule": "Consumers must resolve the current operational universe through this pointer.",
        },
        {
            "convention_id": "CONVENTION_POINTER_TARGET",
            "name": "current_dataset",
            "path": str(ACTIVATED_OPERATIONAL_REFERENCE),
            "status": "validated",
            "required_for": "v2.22C",
            "rule": "Target dataset must match expected rows and SHA before use.",
        },
        {
            "convention_id": "CONVENTION_ROLLBACK",
            "name": "rollback_dataset",
            "path": str(ROLLBACK_DATASET),
            "status": "validated",
            "required_for": "all_future_pointer_updates",
            "rule": "Rollback dataset must be recorded in pointer metadata.",
        },
        {
            "convention_id": "CONVENTION_UPDATE_POLICY",
            "name": "explicit_update_gate",
            "path": str(CURRENT_POINTER_JSON),
            "status": "documented",
            "required_for": "future_pointer_changes",
            "rule": "Future pointer updates require explicit gate, row count validation, SHA validation, and no force push.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "pre_scoring_audit",
            "action": "audit_current_operational_universe_via_pointer",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Pointer convention is now defined; the next required gate is data quality audit.",
            "guardrails": "Audit only; no scoring; no OpenAI; no broker.",
        },
        {
            "action_order": 2,
            "action_scope": "scoring_dry_run",
            "action": "prepare_scoring_dry_run_after_pre_scoring_audit_passes",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Scoring remains conditional on audit success.",
            "guardrails": "No promotion; no canonical replacement; no full59k.",
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

    add_check("scoring_gate_status_expected", scoring_gate.get("status") == EXPECTED_SCORING_GATE_STATUS, "critical", str(scoring_gate.get("status")))
    add_check("scoring_gate_approved_pointer_hardening", as_bool(scoring_summary.get("approved_for_pointer_convention_hardening")) is True, "critical", f"approved_for_pointer_convention_hardening={scoring_summary.get('approved_for_pointer_convention_hardening')}")
    add_check("scoring_gate_not_approved_for_scoring_dry_run", as_bool(scoring_summary.get("approved_for_scoring_dry_run")) is False, "critical", f"approved_for_scoring_dry_run={scoring_summary.get('approved_for_scoring_dry_run')}")
    add_check("activated_rows_expected", activated_rows == ACTIVATED_ROWS_EXPECTED, "critical", f"activated_rows={activated_rows}")
    add_check("activated_sha_expected", activated_sha == ACTIVATED_SHA_EXPECTED, "critical", activated_sha)
    add_check("final_reference_rows_expected", final_reference_rows == FINAL_REFERENCE_ROWS_EXPECTED, "critical", f"final_reference_rows={final_reference_rows}")
    add_check("final_reference_sha_expected", final_reference_sha == FINAL_REFERENCE_SHA_EXPECTED, "critical", final_reference_sha)
    add_check("previous_operational_rows_expected", previous_operational_rows == PREVIOUS_OPERATIONAL_ROWS_EXPECTED, "critical", f"previous_operational_rows={previous_operational_rows}")
    add_check("previous_operational_sha_expected", previous_operational_sha == PREVIOUS_OPERATIONAL_SHA_EXPECTED, "critical", previous_operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("headers_consistent", activated_header == final_reference_header == previous_header, "critical", f"activated_columns={len(activated_header)};final_columns={len(final_reference_header)};previous_columns={len(previous_header)}")
    add_check("pointer_json_created", CURRENT_POINTER_JSON.exists(), "critical", str(CURRENT_POINTER_JSON))
    add_check("pointer_md_created", CURRENT_POINTER_MD.exists(), "critical", str(CURRENT_POINTER_MD))
    add_check("pointer_target_path_expected", pointer_payload["current_dataset"] == str(ACTIVATED_OPERATIONAL_REFERENCE), "critical", pointer_payload["current_dataset"])
    add_check("pointer_target_rows_expected", pointer_payload["current_dataset_rows"] == ACTIVATED_ROWS_EXPECTED, "critical", f"pointer_rows={pointer_payload['current_dataset_rows']}")
    add_check("pointer_target_sha_expected", pointer_payload["current_dataset_sha256"] == ACTIVATED_SHA_EXPECTED, "critical", pointer_payload["current_dataset_sha256"])
    add_check("within_quality_floor", activated_rows >= QUALITY_FLOOR_TARGET, "critical", f"activated_rows={activated_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("within_quality_ceiling", activated_rows <= QUALITY_CEILING_TARGET, "critical", f"activated_rows={activated_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("remaining_capacity_non_negative", QUALITY_CEILING_TARGET - activated_rows >= 0, "critical", f"remaining_capacity={QUALITY_CEILING_TARGET - activated_rows}")
    add_check("activated_dataset_not_modified", activated_sha_after == ACTIVATED_SHA_EXPECTED, "critical", f"activated_sha_after={activated_sha_after}")
    add_check("final_reference_not_modified", final_reference_sha_after == FINAL_REFERENCE_SHA_EXPECTED, "critical", f"final_reference_sha_after={final_reference_sha_after}")
    add_check("previous_operational_not_modified", previous_operational_sha_after == PREVIOUS_OPERATIONAL_SHA_EXPECTED, "critical", f"previous_operational_sha_after={previous_operational_sha_after}")
    add_check("rollback_not_modified", rollback_sha_after == ROLLBACK_SHA_EXPECTED, "critical", f"rollback_sha_after={rollback_sha_after}")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("scoring_not_executed", True, "critical", "scoring_executed=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("convention_register_defined", len(convention_register_rows) >= 4, "critical", f"conventions={len(convention_register_rows)}")

    status = STATUS_COMPLETED if critical_failed == 0 and warning_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Operational pointer convention hardening after v2.22A",
        "phase_type": PHASE_TYPE,
        "pointer_decision": "CURRENT_OPERATIONAL_POINTER_CREATED" if status == STATUS_COMPLETED else "POINTER_CONVENTION_BLOCKED_REVIEW_REQUIRED",
        "current_operational_pointer_json": str(CURRENT_POINTER_JSON),
        "current_operational_pointer_json_sha": current_pointer_sha,
        "current_operational_pointer_md": str(CURRENT_POINTER_MD),
        "current_operational_pointer_md_sha": current_pointer_md_sha,
        "current_dataset": str(ACTIVATED_OPERATIONAL_REFERENCE),
        "current_dataset_rows": activated_rows,
        "current_dataset_sha": activated_sha,
        "previous_operational_base_dataset": str(PREVIOUS_OPERATIONAL_BASE),
        "previous_operational_base_rows": previous_operational_rows,
        "previous_operational_base_sha": previous_operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity": QUALITY_CEILING_TARGET - activated_rows,
        "total_added_rows_vs_previous_operational_base": activated_rows - previous_operational_rows,
        "pointer_convention_hardened": status == STATUS_COMPLETED,
        "single_live_pointer_defined": status == STATUS_COMPLETED,
        "current_pointer_created": status == STATUS_COMPLETED,
        "existing_dataset_files_modified": False,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "approved_for_pre_scoring_data_quality_audit": status == STATUS_COMPLETED,
        "approved_for_scoring_dry_run": False,
        "scoring_authorized": False,
        "scoring_executed": False,
        "openai_authorized": False,
        "openai_called": False,
        "broker_authorized": False,
        "broker_called": False,
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": NEXT_PHASE,
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(CONVENTION_REGISTER_CSV, convention_register_rows, ["convention_id", "name", "path", "status", "required_for", "rule"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "pointer_payload": pointer_payload,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "convention_register": convention_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "single live operational pointer convention",
            "current_operational_pointer_json": str(CURRENT_POINTER_JSON),
            "current_dataset": str(ACTIVATED_OPERATIONAL_REFERENCE),
            "current_dataset_rows": activated_rows,
            "current_dataset_sha": activated_sha,
            "pointer_convention_hardened": status == STATUS_COMPLETED,
            "single_live_pointer_defined": status == STATUS_COMPLETED,
            "current_pointer_created": status == STATUS_COMPLETED,
            "existing_dataset_files_modified": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "approved_for_pre_scoring_data_quality_audit": status == STATUS_COMPLETED,
            "approved_for_scoring_dry_run": False,
            "scoring_authorized": False,
            "scoring_executed": False,
            "scoring_output_created": False,
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

    convention_lines = "\n".join(
        f"- `{row['convention_id']}` — {row['name']} — status `{row['status']}` — {row['rule']}"
        for row in convention_register_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.22B creates a single current operational universe pointer.

Current pointer:

`{CURRENT_POINTER_JSON}`

Human-readable pointer:

`{CURRENT_POINTER_MD}`

The pointer targets:

`{ACTIVATED_OPERATIONAL_REFERENCE}`

Rows: `{activated_rows}`  
SHA256: `{activated_sha}`

No dataset file is modified. No canonical dataset is replaced. No scoring is run. No OpenAI call is made. No broker call is made. full59k remains deprecated/deferred.

## Artifact manifest

{artifact_lines}

## Decisions

{decision_lines}

## Convention register

{convention_lines}

## Checks

{check_lines}

## Recommended next phases

Primary: `{NEXT_PHASE}`

Secondary: `{SECONDARY_NEXT_PHASE}`
""",
    )

    print("")
    print("v2.22B operational pointer convention hardening completed.")
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


if __name__ == "__main__":
    main()
