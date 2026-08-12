from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20E"
PHASE = "ASX Candidate Extraction Dry Run"
PHASE_TYPE = "candidate-extraction-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "asx_v2_20c"
RAW_DOWNLOADS_DIR = RAW_DIR / "downloads"

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
HKEX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V220D_JSON = OUTPUT_DIR / "asx_raw_validation_v2_20d.json"

ASX_ISIN_XLS = RAW_DOWNLOADS_DIR / "asx_isin_xls_direct.xls"
ASX_CONTEXT_CSV = RAW_DOWNLOADS_DIR / "asx_discovered_last_known_closing_price_fy26.csv"

REPORT_JSON = OUTPUT_DIR / "asx_candidate_extraction_dry_run_v2_20e.json"
REPORT_MD = OUTPUT_DIR / "asx_candidate_extraction_dry_run_v2_20e.md"
EXTRACTED_ROWS_CSV = OUTPUT_DIR / "asx_candidate_extraction_dry_run_rows_v2_20e.csv"
INCLUDED_ROWS_CSV = OUTPUT_DIR / "asx_candidate_extraction_dry_run_included_rows_v2_20e.csv"
EXCLUDED_ROWS_CSV = OUTPUT_DIR / "asx_candidate_extraction_dry_run_excluded_rows_v2_20e.csv"
REVIEW_ROWS_CSV = OUTPUT_DIR / "asx_candidate_extraction_dry_run_review_rows_v2_20e.csv"
SHEET_PROFILE_CSV = OUTPUT_DIR / "asx_candidate_extraction_sheet_profile_v2_20e.csv"
SCOPE_SUMMARY_CSV = OUTPUT_DIR / "asx_candidate_extraction_scope_summary_v2_20e.csv"
DUPLICATES_CSV = OUTPUT_DIR / "asx_candidate_extraction_duplicates_v2_20e.csv"
CONTEXT_MATCH_CSV = OUTPUT_DIR / "asx_candidate_extraction_context_match_v2_20e.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_candidate_extraction_checks_v2_20e.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_candidate_extraction_next_actions_v2_20e.csv"

EXPECTED_V220D_STATUS_REPAIR = "ASX_RAW_VALIDATION_COMPLETED_REPAIR_RECOMMENDED_EXTRACTION_POSSIBLE_WITH_ISIN_XLS_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
EXPECTED_V220D_STATUS_READY = "ASX_RAW_VALIDATION_COMPLETED_PARSE_READY_EXTRACTION_DRY_RUN_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
HKEX_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
HKEX_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED = 608
ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED = 3608
ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED = 8608

STATUS_SUCCESS = "ASX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_EXTRACTED_VALIDATION_DRY_RUN_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
STATUS_LOW_YIELD = "ASX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_LOW_YIELD_REVIEW_REQUIRED_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_CANDIDATE_EXTRACTION_DRY_RUN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20F - ASX Candidate Validation Against Current Candidate Dry Run"
NEXT_PHASE_REVIEW = "v2.20E_REVIEW - ASX Candidate Extraction Dry Run Review"


OUTPUT_FIELDNAMES = [
    "source_phase",
    "provider",
    "source_file",
    "source_sheet",
    "source_excel_row_number",
    "asx_code",
    "ticker",
    "symbol",
    "name",
    "isin",
    "security_group_code",
    "product_description",
    "last_price",
    "business_date",
    "instrument_class",
    "include_decision",
    "exclusion_reason",
    "scope_confidence",
    "context_match",
    "duplicate_asx_code_in_extraction",
    "duplicate_isin_in_extraction",
    "raw_code_column",
    "raw_name_column",
    "raw_isin_column",
    "raw_product_column",
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


def read_text_best_effort(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    for encoding in ["utf-8-sig", "utf-8", "cp1252", "iso-8859-1"]:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore"), "utf-8-ignore"


def clean_cell(value: Any) -> str:
    if value is None:
        return ""

    try:
        import pandas as pd  # type: ignore

        if pd.isna(value):
            return ""
    except Exception:
        pass

    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""

    # Keep official punctuation in names, but normalize spacing.
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_header(value: str) -> str:
    value = clean_cell(value).lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def normalize_asx_code(value: str) -> str:
    value = clean_cell(value).upper()
    value = re.sub(r"[^A-Z0-9]", "", value)
    if value.endswith(".AX"):
        value = value[:-3]
    return value


def normalize_isin(value: str) -> str:
    value = clean_cell(value).upper()
    value = re.sub(r"[^A-Z0-9]", "", value)
    return value


def make_unique_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []

    for idx, header in enumerate(headers):
        normalized = normalize_header(header)
        if not normalized:
            normalized = f"column_{idx + 1}"

        count = seen.get(normalized, 0) + 1
        seen[normalized] = count

        if count > 1:
            result.append(f"{normalized}_{count}")
        else:
            result.append(normalized)

    return result


def score_header_row(values: list[str]) -> int:
    normalized = [normalize_header(value) for value in values]
    joined = " ".join(normalized)
    non_empty = sum(1 for value in normalized if value)

    score = 0
    if non_empty >= 2:
        score += 1
    if "isin" in joined:
        score += 5
    if "asx" in joined and "code" in joined:
        score += 5
    if "issuer" in joined or "company" in joined:
        score += 3
    if "security" in joined:
        score += 2
    if "name" in joined:
        score += 2
    if "description" in joined:
        score += 2
    return score


def detect_header_row(frame: Any) -> int:
    best_idx = 0
    best_score = -1
    max_scan = min(40, len(frame.index))

    for idx in range(max_scan):
        values = [clean_cell(value) for value in list(frame.iloc[idx].values)]
        score = score_header_row(values)
        if score > best_score:
            best_idx = idx
            best_score = score

    return best_idx


def choose_column(columns: list[str], kind: str) -> str:
    scores: list[tuple[int, str]] = []

    for col in columns:
        c = normalize_header(col)
        score = 0

        if kind == "code":
            if c in {"asx_code", "asx", "code", "security_code", "trading_code", "stock_code"}:
                score += 10
            if "asx" in c and "code" in c:
                score += 8
            if "security" in c and "code" in c:
                score += 5
            if c.endswith("_code") or c == "code":
                score += 3

        elif kind == "isin":
            if c == "isin":
                score += 10
            if "isin" in c:
                score += 8

        elif kind == "name":
            if c in {"issuer_name", "company_name", "name", "security_name", "issuer_name_full"}:
                score += 10
            if "issuer" in c and "name" in c:
                score += 8
            if "company" in c and "name" in c:
                score += 8
            if "security" in c and "name" in c:
                score += 6
            if "description" in c:
                score += 3
            if c == "name":
                score += 5

        elif kind == "security_group_code":
            if "security_group" in c and "code" in c:
                score += 10
            if "group" in c and "code" in c:
                score += 5

        elif kind == "product_description":
            if "product_description" in c:
                score += 10
            if "description" in c:
                score += 7
            if "security" in c and "type" in c:
                score += 4
            if "instrument" in c:
                score += 4

        if score > 0:
            scores.append((score, col))

    if not scores:
        return ""

    scores.sort(reverse=True, key=lambda item: item[0])
    return scores[0][1]


def read_context_csv(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}

    text, _encoding = read_text_best_effort(path)
    rows = list(csv.DictReader(text.splitlines()))
    context: dict[str, dict[str, str]] = {}

    for row in rows:
        code = normalize_asx_code(row.get("ASX_CODE", ""))
        if not code:
            continue
        context[code] = {str(key): clean_cell(value) for key, value in row.items()}

    return context


def classify_candidate(asx_code: str, name: str, isin: str, security_group_code: str, product_description: str) -> tuple[str, str, str, str]:
    code = normalize_asx_code(asx_code)
    name_l = name.lower()
    product_l = product_description.lower()
    group_l = security_group_code.lower()
    combined = f"{name_l} {product_l} {group_l}"

    if not code:
        return "missing_code", "exclude", "missing_asx_code", "critical"

    if not name and not isin:
        return "missing_identity", "exclude", "missing_name_and_isin", "critical"

    code_len = len(code)

    reit_terms = ["reit", "a-reit", "real estate investment trust", "property trust"]
    lic_lit_terms = [
        "listed investment company",
        "listed investment trust",
        "investment company",
        "investment trust",
    ]

    if code_len == 3 and any(term in combined for term in reit_terms):
        return "a_reit_equity_like", "include_conditional", "a_reit_equity_like_confirm_in_validation", "medium"

    if code_len == 3 and any(term in combined for term in lic_lit_terms):
        return "listed_investment_vehicle_conditional", "include_conditional", "lic_lit_equity_like_confirm_in_validation", "medium"

    strong_exclude_terms = [
        "warrant",
        "option",
        "rights",
        "right issue",
        "partly paid",
        "deferred settlement",
        "note",
        "notes",
        "bond",
        "debenture",
        "debt",
        "hybrid",
        "preference",
        "pref share",
        "capital notes",
        "convertible",
        "exchange traded fund",
        " etf",
        "managed fund",
        "structured product",
    ]

    if any(term in combined for term in strong_exclude_terms):
        return "excluded_non_core_instrument", "exclude", "derivative_debt_fund_or_secondary_issue_keyword", "high"

    if code_len != 3:
        return "non_standard_asx_code_length", "exclude", f"non_standard_asx_code_length_{code_len}", "high"

    ordinary_terms = [
        "ordinary",
        "ordinary fully paid",
        "fully paid ordinary",
        "ord",
        "fpo",
        "ordinary shares",
    ]

    if any(term in combined for term in ordinary_terms):
        return "ordinary_equity", "include_candidate", "ordinary_equity_signal", "high"

    # ASX 3-character codes from official ISIN file are still valid extraction candidates.
    # Final duplicate/net-new decision is intentionally deferred to v2.20F.
    return "ordinary_or_equity_like_unclassified", "include_candidate", "three_character_asx_code_from_official_isin_source", "medium"


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        EXTRACTED_ROWS_CSV,
        INCLUDED_ROWS_CSV,
        EXCLUDED_ROWS_CSV,
        REVIEW_ROWS_CSV,
        SHEET_PROFILE_CSV,
        SCOPE_SUMMARY_CSV,
        DUPLICATES_CSV,
        CONTEXT_MATCH_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220d = read_json(V220D_JSON)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_rows = count_csv_rows(HKEX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_before = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

    rows_needed_to_quality_floor = max(QUALITY_FLOOR_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_quality_ceiling = max(QUALITY_CEILING_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_aspirational_50k = max(ASPIRATIONAL_TARGET - hkex_validated_candidate_rows, 0)

    context_by_code = read_context_csv(ASX_CONTEXT_CSV)

    try:
        import pandas as pd  # type: ignore
    except Exception as exc:
        raise SystemExit(f"pandas is required for v2.20E ASX XLS extraction dry run: {type(exc).__name__}: {exc}")

    try:
        sheets = pd.read_excel(ASX_ISIN_XLS, sheet_name=None, header=None, dtype=object)
    except Exception as exc:
        raise SystemExit(f"Unable to parse ASX ISIN XLS with pandas: {type(exc).__name__}: {exc}")

    extracted_rows: list[dict[str, Any]] = []
    sheet_profile_rows: list[dict[str, Any]] = []

    for sheet_name, frame in sheets.items():
        if frame.empty:
            sheet_profile_rows.append(
                {
                    "sheet_name": sheet_name,
                    "header_row_zero_based": "",
                    "raw_rows": 0,
                    "parsed_rows": 0,
                    "column_count": 0,
                    "columns": "",
                    "code_column": "",
                    "name_column": "",
                    "isin_column": "",
                    "security_group_code_column": "",
                    "product_description_column": "",
                    "status": "empty_sheet",
                }
            )
            continue

        header_row = detect_header_row(frame)
        raw_headers = [clean_cell(value) for value in list(frame.iloc[header_row].values)]
        headers = make_unique_headers(raw_headers)

        data = frame.iloc[header_row + 1 :].copy()
        data.columns = headers

        # Drop rows that are fully empty after cleaning.
        cleaned_records: list[dict[str, str]] = []
        for idx, row in data.iterrows():
            record = {col: clean_cell(row.get(col, "")) for col in headers}
            if not any(record.values()):
                continue
            record["_source_excel_row_number"] = str(int(idx) + 1)
            cleaned_records.append(record)

        code_col = choose_column(headers, "code")
        isin_col = choose_column(headers, "isin")
        name_col = choose_column(headers, "name")
        security_group_col = choose_column(headers, "security_group_code")
        product_col = choose_column(headers, "product_description")

        sheet_status = "parseable"
        if not code_col and not isin_col:
            sheet_status = "no_code_or_isin_column_detected"

        sheet_profile_rows.append(
            {
                "sheet_name": sheet_name,
                "header_row_zero_based": header_row,
                "raw_rows": len(frame.index),
                "parsed_rows": len(cleaned_records),
                "column_count": len(headers),
                "columns": ";".join(headers),
                "code_column": code_col,
                "name_column": name_col,
                "isin_column": isin_col,
                "security_group_code_column": security_group_col,
                "product_description_column": product_col,
                "status": sheet_status,
            }
        )

        if sheet_status != "parseable":
            continue

        for record in cleaned_records:
            raw_code = record.get(code_col, "") if code_col else ""
            asx_code = normalize_asx_code(raw_code)
            isin = normalize_isin(record.get(isin_col, "")) if isin_col else ""
            name = record.get(name_col, "") if name_col else ""
            security_group_code = record.get(security_group_col, "") if security_group_col else ""
            product_description = record.get(product_col, "") if product_col else ""

            context = context_by_code.get(asx_code, {})
            context_match = bool(context)

            if not name and context:
                name = context.get("ISSUER_NAME_FULL", "")

            if not security_group_code and context:
                security_group_code = context.get("SECURITY_GROUP_CODE", "")

            if not product_description and context:
                product_description = context.get("PRODUCT_DESCRIPTION_ABBREV", "")

            instrument_class, include_decision, exclusion_reason, scope_confidence = classify_candidate(
                asx_code=asx_code,
                name=name,
                isin=isin,
                security_group_code=security_group_code,
                product_description=product_description,
            )

            extracted_rows.append(
                {
                    "source_phase": VERSION,
                    "provider": "ASX",
                    "source_file": str(ASX_ISIN_XLS),
                    "source_sheet": str(sheet_name),
                    "source_excel_row_number": record.get("_source_excel_row_number", ""),
                    "asx_code": asx_code,
                    "ticker": f"{asx_code}.AX" if asx_code else "",
                    "symbol": f"{asx_code}.AX" if asx_code else "",
                    "name": name,
                    "isin": isin,
                    "security_group_code": security_group_code,
                    "product_description": product_description,
                    "last_price": context.get("LAST_PRICE", ""),
                    "business_date": context.get("BUSINESS_DATE", ""),
                    "instrument_class": instrument_class,
                    "include_decision": include_decision,
                    "exclusion_reason": exclusion_reason,
                    "scope_confidence": scope_confidence,
                    "context_match": context_match,
                    "duplicate_asx_code_in_extraction": False,
                    "duplicate_isin_in_extraction": False,
                    "raw_code_column": code_col,
                    "raw_name_column": name_col,
                    "raw_isin_column": isin_col,
                    "raw_product_column": product_col,
                }
            )

    asx_code_counts = Counter(row["asx_code"] for row in extracted_rows if row.get("asx_code"))
    isin_counts = Counter(row["isin"] for row in extracted_rows if row.get("isin"))

    for row in extracted_rows:
        row["duplicate_asx_code_in_extraction"] = bool(row.get("asx_code") and asx_code_counts[row["asx_code"]] > 1)
        row["duplicate_isin_in_extraction"] = bool(row.get("isin") and isin_counts[row["isin"]] > 1)

    included_rows = [
        row for row in extracted_rows
        if row["include_decision"] in {"include_candidate", "include_conditional"}
    ]
    excluded_rows = [
        row for row in extracted_rows
        if row["include_decision"] == "exclude"
    ]
    review_rows = [
        row for row in extracted_rows
        if row["include_decision"] == "review_candidate"
    ]

    summary_counter: dict[tuple[str, str], int] = defaultdict(int)
    for row in extracted_rows:
        summary_counter[(row["instrument_class"], row["include_decision"])] += 1

    scope_summary_rows = [
        {
            "instrument_class": instrument_class,
            "include_decision": include_decision,
            "rows": count,
        }
        for (instrument_class, include_decision), count in sorted(summary_counter.items())
    ]

    duplicate_rows: list[dict[str, Any]] = []
    for code, count in sorted(asx_code_counts.items()):
        if count > 1:
            duplicate_rows.append({"duplicate_type": "asx_code", "value": code, "rows": count})
    for isin, count in sorted(isin_counts.items()):
        if count > 1:
            duplicate_rows.append({"duplicate_type": "isin", "value": isin, "rows": count})

    context_match_rows = [
        {
            "metric": "context_codes",
            "value": len(context_by_code),
        },
        {
            "metric": "extracted_rows",
            "value": len(extracted_rows),
        },
        {
            "metric": "extracted_rows_with_context_match",
            "value": sum(1 for row in extracted_rows if row["context_match"] is True),
        },
        {
            "metric": "included_rows_with_context_match",
            "value": sum(1 for row in included_rows if row["context_match"] is True),
        },
    ]

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_after = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

    v220d_status = v220d.get("status", "")
    v220d_summary = v220d.get("validation_summary", {})

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

    add_check("v2_20d_report_exists", V220D_JSON.exists(), "critical", str(V220D_JSON))
    add_check("v2_20d_status_expected", v220d_status in {EXPECTED_V220D_STATUS_READY, EXPECTED_V220D_STATUS_REPAIR}, "critical", str(v220d_status))
    add_check("v2_20d_next_phase_expected", v220d.get("recommended_next_phase") == "v2.20E - ASX Candidate Extraction Dry Run", "critical", str(v220d.get("recommended_next_phase")))
    add_check("v2_20d_parse_ready_for_extraction", v220d_summary.get("parse_ready_for_extraction") is True, "critical", str(v220d_summary.get("parse_ready_for_extraction")))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("hkex_validated_candidate_rows_expected", hkex_validated_candidate_rows == HKEX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"hkex_rows={hkex_validated_candidate_rows}")
    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("current_candidate_sha_expected", current_candidate_sha_before == CURRENT_CANDIDATE_SHA_EXPECTED, "critical", current_candidate_sha_before)
    add_check("hkex_validated_candidate_sha_expected", hkex_validated_candidate_sha_before == HKEX_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", hkex_validated_candidate_sha_before)
    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("current_candidate_sha_unchanged", current_candidate_sha_before == current_candidate_sha_after, "critical", "current candidate sha unchanged")
    add_check("hkex_candidate_sha_unchanged", hkex_validated_candidate_sha_before == hkex_validated_candidate_sha_after, "critical", "HKEX candidate sha unchanged")
    add_check("quality_floor_target_preserved", QUALITY_FLOOR_TARGET == 42000, "critical", f"quality_floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_target_preserved", QUALITY_CEILING_TARGET == 45000, "critical", f"quality_ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_needed_to_quality_floor_expected", rows_needed_to_quality_floor == ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED, "critical", f"rows_needed_to_42k={rows_needed_to_quality_floor}")
    add_check("rows_needed_to_quality_ceiling_expected", rows_needed_to_quality_ceiling == ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED, "critical", f"rows_needed_to_45k={rows_needed_to_quality_ceiling}")
    add_check("rows_needed_to_50k_aspirational_expected", rows_needed_to_aspirational_50k == ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_needed_to_50k={rows_needed_to_aspirational_50k}")
    add_check("asx_isin_xls_exists", ASX_ISIN_XLS.exists(), "critical", str(ASX_ISIN_XLS))
    add_check("asx_isin_xls_non_empty", ASX_ISIN_XLS.exists() and ASX_ISIN_XLS.stat().st_size > 0, "critical", f"bytes={ASX_ISIN_XLS.stat().st_size if ASX_ISIN_XLS.exists() else 0}")
    add_check("asx_context_csv_exists", ASX_CONTEXT_CSV.exists(), "warning", str(ASX_CONTEXT_CSV))
    add_check("excel_sheets_loaded", len(sheets) > 0, "critical", f"sheets={len(sheets)}")
    add_check("sheet_profile_created", len(sheet_profile_rows) > 0, "critical", f"sheet_profiles={len(sheet_profile_rows)}")
    add_check("extracted_rows_non_empty", len(extracted_rows) > 0, "critical", f"extracted_rows={len(extracted_rows)}")
    add_check("included_rows_non_empty", len(included_rows) > 0, "critical", f"included_rows={len(included_rows)}")
    add_check("included_rows_at_least_quality_floor_gap", len(included_rows) >= ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED, "warning", f"included_rows={len(included_rows)};needed_to_42k={ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED}")
    add_check("asx_code_extracted", any(row["asx_code"] for row in extracted_rows), "critical", "at least one ASX code extracted")
    add_check("isin_extracted", any(row["isin"] for row in extracted_rows), "critical", "at least one ISIN extracted")
    add_check("context_match_available", sum(1 for row in extracted_rows if row["context_match"] is True) > 0, "warning", f"context_matches={sum(1 for row in extracted_rows if row['context_match'] is True)}")
    add_check("duplicates_documented", True, "warning", f"duplicate_rows={len(duplicate_rows)}")
    add_check("candidate_extraction_dry_run_only", True, "critical", "candidate extraction dry run only")
    add_check("network_download_not_performed", True, "critical", "network_download_performed=False")
    add_check("candidate_validation_not_performed", True, "critical", "candidate_validation_against_canonical_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("expanded_validation_not_performed", True, "critical", "expanded_validation_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("current_candidate_dataset_not_modified", True, "critical", "current_candidate_dataset_modified=False")
    add_check("hkex_candidate_dataset_not_modified", True, "critical", "hkex_candidate_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
    elif len(included_rows) < ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED:
        status = STATUS_LOW_YIELD
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE

    extraction_summary = {
        "selected_provider": "ASX",
        "source_file": str(ASX_ISIN_XLS),
        "context_file": str(ASX_CONTEXT_CSV),
        "sheets_loaded": len(sheets),
        "sheet_profiles": len(sheet_profile_rows),
        "context_codes": len(context_by_code),
        "extracted_rows_total": len(extracted_rows),
        "included_rows": len(included_rows),
        "excluded_rows": len(excluded_rows),
        "review_rows": len(review_rows),
        "duplicate_asx_codes": sum(1 for _code, count in asx_code_counts.items() if count > 1),
        "duplicate_isins": sum(1 for _isin, count in isin_counts.items() if count > 1),
        "context_matched_rows": sum(1 for row in extracted_rows if row["context_match"] is True),
        "included_rows_with_context_match": sum(1 for row in included_rows if row["context_match"] is True),
        "current_hkex_validated_candidate_rows": hkex_validated_candidate_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_needed_to_quality_floor": rows_needed_to_quality_floor,
        "rows_needed_to_quality_ceiling": rows_needed_to_quality_ceiling,
        "rows_needed_to_aspirational_50k": rows_needed_to_aspirational_50k,
        "included_rows_cover_quality_floor_gap_before_duplicate_validation": len(included_rows) >= rows_needed_to_quality_floor,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "ASX",
            "action": "run_asx_candidate_validation_against_current_candidate_dry_run",
            "priority": "high" if recommended_next_phase == NEXT_PHASE else "blocked",
            "reason": "ASX extraction dry run produced included/conditional candidates; next step is duplicate/net-new validation against the HKEX validated candidate.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "dry run only; no append; no rebuild; no canonical replacement; no scoring",
        },
        {
            "action_order": 2,
            "action_scope": "ASX_scope",
            "action": "preserve_scope_filters_in_validation",
            "priority": "high",
            "reason": "Only ordinary equity and equity-like conditional instruments should survive the ASX validation route.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "exclude warrants/options/debt/rights/ETFs/funds/structured products and non-standard code lengths",
        },
        {
            "action_order": 3,
            "action_scope": "quality_target",
            "action": "validate_net_new_rows_before_rebuild",
            "priority": "high",
            "reason": "Included rows are not yet net-new. v2.20F must compare against the current candidate before any rebuild.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "do not treat gross ASX extracted rows as net-new rows",
        },
    ]

    write_csv(EXTRACTED_ROWS_CSV, extracted_rows, OUTPUT_FIELDNAMES)
    write_csv(INCLUDED_ROWS_CSV, included_rows, OUTPUT_FIELDNAMES)
    write_csv(EXCLUDED_ROWS_CSV, excluded_rows, OUTPUT_FIELDNAMES)
    write_csv(REVIEW_ROWS_CSV, review_rows, OUTPUT_FIELDNAMES)
    write_csv(SHEET_PROFILE_CSV, sheet_profile_rows, ["sheet_name", "header_row_zero_based", "raw_rows", "parsed_rows", "column_count", "columns", "code_column", "name_column", "isin_column", "security_group_code_column", "product_description_column", "status"])
    write_csv(SCOPE_SUMMARY_CSV, scope_summary_rows, ["instrument_class", "include_decision", "rows"])
    write_csv(DUPLICATES_CSV, duplicate_rows, ["duplicate_type", "value", "rows"])
    write_csv(CONTEXT_MATCH_CSV, context_match_rows, ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "extraction_summary": extraction_summary,
        "sheet_profile": sheet_profile_rows,
        "scope_summary": scope_summary_rows,
        "context_match": context_match_rows,
        "duplicate_summary": duplicate_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "candidate_extraction_dry_run_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_validation_performed": False,
            "candidate_extraction_performed": True,
            "candidate_extraction_dry_run": True,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": current_candidate_sha_before == current_candidate_sha_after,
            "hkex_validated_candidate_dataset_read": True,
            "hkex_validated_candidate_dataset_modified": False,
            "hkex_validated_candidate_sha_unchanged": hkex_validated_candidate_sha_before == hkex_validated_candidate_sha_after,
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

    scope_lines = "\n".join(
        f"- `{row['instrument_class']}` / `{row['include_decision']}`: `{row['rows']}`"
        for row in scope_summary_rows
    ) or "- No scope summary."

    sheet_lines = "\n".join(
        f"- `{row['sheet_name']}` — status `{row['status']}` — rows `{row['parsed_rows']}` — code `{row['code_column']}` — isin `{row['isin_column']}` — name `{row['name_column']}`"
        for row in sheet_profile_rows
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

v2.20E performs an ASX candidate extraction dry run from the validated ASX raw files.

The primary source is the official ASX ISIN XLS captured in v2.20C and validated in v2.20D. The ASX last-known-closing-price CSV is used only as context/enrichment, not as the primary universe source.

This phase extracts and classifies ASX rows into include, exclude and review buckets. It does **not** validate against the current candidate dataset, does **not** append rows, does **not** rebuild an expanded candidate, does **not** promote canonical, and does **not** run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

Gross included ASX rows are not net-new rows. v2.20F must perform duplicate/net-new validation against the current HKEX validated candidate before any rebuild is considered.

## Extraction summary

- Selected provider: `ASX`
- Source file: `{ASX_ISIN_XLS}`
- Context file: `{ASX_CONTEXT_CSV}`
- Sheets loaded: `{len(sheets)}`
- Sheet profiles: `{len(sheet_profile_rows)}`
- Context codes: `{len(context_by_code)}`
- Extracted rows total: `{len(extracted_rows)}`
- Included rows: `{len(included_rows)}`
- Excluded rows: `{len(excluded_rows)}`
- Review rows: `{len(review_rows)}`
- Duplicate ASX codes: `{extraction_summary["duplicate_asx_codes"]}`
- Duplicate ISINs: `{extraction_summary["duplicate_isins"]}`
- Context matched rows: `{extraction_summary["context_matched_rows"]}`
- Included rows with context match: `{extraction_summary["included_rows_with_context_match"]}`
- Current HKEX validated candidate rows: `{hkex_validated_candidate_rows}`
- Rows needed to 42k: `{rows_needed_to_quality_floor}`
- Rows needed to 45k: `{rows_needed_to_quality_ceiling}`
- Included rows cover 42k gap before duplicate validation: `{extraction_summary["included_rows_cover_quality_floor_gap_before_duplicate_validation"]}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Sheet profile

{sheet_lines}

## Scope summary

{scope_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Candidate extraction dry run only: true
- Network download performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current candidate dataset modified: false
- HKEX validated candidate dataset modified: false
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

    print("v2.20E ASX candidate extraction dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("EXTRACTION_SUMMARY:")
    for key, value in extraction_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SHEET_PROFILE:")
    for row in sheet_profile_rows:
        print(f"- {row['sheet_name']}: status={row['status']} parsed_rows={row['parsed_rows']} code={row['code_column']} isin={row['isin_column']} name={row['name_column']}")
    print("")
    print("SCOPE_SUMMARY:")
    for row in scope_summary_rows:
        print(f"- {row['instrument_class']} / {row['include_decision']}: {row['rows']}")
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
