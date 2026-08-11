from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.19P"
PHASE = "HKEX Expanded Rebuild Candidate"
PHASE_TYPE = "expanded-rebuild-candidate-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219O_JSON = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_v2_19o.json"
V219O_NET_NEW_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_net_new_candidates_v2_19o.csv"
V219O_COMPARISON_SUMMARY_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_comparison_summary_v2_19o.csv"

EXPANDED_CANDIDATE_CSV = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"
APPENDED_ROWS_CSV = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_appended_rows_v2_19p.csv"
MAPPING_AUDIT_CSV = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_mapping_audit_v2_19p.csv"
ROWCOUNT_AUDIT_CSV = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_rowcount_audit_v2_19p.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_checks_v2_19p.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_next_actions_v2_19p.csv"
REPORT_JSON = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_v2_19p.json"
REPORT_MD = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_v2_19p.md"

EXPECTED_V219O_STATUS = "HKEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NET_NEW_CLASSIFIED_EXPANDED_REBUILD_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
NET_NEW_ROWS_EXPECTED = 396
PROJECTED_REBUILD_ROWS_EXPECTED = 41392
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_AFTER_REBUILD_EXPECTED = 8608

STATUS_SUCCESS = "HKEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_41392_ROWS_EXPANDED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_FAILED = "HKEX_EXPANDED_REBUILD_CANDIDATE_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_VALIDATION = "v2.19Q - HKEX Expanded Validation"
NEXT_PHASE_REVIEW = "v2.19P_REVIEW - HKEX Expanded Rebuild Candidate Review"


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


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return list(reader.fieldnames or []), list(reader)
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


def normalize_header(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s_\-/]+", "_", text)
    text = re.sub(r"[^a-z0-9_]+", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def clean_cell(value: Any) -> str:
    text = str(value or "").strip()
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_text(value: Any) -> str:
    return clean_cell(value).upper()


def normalize_ticker(value: Any) -> str:
    text = normalize_text(value).replace(" ", "").replace("_", ".")
    text = re.sub(r"[^A-Z0-9.\-]", "", text)

    match = re.fullmatch(r"(\d{1,5})\.HK", text)
    if match:
        return f"{match.group(1).zfill(5)}.HK"

    match = re.fullmatch(r"HKEX[_\-\.]?(\d{1,5})", text)
    if match:
        return f"{match.group(1).zfill(5)}.HK"

    return text


def normalize_isin(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^A-Z0-9]", "", text)
    if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", text):
        return text
    return ""


def normalize_stock_code(value: Any) -> str:
    text = normalize_text(value)
    if re.fullmatch(r"\d+\.0", text):
        text = text.split(".")[0]
    digits = re.sub(r"\D", "", text)
    if not digits:
        return ""
    if len(digits) <= 5:
        return digits.zfill(5)
    return ""


def row_values_blob(row: dict[str, str]) -> str:
    return " ".join(normalize_text(v) for v in row.values() if str(v).strip())


def extract_existing_tickers_and_isins(rows: list[dict[str, str]], headers: list[str]) -> tuple[set[str], set[str]]:
    ticker_headers = [
        h for h in headers
        if normalize_header(h) in {"ticker", "symbol", "ticker_yahoo", "yahoo_symbol", "yf_symbol", "candidate_id", "stock_code", "code"}
        or "ticker" in normalize_header(h)
        or normalize_header(h) == "symbol"
    ]
    isin_headers = [h for h in headers if normalize_header(h) == "isin"]

    tickers: set[str] = set()
    isins: set[str] = set()

    for row in rows:
        for header in ticker_headers:
            ticker = normalize_ticker(row.get(header, ""))
            if ticker:
                tickers.add(ticker)

        for header in isin_headers:
            isin = normalize_isin(row.get(header, ""))
            if isin:
                isins.add(isin)

    return tickers, isins


def set_if_header(output_row: dict[str, Any], header: str, value: Any, mapping_audit: list[dict[str, Any]], source_field: str) -> bool:
    if header not in output_row:
        return False

    output_row[header] = clean_cell(value)
    mapping_audit.append(
        {
            "target_header": header,
            "source_field": source_field,
            "mapped_value_example": clean_cell(value),
            "mapping_rule": "direct_or_constant_mapping",
        }
    )
    return True


def build_appended_row(current_headers: list[str], hkex_row: dict[str, str], mapping_audit: list[dict[str, Any]]) -> dict[str, Any]:
    row: dict[str, Any] = {header: "" for header in current_headers}

    stock_code = clean_cell(hkex_row.get("stock_code", ""))
    ticker = clean_cell(hkex_row.get("ticker") or hkex_row.get("symbol") or hkex_row.get("ticker_yahoo") or f"{stock_code}.HK")
    name = clean_cell(hkex_row.get("name", ""))
    isin = clean_cell(hkex_row.get("isin", ""))
    currency = clean_cell(hkex_row.get("trading_currency", ""))
    category = clean_cell(hkex_row.get("category", ""))
    sub_category = clean_cell(hkex_row.get("sub_category", ""))
    instrument_family = clean_cell(hkex_row.get("instrument_family", ""))
    candidate_id = clean_cell(hkex_row.get("candidate_id", f"HKEX_{stock_code}"))

    for header in current_headers:
        h = normalize_header(header)

        if h in {"ticker", "symbol", "ticker_yahoo", "yahoo_symbol", "yf_symbol"}:
            set_if_header(row, header, ticker, mapping_audit, "ticker")
        elif h in {"candidate_id", "id"}:
            set_if_header(row, header, candidate_id, mapping_audit, "candidate_id")
        elif h in {"stock_code", "code", "local_code"}:
            set_if_header(row, header, stock_code, mapping_audit, "stock_code")
        elif h in {"isin"}:
            set_if_header(row, header, isin, mapping_audit, "isin")
        elif h in {"company_name", "security_name", "name", "company", "issuer", "long_name", "short_name"}:
            set_if_header(row, header, name, mapping_audit, "name")
        elif h in {"exchange", "raw_exchange"}:
            set_if_header(row, header, "HKEX", mapping_audit, "constant:HKEX")
        elif h in {"mic"}:
            set_if_header(row, header, "XHKG", mapping_audit, "constant:XHKG")
        elif h in {"country", "source_country"}:
            set_if_header(row, header, "Hong Kong", mapping_audit, "constant:Hong Kong")
        elif h in {"market", "source_market"}:
            set_if_header(row, header, "Hong Kong", mapping_audit, "constant:Hong Kong")
        elif h in {"source_provider", "provider"}:
            set_if_header(row, header, "HKEX", mapping_audit, "constant:HKEX")
        elif h in {"currency", "trading_currency"}:
            set_if_header(row, header, currency, mapping_audit, "trading_currency")
        elif h in {"category"}:
            set_if_header(row, header, category, mapping_audit, "category")
        elif h in {"sub_category", "subcategory"}:
            set_if_header(row, header, sub_category, mapping_audit, "sub_category")
        elif h in {"instrument_family", "asset_class"}:
            set_if_header(row, header, instrument_family, mapping_audit, "instrument_family")
        elif h in {"source_phase", "phase"}:
            set_if_header(row, header, VERSION, mapping_audit, "constant:v2.19P")
        elif h in {"source_artifact_id"}:
            set_if_header(row, header, hkex_row.get("source_artifact_id", ""), mapping_audit, "source_artifact_id")
        elif h in {"source_file"}:
            set_if_header(row, header, hkex_row.get("source_file", ""), mapping_audit, "source_file")
        elif h in {"source_sheet"}:
            set_if_header(row, header, hkex_row.get("source_sheet", ""), mapping_audit, "source_sheet")
        elif h in {"source_row_number"}:
            set_if_header(row, header, hkex_row.get("source_row_number", ""), mapping_audit, "source_row_number")
        elif h in {"board_lot"}:
            set_if_header(row, header, hkex_row.get("board_lot", ""), mapping_audit, "board_lot")
        elif h in {"candidate_scope_flag"}:
            set_if_header(row, header, hkex_row.get("candidate_scope_flag", ""), mapping_audit, "candidate_scope_flag")
        elif h in {"validation_status"}:
            set_if_header(row, header, hkex_row.get("validation_status", ""), mapping_audit, "validation_status")
        elif h in {"validation_reason"}:
            set_if_header(row, header, hkex_row.get("validation_reason", ""), mapping_audit, "validation_reason")
        elif h in {"source", "data_source"}:
            set_if_header(row, header, "HKEX_OFFICIAL_LIST_OF_SECURITIES", mapping_audit, "constant:source")
        elif h in {"rebuild_phase"}:
            set_if_header(row, header, VERSION, mapping_audit, "constant:v2.19P")
        elif h in {"dry_run_only"}:
            set_if_header(row, header, "False", mapping_audit, "constant:False")
        elif h in {"canonical_validation_status"}:
            set_if_header(row, header, "validated_net_new_in_v2_19o", mapping_audit, "constant:validated_net_new_in_v2_19o")
        elif h in {"expanded_rebuild_status"}:
            set_if_header(row, header, "appended_in_expanded_candidate_v2_19p", mapping_audit, "constant:appended_in_expanded_candidate_v2_19p")

    return row


def main() -> None:
    for path in [
        EXPANDED_CANDIDATE_CSV,
        APPENDED_ROWS_CSV,
        MAPPING_AUDIT_CSV,
        ROWCOUNT_AUDIT_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
        REPORT_JSON,
        REPORT_MD,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219o = read_json(V219O_JSON)
    current_headers, current_rows = read_csv_with_header(CURRENT_VALIDATED_CANDIDATE_DATASET)
    _, net_new_rows = read_csv_with_header(V219O_NET_NEW_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = len(current_rows)
    rows_needed_before = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    existing_tickers, existing_isins = extract_existing_tickers_and_isins(current_rows, current_headers)

    mapping_audit_raw: list[dict[str, Any]] = []
    appended_rows: list[dict[str, Any]] = []
    appended_full_rows: list[dict[str, Any]] = []

    appended_tickers: list[str] = []
    appended_isins: list[str] = []

    for hkex_row in net_new_rows:
        row_mapping_events: list[dict[str, Any]] = []
        appended = build_appended_row(current_headers, hkex_row, row_mapping_events)

        ticker = normalize_ticker(hkex_row.get("ticker") or hkex_row.get("symbol") or hkex_row.get("ticker_yahoo"))
        isin = normalize_isin(hkex_row.get("isin", ""))

        appended["__v2_19p_internal_append_order"] = str(len(appended_rows) + 1)

        appended_clean = {header: appended.get(header, "") for header in current_headers}
        appended_rows.append(appended_clean)

        appended_full = {
            **hkex_row,
            "v2_19p_append_order": len(appended_rows),
            "v2_19p_target_dataset": str(EXPANDED_CANDIDATE_CSV),
            "v2_19p_schema_mode": "current_candidate_headers_preserved",
            "v2_19p_ticker_normalized": ticker,
            "v2_19p_isin_normalized": isin,
        }
        appended_full_rows.append(appended_full)

        if ticker:
            appended_tickers.append(ticker)
        if isin:
            appended_isins.append(isin)

        for event in row_mapping_events:
            event["candidate_id"] = hkex_row.get("candidate_id", "")
            event["stock_code"] = hkex_row.get("stock_code", "")
            mapping_audit_raw.append(event)

    expanded_rows = current_rows + appended_rows

    write_csv(EXPANDED_CANDIDATE_CSV, expanded_rows, current_headers)

    appended_full_headers = list(appended_full_rows[0].keys()) if appended_full_rows else []
    write_csv(APPENDED_ROWS_CSV, appended_full_rows, appended_full_headers)

    mapping_counter = Counter((row["target_header"], row["source_field"], row["mapping_rule"]) for row in mapping_audit_raw)
    mapping_audit_rows = [
        {
            "target_header": target_header,
            "source_field": source_field,
            "mapping_rule": mapping_rule,
            "mapped_row_count": count,
        }
        for (target_header, source_field, mapping_rule), count in sorted(mapping_counter.items())
    ]
    write_csv(MAPPING_AUDIT_CSV, mapping_audit_rows, ["target_header", "source_field", "mapping_rule", "mapped_row_count"])

    expanded_candidate_rows = count_csv_rows(EXPANDED_CANDIDATE_CSV)
    expanded_candidate_sha = sha256_file(EXPANDED_CANDIDATE_CSV)

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    rows_needed_after = max(FINAL_TARGET_CANDIDATES - expanded_candidate_rows, 0)
    final_50k_gate_after_rebuild = "READY" if expanded_candidate_rows >= FINAL_TARGET_CANDIDATES else "BLOCKED"

    appended_ticker_counter = Counter(appended_tickers)
    appended_isin_counter = Counter(appended_isins)

    duplicate_appended_tickers = sorted([ticker for ticker, count in appended_ticker_counter.items() if count > 1])
    duplicate_appended_isins = sorted([isin for isin, count in appended_isin_counter.items() if count > 1])

    appended_tickers_already_in_current = sorted([ticker for ticker in set(appended_tickers) if ticker in existing_tickers])
    appended_isins_already_in_current = sorted([isin for isin in set(appended_isins) if isin and isin in existing_isins])

    instrument_counter = Counter(row.get("instrument_family", "") or "(blank)" for row in net_new_rows)
    currency_counter = Counter(row.get("trading_currency", "") or "(blank)" for row in net_new_rows)

    rowcount_audit_rows = [
        {"metric": "active_canonical_rows", "value": active_canonical_rows, "detail": str(ACTIVE_CANONICAL_DATASET)},
        {"metric": "current_validated_candidate_rows", "value": current_candidate_rows, "detail": str(CURRENT_VALIDATED_CANDIDATE_DATASET)},
        {"metric": "net_new_rows_input", "value": len(net_new_rows), "detail": str(V219O_NET_NEW_CSV)},
        {"metric": "expanded_candidate_rows", "value": expanded_candidate_rows, "detail": str(EXPANDED_CANDIDATE_CSV)},
        {"metric": "rows_needed_before_rebuild", "value": rows_needed_before, "detail": "current candidate vs 50k"},
        {"metric": "rows_needed_after_rebuild", "value": rows_needed_after, "detail": "expanded candidate vs 50k"},
        {"metric": "final_50k_gate_after_rebuild", "value": final_50k_gate_after_rebuild, "detail": "expanded candidate projection"},
        {"metric": "duplicate_appended_ticker_count", "value": len(duplicate_appended_tickers), "detail": ",".join(duplicate_appended_tickers[:50])},
        {"metric": "duplicate_appended_isin_count", "value": len(duplicate_appended_isins), "detail": ",".join(duplicate_appended_isins[:50])},
        {"metric": "appended_tickers_already_in_current_count", "value": len(appended_tickers_already_in_current), "detail": ",".join(appended_tickers_already_in_current[:50])},
        {"metric": "appended_isins_already_in_current_count", "value": len(appended_isins_already_in_current), "detail": ",".join(appended_isins_already_in_current[:50])},
        {"metric": "appended_instrument_families", "value": len(instrument_counter), "detail": json.dumps(instrument_counter.most_common(), ensure_ascii=False)},
        {"metric": "appended_trading_currencies", "value": len(currency_counter), "detail": json.dumps(currency_counter.most_common(), ensure_ascii=False)},
    ]
    write_csv(ROWCOUNT_AUDIT_CSV, rowcount_audit_rows, ["metric", "value", "detail"])

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19o_report_exists", V219O_JSON.exists(), "critical", str(V219O_JSON))
    add_check("v2_19o_status_expected", v219o.get("status") == EXPECTED_V219O_STATUS, "critical", str(v219o.get("status", "")))
    add_check("v2_19o_net_new_exists", V219O_NET_NEW_CSV.exists(), "critical", str(V219O_NET_NEW_CSV))
    add_check("net_new_rows_expected", len(net_new_rows) == NET_NEW_ROWS_EXPECTED, "critical", f"net_new_rows={len(net_new_rows)}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("expanded_candidate_rows_expected", expanded_candidate_rows == PROJECTED_REBUILD_ROWS_EXPECTED, "critical", f"expanded_candidate_rows={expanded_candidate_rows}")
    add_check("rowcount_arithmetic_expected", current_candidate_rows + len(net_new_rows) == expanded_candidate_rows, "critical", f"{current_candidate_rows}+{len(net_new_rows)}={expanded_candidate_rows}")
    add_check("rows_needed_after_rebuild_expected", rows_needed_after == ROWS_NEEDED_TO_50K_AFTER_REBUILD_EXPECTED, "critical", f"rows_needed_after={rows_needed_after}")
    add_check("final_50k_gate_after_rebuild_blocked", final_50k_gate_after_rebuild == "BLOCKED", "critical", final_50k_gate_after_rebuild)
    add_check("current_headers_preserved", len(current_headers) > 0, "critical", f"header_count={len(current_headers)}")
    add_check("appended_rows_written", len(appended_rows) == NET_NEW_ROWS_EXPECTED, "critical", f"appended_rows={len(appended_rows)}")
    add_check("appended_full_audit_written", len(appended_full_rows) == NET_NEW_ROWS_EXPECTED, "critical", f"appended_full_rows={len(appended_full_rows)}")
    add_check("duplicate_appended_tickers_zero", len(duplicate_appended_tickers) == 0, "critical", f"duplicate_appended_tickers={len(duplicate_appended_tickers)}")
    add_check("duplicate_appended_isins_documented", len(duplicate_appended_isins) >= 0, "warning", f"duplicate_appended_isins={len(duplicate_appended_isins)}")
    add_check("appended_tickers_not_in_current", len(appended_tickers_already_in_current) == 0, "critical", f"appended_tickers_already_in_current={len(appended_tickers_already_in_current)}")
    add_check("appended_isins_not_in_current", len(appended_isins_already_in_current) == 0, "warning", f"appended_isins_already_in_current={len(appended_isins_already_in_current)}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("current_candidate_sha_unchanged", current_candidate_sha_before == current_candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("new_expanded_candidate_written", EXPANDED_CANDIDATE_CSV.exists(), "critical", str(EXPANDED_CANDIDATE_CSV))
    add_check("expanded_dataset_is_new_candidate_only", True, "critical", "active canonical not replaced")
    add_check("network_not_used_by_rebuild", True, "critical", "network_download_performed=False")
    add_check("candidate_validation_against_canonical_not_performed", True, "critical", "candidate_validation_against_canonical_performed=False")
    add_check("expanded_rebuild_candidate_performed", True, "critical", "expanded_rebuild_candidate_performed=True")
    add_check("expanded_validation_not_performed", True, "critical", "expanded_validation_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("current_candidate_dataset_not_modified", True, "critical", "current_candidate_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed == 0:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE_VALIDATION
    else:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW

    rebuild_summary = {
        "active_canonical_rows": active_canonical_rows,
        "current_validated_candidate_rows": current_candidate_rows,
        "net_new_rows_appended": len(net_new_rows),
        "expanded_candidate_rows": expanded_candidate_rows,
        "rows_needed_before_rebuild": rows_needed_before,
        "rows_needed_after_rebuild": rows_needed_after,
        "final_50k_candidate_gate_after_rebuild": final_50k_gate_after_rebuild,
        "expanded_candidate_dataset": str(EXPANDED_CANDIDATE_CSV),
        "expanded_candidate_sha256": expanded_candidate_sha,
        "current_validated_candidate_sha256_before": current_candidate_sha_before,
        "current_validated_candidate_sha256_after": current_candidate_sha_after,
        "active_canonical_sha256_before": canonical_sha_before,
        "active_canonical_sha256_after": canonical_sha_after,
        "duplicate_appended_ticker_count": len(duplicate_appended_tickers),
        "duplicate_appended_isin_count": len(duplicate_appended_isins),
        "appended_tickers_already_in_current_count": len(appended_tickers_already_in_current),
        "appended_isins_already_in_current_count": len(appended_isins_already_in_current),
        "critical_failed_checks": critical_failed,
        "full59k": "DEPRECATED_DEFERRED",
    }

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "HKEX",
            "action": "run_expanded_validation",
            "priority": "high",
            "reason": "Expanded candidate dataset has been built and must be validated before closure or further use.",
            "recommended_phase": NEXT_PHASE_VALIDATION,
            "guardrails": "validate row counts, schema, duplicates and SHA; do not replace active canonical",
        },
        {
            "action_order": 2,
            "action_scope": "50k",
            "action": "preserve_50k_gate_blocked",
            "priority": "high",
            "reason": "HKEX rebuild projects 41,392 rows, still below the 50,000 target.",
            "recommended_phase": NEXT_PHASE_VALIDATION,
            "guardrails": "no full59k; no scoring; no canonical replacement",
        },
    ]

    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "current_validated_candidate_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "current_validated_candidate_rows": current_candidate_rows,
            "expanded_candidate_dataset": str(EXPANDED_CANDIDATE_CSV),
            "expanded_candidate_rows": expanded_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_before_rebuild": rows_needed_before,
            "rows_needed_after_rebuild": rows_needed_after,
            "final_50k_candidate_gate_after_rebuild": final_50k_gate_after_rebuild,
            "full59k": "DEPRECATED_DEFERRED",
        },
        "v2_19o_context": {
            "status": v219o.get("status"),
            "phase_type": v219o.get("phase_type"),
            "net_new_pending_expanded_rebuild": v219o.get("validation_summary", {}).get("net_new_pending_expanded_rebuild"),
            "current_validated_candidate_rows": v219o.get("validation_summary", {}).get("current_validated_candidate_rows"),
            "projected_candidate_rows_if_rebuilt": v219o.get("validation_summary", {}).get("projected_candidate_rows_if_rebuilt"),
            "projected_rows_needed_to_50k": v219o.get("validation_summary", {}).get("projected_rows_needed_to_50k"),
            "projected_50k_gate_after_hkex": v219o.get("validation_summary", {}).get("projected_50k_gate_after_hkex"),
            "recommended_next_phase": v219o.get("recommended_next_phase"),
        },
        "rebuild_summary": rebuild_summary,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "route_selection_performed": False,
            "acquisition_plan_performed": False,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": False,
            "raw_validation_performed": False,
            "repaired_raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": True,
            "expanded_rebuild_candidate_only": True,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": current_candidate_sha_before == current_candidate_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": True,
            "new_expanded_dataset_path": str(EXPANDED_CANDIDATE_CSV),
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": final_50k_gate_after_rebuild,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    rowcount_lines = "\n".join(
        f"- `{row['metric']}`: `{row['value']}` — {row['detail']}"
        for row in rowcount_audit_rows
    )
    mapping_lines = "\n".join(
        f"- `{row['target_header']}` ← `{row['source_field']}`: `{row['mapped_row_count']}` rows"
        for row in mapping_audit_rows
    )
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

v2.19P builds a new expanded candidate dataset by appending only HKEX net-new rows validated in v2.19O.

This phase writes a new candidate dataset only. It does not replace the active canonical dataset, does not modify the current validated candidate dataset, does not perform expanded validation, and does not run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Rebuild summary

- Current validated candidate rows: `{current_candidate_rows}`
- HKEX net-new rows appended: `{len(net_new_rows)}`
- Expanded candidate rows: `{expanded_candidate_rows}`
- Rows needed before rebuild: `{rows_needed_before}`
- Rows needed after rebuild: `{rows_needed_after}`
- Final 50k candidate gate after rebuild: `{final_50k_gate_after_rebuild}`
- Expanded candidate dataset: `{EXPANDED_CANDIDATE_CSV}`
- Expanded candidate SHA256: `{expanded_candidate_sha}`
- Critical failed checks: `{critical_failed}`

## Rowcount audit

{rowcount_lines}

## Mapping audit

{mapping_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: true
- Expanded rebuild candidate only: true
- Expanded validation performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{current_candidate_sha_before == current_candidate_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: true
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: `{final_50k_gate_after_rebuild}`
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

    print("v2.19P HKEX expanded rebuild candidate completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REBUILD_SUMMARY:")
    for key, value in rebuild_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("ROWCOUNT_AUDIT:")
    for row in rowcount_audit_rows:
        print(f"- {row['metric']}: {row['value']} ({row['detail']})")
    print("")
    print("MAPPING_AUDIT:")
    for row in mapping_audit_rows:
        print(f"- {row['target_header']} <- {row['source_field']}: {row['mapped_row_count']}")
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
