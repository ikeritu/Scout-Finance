from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20G"
PHASE = "ASX Expanded Rebuild Candidate"
PHASE_TYPE = "expanded-rebuild-candidate-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PRE_HKEX_CURRENT_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V220F_JSON = OUTPUT_DIR / "asx_candidate_validation_against_current_dry_run_v2_20f.json"
ASX_NET_NEW_CANDIDATES_CSV = OUTPUT_DIR / "asx_candidate_validation_net_new_candidates_v2_20f.csv"

EXPANDED_CANDIDATE_CSV = OUTPUT_DIR / "expanded_universe_candidate_asx_v2_20g.csv"
APPENDED_ROWS_CSV = OUTPUT_DIR / "asx_expanded_rebuild_appended_rows_v2_20g.csv"
APPENDED_AUDIT_CSV = OUTPUT_DIR / "asx_expanded_rebuild_appended_audit_v2_20g.csv"
REBUILD_SUMMARY_CSV = OUTPUT_DIR / "asx_expanded_rebuild_summary_v2_20g.csv"
REBUILD_CHECKS_CSV = OUTPUT_DIR / "asx_expanded_rebuild_checks_v2_20g.csv"
REPORT_JSON = OUTPUT_DIR / "asx_expanded_rebuild_candidate_v2_20g.json"
REPORT_MD = OUTPUT_DIR / "asx_expanded_rebuild_candidate_v2_20g.md"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_expanded_rebuild_next_actions_v2_20g.csv"

EXPECTED_V220F_STATUS = "ASX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NET_NEW_READY_REBUILD_CANDIDATE_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED = 40996
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392
ASX_NET_NEW_ROWS_EXPECTED = 1316
EXPANDED_ROWS_EXPECTED = 42708

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED = 608
ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED = 3608
ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED = 8608

STATUS_SUCCESS = "ASX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_42708_ROWS_1316_NET_NEW_42K_CROSSED_45K_NOT_EXCEEDED_CANONICAL_UNCHANGED_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_EXPANDED_REBUILD_CANDIDATE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20H - ASX Expanded Validation"
NEXT_PHASE_REVIEW = "v2.20G_REVIEW - ASX Expanded Rebuild Candidate Review"


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


def normalize_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def map_instrument_type(instrument_class: str) -> str:
    mapping = {
        "ordinary_equity": "equity",
        "a_reit_equity_like": "reit",
        "listed_investment_vehicle_conditional": "listed_investment_vehicle",
        "ordinary_or_equity_like_unclassified": "equity_like",
    }
    return mapping.get(instrument_class, "equity_like")


def map_classification_reason(row: dict[str, str]) -> str:
    parts = [
        "ASX v2.20F net_new_candidate",
        f"instrument_class={clean_text(row.get('instrument_class', ''))}",
        f"match_type={clean_text(row.get('match_type', ''))}",
        f"context_match={clean_text(row.get('context_match', ''))}",
    ]
    return "; ".join(part for part in parts if part)


def make_appended_row(current_columns: list[str], row: dict[str, str]) -> dict[str, str]:
    output = {column: "" for column in current_columns}

    ticker = normalize_ticker(row.get("ticker", ""))
    symbol = normalize_ticker(row.get("symbol", "")) or ticker
    name = clean_text(row.get("name", ""))
    isin = normalize_isin(row.get("isin", ""))
    instrument_class = clean_text(row.get("instrument_class", ""))
    scope_confidence = clean_text(row.get("scope_confidence", "")) or "medium"
    product_description = clean_text(row.get("product_description", ""))
    asx_code = clean_text(row.get("asx_code", "")).upper()

    values = {
        "ticker": ticker,
        "company_name": name,
        "exchange": "ASX",
        "country": "Australia",
        "source_provider": "ASX",
        "source_file": str(ASX_NET_NEW_CANDIDATES_CSV),
        "instrument_type": map_instrument_type(instrument_class),
        "instrument_scope": instrument_class,
        "classification_confidence": scope_confidence,
        "classification_reason": map_classification_reason(row),
        "sector": "",
        "industry": "",
        "market_cap": "",
        "raw_cik": "",
        "raw_exchange": "ASX",
        "provider_precedence": "ASX_AFTER_HKEX_V2_20G",
        "merge_action": "append_net_new",
        "merge_reason": "ASX v2.20F validation_decision=net_new_candidate; no_current_match",
        "isin": isin,
        "currency": "AUD",
        "mic": "XASX",
        "source_version": VERSION,
        "source_url": "https://www.asx.com.au/markets/market-resources/isin-services",
        "hkex_category": "",
        "hkex_subcategory": "",
        "hkex_board_lot": "",
        "provider": "ASX",
        "source_phase": VERSION,
        "symbol": symbol,
        "security_name": name,
        "instrument_id": asx_code,
        "product_assignment_group_description": product_description,
        "asset_type": instrument_class,
    }

    for key, value in values.items():
        if key in output:
            output[key] = clean_text(value)

    return output


def main() -> None:
    for path in [
        EXPANDED_CANDIDATE_CSV,
        APPENDED_ROWS_CSV,
        APPENDED_AUDIT_CSV,
        REBUILD_SUMMARY_CSV,
        REBUILD_CHECKS_CSV,
        REPORT_JSON,
        REPORT_MD,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220f = read_json(V220F_JSON)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_rows = count_csv_rows(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_before = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    current_columns, current_rows = read_csv_dicts(CURRENT_VALIDATED_CANDIDATE_DATASET)
    net_new_columns, net_new_rows = read_csv_dicts(ASX_NET_NEW_CANDIDATES_CSV)

    rows_needed_to_quality_floor = max(QUALITY_FLOOR_TARGET - current_validated_candidate_rows, 0)
    rows_needed_to_quality_ceiling = max(QUALITY_CEILING_TARGET - current_validated_candidate_rows, 0)
    rows_needed_to_aspirational_50k = max(ASPIRATIONAL_TARGET - current_validated_candidate_rows, 0)

    appended_rows = [make_appended_row(current_columns, row) for row in net_new_rows]
    expanded_rows = current_rows + appended_rows

    write_csv(EXPANDED_CANDIDATE_CSV, expanded_rows, current_columns)
    write_csv(APPENDED_ROWS_CSV, appended_rows, current_columns)

    expanded_columns, expanded_rows_reloaded = read_csv_dicts(EXPANDED_CANDIDATE_CSV)
    appended_columns, appended_rows_reloaded = read_csv_dicts(APPENDED_ROWS_CSV)

    expanded_candidate_rows = len(expanded_rows_reloaded)
    appended_candidate_rows = len(appended_rows_reloaded)

    expanded_candidate_sha = sha256_file(EXPANDED_CANDIDATE_CSV)
    appended_rows_sha = sha256_file(APPENDED_ROWS_CSV)

    prefix_matches_current = expanded_rows_reloaded[:len(current_rows)] == current_rows
    appended_tail_matches = expanded_rows_reloaded[len(current_rows):] == appended_rows_reloaded
    schema_preserved = expanded_columns == current_columns
    appended_schema_preserved = appended_columns == current_columns

    current_tickers = {normalize_ticker(row.get("ticker", "")) for row in current_rows if normalize_ticker(row.get("ticker", ""))}
    current_symbols = {normalize_ticker(row.get("symbol", "")) for row in current_rows if normalize_ticker(row.get("symbol", ""))}
    current_isins = {normalize_isin(row.get("isin", "")) for row in current_rows if normalize_isin(row.get("isin", ""))}

    appended_tickers = [normalize_ticker(row.get("ticker", "")) for row in appended_rows if normalize_ticker(row.get("ticker", ""))]
    appended_symbols = [normalize_ticker(row.get("symbol", "")) for row in appended_rows if normalize_ticker(row.get("symbol", ""))]
    appended_isins = [normalize_isin(row.get("isin", "")) for row in appended_rows if normalize_isin(row.get("isin", ""))]

    appended_ticker_counts = Counter(appended_tickers)
    appended_symbol_counts = Counter(appended_symbols)
    appended_isin_counts = Counter(appended_isins)

    duplicate_appended_tickers = {ticker: count for ticker, count in appended_ticker_counts.items() if count > 1}
    duplicate_appended_symbols = {symbol: count for symbol, count in appended_symbol_counts.items() if count > 1}
    duplicate_appended_isins = {isin: count for isin, count in appended_isin_counts.items() if count > 1}

    appended_tickers_already_current = sorted(set(appended_tickers) & current_tickers)
    appended_symbols_already_current = sorted(set(appended_symbols) & current_symbols)
    appended_isins_already_current = sorted(set(appended_isins) & current_isins)

    appended_audit_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(net_new_rows, start=1):
        ticker = normalize_ticker(row.get("ticker", ""))
        isin = normalize_isin(row.get("isin", ""))
        appended_audit_rows.append(
            {
                "append_order": idx,
                "source_phase": VERSION,
                "asx_code": clean_text(row.get("asx_code", "")),
                "ticker": ticker,
                "symbol": normalize_ticker(row.get("symbol", "")) or ticker,
                "name": clean_text(row.get("name", "")),
                "isin": isin,
                "instrument_class": clean_text(row.get("instrument_class", "")),
                "scope_confidence": clean_text(row.get("scope_confidence", "")),
                "validation_decision": clean_text(row.get("validation_decision", "")),
                "match_type": clean_text(row.get("match_type", "")),
                "context_match": clean_text(row.get("context_match", "")),
                "last_price": clean_text(row.get("last_price", "")),
                "business_date": clean_text(row.get("business_date", "")),
                "appended_ticker_duplicate_count": appended_ticker_counts.get(ticker, 0),
                "appended_isin_duplicate_count": appended_isin_counts.get(isin, 0) if isin else 0,
                "ticker_already_in_current": ticker in current_tickers,
                "isin_already_in_current": isin in current_isins if isin else False,
            }
        )

    write_csv(
        APPENDED_AUDIT_CSV,
        appended_audit_rows,
        [
            "append_order",
            "source_phase",
            "asx_code",
            "ticker",
            "symbol",
            "name",
            "isin",
            "instrument_class",
            "scope_confidence",
            "validation_decision",
            "match_type",
            "context_match",
            "last_price",
            "business_date",
            "appended_ticker_duplicate_count",
            "appended_isin_duplicate_count",
            "ticker_already_in_current",
            "isin_already_in_current",
        ],
    )

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_after = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    v220f_status = v220f.get("status", "")
    v220f_summary = v220f.get("validation_summary", {})

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

    add_check("v2_20f_report_exists", V220F_JSON.exists(), "critical", str(V220F_JSON))
    add_check("v2_20f_status_expected", v220f_status == EXPECTED_V220F_STATUS, "critical", str(v220f_status))
    add_check("v2_20f_next_phase_expected", v220f.get("recommended_next_phase") == "v2.20G - ASX Expanded Rebuild Candidate", "critical", str(v220f.get("recommended_next_phase")))
    add_check("v2_20f_net_new_rows_expected", int(v220f_summary.get("net_new_candidate_rows", -1)) == ASX_NET_NEW_ROWS_EXPECTED, "critical", f"v2_20f_net_new={v220f_summary.get('net_new_candidate_rows')}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("pre_hkex_current_candidate_rows_expected", pre_hkex_current_candidate_rows == PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED, "critical", f"pre_hkex_rows={pre_hkex_current_candidate_rows}")
    add_check("current_validated_candidate_rows_expected", current_validated_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_validated_rows={current_validated_candidate_rows}")
    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("pre_hkex_current_candidate_sha_expected", pre_hkex_current_candidate_sha_before == PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED, "critical", pre_hkex_current_candidate_sha_before)
    add_check("current_validated_candidate_sha_expected", current_validated_candidate_sha_before == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", current_validated_candidate_sha_before)
    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("pre_hkex_current_candidate_sha_unchanged", pre_hkex_current_candidate_sha_before == pre_hkex_current_candidate_sha_after, "critical", "pre-HKEX current candidate sha unchanged")
    add_check("current_validated_candidate_sha_unchanged", current_validated_candidate_sha_before == current_validated_candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("current_schema_column_count_expected", len(current_columns) == 33, "critical", f"current_columns={len(current_columns)}")
    add_check("expanded_schema_preserved", schema_preserved, "critical", f"schema_preserved={schema_preserved}")
    add_check("appended_schema_preserved", appended_schema_preserved, "critical", f"appended_schema_preserved={appended_schema_preserved}")
    add_check("asx_net_new_rows_loaded", len(net_new_rows) == ASX_NET_NEW_ROWS_EXPECTED, "critical", f"net_new_rows={len(net_new_rows)}")
    add_check("appended_rows_expected", appended_candidate_rows == ASX_NET_NEW_ROWS_EXPECTED, "critical", f"appended_rows={appended_candidate_rows}")
    add_check("expanded_rows_expected", expanded_candidate_rows == EXPANDED_ROWS_EXPECTED, "critical", f"expanded_rows={expanded_candidate_rows}")
    add_check("row_arithmetic_expected", current_validated_candidate_rows + appended_candidate_rows == expanded_candidate_rows, "critical", f"{current_validated_candidate_rows}+{appended_candidate_rows}={expanded_candidate_rows}")
    add_check("quality_floor_crossed", expanded_candidate_rows >= QUALITY_FLOOR_TARGET, "critical", f"expanded_rows={expanded_candidate_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_not_exceeded", expanded_candidate_rows <= QUALITY_CEILING_TARGET, "critical", f"expanded_rows={expanded_candidate_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_needed_to_quality_floor_expected", rows_needed_to_quality_floor == ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED, "critical", f"rows_needed_to_42k={rows_needed_to_quality_floor}")
    add_check("rows_needed_to_quality_ceiling_expected", rows_needed_to_quality_ceiling == ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED, "critical", f"rows_needed_to_45k={rows_needed_to_quality_ceiling}")
    add_check("rows_needed_to_50k_aspirational_expected", rows_needed_to_aspirational_50k == ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_needed_to_50k={rows_needed_to_aspirational_50k}")
    add_check("current_prefix_preserved", prefix_matches_current, "critical", f"prefix_matches_current={prefix_matches_current}")
    add_check("appended_tail_matches_appended_rows", appended_tail_matches, "critical", f"tail_matches={appended_tail_matches}")
    add_check("duplicate_appended_tickers_zero", len(duplicate_appended_tickers) == 0, "critical", f"duplicate_appended_tickers={len(duplicate_appended_tickers)}")
    add_check("duplicate_appended_symbols_zero", len(duplicate_appended_symbols) == 0, "critical", f"duplicate_appended_symbols={len(duplicate_appended_symbols)}")
    add_check("duplicate_appended_isins_zero", len(duplicate_appended_isins) == 0, "warning", f"duplicate_appended_isins={len(duplicate_appended_isins)}")
    add_check("appended_tickers_not_in_current", len(appended_tickers_already_current) == 0, "critical", f"tickers_already_current={len(appended_tickers_already_current)}")
    add_check("appended_symbols_not_in_current", len(appended_symbols_already_current) == 0, "critical", f"symbols_already_current={len(appended_symbols_already_current)}")
    add_check("appended_isins_not_in_current", len(appended_isins_already_current) == 0, "warning", f"isins_already_current={len(appended_isins_already_current)}")
    add_check("expanded_candidate_written", EXPANDED_CANDIDATE_CSV.exists(), "critical", str(EXPANDED_CANDIDATE_CSV))
    add_check("expanded_rebuild_candidate_only", True, "critical", "expanded rebuild candidate only")
    add_check("network_download_not_performed", True, "critical", "network_download_performed=False")
    add_check("raw_acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("raw_validation_not_performed", True, "critical", "raw_validation_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("candidate_validation_not_performed", True, "critical", "candidate_validation_performed=False")
    add_check("expanded_validation_not_performed", True, "critical", "expanded_validation_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("pre_hkex_current_candidate_dataset_not_modified", True, "critical", "pre_hkex_current_candidate_dataset_modified=False")
    add_check("current_validated_candidate_dataset_not_modified", True, "critical", "current_validated_candidate_dataset_modified=False")
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

    rebuild_summary = {
        "selected_provider": "ASX",
        "phase_type": PHASE_TYPE,
        "input_current_candidate": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
        "input_asx_net_new": str(ASX_NET_NEW_CANDIDATES_CSV),
        "expanded_candidate": str(EXPANDED_CANDIDATE_CSV),
        "current_validated_candidate_rows": current_validated_candidate_rows,
        "asx_net_new_rows_appended": appended_candidate_rows,
        "expanded_candidate_rows": expanded_candidate_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "quality_floor_crossed": expanded_candidate_rows >= QUALITY_FLOOR_TARGET,
        "quality_ceiling_not_exceeded": expanded_candidate_rows <= QUALITY_CEILING_TARGET,
        "rows_above_quality_floor": expanded_candidate_rows - QUALITY_FLOOR_TARGET,
        "remaining_capacity_to_quality_ceiling": QUALITY_CEILING_TARGET - expanded_candidate_rows,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_to_aspirational_50k_after_rebuild": ASPIRATIONAL_TARGET - expanded_candidate_rows,
        "schema_column_count": len(current_columns),
        "schema_preserved": schema_preserved,
        "current_prefix_preserved": prefix_matches_current,
        "appended_tail_matches": appended_tail_matches,
        "duplicate_appended_tickers": len(duplicate_appended_tickers),
        "duplicate_appended_symbols": len(duplicate_appended_symbols),
        "duplicate_appended_isins": len(duplicate_appended_isins),
        "appended_tickers_already_current": len(appended_tickers_already_current),
        "appended_symbols_already_current": len(appended_symbols_already_current),
        "appended_isins_already_current": len(appended_isins_already_current),
        "active_canonical_rows": active_canonical_rows,
        "active_canonical_sha": active_canonical_sha_after,
        "current_validated_candidate_sha": current_validated_candidate_sha_after,
        "expanded_candidate_sha": expanded_candidate_sha,
        "appended_rows_sha": appended_rows_sha,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    summary_rows = [{"metric": key, "value": value} for key, value in rebuild_summary.items()]
    write_csv(REBUILD_SUMMARY_CSV, summary_rows, ["metric", "value"])
    write_csv(REBUILD_CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "ASX",
            "action": "run_asx_expanded_validation",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "Expanded ASX candidate has been rebuilt at 42,708 rows; next step is validation before any promotion decision.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "validate expanded candidate only; do not promote canonical; do not score",
        },
        {
            "action_order": 2,
            "action_scope": "quality_target",
            "action": "preserve_42k_45k_operational_band",
            "priority": "high",
            "reason": "ASX rebuild crosses 42k and remains below 45k.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "50k aspirational only; full59k deprecated",
        },
        {
            "action_order": 3,
            "action_scope": "canonical",
            "action": "defer_canonical_promotion_until_validation_pass",
            "priority": "high",
            "reason": "v2.20G writes candidate only. Canonical must remain unchanged until explicit promotion phase.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "no canonical replacement in v2.20G",
        },
    ]
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "rebuild_summary": rebuild_summary,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "expanded_rebuild_candidate_only": True,
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
            "expanded_rebuild_candidate_performed": True,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "pre_hkex_current_candidate_dataset_read": True,
            "pre_hkex_current_candidate_dataset_modified": False,
            "pre_hkex_current_candidate_sha_unchanged": pre_hkex_current_candidate_sha_before == pre_hkex_current_candidate_sha_after,
            "current_validated_candidate_dataset_read": True,
            "current_validated_candidate_dataset_modified": False,
            "current_validated_candidate_sha_unchanged": current_validated_candidate_sha_before == current_validated_candidate_sha_after,
            "new_expanded_candidate_written": True,
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

v2.20G rebuilds a new ASX-expanded candidate dataset.

Input current candidate:

`{CURRENT_VALIDATED_CANDIDATE_DATASET}`

Input ASX net-new candidates:

`{ASX_NET_NEW_CANDIDATES_CSV}`

Output expanded candidate:

`{EXPANDED_CANDIDATE_CSV}`

This phase appends **{appended_candidate_rows:,}** ASX net-new rows to the current validated candidate of **{current_validated_candidate_rows:,}** rows, producing **{expanded_candidate_rows:,}** rows.

The rebuild crosses the operational floor of **{QUALITY_FLOOR_TARGET:,}** and remains below the operational ceiling of **{QUALITY_CEILING_TARGET:,}**.

This phase writes a new candidate only. It does **not** promote canonical, does **not** run expanded validation, does **not** run scoring, does **not** call OpenAI, does **not** call brokers, and does **not** launch full59k.

## Rebuild summary

- Current validated candidate rows: `{current_validated_candidate_rows}`
- ASX net-new rows appended: `{appended_candidate_rows}`
- Expanded candidate rows: `{expanded_candidate_rows}`
- Quality floor crossed: `{expanded_candidate_rows >= QUALITY_FLOOR_TARGET}`
- Quality ceiling not exceeded: `{expanded_candidate_rows <= QUALITY_CEILING_TARGET}`
- Rows above 42k floor: `{expanded_candidate_rows - QUALITY_FLOOR_TARGET}`
- Remaining capacity to 45k ceiling: `{QUALITY_CEILING_TARGET - expanded_candidate_rows}`
- Rows to 50k aspirational after rebuild: `{ASPIRATIONAL_TARGET - expanded_candidate_rows}`
- Schema column count: `{len(current_columns)}`
- Schema preserved: `{schema_preserved}`
- Current prefix preserved: `{prefix_matches_current}`
- Appended tail matches: `{appended_tail_matches}`
- Duplicate appended tickers: `{len(duplicate_appended_tickers)}`
- Duplicate appended symbols: `{len(duplicate_appended_symbols)}`
- Duplicate appended ISINs: `{len(duplicate_appended_isins)}`
- Appended tickers already current: `{len(appended_tickers_already_current)}`
- Appended symbols already current: `{len(appended_symbols_already_current)}`
- Appended ISINs already current: `{len(appended_isins_already_current)}`
- Expanded candidate SHA256: `{expanded_candidate_sha}`
- Appended rows SHA256: `{appended_rows_sha}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Expanded rebuild candidate only: true
- New expanded candidate written: true
- Canonical dataset modified: false
- Current validated candidate dataset modified: false
- Active canonical replaced: false
- Expanded validation performed: false
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

    print("v2.20G ASX expanded rebuild candidate completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REBUILD_SUMMARY:")
    for key, value in rebuild_summary.items():
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
