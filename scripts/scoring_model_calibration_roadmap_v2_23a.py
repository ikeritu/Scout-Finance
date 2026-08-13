from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.23A"
PHASE = "Scoring Model Calibration Roadmap"
PHASE_TYPE = "scoring-model-calibration-roadmap"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

HYGIENE_REPORT = OUTPUT_DIR / "repo_hygiene_untracked_files_review_v2_22f.json"
FREEZE_REPORT = OUTPUT_DIR / "scoring_promotion_freeze_decision_v2_22e.json"
DRY_RUN_REPORT = OUTPUT_DIR / "scoring_dry_run_no_promotion_v2_22d.json"
DRY_RUN_SCORES = OUTPUT_DIR / "scoring_dry_run_no_promotion_scores_v2_22d.csv"
DRY_RUN_DISTRIBUTION = OUTPUT_DIR / "scoring_dry_run_no_promotion_score_distribution_v2_22d.csv"
DRY_RUN_COMPONENTS = OUTPUT_DIR / "scoring_dry_run_no_promotion_score_components_v2_22d.csv"

CURRENT_POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"

REPORT_JSON = OUTPUT_DIR / "scoring_model_calibration_roadmap_v2_23a.json"
REPORT_MD = OUTPUT_DIR / "scoring_model_calibration_roadmap_v2_23a.md"
SUMMARY_CSV = OUTPUT_DIR / "scoring_model_calibration_roadmap_summary_v2_23a.csv"
CHECKS_CSV = OUTPUT_DIR / "scoring_model_calibration_roadmap_checks_v2_23a.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "scoring_model_calibration_roadmap_artifact_manifest_v2_23a.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "scoring_model_calibration_roadmap_decision_register_v2_23a.csv"
CALIBRATION_REQUIREMENTS_CSV = OUTPUT_DIR / "scoring_model_calibration_roadmap_requirements_v2_23a.csv"
CALIBRATION_PHASES_CSV = OUTPUT_DIR / "scoring_model_calibration_roadmap_phases_v2_23a.csv"
CALIBRATION_RISKS_CSV = OUTPUT_DIR / "scoring_model_calibration_roadmap_risks_v2_23a.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "scoring_model_calibration_roadmap_next_actions_v2_23a.csv"

EXPECTED_HYGIENE_STATUS = "REPO_HYGIENE_UNTRACKED_FILES_REVIEW_COMPLETED_UNTRACKED_FILES_CLASSIFIED_NO_AUTO_ADD"
EXPECTED_FREEZE_STATUS = "SCORING_PROMOTION_FREEZE_DECISION_COMPLETED_DRY_RUN_FROZEN_NOT_PROMOTED"
EXPECTED_DRY_RUN_STATUS = "SCORING_DRY_RUN_NO_PROMOTION_COMPLETED_LOCAL_HEURISTIC_SCORES_CREATED_PROMOTION_DEFERRED"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

SCORING_OUTPUT_ROWS_EXPECTED = 33498
SCORING_OUTPUT_SHA_EXPECTED = "a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1"

STATUS_COMPLETED = "SCORING_MODEL_CALIBRATION_ROADMAP_COMPLETED_PRODUCTION_SCORING_DEFERRED"
STATUS_FAILED = "SCORING_MODEL_CALIBRATION_ROADMAP_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.23B - Metadata Coverage Improvement Plan"
SECONDARY_NEXT_PHASE = "v2.23C - Scoring Calibration Data Design"


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


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        DECISION_REGISTER_CSV,
        CALIBRATION_REQUIREMENTS_CSV,
        CALIBRATION_PHASES_CSV,
        CALIBRATION_RISKS_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    hygiene = read_json(HYGIENE_REPORT)
    freeze = read_json(FREEZE_REPORT)
    dry_run = read_json(DRY_RUN_REPORT)
    pointer = read_json(CURRENT_POINTER)

    hygiene_summary = hygiene.get("summary", {})
    freeze_summary = freeze.get("summary", {})
    dry_summary = dry_run.get("summary", {})

    current_rows = count_csv_rows(CURRENT_DATASET)
    scoring_rows = count_csv_rows(DRY_RUN_SCORES)
    distribution_rows = count_csv_rows(DRY_RUN_DISTRIBUTION)
    components_rows = count_csv_rows(DRY_RUN_COMPONENTS)

    current_sha = sha256_file(CURRENT_DATASET)
    scoring_sha = sha256_file(DRY_RUN_SCORES)

    hygiene_sha = sha256_file(HYGIENE_REPORT)
    freeze_sha = sha256_file(FREEZE_REPORT)
    dry_run_sha = sha256_file(DRY_RUN_REPORT)
    pointer_sha = sha256_file(CURRENT_POINTER)
    distribution_sha = sha256_file(DRY_RUN_DISTRIBUTION)
    components_sha = sha256_file(DRY_RUN_COMPONENTS)

    requirements_rows = [
        {
            "requirement_id": "CAL_REQ_001",
            "requirement": "Define target scoring objective before production.",
            "priority": "critical",
            "current_status": "missing_explicit_objective",
            "reason": "v2.22D created local heuristic scores but did not define a production ranking objective.",
            "required_before_production": True,
        },
        {
            "requirement_id": "CAL_REQ_002",
            "requirement": "Improve metadata coverage for country, MIC, currency, asset_type and source_provider before production scoring.",
            "priority": "critical",
            "current_status": "metadata_coverage_gap_known",
            "reason": "v2.22D top_country_by_scorable_rows was __MISSING__.",
            "required_before_production": True,
        },
        {
            "requirement_id": "CAL_REQ_003",
            "requirement": "Create benchmark sample with manually reviewed good/bad scoring examples.",
            "priority": "critical",
            "current_status": "not_created",
            "reason": "No labelled calibration set exists yet.",
            "required_before_production": True,
        },
        {
            "requirement_id": "CAL_REQ_004",
            "requirement": "Separate data-quality score from investment/attractiveness score.",
            "priority": "high",
            "current_status": "not_separated",
            "reason": "v2.22D local heuristic mostly measures data completeness/provenance, not financial attractiveness.",
            "required_before_production": True,
        },
        {
            "requirement_id": "CAL_REQ_005",
            "requirement": "Define exclusion overlay as reusable production input if accepted.",
            "priority": "high",
            "current_status": "dry_run_overlay_exists",
            "reason": "v2.22C2 created a non-common-equity exclusion overlay that worked for v2.22D.",
            "required_before_production": True,
        },
        {
            "requirement_id": "CAL_REQ_006",
            "requirement": "Keep OpenAI, broker APIs and full59k disabled unless a separate future gate authorizes them.",
            "priority": "critical",
            "current_status": "disabled",
            "reason": "Current roadmap did not authorize external enrichment or full59k.",
            "required_before_production": True,
        },
    ]

    phases_rows = [
        {
            "phase_id": "v2.23B",
            "phase_name": "Metadata Coverage Improvement Plan",
            "purpose": "Design improvements for country, MIC, currency, asset_type, source_provider and classification coverage.",
            "output_type": "roadmap_and_validation_plan",
            "promotion_allowed": False,
            "canonical_modification_allowed": False,
        },
        {
            "phase_id": "v2.23C",
            "phase_name": "Scoring Calibration Data Design",
            "purpose": "Define manual benchmark sample, labelled cases and score acceptance criteria.",
            "output_type": "calibration_dataset_design",
            "promotion_allowed": False,
            "canonical_modification_allowed": False,
        },
        {
            "phase_id": "v2.23D",
            "phase_name": "Scoring Formula Redesign Dry Run",
            "purpose": "Create a redesigned deterministic scoring formula in dry-run mode only.",
            "output_type": "dry_run_scores",
            "promotion_allowed": False,
            "canonical_modification_allowed": False,
        },
        {
            "phase_id": "v2.23E",
            "phase_name": "Calibration Review / Freeze Decision",
            "purpose": "Decide whether redesigned dry-run scoring is still frozen or ready for a future promotion gate.",
            "output_type": "decision_gate",
            "promotion_allowed": False,
            "canonical_modification_allowed": False,
        },
    ]

    risks_rows = [
        {
            "risk_id": "CAL_RISK_001",
            "risk": "Current score can over-reward providers with complete metadata rather than genuinely better assets.",
            "severity": "high",
            "mitigation": "Split data-quality score from investment/selection score.",
        },
        {
            "risk_id": "CAL_RISK_002",
            "risk": "Missing country values dominate scorable rows.",
            "severity": "high",
            "mitigation": "Run metadata coverage improvement before production scoring.",
        },
        {
            "risk_id": "CAL_RISK_003",
            "risk": "Dry-run output could be mistaken for production ranking.",
            "severity": "critical",
            "mitigation": "Keep promotion_approved=False and production_scoring_authorized=False.",
        },
        {
            "risk_id": "CAL_RISK_004",
            "risk": "External enrichment may change score semantics if introduced without a gate.",
            "severity": "medium",
            "mitigation": "Keep OpenAI and broker APIs disabled unless separately approved.",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_23A_CALIBRATION_001",
            "decision": "Do not promote v2.22D dry-run scoring.",
            "accepted": True,
            "reason": "v2.22E already froze the dry run as non-promoted reference.",
            "effect": "production_scoring_authorized=False.",
        },
        {
            "decision_id": "V2_23A_CALIBRATION_002",
            "decision": "Create a calibration roadmap before any production scoring.",
            "accepted": True,
            "reason": "The current score is heuristic and metadata-sensitive.",
            "effect": "v2.23B/v2.23C are required before any future scoring promotion.",
        },
        {
            "decision_id": "V2_23A_CALIBRATION_003",
            "decision": "Prioritize metadata coverage before formula redesign.",
            "accepted": True,
            "reason": "top_country_by_scorable_rows=__MISSING__ in v2.22D.",
            "effect": "Recommended next phase is v2.23B.",
        },
        {
            "decision_id": "V2_23A_CALIBRATION_004",
            "decision": "Keep OpenAI, broker APIs and full59k disabled.",
            "accepted": True,
            "reason": "No separate authorization exists.",
            "effect": "No external enrichment or full59k launch.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "metadata_coverage",
            "action": "design_metadata_coverage_improvement_plan",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Metadata coverage must improve before production scoring.",
            "guardrails": "No canonical replacement; no full59k; no OpenAI/broker.",
        },
        {
            "action_order": 2,
            "action_scope": "calibration_data",
            "action": "design_manual_labelled_calibration_sample",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Production scoring needs labelled benchmark cases.",
            "guardrails": "Calibration design only; no production scoring.",
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

    add_check("hygiene_status_expected", hygiene.get("status") == EXPECTED_HYGIENE_STATUS, "critical", str(hygiene.get("status")))
    add_check("hygiene_critical_failed_checks_zero", str(hygiene_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={hygiene_summary.get('critical_failed_checks')}")
    add_check("freeze_status_expected", freeze.get("status") == EXPECTED_FREEZE_STATUS, "critical", str(freeze.get("status")))
    add_check("freeze_critical_failed_checks_zero", str(freeze_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={freeze_summary.get('critical_failed_checks')}")
    add_check("dry_run_status_expected", dry_run.get("status") == EXPECTED_DRY_RUN_STATUS, "critical", str(dry_run.get("status")))
    add_check("dry_run_critical_failed_checks_zero", str(dry_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={dry_summary.get('critical_failed_checks')}")
    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("scoring_rows_expected", scoring_rows == SCORING_OUTPUT_ROWS_EXPECTED, "critical", f"scoring_rows={scoring_rows}")
    add_check("scoring_sha_expected", scoring_sha == SCORING_OUTPUT_SHA_EXPECTED, "critical", scoring_sha)
    add_check("distribution_rows_expected", distribution_rows == 5, "critical", f"distribution_rows={distribution_rows}")
    add_check("components_rows_expected", components_rows == 6, "critical", f"components_rows={components_rows}")
    add_check("calibration_requirements_defined", len(requirements_rows) >= 6, "critical", f"requirements={len(requirements_rows)}")
    add_check("calibration_phases_defined", len(phases_rows) >= 4, "critical", f"phases={len(phases_rows)}")
    add_check("calibration_risks_defined", len(risks_rows) >= 4, "critical", f"risks={len(risks_rows)}")
    add_check("production_scoring_not_authorized", True, "critical", "production_scoring_authorized=False")
    add_check("scoring_not_executed_in_this_phase", True, "critical", "new_scoring_executed=False")
    add_check("promotion_not_performed", True, "critical", "promotion_performed=False")
    add_check("canonical_dataset_not_modified", sha256_file(CURRENT_DATASET) == CURRENT_SHA_EXPECTED, "critical", f"current_sha_after={sha256_file(CURRENT_DATASET)}")
    add_check("dry_run_score_output_not_modified", sha256_file(DRY_RUN_SCORES) == SCORING_OUTPUT_SHA_EXPECTED, "critical", f"scoring_sha_after={sha256_file(DRY_RUN_SCORES)}")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    status = STATUS_COMPLETED if critical_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Scoring model calibration roadmap before production scoring",
        "phase_type": PHASE_TYPE,
        "calibration_decision": "PRODUCTION_SCORING_DEFERRED_CALIBRATION_REQUIRED" if status == STATUS_COMPLETED else "CALIBRATION_ROADMAP_FAILED_REVIEW_REQUIRED",
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows,
        "current_dataset_sha": current_sha,
        "dry_run_scoring_report": str(DRY_RUN_REPORT),
        "dry_run_scoring_report_sha": dry_run_sha,
        "dry_run_scoring_output": str(DRY_RUN_SCORES),
        "dry_run_scoring_output_rows": scoring_rows,
        "dry_run_scoring_output_sha": scoring_sha,
        "dry_run_score_min": dry_summary.get("score_min"),
        "dry_run_score_p25": dry_summary.get("score_p25"),
        "dry_run_score_median": dry_summary.get("score_median"),
        "dry_run_score_p75": dry_summary.get("score_p75"),
        "dry_run_score_max": dry_summary.get("score_max"),
        "dry_run_score_mean": dry_summary.get("score_mean"),
        "top_exchange_by_scorable_rows": dry_summary.get("top_exchange_by_scorable_rows"),
        "top_country_by_scorable_rows": dry_summary.get("top_country_by_scorable_rows"),
        "top_source_provider_by_scorable_rows": dry_summary.get("top_source_provider_by_scorable_rows"),
        "requirements_defined": len(requirements_rows),
        "calibration_phases_defined": len(phases_rows),
        "risks_defined": len(risks_rows),
        "production_scoring_authorized": False,
        "new_scoring_executed": False,
        "scoring_promoted": False,
        "canonical_dataset_modified": False,
        "dry_run_score_output_modified": False,
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
            "artifact": "hygiene_report_input",
            "path": str(HYGIENE_REPORT),
            "rows": 1,
            "sha256": hygiene_sha,
            "role": "input_repo_hygiene_gate",
        },
        {
            "artifact": "freeze_report_input",
            "path": str(FREEZE_REPORT),
            "rows": 1,
            "sha256": freeze_sha,
            "role": "input_scoring_freeze_gate",
        },
        {
            "artifact": "dry_run_report_input",
            "path": str(DRY_RUN_REPORT),
            "rows": 1,
            "sha256": dry_run_sha,
            "role": "input_scoring_dry_run_report",
        },
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
            "artifact": "dry_run_scores_input",
            "path": str(DRY_RUN_SCORES),
            "rows": scoring_rows,
            "sha256": scoring_sha,
            "role": "input_scores_no_modification",
        },
        {
            "artifact": "dry_run_distribution_input",
            "path": str(DRY_RUN_DISTRIBUTION),
            "rows": distribution_rows,
            "sha256": distribution_sha,
            "role": "input_distribution_no_modification",
        },
        {
            "artifact": "dry_run_components_input",
            "path": str(DRY_RUN_COMPONENTS),
            "rows": components_rows,
            "sha256": components_sha,
            "role": "input_components_no_modification",
        },
    ]

    write_csv(CALIBRATION_REQUIREMENTS_CSV, requirements_rows, [
        "requirement_id",
        "requirement",
        "priority",
        "current_status",
        "reason",
        "required_before_production",
    ])
    write_csv(CALIBRATION_PHASES_CSV, phases_rows, [
        "phase_id",
        "phase_name",
        "purpose",
        "output_type",
        "promotion_allowed",
        "canonical_modification_allowed",
    ])
    write_csv(CALIBRATION_RISKS_CSV, risks_rows, [
        "risk_id",
        "risk",
        "severity",
        "mitigation",
    ])

    requirements_sha = sha256_file(CALIBRATION_REQUIREMENTS_CSV)
    phases_sha = sha256_file(CALIBRATION_PHASES_CSV)
    risks_sha = sha256_file(CALIBRATION_RISKS_CSV)

    artifact_manifest_rows.extend([
        {
            "artifact": "calibration_requirements_output",
            "path": str(CALIBRATION_REQUIREMENTS_CSV),
            "rows": len(requirements_rows),
            "sha256": requirements_sha,
            "role": "roadmap_requirements_output",
        },
        {
            "artifact": "calibration_phases_output",
            "path": str(CALIBRATION_PHASES_CSV),
            "rows": len(phases_rows),
            "sha256": phases_sha,
            "role": "roadmap_phases_output",
        },
        {
            "artifact": "calibration_risks_output",
            "path": str(CALIBRATION_RISKS_CSV),
            "rows": len(risks_rows),
            "sha256": risks_sha,
            "role": "roadmap_risks_output",
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
        "calibration_requirements": requirements_rows,
        "calibration_phases": phases_rows,
        "calibration_risks": risks_rows,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "current_dataset": str(CURRENT_DATASET),
            "current_dataset_rows": current_rows,
            "current_dataset_sha": current_sha,
            "dry_run_score_output": str(DRY_RUN_SCORES),
            "dry_run_score_output_rows": scoring_rows,
            "dry_run_score_output_sha": scoring_sha,
            "production_scoring_authorized": False,
            "new_scoring_executed": False,
            "scoring_promoted": False,
            "canonical_dataset_modified": False,
            "dry_run_score_output_modified": False,
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

    requirement_lines = "\n".join(
        f"- `{row['requirement_id']}` — {row['priority']} — {row['requirement']}"
        for row in requirements_rows
    )

    phase_lines = "\n".join(
        f"- `{row['phase_id']}` — {row['phase_name']}: {row['purpose']}"
        for row in phases_rows
    )

    risk_lines = "\n".join(
        f"- `{row['risk_id']}` — {row['severity']} — {row['risk']} Mitigation: {row['mitigation']}"
        for row in risks_rows
    )

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{report["generated_at_utc"]}`

## Decision

Calibration decision: **{summary["calibration_decision"]}**

Production scoring remains deferred. v2.23A creates a calibration roadmap only.

## Current reference

Dataset:

`{CURRENT_DATASET}`

Rows: `{current_rows}`  
SHA256: `{current_sha}`

Dry-run scoring output:

`{DRY_RUN_SCORES}`

Rows: `{scoring_rows}`  
SHA256: `{scoring_sha}`

## Dry-run score reference

- Min: `{dry_summary.get("score_min")}`
- P25: `{dry_summary.get("score_p25")}`
- Median: `{dry_summary.get("score_median")}`
- P75: `{dry_summary.get("score_p75")}`
- Max: `{dry_summary.get("score_max")}`
- Mean: `{dry_summary.get("score_mean")}`

## Calibration requirements

{requirement_lines}

## Calibration phases

{phase_lines}

## Calibration risks

{risk_lines}

## Guardrails

- Production scoring authorized: `False`
- New scoring executed in this phase: `False`
- Scoring promoted: `False`
- Canonical dataset modified: `False`
- Dry-run score output modified: `False`
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
    print("v2.23A scoring model calibration roadmap completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("CALIBRATION_REQUIREMENTS:")
    for row in requirements_rows:
        print(f"- {row['requirement_id']}: {row['priority']} - {row['requirement']}")
    print("")
    print("CALIBRATION_PHASES:")
    for row in phases_rows:
        print(f"- {row['phase_id']}: {row['phase_name']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
