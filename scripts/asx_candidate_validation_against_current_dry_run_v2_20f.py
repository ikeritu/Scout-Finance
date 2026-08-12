from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20F"
PHASE = "ASX Candidate Validation Against Current Candidate Dry Run"
PHASE_TYPE = "candidate-validation-against-current-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
PRE_HKEX_CURRENT_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V220E_JSON = OUTPUT_DIR / "asx_candidate_extraction_dry_run_v2_20e.json"
ASX_INCLUDED_ROWS_CSV = OUTPUT_DIR / "asx_candidate_extraction_dry_run_included_rows_v2_20e.csv"
ASX_ALL_EXTRACTED_ROWS_CSV = OUTPUT_DIR / "asx_candidate_extraction_dry_run_rows_v2_20e.csv"

REPORT_JSON = OUTPUT_DIR / "asx_candidate_validation_against_current_dry_run_v2_20f.json"
REPORT_MD = OUTPUT_DIR / "asx_candidate_validation_against_current_dry_run_v2_20f.md"
VALIDATED_ROWS_CSV = OUTPUT_DIR / "asx_candidate_validation_rows_v2_20f.csv"
NET_NEW_CANDIDATES_CSV = OUTPUT_DIR / "asx_candidate_validation_net_new_candidates_v2_20f.csv"
DUPLICATE_CURRENT_ROWS_CSV = OUTPUT_DIR / "asx_candidate_validation_duplicate_current_rows_v2_20f.csv"
INTERNAL_DUPLICATE_ROWS_CSV = OUTPUT_DIR / "asx_candidate_validation_internal_duplicate_rows_v2_20f.csv"
REVIEW_ROWS_CSV = OUTPUT_DIR / "asx_candidate_validation_review_rows_v2_20f.csv"
VALIDATION_SUMMARY_CSV = OUTPUT_DIR / "asx_candidate_validation_summary_v2_20f.csv"
MATCH_TYPE_SUMMARY_CSV = OUTPUT_DIR / "asx_candidate_validation_match_type_summary_v2_20f.csv"
NET_NEW_SCOPE_SUMMARY_CSV = OUTPUT_DIR / "asx_candidate_validation_net_new_scope_summary_v2_20f.csv"
CURRENT_INDEX_PROFILE_CSV = OUTPUT_DIR / "asx_candidate_validation_current_index_profile_v2_20f.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_candidate_validation_checks_v2_20f.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_candidate_validation_next_actions_v2_20f.csv"

EXPECTED_V220E_STATUS = "ASX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_EXTRACTED_VALIDATION_DRY_RUN_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED = 40996
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED = 608
ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED = 3608
ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED = 8608

STATUS_SUCCESS = "ASX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NET_NEW_READY_REBUILD_CANDIDATE_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
STATUS_LOW_YIELD = "ASX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_LOW_NET_NEW_YIELD_REVIEW_REQUIRED_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_CANDIDATE_VALIDATION_DRY_RUN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20G - ASX Expanded Rebuild Candidate"
NEXT_PHASE_REVIEW = "v2.20F_REVIEW - ASX Candidate Validation Against Current Candidate Review"


VALIDATED_FIELDNAMES = [
    "source_phase",
    "provider",
    "asx_code",
    "ticker",
    "symbol",
    "name",
    "normalized_name",
    "isin",
    "security_group_code",
    "product_description",
    "instrument_class",
    "include_decision",
    "scope_confidence",
    "context_match",
    "last_price",
    "business_date",
    "validation_decision",
    "match_type",
    "match_detail",
    "matched_current_ticker",
    "matched_current_symbol",
    "matched_current_isin",
    "matched_current_name",
    "internal_duplicate_key",
    "internal_duplicate_rank",
    "passes_quality_scope",
    "eligible_for_rebuild",
    "source_file",
    "source_sheet",
    "source_excel_row_number",
]


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


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV artifact: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_ticker(value: Any) -> str:
    text = clean_text(value).upper()
    if not text:
        return ""

    text = text.replace(" ", "")
    text = re.sub(r"[^A-Z0-9\.\-]", "", text)

    # Normalize ASX short code into Yahoo-style .AX symbol for comparison.
    if re.fullmatch(r"[A-Z0-9]{3}", text):
        return f"{text}.AX"

    return text


def normalize_asx_code(value: Any) -> str:
    text = normalize_ticker(value)
    if text.endswith(".AX"):
        text = text[:-3]
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


def normalize_isin(value: Any) -> str:
    text = clean_text(value).upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


def normalize_name(value: Any) -> str:
    text = clean_text(value).upper()
    text = text.replace("&", " AND ")
    text = re.sub(r"\b(LIMITED|LTD|INC|PLC|CORP|CORPORATION|GROUP|HOLDINGS|HOLDING|THE)\b", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def choose_existing_column(columns: list[str], candidates: list[str]) -> str:
    lower_map = {col.lower(): col for col in columns}

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    for col in columns:
        col_l = col.lower()
        for candidate in candidates:
            c = candidate.lower()
            if c in col_l:
                return col

    return ""


def build_current_indexes(rows: list[dict[str, str]]) -> tuple[dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]], dict[str, Any]]:
    if not rows:
        return {}, {}, {}, {}

    columns = list(rows[0].keys())

    ticker_col = choose_existing_column(columns, ["ticker", "yahoo_ticker", "symbol", "asx_code", "code"])
    symbol_col = choose_existing_column(columns, ["symbol", "ticker", "yahoo_ticker"])
    isin_col = choose_existing_column(columns, ["isin", "isin_code", "security_isin"])
    name_col = choose_existing_column(columns, ["name", "company_name", "security_name", "issuer_name", "asset_name"])

    ticker_index: dict[str, list[dict[str, str]]] = defaultdict(list)
    isin_index: dict[str, list[dict[str, str]]] = defaultdict(list)
    name_index: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        possible_tickers = set()

        if ticker_col:
            possible_tickers.add(normalize_ticker(row.get(ticker_col, "")))
        if symbol_col:
            possible_tickers.add(normalize_ticker(row.get(symbol_col, "")))

        # Also index any obvious ticker-like columns if present.
        for col in columns:
            col_l = col.lower()
            if col_l in {"ticker", "symbol", "yahoo_ticker", "bbg_ticker", "ric"} or "ticker" in col_l or col_l.endswith("symbol"):
                possible_tickers.add(normalize_ticker(row.get(col, "")))

        for ticker in possible_tickers:
            if ticker:
                ticker_index[ticker].append(row)

        if isin_col:
            isin = normalize_isin(row.get(isin_col, ""))
            if isin:
                isin_index[isin].append(row)

        if name_col:
            name = normalize_name(row.get(name_col, ""))
            if name:
                name_index[name].append(row)

    profile = {
        "columns_detected": ";".join(columns),
        "ticker_column": ticker_col,
        "symbol_column": symbol_col,
        "isin_column": isin_col,
        "name_column": name_col,
        "ticker_index_keys": len(ticker_index),
        "isin_index_keys": len(isin_index),
        "name_index_keys": len(name_index),
        "rows_indexed": len(rows),
    }

    return ticker_index, isin_index, name_index, profile


def candidate_quality_rank(row: dict[str, str]) -> tuple[int, int, int, str]:
    instrument_class = row.get("instrument_class", "")
    scope_confidence = row.get("scope_confidence", "")
    context_match = truthy(row.get("context_match", ""))
    excel_row_text = clean_text(row.get("source_excel_row_number", ""))

    try:
        excel_row_number = int(float(excel_row_text)) if excel_row_text else 999999
    except ValueError:
        excel_row_number = 999999

    class_score = {
        "ordinary_equity": 100,
        "a_reit_equity_like": 90,
        "listed_investment_vehicle_conditional": 80,
        "ordinary_or_equity_like_unclassified": 70,
    }.get(instrument_class, 0)

    confidence_score = {
        "high": 30,
        "medium": 20,
        "low": 10,
    }.get(scope_confidence, 0)

    context_score = 10 if context_match else 0

    # Higher is better; lower excel row is better, so invert in sorted key later via negative row.
    return (class_score, confidence_score, context_score, f"{999999 - excel_row_number:06d}")


def internal_dedupe(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        ticker = normalize_ticker(row.get("ticker", ""))
        isin = normalize_isin(row.get("isin", ""))
        asx_code = normalize_asx_code(row.get("asx_code", ""))
        key = ticker or f"ISIN:{isin}" or f"ASX:{asx_code}" or f"ROW:{len(grouped)}"
        grouped[key].append(row)

    kept: list[dict[str, str]] = []
    dropped: list[dict[str, str]] = []

    for key, group in grouped.items():
        ranked = sorted(group, key=candidate_quality_rank, reverse=True)
        for rank, row in enumerate(ranked, start=1):
            row["_internal_duplicate_key"] = key
            row["_internal_duplicate_rank"] = str(rank)
            if rank == 1:
                kept.append(row)
            else:
                dropped.append(row)

    return kept, dropped


def get_current_match_detail(matches: list[dict[str, str]], col_candidates: list[str], fallback_value: str = "") -> str:
    if not matches:
        return ""

    columns = list(matches[0].keys())
    col = choose_existing_column(columns, col_candidates)

    values = []
    for row in matches[:3]:
        if col:
            values.append(clean_text(row.get(col, "")))
        else:
            values.append(fallback_value)

    return "|".join(value for value in values if value)


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        VALIDATED_ROWS_CSV,
        NET_NEW_CANDIDATES_CSV,
        DUPLICATE_CURRENT_ROWS_CSV,
        INTERNAL_DUPLICATE_ROWS_CSV,
        REVIEW_ROWS_CSV,
        VALIDATION_SUMMARY_CSV,
        MATCH_TYPE_SUMMARY_CSV,
        NET_NEW_SCOPE_SUMMARY_CSV,
        CURRENT_INDEX_PROFILE_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220e = read_json(V220E_JSON)
    asx_included_rows = read_csv_dicts(ASX_INCLUDED_ROWS_CSV)
    asx_all_extracted_rows = read_csv_dicts(ASX_ALL_EXTRACTED_ROWS_CSV)
    current_rows = read_csv_dicts(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_rows = count_csv_rows(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_before = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    rows_needed_to_quality_floor = max(QUALITY_FLOOR_TARGET - current_validated_candidate_rows, 0)
    rows_needed_to_quality_ceiling = max(QUALITY_CEILING_TARGET - current_validated_candidate_rows, 0)
    rows_needed_to_aspirational_50k = max(ASPIRATIONAL_TARGET - current_validated_candidate_rows, 0)

    ticker_index, isin_index, name_index, current_index_profile = build_current_indexes(current_rows)

    deduped_asx_rows, internal_duplicate_dropped_rows = internal_dedupe(asx_included_rows)

    validated_rows: list[dict[str, Any]] = []
    net_new_rows: list[dict[str, Any]] = []
    duplicate_current_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    internal_duplicate_rows: list[dict[str, Any]] = []

    for row in internal_duplicate_dropped_rows:
        ticker = normalize_ticker(row.get("ticker", ""))
        asx_code = normalize_asx_code(row.get("asx_code", ""))
        isin = normalize_isin(row.get("isin", ""))
        name = clean_text(row.get("name", ""))
        normalized_name = normalize_name(name)

        output = {
            **row,
            "source_phase": VERSION,
            "provider": "ASX",
            "asx_code": asx_code,
            "ticker": ticker,
            "symbol": ticker,
            "name": name,
            "normalized_name": normalized_name,
            "isin": isin,
            "validation_decision": "internal_duplicate_dropped",
            "match_type": "internal_duplicate",
            "match_detail": f"duplicate_key={row.get('_internal_duplicate_key', '')};rank={row.get('_internal_duplicate_rank', '')}",
            "matched_current_ticker": "",
            "matched_current_symbol": "",
            "matched_current_isin": "",
            "matched_current_name": "",
            "internal_duplicate_key": row.get("_internal_duplicate_key", ""),
            "internal_duplicate_rank": row.get("_internal_duplicate_rank", ""),
            "passes_quality_scope": False,
            "eligible_for_rebuild": False,
        }
        validated_rows.append(output)
        internal_duplicate_rows.append(output)

    for row in deduped_asx_rows:
        ticker = normalize_ticker(row.get("ticker", ""))
        symbol = normalize_ticker(row.get("symbol", "")) or ticker
        asx_code = normalize_asx_code(row.get("asx_code", ""))
        isin = normalize_isin(row.get("isin", ""))
        name = clean_text(row.get("name", ""))
        normalized_name = normalize_name(name)
        instrument_class = clean_text(row.get("instrument_class", ""))
        include_decision = clean_text(row.get("include_decision", ""))

        ticker_matches = []
        if ticker:
            ticker_matches.extend(ticker_index.get(ticker, []))
        if symbol and symbol != ticker:
            ticker_matches.extend(ticker_index.get(symbol, []))

        isin_matches = isin_index.get(isin, []) if isin else []
        name_matches = name_index.get(normalized_name, []) if normalized_name else []

        # Remove duplicate current match row object identities from combined detail.
        ticker_match_exists = len(ticker_matches) > 0
        isin_match_exists = len(isin_matches) > 0
        name_match_exists = len(name_matches) > 0

        passes_quality_scope = (
            include_decision in {"include_candidate", "include_conditional"}
            and instrument_class in {
                "ordinary_equity",
                "a_reit_equity_like",
                "listed_investment_vehicle_conditional",
                "ordinary_or_equity_like_unclassified",
            }
            and bool(ticker)
            and bool(asx_code)
            and len(asx_code) == 3
        )

        if ticker_match_exists or isin_match_exists:
            validation_decision = "duplicate_current"
            match_types = []
            if ticker_match_exists:
                match_types.append("ticker")
            if isin_match_exists:
                match_types.append("isin")
            match_type = "+".join(match_types)
            eligible_for_rebuild = False
        elif name_match_exists:
            validation_decision = "review_name_match_only"
            match_type = "name_only"
            eligible_for_rebuild = False
        elif not passes_quality_scope:
            validation_decision = "review_quality_scope"
            match_type = "scope_review"
            eligible_for_rebuild = False
        else:
            validation_decision = "net_new_candidate"
            match_type = "no_current_match"
            eligible_for_rebuild = True

        matched_current_ticker = get_current_match_detail(ticker_matches, ["ticker", "symbol", "yahoo_ticker"], ticker)
        matched_current_symbol = get_current_match_detail(ticker_matches, ["symbol", "ticker", "yahoo_ticker"], symbol)
        matched_current_isin = get_current_match_detail(isin_matches, ["isin", "isin_code"], isin)
        matched_current_name = get_current_match_detail(name_matches, ["name", "company_name", "security_name", "issuer_name"], name)

        match_detail_parts = [
            f"ticker_matches={len(ticker_matches)}",
            f"isin_matches={len(isin_matches)}",
            f"name_matches={len(name_matches)}",
        ]

        output = {
            **row,
            "source_phase": VERSION,
            "provider": "ASX",
            "asx_code": asx_code,
            "ticker": ticker,
            "symbol": symbol,
            "name": name,
            "normalized_name": normalized_name,
            "isin": isin,
            "validation_decision": validation_decision,
            "match_type": match_type,
            "match_detail": ";".join(match_detail_parts),
            "matched_current_ticker": matched_current_ticker,
            "matched_current_symbol": matched_current_symbol,
            "matched_current_isin": matched_current_isin,
            "matched_current_name": matched_current_name,
            "internal_duplicate_key": row.get("_internal_duplicate_key", ""),
            "internal_duplicate_rank": row.get("_internal_duplicate_rank", ""),
            "passes_quality_scope": passes_quality_scope,
            "eligible_for_rebuild": eligible_for_rebuild,
        }

        validated_rows.append(output)

        if validation_decision == "net_new_candidate":
            net_new_rows.append(output)
        elif validation_decision == "duplicate_current":
            duplicate_current_rows.append(output)
        else:
            review_rows.append(output)

    validation_decision_counts = Counter(row["validation_decision"] for row in validated_rows)
    match_type_counts = Counter(row["match_type"] for row in validated_rows)

    match_type_summary_rows = [
        {"match_type": match_type, "rows": count}
        for match_type, count in sorted(match_type_counts.items())
    ]

    net_new_scope_counter = Counter(row["instrument_class"] for row in net_new_rows)
    net_new_scope_summary_rows = [
        {"instrument_class": instrument_class, "rows": count}
        for instrument_class, count in sorted(net_new_scope_counter.items())
    ]

    validation_summary_rows = [
        {"metric": "current_validated_candidate_rows", "value": current_validated_candidate_rows},
        {"metric": "asx_all_extracted_rows", "value": len(asx_all_extracted_rows)},
        {"metric": "asx_included_rows_input", "value": len(asx_included_rows)},
        {"metric": "asx_deduped_rows_validated", "value": len(deduped_asx_rows)},
        {"metric": "internal_duplicate_rows_dropped", "value": len(internal_duplicate_rows)},
        {"metric": "duplicate_current_rows", "value": len(duplicate_current_rows)},
        {"metric": "review_rows", "value": len(review_rows)},
        {"metric": "net_new_candidate_rows", "value": len(net_new_rows)},
        {"metric": "rows_needed_to_quality_floor", "value": rows_needed_to_quality_floor},
        {"metric": "rows_needed_to_quality_ceiling", "value": rows_needed_to_quality_ceiling},
        {"metric": "net_new_covers_quality_floor_gap", "value": len(net_new_rows) >= rows_needed_to_quality_floor},
        {"metric": "post_asx_dry_run_candidate_rows_if_rebuilt_all_net_new", "value": current_validated_candidate_rows + len(net_new_rows)},
        {"metric": "would_exceed_quality_ceiling_if_rebuilt_all_net_new", "value": current_validated_candidate_rows + len(net_new_rows) > QUALITY_CEILING_TARGET},
    ]

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    pre_hkex_current_candidate_sha_after = sha256_file(PRE_HKEX_CURRENT_CANDIDATE_DATASET)
    current_validated_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    v220e_status = v220e.get("status", "")
    v220e_summary = v220e.get("extraction_summary", {})

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

    add_check("v2_20e_report_exists", V220E_JSON.exists(), "critical", str(V220E_JSON))
    add_check("v2_20e_status_expected", v220e_status == EXPECTED_V220E_STATUS, "critical", str(v220e_status))
    add_check("v2_20e_next_phase_expected", v220e.get("recommended_next_phase") == "v2.20F - ASX Candidate Validation Against Current Candidate Dry Run", "critical", str(v220e.get("recommended_next_phase")))
    add_check("v2_20e_included_rows_expected", int(v220e_summary.get("included_rows", -1)) == len(asx_included_rows), "critical", f"report={v220e_summary.get('included_rows')};csv={len(asx_included_rows)}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("pre_hkex_current_candidate_rows_expected", pre_hkex_current_candidate_rows == PRE_HKEX_CURRENT_CANDIDATE_ROWS_EXPECTED, "critical", f"pre_hkex_rows={pre_hkex_current_candidate_rows}")
    add_check("current_validated_candidate_rows_expected", current_validated_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_validated_rows={current_validated_candidate_rows}")
    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("pre_hkex_current_candidate_sha_expected", pre_hkex_current_candidate_sha_before == PRE_HKEX_CURRENT_CANDIDATE_SHA_EXPECTED, "critical", pre_hkex_current_candidate_sha_before)
    add_check("current_validated_candidate_sha_expected", current_validated_candidate_sha_before == CURRENT_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", current_validated_candidate_sha_before)
    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("pre_hkex_current_candidate_sha_unchanged", pre_hkex_current_candidate_sha_before == pre_hkex_current_candidate_sha_after, "critical", "pre-HKEX current candidate sha unchanged")
    add_check("current_validated_candidate_sha_unchanged", current_validated_candidate_sha_before == current_validated_candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("quality_floor_target_preserved", QUALITY_FLOOR_TARGET == 42000, "critical", f"quality_floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_target_preserved", QUALITY_CEILING_TARGET == 45000, "critical", f"quality_ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_needed_to_quality_floor_expected", rows_needed_to_quality_floor == ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED, "critical", f"rows_needed_to_42k={rows_needed_to_quality_floor}")
    add_check("rows_needed_to_quality_ceiling_expected", rows_needed_to_quality_ceiling == ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED, "critical", f"rows_needed_to_45k={rows_needed_to_quality_ceiling}")
    add_check("rows_needed_to_50k_aspirational_expected", rows_needed_to_aspirational_50k == ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_needed_to_50k={rows_needed_to_aspirational_50k}")
    add_check("current_candidate_index_loaded", len(current_rows) == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_rows={len(current_rows)}")
    add_check("current_ticker_index_non_empty", int(current_index_profile.get("ticker_index_keys", 0)) > 0, "critical", f"ticker_keys={current_index_profile.get('ticker_index_keys')}")
    add_check("current_isin_index_non_empty", int(current_index_profile.get("isin_index_keys", 0)) > 0, "warning", f"isin_keys={current_index_profile.get('isin_index_keys')}")
    add_check("asx_included_rows_loaded", len(asx_included_rows) > 0, "critical", f"asx_included_rows={len(asx_included_rows)}")
    add_check("internal_duplicates_documented", True, "warning", f"internal_duplicate_rows={len(internal_duplicate_rows)}")
    add_check("validated_rows_accounting", len(validated_rows) == len(asx_included_rows), "critical", f"validated={len(validated_rows)};input={len(asx_included_rows)}")
    add_check("net_new_rows_non_empty", len(net_new_rows) > 0, "critical", f"net_new_rows={len(net_new_rows)}")
    add_check("net_new_rows_cover_quality_floor_gap", len(net_new_rows) >= rows_needed_to_quality_floor, "warning", f"net_new={len(net_new_rows)};needed_to_42k={rows_needed_to_quality_floor}")
    add_check("duplicate_current_rows_documented", True, "warning", f"duplicate_current_rows={len(duplicate_current_rows)}")
    add_check("review_rows_documented", True, "warning", f"review_rows={len(review_rows)}")
    add_check("would_not_exceed_quality_ceiling_if_rebuilt_all_net_new", current_validated_candidate_rows + len(net_new_rows) <= QUALITY_CEILING_TARGET, "warning", f"post_rows={current_validated_candidate_rows + len(net_new_rows)};ceiling={QUALITY_CEILING_TARGET}")
    add_check("candidate_validation_dry_run_only", True, "critical", "candidate validation against current dry run only")
    add_check("network_download_not_performed", True, "critical", "network_download_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
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
    elif len(net_new_rows) < rows_needed_to_quality_floor:
        status = STATUS_LOW_YIELD
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE

    validation_summary = {
        "selected_provider": "ASX",
        "comparison_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
        "current_validated_candidate_rows": current_validated_candidate_rows,
        "asx_included_rows_input": len(asx_included_rows),
        "asx_deduped_rows_validated": len(deduped_asx_rows),
        "internal_duplicate_rows_dropped": len(internal_duplicate_rows),
        "duplicate_current_rows": len(duplicate_current_rows),
        "review_rows": len(review_rows),
        "net_new_candidate_rows": len(net_new_rows),
        "validation_decision_counts": dict(validation_decision_counts),
        "match_type_counts": dict(match_type_counts),
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_needed_to_quality_floor": rows_needed_to_quality_floor,
        "rows_needed_to_quality_ceiling": rows_needed_to_quality_ceiling,
        "rows_needed_to_aspirational_50k": rows_needed_to_aspirational_50k,
        "net_new_covers_quality_floor_gap": len(net_new_rows) >= rows_needed_to_quality_floor,
        "post_asx_dry_run_candidate_rows_if_rebuilt_all_net_new": current_validated_candidate_rows + len(net_new_rows),
        "would_exceed_quality_ceiling_if_rebuilt_all_net_new": current_validated_candidate_rows + len(net_new_rows) > QUALITY_CEILING_TARGET,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    if current_validated_candidate_rows + len(net_new_rows) > QUALITY_CEILING_TARGET:
        next_action_rebuild_scope = "cap_or_prioritize_net_new_rows_before_rebuild"
        next_action_reason = "All net-new ASX rows would exceed the 45k quality ceiling, so v2.20G must cap/prioritize before rebuild."
    else:
        next_action_rebuild_scope = "append_all_clean_net_new_rows_in_rebuild_candidate"
        next_action_reason = "Clean ASX net-new rows fit inside the 45k quality ceiling."

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "ASX",
            "action": next_action_rebuild_scope,
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": next_action_reason,
            "recommended_phase": recommended_next_phase,
            "guardrails": "rebuild candidate only; do not promote canonical; do not score; preserve 42k-45k band",
        },
        {
            "action_order": 2,
            "action_scope": "ASX_duplicates",
            "action": "exclude_current_duplicates_and_internal_duplicates",
            "priority": "high",
            "reason": "v2.20F identified duplicate-current and internal-duplicate rows; these must not be appended.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "only rows with validation_decision=net_new_candidate are eligible",
        },
        {
            "action_order": 3,
            "action_scope": "quality_target",
            "action": "preserve_42k_45k_operational_band",
            "priority": "high",
            "reason": "Goal is to cross 42k with good candidates, not chase 50k volume.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "50k aspirational only; full59k deprecated",
        },
    ]

    current_index_profile_rows = [
        {"metric": key, "value": value}
        for key, value in current_index_profile.items()
    ]

    write_csv(VALIDATED_ROWS_CSV, validated_rows, VALIDATED_FIELDNAMES)
    write_csv(NET_NEW_CANDIDATES_CSV, net_new_rows, VALIDATED_FIELDNAMES)
    write_csv(DUPLICATE_CURRENT_ROWS_CSV, duplicate_current_rows, VALIDATED_FIELDNAMES)
    write_csv(INTERNAL_DUPLICATE_ROWS_CSV, internal_duplicate_rows, VALIDATED_FIELDNAMES)
    write_csv(REVIEW_ROWS_CSV, review_rows, VALIDATED_FIELDNAMES)
    write_csv(VALIDATION_SUMMARY_CSV, validation_summary_rows, ["metric", "value"])
    write_csv(MATCH_TYPE_SUMMARY_CSV, match_type_summary_rows, ["match_type", "rows"])
    write_csv(NET_NEW_SCOPE_SUMMARY_CSV, net_new_scope_summary_rows, ["instrument_class", "rows"])
    write_csv(CURRENT_INDEX_PROFILE_CSV, current_index_profile_rows, ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "validation_summary": validation_summary,
        "current_index_profile": current_index_profile,
        "validation_decision_counts": dict(validation_decision_counts),
        "match_type_counts": dict(match_type_counts),
        "net_new_scope_summary": net_new_scope_summary_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "candidate_validation_against_current_dry_run_only": True,
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
            "candidate_validation_against_current_performed": True,
            "candidate_validation_against_current_dry_run": True,
            "expanded_rebuild_candidate_performed": False,
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
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
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

    decision_lines = "\n".join(
        f"- `{decision}`: `{count}`"
        for decision, count in sorted(validation_decision_counts.items())
    )

    match_lines = "\n".join(
        f"- `{match_type}`: `{count}`"
        for match_type, count in sorted(match_type_counts.items())
    )

    net_new_scope_lines = "\n".join(
        f"- `{row['instrument_class']}`: `{row['rows']}`"
        for row in net_new_scope_summary_rows
    ) or "- No net-new rows."

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

v2.20F validates the ASX included extraction rows against the current validated candidate dataset.

Comparison dataset:

`{CURRENT_VALIDATED_CANDIDATE_DATASET}`

This phase decides which ASX rows are internal duplicates, current-candidate duplicates, review rows, or clean net-new candidates.

This phase performs candidate validation dry run only. It does **not** append rows, does **not** rebuild an expanded candidate, does **not** promote canonical, and does **not** run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

Only rows with `validation_decision=net_new_candidate` are eligible for v2.20G rebuild consideration.

## Validation summary

- Current validated candidate rows: `{current_validated_candidate_rows}`
- ASX included rows input: `{len(asx_included_rows)}`
- ASX deduped rows validated: `{len(deduped_asx_rows)}`
- Internal duplicate rows dropped: `{len(internal_duplicate_rows)}`
- Duplicate-current rows: `{len(duplicate_current_rows)}`
- Review rows: `{len(review_rows)}`
- Net-new candidate rows: `{len(net_new_rows)}`
- Rows needed to 42k: `{rows_needed_to_quality_floor}`
- Rows needed to 45k: `{rows_needed_to_quality_ceiling}`
- Net-new covers quality floor gap: `{len(net_new_rows) >= rows_needed_to_quality_floor}`
- Post-ASX dry-run rows if all net-new rebuilt: `{current_validated_candidate_rows + len(net_new_rows)}`
- Would exceed 45k ceiling if all net-new rebuilt: `{current_validated_candidate_rows + len(net_new_rows) > QUALITY_CEILING_TARGET}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Validation decisions

{decision_lines}

## Match types

{match_lines}

## Net-new scope summary

{net_new_scope_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Candidate validation against current dry run only: true
- Network download performed: false
- Candidate extraction performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current validated candidate dataset modified: false
- Active canonical replaced: false
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

    print("v2.20F ASX candidate validation against current dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in validation_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_INDEX_PROFILE:")
    for key, value in current_index_profile.items():
        print(f"- {key}: {value}")
    print("")
    print("VALIDATION_DECISION_COUNTS:")
    for decision, count in sorted(validation_decision_counts.items()):
        print(f"- {decision}: {count}")
    print("")
    print("MATCH_TYPE_COUNTS:")
    for match_type, count in sorted(match_type_counts.items()):
        print(f"- {match_type}: {count}")
    print("")
    print("NET_NEW_SCOPE_SUMMARY:")
    for row in net_new_scope_summary_rows:
        print(f"- {row['instrument_class']}: {row['rows']}")
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
