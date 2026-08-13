from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.23E"
PHASE = "Calibration Review / Freeze Decision"
PHASE_TYPE = "calibration-review-freeze-decision"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

FORMULA_DRY_RUN_JSON = OUTPUT_DIR / "scoring_formula_redesign_dry_run_v2_23d.json"
CALIBRATION_DATA_DESIGN_JSON = OUTPUT_DIR / "scoring_calibration_data_design_v2_23c.json"
METADATA_PLAN_JSON = OUTPUT_DIR / "metadata_coverage_improvement_plan_v2_23b.json"
CURRENT_POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
LEGACY_DRY_RUN_SCORES = OUTPUT_DIR / "scoring_dry_run_no_promotion_scores_v2_22d.csv"
REDESIGNED_SCORES = OUTPUT_DIR / "scoring_formula_redesign_dry_run_scores_v2_23d.csv"
REDESIGNED_DISTRIBUTION = OUTPUT_DIR / "scoring_formula_redesign_dry_run_distribution_v2_23d.csv"
REDESIGNED_COMPONENT_WEIGHTS = OUTPUT_DIR / "scoring_formula_redesign_dry_run_component_weights_v2_23d.csv"
REDESIGNED_ACCEPTANCE_REVIEW = OUTPUT_DIR / "scoring_formula_redesign_dry_run_acceptance_review_v2_23d.csv"

REPORT_JSON = OUTPUT_DIR / "calibration_review_freeze_decision_v2_23e.json"
REPORT_MD = OUTPUT_DIR / "calibration_review_freeze_decision_v2_23e.md"
SUMMARY_CSV = OUTPUT_DIR / "calibration_review_freeze_decision_summary_v2_23e.csv"
CHECKS_CSV = OUTPUT_DIR / "calibration_review_freeze_decision_checks_v2_23e.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "calibration_review_freeze_decision_artifact_manifest_v2_23e.csv"
FREEZE_REASONS_CSV = OUTPUT_DIR / "calibration_review_freeze_decision_freeze_reasons_v2_23e.csv"
PROMOTION_BLOCKERS_CSV = OUTPUT_DIR / "calibration_review_freeze_decision_promotion_blockers_v2_23e.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "calibration_review_freeze_decision_decision_register_v2_23e.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "calibration_review_freeze_decision_next_actions_v2_23e.csv"

EXPECTED_FORMULA_STATUS = "SCORING_FORMULA_REDESIGN_DRY_RUN_COMPLETED_NO_PROMOTION_NO_CANONICAL_CHANGE"
EXPECTED_CALDATA_STATUS = "SCORING_CALIBRATION_DATA_DESIGN_COMPLETED_NO_LABELS_NO_SCORING_NO_PROMOTION"
EXPECTED_METADATA_STATUS = "METADATA_COVERAGE_IMPROVEMENT_PLAN_COMPLETED_NO_DATASET_MODIFICATION"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

LEGACY_SCORING_ROWS_EXPECTED = 33498
LEGACY_SCORING_SHA_EXPECTED = "a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1"

REDESIGNED_SCORING_ROWS_EXPECTED = 33498
REDESIGNED_SCORING_SHA_EXPECTED = "096ab26fc05bf9f37d80d99ea934f41be12126b10295e506180bb5eb8ebb7edb"

STATUS_COMPLETED = "CALIBRATION_REVIEW_FREEZE_DECISION_COMPLETED_REDESIGNED_DRY_RUN_FROZEN_NOT_PROMOTED"
STATUS_FAILED = "CALIBRATION_REVIEW_FREEZE_DECISION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.23F - Calibration Closure Report"
SECONDARY_NEXT_PHASE = "v2.24A - Metadata Gap Audit"


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


def boolish(value: Any) -> bool:
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
        FREEZE_REASONS_CSV,
        PROMOTION_BLOCKERS_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    formula = read_json(FORMULA_DRY_RUN_JSON)
    caldata = read_json(CALIBRATION_DATA_DESIGN_JSON)
    metadata_plan = read_json(METADATA_PLAN_JSON)
    pointer = read_json(CURRENT_POINTER)

    formula_summary = formula.get("summary", {})
    caldata_summary = caldata.get("summary", {})
    metadata_summary = metadata_plan.get("summary", {})

    current_rows = count_csv_rows(CURRENT_DATASET)
    legacy_rows = count_csv_rows(LEGACY_DRY_RUN_SCORES)
    redesigned_rows = count_csv_rows(REDESIGNED_SCORES)
    distribution_rows = count_csv_rows(REDESIGNED_DISTRIBUTION)
    component_weight_rows = count_csv_rows(REDESIGNED_COMPONENT_WEIGHTS)
    acceptance_review_rows = count_csv_rows(REDESIGNED_ACCEPTANCE_REVIEW)

    current_sha = sha256_file(CURRENT_DATASET)
    legacy_sha = sha256_file(LEGACY_DRY_RUN_SCORES)
    redesigned_sha = sha256_file(REDESIGNED_SCORES)

    formula_sha = sha256_file(FORMULA_DRY_RUN_JSON)
    caldata_sha = sha256_file(CALIBRATION_DATA_DESIGN_JSON)
    metadata_plan_sha = sha256_file(METADATA_PLAN_JSON)
    pointer_sha = sha256_file(CURRENT_POINTER)
    distribution_sha = sha256_file(REDESIGNED_DISTRIBUTION)
    component_weights_sha = sha256_file(REDESIGNED_COMPONENT_WEIGHTS)
    acceptance_review_sha = sha256_file(REDESIGNED_ACCEPTANCE_REVIEW)

    manual_labels_created = boolish(formula_summary.get("manual_labels_created"))
    attractiveness_available = boolish(formula_summary.get("attractiveness_score_available"))
    attractiveness_invented = boolish(formula_summary.get("attractiveness_score_invented"))
    production_scoring_authorized_prior = boolish(formula_summary.get("production_scoring_authorized"))
    scoring_promoted_prior = boolish(formula_summary.get("scoring_promoted"))

    freeze_reasons_rows = [
        {
            "reason_id": "FREEZE_001",
            "reason": "Redesigned scoring was explicitly created as dry-run only.",
            "severity": "critical",
            "source_phase": "v2.23D",
            "effect": "Do not promote redesigned scores.",
        },
        {
            "reason_id": "FREEZE_002",
            "reason": "Manual labels do not exist yet.",
            "severity": "critical",
            "source_phase": "v2.23C/v2.23D",
            "effect": "No production calibration can be validated.",
        },
        {
            "reason_id": "FREEZE_003",
            "reason": "Attractiveness score is unavailable and was correctly not invented.",
            "severity": "critical",
            "source_phase": "v2.23D",
            "effect": "Ranking remains data-quality/scope/provider oriented, not an investment attractiveness ranking.",
        },
        {
            "reason_id": "FREEZE_004",
            "reason": "Metadata gaps remain blocking for production scoring readiness.",
            "severity": "high",
            "source_phase": "v2.23B",
            "effect": "Run metadata gap audit/improvement phases before any production promotion.",
        },
        {
            "reason_id": "FREEZE_005",
            "reason": "No separate authorization exists for OpenAI, broker APIs, full59k or external enrichment.",
            "severity": "critical",
            "source_phase": "project_guardrails",
            "effect": "Keep external enrichment disabled.",
        },
    ]

    promotion_blockers_rows = [
        {
            "blocker_id": "BLOCKER_001",
            "blocker": "manual_calibration_labels_missing",
            "blocking": True,
            "resolution_path": "Create and review labelled calibration sample in a future execution phase.",
        },
        {
            "blocker_id": "BLOCKER_002",
            "blocker": "attractiveness_score_unavailable",
            "blocking": True,
            "resolution_path": "Add manual labels or authorized financial/fundamental data source through a future gate.",
        },
        {
            "blocker_id": "BLOCKER_003",
            "blocker": "metadata_gap_remediation_not_executed",
            "blocking": True,
            "resolution_path": "Run v2.24 metadata gap audit and deterministic backfill planning/execution.",
        },
        {
            "blocker_id": "BLOCKER_004",
            "blocker": "no_production_scoring_gate_approved",
            "blocking": True,
            "resolution_path": "Use a future explicit production scoring promotion gate only after blockers are resolved.",
        },
        {
            "blocker_id": "BLOCKER_005",
            "blocker": "external_enrichment_not_authorized",
            "blocking": False,
            "resolution_path": "Optional future external enrichment gate; not needed for deterministic closure.",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_23E_FREEZE_001",
            "decision": "Freeze redesigned v2.23D dry-run scoring as non-promoted reference.",
            "accepted": True,
            "reason": "The redesigned score is useful for analysis but lacks manual labels and attractiveness validation.",
            "effect": "scoring_promoted=False; production_scoring_authorized=False.",
        },
        {
            "decision_id": "V2_23E_FREEZE_002",
            "decision": "Do not modify canonical dataset, active pointer or legacy dry-run score output.",
            "accepted": True,
            "reason": "This is a review/freeze decision phase.",
            "effect": "canonical_dataset_modified=False.",
        },
        {
            "decision_id": "V2_23E_FREEZE_003",
            "decision": "Close the calibration block next with v2.23F.",
            "accepted": True,
            "reason": "v2.23A-D produced roadmap, metadata plan, calibration-data design and redesigned dry run.",
            "effect": "recommended_next_phase=v2.23F.",
        },
        {
            "decision_id": "V2_23E_FREEZE_004",
            "decision": "Send metadata quality work to v2.24 instead of promoting scoring.",
            "accepted": True,
            "reason": "v2.23B identified blocking metadata gaps.",
            "effect": "secondary_next_phase=v2.24A.",
        },
        {
            "decision_id": "V2_23E_FREEZE_005",
            "decision": "Keep OpenAI, broker APIs and full59k disabled.",
            "accepted": True,
            "reason": "No separate authorization exists.",
            "effect": "openai_called=False; broker_called=False; full59k=DEPRECATED_DEFERRED.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "calibration_closure",
            "action": "close_v2_23_calibration_block",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "v2.23E freezes redesigned dry-run scoring as non-promoted reference.",
            "guardrails": "No production scoring; no canonical replacement.",
        },
        {
            "action_order": 2,
            "action_scope": "metadata_quality",
            "action": "start_metadata_gap_audit_after_v2_23_closure",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Metadata gaps remain the primary blocker before scoring promotion.",
            "guardrails": "Deterministic only; no full59k; no broker/OpenAI unless separately approved.",
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

    add_check("formula_status_expected", formula.get("status") == EXPECTED_FORMULA_STATUS, "critical", str(formula.get("status")))
    add_check("formula_critical_failed_checks_zero", str(formula_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={formula_summary.get('critical_failed_checks')}")
    add_check("calibration_data_design_status_expected", caldata.get("status") == EXPECTED_CALDATA_STATUS, "critical", str(caldata.get("status")))
    add_check("metadata_plan_status_expected", metadata_plan.get("status") == EXPECTED_METADATA_STATUS, "critical", str(metadata_plan.get("status")))
    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("legacy_scoring_rows_expected", legacy_rows == LEGACY_SCORING_ROWS_EXPECTED, "critical", f"legacy_rows={legacy_rows}")
    add_check("legacy_scoring_sha_expected", legacy_sha == LEGACY_SCORING_SHA_EXPECTED, "critical", legacy_sha)
    add_check("redesigned_scoring_rows_expected", redesigned_rows == REDESIGNED_SCORING_ROWS_EXPECTED, "critical", f"redesigned_rows={redesigned_rows}")
    add_check("redesigned_scoring_sha_expected", redesigned_sha == REDESIGNED_SCORING_SHA_EXPECTED, "critical", redesigned_sha)
    add_check("distribution_rows_expected", distribution_rows == 5, "critical", f"distribution_rows={distribution_rows}")
    add_check("component_weight_rows_expected", component_weight_rows == 4, "critical", f"component_weight_rows={component_weight_rows}")
    add_check("acceptance_review_rows_expected", acceptance_review_rows == 5, "critical", f"acceptance_review_rows={acceptance_review_rows}")
    add_check("manual_labels_absent", manual_labels_created is False, "critical", f"manual_labels_created={manual_labels_created}")
    add_check("attractiveness_score_not_available", attractiveness_available is False, "critical", f"attractiveness_score_available={attractiveness_available}")
    add_check("attractiveness_score_not_invented", attractiveness_invented is False, "critical", f"attractiveness_score_invented={attractiveness_invented}")
    add_check("prior_production_scoring_not_authorized", production_scoring_authorized_prior is False, "critical", f"prior_production_scoring_authorized={production_scoring_authorized_prior}")
    add_check("prior_scoring_not_promoted", scoring_promoted_prior is False, "critical", f"prior_scoring_promoted={scoring_promoted_prior}")
    add_check("freeze_reasons_defined", len(freeze_reasons_rows) >= 5, "critical", f"freeze_reasons={len(freeze_reasons_rows)}")
    add_check("promotion_blockers_defined", len(promotion_blockers_rows) >= 5, "critical", f"promotion_blockers={len(promotion_blockers_rows)}")
    add_check("promotion_decision_false", True, "critical", "promotion_approved=False")
    add_check("production_scoring_not_authorized", True, "critical", "production_scoring_authorized=False")
    add_check("canonical_dataset_not_modified", sha256_file(CURRENT_DATASET) == CURRENT_SHA_EXPECTED, "critical", f"current_sha_after={sha256_file(CURRENT_DATASET)}")
    add_check("redesigned_score_output_not_modified", sha256_file(REDESIGNED_SCORES) == REDESIGNED_SCORING_SHA_EXPECTED, "critical", f"redesigned_sha_after={sha256_file(REDESIGNED_SCORES)}")
    add_check("legacy_score_output_not_modified", sha256_file(LEGACY_DRY_RUN_SCORES) == LEGACY_SCORING_SHA_EXPECTED, "critical", f"legacy_sha_after={sha256_file(LEGACY_DRY_RUN_SCORES)}")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    status = STATUS_COMPLETED if critical_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Calibration review and freeze decision for redesigned scoring dry run",
        "phase_type": PHASE_TYPE,
        "freeze_decision": "FREEZE_REDESIGNED_DRY_RUN_AS_NON_PROMOTED_REFERENCE" if status == STATUS_COMPLETED else "FREEZE_DECISION_FAILED_REVIEW_REQUIRED",
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows,
        "current_dataset_sha": current_sha,
        "legacy_dry_run_scoring_output": str(LEGACY_DRY_RUN_SCORES),
        "legacy_dry_run_scoring_output_rows": legacy_rows,
        "legacy_dry_run_scoring_output_sha": legacy_sha,
        "redesigned_scoring_output": str(REDESIGNED_SCORES),
        "redesigned_scoring_output_rows": redesigned_rows,
        "redesigned_scoring_output_sha": redesigned_sha,
        "redesigned_score_min": formula_summary.get("redesigned_score_min"),
        "redesigned_score_p25": formula_summary.get("redesigned_score_p25"),
        "redesigned_score_median": formula_summary.get("redesigned_score_median"),
        "redesigned_score_p75": formula_summary.get("redesigned_score_p75"),
        "redesigned_score_max": formula_summary.get("redesigned_score_max"),
        "redesigned_score_mean": formula_summary.get("redesigned_score_mean"),
        "mean_delta_vs_v2_22d": formula_summary.get("mean_delta_vs_v2_22d"),
        "data_quality_score_separated": True,
        "attractiveness_score_available": False,
        "attractiveness_score_invented": False,
        "manual_labels_created": False,
        "freeze_reasons": len(freeze_reasons_rows),
        "promotion_blockers": len(promotion_blockers_rows),
        "promotion_approved": False,
        "production_scoring_authorized": False,
        "scoring_promoted": False,
        "canonical_dataset_modified": False,
        "active_pointer_modified": False,
        "redesigned_score_output_modified": False,
        "legacy_score_output_modified": False,
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
            "artifact": "formula_dry_run_input",
            "path": str(FORMULA_DRY_RUN_JSON),
            "rows": 1,
            "sha256": formula_sha,
            "role": "input_redesigned_formula_dry_run",
        },
        {
            "artifact": "calibration_data_design_input",
            "path": str(CALIBRATION_DATA_DESIGN_JSON),
            "rows": 1,
            "sha256": caldata_sha,
            "role": "input_calibration_data_design",
        },
        {
            "artifact": "metadata_plan_input",
            "path": str(METADATA_PLAN_JSON),
            "rows": 1,
            "sha256": metadata_plan_sha,
            "role": "input_metadata_plan",
        },
        {
            "artifact": "current_operational_pointer_input",
            "path": str(CURRENT_POINTER),
            "rows": 1,
            "sha256": pointer_sha,
            "role": "input_pointer_no_modification",
        },
        {
            "artifact": "current_dataset_input",
            "path": str(CURRENT_DATASET),
            "rows": current_rows,
            "sha256": current_sha,
            "role": "input_dataset_no_modification",
        },
        {
            "artifact": "legacy_dry_run_scores_input",
            "path": str(LEGACY_DRY_RUN_SCORES),
            "rows": legacy_rows,
            "sha256": legacy_sha,
            "role": "input_legacy_scores_no_modification",
        },
        {
            "artifact": "redesigned_scores_input",
            "path": str(REDESIGNED_SCORES),
            "rows": redesigned_rows,
            "sha256": redesigned_sha,
            "role": "input_redesigned_scores_no_modification_not_promoted",
        },
        {
            "artifact": "redesigned_distribution_input",
            "path": str(REDESIGNED_DISTRIBUTION),
            "rows": distribution_rows,
            "sha256": distribution_sha,
            "role": "input_distribution_no_modification",
        },
        {
            "artifact": "redesigned_component_weights_input",
            "path": str(REDESIGNED_COMPONENT_WEIGHTS),
            "rows": component_weight_rows,
            "sha256": component_weights_sha,
            "role": "input_component_weights_no_modification",
        },
        {
            "artifact": "redesigned_acceptance_review_input",
            "path": str(REDESIGNED_ACCEPTANCE_REVIEW),
            "rows": acceptance_review_rows,
            "sha256": acceptance_review_sha,
            "role": "input_acceptance_review_no_modification",
        },
    ]

    write_csv(FREEZE_REASONS_CSV, freeze_reasons_rows, ["reason_id", "reason", "severity", "source_phase", "effect"])
    write_csv(PROMOTION_BLOCKERS_CSV, promotion_blockers_rows, ["blocker_id", "blocker", "blocking", "resolution_path"])

    freeze_reasons_sha = sha256_file(FREEZE_REASONS_CSV)
    promotion_blockers_sha = sha256_file(PROMOTION_BLOCKERS_CSV)

    artifact_manifest_rows.extend([
        {
            "artifact": "freeze_reasons_output",
            "path": str(FREEZE_REASONS_CSV),
            "rows": len(freeze_reasons_rows),
            "sha256": freeze_reasons_sha,
            "role": "freeze_decision_reasons_output",
        },
        {
            "artifact": "promotion_blockers_output",
            "path": str(PROMOTION_BLOCKERS_CSV),
            "rows": len(promotion_blockers_rows),
            "sha256": promotion_blockers_sha,
            "role": "promotion_blockers_output",
        },
    ])

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    report = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "freeze_reasons": freeze_reasons_rows,
        "promotion_blockers": promotion_blockers_rows,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "current_dataset": str(CURRENT_DATASET),
            "current_dataset_rows": current_rows,
            "current_dataset_sha": current_sha,
            "legacy_dry_run_score_output": str(LEGACY_DRY_RUN_SCORES),
            "legacy_dry_run_score_output_rows": legacy_rows,
            "legacy_dry_run_score_output_sha": legacy_sha,
            "redesigned_scoring_output": str(REDESIGNED_SCORES),
            "redesigned_scoring_output_rows": redesigned_rows,
            "redesigned_scoring_output_sha": redesigned_sha,
            "promotion_approved": False,
            "production_scoring_authorized": False,
            "scoring_promoted": False,
            "active_pointer_modified": False,
            "canonical_dataset_modified": False,
            "redesigned_score_output_modified": False,
            "legacy_score_output_modified": False,
            "manual_labels_created": False,
            "attractiveness_score_available": False,
            "attractiveness_score_invented": False,
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

    freeze_lines = "\n".join(
        f"- `{row['reason_id']}` — {row['severity']} — {row['reason']}"
        for row in freeze_reasons_rows
    )

    blocker_lines = "\n".join(
        f"- `{row['blocker_id']}` — blocking `{row['blocking']}` — {row['blocker']}"
        for row in promotion_blockers_rows
    )

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{report["generated_at_utc"]}`

## Decision

Freeze decision: **{summary["freeze_decision"]}**

The redesigned v2.23D dry-run scoring is frozen as a non-promoted reference.

It is useful for review, but it is **not** production scoring.

## Reasons

{freeze_lines}

## Promotion blockers

{blocker_lines}

## Score reference

Redesigned dry-run output:

`{REDESIGNED_SCORES}`

Rows: `{redesigned_rows}`  
SHA256: `{redesigned_sha}`

- Redesigned min: `{summary["redesigned_score_min"]}`
- Redesigned p25: `{summary["redesigned_score_p25"]}`
- Redesigned median: `{summary["redesigned_score_median"]}`
- Redesigned p75: `{summary["redesigned_score_p75"]}`
- Redesigned max: `{summary["redesigned_score_max"]}`
- Redesigned mean: `{summary["redesigned_score_mean"]}`

## Guardrails

- Promotion approved: `False`
- Production scoring authorized: `False`
- Scoring promoted: `False`
- Active pointer modified: `False`
- Canonical dataset modified: `False`
- Redesigned score output modified: `False`
- Legacy score output modified: `False`
- Manual labels created: `False`
- Attractiveness score invented: `False`
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
    print("v2.23E calibration review freeze decision completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("FREEZE_REASONS:")
    for row in freeze_reasons_rows:
        print(f"- {row['reason_id']}: {row['severity']} - {row['reason']}")
    print("")
    print("PROMOTION_BLOCKERS:")
    for row in promotion_blockers_rows:
        print(f"- {row['blocker_id']}: blocking={row['blocking']} - {row['blocker']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
