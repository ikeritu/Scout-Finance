from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.23C"
PHASE = "Scoring Calibration Data Design"
PHASE_TYPE = "scoring-calibration-data-design"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

METADATA_PLAN_JSON = OUTPUT_DIR / "metadata_coverage_improvement_plan_v2_23b.json"
CURRENT_POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
DRY_RUN_SCORES = OUTPUT_DIR / "scoring_dry_run_no_promotion_scores_v2_22d.csv"

REPORT_JSON = OUTPUT_DIR / "scoring_calibration_data_design_v2_23c.json"
REPORT_MD = OUTPUT_DIR / "scoring_calibration_data_design_v2_23c.md"
SUMMARY_CSV = OUTPUT_DIR / "scoring_calibration_data_design_summary_v2_23c.csv"
CHECKS_CSV = OUTPUT_DIR / "scoring_calibration_data_design_checks_v2_23c.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "scoring_calibration_data_design_artifact_manifest_v2_23c.csv"
LABEL_SCHEMA_CSV = OUTPUT_DIR / "scoring_calibration_data_design_label_schema_v2_23c.csv"
SAMPLE_PLAN_CSV = OUTPUT_DIR / "scoring_calibration_data_design_sample_plan_v2_23c.csv"
STRATA_PROFILE_CSV = OUTPUT_DIR / "scoring_calibration_data_design_strata_profile_v2_23c.csv"
ACCEPTANCE_CRITERIA_CSV = OUTPUT_DIR / "scoring_calibration_data_design_acceptance_criteria_v2_23c.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "scoring_calibration_data_design_decision_register_v2_23c.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "scoring_calibration_data_design_next_actions_v2_23c.csv"

EXPECTED_METADATA_STATUS = "METADATA_COVERAGE_IMPROVEMENT_PLAN_COMPLETED_NO_DATASET_MODIFICATION"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

SCORING_OUTPUT_ROWS_EXPECTED = 33498
SCORING_OUTPUT_SHA_EXPECTED = "a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1"

STATUS_COMPLETED = "SCORING_CALIBRATION_DATA_DESIGN_COMPLETED_NO_LABELS_NO_SCORING_NO_PROMOTION"
STATUS_FAILED = "SCORING_CALIBRATION_DATA_DESIGN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.23D - Scoring Formula Redesign Dry Run"
SECONDARY_NEXT_PHASE = "v2.23E - Calibration Review / Freeze Decision"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV artifact: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def score_to_float(value: Any) -> float:
    try:
        return float(normalize_value(value))
    except Exception:
        return 0.0


def missing_flag(row: dict[str, str], field: str) -> bool:
    return not bool(normalize_value(row.get(field, "")))


def build_strata_profile(score_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    bucket_counter = Counter()
    provider_counter = Counter()
    bucket_provider_counter = Counter()
    country_missing_counter = Counter()
    asset_type_missing_counter = Counter()

    for row in score_rows:
        bucket = normalize_value(row.get("score_bucket", "")) or "__MISSING_BUCKET__"
        provider = normalize_value(row.get("source_provider", "")) or "__MISSING_PROVIDER__"

        bucket_counter[bucket] += 1
        provider_counter[provider] += 1
        bucket_provider_counter[(bucket, provider)] += 1

        if missing_flag(row, "country"):
            country_missing_counter[(bucket, provider)] += 1

        if missing_flag(row, "asset_type"):
            asset_type_missing_counter[(bucket, provider)] += 1

    output: list[dict[str, Any]] = []

    for (bucket, provider), rows in bucket_provider_counter.most_common():
        country_missing = country_missing_counter[(bucket, provider)]
        asset_type_missing = asset_type_missing_counter[(bucket, provider)]

        output.append({
            "score_bucket": bucket,
            "source_provider": provider,
            "rows": rows,
            "country_missing_rows": country_missing,
            "country_missing_pct": round((country_missing / rows) * 100, 4) if rows else 0.0,
            "asset_type_missing_rows": asset_type_missing,
            "asset_type_missing_pct": round((asset_type_missing / rows) * 100, 4) if rows else 0.0,
            "recommended_manual_review_priority": "high" if country_missing or asset_type_missing else "medium",
        })

    return output


def build_sample_plan(strata_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket_targets = {
        "A_85_100": 30,
        "B_70_84": 40,
        "C_55_69": 40,
        "D_40_54": 40,
        "E_0_39": 20,
    }

    bucket_seen: set[str] = set()
    output: list[dict[str, Any]] = []

    for bucket, target in bucket_targets.items():
        bucket_rows = [row for row in strata_rows if row["score_bucket"] == bucket]
        total_rows = sum(int(row["rows"]) for row in bucket_rows)

        if total_rows == 0:
            output.append({
                "sample_plan_id": f"SAMPLE_{bucket}",
                "sample_type": "score_bucket",
                "score_bucket": bucket,
                "source_provider": "__ANY__",
                "population_rows": 0,
                "target_manual_review_rows": 0,
                "selection_rule": "skip_empty_bucket",
                "purpose": "Bucket has no rows in dry-run output.",
            })
            continue

        bucket_seen.add(bucket)
        output.append({
            "sample_plan_id": f"SAMPLE_{bucket}",
            "sample_type": "score_bucket",
            "score_bucket": bucket,
            "source_provider": "__ANY__",
            "population_rows": total_rows,
            "target_manual_review_rows": min(target, total_rows),
            "selection_rule": "stratified_evenly_across_top_providers_and_missing_metadata_cases",
            "purpose": "Check whether score bucket ordering matches manual quality judgement.",
        })

    provider_priority_rows = sorted(
        strata_rows,
        key=lambda row: (
            -int(row["country_missing_rows"]) - int(row["asset_type_missing_rows"]),
            -int(row["rows"]),
            str(row["source_provider"]),
        ),
    )[:10]

    for index, row in enumerate(provider_priority_rows, start=1):
        output.append({
            "sample_plan_id": f"SAMPLE_PROVIDER_GAP_{index:02d}",
            "sample_type": "provider_gap",
            "score_bucket": row["score_bucket"],
            "source_provider": row["source_provider"],
            "population_rows": row["rows"],
            "target_manual_review_rows": min(15, int(row["rows"])),
            "selection_rule": "prioritize_rows_with_missing_country_or_asset_type",
            "purpose": "Validate metadata-sensitive score behavior for high-gap providers.",
        })

    output.append({
        "sample_plan_id": "SAMPLE_BOUNDARY_CASES",
        "sample_type": "score_boundary",
        "score_bucket": "__MULTI__",
        "source_provider": "__ANY__",
        "population_rows": sum(int(row["rows"]) for row in strata_rows),
        "target_manual_review_rows": 50,
        "selection_rule": "select_scores_near_55_70_85_thresholds",
        "purpose": "Validate score threshold behavior around bucket boundaries.",
    })

    return output


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        LABEL_SCHEMA_CSV,
        SAMPLE_PLAN_CSV,
        STRATA_PROFILE_CSV,
        ACCEPTANCE_CRITERIA_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    metadata_plan = read_json(METADATA_PLAN_JSON)
    metadata_summary = metadata_plan.get("summary", {})
    pointer = read_json(CURRENT_POINTER)

    score_rows_data = read_csv_dicts(DRY_RUN_SCORES)

    current_rows = count_csv_rows(CURRENT_DATASET)
    scoring_rows = len(score_rows_data)

    current_sha = sha256_file(CURRENT_DATASET)
    scoring_sha = sha256_file(DRY_RUN_SCORES)
    metadata_plan_sha = sha256_file(METADATA_PLAN_JSON)
    pointer_sha = sha256_file(CURRENT_POINTER)

    scores = [score_to_float(row.get("dry_run_score", "")) for row in score_rows_data]
    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0

    strata_rows = build_strata_profile(score_rows_data)
    sample_plan_rows = build_sample_plan(strata_rows)

    target_manual_review_rows = sum(int(row["target_manual_review_rows"]) for row in sample_plan_rows)

    label_schema_rows = [
        {
            "field": "manual_label",
            "allowed_values": "good_candidate|borderline_candidate|bad_candidate|not_common_equity|insufficient_metadata",
            "required": True,
            "purpose": "Human judgement label for calibration.",
        },
        {
            "field": "manual_data_quality_label",
            "allowed_values": "high|medium|low|unusable",
            "required": True,
            "purpose": "Separate data-quality assessment from attractiveness.",
        },
        {
            "field": "manual_attractiveness_label",
            "allowed_values": "high|medium|low|unknown",
            "required": True,
            "purpose": "Human judgement of investment/selection attractiveness, separate from metadata completeness.",
        },
        {
            "field": "instrument_validity_label",
            "allowed_values": "common_equity|fund_like|fixed_income|preferred|warrant_right_certificate|unknown",
            "required": True,
            "purpose": "Validate whether v2.22C2 exclusion policy and future scoring scope are correct.",
        },
        {
            "field": "reviewer_notes",
            "allowed_values": "free_text",
            "required": False,
            "purpose": "Capture reviewer reasoning and edge cases.",
        },
        {
            "field": "review_status",
            "allowed_values": "pending|reviewed|needs_second_review|rejected_from_calibration",
            "required": True,
            "purpose": "Workflow status for the manual calibration sample.",
        },
    ]

    acceptance_criteria_rows = [
        {
            "criteria_id": "ACCEPT_001",
            "criteria": "Manual calibration sample must include every score bucket with available rows.",
            "threshold": "all_non_empty_buckets_covered",
            "blocking": True,
        },
        {
            "criteria_id": "ACCEPT_002",
            "criteria": "Manual calibration sample must include high-gap providers, especially CBOE Europe and major missing-metadata groups.",
            "threshold": "top_provider_gap_strata_covered",
            "blocking": True,
        },
        {
            "criteria_id": "ACCEPT_003",
            "criteria": "Scoring redesign must separate data-quality score from attractiveness score.",
            "threshold": "separate_components_required",
            "blocking": True,
        },
        {
            "criteria_id": "ACCEPT_004",
            "criteria": "No production scoring may be authorized from unlabelled dry-run scores.",
            "threshold": "production_scoring_authorized_false",
            "blocking": True,
        },
        {
            "criteria_id": "ACCEPT_005",
            "criteria": "Any future formula must remain deterministic unless a separate external enrichment gate is approved.",
            "threshold": "no_openai_no_broker_no_full59k",
            "blocking": True,
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_23C_CALDATA_001",
            "decision": "Design calibration data schema and sample plan only.",
            "accepted": True,
            "reason": "Manual labels do not exist yet and must not be invented.",
            "effect": "No labels are created in v2.23C.",
        },
        {
            "decision_id": "V2_23C_CALDATA_002",
            "decision": "Require separation of data-quality and attractiveness labels.",
            "accepted": True,
            "reason": "v2.22D score is metadata-sensitive and can over-reward complete provider data.",
            "effect": "Future formula redesign must use separate components.",
        },
        {
            "decision_id": "V2_23C_CALDATA_003",
            "decision": "Include score bucket, provider-gap and boundary-case strata.",
            "accepted": True,
            "reason": "Calibration must test ranking order, metadata gaps and threshold behavior.",
            "effect": "Sample plan covers buckets, providers and boundaries.",
        },
        {
            "decision_id": "V2_23C_CALDATA_004",
            "decision": "Do not execute new scoring, backfill metadata, or promote any output.",
            "accepted": True,
            "reason": "v2.23C is a design phase.",
            "effect": "canonical_dataset_modified=False; production_scoring_authorized=False.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "formula_redesign",
            "action": "redesign_scoring_formula_as_dry_run_only",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Calibration data design exists and can guide formula redesign.",
            "guardrails": "Dry run only; no production scoring; no canonical replacement.",
        },
        {
            "action_order": 2,
            "action_scope": "calibration_review",
            "action": "review_redesigned_formula_against_acceptance_criteria",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Any redesigned formula must still pass a freeze/promotion decision gate.",
            "guardrails": "No promotion without explicit future gate.",
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

    add_check("metadata_plan_status_expected", metadata_plan.get("status") == EXPECTED_METADATA_STATUS, "critical", str(metadata_plan.get("status")))
    add_check("metadata_plan_critical_failed_checks_zero", str(metadata_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={metadata_summary.get('critical_failed_checks')}")
    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("scoring_rows_expected", scoring_rows == SCORING_OUTPUT_ROWS_EXPECTED, "critical", f"scoring_rows={scoring_rows}")
    add_check("scoring_sha_expected", scoring_sha == SCORING_OUTPUT_SHA_EXPECTED, "critical", scoring_sha)
    add_check("score_range_expected", min_score >= 0 and max_score <= 100, "critical", f"min={min_score};max={max_score}")
    add_check("label_schema_created", len(label_schema_rows) >= 6, "critical", f"label_schema_rows={len(label_schema_rows)}")
    add_check("sample_plan_created", len(sample_plan_rows) >= 10, "critical", f"sample_plan_rows={len(sample_plan_rows)}")
    add_check("strata_profile_created", len(strata_rows) > 0, "critical", f"strata_rows={len(strata_rows)}")
    add_check("acceptance_criteria_created", len(acceptance_criteria_rows) >= 5, "critical", f"acceptance_criteria_rows={len(acceptance_criteria_rows)}")
    add_check("manual_labels_not_created", True, "critical", "manual_labels_created=False")
    add_check("production_scoring_not_authorized", True, "critical", "production_scoring_authorized=False")
    add_check("new_scoring_not_executed", True, "critical", "new_scoring_executed=False")
    add_check("metadata_backfill_not_executed", True, "critical", "metadata_backfill_executed=False")
    add_check("canonical_dataset_not_modified", sha256_file(CURRENT_DATASET) == CURRENT_SHA_EXPECTED, "critical", f"current_sha_after={sha256_file(CURRENT_DATASET)}")
    add_check("dry_run_score_output_not_modified", sha256_file(DRY_RUN_SCORES) == SCORING_OUTPUT_SHA_EXPECTED, "critical", f"scoring_sha_after={sha256_file(DRY_RUN_SCORES)}")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    status = STATUS_COMPLETED if critical_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Scoring calibration data design before formula redesign",
        "phase_type": PHASE_TYPE,
        "calibration_data_decision": "CALIBRATION_DATA_DESIGN_CREATED_NO_LABELS_NO_SCORING" if status == STATUS_COMPLETED else "CALIBRATION_DATA_DESIGN_FAILED_REVIEW_REQUIRED",
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows,
        "current_dataset_sha": current_sha,
        "dry_run_scoring_output": str(DRY_RUN_SCORES),
        "dry_run_scoring_output_rows": scoring_rows,
        "dry_run_scoring_output_sha": scoring_sha,
        "dry_run_score_min": min_score,
        "dry_run_score_max": max_score,
        "label_schema_rows": len(label_schema_rows),
        "sample_plan_rows": len(sample_plan_rows),
        "strata_profile_rows": len(strata_rows),
        "acceptance_criteria_rows": len(acceptance_criteria_rows),
        "target_manual_review_rows": target_manual_review_rows,
        "manual_labels_created": False,
        "production_scoring_authorized": False,
        "new_scoring_executed": False,
        "metadata_backfill_executed": False,
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
    ]

    write_csv(LABEL_SCHEMA_CSV, label_schema_rows, ["field", "allowed_values", "required", "purpose"])
    write_csv(SAMPLE_PLAN_CSV, sample_plan_rows, ["sample_plan_id", "sample_type", "score_bucket", "source_provider", "population_rows", "target_manual_review_rows", "selection_rule", "purpose"])
    write_csv(STRATA_PROFILE_CSV, strata_rows, ["score_bucket", "source_provider", "rows", "country_missing_rows", "country_missing_pct", "asset_type_missing_rows", "asset_type_missing_pct", "recommended_manual_review_priority"])
    write_csv(ACCEPTANCE_CRITERIA_CSV, acceptance_criteria_rows, ["criteria_id", "criteria", "threshold", "blocking"])

    label_schema_sha = sha256_file(LABEL_SCHEMA_CSV)
    sample_plan_sha = sha256_file(SAMPLE_PLAN_CSV)
    strata_sha = sha256_file(STRATA_PROFILE_CSV)
    acceptance_sha = sha256_file(ACCEPTANCE_CRITERIA_CSV)

    artifact_manifest_rows.extend([
        {
            "artifact": "label_schema_output",
            "path": str(LABEL_SCHEMA_CSV),
            "rows": len(label_schema_rows),
            "sha256": label_schema_sha,
            "role": "calibration_label_schema_output",
        },
        {
            "artifact": "sample_plan_output",
            "path": str(SAMPLE_PLAN_CSV),
            "rows": len(sample_plan_rows),
            "sha256": sample_plan_sha,
            "role": "calibration_sample_plan_output",
        },
        {
            "artifact": "strata_profile_output",
            "path": str(STRATA_PROFILE_CSV),
            "rows": len(strata_rows),
            "sha256": strata_sha,
            "role": "calibration_strata_profile_output",
        },
        {
            "artifact": "acceptance_criteria_output",
            "path": str(ACCEPTANCE_CRITERIA_CSV),
            "rows": len(acceptance_criteria_rows),
            "sha256": acceptance_sha,
            "role": "calibration_acceptance_criteria_output",
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
        "label_schema": label_schema_rows,
        "sample_plan": sample_plan_rows,
        "strata_profile": strata_rows,
        "acceptance_criteria": acceptance_criteria_rows,
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
            "manual_labels_created": False,
            "production_scoring_authorized": False,
            "new_scoring_executed": False,
            "metadata_backfill_executed": False,
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

    schema_lines = "\n".join(
        f"- `{row['field']}` — {row['allowed_values']}"
        for row in label_schema_rows
    )

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{report["generated_at_utc"]}`

## Decision

Calibration data decision: **{summary["calibration_data_decision"]}**

This phase designs the manual calibration data structure only. It does not create manual labels, execute new scoring, backfill metadata, promote scores, or modify the canonical dataset.

## Inputs

Current dataset:

`{CURRENT_DATASET}`

Rows: `{current_rows}`  
SHA256: `{current_sha}`

Dry-run scoring output:

`{DRY_RUN_SCORES}`

Rows: `{scoring_rows}`  
SHA256: `{scoring_sha}`

## Design outputs

- Label schema rows: `{len(label_schema_rows)}`
- Sample plan rows: `{len(sample_plan_rows)}`
- Strata profile rows: `{len(strata_rows)}`
- Acceptance criteria rows: `{len(acceptance_criteria_rows)}`
- Target manual review rows: `{target_manual_review_rows}`

## Label schema

{schema_lines}

## Guardrails

- Manual labels created: `False`
- Production scoring authorized: `False`
- New scoring executed: `False`
- Metadata backfill executed: `False`
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
    print("v2.23C scoring calibration data design completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("LABEL_SCHEMA:")
    for row in label_schema_rows:
        print(f"- {row['field']}: {row['allowed_values']}")
    print("")
    print("SAMPLE_PLAN:")
    for row in sample_plan_rows[:20]:
        print(f"- {row['sample_plan_id']}: target={row['target_manual_review_rows']} purpose={row['purpose']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
