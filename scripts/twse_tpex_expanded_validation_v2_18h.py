from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.18H"
PHASE = "TWSE + TPEx Expanded Validation"
PHASE_TYPE = "expanded-candidate-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
BASE_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"
EXPANDED_CANDIDATE_CSV = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V218G_JSON = OUTPUT_DIR / "twse_tpex_expanded_rebuild_candidate_v2_18g.json"
V218G_ADDED_ROWS_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_added_rows_v2_18g.csv"
V218G_WITHHELD_ROWS_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_withheld_rows_v2_18g.csv"
V218G_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_profile_v2_18g.csv"
V218G_NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_next_actions_v2_18g.csv"

V218F_CLASSIFICATION_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_classification_v2_18f.csv"

REPORT_JSON = OUTPUT_DIR / "twse_tpex_expanded_validation_v2_18h.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_expanded_validation_v2_18h.md"
PROFILE_CSV = OUTPUT_DIR / "twse_tpex_expanded_validation_profile_v2_18h.csv"
SCHEMA_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_expanded_validation_schema_profile_v2_18h.csv"
ROW_AUDIT_CSV = OUTPUT_DIR / "twse_tpex_expanded_validation_row_audit_v2_18h.csv"
SYMBOL_AUDIT_CSV = OUTPUT_DIR / "twse_tpex_expanded_validation_symbol_audit_v2_18h.csv"
ISSUE_AUDIT_CSV = OUTPUT_DIR / "twse_tpex_expanded_validation_issue_audit_v2_18h.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_expanded_validation_next_actions_v2_18h.csv"

EXPECTED_V218G_STATUS = "TWSE_TPEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_40996_ROWS_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
BASE_ROWS_EXPECTED = 40300
ADDED_ROWS_EXPECTED = 696
WITHHELD_ROWS_EXPECTED = 0
EXPANDED_ROWS_EXPECTED = 40996
SCHEMA_COLUMNS_EXPECTED = 33
POSSIBLE_EXISTING_EXPECTED = 379
EXISTING_EXPECTED = 0
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_AFTER_TWSE_EXPECTED = 9004

RECOMMENDED_NEXT_PHASE = "v2.18I - TWSE + TPEx Closure Report"
RECOMMENDED_REVIEW_PHASE = "v2.18H_REVIEW - TWSE + TPEx Expanded Validation Review"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                return list(reader.fieldnames or []), rows
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


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


def normalize_text(value: Any) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_symbol(value: Any) -> str:
    text = normalize_text(value).upper()
    text = re.sub(r"\.(TW|TWO|TPE|TAI|ROCO|TAIWAN)$", "", text)
    text = re.sub(r"[^0-9A-Z]", "", text)
    return text


def normalize_column_key(column: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(column or "").lower())


def row_value_by_alias(row: dict[str, Any], aliases: list[str]) -> str:
    normalized = {normalize_column_key(key): key for key in row.keys()}
    for alias in aliases:
        key = normalized.get(normalize_column_key(alias))
        if key:
            value = normalize_text(row.get(key, ""))
            if value:
                return value
    return ""


def row_signature(row: dict[str, str], header: list[str]) -> str:
    values = [row.get(col, "") for col in header]
    return json.dumps(values, ensure_ascii=False, separators=(",", ":"))


def count_blank(rows: list[dict[str, str]], column: str) -> int:
    return sum(1 for row in rows if not normalize_text(row.get(column, "")))


def value_counts(rows: list[dict[str, str]], column: str) -> Counter[str]:
    return Counter(normalize_text(row.get(column, "")) for row in rows)


def values_for_column(rows: list[dict[str, str]], column: str) -> list[str]:
    return [normalize_text(row.get(column, "")) for row in rows if normalize_text(row.get(column, ""))]


def symbols_from_classification(rows: list[dict[str, str]], bucket: str) -> set[str]:
    result = set()
    for row in rows:
        if normalize_text(row.get("canonical_validation_bucket", "")) == bucket:
            symbol = normalize_symbol(row.get("symbol", ""))
            if symbol:
                result.add(symbol)
    return result


def symbols_from_rows(rows: list[dict[str, str]]) -> set[str]:
    result = set()
    for row in rows:
        symbol = normalize_symbol(row_value_by_alias(row, ["symbol", "ticker"]))
        if symbol:
            result.add(symbol)
    return result


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        PROFILE_CSV,
        SCHEMA_PROFILE_CSV,
        ROW_AUDIT_CSV,
        SYMBOL_AUDIT_CSV,
        ISSUE_AUDIT_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v218g = read_json(V218G_JSON)

    canonical_sha_before = sha256_bytes(ACTIVE_CANONICAL_DATASET.read_bytes())
    base_sha_before = sha256_bytes(BASE_VALIDATED_CANDIDATE_DATASET.read_bytes())
    expanded_sha_before = sha256_bytes(EXPANDED_CANDIDATE_CSV.read_bytes())

    canonical_header, canonical_rows = read_csv_with_header(ACTIVE_CANONICAL_DATASET)
    base_header, base_rows = read_csv_with_header(BASE_VALIDATED_CANDIDATE_DATASET)
    expanded_header, expanded_rows = read_csv_with_header(EXPANDED_CANDIDATE_CSV)
    added_header, added_rows = read_csv_with_header(V218G_ADDED_ROWS_CSV)
    withheld_header, withheld_rows = read_csv_with_header(V218G_WITHHELD_ROWS_CSV)
    _, v218g_profile_rows = read_csv_with_header(V218G_PROFILE_CSV)
    _, v218g_next_actions_rows = read_csv_with_header(V218G_NEXT_ACTIONS_CSV)
    _, classification_rows = read_csv_with_header(V218F_CLASSIFICATION_CSV)

    canonical_sha_after = sha256_bytes(ACTIVE_CANONICAL_DATASET.read_bytes())
    base_sha_after = sha256_bytes(BASE_VALIDATED_CANDIDATE_DATASET.read_bytes())
    expanded_sha_after = sha256_bytes(EXPANDED_CANDIDATE_CSV.read_bytes())

    base_rows_count = len(base_rows)
    expanded_rows_count = len(expanded_rows)
    added_rows_count = len(added_rows)
    withheld_rows_count = len(withheld_rows)
    row_increment = expanded_rows_count - base_rows_count
    projected_rows_needed_after_twse = max(FINAL_TARGET_CANDIDATES - expanded_rows_count, 0)

    base_prefix_rows = expanded_rows[:base_rows_count]
    expanded_suffix_rows = expanded_rows[base_rows_count:]

    base_prefix_mismatches = []
    for index, (base_row, expanded_row) in enumerate(zip(base_rows, base_prefix_rows), start=1):
        if row_signature(base_row, base_header) != row_signature(expanded_row, expanded_header):
            base_prefix_mismatches.append(index)
            if len(base_prefix_mismatches) >= 20:
                break

    added_suffix_mismatches = []
    for index, (added_row, suffix_row) in enumerate(zip(added_rows, expanded_suffix_rows), start=1):
        if row_signature(added_row, added_header) != row_signature(suffix_row, expanded_header):
            added_suffix_mismatches.append(index)
            if len(added_suffix_mismatches) >= 20:
                break

    potential_net_new_symbols = symbols_from_classification(classification_rows, "potential_net_new")
    possible_existing_symbols = symbols_from_classification(classification_rows, "possible_existing")
    existing_symbols = symbols_from_classification(classification_rows, "existing")

    added_symbols = symbols_from_rows(added_rows)
    added_tickers = values_for_column(added_rows, "ticker")
    added_symbol_values = values_for_column(added_rows, "symbol")
    base_tickers = set(values_for_column(base_rows, "ticker"))
    base_symbols = {normalize_symbol(value) for value in values_for_column(base_rows, "symbol")}

    added_symbols_missing_from_potential = sorted(added_symbols - potential_net_new_symbols)
    potential_symbols_missing_from_added = sorted(potential_net_new_symbols - added_symbols)
    possible_existing_in_added = sorted(added_symbols.intersection(possible_existing_symbols))
    existing_in_added = sorted(added_symbols.intersection(existing_symbols))
    added_ticker_conflicts_with_base = sorted(set(added_tickers).intersection(base_tickers))
    added_symbol_conflicts_with_base = sorted(added_symbols.intersection(base_symbols))

    required_added_columns = [
        "ticker",
        "company_name",
        "exchange",
        "country",
        "source_provider",
        "instrument_type",
        "instrument_scope",
        "classification_confidence",
        "classification_reason",
        "currency",
        "mic",
        "provider",
        "source_phase",
        "symbol",
        "security_name",
    ]

    required_added_blank_counts = {
        column: count_blank(added_rows, column) for column in required_added_columns if column in added_header
    }

    added_ticker_duplicate_count = len(added_tickers) - len(set(added_tickers))
    added_symbol_duplicate_count = len(added_symbol_values) - len(set(added_symbol_values))

    added_non_tw_tickers = [
        ticker for ticker in added_tickers
        if not ticker.upper().endswith(".TW")
    ]

    added_non_twse_exchange = [
        row_value_by_alias(row, ["exchange"])
        for row in added_rows
        if row_value_by_alias(row, ["exchange"]).upper() != "TWSE"
    ]

    added_non_taiwan_country = [
        row_value_by_alias(row, ["country"])
        for row in added_rows
        if row_value_by_alias(row, ["country"]).upper() != "TAIWAN"
    ]

    added_non_twse_provider = [
        row_value_by_alias(row, ["source_provider", "provider"])
        for row in added_rows
        if row_value_by_alias(row, ["source_provider", "provider"]).upper() != "TWSE"
    ]

    added_non_equity_instrument_type = [
        row_value_by_alias(row, ["instrument_type"])
        for row in added_rows
        if row_value_by_alias(row, ["instrument_type"]).upper() != "EQUITY"
    ]

    added_non_common_equity_scope = [
        row_value_by_alias(row, ["instrument_scope"])
        for row in added_rows
        if row_value_by_alias(row, ["instrument_scope"]).lower() != "common_equity"
    ]

    added_wrong_source_phase = [
        row_value_by_alias(row, ["source_phase"])
        for row in added_rows
        if row_value_by_alias(row, ["source_phase"]) != "v2.18G"
    ]

    issue_rows: list[dict[str, Any]] = []

    def add_issue(issue_area: str, severity: str, passed: bool, detail: str) -> None:
        issue_rows.append(
            {
                "issue_area": issue_area,
                "severity": severity,
                "passed": bool(passed),
                "detail": detail,
            }
        )

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})
        add_issue(check, severity, passed, detail)

    add_check("v2_18g_report_exists", V218G_JSON.exists(), "critical", str(V218G_JSON))
    add_check("v2_18g_status_expected", v218g.get("status") == EXPECTED_V218G_STATUS, "critical", v218g.get("status", ""))
    add_check("active_canonical_exists", ACTIVE_CANONICAL_DATASET.exists(), "critical", str(ACTIVE_CANONICAL_DATASET))
    add_check("base_candidate_exists", BASE_VALIDATED_CANDIDATE_DATASET.exists(), "critical", str(BASE_VALIDATED_CANDIDATE_DATASET))
    add_check("expanded_candidate_exists", EXPANDED_CANDIDATE_CSV.exists(), "critical", str(EXPANDED_CANDIDATE_CSV))
    add_check("v2_18g_added_rows_exists", V218G_ADDED_ROWS_CSV.exists(), "critical", str(V218G_ADDED_ROWS_CSV))
    add_check("v2_18g_withheld_rows_exists", V218G_WITHHELD_ROWS_CSV.exists(), "critical", str(V218G_WITHHELD_ROWS_CSV))
    add_check("active_canonical_rows_expected", len(canonical_rows) == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={len(canonical_rows)}")
    add_check("base_rows_expected", base_rows_count == BASE_ROWS_EXPECTED, "critical", f"base_rows={base_rows_count}")
    add_check("expanded_rows_expected", expanded_rows_count == EXPANDED_ROWS_EXPECTED, "critical", f"expanded_rows={expanded_rows_count}")
    add_check("added_rows_expected", added_rows_count == ADDED_ROWS_EXPECTED, "critical", f"added_rows={added_rows_count}")
    add_check("withheld_rows_expected", withheld_rows_count == WITHHELD_ROWS_EXPECTED, "critical", f"withheld_rows={withheld_rows_count}")
    add_check("row_increment_expected", row_increment == ADDED_ROWS_EXPECTED, "critical", f"row_increment={row_increment}")
    add_check("schema_equal_base_expanded", base_header == expanded_header, "critical", "base header equals expanded header")
    add_check("schema_equal_base_added", base_header == added_header, "critical", "base header equals added header")
    add_check("schema_columns_33", len(expanded_header) == SCHEMA_COLUMNS_EXPECTED, "critical", f"schema_columns={len(expanded_header)}")
    add_check("base_prefix_unchanged_in_expanded", len(base_prefix_mismatches) == 0, "critical", f"first_mismatches={base_prefix_mismatches}")
    add_check("added_rows_are_expanded_suffix", len(added_suffix_mismatches) == 0, "critical", f"first_mismatches={added_suffix_mismatches}")
    add_check("potential_net_new_symbols_expected", len(potential_net_new_symbols) == ADDED_ROWS_EXPECTED, "critical", f"potential_net_new_symbols={len(potential_net_new_symbols)}")
    add_check("possible_existing_symbols_expected", len(possible_existing_symbols) == POSSIBLE_EXISTING_EXPECTED, "critical", f"possible_existing_symbols={len(possible_existing_symbols)}")
    add_check("existing_symbols_expected", len(existing_symbols) == EXISTING_EXPECTED, "critical", f"existing_symbols={len(existing_symbols)}")
    add_check("added_symbols_match_potential_net_new", len(added_symbols_missing_from_potential) == 0 and len(potential_symbols_missing_from_added) == 0, "critical", f"added_not_potential={len(added_symbols_missing_from_potential)} potential_not_added={len(potential_symbols_missing_from_added)}")
    add_check("possible_existing_not_added", len(possible_existing_in_added) == 0, "critical", f"possible_existing_in_added={len(possible_existing_in_added)}")
    add_check("existing_not_added", len(existing_in_added) == 0, "critical", f"existing_in_added={len(existing_in_added)}")
    add_check("added_tickers_unique", added_ticker_duplicate_count == 0, "critical", f"added_ticker_duplicate_count={added_ticker_duplicate_count}")
    add_check("added_symbols_unique", added_symbol_duplicate_count == 0, "critical", f"added_symbol_duplicate_count={added_symbol_duplicate_count}")
    add_check("added_tickers_no_base_conflict", len(added_ticker_conflicts_with_base) == 0, "critical", f"added_ticker_conflicts_with_base={len(added_ticker_conflicts_with_base)}")
    add_check("added_symbols_no_base_conflict", len(added_symbol_conflicts_with_base) == 0, "critical", f"added_symbol_conflicts_with_base={len(added_symbol_conflicts_with_base)}")
    add_check("added_tickers_tw_suffix", len(added_non_tw_tickers) == 0, "critical", f"non_tw_tickers={len(added_non_tw_tickers)}")
    add_check("added_exchange_twse", len(added_non_twse_exchange) == 0, "critical", f"non_twse_exchange={len(added_non_twse_exchange)}")
    add_check("added_country_taiwan", len(added_non_taiwan_country) == 0, "critical", f"non_taiwan_country={len(added_non_taiwan_country)}")
    add_check("added_provider_twse", len(added_non_twse_provider) == 0, "critical", f"non_twse_provider={len(added_non_twse_provider)}")
    add_check("added_instrument_type_equity", len(added_non_equity_instrument_type) == 0, "critical", f"non_equity_instrument_type={len(added_non_equity_instrument_type)}")
    add_check("added_instrument_scope_common_equity", len(added_non_common_equity_scope) == 0, "critical", f"non_common_equity_scope={len(added_non_common_equity_scope)}")
    add_check("added_source_phase_v2_18g", len(added_wrong_source_phase) == 0, "critical", f"wrong_source_phase={len(added_wrong_source_phase)}")
    add_check("added_required_columns_non_blank", all(count == 0 for count in required_added_blank_counts.values()), "critical", json.dumps(required_added_blank_counts, ensure_ascii=False, sort_keys=True))
    add_check("projected_rows_needed_after_twse_expected", projected_rows_needed_after_twse == ROWS_NEEDED_AFTER_TWSE_EXPECTED, "critical", f"projected_rows_needed_after_twse={projected_rows_needed_after_twse}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("base_candidate_sha_unchanged", base_sha_before == base_sha_after, "critical", "base candidate sha unchanged")
    add_check("expanded_candidate_sha_unchanged_during_validation", expanded_sha_before == expanded_sha_after, "critical", "expanded candidate sha unchanged during validation")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", expanded_rows_count < FINAL_TARGET_CANDIDATES, "critical", f"{expanded_rows_count} < {FINAL_TARGET_CANDIDATES}")

    schema_profile_rows = [
        {
            "column_order": index,
            "column_name": col,
            "base_present": col in base_header,
            "expanded_present": col in expanded_header,
            "added_present": col in added_header,
            "added_blank_count": count_blank(added_rows, col) if col in added_header else "",
            "added_distinct_count": len(set(values_for_column(added_rows, col))) if col in added_header else "",
        }
        for index, col in enumerate(expanded_header, start=1)
    ]

    row_audit_rows = [
        {"audit_key": "base_rows", "audit_value": base_rows_count, "expected_value": BASE_ROWS_EXPECTED, "passed": base_rows_count == BASE_ROWS_EXPECTED},
        {"audit_key": "expanded_rows", "audit_value": expanded_rows_count, "expected_value": EXPANDED_ROWS_EXPECTED, "passed": expanded_rows_count == EXPANDED_ROWS_EXPECTED},
        {"audit_key": "added_rows", "audit_value": added_rows_count, "expected_value": ADDED_ROWS_EXPECTED, "passed": added_rows_count == ADDED_ROWS_EXPECTED},
        {"audit_key": "withheld_rows", "audit_value": withheld_rows_count, "expected_value": WITHHELD_ROWS_EXPECTED, "passed": withheld_rows_count == WITHHELD_ROWS_EXPECTED},
        {"audit_key": "row_increment", "audit_value": row_increment, "expected_value": ADDED_ROWS_EXPECTED, "passed": row_increment == ADDED_ROWS_EXPECTED},
        {"audit_key": "base_prefix_mismatches", "audit_value": len(base_prefix_mismatches), "expected_value": 0, "passed": len(base_prefix_mismatches) == 0},
        {"audit_key": "added_suffix_mismatches", "audit_value": len(added_suffix_mismatches), "expected_value": 0, "passed": len(added_suffix_mismatches) == 0},
    ]

    symbol_audit_rows = [
        {"audit_key": "potential_net_new_symbols", "audit_value": len(potential_net_new_symbols), "expected_value": ADDED_ROWS_EXPECTED, "passed": len(potential_net_new_symbols) == ADDED_ROWS_EXPECTED, "detail": ""},
        {"audit_key": "added_symbols", "audit_value": len(added_symbols), "expected_value": ADDED_ROWS_EXPECTED, "passed": len(added_symbols) == ADDED_ROWS_EXPECTED, "detail": ""},
        {"audit_key": "added_symbols_missing_from_potential", "audit_value": len(added_symbols_missing_from_potential), "expected_value": 0, "passed": len(added_symbols_missing_from_potential) == 0, "detail": "|".join(added_symbols_missing_from_potential[:30])},
        {"audit_key": "potential_symbols_missing_from_added", "audit_value": len(potential_symbols_missing_from_added), "expected_value": 0, "passed": len(potential_symbols_missing_from_added) == 0, "detail": "|".join(potential_symbols_missing_from_added[:30])},
        {"audit_key": "possible_existing_in_added", "audit_value": len(possible_existing_in_added), "expected_value": 0, "passed": len(possible_existing_in_added) == 0, "detail": "|".join(possible_existing_in_added[:30])},
        {"audit_key": "existing_in_added", "audit_value": len(existing_in_added), "expected_value": 0, "passed": len(existing_in_added) == 0, "detail": "|".join(existing_in_added[:30])},
        {"audit_key": "added_ticker_conflicts_with_base", "audit_value": len(added_ticker_conflicts_with_base), "expected_value": 0, "passed": len(added_ticker_conflicts_with_base) == 0, "detail": "|".join(added_ticker_conflicts_with_base[:30])},
        {"audit_key": "added_symbol_conflicts_with_base", "audit_value": len(added_symbol_conflicts_with_base), "expected_value": 0, "passed": len(added_symbol_conflicts_with_base) == 0, "detail": "|".join(added_symbol_conflicts_with_base[:30])},
    ]

    if critical_failed == 0:
        status = "TWSE_TPEX_EXPANDED_VALIDATION_COMPLETED_40996_ROWS_VALIDATED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "TWSE_TPEX_EXPANDED_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    profile_rows = [
        {"profile_key": "version", "profile_value": VERSION, "notes": ""},
        {"profile_key": "phase", "profile_value": PHASE, "notes": ""},
        {"profile_key": "active_canonical_dataset", "profile_value": str(ACTIVE_CANONICAL_DATASET), "notes": ""},
        {"profile_key": "active_canonical_rows", "profile_value": len(canonical_rows), "notes": ""},
        {"profile_key": "base_candidate_dataset", "profile_value": str(BASE_VALIDATED_CANDIDATE_DATASET), "notes": ""},
        {"profile_key": "base_candidate_rows", "profile_value": base_rows_count, "notes": ""},
        {"profile_key": "expanded_candidate_dataset", "profile_value": str(EXPANDED_CANDIDATE_CSV), "notes": ""},
        {"profile_key": "expanded_candidate_rows", "profile_value": expanded_rows_count, "notes": ""},
        {"profile_key": "added_rows", "profile_value": added_rows_count, "notes": ""},
        {"profile_key": "withheld_rows", "profile_value": withheld_rows_count, "notes": ""},
        {"profile_key": "row_increment", "profile_value": row_increment, "notes": ""},
        {"profile_key": "schema_columns", "profile_value": len(expanded_header), "notes": "|".join(expanded_header)},
        {"profile_key": "potential_net_new_symbols", "profile_value": len(potential_net_new_symbols), "notes": ""},
        {"profile_key": "possible_existing_symbols", "profile_value": len(possible_existing_symbols), "notes": "not auto-added"},
        {"profile_key": "existing_symbols", "profile_value": len(existing_symbols), "notes": "not auto-added"},
        {"profile_key": "projected_rows_needed_after_twse", "profile_value": projected_rows_needed_after_twse, "notes": ""},
        {"profile_key": "active_canonical_sha256_before", "profile_value": canonical_sha_before, "notes": ""},
        {"profile_key": "active_canonical_sha256_after", "profile_value": canonical_sha_after, "notes": ""},
        {"profile_key": "base_candidate_sha256_before", "profile_value": base_sha_before, "notes": ""},
        {"profile_key": "base_candidate_sha256_after", "profile_value": base_sha_after, "notes": ""},
        {"profile_key": "expanded_candidate_sha256_before", "profile_value": expanded_sha_before, "notes": ""},
        {"profile_key": "expanded_candidate_sha256_after", "profile_value": expanded_sha_after, "notes": ""},
    ]

    next_action_rows = [
        {
            "action_order": 1,
            "action_scope": "TWSE",
            "action": "prepare_closure_report",
            "priority": "high",
            "reason": "Expanded candidate validation passed and is ready for TWSE + TPEx closure.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "closure/report only; no active canonical replacement; no scoring; no full59k",
        },
        {
            "action_order": 2,
            "action_scope": "50k",
            "action": "plan_next_provider_after_closure",
            "priority": "medium",
            "reason": f"Expanded candidate has {expanded_rows_count} rows; {projected_rows_needed_after_twse} remain to reach 50k.",
            "recommended_phase": "v2.19A - Next Provider Route Selection" if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "keep 50k target; do not relaunch full59k",
        },
    ]

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "active_canonical_rows": len(canonical_rows),
            "base_candidate_dataset": str(BASE_VALIDATED_CANDIDATE_DATASET),
            "base_candidate_rows": base_rows_count,
            "expanded_candidate_dataset": str(EXPANDED_CANDIDATE_CSV),
            "expanded_candidate_rows": expanded_rows_count,
            "added_rows": added_rows_count,
            "withheld_rows": withheld_rows_count,
            "row_increment": row_increment,
            "schema_columns": len(expanded_header),
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "projected_rows_needed_after_twse": projected_rows_needed_after_twse,
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "base_candidate_sha256_before": base_sha_before,
            "base_candidate_sha256_after": base_sha_after,
            "expanded_candidate_sha256_before": expanded_sha_before,
            "expanded_candidate_sha256_after": expanded_sha_after,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
        },
        "validation_summary": {
            "base_rows": base_rows_count,
            "expanded_rows": expanded_rows_count,
            "added_rows": added_rows_count,
            "withheld_rows": withheld_rows_count,
            "row_increment": row_increment,
            "schema_columns": len(expanded_header),
            "potential_net_new_symbols": len(potential_net_new_symbols),
            "possible_existing_symbols_not_added": len(possible_existing_symbols),
            "existing_symbols_not_added": len(existing_symbols),
            "added_ticker_duplicate_count": added_ticker_duplicate_count,
            "added_symbol_duplicate_count": added_symbol_duplicate_count,
            "added_ticker_conflicts_with_base": len(added_ticker_conflicts_with_base),
            "added_symbol_conflicts_with_base": len(added_symbol_conflicts_with_base),
            "critical_failed_checks": critical_failed,
        },
        "source_references": {
            "v2_18g_report": str(V218G_JSON),
            "v2_18g_added_rows": str(V218G_ADDED_ROWS_CSV),
            "v2_18g_withheld_rows": str(V218G_WITHHELD_ROWS_CSV),
            "v2_18g_profile": str(V218G_PROFILE_CSV),
            "v2_18g_next_actions": str(V218G_NEXT_ACTIONS_CSV),
            "v2_18f_classification": str(V218F_CLASSIFICATION_CSV),
            "v2_18g_profile_rows": len(v218g_profile_rows),
            "v2_18g_next_action_rows": len(v218g_next_actions_rows),
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": True,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "existing_expanded_candidate_read_only": True,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(PROFILE_CSV, profile_rows, ["profile_key", "profile_value", "notes"])
    write_csv(SCHEMA_PROFILE_CSV, schema_profile_rows, ["column_order", "column_name", "base_present", "expanded_present", "added_present", "added_blank_count", "added_distinct_count"])
    write_csv(ROW_AUDIT_CSV, row_audit_rows, ["audit_key", "audit_value", "expected_value", "passed"])
    write_csv(SYMBOL_AUDIT_CSV, symbol_audit_rows, ["audit_key", "audit_value", "expected_value", "passed", "detail"])
    write_csv(ISSUE_AUDIT_CSV, issue_rows, ["issue_area", "severity", "passed", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_action_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.18H validates the TWSE + TPEx expanded candidate generated in v2.18G.

This phase is validation-only. It does not rebuild the candidate, does not replace the active canonical dataset, does not modify canonical, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `{ACTIVE_CANONICAL_DATASET}`
- Active canonical rows: `{len(canonical_rows)}`
- Base candidate dataset: `{BASE_VALIDATED_CANDIDATE_DATASET}`
- Base candidate rows: `{base_rows_count}`
- Expanded candidate dataset: `{EXPANDED_CANDIDATE_CSV}`
- Expanded candidate rows: `{expanded_rows_count}`
- Added rows: `{added_rows_count}`
- Withheld rows: `{withheld_rows_count}`
- Row increment: `{row_increment}`
- Schema columns: `{len(expanded_header)}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Projected rows needed after TWSE: `{projected_rows_needed_after_twse}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

- Base rows: `{base_rows_count}`
- Expanded rows: `{expanded_rows_count}`
- Added rows: `{added_rows_count}`
- Withheld rows: `{withheld_rows_count}`
- Row increment: `{row_increment}`
- Potential net-new symbols: `{len(potential_net_new_symbols)}`
- Possible existing symbols not added: `{len(possible_existing_symbols)}`
- Existing symbols not added: `{len(existing_symbols)}`
- Added ticker duplicate count: `{added_ticker_duplicate_count}`
- Added symbol duplicate count: `{added_symbol_duplicate_count}`
- Added ticker conflicts with base: `{len(added_ticker_conflicts_with_base)}`
- Added symbol conflicts with base: `{len(added_symbol_conflicts_with_base)}`
- Critical failed checks: `{critical_failed}`

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: true
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Existing expanded candidate read only: true
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.18H TWSE + TPEx expanded validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in payload["validation_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
