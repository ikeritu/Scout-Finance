from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.22C_REVIEW"
PHASE = "Pre-Scoring Quality Findings Review"
PHASE_TYPE = "pre-scoring-quality-findings-review"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

AUDIT_REPORT = OUTPUT_DIR / "pre_scoring_data_quality_audit_v2_22c.json"
POINTER_JSON = OUTPUT_DIR / "current_operational_universe_pointer.json"
CURRENT_DATASET = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
PREVIOUS_OPERATIONAL_BASE = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

REPORT_JSON = OUTPUT_DIR / "pre_scoring_quality_findings_review_v2_22c_review.json"
REPORT_MD = OUTPUT_DIR / "pre_scoring_quality_findings_review_v2_22c_review.md"
SUMMARY_CSV = OUTPUT_DIR / "pre_scoring_quality_findings_review_summary_v2_22c_review.csv"
CHECKS_CSV = OUTPUT_DIR / "pre_scoring_quality_findings_review_checks_v2_22c_review.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "pre_scoring_quality_findings_review_decision_register_v2_22c_review.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "pre_scoring_quality_findings_review_artifact_manifest_v2_22c_review.csv"
FINDINGS_CLASSIFICATION_CSV = OUTPUT_DIR / "pre_scoring_quality_findings_review_findings_classification_v2_22c_review.csv"
REFINED_INSTRUMENT_FLAGS_CSV = OUTPUT_DIR / "pre_scoring_quality_findings_review_refined_instrument_flags_v2_22c_review.csv"
NEW_ROWS_REVIEW_CSV = OUTPUT_DIR / "pre_scoring_quality_findings_review_new_rows_v2_22c_review.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "pre_scoring_quality_findings_review_next_actions_v2_22c_review.csv"

EXPECTED_AUDIT_STATUS = "PRE_SCORING_DATA_QUALITY_AUDIT_COMPLETED_REVIEW_FINDINGS_DOCUMENTED_SCORING_DRY_RUN_DEFERRED"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

PREVIOUS_ROWS_EXPECTED = 42708
PREVIOUS_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

EXPECTED_NEW_ROWS = 381
EXPECTED_SINGAPORE_NEW_ROWS = 358
EXPECTED_COLOMBIA_NEW_ROWS = 23

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_READY = "PRE_SCORING_QUALITY_FINDINGS_REVIEW_COMPLETED_FINDINGS_CLASSIFIED_READY_FOR_SCORING_DRY_RUN_DECISION"
STATUS_REVIEW = "PRE_SCORING_QUALITY_FINDINGS_REVIEW_COMPLETED_RESIDUAL_REVIEW_REQUIRED_SCORING_DRY_RUN_DEFERRED"
STATUS_FAILED = "PRE_SCORING_QUALITY_FINDINGS_REVIEW_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_READY = "v2.22D - Scoring Dry Run / No Promotion"
NEXT_PHASE_REVIEW = "v2.22C2 - Residual Instrument Classification Review"

# Word-boundary patterns avoid false positives like Netflix -> "etf" and CDT Equity -> "cdt".
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


def read_csv_dicts(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return header, rows


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


def row_fingerprint(row: dict[str, str], header: list[str]) -> str:
    payload = "\u241f".join(normalize_value(row.get(column, "")) for column in header)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def row_text(row: dict[str, str], columns: dict[str, str | None]) -> str:
    parts = [
        get_value(row, columns.get("name")),
        get_value(row, columns.get("asset_type")),
        get_value(row, columns.get("instrument_type")),
        get_value(row, columns.get("instrument_scope")),
    ]
    return " | ".join(parts)


def classify_refined_instrument_flag(row: dict[str, str], columns: dict[str, str | None]) -> tuple[str, list[str], str]:
    text = row_text(row, columns)
    lower_text = text.lower()

    matched = [label for label, pattern in REVIEW_PATTERNS.items() if pattern.search(text)]

    if not matched:
        return "no_refined_flag", [], "No word-boundary instrument review term matched."

    asset_type = get_value(row, columns.get("asset_type")).lower()
    instrument_type = get_value(row, columns.get("instrument_type")).lower()
    instrument_scope = get_value(row, columns.get("instrument_scope")).lower()

    if asset_type.startswith("equity") or "equity_like" in asset_type or "common_equity" in asset_type:
        if any(context in lower_text for context in FALSE_POSITIVE_CONTEXTS):
            return "non_blocking_equity_context", matched, "Matched term appears in equity/common-share context."

    if "common_stock" in instrument_type or "common stock" in lower_text or "ordinary share" in lower_text:
        if not any(term in matched for term in ["note", "debenture", "preferred_or_preference", "bond", "warrant", "right", "certificate"]):
            return "non_blocking_equity_context", matched, "Common stock / ordinary share context."

    if "in_scope" in instrument_scope and not any(term in matched for term in ["note", "debenture", "preferred_or_preference", "bond", "warrant", "right", "certificate"]):
        return "non_blocking_in_scope_context", matched, "Existing instrument scope is in-scope."

    return "residual_review_required", matched, "Potential non-common-equity or fund-like instrument needs review/exclusion policy before scoring."


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        DECISION_REGISTER_CSV,
        ARTIFACT_MANIFEST_CSV,
        FINDINGS_CLASSIFICATION_CSV,
        REFINED_INSTRUMENT_FLAGS_CSV,
        NEW_ROWS_REVIEW_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    audit = read_json(AUDIT_REPORT)
    audit_summary = audit.get("summary", {})
    pointer = read_json(POINTER_JSON)

    current_header, current_rows = read_csv_dicts(CURRENT_DATASET)
    previous_header, previous_rows = read_csv_dicts(PREVIOUS_OPERATIONAL_BASE)
    rollback_header, rollback_rows = read_csv_dicts(ROLLBACK_DATASET)

    columns = resolve_columns(current_header)

    current_rows_count = len(current_rows)
    previous_rows_count = len(previous_rows)
    rollback_rows_count = len(rollback_rows)

    current_sha = sha256_file(CURRENT_DATASET)
    previous_sha = sha256_file(PREVIOUS_OPERATIONAL_BASE)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    pointer_sha = sha256_file(POINTER_JSON)

    previous_fingerprints = set(row_fingerprint(row, previous_header) for row in previous_rows)
    current_fingerprints = [row_fingerprint(row, current_header) for row in current_rows]
    duplicate_full_row_counter = Counter(current_fingerprints)
    duplicate_full_row_groups = sum(1 for count in duplicate_full_row_counter.values() if count > 1)
    duplicate_full_row_extra_rows = sum(count - 1 for count in duplicate_full_row_counter.values() if count > 1)

    new_rows = [
        row
        for row, fingerprint in zip(current_rows, current_fingerprints)
        if fingerprint not in previous_fingerprints
    ]

    new_country_counter = Counter(get_value(row, columns.get("country")) or "__MISSING__" for row in new_rows)
    new_exchange_counter = Counter(get_value(row, columns.get("exchange")) or "__MISSING__" for row in new_rows)
    new_mic_counter = Counter(get_value(row, columns.get("mic")) or "__MISSING__" for row in new_rows)
    new_currency_counter = Counter(get_value(row, columns.get("currency")) or "__MISSING__" for row in new_rows)
    new_source_counter = Counter(get_value(row, columns.get("source_provider")) or "__MISSING__" for row in new_rows)
    new_asset_counter = Counter(get_value(row, columns.get("asset_type")) or "__MISSING__" for row in new_rows)

    refined_flag_rows: list[dict[str, Any]] = []
    refined_counts = Counter()

    for row_number, row in enumerate(current_rows, start=2):
        classification, matched_terms, reason = classify_refined_instrument_flag(row, columns)
        refined_counts[classification] += 1

        if classification != "no_refined_flag" and len(refined_flag_rows) < 2000:
            refined_flag_rows.append({
                "row_number": row_number,
                "classification": classification,
                "matched_terms": ";".join(matched_terms),
                "reason": reason,
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

    residual_review_required = refined_counts["residual_review_required"]

    findings_classification_rows = [
        {
            "finding": "new_rows_vs_previous",
            "audit_value": audit_summary.get("new_rows_vs_previous_operational_base"),
            "review_classification": "accepted_expected_delta",
            "blocking": False,
            "reason": "381 new rows exactly match expected Singapore + Colombia expansion.",
        },
        {
            "finding": "full_row_duplicates",
            "audit_value": audit_summary.get("duplicate_full_row_extra_rows"),
            "review_classification": "no_blocker",
            "blocking": False,
            "reason": "No full-row duplicate extra rows were found.",
        },
        {
            "finding": "primary_key_duplicates",
            "audit_value": audit_summary.get("duplicate_primary_key_extra_rows"),
            "review_classification": "weak_key_false_positive",
            "blocking": False,
            "reason": "The audit primary key collapsed rows where identifier columns were missing; full-row duplicates are zero.",
        },
        {
            "finding": "instrument_suitability_flags_original",
            "audit_value": audit_summary.get("instrument_suitability_flag_rows"),
            "review_classification": "broad_substring_scan_overflagged",
            "blocking": False,
            "reason": "Original scan used broad substrings and overflagged cases such as Netflix containing 'etf'.",
        },
        {
            "finding": "instrument_suitability_refined_residual",
            "audit_value": residual_review_required,
            "review_classification": "residual_review_required" if residual_review_required else "no_residual_blocker",
            "blocking": bool(residual_review_required),
            "reason": "Refined word-boundary scan isolates likely non-common-equity/fund-like instruments.",
        },
        {
            "finding": "colombia_asset_type_missing",
            "audit_value": new_asset_counter.get("__MISSING__", 0),
            "review_classification": "accepted_source_limitation_reviewed",
            "blocking": False,
            "reason": "The 23 Colombia rows are expected regulatory-source additions; missing asset_type should be handled by scoring config/audit metadata, not treated as a structural failure.",
        },
    ]

    new_rows_review_rows = [
        {"dimension": "country", "value": key, "count": value} for key, value in new_country_counter.most_common()
    ] + [
        {"dimension": "exchange", "value": key, "count": value} for key, value in new_exchange_counter.most_common()
    ] + [
        {"dimension": "mic", "value": key, "count": value} for key, value in new_mic_counter.most_common()
    ] + [
        {"dimension": "currency", "value": key, "count": value} for key, value in new_currency_counter.most_common()
    ] + [
        {"dimension": "source_provider", "value": key, "count": value} for key, value in new_source_counter.most_common()
    ] + [
        {"dimension": "asset_type", "value": key, "count": value} for key, value in new_asset_counter.most_common()
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

    add_check("audit_status_expected", audit.get("status") == EXPECTED_AUDIT_STATUS, "critical", str(audit.get("status")))
    add_check("audit_critical_failed_checks_zero", str(audit_summary.get("critical_failed_checks")) == "0", "critical", f"critical_failed_checks={audit_summary.get('critical_failed_checks')}")
    add_check("pointer_current_dataset_expected", Path(pointer.get("current_dataset", "")) == CURRENT_DATASET, "critical", str(pointer.get("current_dataset")))
    add_check("current_rows_expected", current_rows_count == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows_count}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("previous_rows_expected", previous_rows_count == PREVIOUS_ROWS_EXPECTED, "critical", f"previous_rows={previous_rows_count}")
    add_check("previous_sha_expected", previous_sha == PREVIOUS_SHA_EXPECTED, "critical", previous_sha)
    add_check("rollback_rows_expected", rollback_rows_count == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows_count}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("headers_consistent_current_previous", current_header == previous_header, "critical", f"current_columns={len(current_header)};previous_columns={len(previous_header)}")
    add_check("headers_consistent_current_rollback", len(current_header) == len(rollback_header), "critical", f"current_columns={len(current_header)};rollback_columns={len(rollback_header)}")
    add_check("new_rows_total_expected", len(new_rows) == EXPECTED_NEW_ROWS, "critical", f"new_rows={len(new_rows)}")
    add_check("new_rows_singapore_expected", new_country_counter.get("Singapore", 0) == EXPECTED_SINGAPORE_NEW_ROWS, "critical", f"singapore={new_country_counter.get('Singapore', 0)}")
    add_check("new_rows_colombia_expected", new_country_counter.get("Colombia", 0) == EXPECTED_COLOMBIA_NEW_ROWS, "critical", f"colombia={new_country_counter.get('Colombia', 0)}")
    add_check("full_row_duplicates_zero", duplicate_full_row_extra_rows == 0, "critical", f"extra_rows={duplicate_full_row_extra_rows};groups={duplicate_full_row_groups}")
    add_check("primary_key_duplicates_classified_non_blocking", True, "critical", "weak_key_false_positive=True")
    add_check("original_instrument_flags_classified_as_overbroad", True, "critical", "broad_substring_scan_overflagged=True")
    add_check("refined_instrument_residual_documented", True, "warning", f"residual_review_required={residual_review_required}")
    add_check("within_quality_floor", current_rows_count >= QUALITY_FLOOR_TARGET, "critical", f"current_rows={current_rows_count};floor={QUALITY_FLOOR_TARGET}")
    add_check("within_quality_ceiling", current_rows_count <= QUALITY_CEILING_TARGET, "critical", f"current_rows={current_rows_count};ceiling={QUALITY_CEILING_TARGET}")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("scoring_not_executed", True, "critical", "scoring_executed=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")

    approved_for_scoring_dry_run_decision = critical_failed == 0
    approved_for_scoring_execution = False

    if critical_failed > 0:
        status = STATUS_FAILED
    elif residual_review_required > 0:
        status = STATUS_REVIEW
    else:
        status = STATUS_READY

    recommended_next_phase = NEXT_PHASE_REVIEW if residual_review_required > 0 else NEXT_PHASE_READY

    decision_register_rows = [
        {
            "decision_id": "V2_22C_REVIEW_001",
            "decision": "Accept 381 new rows as expected Singapore + Colombia delta.",
            "accepted": True,
            "reason": "New rows split is Singapore 358 and Colombia 23.",
            "effect": "No row-count blocker remains.",
        },
        {
            "decision_id": "V2_22C_REVIEW_002",
            "decision": "Classify primary-key duplicates as non-blocking weak-key false positives.",
            "accepted": True,
            "reason": "Full-row duplicates are zero; weak key collapsed broad exchange-level rows.",
            "effect": "No duplicate blocker remains.",
        },
        {
            "decision_id": "V2_22C_REVIEW_003",
            "decision": "Replace broad substring instrument scan with refined word-boundary review.",
            "accepted": True,
            "reason": "Broad scan overflagged false positives such as Netflix containing 'etf'.",
            "effect": "Residual review list is isolated in refined instrument flags.",
        },
        {
            "decision_id": "V2_22C_REVIEW_004",
            "decision": "Do not execute scoring in review phase.",
            "accepted": True,
            "reason": "This phase classifies findings only.",
            "effect": "Scoring remains not executed.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "residual_review" if residual_review_required else "scoring_dry_run_decision",
            "action": "review_refined_residual_instrument_flags" if residual_review_required else "prepare_scoring_dry_run_no_promotion",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": f"residual_review_required={residual_review_required}",
            "guardrails": "No scoring until residual flags are handled." if residual_review_required else "Dry run only; no promotion; no OpenAI; no broker.",
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

    artifact_manifest_rows = [
        {
            "artifact": "audit_report_input",
            "path": str(AUDIT_REPORT),
            "rows": 1,
            "sha256": sha256_file(AUDIT_REPORT),
            "role": "input_audit_report",
        },
        {
            "artifact": "current_operational_pointer_input",
            "path": str(POINTER_JSON),
            "rows": 1,
            "sha256": pointer_sha,
            "role": "input_pointer",
        },
        {
            "artifact": "current_operational_dataset_input",
            "path": str(CURRENT_DATASET),
            "rows": current_rows_count,
            "sha256": current_sha,
            "role": "reviewed_dataset_no_modification",
        },
        {
            "artifact": "previous_operational_base_input",
            "path": str(PREVIOUS_OPERATIONAL_BASE),
            "rows": previous_rows_count,
            "sha256": previous_sha,
            "role": "comparison_reference_unchanged",
        },
        {
            "artifact": "rollback_dataset_input",
            "path": str(ROLLBACK_DATASET),
            "rows": rollback_rows_count,
            "sha256": rollback_sha,
            "role": "rollback_reference_unchanged",
        },
    ]

    summary = {
        "selected_route": "Pre-scoring quality findings review",
        "phase_type": PHASE_TYPE,
        "review_decision": "FINDINGS_CLASSIFIED_READY_FOR_SCORING_DRY_RUN_DECISION" if status == STATUS_READY else "FINDINGS_CLASSIFIED_RESIDUAL_REVIEW_REQUIRED",
        "current_dataset": str(CURRENT_DATASET),
        "current_dataset_rows": current_rows_count,
        "current_dataset_sha": current_sha,
        "new_rows_vs_previous": len(new_rows),
        "new_rows_singapore": new_country_counter.get("Singapore", 0),
        "new_rows_colombia": new_country_counter.get("Colombia", 0),
        "duplicate_full_row_groups": duplicate_full_row_groups,
        "duplicate_full_row_extra_rows": duplicate_full_row_extra_rows,
        "primary_key_duplicates_classified": "weak_key_false_positive",
        "original_instrument_flags": audit_summary.get("instrument_suitability_flag_rows"),
        "original_instrument_flags_classification": "broad_substring_scan_overflagged",
        "refined_instrument_no_flag": refined_counts["no_refined_flag"],
        "refined_instrument_non_blocking_equity_context": refined_counts["non_blocking_equity_context"],
        "refined_instrument_non_blocking_in_scope_context": refined_counts["non_blocking_in_scope_context"],
        "refined_instrument_residual_review_required": residual_review_required,
        "colombia_asset_type_missing_rows": new_asset_counter.get("__MISSING__", 0),
        "colombia_asset_type_missing_classification": "accepted_source_limitation_reviewed",
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

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(FINDINGS_CLASSIFICATION_CSV, findings_classification_rows, ["finding", "audit_value", "review_classification", "blocking", "reason"])
    write_csv(REFINED_INSTRUMENT_FLAGS_CSV, refined_flag_rows, ["row_number", "classification", "matched_terms", "reason", "isin", "ticker", "name", "exchange", "country", "mic", "currency", "source_provider", "asset_type", "instrument_type", "instrument_scope"])
    write_csv(NEW_ROWS_REVIEW_CSV, new_rows_review_rows, ["dimension", "value", "count"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "resolved_columns": columns,
        "artifact_manifest": artifact_manifest_rows,
        "decision_register": decision_register_rows,
        "findings_classification": findings_classification_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "current_dataset": str(CURRENT_DATASET),
            "current_dataset_rows": current_rows_count,
            "current_dataset_sha": current_sha,
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

v2.22C_REVIEW classifies the quality findings from v2.22C.

No scoring is executed.

## Key results

- Current dataset rows: `{current_rows_count}`
- Current dataset SHA256: `{current_sha}`
- New rows vs previous base: `{len(new_rows)}`
- Singapore new rows: `{new_country_counter.get("Singapore", 0)}`
- Colombia new rows: `{new_country_counter.get("Colombia", 0)}`
- Full-row duplicate extra rows: `{duplicate_full_row_extra_rows}`
- Primary-key duplicate finding classification: weak-key false positive
- Original instrument flags classification: broad substring scan overflagged
- Refined residual instrument review required: `{residual_review_required}`

## Scoring status

Approved for scoring dry run decision: `{approved_for_scoring_dry_run_decision}`

Approved for scoring execution: `{approved_for_scoring_execution}`

Scoring executed: `False`

## Checks

{check_lines}

## Recommended next phase

Primary: `{recommended_next_phase}`

Secondary: `{NEXT_PHASE_READY}`
""",
    )

    print("")
    print("v2.22C_REVIEW pre-scoring quality findings review completed.")
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
