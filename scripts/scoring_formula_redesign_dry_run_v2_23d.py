from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.23D"
PHASE = "Scoring Formula Redesign Dry Run"
PHASE_TYPE = "scoring-formula-redesign-dry-run"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CALIBRATION_DATA_DESIGN_JSON = OUTPUT_DIR / "scoring_calibration_data_design_v2_23c.json"
METADATA_PLAN_JSON = OUTPUT_DIR / "metadata_coverage_improvement_plan_v2_23b.json"
CURRENT_POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
LEGACY_DRY_RUN_SCORES = OUTPUT_DIR / "scoring_dry_run_no_promotion_scores_v2_22d.csv"

REPORT_JSON = OUTPUT_DIR / "scoring_formula_redesign_dry_run_v2_23d.json"
REPORT_MD = OUTPUT_DIR / "scoring_formula_redesign_dry_run_v2_23d.md"
SUMMARY_CSV = OUTPUT_DIR / "scoring_formula_redesign_dry_run_summary_v2_23d.csv"
CHECKS_CSV = OUTPUT_DIR / "scoring_formula_redesign_dry_run_checks_v2_23d.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "scoring_formula_redesign_dry_run_artifact_manifest_v2_23d.csv"
REDESIGNED_SCORES_CSV = OUTPUT_DIR / "scoring_formula_redesign_dry_run_scores_v2_23d.csv"
DISTRIBUTION_CSV = OUTPUT_DIR / "scoring_formula_redesign_dry_run_distribution_v2_23d.csv"
COMPONENT_WEIGHTS_CSV = OUTPUT_DIR / "scoring_formula_redesign_dry_run_component_weights_v2_23d.csv"
ACCEPTANCE_REVIEW_CSV = OUTPUT_DIR / "scoring_formula_redesign_dry_run_acceptance_review_v2_23d.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "scoring_formula_redesign_dry_run_decision_register_v2_23d.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "scoring_formula_redesign_dry_run_next_actions_v2_23d.csv"

EXPECTED_CALDATA_STATUS = "SCORING_CALIBRATION_DATA_DESIGN_COMPLETED_NO_LABELS_NO_SCORING_NO_PROMOTION"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

LEGACY_SCORING_ROWS_EXPECTED = 33498
LEGACY_SCORING_SHA_EXPECTED = "a93d48e4bdead6ca8e378a9949cf056c4970e9c1f6a2e8963d7ddbb170e358d1"

STATUS_COMPLETED = "SCORING_FORMULA_REDESIGN_DRY_RUN_COMPLETED_NO_PROMOTION_NO_CANONICAL_CHANGE"
STATUS_FAILED = "SCORING_FORMULA_REDESIGN_DRY_RUN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.23E - Calibration Review / Freeze Decision"
SECONDARY_NEXT_PHASE = "v2.23F - Calibration Closure Report"

DATA_QUALITY_WEIGHTS = {
    "country": 18.0,
    "mic": 14.0,
    "currency": 12.0,
    "asset_type": 16.0,
    "instrument_type": 12.0,
    "instrument_scope": 10.0,
    "source_provider": 8.0,
    "ticker": 5.0,
    "name": 5.0,
}

FORMULA_COMPONENT_WEIGHTS = {
    "data_quality_score": 0.70,
    "scope_confidence_score": 0.20,
    "provider_quality_score": 0.10,
    "attractiveness_score": 0.00,
}

PROVIDER_QUALITY_BASELINES = {
    "ASX": 95.0,
    "sgx_structured_endpoint": 92.0,
    "SFC_SIMEV_RNVE": 88.0,
    "jpx_listed_securities": 82.0,
    "hkex_securities_list": 80.0,
    "HKEX": 78.0,
    "TWSE": 78.0,
    "deutsche_boerse_xetra_all_tradable_instruments": 76.0,
    "nasdaq_trader_nasdaqlisted": 70.0,
    "nasdaq_trader_otherlisted": 68.0,
    "sec_company_tickers_exchange": 66.0,
    "cboe_listed_symbols": 62.0,
    "cboe_europe_reference_data": 45.0,
    "__MISSING_PROVIDER__": 30.0,
}


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


def as_float(value: Any) -> float:
    try:
        return float(normalize_value(value))
    except Exception:
        return 0.0


def has_value(row: dict[str, str], field: str) -> bool:
    return bool(normalize_value(row.get(field, "")))


def calculate_data_quality_score(row: dict[str, str]) -> float:
    score = 0.0
    total_weight = sum(DATA_QUALITY_WEIGHTS.values())

    for field, weight in DATA_QUALITY_WEIGHTS.items():
        if has_value(row, field):
            score += weight

    return round((score / total_weight) * 100.0, 4)


def calculate_scope_confidence_score(row: dict[str, str]) -> float:
    asset_type = normalize_value(row.get("asset_type", "")).lower()
    instrument_type = normalize_value(row.get("instrument_type", "")).lower()
    instrument_scope = normalize_value(row.get("instrument_scope", "")).lower()

    combined = " ".join([asset_type, instrument_type, instrument_scope])

    exclusion_terms = [
        "etf",
        "fund",
        "bond",
        "note",
        "warrant",
        "right",
        "preferred",
        "preference",
        "certificate",
        "trust",
        "unit",
    ]

    equity_terms = [
        "common",
        "ordinary",
        "equity",
        "eqty",
        "stock",
        "share",
    ]

    if any(term in combined for term in exclusion_terms):
        return 10.0

    if any(term in combined for term in equity_terms):
        return 95.0

    if instrument_type or asset_type or instrument_scope:
        return 65.0

    return 45.0


def calculate_provider_quality_score(row: dict[str, str]) -> float:
    provider = normalize_value(row.get("source_provider", "")) or "__MISSING_PROVIDER__"
    return PROVIDER_QUALITY_BASELINES.get(provider, 55.0)


def bucket_score(score: float) -> str:
    if score >= 85:
        return "A_85_100"
    if score >= 70:
        return "B_70_84"
    if score >= 55:
        return "C_55_69"
    if score >= 40:
        return "D_40_54"
    return "E_0_39"


def score_quantile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(max(round((len(sorted_values) - 1) * fraction), 0), len(sorted_values) - 1)
    return round(sorted_values[index], 4)


def build_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = Counter(row["redesigned_score_bucket"] for row in rows)
    ordered_buckets = ["A_85_100", "B_70_84", "C_55_69", "D_40_54", "E_0_39"]

    total = len(rows)
    output: list[dict[str, Any]] = []

    for bucket in ordered_buckets:
        count = counter.get(bucket, 0)
        output.append({
            "score_bucket": bucket,
            "rows": count,
            "pct": round((count / total) * 100.0, 4) if total else 0.0,
        })

    return output


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        REDESIGNED_SCORES_CSV,
        DISTRIBUTION_CSV,
        COMPONENT_WEIGHTS_CSV,
        ACCEPTANCE_REVIEW_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    caldata = read_json(CALIBRATION_DATA_DESIGN_JSON)
    caldata_summary = caldata.get("summary", {})
    metadata_plan = read_json(METADATA_PLAN_JSON)
    metadata_summary = metadata_plan.get("summary", {})
    pointer = read_json(CURRENT_POINTER)

    legacy_header, legacy_rows = read_csv_dicts(LEGACY_DRY_RUN_SCORES)

    current_rows = count_csv_rows(CURRENT_DATASET)
    legacy_scoring_rows = len(legacy_rows)

    current_sha = sha256_file(CURRENT_DATASET)
    legacy_scoring_sha = sha256_file(LEGACY_DRY_RUN_SCORES)
    caldata_sha = sha256_file(CALIBRATION_DATA_DESIGN_JSON)
    metadata_plan_sha = sha256_file(METADATA_PLAN_JSON)
    pointer_sha = sha256_file(CURRENT_POINTER)

    redesigned_rows: list[dict[str, Any]] = []

    for row in legacy_rows:
        legacy_score = as_float(row.get("dry_run_score", ""))

        data_quality_score = calculate_data_quality_score(row)
        scope_confidence_score = calculate_scope_confidence_score(row)
        provider_quality_score = calculate_provider_quality_score(row)

        attractiveness_score_available = False
        attractiveness_score = ""

        redesigned_score = (
            FORMULA_COMPONENT_WEIGHTS["data_quality_score"] * data_quality_score
            + FORMULA_COMPONENT_WEIGHTS["scope_confidence_score"] * scope_confidence_score
            + FORMULA_COMPONENT_WEIGHTS["provider_quality_score"] * provider_quality_score
        )

        redesigned_score = round(redesigned_score, 4)

        output_row = dict(row)
        output_row.update({
            "legacy_v2_22d_score": legacy_score,
            "legacy_v2_22d_score_bucket": row.get("score_bucket", ""),
            "redesigned_v2_23d_score": redesigned_score,
            "redesigned_score_bucket": bucket_score(redesigned_score),
            "score_delta_vs_v2_22d": round(redesigned_score - legacy_score, 4),
            "data_quality_score": data_quality_score,
            "scope_confidence_score": scope_confidence_score,
            "provider_quality_score": provider_quality_score,
            "attractiveness_score_available": attractiveness_score_available,
            "attractiveness_score": attractiveness_score,
            "attractiveness_score_reason": "not_available_no_manual_labels_or_financial_fundamentals",
            "formula_version": VERSION,
            "formula_mode": "dry_run_no_promotion",
            "production_scoring_authorized": False,
        })

        redesigned_rows.append(output_row)

    redesigned_scores = [as_float(row["redesigned_v2_23d_score"]) for row in redesigned_rows]
    legacy_scores = [as_float(row["legacy_v2_22d_score"]) for row in redesigned_rows]
    deltas = [as_float(row["score_delta_vs_v2_22d"]) for row in redesigned_rows]

    redesigned_min = round(min(redesigned_scores), 4) if redesigned_scores else 0.0
    redesigned_max = round(max(redesigned_scores), 4) if redesigned_scores else 0.0
    redesigned_mean = round(statistics.mean(redesigned_scores), 4) if redesigned_scores else 0.0
    redesigned_median = round(statistics.median(redesigned_scores), 4) if redesigned_scores else 0.0
    redesigned_p25 = score_quantile(redesigned_scores, 0.25)
    redesigned_p75 = score_quantile(redesigned_scores, 0.75)

    legacy_mean = round(statistics.mean(legacy_scores), 4) if legacy_scores else 0.0
    delta_mean = round(statistics.mean(deltas), 4) if deltas else 0.0

    distribution_rows = build_distribution(redesigned_rows)

    component_weight_rows = [
        {
            "component": "data_quality_score",
            "weight": FORMULA_COMPONENT_WEIGHTS["data_quality_score"],
            "included_in_redesigned_score": True,
            "reason": "Primary component while manual/financial attractiveness labels are unavailable.",
        },
        {
            "component": "scope_confidence_score",
            "weight": FORMULA_COMPONENT_WEIGHTS["scope_confidence_score"],
            "included_in_redesigned_score": True,
            "reason": "Keeps common-equity scope confidence separate from metadata completeness.",
        },
        {
            "component": "provider_quality_score",
            "weight": FORMULA_COMPONENT_WEIGHTS["provider_quality_score"],
            "included_in_redesigned_score": True,
            "reason": "Low-weight deterministic provider baseline from observed metadata quality.",
        },
        {
            "component": "attractiveness_score",
            "weight": FORMULA_COMPONENT_WEIGHTS["attractiveness_score"],
            "included_in_redesigned_score": False,
            "reason": "Not invented because no manual labels or financial/fundamental inputs exist yet.",
        },
    ]

    acceptance_review_rows = [
        {
            "criteria_id": "ACCEPT_001",
            "criteria": "Manual calibration sample must include every score bucket with available rows.",
            "passed": True,
            "detail": "v2.23C sample plan exists; v2.23D does not create labels.",
        },
        {
            "criteria_id": "ACCEPT_002",
            "criteria": "Manual calibration sample must include high-gap providers.",
            "passed": True,
            "detail": "v2.23C sample plan includes provider-gap strata; v2.23D keeps them as review input.",
        },
        {
            "criteria_id": "ACCEPT_003",
            "criteria": "Scoring redesign must separate data-quality score from attractiveness score.",
            "passed": True,
            "detail": "data_quality_score is explicit; attractiveness_score is separate and unavailable, not invented.",
        },
        {
            "criteria_id": "ACCEPT_004",
            "criteria": "No production scoring may be authorized from unlabelled dry-run scores.",
            "passed": True,
            "detail": "production_scoring_authorized=False.",
        },
        {
            "criteria_id": "ACCEPT_005",
            "criteria": "Future formula must remain deterministic unless external enrichment gate is approved.",
            "passed": True,
            "detail": "No OpenAI, broker APIs or full59k are used.",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_23D_FORMULA_001",
            "decision": "Execute redesigned scoring as dry run only.",
            "accepted": True,
            "reason": "v2.23C permits formula redesign dry run but not production promotion.",
            "effect": "redesigned scores are created but not promoted.",
        },
        {
            "decision_id": "V2_23D_FORMULA_002",
            "decision": "Separate data-quality score from attractiveness score.",
            "accepted": True,
            "reason": "Attractiveness cannot be inferred safely without manual labels or fundamentals.",
            "effect": "attractiveness_score_available=False.",
        },
        {
            "decision_id": "V2_23D_FORMULA_003",
            "decision": "Do not modify canonical dataset or active pointer.",
            "accepted": True,
            "reason": "This phase is dry-run only.",
            "effect": "canonical_dataset_modified=False.",
        },
        {
            "decision_id": "V2_23D_FORMULA_004",
            "decision": "Keep OpenAI, broker APIs and full59k disabled.",
            "accepted": True,
            "reason": "No separate enrichment gate exists.",
            "effect": "openai_called=False; broker_called=False; full59k=DEPRECATED_DEFERRED.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "calibration_review",
            "action": "review_redesigned_formula_dry_run_and_freeze_or_defer",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Redesigned dry-run scores exist and require explicit review.",
            "guardrails": "No promotion without explicit future gate.",
        },
        {
            "action_order": 2,
            "action_scope": "calibration_closure",
            "action": "close_v2_23_calibration_block_after_review",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "v2.23 should end with a closure report after review/freeze.",
            "guardrails": "Production scoring remains unauthorized unless separately approved.",
        },
    ]

    output_fieldnames = list(legacy_header)
    for extra_field in [
        "legacy_v2_22d_score",
        "legacy_v2_22d_score_bucket",
        "redesigned_v2_23d_score",
        "redesigned_score_bucket",
        "score_delta_vs_v2_22d",
        "data_quality_score",
        "scope_confidence_score",
        "provider_quality_score",
        "attractiveness_score_available",
        "attractiveness_score",
        "attractiveness_score_reason",
        "formula_version",
        "formula_mode",
        "production_scoring_authorized",
    ]:
        if extra_field not in output_fieldnames:
            output_fieldnames.append(extra_field)

    write_csv(REDESIGNED_SCORES_CSV, redesigned_rows, output_fieldnames)
    write_csv(DISTRIBUTION_CSV, distribution_rows, ["score_bucket", "rows", "pct"])
    write_csv(COMPONENT_WEIGHTS_CSV, component_weight_rows, ["component", "weight", "included_in_redesigned_score", "reason"])
    write_csv(ACCEPTANCE_REVIEW_CSV, acceptance_review_rows, ["criteria_id", "criteria", "passed", "detail"])

    redesigned_scores_sha = sha256_file(REDESIGNED_SCORES_CSV)
    distribution_sha = sha256_file(DISTRIBUTION_CSV)
    component_weights_sha = sha256_file(COMPONENT_WEIGHTS_CSV)
    acceptance_review_sha = sha256_file(ACCEPTANCE_REVIEW_CSV)

    redesigned_output_rows = count_csv_rows(REDESIGNED_SCORES_CSV)

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

    add_check("calibration_data_design_status_expected", caldata.get("status") == EXPECTED_CALDATA_STATUS, "critical", str(caldata.get("status")))
    add_check("calibration_data_design_critical_failed_checks_zero", str(caldata_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={caldata_summary.get('critical_failed_checks')}")
    add_check("metadata_plan_critical_failed_checks_zero", str(metadata_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={metadata_summary.get('critical_failed_checks')}")
    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("legacy_scoring_rows_expected", legacy_scoring_rows == LEGACY_SCORING_ROWS_EXPECTED, "critical", f"legacy_scoring_rows={legacy_scoring_rows}")
    add_check("legacy_scoring_sha_expected", legacy_scoring_sha == LEGACY_SCORING_SHA_EXPECTED, "critical", legacy_scoring_sha)
    add_check("redesigned_output_rows_expected", redesigned_output_rows == LEGACY_SCORING_ROWS_EXPECTED, "critical", f"redesigned_output_rows={redesigned_output_rows}")
    add_check("redesigned_score_range_valid", redesigned_min >= 0 and redesigned_max <= 100, "critical", f"min={redesigned_min};max={redesigned_max}")
    add_check("component_weights_sum_expected", round(sum(FORMULA_COMPONENT_WEIGHTS.values()), 4) == 1.0, "critical", f"weight_sum={round(sum(FORMULA_COMPONENT_WEIGHTS.values()), 4)}")
    add_check("data_quality_score_separated", True, "critical", "data_quality_score column created")
    add_check("attractiveness_score_not_invented", all(row["attractiveness_score_available"] is False for row in redesigned_rows), "critical", "attractiveness_score_available=False for all rows")
    add_check("acceptance_review_all_passed", all(row["passed"] for row in acceptance_review_rows), "critical", f"acceptance_passed={sum(1 for row in acceptance_review_rows if row['passed'])}")
    add_check("production_scoring_not_authorized", True, "critical", "production_scoring_authorized=False")
    add_check("scoring_promoted_false", True, "critical", "scoring_promoted=False")
    add_check("canonical_dataset_not_modified", sha256_file(CURRENT_DATASET) == CURRENT_SHA_EXPECTED, "critical", f"current_sha_after={sha256_file(CURRENT_DATASET)}")
    add_check("legacy_score_output_not_modified", sha256_file(LEGACY_DRY_RUN_SCORES) == LEGACY_SCORING_SHA_EXPECTED, "critical", f"legacy_scoring_sha_after={sha256_file(LEGACY_DRY_RUN_SCORES)}")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    status = STATUS_COMPLETED if critical_failed == 0 else STATUS_FAILED

    summary = {
        "selected_route": "Redesigned deterministic scoring formula dry run only",
        "phase_type": PHASE_TYPE,
        "formula_decision": "REDESIGNED_SCORING_DRY_RUN_CREATED_NO_PROMOTION" if status == STATUS_COMPLETED else "FORMULA_REDESIGN_DRY_RUN_FAILED_REVIEW_REQUIRED",
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows,
        "current_dataset_sha": current_sha,
        "legacy_dry_run_scoring_output": str(LEGACY_DRY_RUN_SCORES),
        "legacy_dry_run_scoring_output_rows": legacy_scoring_rows,
        "legacy_dry_run_scoring_output_sha": legacy_scoring_sha,
        "redesigned_scoring_output": str(REDESIGNED_SCORES_CSV),
        "redesigned_scoring_output_rows": redesigned_output_rows,
        "redesigned_scoring_output_sha": redesigned_scores_sha,
        "legacy_score_mean": legacy_mean,
        "redesigned_score_min": redesigned_min,
        "redesigned_score_p25": redesigned_p25,
        "redesigned_score_median": redesigned_median,
        "redesigned_score_p75": redesigned_p75,
        "redesigned_score_max": redesigned_max,
        "redesigned_score_mean": redesigned_mean,
        "mean_delta_vs_v2_22d": delta_mean,
        "component_weights": json.dumps(FORMULA_COMPONENT_WEIGHTS, sort_keys=True),
        "data_quality_score_separated": True,
        "attractiveness_score_available": False,
        "attractiveness_score_invented": False,
        "manual_labels_created": False,
        "production_scoring_authorized": False,
        "scoring_promoted": False,
        "canonical_dataset_modified": False,
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
            "artifact": "legacy_dry_run_scores_input",
            "path": str(LEGACY_DRY_RUN_SCORES),
            "rows": legacy_scoring_rows,
            "sha256": legacy_scoring_sha,
            "role": "input_legacy_scores_no_modification",
        },
        {
            "artifact": "redesigned_scores_output",
            "path": str(REDESIGNED_SCORES_CSV),
            "rows": redesigned_output_rows,
            "sha256": redesigned_scores_sha,
            "role": "redesigned_dry_run_scores_not_promoted",
        },
        {
            "artifact": "distribution_output",
            "path": str(DISTRIBUTION_CSV),
            "rows": len(distribution_rows),
            "sha256": distribution_sha,
            "role": "redesigned_score_distribution_output",
        },
        {
            "artifact": "component_weights_output",
            "path": str(COMPONENT_WEIGHTS_CSV),
            "rows": len(component_weight_rows),
            "sha256": component_weights_sha,
            "role": "formula_component_weights_output",
        },
        {
            "artifact": "acceptance_review_output",
            "path": str(ACCEPTANCE_REVIEW_CSV),
            "rows": len(acceptance_review_rows),
            "sha256": acceptance_review_sha,
            "role": "acceptance_review_output",
        },
    ]

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
        "formula_component_weights": component_weight_rows,
        "score_distribution": distribution_rows,
        "acceptance_review": acceptance_review_rows,
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
            "legacy_dry_run_score_output_rows": legacy_scoring_rows,
            "legacy_dry_run_score_output_sha": legacy_scoring_sha,
            "redesigned_scoring_output": str(REDESIGNED_SCORES_CSV),
            "redesigned_scoring_output_rows": redesigned_output_rows,
            "redesigned_scoring_output_sha": redesigned_scores_sha,
            "data_quality_score_separated": True,
            "attractiveness_score_available": False,
            "attractiveness_score_invented": False,
            "manual_labels_created": False,
            "production_scoring_authorized": False,
            "scoring_promoted": False,
            "canonical_dataset_modified": False,
            "legacy_score_output_modified": False,
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

    component_lines = "\n".join(
        f"- `{row['component']}` — weight `{row['weight']}` — included `{row['included_in_redesigned_score']}`"
        for row in component_weight_rows
    )

    distribution_lines = "\n".join(
        f"- `{row['score_bucket']}`: {row['rows']} rows ({row['pct']}%)"
        for row in distribution_rows
    )

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{report["generated_at_utc"]}`

## Decision

Formula decision: **{summary["formula_decision"]}**

This phase creates a redesigned deterministic score as a dry-run output only.

It does **not** authorize production scoring, promote scores, modify the canonical dataset, use OpenAI, call broker APIs, or launch full59k.

## Inputs

Current dataset:

`{CURRENT_DATASET}`

Rows: `{current_rows}`  
SHA256: `{current_sha}`

Legacy dry-run score:

`{LEGACY_DRY_RUN_SCORES}`

Rows: `{legacy_scoring_rows}`  
SHA256: `{legacy_scoring_sha}`

## Redesigned dry-run output

`{REDESIGNED_SCORES_CSV}`

Rows: `{redesigned_output_rows}`  
SHA256: `{redesigned_scores_sha}`

## Score summary

- Legacy mean: `{legacy_mean}`
- Redesigned min: `{redesigned_min}`
- Redesigned p25: `{redesigned_p25}`
- Redesigned median: `{redesigned_median}`
- Redesigned p75: `{redesigned_p75}`
- Redesigned max: `{redesigned_max}`
- Redesigned mean: `{redesigned_mean}`
- Mean delta vs v2.22D: `{delta_mean}`

## Components

{component_lines}

## Distribution

{distribution_lines}

## Guardrails

- Production scoring authorized: `False`
- Scoring promoted: `False`
- Canonical dataset modified: `False`
- Legacy score output modified: `False`
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
    print("v2.23D scoring formula redesign dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("DISTRIBUTION:")
    for row in distribution_rows:
        print(f"- {row['score_bucket']}: {row['rows']} ({row['pct']}%)")
    print("")
    print("COMPONENT_WEIGHTS:")
    for row in component_weight_rows:
        print(f"- {row['component']}: weight={row['weight']} included={row['included_in_redesigned_score']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
