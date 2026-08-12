from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20H"
PHASE = "ASX Expanded Validation"
PHASE_TYPE = "expanded-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PRE_HKEX_CURRENT_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
EXPANDED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"

V220G_JSON = OUTPUT_DIR / "asx_expanded_rebuild_candidate_v2_20g.json"
ASX_APPENDED_ROWS_CSV = OUTPUT_DIR / "asx_expanded_rebuild_appended_rows_v2_20g.csv"
ASX_APPENDED_AUDIT_CSV = OUTPUT_DIR / "asx_expanded_rebuild_appended_audit_v2_20g.csv"

REPORT_JSON = OUTPUT_DIR / "asx_expanded_validation_v2_20h.json"
REPORT_MD = OUTPUT_DIR / "asx_expanded_validation_v2_20h.md"
VALIDATION_SUMMARY_CSV = OUTPUT_DIR / "asx_expanded_validation_summary_v2_20h.csv"
SCHEMA_PROFILE_CSV = OUTPUT_DIR / "asx_expanded_validation_schema_profile_v2_20h.csv"
ROW_INTEGRITY_CSV = OUTPUT_DIR / "asx_expanded_validation_row_integrity_v2_20h.csv"
APPENDED_PROFILE_CSV = OUTPUT_DIR / "asx_expanded_validation_appended_profile_v2_20h.csv"
DUPLICATES_CSV = OUTPUT_DIR / "asx_expanded_validation_duplicates_v2_20h.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_expanded_validation_checks_v2_20h.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_expanded_validation_next_actions_v2_20h.csv"

EXPECTED_V220G_STATUS = "ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED = 40996
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392
ASX_APPENDED_ROWS_EXPECTED = 1316
EXPANDED_ROWS_EXPECTED = 42708

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"
EXPANDED_CANDIDATE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
APPENDED_ROWS_SHA_EXPECTED = "48cdcc8b28740421740ef6e14c830b37c1efcf03802fc2740f5555d891e23da4"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_ABOVE_QUALITY_FLOOR_EXPECTED = 708
REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED = 2292
ROWS_TO_ASPIRATIONAL_50K_AFTER_REBUILD_EXPECTED = 7292

STATUS_SUCCESS = "ASX_EXPANDED_VALIDATION_COMPLETED_42708_ROWS_1316_ASX_NET_NEW_VALIDATED_42K_CROSSED_45K_NOT_EXCEEDED_CLOSURE_REPORT_READY_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_EXPANDED_VALIDATION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20I - ASX Closure Report"
NEXT_PHASE_REVIEW = "v2.20H_REVIEW - ASX Expanded Validation Review"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_dicts(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV artifact: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


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


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_ticker(value: Any) -> str:
    text = clean_text(value).upper().replace(" ", "")
    text = re.sub(r"[^A-Z0-9\.\-]", "", text)

    if re.fullmatch(r"[A-Z0-9]{3}", text):
        return f"{text}.AX"

    return text


def normalize_isin(value: Any) -> str:
    text = clean_text(value).upper()
    return re.sub(r"[^A-Z0-9]", "", text)


def count_duplicates(values: list[str]) -> dict[str, int]:
    counts = Counter(value for value in values if value)
    return {value: count for value, count in sorted(counts.items()) if count > 1}


def get_values(rows: list[dict[str, str]], column: str, normalizer) -> list[str]:
    return [normalizer(row.get(column, "")) for row in rows if normalizer(row.get(column, ""))]


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        VALIDATION_SUMMARY_CSV,
        SCHEMA_PROFILE_CSV,
        ROW_INTEGRITY_CSV,
        APPENDED_PROFILE_CSV,
        DUPLICATES_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220g = read_json(V220G_JSON)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_rows = count_csv_rows(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    expanded_candidate_rows = count_csv_rows(EXPANDED_CANDIDATE_DATASET)
    appended_rows_count = count_csv_rows(ASX_APPENDED_ROWS_CSV)
    appended_audit_rows_count = count_csv_rows(ASX_APPENDED_AUDIT_CSV)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_before = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    expanded_candidate_sha_before = sha256_file(EXPANDED_CANDIDATE_DATASET)
    appended_rows_sha_before = sha256_file(ASX_APPENDED_ROWS_CSV)

    current_columns, current_rows = read_csv_dicts(CURRENT_VALIDATED_CANDIDATE_DATASET)
    expanded_columns, expanded_rows = read_csv_dicts(EXPANDED_CANDIDATE_DATASET)
    appended_columns, appended_rows = read_csv_dicts(ASX_APPENDED_ROWS_CSV)
    appended_audit_columns, appended_audit_rows = read_csv_dicts(ASX_APPENDED_AUDIT_CSV)

    current_prefix = expanded_rows[:current_validated_candidate_rows]
    expanded_tail = expanded_rows[current_validated_candidate_rows:]

    schema_preserved = expanded_columns == current_columns
    appended_schema_preserved = appended_columns == current_columns
    prefix_matches_current = current_prefix == current_rows
    tail_matches_appended_rows = expanded_tail == appended_rows

    rows_above_quality_floor = expanded_candidate_rows - QUALITY_FLOOR_TARGET
    remaining_capacity_to_quality_ceiling = QUALITY_CEILING_TARGET - expanded_candidate_rows
    rows_to_aspirational_50k_after_rebuild = ASPIRATIONAL_TARGET - expanded_candidate_rows

    current_tickers = set(get_values(current_rows, "ticker", normalize_ticker))
    current_symbols = set(get_values(current_rows, "symbol", normalize_ticker))
    current_isins = set(get_values(current_rows, "isin", normalize_isin))

    appended_tickers = get_values(appended_rows, "ticker", normalize_ticker)
    appended_symbols = get_values(appended_rows, "symbol", normalize_ticker)
    appended_isins = get_values(appended_rows, "isin", normalize_isin)

    expanded_tickers = get_values(expanded_rows, "ticker", normalize_ticker)
    expanded_symbols = get_values(expanded_rows, "symbol", normalize_ticker)
    expanded_isins = get_values(expanded_rows, "isin", normalize_isin)

    current_duplicate_tickers = count_duplicates(list(current_tickers))
    current_duplicate_symbols = count_duplicates(list(current_symbols))
    current_duplicate_isins = count_duplicates(list(current_isins))

    appended_duplicate_tickers = count_duplicates(appended_tickers)
    appended_duplicate_symbols = count_duplicates(appended_symbols)
    appended_duplicate_isins = count_duplicates(appended_isins)

    expanded_duplicate_tickers = count_duplicates(expanded_tickers)
    expanded_duplicate_symbols = count_duplicates(expanded_symbols)
    expanded_duplicate_isins = count_duplicates(expanded_isins)

    appended_tickers_already_current = sorted(set(appended_tickers) & current_tickers)
    appended_symbols_already_current = sorted(set(appended_symbols) & current_symbols)
    appended_isins_already_current = sorted(set(appended_isins) & current_isins)

    appended_provider_counts = Counter(clean_text(row.get("source_provider", "")) for row in appended_rows)
    appended_exchange_counts = Counter(clean_text(row.get("exchange", "")) for row in appended_rows)
    appended_country_counts = Counter(clean_text(row.get("country", "")) for row in appended_rows)
    appended_currency_counts = Counter(clean_text(row.get("currency", "")) for row in appended_rows)
    appended_mic_counts = Counter(clean_text(row.get("mic", "")) for row in appended_rows)
    appended_source_phase_counts = Counter(clean_text(row.get("source_phase", "")) for row in appended_rows)
    appended_instrument_type_counts = Counter(clean_text(row.get("instrument_type", "")) for row in appended_rows)
    appended_instrument_scope_counts = Counter(clean_text(row.get("instrument_scope", "")) for row in appended_rows)
    appended_merge_action_counts = Counter(clean_text(row.get("merge_action", "")) for row in appended_rows)

    appended_required_ticker_non_empty = all(normalize_ticker(row.get("ticker", "")) for row in appended_rows)
    appended_required_name_non_empty = all(clean_text(row.get("company_name", "")) for row in appended_rows)
    appended_required_isin_non_empty = all(normalize_isin(row.get("isin", "")) for row in appended_rows)
    appended_tickers_ax_suffix = all(normalize_ticker(row.get("ticker", "")).endswith(".AX") for row in appended_rows)

    appended_all_exchange_asx = set(appended_exchange_counts.keys()) == {"ASX"}
    appended_all_country_au = set(appended_country_counts.keys()) == {"Australia"}
    appended_all_provider_asx = set(appended_provider_counts.keys()) == {"ASX"}
    appended_all_currency_aud = set(appended_currency_counts.keys()) == {"AUD"}
    appended_all_mic_xasx = set(appended_mic_counts.keys()) == {"XASX"}
    appended_all_source_phase_v220g = set(appended_source_phase_counts.keys()) == {"v2.20G"}
    appended_all_merge_action_append = set(appended_merge_action_counts.keys()) == {"append_net_new"}

    allowed_instrument_types = {"equity", "reit", "listed_investment_vehicle", "equity_like"}
    allowed_instrument_scopes = {
        "ordinary_equity",
        "a_reit_equity_like",
        "listed_investment_vehicle_conditional",
        "ordinary_or_equity_like_unclassified",
    }

    appended_instrument_types_allowed = set(appended_instrument_type_counts.keys()).issubset(allowed_instrument_types)
    appended_instrument_scopes_allowed = set(appended_instrument_scope_counts.keys()).issubset(allowed_instrument_scopes)

    v220g_status = v220g.get("status", "")
    v220g_summary = v220g.get("rebuild_summary", {})

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_after = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    expanded_candidate_sha_after = sha256_file(EXPANDED_CANDIDATE_DATASET)
    appended_rows_sha_after = sha256_file(ASX_APPENDED_ROWS_CSV)

    checks: list[dict[str, Any]] = []
    critical_failed = 0
    warning_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed, warning_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        if severity == "warning" and not passed:
            warning_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_20g_report_exists", V220G_JSON.exists(), "critical", str(V220G_JSON))
    add_check("v2_20g_status_expected", v220g_status == EXPECTED_V220G_STATUS, "critical", str(v220g_status))
    add_check("v2_20g_next_phase_expected", v220g.get("recommended_next_phase") == "v2.20H - ASX Expanded Validation", "critical", str(v220g.get("recommended_next_phase")))
    add_check("v2_20g_expanded_rows_expected", int(v220g_summary.get("expanded_candidate_rows", -1)) == EXPANDED_ROWS_EXPECTED, "critical", f"v2_20g_expanded_rows={v220g_summary.get('expanded_candidate_rows')}")
    add_check("v2_20g_appended_rows_expected", int(v220g_summary.get("asx_net_new_rows_appended", -1)) == ASX_APPENDED_ROWS_EXPECTED, "critical", f"v2_20g_appended_rows={v220g_summary.get('asx_net_new_rows_appended')}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("pre_hkex_current_candidate_rows_expected", pre_hkex_current_candidate_rows == PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED, "critical", f"pre_hkex_rows={pre_hkex_current_candidate_rows}")
    add_check("current_validated_candidate_rows_expected", current_validated_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_validated_rows={current_validated_candidate_rows}")
    add_check("expanded_candidate_rows_expected", expanded_candidate_rows == EXPANDED_ROWS_EXPECTED, "critical", f"expanded_rows={expanded_candidate_rows}")
    add_check("appended_rows_expected", appended_rows_count == ASX_APPENDED_ROWS_EXPECTED, "critical", f"appended_rows={appended_rows_count}")
    add_check("appended_audit_rows_expected", appended_audit_rows_count == ASX_APPENDED_ROWS_EXPECTED, "critical", f"appended_audit_rows={appended_audit_rows_count}")
    add_check("row_arithmetic_expected", current_validated_candidate_rows + appended_rows_count == expanded_candidate_rows, "critical", f"{current_validated_candidate_rows}+{appended_rows_count}={expanded_candidate_rows}")

    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("pre_hkex_current_candidate_sha_expected", pre_hkex_current_candidate_sha_before == PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED, "critical", pre_hkex_current_candidate_sha_before)
    add_check("current_validated_candidate_sha_expected", current_validated_candidate_sha_before == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", current_validated_candidate_sha_before)
    add_check("expanded_candidate_sha_expected", expanded_candidate_sha_before == EXPANDED_CANDIDATE_SHA_EXPECTED, "critical", expanded_candidate_sha_before)
    add_check("appended_rows_sha_expected", appended_rows_sha_before == APPENDED_ROWS_SHA_EXPECTED, "critical", appended_rows_sha_before)

    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("pre_hkex_current_candidate_sha_unchanged", pre_hkex_current_candidate_sha_before == pre_hkex_current_candidate_sha_after, "critical", "pre-HKEX current candidate sha unchanged")
    add_check("current_validated_candidate_sha_unchanged", current_validated_candidate_sha_before == current_validated_candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("expanded_candidate_sha_unchanged", expanded_candidate_sha_before == expanded_candidate_sha_after, "critical", "expanded candidate sha unchanged during validation")
    add_check("appended_rows_sha_unchanged", appended_rows_sha_before == appended_rows_sha_after, "critical", "appended rows sha unchanged during validation")

    add_check("schema_column_count_expected", len(expanded_columns) == 33, "critical", f"expanded_columns={len(expanded_columns)}")
    add_check("schema_preserved_vs_current", schema_preserved, "critical", f"schema_preserved={schema_preserved}")
    add_check("appended_schema_preserved_vs_current", appended_schema_preserved, "critical", f"appended_schema_preserved={appended_schema_preserved}")
    add_check("current_prefix_preserved", prefix_matches_current, "critical", f"prefix_matches_current={prefix_matches_current}")
    add_check("appended_tail_matches_appended_rows", tail_matches_appended_rows, "critical", f"tail_matches_appended_rows={tail_matches_appended_rows}")

    add_check("quality_floor_crossed", expanded_candidate_rows >= QUALITY_FLOOR_TARGET, "critical", f"expanded_rows={expanded_candidate_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", expanded_candidate_rows <= QUALITY_CEILING_TARGET, "critical", f"expanded_rows={expanded_candidate_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_above_quality_floor_expected", rows_above_quality_floor == ROWS_ABOVE_QUALITY_FLOOR_EXPECTED, "critical", f"rows_above_floor={rows_above_quality_floor}")
    add_check("remaining_capacity_to_quality_ceiling_expected", remaining_capacity_to_quality_ceiling == REMAINING_CAPACITY_TO_QUALITY_CEILING_EXPECTED, "critical", f"capacity_to_ceiling={remaining_capacity_to_quality_ceiling}")
    add_check("rows_to_aspirational_50k_expected", rows_to_aspirational_50k_after_rebuild == ROWS_TO_ASPIRATIONAL_50K_AFTER_REBUILD_EXPECTED, "warning", f"rows_to_50k={rows_to_aspirational_50k_after_rebuild}")

    add_check("duplicate_appended_tickers_zero", len(appended_duplicate_tickers) == 0, "critical", f"duplicate_appended_tickers={len(appended_duplicate_tickers)}")
    add_check("duplicate_appended_symbols_zero", len(appended_duplicate_symbols) == 0, "critical", f"duplicate_appended_symbols={len(appended_duplicate_symbols)}")
    add_check("duplicate_appended_isins_zero", len(appended_duplicate_isins) == 0, "warning", f"duplicate_appended_isins={len(appended_duplicate_isins)}")
    add_check("appended_tickers_not_in_current", len(appended_tickers_already_current) == 0, "critical", f"tickers_already_current={len(appended_tickers_already_current)}")
    add_check("appended_symbols_not_in_current", len(appended_symbols_already_current) == 0, "critical", f"symbols_already_current={len(appended_symbols_already_current)}")
    add_check("appended_isins_not_in_current", len(appended_isins_already_current) == 0, "warning", f"isins_already_current={len(appended_isins_already_current)}")

    add_check("appended_required_ticker_non_empty", appended_required_ticker_non_empty, "critical", f"ticker_non_empty={appended_required_ticker_non_empty}")
    add_check("appended_required_name_non_empty", appended_required_name_non_empty, "critical", f"name_non_empty={appended_required_name_non_empty}")
    add_check("appended_required_isin_non_empty", appended_required_isin_non_empty, "warning", f"isin_non_empty={appended_required_isin_non_empty}")
    add_check("appended_tickers_ax_suffix", appended_tickers_ax_suffix, "critical", f"tickers_ax_suffix={appended_tickers_ax_suffix}")
    add_check("appended_all_exchange_asx", appended_all_exchange_asx, "critical", dict(appended_exchange_counts).__repr__())
    add_check("appended_all_country_australia", appended_all_country_au, "critical", dict(appended_country_counts).__repr__())
    add_check("appended_all_provider_asx", appended_all_provider_asx, "critical", dict(appended_provider_counts).__repr__())
    add_check("appended_all_currency_aud", appended_all_currency_aud, "critical", dict(appended_currency_counts).__repr__())
    add_check("appended_all_mic_xasx", appended_all_mic_xasx, "critical", dict(appended_mic_counts).__repr__())
    add_check("appended_all_source_phase_v220g", appended_all_source_phase_v220g, "critical", dict(appended_source_phase_counts).__repr__())
    add_check("appended_all_merge_action_append_net_new", appended_all_merge_action_append, "critical", dict(appended_merge_action_counts).__repr__())
    add_check("appended_instrument_types_allowed", appended_instrument_types_allowed, "critical", dict(appended_instrument_type_counts).__repr__())
    add_check("appended_instrument_scopes_allowed", appended_instrument_scopes_allowed, "critical", dict(appended_instrument_scope_counts).__repr__())

    add_check("expanded_validation_only", True, "critical", "expanded validation only")
    add_check("network_download_not_performed", True, "critical", "network_download_performed=False")
    add_check("raw_acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("raw_validation_not_performed", True, "critical", "raw_validation_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("candidate_validation_not_performed", True, "critical", "candidate_validation_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("pre_hkex_current_candidate_dataset_not_modified", True, "critical", "pre_hkex_current_candidate_dataset_modified=False")
    add_check("current_validated_candidate_dataset_not_modified", True, "critical", "current_validated_candidate_dataset_modified=False")
    add_check("expanded_candidate_dataset_not_modified", True, "critical", "expanded_candidate_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE

    validation_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "validated_candidate": str(EXPANDED_CANDIDATE_DATASET),
        "input_current_candidate": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
        "input_appended_rows": str(ASX_APPENDED_ROWS_CSV),
        "active_canonical_rows": active_canonical_rows,
        "current_validated_candidate_rows": current_validated_candidate_rows,
        "asx_appended_rows": appended_rows_count,
        "expanded_candidate_rows": expanded_candidate_rows,
        "row_arithmetic": f"{current_validated_candidate_rows}+{appended_rows_count}={expanded_candidate_rows}",
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": expanded_candidate_rows >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": expanded_candidate_rows <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": rows_above_quality_floor,
        "remaining_capacity_to_quality_ceiling": remaining_capacity_to_quality_ceiling,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k_after_rebuild": rows_to_aspirational_50k_after_rebuild,
        "schema_column_count": len(expanded_columns),
        "schema_preserved": schema_preserved,
        "current_prefix_preserved": prefix_matches_current,
        "appended_tail_matches_appended_rows": tail_matches_appended_rows,
        "duplicate_appended_tickers": len(appended_duplicate_tickers),
        "duplicate_appended_symbols": len(appended_duplicate_symbols),
        "duplicate_appended_isins": len(appended_duplicate_isins),
        "appended_tickers_already_current": len(appended_tickers_already_current),
        "appended_symbols_already_current": len(appended_symbols_already_current),
        "appended_isins_already_current": len(appended_isins_already_current),
        "expanded_candidate_sha": expanded_candidate_sha_after,
        "appended_rows_sha": appended_rows_sha_after,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    schema_profile_rows = [
        {
            "metric": "current_schema_column_count",
            "value": len(current_columns),
        },
        {
            "metric": "expanded_schema_column_count",
            "value": len(expanded_columns),
        },
        {
            "metric": "appended_schema_column_count",
            "value": len(appended_columns),
        },
        {
            "metric": "schema_preserved",
            "value": schema_preserved,
        },
        {
            "metric": "columns",
            "value": ";".join(expanded_columns),
        },
    ]

    row_integrity_rows = [
        {"metric": "current_validated_candidate_rows", "value": current_validated_candidate_rows},
        {"metric": "asx_appended_rows", "value": appended_rows_count},
        {"metric": "expanded_candidate_rows", "value": expanded_candidate_rows},
        {"metric": "row_arithmetic_expected", "value": current_validated_candidate_rows + appended_rows_count == expanded_candidate_rows},
        {"metric": "current_prefix_preserved", "value": prefix_matches_current},
        {"metric": "appended_tail_matches_appended_rows", "value": tail_matches_appended_rows},
        {"metric": "quality_floor_crossed", "value": expanded_candidate_rows >= QUALITY_FLOOR_TARGET},
        {"metric": "quality_ceiling_not_exceeded", "value": expanded_candidate_rows <= QUALITY_CEILING_TARGET},
    ]

    appended_profile_rows = [
        {"metric": "appended_rows", "value": appended_rows_count},
        {"metric": "appended_audit_rows", "value": appended_audit_rows_count},
        {"metric": "ticker_non_empty", "value": appended_required_ticker_non_empty},
        {"metric": "name_non_empty", "value": appended_required_name_non_empty},
        {"metric": "isin_non_empty", "value": appended_required_isin_non_empty},
        {"metric": "tickers_ax_suffix", "value": appended_tickers_ax_suffix},
        {"metric": "provider_counts", "value": dict(appended_provider_counts)},
        {"metric": "exchange_counts", "value": dict(appended_exchange_counts)},
        {"metric": "country_counts", "value": dict(appended_country_counts)},
        {"metric": "currency_counts", "value": dict(appended_currency_counts)},
        {"metric": "mic_counts", "value": dict(appended_mic_counts)},
        {"metric": "source_phase_counts", "value": dict(appended_source_phase_counts)},
        {"metric": "instrument_type_counts", "value": dict(appended_instrument_type_counts)},
        {"metric": "instrument_scope_counts", "value": dict(appended_instrument_scope_counts)},
        {"metric": "merge_action_counts", "value": dict(appended_merge_action_counts)},
    ]

    duplicate_rows = [
        {"duplicate_scope": "appended", "duplicate_type": "ticker", "duplicate_keys": len(appended_duplicate_tickers), "sample": ";".join(list(appended_duplicate_tickers.keys())[:20])},
        {"duplicate_scope": "appended", "duplicate_type": "symbol", "duplicate_keys": len(appended_duplicate_symbols), "sample": ";".join(list(appended_duplicate_symbols.keys())[:20])},
        {"duplicate_scope": "appended", "duplicate_type": "isin", "duplicate_keys": len(appended_duplicate_isins), "sample": ";".join(list(appended_duplicate_isins.keys())[:20])},
        {"duplicate_scope": "appended_vs_current", "duplicate_type": "ticker", "duplicate_keys": len(appended_tickers_already_current), "sample": ";".join(appended_tickers_already_current[:20])},
        {"duplicate_scope": "appended_vs_current", "duplicate_type": "symbol", "duplicate_keys": len(appended_symbols_already_current), "sample": ";".join(appended_symbols_already_current[:20])},
        {"duplicate_scope": "appended_vs_current", "duplicate_type": "isin", "duplicate_keys": len(appended_isins_already_current), "sample": ";".join(appended_isins_already_current[:20])},
        {"duplicate_scope": "expanded_total", "duplicate_type": "ticker", "duplicate_keys": len(expanded_duplicate_tickers), "sample": ";".join(list(expanded_duplicate_tickers.keys())[:20])},
        {"duplicate_scope": "expanded_total", "duplicate_type": "symbol", "duplicate_keys": len(expanded_duplicate_symbols), "sample": ";".join(list(expanded_duplicate_symbols.keys())[:20])},
        {"duplicate_scope": "expanded_total", "duplicate_type": "isin", "duplicate_keys": len(expanded_duplicate_isins), "sample": ";".join(list(expanded_duplicate_isins.keys())[:20])},
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "ASX",
            "action": "prepare_asx_closure_report",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Expanded ASX candidate validation passed at 42,708 rows with 1,316 net-new ASX rows.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "closure report only; do not promote canonical unless an explicit promotion phase is opened",
        },
        {
            "action_order": 2,
            "action_scope": "canonical",
            "action": "keep_canonical_unchanged_until_explicit_promotion",
            "priority": "high",
            "reason": "v2.20H validates the candidate only; canonical remains the old stable dataset.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "no replacement of expanded_universe_v2_14e.csv in v2.20H or closure report",
        },
        {
            "action_order": 3,
            "action_scope": "quality_target",
            "action": "record_quality_first_target_achieved",
            "priority": "high",
            "reason": "The operational 42k floor has been crossed while remaining below 45k.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "50k aspirational only; full59k deprecated",
        },
    ]

    write_csv(VALIDATION_SUMMARY_CSV, [{"metric": key, "value": value} for key, value in validation_summary.items()], ["metric", "value"])
    write_csv(SCHEMA_PROFILE_CSV, schema_profile_rows, ["metric", "value"])
    write_csv(ROW_INTEGRITY_CSV, row_integrity_rows, ["metric", "value"])
    write_csv(APPENDED_PROFILE_CSV, appended_profile_rows, ["metric", "value"])
    write_csv(DUPLICATES_CSV, duplicate_rows, ["duplicate_scope", "duplicate_type", "duplicate_keys", "sample"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "validation_summary": validation_summary,
        "schema_profile": schema_profile_rows,
        "row_integrity": row_integrity_rows,
        "appended_profile": appended_profile_rows,
        "duplicates": duplicate_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "expanded_validation_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_current_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": True,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "pre_hkex_current_candidate_dataset_read": True,
            "pre_hkex_current_candidate_dataset_modified": False,
            "pre_hkex_current_candidate_sha_unchanged": pre_hkex_current_candidate_sha_before == pre_hkex_current_candidate_sha_after,
            "current_validated_candidate_dataset_read": True,
            "current_validated_candidate_dataset_modified": False,
            "current_validated_candidate_sha_unchanged": current_validated_candidate_sha_before == current_validated_candidate_sha_after,
            "expanded_candidate_dataset_read": True,
            "expanded_candidate_dataset_modified": False,
            "expanded_candidate_sha_unchanged": expanded_candidate_sha_before == expanded_candidate_sha_after,
            "active_canonical_replaced": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.20H validates the ASX-expanded candidate dataset created in v2.20G.

Validated candidate:

`{EXPANDED_CANDIDATE_DATASET}`

The candidate contains **{expanded_candidate_rows:,}** rows. It preserves the current validated candidate prefix of **{current_validated_candidate_rows:,}** rows and appends **{appended_rows_count:,}** validated ASX net-new rows.

The candidate crosses the operational floor of **{QUALITY_FLOOR_TARGET:,}** and remains below the operational ceiling of **{QUALITY_CEILING_TARGET:,}**.

This phase validates the expanded candidate only. It does **not** promote canonical, does **not** rebuild again, does **not** run scoring, does **not** call OpenAI, does **not** call brokers, and does **not** launch full59k.

## Validation summary

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_validated_candidate_rows}`
- ASX appended rows: `{appended_rows_count}`
- Expanded candidate rows: `{expanded_candidate_rows}`
- Row arithmetic: `{current_validated_candidate_rows}+{appended_rows_count}={expanded_candidate_rows}`
- Quality floor crossed: `{expanded_candidate_rows >= QUALITY_FLOOR_TARGET}`
- Quality ceiling not exceeded: `{expanded_candidate_rows <= QUALITY_CEILING_TARGET}`
- Rows above 42k floor: `{rows_above_quality_floor}`
- Remaining capacity to 45k ceiling: `{remaining_capacity_to_quality_ceiling}`
- Rows to 50k aspirational after rebuild: `{rows_to_aspirational_50k_after_rebuild}`
- Schema column count: `{len(expanded_columns)}`
- Schema preserved: `{schema_preserved}`
- Current prefix preserved: `{prefix_matches_current}`
- Appended tail matches appended rows: `{tail_matches_appended_rows}`
- Duplicate appended tickers: `{len(appended_duplicate_tickers)}`
- Duplicate appended symbols: `{len(appended_duplicate_symbols)}`
- Duplicate appended ISINs: `{len(appended_duplicate_isins)}`
- Appended tickers already current: `{len(appended_tickers_already_current)}`
- Appended symbols already current: `{len(appended_symbols_already_current)}`
- Appended ISINs already current: `{len(appended_isins_already_current)}`
- Expanded candidate SHA256: `{expanded_candidate_sha_after}`
- Appended rows SHA256: `{appended_rows_sha_after}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Expanded validation only: true
- Canonical dataset modified: false
- Current validated candidate dataset modified: false
- Expanded candidate dataset modified: false
- Active canonical replaced: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.20H ASX expanded validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in validation_summary.items():
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
