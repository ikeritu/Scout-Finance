from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.22C"
PHASE = "Pre-Scoring Data Quality Audit"
PHASE_TYPE = "pre-scoring-data-quality-audit"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

POINTER_JSON = OUTPUT_DIR / "current_operational_universe_pointer.json"
POINTER_HARDENING_REPORT = OUTPUT_DIR / "operational_pointer_convention_hardening_v2_22b.json"

CURRENT_DATASET_EXPECTED = OUTPUT_DIR / "expanded_universe_v2_21h_activated_operational_reference.csv"
PREVIOUS_OPERATIONAL_BASE = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

REPORT_JSON = OUTPUT_DIR / "pre_scoring_data_quality_audit_v2_22c.json"
REPORT_MD = OUTPUT_DIR / "pre_scoring_data_quality_audit_v2_22c.md"
SUMMARY_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_summary_v2_22c.csv"
CHECKS_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_checks_v2_22c.csv"
ARTIFACT_MANIFEST_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_artifact_manifest_v2_22c.csv"
COLUMN_PROFILE_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_column_profile_v2_22c.csv"
IDENTIFIER_COVERAGE_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_identifier_coverage_v2_22c.csv"
VALUE_COVERAGE_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_value_coverage_v2_22c.csv"
DUPLICATE_FINDINGS_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_duplicate_findings_v2_22c.csv"
NEW_ROWS_PROFILE_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_new_rows_profile_v2_22c.csv"
INSTRUMENT_FLAGS_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_instrument_suitability_flags_v2_22c.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_decision_register_v2_22c.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "pre_scoring_data_quality_audit_next_actions_v2_22c.csv"

EXPECTED_POINTER_HARDENING_STATUS = "OPERATIONAL_POINTER_CONVENTION_HARDENING_COMPLETED_CURRENT_OPERATIONAL_POINTER_CREATED_SCORING_DEFERRED"

CURRENT_ROWS_EXPECTED = 43089
CURRENT_SHA_EXPECTED = "9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707"

PREVIOUS_OPERATIONAL_ROWS_EXPECTED = 42708
PREVIOUS_OPERATIONAL_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
EXPECTED_NEW_ROWS_VS_PREVIOUS = 381

STATUS_COMPLETED_CLEAN = "PRE_SCORING_DATA_QUALITY_AUDIT_COMPLETED_NO_BLOCKING_FINDINGS_READY_FOR_SCORING_DRY_RUN_DECISION"
STATUS_COMPLETED_REVIEW = "PRE_SCORING_DATA_QUALITY_AUDIT_COMPLETED_REVIEW_FINDINGS_DOCUMENTED_SCORING_DRY_RUN_DEFERRED"
STATUS_FAILED = "PRE_SCORING_DATA_QUALITY_AUDIT_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_IF_CLEAN = "v2.22D - Scoring Dry Run / No Promotion"
NEXT_PHASE_IF_REVIEW = "v2.22C_REVIEW - Pre-Scoring Quality Findings Review"
SECONDARY_NEXT_PHASE = "v2.22D - Scoring Dry Run / No Promotion"

TOP_VALUE_LIMIT = 200
FINDING_SAMPLE_LIMIT = 1000

INSTRUMENT_REVIEW_TERMS = [
    "bond",
    "bonds",
    "bono",
    "bonos",
    "note",
    "notes",
    "debenture",
    "debentures",
    "cdt",
    "certificate",
    "certificado",
    "commercial paper",
    "papeles comerciales",
    "fondo",
    "fund",
    "etf",
    "warrant",
    "warrants",
    "right",
    "rights",
    "preference share",
    "preferred share",
    "preferred",
    "preferencial",
    "titularizacion",
    "titularización",
    "derivative",
    "derivado",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def normalize_key(value: Any) -> str:
    return normalize_value(value).lower()


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(content, encoding="utf-8", newline="\n")


def read_csv_dicts(path: Path) -> tuple[list[str], list[dict[str, str]], int]:
    bad_width_rows = 0
    rows: list[dict[str, str]] = []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return [], [], 0

        expected_width = len(header)

        for line_number, values in enumerate(reader, start=2):
            if len(values) != expected_width:
                bad_width_rows += 1

            padded = values[:expected_width] + [""] * max(0, expected_width - len(values))
            rows.append({header[index]: padded[index] for index in range(expected_width)})

    return header, rows, bad_width_rows


def row_fingerprint(row: dict[str, str], header: list[str]) -> str:
    payload = "\u241f".join(normalize_value(row.get(column, "")) for column in header)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
        "symbol": find_column(header, ["symbol", "ticker", "ticker_symbol", "local_symbol"]),
        "name": find_column(header, ["name", "company_name", "security_name", "instrument_name", "issuer_name"]),
        "country": find_column(header, ["country", "country_name", "domicile_country"]),
        "exchange": find_column(header, ["exchange", "exchange_name", "market", "market_name"]),
        "mic": find_column(header, ["mic", "operating_mic", "exchange_mic"]),
        "currency": find_column(header, ["currency", "currency_code", "trading_currency"]),
        "source_provider": find_column(header, ["source_provider", "provider", "source", "data_source"]),
        "asset_type": find_column(header, ["asset_type", "instrument_type", "security_type", "type", "category"]),
    }


def get_value(row: dict[str, str], column: str | None) -> str:
    if not column:
        return ""
    return normalize_value(row.get(column, ""))


def primary_key(row: dict[str, str], columns: dict[str, str | None]) -> str:
    parts = [
        get_value(row, columns.get("isin")),
        get_value(row, columns.get("symbol")),
        get_value(row, columns.get("mic")) or get_value(row, columns.get("exchange")),
        get_value(row, columns.get("currency")),
    ]
    compact = [normalize_key(part) for part in parts if normalize_key(part)]
    return "|".join(compact)


def all_text(row: dict[str, str], header: list[str]) -> str:
    return " | ".join(normalize_value(row.get(column, "")) for column in header).lower()


def safe_pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 4)


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ARTIFACT_MANIFEST_CSV,
        COLUMN_PROFILE_CSV,
        IDENTIFIER_COVERAGE_CSV,
        VALUE_COVERAGE_CSV,
        DUPLICATE_FINDINGS_CSV,
        NEW_ROWS_PROFILE_CSV,
        INSTRUMENT_FLAGS_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    pointer = read_json(POINTER_JSON)
    pointer_hardening = read_json(POINTER_HARDENING_REPORT)

    current_dataset = Path(pointer.get("current_dataset", ""))
    current_dataset_rows_declared = pointer.get("current_dataset_rows")
    current_dataset_sha_declared = pointer.get("current_dataset_sha256")

    current_header, current_rows, current_bad_width_rows = read_csv_dicts(current_dataset)
    previous_header, previous_rows, previous_bad_width_rows = read_csv_dicts(PREVIOUS_OPERATIONAL_BASE)
    rollback_header, rollback_rows_data, rollback_bad_width_rows = read_csv_dicts(ROLLBACK_DATASET)

    current_rows_count = len(current_rows)
    previous_rows_count = len(previous_rows)
    rollback_rows_count = len(rollback_rows_data)

    current_sha = sha256_file(current_dataset)
    previous_sha = sha256_file(PREVIOUS_OPERATIONAL_BASE)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    pointer_sha = sha256_file(POINTER_JSON)

    columns = resolve_columns(current_header)

    current_fingerprints = [row_fingerprint(row, current_header) for row in current_rows]
    previous_fingerprints = set(row_fingerprint(row, previous_header) for row in previous_rows)

    current_fp_counter = Counter(current_fingerprints)
    duplicate_full_row_groups = {fingerprint: count for fingerprint, count in current_fp_counter.items() if count > 1}
    duplicate_full_row_extra_rows = sum(count - 1 for count in duplicate_full_row_groups.values())

    primary_key_values = [primary_key(row, columns) for row in current_rows]
    populated_primary_keys = [key for key in primary_key_values if key]
    primary_key_counter = Counter(populated_primary_keys)
    duplicate_primary_key_groups = {key: count for key, count in primary_key_counter.items() if count > 1}
    duplicate_primary_key_extra_rows = sum(count - 1 for count in duplicate_primary_key_groups.values())

    new_row_indexes = [
        index
        for index, fingerprint in enumerate(current_fingerprints)
        if fingerprint not in previous_fingerprints
    ]
    new_rows = [current_rows[index] for index in new_row_indexes]
    new_rows_count = len(new_rows)

    column_profile_rows: list[dict[str, Any]] = []
    for column in current_header:
        values = [normalize_value(row.get(column, "")) for row in current_rows]
        missing = sum(1 for value in values if value == "")
        non_missing = current_rows_count - missing
        unique_non_empty = len(set(value for value in values if value))
        examples = "; ".join(list(dict.fromkeys(value for value in values if value))[:5])
        column_profile_rows.append({
            "column": column,
            "non_missing": non_missing,
            "missing": missing,
            "missing_pct": safe_pct(missing, current_rows_count),
            "unique_non_empty": unique_non_empty,
            "sample_values": examples,
        })

    identifier_coverage_rows: list[dict[str, Any]] = []
    for role, column in columns.items():
        if column:
            non_empty = sum(1 for row in current_rows if get_value(row, column))
            missing = current_rows_count - non_empty
            unique_non_empty = len(set(get_value(row, column) for row in current_rows if get_value(row, column)))
        else:
            non_empty = 0
            missing = current_rows_count
            unique_non_empty = 0

        identifier_coverage_rows.append({
            "role": role,
            "column": column or "",
            "column_resolved": bool(column),
            "non_empty": non_empty,
            "missing": missing,
            "missing_pct": safe_pct(missing, current_rows_count),
            "unique_non_empty": unique_non_empty,
        })

    value_coverage_rows: list[dict[str, Any]] = []
    for role in ["country", "exchange", "mic", "currency", "source_provider", "asset_type"]:
        column = columns.get(role)
        if not column:
            value_coverage_rows.append({
                "scope": "current_dataset",
                "dimension": role,
                "column": "",
                "value": "__COLUMN_NOT_RESOLVED__",
                "count": current_rows_count,
                "pct": 100.0,
            })
            continue

        counter = Counter(get_value(row, column) or "__MISSING__" for row in current_rows)
        for value, count in counter.most_common(TOP_VALUE_LIMIT):
            value_coverage_rows.append({
                "scope": "current_dataset",
                "dimension": role,
                "column": column,
                "value": value,
                "count": count,
                "pct": safe_pct(count, current_rows_count),
            })

    duplicate_finding_rows: list[dict[str, Any]] = []
    for fingerprint, count in list(duplicate_full_row_groups.items())[:FINDING_SAMPLE_LIMIT]:
        duplicate_finding_rows.append({
            "finding_type": "full_row_duplicate",
            "key": fingerprint,
            "count": count,
            "extra_rows": count - 1,
            "severity": "review",
        })

    for key, count in list(duplicate_primary_key_groups.items())[:FINDING_SAMPLE_LIMIT]:
        duplicate_finding_rows.append({
            "finding_type": "primary_key_duplicate",
            "key": key,
            "count": count,
            "extra_rows": count - 1,
            "severity": "review",
        })

    new_rows_profile_rows: list[dict[str, Any]] = [
        {
            "scope": "new_rows_vs_previous_operational_base",
            "dimension": "__total__",
            "column": "",
            "value": "__total_new_rows__",
            "count": new_rows_count,
            "pct": 100.0 if new_rows_count else 0.0,
        }
    ]

    for role in ["country", "exchange", "mic", "currency", "source_provider", "asset_type"]:
        column = columns.get(role)
        if not column:
            new_rows_profile_rows.append({
                "scope": "new_rows_vs_previous_operational_base",
                "dimension": role,
                "column": "",
                "value": "__COLUMN_NOT_RESOLVED__",
                "count": new_rows_count,
                "pct": 100.0 if new_rows_count else 0.0,
            })
            continue

        counter = Counter(get_value(row, column) or "__MISSING__" for row in new_rows)
        for value, count in counter.most_common(TOP_VALUE_LIMIT):
            new_rows_profile_rows.append({
                "scope": "new_rows_vs_previous_operational_base",
                "dimension": role,
                "column": column,
                "value": value,
                "count": count,
                "pct": safe_pct(count, new_rows_count),
            })

    instrument_flag_rows: list[dict[str, Any]] = []
    instrument_flag_total = 0

    for row_index, row in enumerate(current_rows, start=2):
        text = all_text(row, current_header)
        matched_terms = sorted({term for term in INSTRUMENT_REVIEW_TERMS if term in text})
        if not matched_terms:
            continue

        instrument_flag_total += 1

        if len(instrument_flag_rows) < FINDING_SAMPLE_LIMIT:
            instrument_flag_rows.append({
                "row_number": row_index,
                "matched_terms": ";".join(matched_terms),
                "isin": get_value(row, columns.get("isin")),
                "symbol": get_value(row, columns.get("symbol")),
                "name": get_value(row, columns.get("name")),
                "country": get_value(row, columns.get("country")),
                "exchange": get_value(row, columns.get("exchange")),
                "mic": get_value(row, columns.get("mic")),
                "currency": get_value(row, columns.get("currency")),
                "source_provider": get_value(row, columns.get("source_provider")),
                "severity": "review",
            })

    blocking_quality_findings = 0
    blocking_quality_findings += 1 if duplicate_full_row_extra_rows > 0 else 0
    blocking_quality_findings += 1 if new_rows_count != EXPECTED_NEW_ROWS_VS_PREVIOUS else 0
    blocking_quality_findings += 1 if instrument_flag_total > 0 else 0

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

    add_check("pointer_hardening_status_expected", pointer_hardening.get("status") == EXPECTED_POINTER_HARDENING_STATUS, "critical", str(pointer_hardening.get("status")))
    add_check("pointer_json_exists", POINTER_JSON.exists(), "critical", str(POINTER_JSON))
    add_check("pointer_current_dataset_path_expected", current_dataset == CURRENT_DATASET_EXPECTED, "critical", str(current_dataset))
    add_check("pointer_declared_rows_expected", int(current_dataset_rows_declared) == CURRENT_ROWS_EXPECTED, "critical", f"pointer_rows={current_dataset_rows_declared}")
    add_check("pointer_declared_sha_expected", current_dataset_sha_declared == CURRENT_SHA_EXPECTED, "critical", str(current_dataset_sha_declared))
    add_check("current_dataset_exists", current_dataset.exists(), "critical", str(current_dataset))
    add_check("current_rows_expected", current_rows_count == CURRENT_ROWS_EXPECTED, "critical", f"current_rows={current_rows_count}")
    add_check("current_sha_expected", current_sha == CURRENT_SHA_EXPECTED, "critical", current_sha)
    add_check("previous_operational_rows_expected", previous_rows_count == PREVIOUS_OPERATIONAL_ROWS_EXPECTED, "critical", f"previous_rows={previous_rows_count}")
    add_check("previous_operational_sha_expected", previous_sha == PREVIOUS_OPERATIONAL_SHA_EXPECTED, "critical", previous_sha)
    add_check("rollback_rows_expected", rollback_rows_count == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows_count}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("headers_consistent_current_previous", current_header == previous_header, "critical", f"current_columns={len(current_header)};previous_columns={len(previous_header)}")
    add_check("headers_consistent_current_rollback", len(current_header) == len(rollback_header), "critical", f"current_columns={len(current_header)};rollback_columns={len(rollback_header)}")
    add_check("current_bad_width_rows_zero", current_bad_width_rows == 0, "critical", f"bad_width_rows={current_bad_width_rows}")
    add_check("previous_bad_width_rows_zero", previous_bad_width_rows == 0, "critical", f"bad_width_rows={previous_bad_width_rows}")
    add_check("rollback_bad_width_rows_zero", rollback_bad_width_rows == 0, "critical", f"bad_width_rows={rollback_bad_width_rows}")
    add_check("within_quality_floor", current_rows_count >= QUALITY_FLOOR_TARGET, "critical", f"current_rows={current_rows_count};floor={QUALITY_FLOOR_TARGET}")
    add_check("within_quality_ceiling", current_rows_count <= QUALITY_CEILING_TARGET, "critical", f"current_rows={current_rows_count};ceiling={QUALITY_CEILING_TARGET}")
    add_check("remaining_capacity_non_negative", QUALITY_CEILING_TARGET - current_rows_count >= 0, "critical", f"remaining_capacity={QUALITY_CEILING_TARGET - current_rows_count}")
    add_check("new_rows_vs_previous_expected", new_rows_count == EXPECTED_NEW_ROWS_VS_PREVIOUS, "warning", f"new_rows={new_rows_count};expected={EXPECTED_NEW_ROWS_VS_PREVIOUS}")
    add_check("full_row_duplicates_zero", duplicate_full_row_extra_rows == 0, "warning", f"duplicate_full_row_extra_rows={duplicate_full_row_extra_rows};groups={len(duplicate_full_row_groups)}")
    add_check("primary_key_duplicates_documented", True, "warning", f"duplicate_primary_key_extra_rows={duplicate_primary_key_extra_rows};groups={len(duplicate_primary_key_groups)}")
    add_check("instrument_suitability_flags_documented", True, "warning", f"instrument_flag_total={instrument_flag_total};sample_rows={len(instrument_flag_rows)}")
    add_check("identifier_columns_resolved", any(columns.values()), "critical", f"resolved_columns={columns}")
    add_check("country_or_exchange_dimension_resolved", bool(columns.get("country") or columns.get("exchange") or columns.get("mic")), "critical", f"country={columns.get('country')};exchange={columns.get('exchange')};mic={columns.get('mic')}")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("scoring_not_executed", True, "critical", "scoring_executed=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")

    approved_for_scoring_dry_run = critical_failed == 0 and blocking_quality_findings == 0

    if critical_failed > 0:
        status = STATUS_FAILED
    elif approved_for_scoring_dry_run:
        status = STATUS_COMPLETED_CLEAN
    else:
        status = STATUS_COMPLETED_REVIEW

    recommended_next_phase = NEXT_PHASE_IF_CLEAN if approved_for_scoring_dry_run else NEXT_PHASE_IF_REVIEW

    decision_register_rows = [
        {
            "decision_id": "V2_22C_AUDIT_001",
            "decision": "Use current operational universe pointer as audit source.",
            "accepted": True,
            "reason": "v2.22B created the single live operational pointer.",
            "effect": "Audit reads current_operational_universe_pointer.json.",
        },
        {
            "decision_id": "V2_22C_AUDIT_002",
            "decision": "Do not run scoring in v2.22C.",
            "accepted": True,
            "reason": "v2.22C is a data quality audit phase.",
            "effect": "No scoring output is created.",
        },
        {
            "decision_id": "V2_22C_AUDIT_003",
            "decision": "Document duplicates, identifier coverage, value coverage, new rows, and instrument suitability flags.",
            "accepted": True,
            "reason": "Pre-scoring requires auditable quality evidence.",
            "effect": "Creates quality audit CSVs and JSON/MD report.",
        },
        {
            "decision_id": "V2_22C_AUDIT_004",
            "decision": "Approve scoring dry run only if no critical failures and no blocking quality findings.",
            "accepted": True,
            "reason": "Scoring should not run over unresolved blocking findings.",
            "effect": f"approved_for_scoring_dry_run={approved_for_scoring_dry_run}.",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "quality_review" if not approved_for_scoring_dry_run else "scoring_dry_run",
            "action": "review_pre_scoring_quality_findings" if not approved_for_scoring_dry_run else "prepare_scoring_dry_run_no_promotion",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "Blocking or review findings exist." if not approved_for_scoring_dry_run else "Audit is clean enough for scoring dry run decision.",
            "guardrails": "No scoring in review phase." if not approved_for_scoring_dry_run else "Dry run only; no promotion; no OpenAI; no broker.",
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
            "artifact": "current_operational_pointer",
            "path": str(POINTER_JSON),
            "rows": 1,
            "sha256": pointer_sha,
            "role": "audit_input_pointer",
        },
        {
            "artifact": "current_operational_dataset",
            "path": str(current_dataset),
            "rows": current_rows_count,
            "sha256": current_sha,
            "role": "audited_dataset_no_modification",
        },
        {
            "artifact": "previous_operational_base",
            "path": str(PREVIOUS_OPERATIONAL_BASE),
            "rows": previous_rows_count,
            "sha256": previous_sha,
            "role": "new_row_comparison_reference",
        },
        {
            "artifact": "rollback_dataset",
            "path": str(ROLLBACK_DATASET),
            "rows": rollback_rows_count,
            "sha256": rollback_sha,
            "role": "rollback_reference_unchanged",
        },
    ]

    summary = {
        "selected_route": "Pre-scoring data quality audit via current operational pointer",
        "phase_type": PHASE_TYPE,
        "audit_decision": "AUDIT_CLEAN_READY_FOR_SCORING_DRY_RUN_DECISION" if approved_for_scoring_dry_run else "AUDIT_COMPLETED_REVIEW_FINDINGS_DOCUMENTED",
        "current_operational_pointer": str(POINTER_JSON),
        "current_operational_pointer_sha": pointer_sha,
        "current_dataset": str(current_dataset),
        "current_dataset_rows": current_rows_count,
        "current_dataset_sha": current_sha,
        "previous_operational_base_dataset": str(PREVIOUS_OPERATIONAL_BASE),
        "previous_operational_base_rows": previous_rows_count,
        "previous_operational_base_sha": previous_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows_count,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity": QUALITY_CEILING_TARGET - current_rows_count,
        "new_rows_vs_previous_operational_base": new_rows_count,
        "expected_new_rows_vs_previous_operational_base": EXPECTED_NEW_ROWS_VS_PREVIOUS,
        "current_column_count": len(current_header),
        "bad_width_rows_current": current_bad_width_rows,
        "bad_width_rows_previous": previous_bad_width_rows,
        "bad_width_rows_rollback": rollback_bad_width_rows,
        "duplicate_full_row_groups": len(duplicate_full_row_groups),
        "duplicate_full_row_extra_rows": duplicate_full_row_extra_rows,
        "duplicate_primary_key_groups": len(duplicate_primary_key_groups),
        "duplicate_primary_key_extra_rows": duplicate_primary_key_extra_rows,
        "instrument_suitability_flag_rows": instrument_flag_total,
        "instrument_suitability_flag_sample_rows": len(instrument_flag_rows),
        "blocking_quality_findings": blocking_quality_findings,
        "resolved_isin_column": columns.get("isin") or "",
        "resolved_symbol_column": columns.get("symbol") or "",
        "resolved_name_column": columns.get("name") or "",
        "resolved_country_column": columns.get("country") or "",
        "resolved_exchange_column": columns.get("exchange") or "",
        "resolved_mic_column": columns.get("mic") or "",
        "resolved_currency_column": columns.get("currency") or "",
        "resolved_source_provider_column": columns.get("source_provider") or "",
        "resolved_asset_type_column": columns.get("asset_type") or "",
        "approved_for_scoring_dry_run": approved_for_scoring_dry_run,
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
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ARTIFACT_MANIFEST_CSV, artifact_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(COLUMN_PROFILE_CSV, column_profile_rows, ["column", "non_missing", "missing", "missing_pct", "unique_non_empty", "sample_values"])
    write_csv(IDENTIFIER_COVERAGE_CSV, identifier_coverage_rows, ["role", "column", "column_resolved", "non_empty", "missing", "missing_pct", "unique_non_empty"])
    write_csv(VALUE_COVERAGE_CSV, value_coverage_rows, ["scope", "dimension", "column", "value", "count", "pct"])
    write_csv(DUPLICATE_FINDINGS_CSV, duplicate_finding_rows, ["finding_type", "key", "count", "extra_rows", "severity"])
    write_csv(NEW_ROWS_PROFILE_CSV, new_rows_profile_rows, ["scope", "dimension", "column", "value", "count", "pct"])
    write_csv(INSTRUMENT_FLAGS_CSV, instrument_flag_rows, ["row_number", "matched_terms", "isin", "symbol", "name", "country", "exchange", "mic", "currency", "source_provider", "severity"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
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
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "current_operational_pointer": str(POINTER_JSON),
            "current_dataset": str(current_dataset),
            "current_dataset_rows": current_rows_count,
            "current_dataset_sha": current_sha,
            "approved_for_scoring_dry_run": approved_for_scoring_dry_run,
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
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
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

v2.22C audits the current operational universe through the hardened pointer created in v2.22B.

Current dataset:

`{current_dataset}`

Rows: `{current_rows_count}`  
SHA256: `{current_sha}`

No scoring is executed. No OpenAI call is made. No broker call is made. full59k remains deprecated/deferred.

## Quality audit result

Audit decision: `{summary["audit_decision"]}`

Approved for scoring dry run: `{approved_for_scoring_dry_run}`

Blocking quality findings: `{blocking_quality_findings}`

## Key findings

- New rows vs previous operational base: `{new_rows_count}` expected `{EXPECTED_NEW_ROWS_VS_PREVIOUS}`
- Full-row duplicate groups: `{len(duplicate_full_row_groups)}`
- Full-row duplicate extra rows: `{duplicate_full_row_extra_rows}`
- Primary-key duplicate groups: `{len(duplicate_primary_key_groups)}`
- Primary-key duplicate extra rows: `{duplicate_primary_key_extra_rows}`
- Instrument suitability flagged rows: `{instrument_flag_total}`
- Bad-width rows current dataset: `{current_bad_width_rows}`
- Current column count: `{len(current_header)}`
- Remaining capacity vs 45k ceiling: `{QUALITY_CEILING_TARGET - current_rows_count}`

## Checks

{check_lines}

## Recommended next phase

Primary: `{recommended_next_phase}`

Secondary: `{SECONDARY_NEXT_PHASE}`
""",
    )

    print("")
    print("v2.22C pre-scoring data quality audit completed.")
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
    print("")
    print("SECONDARY_NEXT_PHASE:")
    print(f"- {SECONDARY_NEXT_PHASE}")


if __name__ == "__main__":
    main()
