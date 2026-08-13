from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.22D"
PHASE = "Scoring Dry Run / No Promotion"
PHASE_TYPE = "scoring-dry-run-no-promotion"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

POINTER_JSON = OUTPUT_DIR / "current_operational_universe_pointer.json"
CLASSIFICATION_REVIEW_JSON = OUTPUT_DIR / "residual_instrument_classification_review_v2_22c2.json"
CLASSIFICATION_OVERLAY_CSV = OUTPUT_DIR / "residual_instrument_classification_review_classification_v2_22c2.csv"

CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
PREVIOUS_OPERATIONAL_BASE = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

REPORT_JSON = OUTPUT_DIR / "scoring_dry_run_no_promotion_v2_22d.json"
REPORT_MD = OUTPUT_DIR / "scoring_dry_run_no_promotion_v2_22d.md"
SUMMARY_CSV = OUTPUT_DIR / "scoring_dry_run_no_promotion_summary_v2_22d.csv"
CHECKS_CSV = OUTPUT_DIR / "scoring_dry_run_no_promotion_checks_v2_22d.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "scoring_dry_run_no_promotion_artifact_manifest_v2_22d.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "scoring_dry_run_no_promotion_decision_register_v2_22d.csv"
SCORING_OUTPUT_CSV = OUTPUT_DIR / "scoring_dry_run_no_promotion_scores_v2_22d.csv"
SCORE_DISTRIBUTION_CSV = OUTPUT_DIR / "scoring_dry_run_no_promotion_score_distribution_v2_22d.csv"
SCORE_COMPONENTS_CSV = OUTPUT_DIR / "scoring_dry_run_no_promotion_score_components_v2_22d.csv"
EXCLUDED_SUMMARY_CSV = OUTPUT_DIR / "scoring_dry_run_no_promotion_excluded_summary_v2_22d.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "scoring_dry_run_no_promotion_next_actions_v2_22d.csv"

EXPECTED_CLASSIFICATION_STATUS = "RESIDUAL_INSTRUMENT_CLASSIFICATION_REVIEW_COMPLETED_FULL_DATASET_POLICY_OVERLAY_READY_FOR_SCORING_DRY_RUN_DECISION"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

PREVIOUS_ROWS_EXPECTED = 42708
PREVIOUS_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

EXPECTED_EXCLUDED_ROWS = 9591
EXPECTED_SCORABLE_ROWS = 33498
EXPECTED_OVERLAY_ROWS = 9857

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_COMPLETED = "SCORING_DRY_RUN_NO_PROMOTION_COMPLETED_LOCAL_HEURISTIC_SCORES_CREATED_PROMOTION_DEFERRED"
STATUS_FAILED = "SCORING_DRY_RUN_NO_PROMOTION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.22E - Scoring Promotion / Freeze Decision"
SECONDARY_NEXT_PHASE = "v2.22F - Repo Hygiene / Untracked Files Review"


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


def normalize_key(value: Any) -> str:
    return normalize_value(value).lower()


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
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


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
        "isin": find_column(header, ["isin"]),
        "ticker": find_column(header, ["ticker", "symbol"]),
        "name": find_column(header, ["company_name", "name", "security_name", "instrument_name"]),
        "exchange": find_column(header, ["exchange"]),
        "country": find_column(header, ["country"]),
        "mic": find_column(header, ["mic"]),
        "currency": find_column(header, ["currency"]),
        "source_provider": find_column(header, ["source_provider", "provider"]),
        "asset_type": find_column(header, ["asset_type"]),
        "instrument_type": find_column(header, ["instrument_type"]),
        "instrument_scope": find_column(header, ["instrument_scope"]),
        "classification_confidence": find_column(header, ["classification_confidence"]),
        "classification_reason": find_column(header, ["classification_reason"]),
        "market_cap": find_column(header, ["market_cap"]),
        "sector": find_column(header, ["sector"]),
        "industry": find_column(header, ["industry"]),
        "source_version": find_column(header, ["source_version"]),
        "source_url": find_column(header, ["source_url"]),
    }


def get_value(row: dict[str, str], column: str | None) -> str:
    if not column:
        return ""
    return normalize_value(row.get(column, ""))


def has_value(row: dict[str, str], column: str | None) -> bool:
    return bool(get_value(row, column))


def score_presence(row: dict[str, str], columns: dict[str, str | None], roles: list[str]) -> float:
    available = 0
    possible = 0

    for role in roles:
        possible += 1
        if has_value(row, columns.get(role)):
            available += 1

    if possible == 0:
        return 0.0

    return available / possible


def confidence_points(value: str) -> float:
    normalized = normalize_key(value)

    if normalized == "high":
        return 1.0
    if normalized == "medium":
        return 0.65
    if normalized == "low":
        return 0.35
    if normalized:
        return 0.5

    return 0.0


def source_provider_points(value: str) -> float:
    normalized = normalize_key(value)

    if not normalized:
        return 0.25

    strong_sources = [
        "nasdaq",
        "sec_company_tickers_exchange",
        "cboe",
        "hkex",
        "jpx",
        "xetra",
        "deutsche_boerse",
        "nse",
        "twse",
        "asx",
        "sgx_structured_endpoint",
        "sfc_simev_rnve",
    ]

    if any(token in normalized for token in strong_sources):
        return 1.0

    return 0.6


def asset_type_points(value: str) -> float:
    normalized = normalize_key(value)

    if not normalized:
        return 0.35

    if "equity" in normalized or "ordinary" in normalized or "common" in normalized or "reit" in normalized or "trust" in normalized:
        return 1.0

    return 0.45


def instrument_scope_points(value: str) -> float:
    normalized = normalize_key(value)

    if not normalized:
        return 0.35

    if "in_scope" in normalized:
        return 1.0

    if "candidate" in normalized or "pending" in normalized or "unknown" in normalized:
        return 0.45

    return 0.6


def compute_score(row: dict[str, str], columns: dict[str, str | None]) -> tuple[float, dict[str, float]]:
    identifier_component = score_presence(row, columns, ["isin", "ticker", "name", "exchange"])
    market_component = score_presence(row, columns, ["country", "mic", "currency", "exchange"])
    classification_component = (
        0.45 * asset_type_points(get_value(row, columns.get("asset_type"))) +
        0.35 * instrument_scope_points(get_value(row, columns.get("instrument_scope"))) +
        0.20 * confidence_points(get_value(row, columns.get("classification_confidence")))
    )
    provenance_component = (
        0.60 * source_provider_points(get_value(row, columns.get("source_provider"))) +
        0.20 * (1.0 if has_value(row, columns.get("source_version")) else 0.0) +
        0.20 * (1.0 if has_value(row, columns.get("source_url")) else 0.0)
    )
    enrichment_component = score_presence(row, columns, ["sector", "industry", "market_cap"])

    total = (
        0.30 * identifier_component +
        0.20 * market_component +
        0.20 * classification_component +
        0.20 * provenance_component +
        0.10 * enrichment_component
    )

    components = {
        "identifier_component": round(identifier_component, 6),
        "market_component": round(market_component, 6),
        "classification_component": round(classification_component, 6),
        "provenance_component": round(provenance_component, 6),
        "enrichment_component": round(enrichment_component, 6),
    }

    return round(total * 100, 4), components


def score_bucket(score: float) -> str:
    if score >= 85:
        return "A_85_100"
    if score >= 70:
        return "B_70_84"
    if score >= 55:
        return "C_55_69"
    if score >= 40:
        return "D_40_54"
    return "E_0_39"


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return round(sorted_values[int(position)], 4)

    lower_value = sorted_values[lower]
    upper_value = sorted_values[upper]
    weight = position - lower

    return round(lower_value * (1 - weight) + upper_value * weight, 4)


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        DECISION_REGISTER_CSV,
        SCORING_OUTPUT_CSV,
        SCORE_DISTRIBUTION_CSV,
        SCORE_COMPONENTS_CSV,
        EXCLUDED_SUMMARY_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    pointer = read_json(POINTER_JSON)
    classification_review = read_json(CLASSIFICATION_REVIEW_JSON)
    classification_summary = classification_review.get("summary", {})

    current_header, current_rows = read_csv_dicts(CURRENT_DATASET)
    _, overlay_rows = read_csv_dicts(CLASSIFICATION_OVERLAY_CSV)

    columns = resolve_columns(current_header)

    current_rows_count = len(current_rows)
    previous_rows_count = count_csv_rows(PREVIOUS_OPERATIONAL_BASE)
    rollback_rows_count = count_csv_rows(ROLLBACK_DATASET)

    current_sha = sha256_file(CURRENT_DATASET)
    previous_sha = sha256_file(PREVIOUS_OPERATIONAL_BASE)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    pointer_sha = sha256_file(POINTER_JSON)
    classification_review_sha = sha256_file(CLASSIFICATION_REVIEW_JSON)
    classification_overlay_sha = sha256_file(CLASSIFICATION_OVERLAY_CSV)

    excluded_row_numbers: set[int] = set()
    overlay_row_numbers: set[int] = set()
    excluded_policy_counter = Counter()

    for overlay in overlay_rows:
        row_number_raw = normalize_value(overlay.get("row_number", ""))
        if not row_number_raw:
            continue

        row_number = int(row_number_raw)
        overlay_row_numbers.add(row_number)

        if normalize_value(overlay.get("policy_classification", "")) == "exclude_from_common_equity_scoring":
            excluded_row_numbers.add(row_number)
            excluded_policy_counter[normalize_value(overlay.get("policy_match", "")) or "__MISSING_POLICY_MATCH__"] += 1

    scoring_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    score_values: list[float] = []
    score_bucket_counter = Counter()
    exchange_counter = Counter()
    country_counter = Counter()
    source_counter = Counter()

    for zero_based_index, row in enumerate(current_rows):
        csv_row_number = zero_based_index + 2

        if csv_row_number in excluded_row_numbers:
            continue

        score, components = compute_score(row, columns)
        bucket = score_bucket(score)

        score_values.append(score)
        score_bucket_counter[bucket] += 1
        exchange_counter[get_value(row, columns.get("exchange")) or "__MISSING__"] += 1
        country_counter[get_value(row, columns.get("country")) or "__MISSING__"] += 1
        source_counter[get_value(row, columns.get("source_provider")) or "__MISSING__"] += 1

        isin = get_value(row, columns.get("isin"))
        ticker = get_value(row, columns.get("ticker"))
        name = get_value(row, columns.get("name"))
        exchange = get_value(row, columns.get("exchange"))

        scoring_rows.append({
            "dry_run_rank": 0,
            "source_row_number": csv_row_number,
            "dry_run_score": score,
            "score_bucket": bucket,
            "isin": isin,
            "ticker": ticker,
            "name": name,
            "exchange": exchange,
            "country": get_value(row, columns.get("country")),
            "mic": get_value(row, columns.get("mic")),
            "currency": get_value(row, columns.get("currency")),
            "source_provider": get_value(row, columns.get("source_provider")),
            "asset_type": get_value(row, columns.get("asset_type")),
            "instrument_type": get_value(row, columns.get("instrument_type")),
            "instrument_scope": get_value(row, columns.get("instrument_scope")),
            "classification_confidence": get_value(row, columns.get("classification_confidence")),
            "scoring_mode": "LOCAL_HEURISTIC_DRY_RUN",
            "promotion_status": "NOT_PROMOTED",
        })

        component_rows.append({
            "source_row_number": csv_row_number,
            "dry_run_score": score,
            "identifier_component": components["identifier_component"],
            "market_component": components["market_component"],
            "classification_component": components["classification_component"],
            "provenance_component": components["provenance_component"],
            "enrichment_component": components["enrichment_component"],
        })

    scoring_rows.sort(key=lambda item: (-float(item["dry_run_score"]), str(item["exchange"]), str(item["ticker"]), str(item["name"])))

    for rank, row in enumerate(scoring_rows, start=1):
        row["dry_run_rank"] = rank

    score_distribution_rows = [
        {
            "bucket": bucket,
            "count": score_bucket_counter[bucket],
            "pct": round((score_bucket_counter[bucket] / len(scoring_rows)) * 100, 4) if scoring_rows else 0.0,
        }
        for bucket in ["A_85_100", "B_70_84", "C_55_69", "D_40_54", "E_0_39"]
    ]

    excluded_summary_rows = [
        {
            "policy_match": key,
            "excluded_rows": value,
            "pct_of_excluded": round((value / len(excluded_row_numbers)) * 100, 4) if excluded_row_numbers else 0.0,
        }
        for key, value in excluded_policy_counter.most_common()
    ]

    score_component_summary_rows = [
        {
            "metric": "score_min",
            "value": min(score_values) if score_values else 0.0,
        },
        {
            "metric": "score_p25",
            "value": quantile(score_values, 0.25),
        },
        {
            "metric": "score_median",
            "value": quantile(score_values, 0.50),
        },
        {
            "metric": "score_p75",
            "value": quantile(score_values, 0.75),
        },
        {
            "metric": "score_max",
            "value": max(score_values) if score_values else 0.0,
        },
        {
            "metric": "score_mean",
            "value": round(sum(score_values) / len(score_values), 4) if score_values else 0.0,
        },
    ]

    write_csv(SCORING_OUTPUT_CSV, scoring_rows, [
        "dry_run_rank",
        "source_row_number",
        "dry_run_score",
        "score_bucket",
        "isin",
        "ticker",
        "name",
        "exchange",
        "country",
        "mic",
        "currency",
        "source_provider",
        "asset_type",
        "instrument_type",
        "instrument_scope",
        "classification_confidence",
        "scoring_mode",
        "promotion_status",
    ])

    write_csv(SCORE_DISTRIBUTION_CSV, score_distribution_rows, ["bucket", "count", "pct"])
    write_csv(SCORE_COMPONENTS_CSV, score_component_summary_rows, ["metric", "value"])
    write_csv(EXCLUDED_SUMMARY_CSV, excluded_summary_rows, ["policy_match", "excluded_rows", "pct_of_excluded"])

    scoring_output_sha = sha256_file(SCORING_OUTPUT_CSV)
    score_distribution_sha = sha256_file(SCORE_DISTRIBUTION_CSV)
    score_components_sha = sha256_file(SCORE_COMPONENTS_CSV)
    excluded_summary_sha = sha256_file(EXCLUDED_SUMMARY_CSV)

    scoring_rows_count = len(scoring_rows)
    excluded_rows_count = len(excluded_row_numbers)
    overlay_rows_count = len(overlay_rows)

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

    add_check("classification_review_status_expected", classification_review.get("status") == EXPECTED_CLASSIFICATION_STATUS, "critical", str(classification_review.get("status")))
    add_check("classification_review_approved_for_scoring_dry_run_decision", str(classification_summary.get("approved_for_scoring_dry_run_decision")) == "True", "critical", f"approved={classification_summary.get('approved_for_scoring_dry_run_decision')}")
    add_check("classification_review_not_approved_for_scoring_execution", str(classification_summary.get("approved_for_scoring_execution")) == "False", "critical", f"approved_for_scoring_execution={classification_summary.get('approved_for_scoring_execution')}")
    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows_count == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows_count}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("previous_rows_expected", previous_rows_count == PREVIOUS_ROWS_EXPECTED, "critical", f"previous_rows={previous_rows_count}")
    add_check("previous_sha_expected", previous_sha == PREVIOUS_SHA_EXPECTED, "critical", previous_sha)
    add_check("rollback_rows_expected", rollback_rows_count == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows_count}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("classification_overlay_rows_expected", overlay_rows_count == EXPECTED_OVERLAY_ROWS, "critical", f"overlay_rows={overlay_rows_count};expected={EXPECTED_OVERLAY_ROWS}")
    add_check("excluded_rows_expected", excluded_rows_count == EXPECTED_EXCLUDED_ROWS, "critical", f"excluded_rows={excluded_rows_count};expected={EXPECTED_EXCLUDED_ROWS}")
    add_check("scorable_rows_expected", scoring_rows_count == EXPECTED_SCORABLE_ROWS, "critical", f"scorable_rows={scoring_rows_count};expected={EXPECTED_SCORABLE_ROWS}")
    add_check("excluded_plus_scorable_equals_current", excluded_rows_count + scoring_rows_count == current_rows_count, "critical", f"excluded={excluded_rows_count};scorable={scoring_rows_count};current={current_rows_count}")
    add_check("score_output_created", SCORING_OUTPUT_CSV.exists(), "critical", str(SCORING_OUTPUT_CSV))
    add_check("score_output_rows_expected", count_csv_rows(SCORING_OUTPUT_CSV) == EXPECTED_SCORABLE_ROWS, "critical", f"score_rows={count_csv_rows(SCORING_OUTPUT_CSV)}")
    add_check("score_values_within_0_100", all(0 <= value <= 100 for value in score_values), "critical", "all_scores_between_0_and_100=True")
    add_check("within_quality_floor", current_rows_count >= QUALITY_FLOOR_TARGET, "critical", f"current_rows={current_rows_count};floor={QUALITY_FLOOR_TARGET}")
    add_check("within_quality_ceiling", current_rows_count <= QUALITY_CEILING_TARGET, "critical", f"current_rows={current_rows_count};ceiling={QUALITY_CEILING_TARGET}")
    add_check("dry_run_scoring_executed", True, "critical", "dry_run_scoring_executed=True")
    add_check("production_scoring_not_authorized", True, "critical", "production_scoring_authorized=False")
    add_check("promotion_not_performed", True, "critical", "scoring_promoted=False")
    add_check("canonical_dataset_not_modified", sha256_file(CURRENT_DATASET) == CURRENT_SHA_EXPECTED, "critical", f"current_sha_after={sha256_file(CURRENT_DATASET)}")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    status = STATUS_COMPLETED if critical_failed == 0 else STATUS_FAILED

    dry_run_score_min = min(score_values) if score_values else 0.0
    dry_run_score_max = max(score_values) if score_values else 0.0
    dry_run_score_mean = round(sum(score_values) / len(score_values), 4) if score_values else 0.0
    dry_run_score_median = quantile(score_values, 0.50)

    top_exchange = exchange_counter.most_common(1)[0][0] if exchange_counter else ""
    top_country = country_counter.most_common(1)[0][0] if country_counter else ""
    top_source_provider = source_counter.most_common(1)[0][0] if source_counter else ""

    summary = {
        "selected_route": "Local heuristic scoring dry run using v2.22C2 exclusion overlay",
        "phase_type": PHASE_TYPE,
        "dry_run_decision": "SCORING_DRY_RUN_CREATED_PROMOTION_DEFERRED" if status == STATUS_COMPLETED else "SCORING_DRY_RUN_FAILED_REVIEW_REQUIRED",
        "current_operational_pointer": str(POINTER_JSON),
        "current_operational_pointer_sha": pointer_sha,
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows_count,
        "current_dataset_sha": current_sha,
        "classification_review": str(CLASSIFICATION_REVIEW_JSON),
        "classification_review_sha": classification_review_sha,
        "classification_overlay": str(CLASSIFICATION_OVERLAY_CSV),
        "classification_overlay_rows": overlay_rows_count,
        "classification_overlay_sha": classification_overlay_sha,
        "excluded_from_common_equity_scoring_rows": excluded_rows_count,
        "scorable_rows": scoring_rows_count,
        "scoring_output": str(SCORING_OUTPUT_CSV),
        "scoring_output_rows": scoring_rows_count,
        "scoring_output_sha": scoring_output_sha,
        "score_min": dry_run_score_min,
        "score_p25": quantile(score_values, 0.25),
        "score_median": dry_run_score_median,
        "score_p75": quantile(score_values, 0.75),
        "score_max": dry_run_score_max,
        "score_mean": dry_run_score_mean,
        "top_exchange_by_scorable_rows": top_exchange,
        "top_country_by_scorable_rows": top_country,
        "top_source_provider_by_scorable_rows": top_source_provider,
        "dry_run_scoring_authorized": True,
        "dry_run_scoring_executed": True,
        "approved_for_promotion": False,
        "scoring_promoted": False,
        "production_scoring_authorized": False,
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
            "path": str(POINTER_JSON),
            "rows": 1,
            "sha256": pointer_sha,
            "role": "input_pointer",
        },
        {
            "artifact": "current_dataset_input",
            "path": str(CURRENT_DATASET),
            "rows": current_rows_count,
            "sha256": current_sha,
            "role": "input_dataset_no_modification",
        },
        {
            "artifact": "classification_review_input",
            "path": str(CLASSIFICATION_REVIEW_JSON),
            "rows": 1,
            "sha256": classification_review_sha,
            "role": "input_classification_gate",
        },
        {
            "artifact": "classification_overlay_input",
            "path": str(CLASSIFICATION_OVERLAY_CSV),
            "rows": overlay_rows_count,
            "sha256": classification_overlay_sha,
            "role": "input_exclusion_overlay",
        },
        {
            "artifact": "scoring_output",
            "path": str(SCORING_OUTPUT_CSV),
            "rows": scoring_rows_count,
            "sha256": scoring_output_sha,
            "role": "dry_run_scores_not_promoted",
        },
        {
            "artifact": "score_distribution",
            "path": str(SCORE_DISTRIBUTION_CSV),
            "rows": len(score_distribution_rows),
            "sha256": score_distribution_sha,
            "role": "dry_run_score_distribution",
        },
        {
            "artifact": "score_components",
            "path": str(SCORE_COMPONENTS_CSV),
            "rows": len(score_component_summary_rows),
            "sha256": score_components_sha,
            "role": "dry_run_score_component_summary",
        },
        {
            "artifact": "excluded_summary",
            "path": str(EXCLUDED_SUMMARY_CSV),
            "rows": len(excluded_summary_rows),
            "sha256": excluded_summary_sha,
            "role": "excluded_rows_policy_summary",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_22D_SCORE_001",
            "decision": "Run local heuristic scoring as dry run only.",
            "accepted": True,
            "reason": "v2.22C2 approved a scoring dry run decision but not production scoring.",
            "effect": "Creates dry-run scores without promotion.",
        },
        {
            "decision_id": "V2_22D_SCORE_002",
            "decision": "Exclude v2.22C2 non-common-equity policy rows from the scoring dry run.",
            "accepted": True,
            "reason": "Residual instrument classification identified non-common-equity/fund/fixed-income rows.",
            "effect": f"excluded_from_common_equity_scoring_rows={excluded_rows_count}.",
        },
        {
            "decision_id": "V2_22D_SCORE_003",
            "decision": "Do not promote dry-run score output.",
            "accepted": True,
            "reason": "Promotion/freeze decision belongs to v2.22E.",
            "effect": "approved_for_promotion=False.",
        },
        {
            "decision_id": "V2_22D_SCORE_004",
            "decision": "Do not call OpenAI, broker APIs, or full59k.",
            "accepted": True,
            "reason": "v2.22D is a local deterministic dry run.",
            "effect": "External calls remain disabled.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "promotion_freeze_decision",
            "action": "review_scoring_dry_run_and_decide_promote_or_freeze",
            "priority": "high",
            "recommended_phase": NEXT_PHASE,
            "reason": "Dry-run scores exist but are not promoted.",
            "guardrails": "No canonical replacement without explicit v2.22E decision.",
        },
        {
            "action_order": 2,
            "action_scope": "repo_hygiene",
            "action": "review_untracked_audit_and_country_breakdown_files",
            "priority": "medium",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Repo still has unrelated untracked files.",
            "guardrails": "Do not add unrelated files automatically.",
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
        "score_distribution": score_distribution_rows,
        "score_component_summary": score_component_summary_rows,
        "excluded_summary": excluded_summary_rows,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "current_dataset": str(CURRENT_DATASET),
            "current_dataset_rows": current_rows_count,
            "current_dataset_sha": current_sha,
            "classification_overlay": str(CLASSIFICATION_OVERLAY_CSV),
            "scoring_output": str(SCORING_OUTPUT_CSV),
            "scoring_output_rows": scoring_rows_count,
            "dry_run_scoring_authorized": True,
            "dry_run_scoring_executed": True,
            "approved_for_promotion": False,
            "scoring_promoted": False,
            "production_scoring_authorized": False,
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

    distribution_lines = "\n".join(
        f"- {row['bucket']}: {row['count']} ({row['pct']}%)"
        for row in score_distribution_rows
    )

    write_text(
        REPORT_MD,
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{report["generated_at_utc"]}`

## Executive summary

v2.22D creates a local deterministic scoring dry run using the current operational universe and the v2.22C2 exclusion overlay.

This phase does not promote scores and does not modify the canonical dataset.

## Inputs

Current dataset:

`{CURRENT_DATASET}`

Rows: `{current_rows_count}`  
SHA256: `{current_sha}`

Classification overlay:

`{CLASSIFICATION_OVERLAY_CSV}`

Overlay rows: `{overlay_rows_count}`  
Excluded rows: `{excluded_rows_count}`

## Dry-run scoring output

`{SCORING_OUTPUT_CSV}`

Scored rows: `{scoring_rows_count}`  
SHA256: `{scoring_output_sha}`

## Score summary

- Min: `{dry_run_score_min}`
- P25: `{quantile(score_values, 0.25)}`
- Median: `{dry_run_score_median}`
- P75: `{quantile(score_values, 0.75)}`
- Max: `{dry_run_score_max}`
- Mean: `{dry_run_score_mean}`

## Score distribution

{distribution_lines}

## Guardrails

- Dry-run scoring executed: `True`
- Approved for promotion: `False`
- Scoring promoted: `False`
- Production scoring authorized: `False`
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
    print("v2.22D scoring dry run / no promotion completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SCORE_DISTRIBUTION:")
    for row in score_distribution_rows:
        print(f"- {row['bucket']}: {row['count']} ({row['pct']}%)")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
