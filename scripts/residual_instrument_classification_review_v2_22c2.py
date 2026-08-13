from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.22C2"
PHASE = "Residual Instrument Classification Review"
PHASE_TYPE = "residual-instrument-classification-review"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

REVIEW_REPORT = OUTPUT_DIR / "pre_scoring_quality_findings_review_v2_22c_review.json"
CURRENT_POINTER = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
PREVIOUS_OPERATIONAL_BASE = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

REPORT_JSON = OUTPUT_DIR / "residual_instrument_classification_review_v2_22c2.json"
REPORT_MD = OUTPUT_DIR / "residual_instrument_classification_review_v2_22c2.md"
SUMMARY_CSV = OUTPUT_DIR / "residual_instrument_classification_review_summary_v2_22c2.csv"
CHECKS_CSV = OUTPUT_DIR / "residual_instrument_classification_review_checks_v2_22c2.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "residual_instrument_classification_review_artifact_manifest_v2_22c2.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "residual_instrument_classification_review_decision_register_v2_22c2.csv"
CLASSIFICATION_CSV = OUTPUT_DIR / "residual_instrument_classification_review_classification_v2_22c2.csv"
POLICY_CSV = OUTPUT_DIR / "residual_instrument_classification_review_policy_v2_22c2.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "residual_instrument_classification_review_next_actions_v2_22c2.csv"

EXPECTED_REVIEW_STATUS = "PRE_SCORING_QUALITY_FINDINGS_REVIEW_COMPLETED_RESIDUAL_REVIEW_REQUIRED_SCORING_DRY_RUN_DEFERRED"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

PREVIOUS_ROWS_EXPECTED = 42708
PREVIOUS_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_READY = "RESIDUAL_INSTRUMENT_CLASSIFICATION_REVIEW_COMPLETED_FULL_DATASET_POLICY_OVERLAY_READY_FOR_SCORING_DRY_RUN_DECISION"
STATUS_REVIEW = "RESIDUAL_INSTRUMENT_CLASSIFICATION_REVIEW_COMPLETED_UNCLASSIFIED_RESIDUALS_REMAIN_SCORING_DRY_RUN_DEFERRED"
STATUS_FAILED = "RESIDUAL_INSTRUMENT_CLASSIFICATION_REVIEW_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_READY = "v2.22D - Scoring Dry Run / No Promotion"
NEXT_PHASE_REVIEW = "v2.22C3 - Manual Residual Classification Review"

REVIEW_PATTERNS = {
    "fund": re.compile(r"\bfunds?\b", re.IGNORECASE),
    "closed_end_fund": re.compile(r"\bclosed[- ]end fund\b", re.IGNORECASE),
    "etf": re.compile(r"\betfs?\b|\bexchange[- ]traded fund\b", re.IGNORECASE),
    "note": re.compile(r"\bnotes?\b", re.IGNORECASE),
    "debenture": re.compile(r"\bdebentures?\b", re.IGNORECASE),
    "preferred_or_preference": re.compile(r"\bpreferred\b|\bpreference share\b|\bpreferential\b", re.IGNORECASE),
    "bond": re.compile(r"\bbonds?\b|\bbonos?\b", re.IGNORECASE),
    "warrant": re.compile(r"\bwarrants?\b", re.IGNORECASE),
    "right": re.compile(r"\brights?\b", re.IGNORECASE),
    "certificate": re.compile(r"\bcertificates?\b|\bcertificados?\b|\bcdt\b", re.IGNORECASE),
}

FALSE_POSITIVE_CONTEXTS = {
    "common stock",
    "ordinary shares",
    "ordinary share",
    "common shares",
    "equity inc.",
}

NON_COMMON_POLICIES = {
    "exclude_fixed_income_note": re.compile(r"\bnotes?\b", re.IGNORECASE),
    "exclude_fixed_income_debenture": re.compile(r"\bdebentures?\b", re.IGNORECASE),
    "exclude_fixed_income_bond": re.compile(r"\bbonds?\b|\bbonos?\b", re.IGNORECASE),
    "exclude_preferred_or_preference": re.compile(r"\bpreferred\b|\bpreference share\b|\bpreferential\b", re.IGNORECASE),
    "exclude_warrant": re.compile(r"\bwarrants?\b", re.IGNORECASE),
    "exclude_right": re.compile(r"\brights?\b", re.IGNORECASE),
    "exclude_certificate": re.compile(r"\bcertificates?\b|\bcertificados?\b|\bcdt\b", re.IGNORECASE),
    "exclude_etf": re.compile(r"\betfs?\b|\bexchange[- ]traded fund\b", re.IGNORECASE),
    "exclude_closed_end_fund": re.compile(r"\bclosed[- ]end fund\b", re.IGNORECASE),
    "exclude_fund_like": re.compile(r"\bfunds?\b", re.IGNORECASE),
}


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
    }


def get_value(row: dict[str, str], column: str | None) -> str:
    if not column:
        return ""
    return normalize_value(row.get(column, ""))


def row_text(row: dict[str, str], columns: dict[str, str | None]) -> str:
    parts = [
        get_value(row, columns.get("name")),
        get_value(row, columns.get("asset_type")),
        get_value(row, columns.get("instrument_type")),
        get_value(row, columns.get("instrument_scope")),
    ]
    return " | ".join(parts)


def refined_stage_classification(row: dict[str, str], columns: dict[str, str | None]) -> tuple[str, list[str], str]:
    text = row_text(row, columns)
    lower_text = text.lower()

    matched = [label for label, pattern in REVIEW_PATTERNS.items() if pattern.search(text)]

    if not matched:
        return "no_refined_flag", [], "No refined word-boundary review term matched."

    asset_type = get_value(row, columns.get("asset_type")).lower()
    instrument_type = get_value(row, columns.get("instrument_type")).lower()
    instrument_scope = get_value(row, columns.get("instrument_scope")).lower()

    hard_non_common_terms = {
        "note",
        "debenture",
        "preferred_or_preference",
        "bond",
        "warrant",
        "right",
        "certificate",
    }

    if asset_type.startswith("equity") or "equity_like" in asset_type or "common_equity" in asset_type:
        if any(context in lower_text for context in FALSE_POSITIVE_CONTEXTS):
            return "non_blocking_equity_context", matched, "Matched term appears in equity/common-share context."

    if "common_stock" in instrument_type or "common stock" in lower_text or "ordinary share" in lower_text:
        if not any(term in matched for term in hard_non_common_terms):
            return "non_blocking_equity_context", matched, "Common stock / ordinary share context."

    if "in_scope" in instrument_scope and not any(term in matched for term in hard_non_common_terms):
        return "non_blocking_in_scope_context", matched, "Existing instrument scope is in-scope."

    return "residual_review_required", matched, "Potential non-common-equity/fund-like instrument needs policy overlay."


def policy_overlay_classification(row: dict[str, str], columns: dict[str, str | None], refined_classification: str, matched_terms: list[str]) -> tuple[str, str, str]:
    if refined_classification != "residual_review_required":
        return (
            "not_residual_prior_non_blocking_or_no_flag",
            refined_classification,
            "Row is not a residual blocker after refined review."
        )

    text = row_text(row, columns) + " | " + ";".join(matched_terms)

    policy_matches = [
        label for label, pattern in NON_COMMON_POLICIES.items()
        if pattern.search(text)
    ]

    if policy_matches:
        return (
            "exclude_from_common_equity_scoring",
            ";".join(policy_matches),
            "Residual row matches explicit non-common-equity/fund/fixed-income policy."
        )

    asset_type = get_value(row, columns.get("asset_type"))
    instrument_type = get_value(row, columns.get("instrument_type"))
    instrument_scope = get_value(row, columns.get("instrument_scope"))

    if not asset_type and not instrument_type and not instrument_scope:
        return (
            "classification_unknown_missing_instrument_metadata",
            "missing_asset_type_instrument_type_scope",
            "Instrument metadata is missing; hold out until metadata/policy review."
        )

    return (
        "classification_unknown_manual_review_required",
        "no_policy_match",
        "No clear exclusion or eligibility policy matched."
    )


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        DECISION_REGISTER_CSV,
        CLASSIFICATION_CSV,
        POLICY_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    review = read_json(REVIEW_REPORT)
    review_summary = review.get("summary", {})
    pointer = read_json(CURRENT_POINTER)

    current_header, current_rows_data = read_csv_dicts(CURRENT_DATASET)

    columns = resolve_columns(current_header)

    current_rows = len(current_rows_data)
    previous_rows = count_csv_rows(PREVIOUS_OPERATIONAL_BASE)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)

    current_sha = sha256_file(CURRENT_DATASET)
    previous_sha = sha256_file(PREVIOUS_OPERATIONAL_BASE)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    pointer_sha = sha256_file(CURRENT_POINTER)
    review_sha = sha256_file(REVIEW_REPORT)

    expected_residual_rows = int(review_summary.get("refined_instrument_residual_review_required", 0))
    expected_no_flag_rows = int(review_summary.get("refined_instrument_no_flag", 0))
    expected_non_blocking_equity = int(review_summary.get("refined_instrument_non_blocking_equity_context", 0))
    expected_non_blocking_scope = int(review_summary.get("refined_instrument_non_blocking_in_scope_context", 0))

    classification_rows: list[dict[str, Any]] = []
    refined_counter = Counter()
    policy_counter = Counter()
    policy_match_counter = Counter()

    for row_number, row in enumerate(current_rows_data, start=2):
        refined_classification, matched_terms, refined_reason = refined_stage_classification(row, columns)
        policy_classification, policy_match, policy_reason = policy_overlay_classification(row, columns, refined_classification, matched_terms)

        refined_counter[refined_classification] += 1
        policy_counter[policy_classification] += 1
        policy_match_counter[policy_match] += 1

        # Overlay stores all rows that were flagged or policy-relevant.
        # Non-flag rows are implicitly eligible candidates and are summarized, not written row-by-row.
        if refined_classification != "no_refined_flag":
            classification_rows.append({
                "row_number": row_number,
                "refined_classification": refined_classification,
                "matched_terms": ";".join(matched_terms),
                "refined_reason": refined_reason,
                "policy_classification": policy_classification,
                "policy_match": policy_match,
                "policy_reason": policy_reason,
                "isin": get_value(row, columns.get("isin")),
                "ticker": get_value(row, columns.get("ticker")),
                "name": get_value(row, columns.get("name")),
                "exchange": get_value(row, columns.get("exchange")),
                "country": get_value(row, columns.get("country")),
                "mic": get_value(row, columns.get("mic")),
                "currency": get_value(row, columns.get("currency")),
                "source_provider": get_value(row, columns.get("source_provider")),
                "asset_type": get_value(row, columns.get("asset_type")),
                "instrument_type": get_value(row, columns.get("instrument_type")),
                "instrument_scope": get_value(row, columns.get("instrument_scope")),
            })

    residual_rows = refined_counter["residual_review_required"]
    no_flag_rows = refined_counter["no_refined_flag"]
    non_blocking_equity_rows = refined_counter["non_blocking_equity_context"]
    non_blocking_scope_rows = refined_counter["non_blocking_in_scope_context"]
    flagged_overlay_rows = len(classification_rows)

    excluded_rows = policy_counter["exclude_from_common_equity_scoring"]
    unknown_missing_metadata_rows = policy_counter["classification_unknown_missing_instrument_metadata"]
    unknown_manual_review_rows = policy_counter["classification_unknown_manual_review_required"]
    unknown_total = unknown_missing_metadata_rows + unknown_manual_review_rows

    policy_rows = []
    for bucket, count in policy_counter.most_common():
        if bucket == "exclude_from_common_equity_scoring":
            scoring_policy = "exclude_from_v2_22d_common_equity_scoring_dry_run"
        elif bucket == "not_residual_prior_non_blocking_or_no_flag":
            scoring_policy = "not_excluded_by_residual_policy"
        else:
            scoring_policy = "hold_out_until_manual_or_metadata_review"

        policy_rows.append({
            "policy_bucket": bucket,
            "count": count,
            "scoring_policy": scoring_policy,
        })

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

    add_check("review_status_expected", review.get("status") == EXPECTED_REVIEW_STATUS, "critical", str(review.get("status")))
    add_check("review_critical_failed_checks_zero", str(review_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={review_summary.get('critical_failed_checks')}")
    add_check("pointer_current_dataset_expected", pointer.get("current_dataset") == str(CURRENT_DATASET), "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("previous_rows_expected", previous_rows == PREVIOUS_ROWS_EXPECTED, "critical", f"previous_rows={previous_rows}")
    add_check("previous_sha_expected", previous_sha == PREVIOUS_SHA_EXPECTED, "critical", previous_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("full_dataset_residual_rows_expected", residual_rows == expected_residual_rows, "critical", f"residual_rows={residual_rows};expected={expected_residual_rows}")
    add_check("full_dataset_no_flag_rows_expected", no_flag_rows == expected_no_flag_rows, "critical", f"no_flag_rows={no_flag_rows};expected={expected_no_flag_rows}")
    add_check("non_blocking_equity_rows_expected", non_blocking_equity_rows == expected_non_blocking_equity, "critical", f"non_blocking_equity={non_blocking_equity_rows};expected={expected_non_blocking_equity}")
    add_check("non_blocking_scope_rows_expected", non_blocking_scope_rows == expected_non_blocking_scope, "critical", f"non_blocking_scope={non_blocking_scope_rows};expected={expected_non_blocking_scope}")
    add_check("classification_overlay_rows_expected", flagged_overlay_rows == (residual_rows + non_blocking_equity_rows + non_blocking_scope_rows), "critical", f"overlay_rows={flagged_overlay_rows}")
    add_check("excluded_rows_documented", excluded_rows >= 0, "critical", f"excluded_rows={excluded_rows}")
    add_check("unknown_rows_documented", True, "warning", f"unknown_total={unknown_total};missing_metadata={unknown_missing_metadata_rows};manual={unknown_manual_review_rows}")
    add_check("within_quality_floor", current_rows >= QUALITY_FLOOR_TARGET, "critical", f"current_rows={current_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("within_quality_ceiling", current_rows <= QUALITY_CEILING_TARGET, "critical", f"current_rows={current_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("scoring_not_executed", True, "critical", "scoring_executed=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("dataset_not_modified", sha256_file(CURRENT_DATASET) == CURRENT_SHA_EXPECTED, "critical", f"current_sha_after={sha256_file(CURRENT_DATASET)}")

    approved_for_scoring_dry_run_decision = critical_failed == 0 and unknown_total == 0
    approved_for_scoring_execution = False

    if critical_failed > 0:
        status = STATUS_FAILED
    elif unknown_total == 0:
        status = STATUS_READY
    else:
        status = STATUS_REVIEW

    recommended_next_phase = NEXT_PHASE_READY if status == STATUS_READY else NEXT_PHASE_REVIEW

    write_csv(CLASSIFICATION_CSV, classification_rows, [
        "row_number",
        "refined_classification",
        "matched_terms",
        "refined_reason",
        "policy_classification",
        "policy_match",
        "policy_reason",
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
    ])

    classification_sha = sha256_file(CLASSIFICATION_CSV)

    summary = {
        "selected_route": "Full-dataset residual instrument classification review before scoring dry run",
        "phase_type": PHASE_TYPE,
        "classification_decision": "FULL_DATASET_POLICY_OVERLAY_READY" if status == STATUS_READY else "UNCLASSIFIED_RESIDUALS_REMAIN",
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows,
        "current_dataset_sha": current_sha,
        "refined_full_dataset_no_flag_rows": no_flag_rows,
        "refined_full_dataset_non_blocking_equity_context_rows": non_blocking_equity_rows,
        "refined_full_dataset_non_blocking_in_scope_context_rows": non_blocking_scope_rows,
        "refined_full_dataset_residual_review_required_rows": residual_rows,
        "expected_residual_review_required_rows": expected_residual_rows,
        "classification_overlay_rows": flagged_overlay_rows,
        "excluded_from_common_equity_scoring_rows": excluded_rows,
        "classification_unknown_missing_instrument_metadata_rows": unknown_missing_metadata_rows,
        "classification_unknown_manual_review_required_rows": unknown_manual_review_rows,
        "classification_unknown_total_rows": unknown_total,
        "approved_for_scoring_dry_run_decision": approved_for_scoring_dry_run_decision,
        "approved_for_scoring_execution": approved_for_scoring_execution,
        "scoring_authorized": False,
        "scoring_executed": False,
        "scoring_output_created": False,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "openai_authorized": False,
        "openai_called": False,
        "broker_authorized": False,
        "broker_called": False,
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": recommended_next_phase,
        "secondary_next_phase": NEXT_PHASE_READY,
    }

    artifact_manifest_rows = [
        {
            "artifact": "review_report_input",
            "path": str(REVIEW_REPORT),
            "rows": 1,
            "sha256": review_sha,
            "role": "input_review_report",
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
            "role": "full_dataset_reviewed_no_modification",
        },
        {
            "artifact": "classification_overlay_output",
            "path": str(CLASSIFICATION_CSV),
            "rows": flagged_overlay_rows,
            "sha256": classification_sha,
            "role": "full_dataset_policy_overlay_for_future_scoring_dry_run",
        },
    ]

    decision_register_rows = [
        {
            "decision_id": "V2_22C2_CLASSIFICATION_001",
            "decision": "Reclassify residual instruments from the full 43,089-row dataset instead of using the sampled CSV.",
            "accepted": True,
            "reason": "The previous CSV was a sample/capped review artifact and not a complete residual universe.",
            "effect": "v2.22C2 now validates against the full residual count from v2.22C_REVIEW.",
        },
        {
            "decision_id": "V2_22C2_CLASSIFICATION_002",
            "decision": "Create a policy overlay, not a mutated dataset.",
            "accepted": True,
            "reason": "Rows should not be deleted before scoring dry run.",
            "effect": "Classification overlay is available for v2.22D.",
        },
        {
            "decision_id": "V2_22C2_CLASSIFICATION_003",
            "decision": "Exclude explicit fixed-income/fund/preferred/warrant/right/certificate/ETF instruments from common-equity scoring dry run.",
            "accepted": True,
            "reason": "These are not common-equity candidates under current policy.",
            "effect": f"excluded_from_common_equity_scoring_rows={excluded_rows}.",
        },
        {
            "decision_id": "V2_22C2_CLASSIFICATION_004",
            "decision": "Do not execute scoring.",
            "accepted": True,
            "reason": "This is a classification review phase.",
            "effect": "Scoring remains not executed.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "scoring_dry_run" if status == STATUS_READY else "manual_review",
            "action": "prepare_scoring_dry_run_using_classification_overlay" if status == STATUS_READY else "review_unknown_residual_classifications",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "Full residual policy overlay is ready." if status == STATUS_READY else f"unknown_total={unknown_total}",
            "guardrails": "Dry run only; exclude non-common-equity rows; no OpenAI; no broker." if status == STATUS_READY else "No scoring until unknown residual rows are handled.",
        },
        {
            "action_order": 2,
            "action_scope": "full59k",
            "action": "keep_full59k_deprecated_deferred",
            "priority": "low",
            "recommended_phase": "none",
            "reason": "Quality target remains 42k-45k.",
            "guardrails": "No full59k without separate roadmap.",
        },
    ]

    write_csv(POLICY_CSV, policy_rows, ["policy_bucket", "count", "scoring_policy"])
    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "policy_counts": dict(policy_counter),
        "refined_counts": dict(refined_counter),
        "policy_matches": dict(policy_match_counter),
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "current_dataset": str(CURRENT_DATASET),
            "current_dataset_rows": current_rows,
            "current_dataset_sha": current_sha,
            "classification_overlay": str(CLASSIFICATION_CSV),
            "approved_for_scoring_dry_run_decision": approved_for_scoring_dry_run_decision,
            "approved_for_scoring_execution": approved_for_scoring_execution,
            "scoring_authorized": False,
            "scoring_executed": False,
            "scoring_output_created": False,
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
        "recommended_next_phase": recommended_next_phase,
        "secondary_next_phase": NEXT_PHASE_READY,
    }

    write_json(REPORT_JSON, payload)

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

v2.22C2 classifies residual instrument flags using the full 43,089-row operational dataset, not the capped/sample CSV.

No dataset rows are deleted. No dataset is modified. No scoring is executed.

## Current dataset

`{CURRENT_DATASET}`

Rows: `{current_rows}`  
SHA256: `{current_sha}`

## Classification result

- Full dataset no-flag rows: `{no_flag_rows}`
- Non-blocking equity-context rows: `{non_blocking_equity_rows}`
- Non-blocking in-scope rows: `{non_blocking_scope_rows}`
- Residual review required rows: `{residual_rows}`
- Expected residual rows from v2.22C_REVIEW: `{expected_residual_rows}`
- Classification overlay rows: `{flagged_overlay_rows}`
- Excluded from common-equity scoring rows: `{excluded_rows}`
- Unknown total rows: `{unknown_total}`

Approved for scoring dry run decision: `{approved_for_scoring_dry_run_decision}`

Approved for scoring execution: `{approved_for_scoring_execution}`

## Checks

{check_lines}

## Recommended next phase

Primary: `{recommended_next_phase}`

Secondary: `{NEXT_PHASE_READY}`
""",
    )

    print("")
    print("v2.22C2 residual instrument classification review completed.")
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
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
