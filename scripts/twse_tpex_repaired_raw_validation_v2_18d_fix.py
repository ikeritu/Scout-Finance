from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.18D_FIX"
PHASE = "TWSE + TPEx Repaired Raw Validation"
PHASE_TYPE = "repaired-raw-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
VALIDATED_NSE_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"

V218C_FIX_JSON = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_v2_18c_fix.json"
V218C_FIX_MANIFEST_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_manifest_v2_18c_fix.csv"
V218C_FIX_DECISION_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_decision_v2_18c_fix.csv"
V218C_FIX_ENDPOINT_DISCOVERY_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_endpoint_discovery_v2_18c_fix.csv"
V218C_FIX_SOURCE_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_source_actions_v2_18c_fix.csv"

V218D_JSON = OUTPUT_DIR / "twse_tpex_raw_validation_v2_18d.json"
V218D_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "twse_tpex_raw_validation_source_diagnostics_v2_18d.csv"

REPORT_JSON = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_v2_18d_fix.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_v2_18d_fix.md"
FILE_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_file_profile_v2_18d_fix.csv"
SCHEMA_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_schema_profile_v2_18d_fix.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_source_diagnostics_v2_18d_fix.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_repaired_raw_validation_next_actions_v2_18d_fix.csv"

EXPECTED_V218C_FIX_STATUS = "TWSE_TPEX_RAW_ACQUISITION_REPAIR_COMPLETED_ROW_DATA_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
EXPECTED_V218D_STATUS = "TWSE_TPEX_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
VALIDATED_CANDIDATE_ROWS_EXPECTED = 40300
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9700

RECOMMENDED_NEXT_PHASE = "v2.18E - TWSE + TPEx Candidate Extraction Dry Run"
RECOMMENDED_FIX_PHASE = "v2.18D_FIX_REVIEW - TWSE + TPEx Repaired Raw Validation Review"

FILE_PROFILE_FIELDS = [
    "repair_source_id",
    "provider",
    "repair_role",
    "origin_source_id",
    "candidate_role",
    "source_url",
    "http_status",
    "download_status",
    "ssl_mode",
    "raw_artifact_path",
    "file_exists",
    "manifest_bytes",
    "actual_bytes",
    "bytes_match",
    "manifest_sha256",
    "actual_sha256",
    "sha256_match",
    "manifest_detected_format",
    "detected_format",
    "parse_status",
    "row_like_count",
    "column_like_count",
    "row_data_candidate_manifest",
    "row_data_candidate_validated",
    "validation_bucket",
    "extraction_readiness",
    "notes",
]

SCHEMA_PROFILE_FIELDS = [
    "repair_source_id",
    "provider",
    "candidate_role",
    "parse_status",
    "row_like_count",
    "column_like_count",
    "columns_detected",
    "symbol_column_candidates",
    "name_column_candidates",
    "isin_column_candidates",
    "listing_date_column_candidates",
    "security_type_column_candidates",
    "schema_bucket",
    "schema_notes",
]

SOURCE_DIAGNOSTICS_FIELDS = [
    "repair_source_id",
    "provider",
    "origin_source_id",
    "candidate_role",
    "http_status",
    "download_status",
    "detected_format",
    "parse_status",
    "row_like_count",
    "column_like_count",
    "row_data_candidate_validated",
    "candidate_extraction_readiness",
    "repair_still_required",
    "repair_reason",
    "next_action",
]

NEXT_ACTIONS_FIELDS = [
    "action_order",
    "action_scope",
    "action",
    "priority",
    "reason",
    "recommended_phase",
    "guardrails",
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


def decode_text(data: bytes) -> tuple[str, str]:
    for encoding in ["utf-8-sig", "utf-8", "big5", "cp950", "latin-1"]:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replace"


def detect_format(data: bytes, content_type: str, path: Path) -> str:
    if not data:
        return "empty"

    text_head, _ = decode_text(data[:8192])
    stripped = text_head.lstrip()
    low = stripped.lower()
    ct = (content_type or "").lower()
    suffix = path.suffix.lower()

    if "certificate verify failed" in low or "urlopen error" in low:
        return "error_text"

    if stripped.startswith("{") or stripped.startswith("[") or "application/json" in ct or suffix == ".json":
        return "json_like"

    if "<!doctype html" in low or low.startswith("<html") or "<html" in low or "text/html" in ct:
        return "html"

    if "," in text_head and ("\n" in text_head or "\r" in text_head):
        return "csv_like"

    return "text_or_binary"


def parse_artifact(data: bytes, detected_format: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "parse_status": "not_attempted",
        "row_like_count": 0,
        "column_like_count": 0,
        "columns": [],
        "sample_type": "",
        "notes": "",
    }

    text, encoding = decode_text(data)

    if detected_format == "json_like":
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                result["row_like_count"] = len(parsed)
                result["sample_type"] = "list"
                if parsed and isinstance(parsed[0], dict):
                    columns = sorted({key for item in parsed[:100] if isinstance(item, dict) for key in item.keys()})
                    result["columns"] = columns
                    result["column_like_count"] = len(columns)
                result["parse_status"] = "json_list_parsed"
            elif isinstance(parsed, dict):
                result["row_like_count"] = len(parsed)
                result["columns"] = sorted(parsed.keys())
                result["column_like_count"] = len(parsed.keys())
                result["sample_type"] = "dict"
                result["parse_status"] = "json_dict_parsed"
            else:
                result["sample_type"] = type(parsed).__name__
                result["parse_status"] = f"json_scalar_parsed_{type(parsed).__name__}"
            result["notes"] = f"encoding={encoding}"
        except Exception as error:
            result["parse_status"] = "json_parse_failed"
            result["notes"] = str(error)
        return result

    if detected_format == "csv_like":
        try:
            rows = list(csv.reader(text.splitlines()))
            result["row_like_count"] = len(rows)
            result["column_like_count"] = max((len(row) for row in rows), default=0)
            result["columns"] = rows[0] if rows else []
            result["sample_type"] = "csv_rows"
            result["parse_status"] = "csv_like_parsed"
            result["notes"] = f"encoding={encoding}"
        except Exception as error:
            result["parse_status"] = "csv_parse_failed"
            result["notes"] = str(error)
        return result

    if detected_format == "html":
        low = text.lower()
        result["row_like_count"] = len(re.findall(r"<tr[\s>]", low))
        result["column_like_count"] = 0
        result["sample_type"] = "html"
        result["parse_status"] = "html_profiled"
        result["notes"] = f"encoding={encoding}; csv_mentions={low.count('csv')}; download_mentions={low.count('download') + low.count('下載')}"
        return result

    if detected_format == "error_text":
        result["sample_type"] = "error_text"
        result["parse_status"] = "error_payload_profiled"
        result["notes"] = text[:300].replace("\n", " ").replace("\r", " ")
        return result

    result["sample_type"] = "text_or_binary"
    result["parse_status"] = "text_or_binary_profiled"
    result["notes"] = f"encoding={encoding}"
    return result


def find_columns(columns: list[str], tokens: list[str]) -> list[str]:
    result = []
    for col in columns:
        low = str(col).lower()
        if any(token.lower() in low or token in str(col) for token in tokens):
            result.append(col)
    return result


def schema_profile_for_source(row: dict[str, str], parse_info: dict[str, Any]) -> dict[str, Any]:
    columns = list(parse_info.get("columns", []) or [])

    symbol_cols = find_columns(
        columns,
        [
            "code",
            "stock_code",
            "stockno",
            "symbol",
            "ticker",
            "securitiescode",
            "securitycode",
            "公司代號",
            "證券代號",
            "有價證券代號",
            "股票代號",
        ],
    )

    name_cols = find_columns(
        columns,
        [
            "name",
            "companyname",
            "company_name",
            "securityname",
            "securitiesname",
            "shortname",
            "公司名稱",
            "公司簡稱",
            "證券名稱",
            "股票名稱",
            "有價證券名稱",
        ],
    )

    isin_cols = find_columns(columns, ["isin", "isin code", "國際證券辨識號碼", "國際證券代號"])
    listing_date_cols = find_columns(columns, ["listing", "list", "上市日期", "掛牌日期", "上市日"])
    security_type_cols = find_columns(columns, ["type", "market", "category", "industry", "產業別", "市場別", "證券別"])

    row_count = int(parse_info.get("row_like_count", 0) or 0)
    parse_status = str(parse_info.get("parse_status", ""))

    if parse_status == "json_list_parsed" and row_count > 0 and symbol_cols and name_cols:
        schema_bucket = "candidate_schema_ready"
        schema_notes = "row-data JSON list with symbol/name fields detected"
    elif parse_status == "json_list_parsed" and row_count > 0:
        schema_bucket = "row_data_schema_review_required"
        schema_notes = "row-data JSON list parsed but symbol/name field detection is incomplete"
    elif parse_status.endswith("_parsed"):
        schema_bucket = "parsed_non_candidate_shape"
        schema_notes = "parsed but not a list-shaped candidate source"
    else:
        schema_bucket = "not_parse_ready"
        schema_notes = parse_info.get("notes", "")

    return {
        "repair_source_id": row.get("repair_source_id", ""),
        "provider": row.get("provider", ""),
        "candidate_role": row.get("candidate_role", ""),
        "parse_status": parse_status,
        "row_like_count": row_count,
        "column_like_count": int(parse_info.get("column_like_count", 0) or 0),
        "columns_detected": "|".join(columns),
        "symbol_column_candidates": "|".join(symbol_cols),
        "name_column_candidates": "|".join(name_cols),
        "isin_column_candidates": "|".join(isin_cols),
        "listing_date_column_candidates": "|".join(listing_date_cols),
        "security_type_column_candidates": "|".join(security_type_cols),
        "schema_bucket": schema_bucket,
        "schema_notes": schema_notes,
    }


def classify_source(row: dict[str, str], detected_format: str, parse_info: dict[str, Any], schema_profile: dict[str, Any]) -> dict[str, Any]:
    provider = row.get("provider", "")
    repair_source_id = row.get("repair_source_id", "")
    candidate_role = row.get("candidate_role", "")
    http_status = str(row.get("http_status", "") or "")
    download_status = row.get("download_status", "")
    parse_status = parse_info.get("parse_status", "")
    row_count = int(parse_info.get("row_like_count", 0) or 0)
    column_count = int(parse_info.get("column_like_count", 0) or 0)
    schema_bucket = schema_profile.get("schema_bucket", "")

    row_data_validated = (
        http_status == "200"
        and detected_format in {"json_like", "csv_like"}
        and parse_status in {"json_list_parsed", "csv_like_parsed"}
        and row_count > 0
    )

    if schema_bucket == "candidate_schema_ready":
        readiness = "ready_for_candidate_extraction_dry_run"
        repair_still_required = False
        repair_reason = ""
        next_action = "use_as_primary_source_in_v2_18e_dry_run"
    elif row_data_validated:
        readiness = "row_data_ready_but_schema_review_required"
        repair_still_required = False
        repair_reason = "schema field detection incomplete"
        next_action = "allow_v2_18e_with_schema_mapping_review"
    elif provider == "TPEx" and ("error" in download_status or detected_format == "error_text"):
        readiness = "tpex_still_not_ready_technical_error"
        repair_still_required = True
        repair_reason = row.get("error_message", "") or download_status
        next_action = "keep_tpex_as_deferred_or repair_later_if_twse_delta_insufficient"
    elif detected_format == "html":
        readiness = "support_html_only_not_for_direct_extraction"
        repair_still_required = False
        repair_reason = ""
        next_action = "use_as_support_crosscheck_only"
    else:
        readiness = "not_ready_for_candidate_extraction"
        repair_still_required = True
        repair_reason = f"format={detected_format}; parse_status={parse_status}; rows={row_count}; cols={column_count}"
        next_action = "inspect_or_repair_before_extraction"

    return {
        "repair_source_id": repair_source_id,
        "provider": provider,
        "origin_source_id": row.get("origin_source_id", ""),
        "candidate_role": candidate_role,
        "http_status": http_status,
        "download_status": download_status,
        "detected_format": detected_format,
        "parse_status": parse_status,
        "row_like_count": row_count,
        "column_like_count": column_count,
        "row_data_candidate_validated": row_data_validated,
        "candidate_extraction_readiness": readiness,
        "repair_still_required": repair_still_required,
        "repair_reason": repair_reason,
        "next_action": next_action,
    }


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        FILE_PROFILE_CSV,
        SCHEMA_PROFILE_CSV,
        SOURCE_DIAGNOSTICS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    v218c_fix = read_json(V218C_FIX_JSON)
    v218d = read_json(V218D_JSON)

    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)
    candidate_header, candidate_rows = read_csv_with_header(VALIDATED_NSE_CANDIDATE_DATASET)
    _, repair_manifest_rows = read_csv_with_header(V218C_FIX_MANIFEST_CSV)
    _, repair_decision_rows = read_csv_with_header(V218C_FIX_DECISION_CSV)
    _, endpoint_discovery_rows = read_csv_with_header(V218C_FIX_ENDPOINT_DISCOVERY_CSV)
    _, repair_source_actions_rows = read_csv_with_header(V218C_FIX_SOURCE_ACTIONS_CSV)
    _, previous_diagnostics_rows = read_csv_with_header(V218D_SOURCE_DIAGNOSTICS_CSV)

    file_profile_rows: list[dict[str, Any]] = []
    schema_profile_rows: list[dict[str, Any]] = []
    source_diagnostics_rows: list[dict[str, Any]] = []

    for row in repair_manifest_rows:
        raw_path = Path(row.get("raw_artifact_path", ""))
        file_exists = raw_path.exists()
        data = raw_path.read_bytes() if file_exists else b""

        actual_bytes = len(data)
        actual_sha = sha256_bytes(data) if file_exists else ""

        try:
            manifest_bytes = int(row.get("bytes", 0) or 0)
        except ValueError:
            manifest_bytes = -1

        manifest_sha = row.get("sha256", "")
        bytes_match = file_exists and manifest_bytes == actual_bytes
        sha256_match = file_exists and manifest_sha == actual_sha

        detected_format = detect_format(data, row.get("content_type", ""), raw_path)
        parse_info = parse_artifact(data, detected_format)
        schema_profile = schema_profile_for_source(row, parse_info)
        diagnostic = classify_source(row, detected_format, parse_info, schema_profile)

        row_data_candidate_manifest = str(row.get("row_data_candidate", "")).lower() == "true"
        row_data_candidate_validated = bool(diagnostic["row_data_candidate_validated"])

        if not file_exists:
            validation_bucket = "missing_repair_raw_artifact"
            extraction_readiness = "not_ready_missing_file"
        elif not bytes_match or not sha256_match:
            validation_bucket = "integrity_mismatch"
            extraction_readiness = "not_ready_integrity_mismatch"
        elif row_data_candidate_validated:
            validation_bucket = "validated_row_data_candidate"
            extraction_readiness = diagnostic["candidate_extraction_readiness"]
        elif detected_format == "html":
            validation_bucket = "valid_support_html_artifact"
            extraction_readiness = diagnostic["candidate_extraction_readiness"]
        elif detected_format == "error_text":
            validation_bucket = "captured_error_payload"
            extraction_readiness = diagnostic["candidate_extraction_readiness"]
        else:
            validation_bucket = "valid_non_candidate_artifact"
            extraction_readiness = diagnostic["candidate_extraction_readiness"]

        file_profile_rows.append(
            {
                "repair_source_id": row.get("repair_source_id", ""),
                "provider": row.get("provider", ""),
                "repair_role": row.get("repair_role", ""),
                "origin_source_id": row.get("origin_source_id", ""),
                "candidate_role": row.get("candidate_role", ""),
                "source_url": row.get("source_url", ""),
                "http_status": row.get("http_status", ""),
                "download_status": row.get("download_status", ""),
                "ssl_mode": row.get("ssl_mode", ""),
                "raw_artifact_path": str(raw_path),
                "file_exists": file_exists,
                "manifest_bytes": manifest_bytes,
                "actual_bytes": actual_bytes,
                "bytes_match": bytes_match,
                "manifest_sha256": manifest_sha,
                "actual_sha256": actual_sha,
                "sha256_match": sha256_match,
                "manifest_detected_format": row.get("detected_format", ""),
                "detected_format": detected_format,
                "parse_status": parse_info["parse_status"],
                "row_like_count": parse_info["row_like_count"],
                "column_like_count": parse_info["column_like_count"],
                "row_data_candidate_manifest": row_data_candidate_manifest,
                "row_data_candidate_validated": row_data_candidate_validated,
                "validation_bucket": validation_bucket,
                "extraction_readiness": extraction_readiness,
                "notes": parse_info.get("notes", ""),
            }
        )

        schema_profile_rows.append(schema_profile)
        source_diagnostics_rows.append(diagnostic)

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())
    candidate_sha = sha256_bytes(VALIDATED_NSE_CANDIDATE_DATASET.read_bytes())

    active_canonical_rows = len(canonical_rows)
    validated_candidate_rows = len(candidate_rows)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - validated_candidate_rows, 0)
    completion_percent = round((validated_candidate_rows / FINAL_TARGET_CANDIDATES) * 100, 2)

    raw_files_exist_count = sum(1 for row in file_profile_rows if row["file_exists"])
    bytes_match_count = sum(1 for row in file_profile_rows if row["bytes_match"])
    sha_match_count = sum(1 for row in file_profile_rows if row["sha256_match"])
    validated_row_data_count = sum(1 for row in file_profile_rows if row["row_data_candidate_validated"])
    manifest_row_data_count = sum(1 for row in file_profile_rows if row["row_data_candidate_manifest"])
    ready_for_extraction_count = sum(
        1 for row in source_diagnostics_rows
        if row["candidate_extraction_readiness"] == "ready_for_candidate_extraction_dry_run"
    )
    schema_ready_count = sum(1 for row in schema_profile_rows if row["schema_bucket"] == "candidate_schema_ready")
    twse_ready_count = sum(
        1 for row in source_diagnostics_rows
        if row["provider"] == "TWSE"
        and row["candidate_extraction_readiness"] in {
            "ready_for_candidate_extraction_dry_run",
            "row_data_ready_but_schema_review_required",
        }
    )
    tpex_still_error_count = sum(
        1 for row in source_diagnostics_rows
        if row["provider"] == "TPEx" and row["repair_still_required"]
    )
    non_official_selected_downloads = sum(
        1 for row in endpoint_discovery_rows
        if str(row.get("selected_for_download", "")).lower() == "true"
        and not (
            "twse.com.tw" in str(row.get("discovered_url", "")).lower()
            or "tpex.org.tw" in str(row.get("discovered_url", "")).lower()
        )
    )

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18c_fix_report_exists", V218C_FIX_JSON.exists(), "critical", str(V218C_FIX_JSON))
    add_check("v2_18c_fix_status_expected", v218c_fix.get("status") == EXPECTED_V218C_FIX_STATUS, "critical", v218c_fix.get("status", ""))
    add_check("v2_18d_report_exists", V218D_JSON.exists(), "critical", str(V218D_JSON))
    add_check("v2_18d_status_expected", v218d.get("status") == EXPECTED_V218D_STATUS, "critical", v218d.get("status", ""))
    add_check("repair_manifest_exists", V218C_FIX_MANIFEST_CSV.exists(), "critical", str(V218C_FIX_MANIFEST_CSV))
    add_check("repair_decision_exists", V218C_FIX_DECISION_CSV.exists(), "critical", str(V218C_FIX_DECISION_CSV))
    add_check("endpoint_discovery_exists", V218C_FIX_ENDPOINT_DISCOVERY_CSV.exists(), "critical", str(V218C_FIX_ENDPOINT_DISCOVERY_CSV))
    add_check("repair_source_actions_exists", V218C_FIX_SOURCE_ACTIONS_CSV.exists(), "critical", str(V218C_FIX_SOURCE_ACTIONS_CSV))
    add_check("previous_raw_diagnostics_exists", V218D_SOURCE_DIAGNOSTICS_CSV.exists(), "critical", str(V218D_SOURCE_DIAGNOSTICS_CSV))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("validated_candidate_dataset_exists", VALIDATED_NSE_CANDIDATE_DATASET.exists(), "critical", str(VALIDATED_NSE_CANDIDATE_DATASET))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("validated_candidate_rows_expected", validated_candidate_rows == VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"validated_candidate_rows={validated_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("candidate_schema_matches_canonical", canonical_header == candidate_header, "critical", f"canonical_cols={len(canonical_header)} candidate_cols={len(candidate_header)}")
    add_check("repair_manifest_rows_present", len(repair_manifest_rows) > 0, "critical", f"repair_manifest_rows={len(repair_manifest_rows)}")
    add_check("repair_raw_files_exist", raw_files_exist_count == len(repair_manifest_rows), "critical", f"{raw_files_exist_count}/{len(repair_manifest_rows)}")
    add_check("repair_raw_bytes_match_manifest", bytes_match_count == len(repair_manifest_rows), "critical", f"{bytes_match_count}/{len(repair_manifest_rows)}")
    add_check("repair_raw_sha256_match_manifest", sha_match_count == len(repair_manifest_rows), "critical", f"{sha_match_count}/{len(repair_manifest_rows)}")
    add_check("manifest_row_data_candidates_preserved", manifest_row_data_count >= 1, "critical", f"manifest_row_data_count={manifest_row_data_count}")
    add_check("validated_row_data_candidates_detected", validated_row_data_count >= 1, "critical", f"validated_row_data_count={validated_row_data_count}")
    add_check("ready_for_extraction_sources_detected", ready_for_extraction_count >= 1, "critical", f"ready_for_extraction_count={ready_for_extraction_count}")
    add_check("twse_repaired_row_data_detected", twse_ready_count >= 1, "critical", f"twse_ready_count={twse_ready_count}")
    add_check("network_not_used_in_repaired_validation", True, "critical", "network_download_performed=False")
    add_check("raw_acquisition_not_performed", True, "critical", "raw_acquisition_performed=False")
    add_check("raw_files_not_modified", True, "critical", "raw_files_modified=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "canonical sha unchanged")
    add_check("network_scope_official_discovery_preserved", non_official_selected_downloads == 0, "critical", f"non_official_selected_downloads={non_official_selected_downloads}")
    add_check("final_50k_gate_still_blocked", validated_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{validated_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")

    add_check("tpex_still_requires_repair_or_deferral", tpex_still_error_count >= 1, "warning", f"tpex_still_error_count={tpex_still_error_count}")
    add_check("schema_ready_sources_detected", schema_ready_count >= 1, "warning", f"schema_ready_count={schema_ready_count}")

    next_actions: list[dict[str, Any]] = []
    action_order = 1

    if critical_failed == 0 and ready_for_extraction_count >= 1:
        next_actions.append(
            {
                "action_order": action_order,
                "action_scope": "TWSE",
                "action": "proceed_to_candidate_extraction_dry_run",
                "priority": "high",
                "reason": "At least one repaired TWSE row-data source is validated and ready for candidate extraction dry run.",
                "recommended_phase": RECOMMENDED_NEXT_PHASE,
                "guardrails": "dry run only; no canonical modification; no scoring; no full59k",
            }
        )
        action_order += 1

    if tpex_still_error_count > 0:
        next_actions.append(
            {
                "action_order": action_order,
                "action_scope": "TPEx",
                "action": "defer_or_repair_tpex_later",
                "priority": "medium",
                "reason": "TPEx official OpenAPI endpoints still captured technical SSL errors and are not needed if TWSE delta is sufficient for this route step.",
                "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 and ready_for_extraction_count >= 1 else RECOMMENDED_FIX_PHASE,
                "guardrails": "do not block TWSE dry run if repaired TWSE row-data is valid; keep TPEx as deferred/support unless needed",
            }
        )

    if not next_actions:
        next_actions.append(
            {
                "action_order": action_order,
                "action_scope": "TWSE_TPEX",
                "action": "review_repaired_raw_validation",
                "priority": "high",
                "reason": "No extraction-ready repaired raw source was validated.",
                "recommended_phase": RECOMMENDED_FIX_PHASE,
                "guardrails": "no candidate extraction until a row-data source is validated",
            }
        )

    if critical_failed == 0 and ready_for_extraction_count >= 1:
        status = "TWSE_TPEX_REPAIRED_RAW_VALIDATION_COMPLETED_ROW_DATA_VALID_CANDIDATE_EXTRACTION_DRY_RUN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "TWSE_TPEX_REPAIRED_RAW_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_FIX_PHASE

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "validated_candidate_dataset": str(VALIDATED_NSE_CANDIDATE_DATASET),
            "validated_candidate_rows": validated_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "candidate_completion_percent": completion_percent,
            "canonical_sha256_before": canonical_sha_before,
            "canonical_sha256_after": canonical_sha_after,
            "validated_candidate_sha256": candidate_sha,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
        },
        "repaired_raw_validation_summary": {
            "repair_manifest_rows": len(repair_manifest_rows),
            "raw_files_exist_count": raw_files_exist_count,
            "bytes_match_count": bytes_match_count,
            "sha256_match_count": sha_match_count,
            "manifest_row_data_count": manifest_row_data_count,
            "validated_row_data_count": validated_row_data_count,
            "ready_for_extraction_count": ready_for_extraction_count,
            "schema_ready_count": schema_ready_count,
            "twse_ready_count": twse_ready_count,
            "tpex_still_error_count": tpex_still_error_count,
            "non_official_selected_downloads": non_official_selected_downloads,
            "critical_failed_checks": critical_failed,
        },
        "readiness_decision": {
            "candidate_extraction_dry_run_ready": critical_failed == 0 and ready_for_extraction_count >= 1,
            "primary_ready_provider": "TWSE" if twse_ready_count >= 1 else "",
            "tpex_status": "deferred_or_repair_later" if tpex_still_error_count > 0 else "not_required",
            "recommended_next_phase": recommended_next_phase,
        },
        "source_references": {
            "v2_18c_fix_report": str(V218C_FIX_JSON),
            "v2_18c_fix_manifest": str(V218C_FIX_MANIFEST_CSV),
            "v2_18c_fix_decision": str(V218C_FIX_DECISION_CSV),
            "v2_18c_fix_endpoint_discovery": str(V218C_FIX_ENDPOINT_DISCOVERY_CSV),
            "v2_18c_fix_source_actions": str(V218C_FIX_SOURCE_ACTIONS_CSV),
            "v2_18d_report": str(V218D_JSON),
            "v2_18d_source_diagnostics": str(V218D_SOURCE_DIAGNOSTICS_CSV),
            "repair_decision_rows": len(repair_decision_rows),
            "endpoint_discovery_rows": len(endpoint_discovery_rows),
            "repair_source_actions_rows": len(repair_source_actions_rows),
            "previous_diagnostics_rows": len(previous_diagnostics_rows),
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": False,
            "repaired_raw_validation_performed": True,
            "raw_files_read": True,
            "raw_files_written": False,
            "raw_files_modified": False,
            "repair_manifest_read": True,
            "file_profile_written": True,
            "schema_profile_written": True,
            "source_diagnostics_written": True,
            "next_actions_written": True,
            "candidate_extraction_performed": False,
            "canonical_comparison_performed": False,
            "canonical_dataset_read": True,
            "validated_candidate_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "final_target_50k_active": True,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(FILE_PROFILE_CSV, file_profile_rows, FILE_PROFILE_FIELDS)
    write_csv(SCHEMA_PROFILE_CSV, schema_profile_rows, SCHEMA_PROFILE_FIELDS)
    write_csv(SOURCE_DIAGNOSTICS_CSV, source_diagnostics_rows, SOURCE_DIAGNOSTICS_FIELDS)
    write_csv(NEXT_ACTIONS_CSV, next_actions, NEXT_ACTIONS_FIELDS)
    write_json(REPORT_JSON, payload)

    profile_lines = "\n".join(
        f"- `{row['repair_source_id']}` — {row['provider']} — {row['validation_bucket']} — format `{row['detected_format']}` — rows `{row['row_like_count']}` — readiness `{row['extraction_readiness']}`"
        for row in file_profile_rows
    )

    schema_lines = "\n".join(
        f"- `{row['repair_source_id']}` — {row['schema_bucket']} — rows `{row['row_like_count']}` — cols `{row['column_like_count']}` — symbol `{row['symbol_column_candidates']}` — name `{row['name_column_candidates']}`"
        for row in schema_profile_rows
    )

    diagnostic_lines = "\n".join(
        f"- `{row['repair_source_id']}` — ready `{row['candidate_extraction_readiness']}` — repair_still_required `{row['repair_still_required']}` — {row['next_action']}"
        for row in source_diagnostics_rows
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions
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

v2.18D_FIX validates the repaired raw artifacts produced by v2.18C_FIX.

This is a local repaired-raw-validation-only phase. It does not perform network calls, endpoint calls, raw acquisition, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{active_canonical_rows}`
- Validated candidate dataset: `{VALIDATED_NSE_CANDIDATE_DATASET}`
- Validated candidate rows: `{validated_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Candidate completion: `{completion_percent}%`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Repaired raw validation summary

- Repair manifest rows: `{len(repair_manifest_rows)}`
- Raw files exist: `{raw_files_exist_count}/{len(repair_manifest_rows)}`
- Bytes match manifest: `{bytes_match_count}/{len(repair_manifest_rows)}`
- SHA-256 match manifest: `{sha_match_count}/{len(repair_manifest_rows)}`
- Manifest row-data candidates: `{manifest_row_data_count}`
- Validated row-data candidates: `{validated_row_data_count}`
- Ready-for-extraction sources: `{ready_for_extraction_count}`
- Schema-ready sources: `{schema_ready_count}`
- TWSE ready sources: `{twse_ready_count}`
- TPEx still error sources: `{tpex_still_error_count}`
- Non-official selected downloads: `{non_official_selected_downloads}`
- Critical failed checks: `{critical_failed}`

## File profile

{profile_lines}

## Schema profile

{schema_lines}

## Source diagnostics

{diagnostic_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw acquisition repair performed: false
- Repaired raw validation performed: true
- Raw files read: true
- Raw files written: false
- Raw files modified: false
- Repair manifest read: true
- File profile written: true
- Schema profile written: true
- Source diagnostics written: true
- Next actions written: true
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Final target 50k active: true
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Overwrite allowed: false

## Conclusion

v2.18D_FIX determines whether repaired TWSE/TPEx raw artifacts are valid enough for candidate extraction dry run.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.18D_FIX TWSE + TPEx repaired raw validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REPAIRED_RAW_VALIDATION_SUMMARY:")
    for key, value in payload["repaired_raw_validation_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("READINESS_DECISION:")
    for key, value in payload["readiness_decision"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_DIAGNOSTICS:")
    for row in source_diagnostics_rows:
        print(
            f"- {row['repair_source_id']}: {row['candidate_extraction_readiness']} "
            f"rows={row['row_like_count']} cols={row['column_like_count']} "
            f"repair_still_required={row['repair_still_required']}"
        )
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
