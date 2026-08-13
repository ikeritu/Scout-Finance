from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.23B"
PHASE = "Metadata Coverage Improvement Plan"
PHASE_TYPE = "metadata-coverage-improvement-plan"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CALIBRATION_ROADMAP_JSON = OUTPUT_DIR / "scoring_model_calibration_roadmap_v2_23a.json"
CURRENT_POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
DRY_RUN_SCORES = OUTPUT_DIR / "scoring_dry_run_no_promotion_scores_v2_22d.csv"

REPORT_JSON = OUTPUT_DIR / "metadata_coverage_improvement_plan_v2_23b.json"
REPORT_MD = OUTPUT_DIR / "metadata_coverage_improvement_plan_v2_23b.md"
SUMMARY_CSV = OUTPUT_DIR / "metadata_coverage_improvement_plan_summary_v2_23b.csv"
CHECKS_CSV = OUTPUT_DIR / "metadata_coverage_improvement_plan_checks_v2_23b.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "metadata_coverage_improvement_plan_artifact_manifest_v2_23b.csv"
COVERAGE_METRICS_CSV = OUTPUT_DIR / "metadata_coverage_improvement_plan_coverage_metrics_v2_23b.csv"
GAP_PLAN_CSV = OUTPUT_DIR / "metadata_coverage_improvement_plan_gap_plan_v2_23b.csv"
PROVIDER_PRIORITIES_CSV = OUTPUT_DIR / "metadata_coverage_improvement_plan_provider_priorities_v2_23b.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "metadata_coverage_improvement_plan_decision_register_v2_23b.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "metadata_coverage_improvement_plan_next_actions_v2_23b.csv"

EXPECTED_CALIBRATION_STATUS = "SCORING_MODEL_CALIBRATION_ROADMAP_COMPLETED_PRODUCTION_SCORING_DEFERRED"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

SCORING_OUTPUT_ROWS_EXPECTED = 33498
SCORING_OUTPUT_SHA_EXPECTED = "a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1"

STATUS_COMPLETED = "METADATA_COVERAGE_IMPROVEMENT_PLAN_COMPLETED_NO_DATASET_MODIFICATION"
STATUS_FAILED = "METADATA_COVERAGE_IMPROVEMENT_PLAN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.23C - Scoring Calibration Data Design"
SECONDARY_NEXT_PHASE = "v2.23D - Scoring Formula Redesign Dry Run"

TARGET_FIELDS = [
    "country",
    "mic",
    "currency",
    "asset_type",
    "instrument_type",
    "instrument_scope",
    "source_provider",
    "classification_confidence",
    "isin",
    "ticker",
    "name",
    "exchange",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_dicts(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV artifact: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def find_column(header: list[str], candidates: list[str]) -> str | None:
    normalized = {column: normalize_header(column) for column in header}
    candidate_norms = [normalize_header(candidate) for candidate in candidates]

    for candidate in candidate_norms:
        for column, normalized_column in normalized.items():
            if normalized_column == candidate:
                return column

    for candidate in candidate_norms:
        for column, normalized_column in normalized.items():
            if candidate and candidate in normalized_column:
                return column

    return None


def resolve_columns(header: list[str]) -> dict[str, str | None]:
    return {
        "country": find_column(header, ["country"]),
        "mic": find_column(header, ["mic"]),
        "currency": find_column(header, ["currency"]),
        "asset_type": find_column(header, ["asset_type"]),
        "instrument_type": find_column(header, ["instrument_type"]),
        "instrument_scope": find_column(header, ["instrument_scope"]),
        "source_provider": find_column(header, ["source_provider", "provider"]),
        "classification_confidence": find_column(header, ["classification_confidence"]),
        "isin": find_column(header, ["isin"]),
        "ticker": find_column(header, ["ticker", "symbol"]),
        "name": find_column(header, ["company_name", "name", "security_name", "instrument_name"]),
        "exchange": find_column(header, ["exchange"]),
    }


def value_for(row: dict[str, str], column: str | None) -> str:
    if column is None:
        return ""
    return normalize_value(row.get(column, ""))


def coverage_for_rows(
    rows: list[dict[str, str]],
    columns: dict[str, str | None],
    dataset_scope: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    total = len(rows)

    for field in TARGET_FIELDS:
        column = columns.get(field)
        if column is None:
            present = 0
            missing = total
            distinct = 0
            top_value = "__COLUMN_NOT_FOUND__"
            top_value_count = 0
        else:
            values = [value_for(row, column) for row in rows]
            present = sum(1 for value in values if value)
            missing = total - present
            counter = Counter(value if value else "__MISSING__" for value in values)
            distinct = len([key for key in counter if key != "__MISSING__"])
            top_value, top_value_count = counter.most_common(1)[0] if counter else ("", 0)

        coverage_pct = round((present / total) * 100, 4) if total else 0.0
        missing_pct = round((missing / total) * 100, 4) if total else 0.0

        if column is None:
            severity = "critical"
            recommendation = "map_or_create_column_before_production_scoring"
        elif missing_pct >= 50:
            severity = "high"
            recommendation = "priority_backfill_required"
        elif missing_pct >= 10:
            severity = "medium"
            recommendation = "coverage_improvement_recommended"
        elif missing_pct > 0:
            severity = "low"
            recommendation = "minor_cleanup_recommended"
        else:
            severity = "ok"
            recommendation = "coverage_ok"

        output.append({
            "dataset_scope": dataset_scope,
            "field": field,
            "resolved_column": column or "",
            "total_rows": total,
            "present_rows": present,
            "missing_rows": missing,
            "coverage_pct": coverage_pct,
            "missing_pct": missing_pct,
            "distinct_non_missing_values": distinct,
            "top_value": top_value,
            "top_value_rows": top_value_count,
            "severity": severity,
            "recommendation": recommendation,
        })

    return output


def provider_gap_rows(
    rows: list[dict[str, str]],
    columns: dict[str, str | None],
    dataset_scope: str,
) -> list[dict[str, Any]]:
    provider_col = columns.get("source_provider")
    if provider_col is None:
        return []

    provider_counter: dict[str, Counter[str]] = {}

    for row in rows:
        provider = value_for(row, provider_col) or "__MISSING_PROVIDER__"
        if provider not in provider_counter:
            provider_counter[provider] = Counter()

        for field in ["country", "mic", "currency", "asset_type", "instrument_type", "instrument_scope"]:
            column = columns.get(field)
            if column is None or not value_for(row, column):
                provider_counter[provider][field] += 1

        provider_counter[provider]["__rows__"] += 1

    output: list[dict[str, Any]] = []
    for provider, counter in provider_counter.items():
        total = counter["__rows__"]
        country_missing = counter["country"]
        mic_missing = counter["mic"]
        currency_missing = counter["currency"]
        asset_type_missing = counter["asset_type"]

        priority_score = country_missing + mic_missing + currency_missing + asset_type_missing

        output.append({
            "dataset_scope": dataset_scope,
            "source_provider": provider,
            "rows": total,
            "country_missing_rows": country_missing,
            "mic_missing_rows": mic_missing,
            "currency_missing_rows": currency_missing,
            "asset_type_missing_rows": asset_type_missing,
            "instrument_type_missing_rows": counter["instrument_type"],
            "instrument_scope_missing_rows": counter["instrument_scope"],
            "priority_score": priority_score,
            "recommended_action": "review_provider_mapping_rules" if priority_score else "no_immediate_action",
        })

    output.sort(key=lambda row: (-int(row["priority_score"]), -int(row["rows"]), str(row["source_provider"])))
    return output[:50]


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        COVERAGE_METRICS_CSV,
        GAP_PLAN_CSV,
        PROVIDER_PRIORITIES_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    calibration = read_json(CALIBRATION_ROADMAP_JSON)
    calibration_summary = calibration.get("summary", {})
    pointer = read_json(CURRENT_POINTER)

    current_header, current_rows_data = read_csv_dicts(CURRENT_DATASET)
    score_header, score_rows_data = read_csv_dicts(DRY_RUN_SCORES)

    current_rows = len(current_rows_data)
    scoring_rows = len(score_rows_data)

    current_sha = sha256_file(CURRENT_DATASET)
    scoring_sha = sha256_file(DRY_RUN_SCORES)
    calibration_sha = sha256_file(CALIBRATION_ROADMAP_JSON)
    pointer_sha = sha256_file(CURRENT_POINTER)

    current_columns = resolve_columns(current_header)
    score_columns = resolve_columns(score_header)

    current_coverage = coverage_for_rows(current_rows_data, current_columns, "current_operational_dataset")
    score_coverage = coverage_for_rows(score_rows_data, score_columns, "scorable_dry_run_output")

    coverage_rows = current_coverage + score_coverage

    high_or_critical_gaps = [
        row for row in coverage_rows
        if row["severity"] in {"critical", "high"}
    ]

    scorable_country_metric = next(
        (row for row in score_coverage if row["field"] == "country"),
        None,
    )

    scorable_country_missing_pct = scorable_country_metric["missing_pct"] if scorable_country_metric else 0.0
    scorable_country_top_value = scorable_country_metric["top_value"] if scorable_country_metric else ""

    provider_rows = (
        provider_gap_rows(current_rows_data, current_columns, "current_operational_dataset") +
        provider_gap_rows(score_rows_data, score_columns, "scorable_dry_run_output")
    )

    gap_plan_rows = [
        {
            "gap_id": "META_GAP_001",
            "area": "country",
            "priority": "critical",
            "problem": "Country coverage is insufficient for production scoring if missing values dominate scoreable rows.",
            "planned_resolution": "Design deterministic country backfill from exchange, MIC, source provider or listing suffix.",
            "phase_to_execute": "v2.24B - Country / MIC / Currency Backfill Plan",
            "promotion_allowed": False,
        },
        {
            "gap_id": "META_GAP_002",
            "area": "mic",
            "priority": "high",
            "problem": "MIC is needed to normalize venue-level identification and country mapping.",
            "planned_resolution": "Design exchange-to-MIC and provider-specific MIC mapping tables.",
            "phase_to_execute": "v2.24B - Country / MIC / Currency Backfill Plan",
            "promotion_allowed": False,
        },
        {
            "gap_id": "META_GAP_003",
            "area": "currency",
            "priority": "high",
            "problem": "Currency gaps reduce comparability and weaken future scoring interpretability.",
            "planned_resolution": "Backfill currency from exchange/MIC/provider where deterministic.",
            "phase_to_execute": "v2.24B - Country / MIC / Currency Backfill Plan",
            "promotion_allowed": False,
        },
        {
            "gap_id": "META_GAP_004",
            "area": "asset_type/instrument_type/instrument_scope",
            "priority": "critical",
            "problem": "Production scoring needs reliable separation of common equity, fund-like, fixed income and residual instruments.",
            "planned_resolution": "Promote a normalized taxonomy design before scoring promotion.",
            "phase_to_execute": "v2.24C - Asset Type Normalization Plan",
            "promotion_allowed": False,
        },
        {
            "gap_id": "META_GAP_005",
            "area": "source_provider",
            "priority": "medium",
            "problem": "Provider-specific gap patterns should guide deterministic cleanup order.",
            "planned_resolution": "Create provider quality matrix and prioritize providers with largest missing metadata burden.",
            "phase_to_execute": "v2.24D - Provider Quality Matrix",
            "promotion_allowed": False,
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_23B_METADATA_001",
            "decision": "Create metadata coverage plan before formula redesign.",
            "accepted": True,
            "reason": "v2.23A prioritized metadata coverage before production scoring.",
            "effect": "v2.23B remains planning/audit only.",
        },
        {
            "decision_id": "V2_23B_METADATA_002",
            "decision": "Do not backfill or mutate metadata in this phase.",
            "accepted": True,
            "reason": "This phase is an improvement plan, not an execution phase.",
            "effect": "canonical_dataset_modified=False.",
        },
        {
            "decision_id": "V2_23B_METADATA_003",
            "decision": "Treat country, MIC, currency and asset taxonomy as blocking production-scoring readiness areas.",
            "accepted": True,
            "reason": "v2.22D/v2.23A identified metadata sensitivity and missing country dominance.",
            "effect": "Production scoring remains unauthorized.",
        },
        {
            "decision_id": "V2_23B_METADATA_004",
            "decision": "Keep OpenAI, broker APIs and full59k disabled.",
            "accepted": True,
            "reason": "No separate authorization exists for external enrichment.",
            "effect": "openai_called=False; broker_called=False; full59k=DEPRECATED_DEFERRED.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "calibration_data",
            "action": "design_manual_labelled_calibration_sample",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Coverage plan exists; calibration data design is needed before formula redesign.",
            "guardrails": "No production scoring; no canonical replacement.",
        },
        {
            "action_order": 2,
            "action_scope": "metadata_execution",
            "action": "prepare_future_country_mic_currency_backfill_plan",
            "priority": "medium",
            "recommended_phase": "v2.24B - Country / MIC / Currency Backfill Plan",
            "reason": "Metadata backfill should be designed separately and deterministically.",
            "guardrails": "No full59k; no broker/OpenAI unless separately approved.",
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

    add_check("calibration_status_expected", calibration.get("status") == EXPECTED_CALIBRATION_STATUS, "critical", str(calibration.get("status")))
    add_check("calibration_critical_failed_checks_zero", str(calibration_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={calibration_summary.get('critical_failed_checks')}")
    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("scoring_rows_expected", scoring_rows == SCORING_OUTPUT_ROWS_EXPECTED, "critical", f"scoring_rows={scoring_rows}")
    add_check("scoring_sha_expected", scoring_sha == SCORING_OUTPUT_SHA_EXPECTED, "critical", scoring_sha)
    add_check("coverage_metrics_created", len(coverage_rows) == len(TARGET_FIELDS) * 2, "critical", f"coverage_metrics={len(coverage_rows)}")
    add_check("gap_plan_created", len(gap_plan_rows) >= 5, "critical", f"gap_plan_rows={len(gap_plan_rows)}")
    add_check("provider_priorities_created", len(provider_rows) > 0, "critical", f"provider_priority_rows={len(provider_rows)}")
    add_check("known_country_gap_documented", scorable_country_top_value == "__MISSING__" or scorable_country_missing_pct > 0, "warning", f"top_country={scorable_country_top_value};missing_pct={scorable_country_missing_pct}")
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
        "selected_route": "Metadata coverage improvement plan before scoring calibration data design",
        "phase_type": PHASE_TYPE,
        "metadata_decision": "METADATA_COVERAGE_PLAN_CREATED_NO_DATASET_MODIFICATION" if status == STATUS_COMPLETED else "METADATA_COVERAGE_PLAN_FAILED_REVIEW_REQUIRED",
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows,
        "current_dataset_sha": current_sha,
        "dry_run_scoring_output": str(DRY_RUN_SCORES),
        "dry_run_scoring_output_rows": scoring_rows,
        "dry_run_scoring_output_sha": scoring_sha,
        "coverage_metrics_created": len(coverage_rows),
        "high_or_critical_gap_metrics": len(high_or_critical_gaps),
        "gap_plan_rows": len(gap_plan_rows),
        "provider_priority_rows": len(provider_rows),
        "scorable_country_top_value": scorable_country_top_value,
        "scorable_country_missing_pct": scorable_country_missing_pct,
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
            "artifact": "calibration_roadmap_input",
            "path": str(CALIBRATION_ROADMAP_JSON),
            "rows": 1,
            "sha256": calibration_sha,
            "role": "input_calibration_roadmap",
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

    write_csv(COVERAGE_METRICS_CSV, coverage_rows, [
        "dataset_scope",
        "field",
        "resolved_column",
        "total_rows",
        "present_rows",
        "missing_rows",
        "coverage_pct",
        "missing_pct",
        "distinct_non_missing_values",
        "top_value",
        "top_value_rows",
        "severity",
        "recommendation",
    ])
    write_csv(GAP_PLAN_CSV, gap_plan_rows, [
        "gap_id",
        "area",
        "priority",
        "problem",
        "planned_resolution",
        "phase_to_execute",
        "promotion_allowed",
    ])
    write_csv(PROVIDER_PRIORITIES_CSV, provider_rows, [
        "dataset_scope",
        "source_provider",
        "rows",
        "country_missing_rows",
        "mic_missing_rows",
        "currency_missing_rows",
        "asset_type_missing_rows",
        "instrument_type_missing_rows",
        "instrument_scope_missing_rows",
        "priority_score",
        "recommended_action",
    ])

    coverage_sha = sha256_file(COVERAGE_METRICS_CSV)
    gap_plan_sha = sha256_file(GAP_PLAN_CSV)
    provider_sha = sha256_file(PROVIDER_PRIORITIES_CSV)

    artifact_manifest_rows.extend([
        {
            "artifact": "coverage_metrics_output",
            "path": str(COVERAGE_METRICS_CSV),
            "rows": len(coverage_rows),
            "sha256": coverage_sha,
            "role": "metadata_coverage_metrics_output",
        },
        {
            "artifact": "gap_plan_output",
            "path": str(GAP_PLAN_CSV),
            "rows": len(gap_plan_rows),
            "sha256": gap_plan_sha,
            "role": "metadata_gap_plan_output",
        },
        {
            "artifact": "provider_priorities_output",
            "path": str(PROVIDER_PRIORITIES_CSV),
            "rows": len(provider_rows),
            "sha256": provider_sha,
            "role": "provider_gap_priority_output",
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
        "coverage_metrics": coverage_rows,
        "gap_plan": gap_plan_rows,
        "provider_priorities": provider_rows,
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

    gap_lines = "\n".join(
        f"- `{row['gap_id']}` — {row['priority']} — {row['area']}: {row['planned_resolution']}"
        for row in gap_plan_rows
    )

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{report["generated_at_utc"]}`

## Decision

Metadata decision: **{summary["metadata_decision"]}**

This phase creates a metadata coverage improvement plan only. It does not backfill metadata, execute scoring, promote scoring, or modify the canonical dataset.

## Coverage focus

Coverage metrics created: `{len(coverage_rows)}`  
High or critical gap metrics: `{len(high_or_critical_gaps)}`  
Provider priority rows: `{len(provider_rows)}`

Scorable country top value: `{scorable_country_top_value}`  
Scorable country missing pct: `{scorable_country_missing_pct}`

## Gap plan

{gap_lines}

## Guardrails

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
    print("v2.23B metadata coverage improvement plan completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("TOP_COVERAGE_GAPS:")
    for row in high_or_critical_gaps[:12]:
        print(f"- {row['dataset_scope']} | {row['field']}: missing_pct={row['missing_pct']} severity={row['severity']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
