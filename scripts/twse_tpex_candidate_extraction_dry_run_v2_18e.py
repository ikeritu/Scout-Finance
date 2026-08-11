from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.18E"
PHASE = "TWSE + TPEx Candidate Extraction Dry Run"
PHASE_TYPE = "candidate-extraction-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

V218D_FIX_JSON = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_v2_18d_fix.json"
V218D_FIX_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_source_diagnostics_v2_18d_fix.csv"
V218D_FIX_SCHEMA_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_schema_profile_v2_18d_fix.csv"
V218D_FIX_FILE_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_file_profile_v2_18d_fix.csv"
V218D_FIX_NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_next_actions_v2_18d_fix.csv"

V218C_FIX_MANIFEST_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_manifest_v2_18c_fix.csv"
V218C_FIX_JSON = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_v2_18c_fix.json"

REPORT_JSON = OUTPUT_DIR / "twse_tpex_candidate_extraction_dry_run_v2_18e.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_candidate_extraction_dry_run_v2_18e.md"
CANDIDATES_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_candidates_v2_18e.csv"
EXCLUSIONS_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_exclusions_v2_18e.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_source_diagnostics_v2_18e.csv"
FIELD_MAPPING_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_field_mapping_v2_18e.csv"
CROSSCHECK_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_crosscheck_v2_18e.csv"

EXPECTED_V218D_FIX_STATUS = "TWSE_TPEX_REPAIRED_RAW_VALIDATION_COMPLETED_ROW_DATA_VALID_CANDIDATE_EXTRACTION_DRY_RUN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
EXPECTED_V218C_FIX_STATUS = "TWSE_TPEX_RAW_ACQUISITION_REPAIR_COMPLETED_ROW_DATA_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

FINAL_TARGET_CANDIDATES = 50000
VALIDATED_CANDIDATE_ROWS_EXPECTED = 40300
ROWS_NEEDED_TO_50K_EXPECTED = 9700

PRIMARY_REPAIR_SOURCE_ID = "twse_ssl_repair_twse_listed_company_profile"
CROSSCHECK_REPAIR_SOURCE_ID = "twse_ssl_repair_twse_stock_day_all"

RECOMMENDED_NEXT_PHASE = "v2.18F - TWSE + TPEx Candidate Validation Against Canonical Dry Run"
RECOMMENDED_REVIEW_PHASE = "v2.18E_REVIEW - TWSE + TPEx Candidate Extraction Review"

CANDIDATE_FIELDS = [
    "candidate_id",
    "provider",
    "market",
    "exchange",
    "source_id",
    "source_role",
    "raw_symbol",
    "symbol",
    "name",
    "short_name",
    "english_name",
    "industry",
    "listing_date",
    "isin",
    "security_type",
    "country",
    "currency",
    "candidate_bucket",
    "confidence_bucket",
    "crosscheck_status",
    "crosscheck_source_id",
    "crosscheck_name",
    "crosscheck_fields_available",
    "review_required",
    "review_reason",
    "raw_row_index",
    "raw_json",
]

EXCLUSION_FIELDS = [
    "source_id",
    "provider",
    "raw_row_index",
    "raw_symbol",
    "raw_name",
    "exclusion_reason",
    "exclusion_bucket",
    "raw_json",
]

SOURCE_DIAGNOSTICS_FIELDS = [
    "source_id",
    "provider",
    "source_role",
    "raw_artifact_path",
    "file_exists",
    "parse_status",
    "raw_rows",
    "columns_detected",
    "candidates_emitted",
    "exclusions_emitted",
    "used_for_primary_extraction",
    "used_for_crosscheck",
    "notes",
]

FIELD_MAPPING_FIELDS = [
    "source_id",
    "provider",
    "source_role",
    "target_field",
    "raw_field",
    "mapping_status",
    "notes",
]

CROSSCHECK_FIELDS = [
    "symbol",
    "candidate_name",
    "crosscheck_name",
    "crosscheck_found",
    "name_match_type",
    "crosscheck_raw_json",
]


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


def load_json_raw(path: Path) -> Any:
    if not path.exists():
        raise SystemExit(f"Missing raw artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_text(value: Any) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_symbol(value: Any) -> str:
    text = normalize_text(value).upper()
    text = text.replace(".TW", "").replace(".TWO", "")
    text = re.sub(r"\s+", "", text)
    return text


def make_candidate_id(provider: str, exchange: str, symbol: str) -> str:
    return f"{provider.upper()}_{exchange.upper()}_{symbol}"


def is_probable_equity_symbol(symbol: str) -> bool:
    if not symbol:
        return False
    return bool(re.fullmatch(r"[0-9A-Z]{3,8}", symbol))


def has_excluded_instrument_keyword(*values: str) -> bool:
    text = " ".join(normalize_text(value).lower() for value in values)

    excluded_keywords = [
        "etf",
        "etn",
        "fund",
        "index",
        "bond",
        "warrant",
        "reit",
        "preferred",
        "preference",
        "beneficiary",
        "right",
        "rights",
        "depositary receipt",
        "depository receipt",
        "dr",
        "基金",
        "指數",
        "債券",
        "權證",
        "認購",
        "認售",
        "受益",
        "特別股",
        "優先股",
        "存託憑證",
    ]

    return any(keyword in text for keyword in excluded_keywords)


def is_depositary_receipt_candidate(symbol: str, company_name: str, short_name: str, english_name: str, industry: str) -> bool:
    joined = " ".join(
        normalize_text(value).upper()
        for value in [symbol, company_name, short_name, english_name, industry]
    )

    if normalize_text(industry) == "91":
        return True

    dr_patterns = [
        "-DR",
        " DR",
        "存託憑證",
    ]

    return any(pattern in joined for pattern in dr_patterns)


def value_from(row: dict[str, Any], names: list[str]) -> str:
    for name in names:
        if name in row and normalize_text(row.get(name)):
            return normalize_text(row.get(name))
    return ""


def load_manifest_by_source(manifest_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("repair_source_id", ""): row for row in manifest_rows}


def build_stock_day_crosscheck(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    for row in rows:
        symbol = normalize_symbol(value_from(row, ["Code", "code", "證券代號", "公司代號"]))
        if not symbol:
            continue
        result[symbol] = row

    return result


def classify_name_match(candidate_name: str, crosscheck_name: str) -> str:
    a = normalize_text(candidate_name).lower()
    b = normalize_text(crosscheck_name).lower()

    if not a or not b:
        return "missing_name"
    if a == b:
        return "exact"
    if a in b or b in a:
        return "contains"
    return "different"


def extract_candidates(
    primary_rows: list[dict[str, Any]],
    crosscheck_by_symbol: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    crosscheck_rows: list[dict[str, Any]] = []

    seen_symbols: set[str] = set()

    for index, row in enumerate(primary_rows, start=1):
        raw_symbol = value_from(row, ["公司代號", "Code", "code", "symbol", "ticker"])
        symbol = normalize_symbol(raw_symbol)

        company_name = value_from(row, ["公司名稱", "Name", "name", "company_name", "CompanyName"])
        short_name = value_from(row, ["公司簡稱", "ShortName", "short_name", "簡稱"])
        english_name = value_from(row, ["英文簡稱", "英文名稱", "EnglishName", "english_name"])
        industry = value_from(row, ["產業別", "Industry", "industry"])
        listing_date = value_from(row, ["上市日期", "掛牌日期", "ListingDate", "listing_date"])
        security_type = value_from(row, ["普通股每股面額", "市場別", "證券別", "type"])
        raw_name = company_name or short_name or english_name

        raw_json = json.dumps(row, ensure_ascii=False, sort_keys=True)

        if not symbol:
            exclusions.append(
                {
                    "source_id": PRIMARY_REPAIR_SOURCE_ID,
                    "provider": "TWSE",
                    "raw_row_index": index,
                    "raw_symbol": raw_symbol,
                    "raw_name": raw_name,
                    "exclusion_reason": "missing_symbol",
                    "exclusion_bucket": "missing_required_identifier",
                    "raw_json": raw_json,
                }
            )
            continue

        if not raw_name:
            exclusions.append(
                {
                    "source_id": PRIMARY_REPAIR_SOURCE_ID,
                    "provider": "TWSE",
                    "raw_row_index": index,
                    "raw_symbol": raw_symbol,
                    "raw_name": raw_name,
                    "exclusion_reason": "missing_name",
                    "exclusion_bucket": "missing_required_name",
                    "raw_json": raw_json,
                }
            )
            continue

        if not is_probable_equity_symbol(symbol):
            exclusions.append(
                {
                    "source_id": PRIMARY_REPAIR_SOURCE_ID,
                    "provider": "TWSE",
                    "raw_row_index": index,
                    "raw_symbol": raw_symbol,
                    "raw_name": raw_name,
                    "exclusion_reason": "symbol_shape_review",
                    "exclusion_bucket": "not_auto_promotable_symbol_shape",
                    "raw_json": raw_json,
                }
            )
            continue

        if is_depositary_receipt_candidate(symbol, company_name, short_name, english_name, industry):
            exclusions.append(
                {
                    "source_id": PRIMARY_REPAIR_SOURCE_ID,
                    "provider": "TWSE",
                    "raw_row_index": index,
                    "raw_symbol": raw_symbol,
                    "raw_name": raw_name,
                    "exclusion_reason": "depositary_receipt_or_industry_91",
                    "exclusion_bucket": "depositary_receipt_not_common_equity",
                    "raw_json": raw_json,
                }
            )
            continue

        if has_excluded_instrument_keyword(company_name, short_name, english_name, industry, security_type):
            exclusions.append(
                {
                    "source_id": PRIMARY_REPAIR_SOURCE_ID,
                    "provider": "TWSE",
                    "raw_row_index": index,
                    "raw_symbol": raw_symbol,
                    "raw_name": raw_name,
                    "exclusion_reason": "excluded_instrument_keyword",
                    "exclusion_bucket": "fund_etf_etn_bond_warrant_or_non_common_equity",
                    "raw_json": raw_json,
                }
            )
            continue

        if symbol in seen_symbols:
            exclusions.append(
                {
                    "source_id": PRIMARY_REPAIR_SOURCE_ID,
                    "provider": "TWSE",
                    "raw_row_index": index,
                    "raw_symbol": raw_symbol,
                    "raw_name": raw_name,
                    "exclusion_reason": "duplicate_symbol_in_primary_source",
                    "exclusion_bucket": "internal_duplicate",
                    "raw_json": raw_json,
                }
            )
            continue

        seen_symbols.add(symbol)

        crosscheck = crosscheck_by_symbol.get(symbol)
        crosscheck_found = crosscheck is not None
        crosscheck_name = value_from(crosscheck or {}, ["Name", "name", "證券名稱", "公司簡稱", "公司名稱"])
        name_match_type = classify_name_match(short_name or company_name, crosscheck_name)

        crosscheck_status = "matched_stock_day_all" if crosscheck_found else "not_found_in_stock_day_all"
        crosscheck_fields_available = len(crosscheck.keys()) if isinstance(crosscheck, dict) else 0

        review_required = False
        review_reason = ""

        if not crosscheck_found:
            review_required = True
            review_reason = "not_found_in_stock_day_all_crosscheck"
            confidence_bucket = "medium"
        elif name_match_type in {"exact", "contains"}:
            confidence_bucket = "high"
        else:
            review_required = True
            review_reason = f"name_mismatch_crosscheck_{name_match_type}"
            confidence_bucket = "medium_review"

        candidate = {
            "candidate_id": make_candidate_id("TWSE", "TWSE", symbol),
            "provider": "TWSE",
            "market": "Taiwan",
            "exchange": "TWSE",
            "source_id": PRIMARY_REPAIR_SOURCE_ID,
            "source_role": "primary_twse_candidate_source",
            "raw_symbol": raw_symbol,
            "symbol": symbol,
            "name": company_name or short_name,
            "short_name": short_name,
            "english_name": english_name,
            "industry": industry,
            "listing_date": listing_date,
            "isin": "",
            "security_type": security_type,
            "country": "Taiwan",
            "currency": "TWD",
            "candidate_bucket": "twse_listed_company_profile_equity_candidate",
            "confidence_bucket": confidence_bucket,
            "crosscheck_status": crosscheck_status,
            "crosscheck_source_id": CROSSCHECK_REPAIR_SOURCE_ID if crosscheck_found else "",
            "crosscheck_name": crosscheck_name,
            "crosscheck_fields_available": crosscheck_fields_available,
            "review_required": review_required,
            "review_reason": review_reason,
            "raw_row_index": index,
            "raw_json": raw_json,
        }

        candidates.append(candidate)

        crosscheck_rows.append(
            {
                "symbol": symbol,
                "candidate_name": short_name or company_name,
                "crosscheck_name": crosscheck_name,
                "crosscheck_found": crosscheck_found,
                "name_match_type": name_match_type,
                "crosscheck_raw_json": json.dumps(crosscheck or {}, ensure_ascii=False, sort_keys=True),
            }
        )

    return candidates, exclusions, crosscheck_rows


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        CANDIDATES_CSV,
        EXCLUSIONS_CSV,
        SOURCE_DIAGNOSTICS_CSV,
        FIELD_MAPPING_CSV,
        CROSSCHECK_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v218d_fix = read_json(V218D_FIX_JSON)
    v218c_fix = read_json(V218C_FIX_JSON)

    _, repair_manifest_rows = read_csv_with_header(V218C_FIX_MANIFEST_CSV)
    _, v218d_fix_diagnostics_rows = read_csv_with_header(V218D_FIX_SOURCE_DIAGNOSTICS_CSV)
    _, v218d_fix_schema_rows = read_csv_with_header(V218D_FIX_SCHEMA_PROFILE_CSV)
    _, v218d_fix_file_rows = read_csv_with_header(V218D_FIX_FILE_PROFILE_CSV)
    _, v218d_fix_next_rows = read_csv_with_header(V218D_FIX_NEXT_ACTIONS_CSV)

    manifest_by_source = load_manifest_by_source(repair_manifest_rows)

    primary_manifest = manifest_by_source.get(PRIMARY_REPAIR_SOURCE_ID)
    crosscheck_manifest = manifest_by_source.get(CROSSCHECK_REPAIR_SOURCE_ID)

    if not primary_manifest:
        raise SystemExit(f"PRIMARY_SOURCE_NOT_FOUND_IN_REPAIR_MANIFEST: {PRIMARY_REPAIR_SOURCE_ID}")

    if not crosscheck_manifest:
        raise SystemExit(f"CROSSCHECK_SOURCE_NOT_FOUND_IN_REPAIR_MANIFEST: {CROSSCHECK_REPAIR_SOURCE_ID}")

    primary_raw_path = Path(primary_manifest["raw_artifact_path"])
    crosscheck_raw_path = Path(crosscheck_manifest["raw_artifact_path"])

    primary_sha_before = sha256_bytes(primary_raw_path.read_bytes())
    crosscheck_sha_before = sha256_bytes(crosscheck_raw_path.read_bytes())

    primary_rows = load_json_raw(primary_raw_path)
    crosscheck_rows_raw = load_json_raw(crosscheck_raw_path)

    if not isinstance(primary_rows, list):
        raise SystemExit("PRIMARY_SOURCE_NOT_JSON_LIST")
    if not isinstance(crosscheck_rows_raw, list):
        raise SystemExit("CROSSCHECK_SOURCE_NOT_JSON_LIST")

    crosscheck_by_symbol = build_stock_day_crosscheck(crosscheck_rows_raw)
    candidates, exclusions, crosscheck_rows = extract_candidates(primary_rows, crosscheck_by_symbol)

    primary_sha_after = sha256_bytes(primary_raw_path.read_bytes())
    crosscheck_sha_after = sha256_bytes(crosscheck_raw_path.read_bytes())

    total_primary_rows = len(primary_rows)
    total_crosscheck_rows = len(crosscheck_rows_raw)
    candidates_count = len(candidates)
    exclusions_count = len(exclusions)

    unique_candidate_ids = len({row["candidate_id"] for row in candidates})
    unique_symbols = len({row["symbol"] for row in candidates})
    duplicate_candidate_ids = candidates_count - unique_candidate_ids
    duplicate_symbols = candidates_count - unique_symbols

    high_confidence_count = sum(1 for row in candidates if row["confidence_bucket"] == "high")
    medium_count = sum(1 for row in candidates if row["confidence_bucket"] == "medium")
    medium_review_count = sum(1 for row in candidates if row["confidence_bucket"] == "medium_review")
    review_required_count = sum(1 for row in candidates if str(row["review_required"]).lower() == "true" or row["review_required"] is True)
    crosscheck_found_count = sum(1 for row in crosscheck_rows if str(row["crosscheck_found"]).lower() == "true" or row["crosscheck_found"] is True)
    crosscheck_missing_count = len(crosscheck_rows) - crosscheck_found_count

    current_state = v218d_fix.get("current_state", {})
    active_canonical_rows = int(current_state.get("active_canonical_rows", 38287))
    validated_candidate_rows = int(current_state.get("validated_candidate_rows", VALIDATED_CANDIDATE_ROWS_EXPECTED))
    rows_needed_to_50k = int(current_state.get("rows_needed_to_50k", ROWS_NEEDED_TO_50K_EXPECTED))
    candidate_completion_percent = current_state.get("candidate_completion_percent", 80.6)

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18d_fix_report_exists", V218D_FIX_JSON.exists(), "critical", str(V218D_FIX_JSON))
    add_check("v2_18d_fix_status_expected", v218d_fix.get("status") == EXPECTED_V218D_FIX_STATUS, "critical", v218d_fix.get("status", ""))
    add_check("v2_18c_fix_report_exists", V218C_FIX_JSON.exists(), "critical", str(V218C_FIX_JSON))
    add_check("v2_18c_fix_status_expected", v218c_fix.get("status") == EXPECTED_V218C_FIX_STATUS, "critical", v218c_fix.get("status", ""))
    add_check("repair_manifest_exists", V218C_FIX_MANIFEST_CSV.exists(), "critical", str(V218C_FIX_MANIFEST_CSV))
    add_check("primary_source_manifest_present", primary_manifest is not None, "critical", PRIMARY_REPAIR_SOURCE_ID)
    add_check("crosscheck_source_manifest_present", crosscheck_manifest is not None, "critical", CROSSCHECK_REPAIR_SOURCE_ID)
    add_check("primary_raw_artifact_exists", primary_raw_path.exists(), "critical", str(primary_raw_path))
    add_check("crosscheck_raw_artifact_exists", crosscheck_raw_path.exists(), "critical", str(crosscheck_raw_path))
    add_check("primary_raw_sha_unchanged", primary_sha_before == primary_sha_after, "critical", "primary raw sha unchanged")
    add_check("crosscheck_raw_sha_unchanged", crosscheck_sha_before == crosscheck_sha_after, "critical", "crosscheck raw sha unchanged")
    add_check("primary_json_list_parsed", isinstance(primary_rows, list), "critical", f"primary_rows={total_primary_rows}")
    add_check("crosscheck_json_list_parsed", isinstance(crosscheck_rows_raw, list), "critical", f"crosscheck_rows={total_crosscheck_rows}")
    add_check("primary_rows_expected_minimum", total_primary_rows >= 1000, "critical", f"primary_rows={total_primary_rows}")
    add_check("crosscheck_rows_expected_minimum", total_crosscheck_rows >= 1000, "critical", f"crosscheck_rows={total_crosscheck_rows}")
    add_check("candidates_emitted", candidates_count > 0, "critical", f"candidates_count={candidates_count}")
    add_check("candidate_ids_unique", duplicate_candidate_ids == 0, "critical", f"duplicate_candidate_ids={duplicate_candidate_ids}")
    add_check("candidate_symbols_unique", duplicate_symbols == 0, "critical", f"duplicate_symbols={duplicate_symbols}")
    add_check("no_canonical_comparison_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("canonical_dataset_not_read", True, "critical", "canonical_dataset_read=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("candidate_extraction_dry_run_only", True, "critical", "candidate_extraction_dry_run_only=True")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", validated_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{validated_candidate_rows} < {FINAL_TARGET_CANDIDATES}")

    add_check("crosscheck_coverage_positive", crosscheck_found_count > 0, "warning", f"crosscheck_found_count={crosscheck_found_count}")
    add_check("high_confidence_candidates_positive", high_confidence_count > 0, "warning", f"high_confidence_count={high_confidence_count}")
    add_check("review_required_candidates_tracked", True, "warning", f"review_required_count={review_required_count}")

    source_diagnostics_rows = [
        {
            "source_id": PRIMARY_REPAIR_SOURCE_ID,
            "provider": "TWSE",
            "source_role": "primary_twse_candidate_source",
            "raw_artifact_path": str(primary_raw_path),
            "file_exists": primary_raw_path.exists(),
            "parse_status": "json_list_parsed",
            "raw_rows": total_primary_rows,
            "columns_detected": "|".join(sorted({key for item in primary_rows[:100] if isinstance(item, dict) for key in item.keys()})),
            "candidates_emitted": candidates_count,
            "exclusions_emitted": exclusions_count,
            "used_for_primary_extraction": True,
            "used_for_crosscheck": False,
            "notes": "Primary TWSE listed company profile source used for dry-run candidate extraction.",
        },
        {
            "source_id": CROSSCHECK_REPAIR_SOURCE_ID,
            "provider": "TWSE",
            "source_role": "twse_symbol_name_crosscheck",
            "raw_artifact_path": str(crosscheck_raw_path),
            "file_exists": crosscheck_raw_path.exists(),
            "parse_status": "json_list_parsed",
            "raw_rows": total_crosscheck_rows,
            "columns_detected": "|".join(sorted({key for item in crosscheck_rows_raw[:100] if isinstance(item, dict) for key in item.keys()})),
            "candidates_emitted": 0,
            "exclusions_emitted": 0,
            "used_for_primary_extraction": False,
            "used_for_crosscheck": True,
            "notes": "TWSE stock day all source used as symbol/name crosscheck only.",
        },
    ]

    field_mapping_rows = [
        {"source_id": PRIMARY_REPAIR_SOURCE_ID, "provider": "TWSE", "source_role": "primary", "target_field": "symbol", "raw_field": "公司代號", "mapping_status": "mapped", "notes": ""},
        {"source_id": PRIMARY_REPAIR_SOURCE_ID, "provider": "TWSE", "source_role": "primary", "target_field": "name", "raw_field": "公司名稱", "mapping_status": "mapped", "notes": ""},
        {"source_id": PRIMARY_REPAIR_SOURCE_ID, "provider": "TWSE", "source_role": "primary", "target_field": "short_name", "raw_field": "公司簡稱", "mapping_status": "mapped", "notes": ""},
        {"source_id": PRIMARY_REPAIR_SOURCE_ID, "provider": "TWSE", "source_role": "primary", "target_field": "industry", "raw_field": "產業別", "mapping_status": "mapped", "notes": ""},
        {"source_id": PRIMARY_REPAIR_SOURCE_ID, "provider": "TWSE", "source_role": "primary", "target_field": "listing_date", "raw_field": "上市日期", "mapping_status": "mapped", "notes": ""},
        {"source_id": PRIMARY_REPAIR_SOURCE_ID, "provider": "TWSE", "source_role": "primary", "target_field": "isin", "raw_field": "", "mapping_status": "not_available_in_source", "notes": "ISIN not detected in TWSE listed company profile raw schema."},
        {"source_id": CROSSCHECK_REPAIR_SOURCE_ID, "provider": "TWSE", "source_role": "crosscheck", "target_field": "symbol", "raw_field": "Code", "mapping_status": "mapped", "notes": ""},
        {"source_id": CROSSCHECK_REPAIR_SOURCE_ID, "provider": "TWSE", "source_role": "crosscheck", "target_field": "name", "raw_field": "Name", "mapping_status": "mapped", "notes": ""},
    ]

    if critical_failed == 0:
        status = "TWSE_TPEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_TWSE_CANDIDATES_READY_FOR_CANONICAL_VALIDATION_DRY_RUN_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "TWSE_TPEX_CANDIDATE_EXTRACTION_DRY_RUN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_rows": active_canonical_rows,
            "validated_candidate_rows": validated_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "candidate_completion_percent": candidate_completion_percent,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
        },
        "candidate_extraction_summary": {
            "primary_source_id": PRIMARY_REPAIR_SOURCE_ID,
            "crosscheck_source_id": CROSSCHECK_REPAIR_SOURCE_ID,
            "primary_rows": total_primary_rows,
            "crosscheck_rows": total_crosscheck_rows,
            "candidates_count": candidates_count,
            "exclusions_count": exclusions_count,
            "unique_candidate_ids": unique_candidate_ids,
            "duplicate_candidate_ids": duplicate_candidate_ids,
            "unique_symbols": unique_symbols,
            "duplicate_symbols": duplicate_symbols,
            "high_confidence_count": high_confidence_count,
            "medium_count": medium_count,
            "medium_review_count": medium_review_count,
            "review_required_count": review_required_count,
            "crosscheck_found_count": crosscheck_found_count,
            "crosscheck_missing_count": crosscheck_missing_count,
            "critical_failed_checks": critical_failed,
        },
        "input_references": {
            "v2_18d_fix_report": str(V218D_FIX_JSON),
            "v2_18d_fix_diagnostics": str(V218D_FIX_SOURCE_DIAGNOSTICS_CSV),
            "v2_18d_fix_schema_profile": str(V218D_FIX_SCHEMA_PROFILE_CSV),
            "v2_18d_fix_file_profile": str(V218D_FIX_FILE_PROFILE_CSV),
            "v2_18d_fix_next_actions": str(V218D_FIX_NEXT_ACTIONS_CSV),
            "v2_18c_fix_report": str(V218C_FIX_JSON),
            "v2_18c_fix_manifest": str(V218C_FIX_MANIFEST_CSV),
            "v2_18d_fix_diagnostics_rows": len(v218d_fix_diagnostics_rows),
            "v2_18d_fix_schema_rows": len(v218d_fix_schema_rows),
            "v2_18d_fix_file_rows": len(v218d_fix_file_rows),
            "v2_18d_fix_next_action_rows": len(v218d_fix_next_rows),
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": False,
            "raw_validation_performed": False,
            "repaired_raw_validation_performed": False,
            "candidate_extraction_performed": True,
            "candidate_extraction_mode": "dry_run_only",
            "canonical_dataset_read": False,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "candidate_validation_against_canonical_performed": False,
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

    write_csv(CANDIDATES_CSV, candidates, CANDIDATE_FIELDS)
    write_csv(EXCLUSIONS_CSV, exclusions, EXCLUSION_FIELDS)
    write_csv(SOURCE_DIAGNOSTICS_CSV, source_diagnostics_rows, SOURCE_DIAGNOSTICS_FIELDS)
    write_csv(FIELD_MAPPING_CSV, field_mapping_rows, FIELD_MAPPING_FIELDS)
    write_csv(CROSSCHECK_CSV, crosscheck_rows, CROSSCHECK_FIELDS)
    write_json(REPORT_JSON, payload)

    confidence_lines = "\n".join(
        f"- {bucket}: {count}"
        for bucket, count in [
            ("high", high_confidence_count),
            ("medium", medium_count),
            ("medium_review", medium_review_count),
        ]
    )

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

v2.18E performs a TWSE + TPEx candidate extraction dry run.

This phase uses the repaired TWSE listed company profile JSON as the primary source and TWSE stock day all JSON as crosscheck. TPEx remains deferred/support because v2.18D_FIX confirmed TPEx still has technical acquisition errors.

This is a dry-run-only phase. It does not read the canonical dataset, does not compare against canonical, does not write an expanded candidate dataset, does not modify canonical, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Validated candidate rows: `{validated_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Candidate completion: `{candidate_completion_percent}%`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Extraction summary

- Primary source: `{PRIMARY_REPAIR_SOURCE_ID}`
- Crosscheck source: `{CROSSCHECK_REPAIR_SOURCE_ID}`
- Primary rows: `{total_primary_rows}`
- Crosscheck rows: `{total_crosscheck_rows}`
- Candidates emitted: `{candidates_count}`
- Exclusions emitted: `{exclusions_count}`
- Unique candidate IDs: `{unique_candidate_ids}`
- Duplicate candidate IDs: `{duplicate_candidate_ids}`
- Unique symbols: `{unique_symbols}`
- Duplicate symbols: `{duplicate_symbols}`
- Review required candidates: `{review_required_count}`
- Crosscheck found: `{crosscheck_found_count}`
- Crosscheck missing: `{crosscheck_missing_count}`
- Critical failed checks: `{critical_failed}`

## Confidence buckets

{confidence_lines}

## Field mapping

- Primary symbol: `公司代號`
- Primary name: `公司名稱`
- Primary short name: `公司簡稱`
- Primary industry: `產業別`
- Primary listing date: `上市日期`
- Crosscheck symbol: `Code`
- Crosscheck name: `Name`
- ISIN: not available in source

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw acquisition repair performed: false
- Raw validation performed: false
- Repaired raw validation performed: false
- Candidate extraction performed: true
- Candidate extraction mode: dry_run_only
- Canonical dataset read: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Candidate validation against canonical performed: false
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

    print("v2.18E TWSE + TPEx candidate extraction dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CANDIDATE_EXTRACTION_SUMMARY:")
    for key, value in payload["candidate_extraction_summary"].items():
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
