from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.22E"
PHASE = "Scoring Promotion / Freeze Decision"
PHASE_TYPE = "scoring-promotion-freeze-decision"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

SCORING_DRY_RUN_JSON = OUTPUT_DIR / "scoring_dry_run_no_promotion_v2_22d.json"
SCORING_DRY_RUN_SCORES = OUTPUT_DIR / "scoring_dry_run_no_promotion_scores_v2_22d.csv"
SCORING_DRY_RUN_DISTRIBUTION = OUTPUT_DIR / "scoring_dry_run_no_promotion_score_distribution_v2_22d.csv"
SCORING_DRY_RUN_COMPONENTS = OUTPUT_DIR / "scoring_dry_run_no_promotion_score_components_v2_22d.csv"
SCORING_DRY_RUN_EXCLUDED = OUTPUT_DIR / "scoring_dry_run_no_promotion_excluded_summary_v2_22d.csv"

CURRENT_POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

REPORT_JSON = OUTPUT_DIR / "scoring_promotion_freeze_decision_v2_22e.json"
REPORT_MD = OUTPUT_DIR / "scoring_promotion_freeze_decision_v2_22e.md"
SUMMARY_CSV = OUTPUT_DIR / "scoring_promotion_freeze_decision_summary_v2_22e.csv"
CHECKS_CSV = OUTPUT_DIR / "scoring_promotion_freeze_decision_checks_v2_22e.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "scoring_promotion_freeze_decision_artifact_manifest_v2_22e.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "scoring_promotion_freeze_decision_decision_register_v2_22e.csv"
PROMOTION_POLICY_CSV = OUTPUT_DIR / "scoring_promotion_freeze_decision_policy_v2_22e.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "scoring_promotion_freeze_decision_next_actions_v2_22e.csv"

EXPECTED_DRY_RUN_STATUS = "SCORING_DRY_RUN_NO_PROMOTION_COMPLETED_LOCAL_HEURISTIC_SCORES_CREATED_PROMOTION_DEFERRED"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

EXPECTED_SCORABLE_ROWS = 33498
EXPECTED_EXCLUDED_ROWS = 9591
EXPECTED_SCORE_MEAN = "58.2468"
EXPECTED_SCORE_MEDIAN = "52.2"
EXPECTED_SCORE_MAX = "87.2"
EXPECTED_SCORE_MIN = "44.7"

STATUS_COMPLETED = "SCORING_PROMOTION_FREEZE_DECISION_COMPLETED_DRY_RUN_FROZEN_NOT_PROMOTED"
STATUS_FAILED = "SCORING_PROMOTION_FREEZE_DECISION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.22F - Repo Hygiene / Untracked Files Review"
SECONDARY_NEXT_PHASE = "v2.23A - Scoring Model Calibration Roadmap"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        raise SystemExit(f"Missing required CSV artifact: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV artifact: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def write_text(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        DECISION_REGISTER_CSV,
        PROMOTION_POLICY_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    dry_run = read_json(SCORING_DRY_RUN_JSON)
    dry_summary = dry_run.get("summary", {})

    pointer = read_json(CURRENT_POINTER)

    current_rows = count_csv_rows(CURRENT_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    scoring_rows = count_csv_rows(SCORING_DRY_RUN_SCORES)
    distribution_rows = count_csv_rows(SCORING_DRY_RUN_DISTRIBUTION)
    component_rows = count_csv_rows(SCORING_DRY_RUN_COMPONENTS)
    excluded_summary_rows = count_csv_rows(SCORING_DRY_RUN_EXCLUDED)

    current_sha = sha256_file(CURRENT_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    pointer_sha = sha256_file(CURRENT_POINTER)
    dry_run_sha = sha256_file(SCORING_DRY_RUN_JSON)
    scores_sha = sha256_file(SCORING_DRY_RUN_SCORES)
    distribution_sha = sha256_file(SCORING_DRY_RUN_DISTRIBUTION)
    components_sha = sha256_file(SCORING_DRY_RUN_COMPONENTS)
    excluded_sha = sha256_file(SCORING_DRY_RUN_EXCLUDED)

    promotion_decision = "FREEZE_DRY_RUN_SCORE_OUTPUT_AS_NON_PROMOTED_REFERENCE"
    promotion_approved = False
    scoring_promoted = False
    production_scoring_authorized = False

    reasons_to_freeze = [
        "v2.22D was explicitly dry-run/no-promotion.",
        "Scores are local deterministic heuristic scores, not calibrated production scores.",
        "top_country_by_scorable_rows is __MISSING__, indicating metadata coverage should be improved before promotion.",
        "Promotion/canonical replacement requires a separate explicit future gate.",
        "OpenAI, broker enrichment, and full59k remain unauthorized/deferred.",
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

    add_check("dry_run_status_expected", dry_run.get("status") == EXPECTED_DRY_RUN_STATUS, "critical", str(dry_run.get("status")))
    add_check("dry_run_critical_failed_checks_zero", str(dry_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={dry_summary.get('critical_failed_checks')}")
    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("scoring_rows_expected", scoring_rows == EXPECTED_SCORABLE_ROWS, "critical", f"scoring_rows={scoring_rows}")
    add_check("excluded_rows_expected", str(dry_summary.get("excluded_from_common_equity_scoring_rows")) == str(EXPECTED_EXCLUDED_ROWS), "critical", f"excluded={dry_summary.get('excluded_from_common_equity_scoring_rows')}")
    add_check("score_min_expected", str(dry_summary.get("score_min")) == EXPECTED_SCORE_MIN, "critical", f"score_min={dry_summary.get('score_min')}")
    add_check("score_median_expected", str(dry_summary.get("score_median")) == EXPECTED_SCORE_MEDIAN, "critical", f"score_median={dry_summary.get('score_median')}")
    add_check("score_max_expected", str(dry_summary.get("score_max")) == EXPECTED_SCORE_MAX, "critical", f"score_max={dry_summary.get('score_max')}")
    add_check("score_mean_expected", str(dry_summary.get("score_mean")) == EXPECTED_SCORE_MEAN, "critical", f"score_mean={dry_summary.get('score_mean')}")
    add_check("distribution_rows_expected", distribution_rows == 5, "critical", f"distribution_rows={distribution_rows}")
    add_check("component_rows_expected", component_rows == 6, "critical", f"component_rows={component_rows}")
    add_check("excluded_summary_rows_expected", excluded_summary_rows == 16, "critical", f"excluded_summary_rows={excluded_summary_rows}")
    add_check("promotion_not_approved", promotion_approved is False, "critical", "promotion_approved=False")
    add_check("scoring_not_promoted", scoring_promoted is False, "critical", "scoring_promoted=False")
    add_check("production_scoring_not_authorized", production_scoring_authorized is False, "critical", "production_scoring_authorized=False")
    add_check("canonical_dataset_not_modified", sha256_file(CURRENT_DATASET) == CURRENT_SHA_EXPECTED, "critical", f"current_sha_after={sha256_file(CURRENT_DATASET)}")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    status = STATUS_COMPLETED if critical_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Scoring dry-run promotion/freeze decision",
        "phase_type": PHASE_TYPE,
        "promotion_decision": promotion_decision,
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows,
        "current_dataset_sha": current_sha,
        "scoring_dry_run_report": str(SCORING_DRY_RUN_JSON),
        "scoring_dry_run_report_sha": dry_run_sha,
        "scoring_output": str(SCORING_DRY_RUN_SCORES),
        "scoring_output_rows": scoring_rows,
        "scoring_output_sha": scores_sha,
        "score_min": dry_summary.get("score_min"),
        "score_p25": dry_summary.get("score_p25"),
        "score_median": dry_summary.get("score_median"),
        "score_p75": dry_summary.get("score_p75"),
        "score_max": dry_summary.get("score_max"),
        "score_mean": dry_summary.get("score_mean"),
        "excluded_from_common_equity_scoring_rows": dry_summary.get("excluded_from_common_equity_scoring_rows"),
        "scorable_rows": dry_summary.get("scorable_rows"),
        "top_exchange_by_scorable_rows": dry_summary.get("top_exchange_by_scorable_rows"),
        "top_country_by_scorable_rows": dry_summary.get("top_country_by_scorable_rows"),
        "top_source_provider_by_scorable_rows": dry_summary.get("top_source_provider_by_scorable_rows"),
        "dry_run_scoring_authorized": True,
        "dry_run_scoring_executed": True,
        "promotion_approved": promotion_approved,
        "scoring_promoted": scoring_promoted,
        "production_scoring_authorized": production_scoring_authorized,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
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

    artifact_manifest_rows = [
        {
            "artifact": "current_operational_pointer_input",
            "path": str(CURRENT_POINTER),
            "rows": 1,
            "sha256": pointer_sha,
            "role": "input_pointer",
        },
        {
            "artifact": "current_dataset_input",
            "path": str(CURRENT_DATASET),
            "rows": current_rows,
            "sha256": current_sha,
            "role": "input_dataset_no_modification",
        },
        {
            "artifact": "scoring_dry_run_report_input",
            "path": str(SCORING_DRY_RUN_JSON),
            "rows": 1,
            "sha256": dry_run_sha,
            "role": "input_dry_run_report",
        },
        {
            "artifact": "scoring_output_frozen_reference",
            "path": str(SCORING_DRY_RUN_SCORES),
            "rows": scoring_rows,
            "sha256": scores_sha,
            "role": "dry_run_scores_frozen_not_promoted",
        },
        {
            "artifact": "score_distribution_input",
            "path": str(SCORING_DRY_RUN_DISTRIBUTION),
            "rows": distribution_rows,
            "sha256": distribution_sha,
            "role": "score_distribution_reference",
        },
        {
            "artifact": "score_components_input",
            "path": str(SCORING_DRY_RUN_COMPONENTS),
            "rows": component_rows,
            "sha256": components_sha,
            "role": "score_component_reference",
        },
        {
            "artifact": "excluded_summary_input",
            "path": str(SCORING_DRY_RUN_EXCLUDED),
            "rows": excluded_summary_rows,
            "sha256": excluded_sha,
            "role": "excluded_policy_reference",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_22E_FREEZE_001",
            "decision": "Freeze v2.22D scoring dry run as non-promoted reference.",
            "accepted": True,
            "reason": reasons_to_freeze[0],
            "effect": "Dry-run scores remain available for review but are not promoted.",
        },
        {
            "decision_id": "V2_22E_FREEZE_002",
            "decision": "Do not replace canonical or active operational dataset.",
            "accepted": True,
            "reason": "v2.22D is heuristic and not calibrated for production scoring.",
            "effect": "canonical_dataset_modified=False; active_canonical_replaced=False.",
        },
        {
            "decision_id": "V2_22E_FREEZE_003",
            "decision": "Defer production scoring authorization.",
            "accepted": True,
            "reason": "Scoring model calibration and metadata coverage should be reviewed separately.",
            "effect": "production_scoring_authorized=False.",
        },
        {
            "decision_id": "V2_22E_FREEZE_004",
            "decision": "Keep OpenAI, broker APIs and full59k disabled.",
            "accepted": True,
            "reason": "No external enrichment was authorized for this roadmap segment.",
            "effect": "openai_called=False; broker_called=False; full59k=DEPRECATED_DEFERRED.",
        },
    ]

    policy_rows = [
        {
            "policy_id": "PROMOTION_POLICY_001",
            "rule": "Dry-run score output may be reviewed but not used as production scoring.",
            "decision": "freeze_not_promote",
        },
        {
            "policy_id": "PROMOTION_POLICY_002",
            "rule": "No canonical replacement without explicit future promotion gate.",
            "decision": "no_canonical_replacement",
        },
        {
            "policy_id": "PROMOTION_POLICY_003",
            "rule": "Future production scoring requires model calibration and metadata coverage review.",
            "decision": "defer_to_v2_23a_or_later",
        },
        {
            "policy_id": "PROMOTION_POLICY_004",
            "rule": "Untracked repo hygiene files remain excluded from this phase.",
            "decision": "defer_to_v2_22f",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "repo_hygiene",
            "action": "review_untracked_audit_and_country_breakdown_files",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Only unrelated untracked files remain in git status.",
            "guardrails": "Do not add docx/country_breakdown files automatically.",
        },
        {
            "action_order": 2,
            "action_scope": "scoring_model",
            "action": "plan_scoring_model_calibration_before_any_production_promotion",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Dry-run score is useful but heuristic.",
            "guardrails": "No production scoring without explicit future gate.",
        },
    ]

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(PROMOTION_POLICY_CSV, policy_rows, ["policy_id", "rule", "decision"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    report = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "reasons_to_freeze": reasons_to_freeze,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "promotion_policy": policy_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "promotion_decision": promotion_decision,
            "current_dataset": str(CURRENT_DATASET),
            "current_dataset_rows": current_rows,
            "current_dataset_sha": current_sha,
            "scoring_output": str(SCORING_DRY_RUN_SCORES),
            "scoring_output_rows": scoring_rows,
            "dry_run_scoring_authorized": True,
            "dry_run_scoring_executed": True,
            "promotion_approved": promotion_approved,
            "scoring_promoted": scoring_promoted,
            "production_scoring_authorized": production_scoring_authorized,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
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

    write_json(REPORT_JSON, report)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    freeze_lines = "\n".join(f"- {reason}" for reason in reasons_to_freeze)

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{report["generated_at_utc"]}`

## Decision

Promotion decision: **{promotion_decision}**

The v2.22D scoring dry run is frozen as a non-promoted reference artifact.

## Reasons to freeze

{freeze_lines}

## Dry-run scoring reference

`{SCORING_DRY_RUN_SCORES}`

Rows: `{scoring_rows}`  
SHA256: `{scores_sha}`

## Score summary

- Min: `{dry_summary.get("score_min")}`
- P25: `{dry_summary.get("score_p25")}`
- Median: `{dry_summary.get("score_median")}`
- P75: `{dry_summary.get("score_p75")}`
- Max: `{dry_summary.get("score_max")}`
- Mean: `{dry_summary.get("score_mean")}`

## Guardrails

- Promotion approved: `{promotion_approved}`
- Scoring promoted: `{scoring_promoted}`
- Production scoring authorized: `{production_scoring_authorized}`
- Canonical dataset modified: `False`
- Active canonical replaced: `False`
- OpenAI called: `False`
- Broker called: `False`
- full59k: `DEPRECATED_DEFERRED`

## Checks

{check_lines}

## Recommended next phase

Primary: `{NEXT_PHASE}`

Secondary: `{SECONDARY_NEXT_PHASE}`
""",
    )

    print("")
    print("v2.22E scoring promotion / freeze decision completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("REASONS_TO_FREEZE:")
    for reason in reasons_to_freeze:
        print(f"- {reason}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
