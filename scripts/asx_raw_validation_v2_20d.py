from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.20D"
PHASE = "ASX Raw Validation"
PHASE_TYPE = "raw-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "asx_v2_20c"

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
HKEX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V220C_JSON = OUTPUT_DIR / "asx_quality_first_raw_acquisition_v2_20c.json"
V220C_MANIFEST_CSV = OUTPUT_DIR / "asx_quality_first_raw_manifest_v2_20c.csv"
V220C_ATTEMPTS_CSV = OUTPUT_DIR / "asx_quality_first_raw_download_attempts_v2_20c.csv"
V220C_DISCOVERED_LINKS_CSV = OUTPUT_DIR / "asx_quality_first_raw_discovered_links_v2_20c.csv"

REPORT_JSON = OUTPUT_DIR / "asx_raw_validation_v2_20d.json"
REPORT_MD = OUTPUT_DIR / "asx_raw_validation_v2_20d.md"
FILE_VALIDATION_CSV = OUTPUT_DIR / "asx_raw_validation_files_v2_20d.csv"
SOURCE_READINESS_CSV = OUTPUT_DIR / "asx_raw_validation_source_readiness_v2_20d.csv"
CSV_PROFILE_CSV = OUTPUT_DIR / "asx_raw_validation_csv_profile_v2_20d.csv"
XLS_PROFILE_CSV = OUTPUT_DIR / "asx_raw_validation_xls_profile_v2_20d.csv"
HTML_SIGNAL_CSV = OUTPUT_DIR / "asx_raw_validation_html_signals_v2_20d.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_raw_validation_checks_v2_20d.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_raw_validation_next_actions_v2_20d.csv"

EXPECTED_V220C_STATUS = "ASX_QUALITY_FIRST_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"

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

STATUS_READY = "ASX_RAW_VALIDATION_COMPLETED_PARSE_READY_EXTRACTION_DRY_RUN_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
STATUS_REPAIR_RECOMMENDED = "ASX_RAW_VALIDATION_COMPLETED_REPAIR_RECOMMENDED_EXTRACTION_POSSIBLE_WITH_ISIN_XLS_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
STATUS_FAILED = "ASX_RAW_VALIDATION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_READY = "v2.20E - ASX Candidate Extraction Dry Run"
NEXT_PHASE_REPAIR = "v2.20C_FIX - ASX Complete List Route Repair"
NEXT_PHASE_REVIEW = "v2.20D_REVIEW - ASX Raw Validation Review"


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


def read_text_best_effort(path: Path, max_chars: int | None = None) -> tuple[str, str]:
    data = path.read_bytes()
    encodings = ["utf-8-sig", "utf-8", "cp1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            text = data.decode(encoding)
            if max_chars is not None:
                return text[:max_chars], encoding
            return text, encoding
        except UnicodeDecodeError:
            continue

    text = data.decode("utf-8", errors="ignore")
    if max_chars is not None:
        return text[:max_chars], "utf-8-ignore"
    return text, "utf-8-ignore"


def normalize_header(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def detect_csv_dialect_and_profile(path: Path, source_id: str) -> dict[str, Any]:
    text, encoding = read_text_best_effort(path)
    sample = text[:8192]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    header: list[str] = []
    row_count = 0
    parse_error = ""

    try:
        reader = csv.reader(non_empty_lines, delimiter=delimiter)
        rows = list(reader)
        if rows:
            header = rows[0]
            row_count = max(len(rows) - 1, 0)
    except Exception as exc:
        parse_error = f"{type(exc).__name__}: {exc}"

    normalized_header = [normalize_header(col) for col in header]
    header_text = "|".join(normalized_header)

    has_code_like_header = any(
        token in header_text
        for token in [
            "code",
            "asx_code",
            "ticker",
            "security",
            "symbol",
            "issuer",
        ]
    )
    has_name_like_header = any(token in header_text for token in ["name", "company", "issuer", "description"])
    has_price_like_header = any(token in header_text for token in ["price", "closing", "last"])

    return {
        "source_id": source_id,
        "path": str(path),
        "encoding": encoding,
        "delimiter": delimiter,
        "row_count": row_count,
        "column_count": len(header),
        "header": ";".join(header),
        "normalized_header": ";".join(normalized_header),
        "has_code_like_header": has_code_like_header,
        "has_name_like_header": has_name_like_header,
        "has_price_like_header": has_price_like_header,
        "parse_error": parse_error,
        "parseable_as_csv": parse_error == "" and row_count > 0 and len(header) > 0,
    }


def profile_xls_binary(path: Path, source_id: str) -> dict[str, Any]:
    data = path.read_bytes()
    header = data[:16].hex()
    is_ole_xls = data.startswith(bytes.fromhex("D0CF11E0A1B11AE1"))
    is_zip_xlsx = data.startswith(b"PK")
    size_bytes = len(data)

    ascii_preview = data[:250000].decode("latin-1", errors="ignore").lower()
    contains_isin_text = "isin" in ascii_preview
    contains_asx_text = "asx" in ascii_preview
    contains_security_text = "security" in ascii_preview or "securities" in ascii_preview
    contains_code_text = "code" in ascii_preview

    optional_parse_status = "not_attempted"
    optional_parse_rows = ""
    optional_parse_columns = ""
    optional_parse_error = ""

    try:
        import pandas as pd  # type: ignore

        try:
            frame = pd.read_excel(path, dtype=str, nrows=25)
            optional_parse_status = "parseable_with_pandas"
            optional_parse_rows = str(len(frame.index))
            optional_parse_columns = str(len(frame.columns))
        except Exception as exc:
            optional_parse_status = "pandas_available_but_parse_failed"
            optional_parse_error = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        optional_parse_status = "pandas_not_available_or_import_failed"
        optional_parse_error = f"{type(exc).__name__}: {exc}"

    return {
        "source_id": source_id,
        "path": str(path),
        "size_bytes": size_bytes,
        "header_hex": header,
        "is_ole_xls": is_ole_xls,
        "is_zip_xlsx": is_zip_xlsx,
        "contains_isin_text_in_binary_preview": contains_isin_text,
        "contains_asx_text_in_binary_preview": contains_asx_text,
        "contains_security_text_in_binary_preview": contains_security_text,
        "contains_code_text_in_binary_preview": contains_code_text,
        "binary_valid_excel_container": is_ole_xls or is_zip_xlsx,
        "optional_parse_status": optional_parse_status,
        "optional_parse_rows_preview": optional_parse_rows,
        "optional_parse_columns_preview": optional_parse_columns,
        "optional_parse_error": optional_parse_error,
    }


def profile_html(path: Path, source_id: str) -> dict[str, Any]:
    text, encoding = read_text_best_effort(path)
    lower = text.lower()

    signals = {
        "source_id": source_id,
        "path": str(path),
        "encoding": encoding,
        "bytes": path.stat().st_size,
        "contains_asx": "asx" in lower,
        "contains_listed_companies": "listed companies" in lower or "listed company" in lower,
        "contains_complete_list": "complete list" in lower,
        "contains_download": "download" in lower,
        "contains_csv": ".csv" in lower or "csv" in lower,
        "contains_isin": "isin" in lower,
        "contains_warrant": "warrant" in lower,
        "contains_options": "option" in lower,
        "contains_debt": "debt" in lower,
        "contains_directory": "directory" in lower,
        "contains_market_statistics": "market statistics" in lower,
        "contains_last_known_closing_price": "last-known-closing-price" in lower or "last known closing price" in lower,
        "html_signal_score": 0,
    }

    positive_keys = [
        "contains_asx",
        "contains_listed_companies",
        "contains_complete_list",
        "contains_download",
        "contains_csv",
        "contains_isin",
        "contains_directory",
        "contains_market_statistics",
        "contains_last_known_closing_price",
    ]
    signals["html_signal_score"] = sum(1 for key in positive_keys if signals[key] is True)

    return signals


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        FILE_VALIDATION_CSV,
        SOURCE_READINESS_CSV,
        CSV_PROFILE_CSV,
        XLS_PROFILE_CSV,
        HTML_SIGNAL_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v220c = read_json(V220C_JSON)
    manifest = read_csv_dicts(V220C_MANIFEST_CSV)
    attempts = read_csv_dicts(V220C_ATTEMPTS_CSV)
    discovered_links = read_csv_dicts(V220C_DISCOVERED_LINKS_CSV)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_rows = count_csv_rows(HKEX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_before = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

    rows_needed_to_quality_floor = max(QUALITY_FLOOR_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_quality_ceiling = max(QUALITY_CEILING_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_aspirational_50k = max(ASPIRATIONAL_TARGET - hkex_validated_candidate_rows, 0)

    file_validation_rows: list[dict[str, Any]] = []
    csv_profile_rows: list[dict[str, Any]] = []
    xls_profile_rows: list[dict[str, Any]] = []
    html_signal_rows: list[dict[str, Any]] = []

    for row in manifest:
        path = Path(row.get("path", ""))
        source_id = row.get("source_id", "")
        expected_sha = row.get("sha256", "")
        expected_bytes = int(row.get("bytes") or 0)
        exists = path.exists()
        actual_bytes = path.stat().st_size if exists else 0
        actual_sha = sha256_file(path) if exists else ""
        suffix = path.suffix.lower()

        type_hint = "unknown"
        if suffix in [".html", ".htm"]:
            type_hint = "html"
        elif suffix == ".csv":
            type_hint = "csv"
        elif suffix in [".xls", ".xlsx"]:
            type_hint = "excel"

        file_validation_rows.append(
            {
                "source_id": source_id,
                "path": str(path),
                "expected_role": row.get("expected_role", ""),
                "required": row.get("required", ""),
                "content_type": row.get("content_type", ""),
                "type_hint": type_hint,
                "exists": exists,
                "expected_bytes": expected_bytes,
                "actual_bytes": actual_bytes,
                "bytes_match": expected_bytes == actual_bytes,
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "sha256_match": expected_sha == actual_sha,
                "non_empty": actual_bytes > 0,
            }
        )

        if not exists:
            continue

        if type_hint == "csv":
            csv_profile_rows.append(detect_csv_dialect_and_profile(path, source_id))
        elif type_hint == "excel":
            xls_profile_rows.append(profile_xls_binary(path, source_id))
        elif type_hint == "html":
            html_signal_rows.append(profile_html(path, source_id))

    manifest_source_ids = {row["source_id"] for row in manifest}
    attempt_by_source_id = {row["source_id"]: row for row in attempts}

    legacy_csv_attempt = attempt_by_source_id.get("asx_listed_companies_legacy_csv", {})
    legacy_csv_status = legacy_csv_attempt.get("status_code", "")

    required_page_ids = {
        "asx_indices_page",
        "asx_company_directory_page",
        "asx_isin_services_page",
        "asx_codes_and_descriptors_page",
    }

    required_pages_captured = required_page_ids.issubset(manifest_source_ids)
    market_statistics_captured = "asx_market_statistics_page" in manifest_source_ids
    isin_xls_captured = "asx_isin_xls_direct" in manifest_source_ids
    complete_list_legacy_csv_captured = "asx_listed_companies_legacy_csv" in manifest_source_ids
    last_known_price_csv_captured = "asx_discovered_last_known_closing_price_fy26" in manifest_source_ids

    isin_xls_profiles = [row for row in xls_profile_rows if row["source_id"] == "asx_isin_xls_direct"]
    isin_xls_binary_valid = bool(isin_xls_profiles and isin_xls_profiles[0]["binary_valid_excel_container"])
    isin_xls_optional_parse_ready = bool(isin_xls_profiles and isin_xls_profiles[0]["optional_parse_status"] == "parseable_with_pandas")

    last_price_csv_profiles = [row for row in csv_profile_rows if row["source_id"] == "asx_discovered_last_known_closing_price_fy26"]
    last_price_csv_parseable = bool(last_price_csv_profiles and last_price_csv_profiles[0]["parseable_as_csv"])
    last_price_csv_rows = int(last_price_csv_profiles[0]["row_count"]) if last_price_csv_profiles else 0

    all_files_exist = all(row["exists"] is True for row in file_validation_rows)
    all_files_sha_match = all(row["sha256_match"] is True for row in file_validation_rows)
    all_files_non_empty = all(row["non_empty"] is True for row in file_validation_rows)

    html_required_signal_ready = all(
        any(row["source_id"] == source_id and int(row["html_signal_score"]) >= 1 for row in html_signal_rows)
        for source_id in required_page_ids
    )

    discovered_download_candidates = [
        row for row in discovered_links
        if str(row.get("download_candidate", "")).lower() == "true"
    ]

    source_readiness_rows = [
        {
            "source_id": "asx_required_pages",
            "readiness": "ready" if required_pages_captured and html_required_signal_ready else "blocked",
            "role": "official source evidence and scope context",
            "evidence": f"required_pages_captured={required_pages_captured};html_required_signal_ready={html_required_signal_ready}",
            "blocking_issue": "" if required_pages_captured else "one or more required ASX pages missing",
            "recommended_action": "use as validation/context evidence",
        },
        {
            "source_id": "asx_isin_xls_direct",
            "readiness": "ready" if isin_xls_captured and isin_xls_binary_valid else "blocked",
            "role": "identifier enrichment and possible extraction backbone",
            "evidence": f"captured={isin_xls_captured};binary_valid_excel_container={isin_xls_binary_valid};optional_parse_ready={isin_xls_optional_parse_ready}",
            "blocking_issue": "" if isin_xls_captured and isin_xls_binary_valid else "ISIN XLS missing or not valid Excel container",
            "recommended_action": "use for v2.20E extraction dry run; install/repair XLS parser only if extraction script cannot parse it",
        },
        {
            "source_id": "asx_complete_list_legacy_csv",
            "readiness": "not_ready_optional",
            "role": "legacy complete list CSV",
            "evidence": f"captured={complete_list_legacy_csv_captured};legacy_status={legacy_csv_status}",
            "blocking_issue": "legacy endpoint returned 404 and was optional in v2.20C",
            "recommended_action": "do not block extraction if ISIN XLS is usable; repair only if extraction yield is poor",
        },
        {
            "source_id": "asx_last_known_closing_price_csv",
            "readiness": "ready_context_only" if last_known_price_csv_captured and last_price_csv_parseable else "not_ready_optional",
            "role": "market statistics / price context, not primary candidate source",
            "evidence": f"captured={last_known_price_csv_captured};parseable={last_price_csv_parseable};rows={last_price_csv_rows}",
            "blocking_issue": "" if last_known_price_csv_captured else "optional CSV not captured",
            "recommended_action": "do not use as primary candidate universe; may support liquidity/context later",
        },
    ]

    parse_ready_for_extraction = required_pages_captured and isin_xls_captured and isin_xls_binary_valid
    complete_list_route_needs_repair = not complete_list_legacy_csv_captured and str(legacy_csv_status) == "404"

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_after = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

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

    add_check("v2_20c_report_exists", V220C_JSON.exists(), "critical", str(V220C_JSON))
    add_check("v2_20c_status_expected", v220c.get("status") == EXPECTED_V220C_STATUS, "critical", str(v220c.get("status", "")))
    add_check("v2_20c_next_phase_expected", v220c.get("recommended_next_phase") == "v2.20D - ASX Raw Validation", "critical", str(v220c.get("recommended_next_phase")))
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
    add_check("raw_manifest_loaded", len(manifest) == 7, "critical", f"manifest_rows={len(manifest)}")
    add_check("attempts_loaded", len(attempts) >= 8, "critical", f"attempts={len(attempts)}")
    add_check("all_manifest_files_exist", all_files_exist, "critical", f"all_files_exist={all_files_exist}")
    add_check("all_manifest_files_non_empty", all_files_non_empty, "critical", f"all_files_non_empty={all_files_non_empty}")
    add_check("all_manifest_sha_match", all_files_sha_match, "critical", f"all_files_sha_match={all_files_sha_match}")
    add_check("required_pages_captured", required_pages_captured, "critical", f"required_pages_captured={required_pages_captured}")
    add_check("market_statistics_page_captured", market_statistics_captured, "warning", f"market_statistics_captured={market_statistics_captured}")
    add_check("html_required_signals_ready", html_required_signal_ready, "critical", f"html_required_signal_ready={html_required_signal_ready}")
    add_check("isin_xls_captured", isin_xls_captured, "critical", f"isin_xls_captured={isin_xls_captured}")
    add_check("isin_xls_binary_valid", isin_xls_binary_valid, "critical", f"isin_xls_binary_valid={isin_xls_binary_valid}")
    add_check("isin_xls_optional_pandas_parse_ready", isin_xls_optional_parse_ready, "warning", f"optional_parse_ready={isin_xls_optional_parse_ready}")
    add_check("legacy_complete_list_csv_optional_404_documented", complete_list_route_needs_repair, "warning", f"legacy_csv_status={legacy_csv_status};captured={complete_list_legacy_csv_captured}")
    add_check("last_price_csv_parseable_context_only", last_price_csv_parseable, "warning", f"last_price_csv_parseable={last_price_csv_parseable};rows={last_price_csv_rows}")
    add_check("discovered_download_candidates_available", len(discovered_download_candidates) >= 1, "warning", f"download_candidates={len(discovered_download_candidates)}")
    add_check("parse_ready_for_extraction", parse_ready_for_extraction, "critical", f"parse_ready_for_extraction={parse_ready_for_extraction}")
    add_check("raw_validation_only", True, "critical", "raw validation only")
    add_check("network_download_not_performed", True, "critical", "network_download_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
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
    elif complete_list_route_needs_repair:
        status = STATUS_REPAIR_RECOMMENDED
        recommended_next_phase = NEXT_PHASE_READY
    else:
        status = STATUS_READY
        recommended_next_phase = NEXT_PHASE_READY

    validation_summary = {
        "selected_provider": "ASX",
        "raw_dir": str(RAW_DIR),
        "manifest_rows": len(manifest),
        "attempts_rows": len(attempts),
        "discovered_links_rows": len(discovered_links),
        "required_pages_captured": required_pages_captured,
        "html_required_signals_ready": html_required_signal_ready,
        "isin_xls_captured": isin_xls_captured,
        "isin_xls_binary_valid": isin_xls_binary_valid,
        "isin_xls_optional_parse_ready": isin_xls_optional_parse_ready,
        "complete_list_legacy_csv_captured": complete_list_legacy_csv_captured,
        "legacy_csv_status": legacy_csv_status,
        "complete_list_route_needs_repair": complete_list_route_needs_repair,
        "last_known_price_csv_captured": last_known_price_csv_captured,
        "last_price_csv_parseable": last_price_csv_parseable,
        "last_price_csv_rows": last_price_csv_rows,
        "parse_ready_for_extraction": parse_ready_for_extraction,
        "current_hkex_validated_candidate_rows": hkex_validated_candidate_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_needed_to_quality_floor": rows_needed_to_quality_floor,
        "rows_needed_to_quality_ceiling": rows_needed_to_quality_ceiling,
        "rows_needed_to_aspirational_50k": rows_needed_to_aspirational_50k,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "ASX",
            "action": "open_asx_candidate_extraction_dry_run",
            "priority": "high" if parse_ready_for_extraction else "blocked",
            "reason": "ISIN XLS is captured and valid as an Excel container; extraction dry run can test whether it yields clean ASX candidates.",
            "recommended_phase": NEXT_PHASE_READY if parse_ready_for_extraction else NEXT_PHASE_REVIEW,
            "guardrails": "dry run only; no append; no canonical replacement; ordinary equity/A-REIT scope rules only",
        },
        {
            "action_order": 2,
            "action_scope": "ASX_complete_list",
            "action": "defer_legacy_complete_list_repair_until_after_isin_extraction_yield",
            "priority": "medium",
            "reason": "Legacy ASXListedCompanies.csv returned 404, but this was optional and ISIN XLS may be enough for extraction dry run.",
            "recommended_phase": NEXT_PHASE_READY if parse_ready_for_extraction else NEXT_PHASE_REPAIR,
            "guardrails": "repair only if ISIN extraction is blocked or yields too few clean rows",
        },
        {
            "action_order": 3,
            "action_scope": "quality_target",
            "action": "preserve_42k_45k_operational_band",
            "priority": "high",
            "reason": "Only 608 clean net-new rows are needed to cross 42k.",
            "recommended_phase": NEXT_PHASE_READY if parse_ready_for_extraction else NEXT_PHASE_REVIEW,
            "guardrails": "50k aspirational only; full59k deprecated; do not include instruments only for volume",
        },
    ]

    write_csv(FILE_VALIDATION_CSV, file_validation_rows, ["source_id", "path", "expected_role", "required", "content_type", "type_hint", "exists", "expected_bytes", "actual_bytes", "bytes_match", "expected_sha256", "actual_sha256", "sha256_match", "non_empty"])
    write_csv(SOURCE_READINESS_CSV, source_readiness_rows, ["source_id", "readiness", "role", "evidence", "blocking_issue", "recommended_action"])
    write_csv(CSV_PROFILE_CSV, csv_profile_rows, ["source_id", "path", "encoding", "delimiter", "row_count", "column_count", "header", "normalized_header", "has_code_like_header", "has_name_like_header", "has_price_like_header", "parse_error", "parseable_as_csv"])
    write_csv(XLS_PROFILE_CSV, xls_profile_rows, ["source_id", "path", "size_bytes", "header_hex", "is_ole_xls", "is_zip_xlsx", "contains_isin_text_in_binary_preview", "contains_asx_text_in_binary_preview", "contains_security_text_in_binary_preview", "contains_code_text_in_binary_preview", "binary_valid_excel_container", "optional_parse_status", "optional_parse_rows_preview", "optional_parse_columns_preview", "optional_parse_error"])
    write_csv(HTML_SIGNAL_CSV, html_signal_rows, ["source_id", "path", "encoding", "bytes", "contains_asx", "contains_listed_companies", "contains_complete_list", "contains_download", "contains_csv", "contains_isin", "contains_warrant", "contains_options", "contains_debt", "contains_directory", "contains_market_statistics", "contains_last_known_closing_price", "html_signal_score"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "validation_summary": validation_summary,
        "file_validation": file_validation_rows,
        "source_readiness": source_readiness_rows,
        "csv_profile": csv_profile_rows,
        "xls_profile": xls_profile_rows,
        "html_signals": html_signal_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "raw_validation_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_validation_performed": True,
            "candidate_extraction_performed": False,
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

    readiness_lines = "\n".join(
        f"- `{row['source_id']}` — `{row['readiness']}` — {row['evidence']}"
        for row in source_readiness_rows
    )
    xls_lines = "\n".join(
        f"- `{row['source_id']}` — binary_valid `{row['binary_valid_excel_container']}` — optional_parse `{row['optional_parse_status']}` — `{row['optional_parse_error']}`"
        for row in xls_profile_rows
    ) or "- No XLS profiles."
    csv_lines = "\n".join(
        f"- `{row['source_id']}` — rows `{row['row_count']}` — columns `{row['column_count']}` — parseable `{row['parseable_as_csv']}`"
        for row in csv_profile_rows
    ) or "- No CSV profiles."
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

v2.20D validates ASX raw files captured in v2.20C.

The raw set is considered ready for extraction dry run if required ASX pages exist, captured file hashes match the v2.20C manifest, the ISIN XLS is captured, and the ISIN XLS is a valid Excel container.

The legacy ASXListedCompanies CSV endpoint returned `{legacy_csv_status}` and remains optional. Repair is recommended only if the ISIN XLS extraction dry run fails or yields too few clean candidates.

This phase performs raw validation only. It does not download new files, extract candidates, validate candidates against canonical, rebuild datasets, promote canonical, run scoring, call OpenAI, call brokers, run repo-wide renormalization or launch full59k.

## Validation summary

- Selected provider: `ASX`
- Manifest rows: `{len(manifest)}`
- Attempts rows: `{len(attempts)}`
- Required pages captured: `{required_pages_captured}`
- HTML required signals ready: `{html_required_signal_ready}`
- ISIN XLS captured: `{isin_xls_captured}`
- ISIN XLS binary valid: `{isin_xls_binary_valid}`
- ISIN XLS optional parse ready: `{isin_xls_optional_parse_ready}`
- Complete list legacy CSV captured: `{complete_list_legacy_csv_captured}`
- Legacy CSV status: `{legacy_csv_status}`
- Complete list route needs repair: `{complete_list_route_needs_repair}`
- Last price CSV captured: `{last_known_price_csv_captured}`
- Last price CSV parseable: `{last_price_csv_parseable}`
- Last price CSV rows: `{last_price_csv_rows}`
- Parse ready for extraction: `{parse_ready_for_extraction}`
- Current HKEX validated candidate rows: `{hkex_validated_candidate_rows}`
- Rows needed to 42k: `{rows_needed_to_quality_floor}`
- Rows needed to 45k: `{rows_needed_to_quality_ceiling}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Source readiness

{readiness_lines}

## XLS profile

{xls_lines}

## CSV profile

{csv_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Raw validation only: true
- Network download performed: false
- Candidate extraction performed: false
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

    print("v2.20D ASX raw validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in validation_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_READINESS:")
    for row in source_readiness_rows:
        print(f"- {row['source_id']}: {row['readiness']} | {row['evidence']} | action={row['recommended_action']}")
    print("")
    print("XLS_PROFILE:")
    for row in xls_profile_rows:
        print(f"- {row['source_id']}: binary_valid={row['binary_valid_excel_container']} optional_parse={row['optional_parse_status']} error={row['optional_parse_error']}")
    print("")
    print("CSV_PROFILE:")
    for row in csv_profile_rows:
        print(f"- {row['source_id']}: rows={row['row_count']} columns={row['column_count']} parseable={row['parseable_as_csv']}")
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
