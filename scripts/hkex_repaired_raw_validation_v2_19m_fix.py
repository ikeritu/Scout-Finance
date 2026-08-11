from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import posixpath


VERSION = "v2.19M_FIX"
PHASE = "HKEX Repaired Raw Validation"
PHASE_TYPE = "repaired-raw-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219L_FIX_JSON = OUTPUT_DIR / "hkex_raw_acquisition_repair_v2_19l_fix.json"
V219L_FIX_MANIFEST_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_manifest_v2_19l_fix.csv"
V219L_FIX_ARTIFACT_INDEX_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_artifact_index_v2_19l_fix.csv"
V219L_FIX_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_source_diagnostics_v2_19l_fix.csv"
V219L_FIX_SELECTED_DOWNLOADS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_selected_downloads_v2_19l_fix.csv"

REPORT_JSON = OUTPUT_DIR / "hkex_repaired_raw_validation_v2_19m_fix.json"
REPORT_MD = OUTPUT_DIR / "hkex_repaired_raw_validation_v2_19m_fix.md"
ARTIFACT_AUDIT_CSV = OUTPUT_DIR / "hkex_repaired_raw_validation_artifact_audit_v2_19m_fix.csv"
WORKBOOK_INVENTORY_CSV = OUTPUT_DIR / "hkex_repaired_raw_validation_workbook_inventory_v2_19m_fix.csv"
SHEET_SCHEMA_CSV = OUTPUT_DIR / "hkex_repaired_raw_validation_sheet_schema_v2_19m_fix.csv"
PARSE_READINESS_CSV = OUTPUT_DIR / "hkex_repaired_raw_validation_parse_readiness_v2_19m_fix.csv"
ISSUE_AUDIT_CSV = OUTPUT_DIR / "hkex_repaired_raw_validation_issue_audit_v2_19m_fix.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_repaired_raw_validation_checks_v2_19m_fix.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_repaired_raw_validation_next_actions_v2_19m_fix.csv"

EXPECTED_V219L_FIX_STATUS = "HKEX_RAW_ACQUISITION_REPAIR_COMPLETED_STRUCTURED_DOWNLOADS_CAPTURED_RAW_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

STATUS_EXTRACTION_READY = "HKEX_REPAIRED_RAW_VALIDATION_COMPLETED_PARSE_READY_EXTRACTION_DRY_RUN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_REPAIR_REQUIRED = "HKEX_REPAIRED_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_FAILED = "HKEX_REPAIRED_RAW_VALIDATION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_EXTRACTION = "v2.19N - HKEX Candidate Extraction Dry Run"
NEXT_PHASE_REPAIR_REVIEW = "v2.19L_FIX_REVIEW - HKEX Raw Acquisition Repair Review"
NEXT_PHASE_VALIDATION_REVIEW = "v2.19M_FIX_REVIEW - HKEX Repaired Raw Validation Review"

ALLOWED_HOSTS = {
    "www.hkex.com.hk",
    "hkex.com.hk",
    "www.hkexnews.hk",
    "hkexnews.hk",
}

OLE_HEADER = bytes.fromhex("D0CF11E0A1B11AE1")

XLSX_EXTENSIONS = {".xlsx"}
XLS_EXTENSIONS = {".xls"}
STRUCTURED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

HEADER_CATEGORIES = {
    "stock_code": [
        "stock code",
        "security code",
        "securities code",
        "code",
        "stockcode",
    ],
    "stock_short_name": [
        "stock short name",
        "short name",
        "english stock short name",
        "stock name",
        "name of securities",
        "securities name",
        "security name",
    ],
    "issuer_or_name": [
        "issuer",
        "company",
        "company name",
        "listed company",
        "name",
        "english name",
    ],
    "board_lot": [
        "board lot",
        "lot size",
        "board lot size",
        "trading lot",
    ],
    "security_type": [
        "category",
        "security type",
        "securities type",
        "product type",
        "type",
    ],
    "board": [
        "board",
        "market",
        "listing board",
    ],
    "isin": [
        "isin",
    ],
    "currency": [
        "currency",
        "ccy",
        "trading currency",
    ],
}


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


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def official_scope_allowed(url: str) -> bool:
    parsed = urlparse(str(url))
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS


def extension_from_path(path: str) -> str:
    return Path(str(path)).suffix.lower()


def normalize_text(value: Any) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"[\s_\-\/]+", " ", value)
    value = re.sub(r"[^a-z0-9 ]+", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def cell_ref_to_col_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref.upper())
    if not match:
        return 0
    letters = match.group(1)
    value = 0
    for char in letters:
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value - 1


def load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []

    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    shared: list[str] = []

    for si in root:
        texts: list[str] = []
        for elem in si.iter():
            if elem.tag.endswith("}t") or elem.tag == "t":
                texts.append(elem.text or "")
        shared.append("".join(texts))

    return shared


def workbook_sheet_paths(zf: zipfile.ZipFile) -> list[dict[str, str]]:
    names = set(zf.namelist())

    if "xl/workbook.xml" not in names:
        return [
            {
                "sheet_name": Path(name).stem,
                "sheet_path": name,
                "relationship_id": "",
            }
            for name in sorted(names)
            if name.startswith("xl/worksheets/") and name.endswith(".xml")
        ]

    workbook_root = ET.fromstring(zf.read("xl/workbook.xml"))

    rid_to_target: dict[str, str] = {}
    if "xl/_rels/workbook.xml.rels" in names:
        rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        for rel in rels_root:
            rid = rel.attrib.get("Id", "")
            target = rel.attrib.get("Target", "")
            if target.startswith("/"):
                normalized_target = target.lstrip("/")
            else:
                normalized_target = posixpath.normpath("xl/" + target)
            rid_to_target[rid] = normalized_target

    sheets: list[dict[str, str]] = []
    for elem in workbook_root.iter():
        if not elem.tag.endswith("}sheet") and elem.tag != "sheet":
            continue
        sheet_name = elem.attrib.get("name", "")
        relationship_id = ""
        for key, value in elem.attrib.items():
            if key.endswith("}id") or key == "id":
                relationship_id = value
        sheet_path = rid_to_target.get(relationship_id, "")
        if sheet_path and sheet_path in names:
            sheets.append(
                {
                    "sheet_name": sheet_name,
                    "sheet_path": sheet_path,
                    "relationship_id": relationship_id,
                }
            )

    if sheets:
        return sheets

    return [
        {
            "sheet_name": Path(name).stem,
            "sheet_path": name,
            "relationship_id": "",
        }
        for name in sorted(names)
        if name.startswith("xl/worksheets/") and name.endswith(".xml")
    ]


def read_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    value_elem = None
    for child in cell:
        if child.tag.endswith("}v") or child.tag == "v":
            value_elem = child
            break

    if cell_type == "inlineStr":
        texts: list[str] = []
        for elem in cell.iter():
            if elem.tag.endswith("}t") or elem.tag == "t":
                texts.append(elem.text or "")
        return "".join(texts).strip()

    if value_elem is None:
        return ""

    raw_value = value_elem.text or ""

    if cell_type == "s":
        idx = to_int(raw_value, -1)
        if 0 <= idx < len(shared_strings):
            return shared_strings[idx].strip()
        return raw_value.strip()

    return raw_value.strip()


def read_sheet_rows(zf: zipfile.ZipFile, sheet_path: str, shared_strings: list[str]) -> list[list[str]]:
    root = ET.fromstring(zf.read(sheet_path))
    rows: list[list[str]] = []

    for row_elem in root.iter():
        if not row_elem.tag.endswith("}row") and row_elem.tag != "row":
            continue

        values_by_index: dict[int, str] = {}
        max_col = -1

        for cell in row_elem:
            if not cell.tag.endswith("}c") and cell.tag != "c":
                continue
            cell_ref = cell.attrib.get("r", "")
            col_index = cell_ref_to_col_index(cell_ref)
            max_col = max(max_col, col_index)
            values_by_index[col_index] = read_cell_value(cell, shared_strings)

        if max_col >= 0:
            row = [values_by_index.get(i, "") for i in range(max_col + 1)]
            if any(str(v).strip() for v in row):
                rows.append(row)

    return rows


def classify_header_cell(value: str) -> list[str]:
    normalized = normalize_text(value)
    if not normalized:
        return []

    matches: list[str] = []
    for category, patterns in HEADER_CATEGORIES.items():
        for pattern in patterns:
            pattern_norm = normalize_text(pattern)
            if normalized == pattern_norm or pattern_norm in normalized:
                matches.append(category)
                break

    return matches


def detect_header(rows: list[list[str]]) -> dict[str, Any]:
    best = {
        "header_row_index": -1,
        "header_row_number": 0,
        "score": 0,
        "categories": {},
        "headers_joined": "",
        "column_count": 0,
    }

    for idx, row in enumerate(rows[:30]):
        categories: dict[str, int] = {}
        for col_idx, value in enumerate(row):
            for category in classify_header_cell(value):
                categories.setdefault(category, col_idx)

        score = len(categories)
        has_code = "stock_code" in categories
        has_name = "stock_short_name" in categories or "issuer_or_name" in categories

        if has_code:
            score += 2
        if has_name:
            score += 1

        if score > best["score"]:
            best = {
                "header_row_index": idx,
                "header_row_number": idx + 1,
                "score": score,
                "categories": categories,
                "headers_joined": " | ".join(str(v).strip() for v in row if str(v).strip())[:1000],
                "column_count": len(row),
            }

    return best


def count_parseable_stock_rows(rows: list[list[str]], header: dict[str, Any]) -> int:
    header_row_index = to_int(header.get("header_row_index", -1), -1)
    categories = header.get("categories", {})
    if header_row_index < 0 or not isinstance(categories, dict) or "stock_code" not in categories:
        return 0

    stock_code_col = to_int(categories["stock_code"], -1)
    if stock_code_col < 0:
        return 0

    count = 0
    for row in rows[header_row_index + 1:]:
        value = str(row[stock_code_col]).strip() if stock_code_col < len(row) else ""
        if re.fullmatch(r"\d{4,5}", value):
            count += 1

    return count


def inspect_xlsx(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "xlsx_valid_zip": False,
        "xlsx_error": "",
        "sheet_count": 0,
        "sheets": [],
        "max_data_rows": 0,
        "total_data_rows": 0,
        "primary_sheet_name": "",
        "primary_sheet_path": "",
        "primary_header_row_number": 0,
        "primary_header_score": 0,
        "primary_headers_joined": "",
        "primary_parseable_stock_code_rows": 0,
        "primary_detected_columns": {},
    }

    try:
        with zipfile.ZipFile(path, "r") as zf:
            bad_file = zf.testzip()
            if bad_file:
                result["xlsx_error"] = f"bad_zip_member={bad_file}"
                return result

            result["xlsx_valid_zip"] = True
            shared_strings = load_shared_strings(zf)
            sheets = workbook_sheet_paths(zf)
            result["sheet_count"] = len(sheets)

            sheet_results: list[dict[str, Any]] = []

            for sheet in sheets:
                rows = read_sheet_rows(zf, sheet["sheet_path"], shared_strings)
                header = detect_header(rows)
                parseable_rows = count_parseable_stock_rows(rows, header)

                sheet_result = {
                    "sheet_name": sheet["sheet_name"],
                    "sheet_path": sheet["sheet_path"],
                    "data_rows": len(rows),
                    "column_count_header_row": header.get("column_count", 0),
                    "header_row_number": header.get("header_row_number", 0),
                    "header_score": header.get("score", 0),
                    "headers_joined": header.get("headers_joined", ""),
                    "detected_columns": header.get("categories", {}),
                    "parseable_stock_code_rows": parseable_rows,
                }
                sheet_results.append(sheet_result)

            result["sheets"] = sheet_results
            result["max_data_rows"] = max([row["data_rows"] for row in sheet_results], default=0)
            result["total_data_rows"] = sum(row["data_rows"] for row in sheet_results)

            primary = sorted(
                sheet_results,
                key=lambda row: (
                    row["parseable_stock_code_rows"],
                    row["header_score"],
                    row["data_rows"],
                ),
                reverse=True,
            )[0] if sheet_results else {}

            result["primary_sheet_name"] = primary.get("sheet_name", "")
            result["primary_sheet_path"] = primary.get("sheet_path", "")
            result["primary_header_row_number"] = primary.get("header_row_number", 0)
            result["primary_header_score"] = primary.get("header_score", 0)
            result["primary_headers_joined"] = primary.get("headers_joined", "")
            result["primary_parseable_stock_code_rows"] = primary.get("parseable_stock_code_rows", 0)
            result["primary_detected_columns"] = primary.get("detected_columns", {})

    except Exception as exc:
        result["xlsx_error"] = f"{type(exc).__name__}: {exc}"

    return result


def inspect_xls(path: Path) -> dict[str, Any]:
    data = path.read_bytes()[:16] if path.exists() else b""
    return {
        "xls_ole_header_valid": data.startswith(OLE_HEADER),
        "xls_binary_parse_not_attempted": True,
        "xls_validation_scope": "binary_container_integrity_only",
    }


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        ARTIFACT_AUDIT_CSV,
        WORKBOOK_INVENTORY_CSV,
        SHEET_SCHEMA_CSV,
        PARSE_READINESS_CSV,
        ISSUE_AUDIT_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219l_fix = read_json(V219L_FIX_JSON)
    _, manifest_rows = read_csv_with_header(V219L_FIX_MANIFEST_CSV)
    _, artifact_index_rows = read_csv_with_header(V219L_FIX_ARTIFACT_INDEX_CSV)
    _, source_diagnostics_rows = read_csv_with_header(V219L_FIX_SOURCE_DIAGNOSTICS_CSV)
    _, selected_download_rows = read_csv_with_header(V219L_FIX_SELECTED_DOWNLOADS_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    artifact_audit_rows: list[dict[str, Any]] = []
    workbook_inventory_rows: list[dict[str, Any]] = []
    sheet_schema_rows: list[dict[str, Any]] = []
    parse_readiness_rows: list[dict[str, Any]] = []
    issue_audit_rows: list[dict[str, Any]] = []

    for manifest in manifest_rows:
        artifact_id = manifest.get("artifact_id", "")
        source_id = manifest.get("source_id", "")
        label = manifest.get("label", "")
        requested_url = manifest.get("requested_url", "")
        final_url = manifest.get("final_url", "")
        raw_path = Path(manifest.get("raw_path", ""))
        headers_path = Path(manifest.get("headers_path", ""))
        content_type = manifest.get("content_type", "")
        declared_bytes = to_int(manifest.get("byte_count", 0))
        declared_sha = manifest.get("sha256", "")
        extension = extension_from_path(str(raw_path))

        raw_exists = raw_path.exists()
        headers_exists = headers_path.exists()
        actual_bytes = raw_path.stat().st_size if raw_exists else 0
        actual_sha = sha256_file(raw_path) if raw_exists else ""
        bytes_match = declared_bytes == actual_bytes
        sha256_match = declared_sha == actual_sha
        http_success = to_bool(manifest.get("http_success", False))
        http_status = to_int(manifest.get("http_status", 0))
        requested_official_scope = official_scope_allowed(requested_url)
        final_official_scope = official_scope_allowed(final_url)

        xlsx_info: dict[str, Any] = {}
        xls_info: dict[str, Any] = {}

        if raw_exists and extension in XLSX_EXTENSIONS:
            xlsx_info = inspect_xlsx(raw_path)
        elif raw_exists and extension in XLS_EXTENSIONS:
            xls_info = inspect_xls(raw_path)

        is_top_primary_full_list = "ListOfSecurities.xlsx" in requested_url or artifact_id == "hkex_repair_01_full_list_of_securities"

        xlsx_valid_zip = bool(xlsx_info.get("xlsx_valid_zip", False))
        xls_ole_valid = bool(xls_info.get("xls_ole_header_valid", False))
        primary_parseable_stock_rows = to_int(xlsx_info.get("primary_parseable_stock_code_rows", 0))
        detected_columns = xlsx_info.get("primary_detected_columns", {})
        has_stock_code_column = isinstance(detected_columns, dict) and "stock_code" in detected_columns
        has_name_column = isinstance(detected_columns, dict) and (
            "stock_short_name" in detected_columns or "issuer_or_name" in detected_columns
        )

        primary_parse_ready = (
            is_top_primary_full_list
            and extension == ".xlsx"
            and xlsx_valid_zip
            and primary_parseable_stock_rows >= 100
            and has_stock_code_column
            and has_name_column
            and raw_exists
            and bytes_match
            and sha256_match
            and http_success
            and requested_official_scope
            and final_official_scope
        )

        support_structured_valid = (
            not primary_parse_ready
            and extension in STRUCTURED_EXTENSIONS
            and raw_exists
            and actual_bytes > 0
            and bytes_match
            and sha256_match
            and http_success
            and requested_official_scope
            and final_official_scope
            and (xlsx_valid_zip or xls_ole_valid or extension == ".csv")
        )

        if primary_parse_ready:
            readiness_status = "primary_parse_ready_for_candidate_extraction_dry_run"
        elif is_top_primary_full_list:
            readiness_status = "primary_full_list_present_but_schema_not_parse_ready"
        elif support_structured_valid:
            readiness_status = "supporting_structured_file_validated"
        elif extension in XLS_EXTENSIONS:
            readiness_status = "xls_binary_support_file_requires_optional_parser_if_needed"
        else:
            readiness_status = "not_parse_ready"

        artifact_audit_rows.append(
            {
                "artifact_id": artifact_id,
                "source_id": source_id,
                "label": label,
                "raw_path": str(raw_path),
                "headers_path": str(headers_path),
                "extension": extension,
                "content_type": content_type,
                "raw_exists": raw_exists,
                "headers_exists": headers_exists,
                "declared_bytes": declared_bytes,
                "actual_bytes": actual_bytes,
                "bytes_match": bytes_match,
                "declared_sha256": declared_sha,
                "actual_sha256": actual_sha,
                "sha256_match": sha256_match,
                "http_status": http_status,
                "http_success": http_success,
                "requested_official_scope": requested_official_scope,
                "final_official_scope": final_official_scope,
                "xlsx_valid_zip": xlsx_valid_zip,
                "xls_ole_header_valid": xls_ole_valid,
                "is_top_primary_full_list": is_top_primary_full_list,
            }
        )

        workbook_inventory_rows.append(
            {
                "artifact_id": artifact_id,
                "source_id": source_id,
                "label": label,
                "extension": extension,
                "xlsx_valid_zip": xlsx_valid_zip,
                "xlsx_error": xlsx_info.get("xlsx_error", ""),
                "xls_ole_header_valid": xls_ole_valid,
                "sheet_count": xlsx_info.get("sheet_count", 0),
                "max_data_rows": xlsx_info.get("max_data_rows", 0),
                "total_data_rows": xlsx_info.get("total_data_rows", 0),
                "primary_sheet_name": xlsx_info.get("primary_sheet_name", ""),
                "primary_sheet_path": xlsx_info.get("primary_sheet_path", ""),
                "primary_header_row_number": xlsx_info.get("primary_header_row_number", 0),
                "primary_header_score": xlsx_info.get("primary_header_score", 0),
                "primary_parseable_stock_code_rows": primary_parseable_stock_rows,
                "primary_headers_joined": xlsx_info.get("primary_headers_joined", ""),
            }
        )

        for sheet in xlsx_info.get("sheets", []) if isinstance(xlsx_info.get("sheets", []), list) else []:
            detected = sheet.get("detected_columns", {})
            sheet_schema_rows.append(
                {
                    "artifact_id": artifact_id,
                    "source_id": source_id,
                    "label": label,
                    "sheet_name": sheet.get("sheet_name", ""),
                    "sheet_path": sheet.get("sheet_path", ""),
                    "data_rows": sheet.get("data_rows", 0),
                    "header_row_number": sheet.get("header_row_number", 0),
                    "header_score": sheet.get("header_score", 0),
                    "parseable_stock_code_rows": sheet.get("parseable_stock_code_rows", 0),
                    "has_stock_code_column": isinstance(detected, dict) and "stock_code" in detected,
                    "has_stock_short_name_column": isinstance(detected, dict) and "stock_short_name" in detected,
                    "has_issuer_or_name_column": isinstance(detected, dict) and "issuer_or_name" in detected,
                    "has_board_lot_column": isinstance(detected, dict) and "board_lot" in detected,
                    "has_security_type_column": isinstance(detected, dict) and "security_type" in detected,
                    "has_isin_column": isinstance(detected, dict) and "isin" in detected,
                    "detected_columns_json": json.dumps(detected, ensure_ascii=False, sort_keys=True),
                    "headers_joined": sheet.get("headers_joined", ""),
                }
            )

        parse_readiness_rows.append(
            {
                "artifact_id": artifact_id,
                "source_id": source_id,
                "label": label,
                "is_top_primary_full_list": is_top_primary_full_list,
                "primary_parse_ready": primary_parse_ready,
                "support_structured_valid": support_structured_valid,
                "readiness_status": readiness_status,
                "extension": extension,
                "xlsx_valid_zip": xlsx_valid_zip,
                "xls_ole_header_valid": xls_ole_valid,
                "primary_sheet_name": xlsx_info.get("primary_sheet_name", ""),
                "primary_header_score": xlsx_info.get("primary_header_score", 0),
                "primary_parseable_stock_code_rows": primary_parseable_stock_rows,
                "has_stock_code_column": has_stock_code_column,
                "has_name_column": has_name_column,
                "extraction_dry_run_allowed": primary_parse_ready,
                "candidate_extraction_phase": "v2.19N" if primary_parse_ready else "not_allowed_from_this_artifact",
            }
        )

        if not raw_exists:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_MFIX_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "artifact_id": artifact_id,
                    "issue": "raw_file_missing",
                    "detail": str(raw_path),
                }
            )
        if raw_exists and actual_bytes <= 0:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_MFIX_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "artifact_id": artifact_id,
                    "issue": "raw_file_empty",
                    "detail": str(raw_path),
                }
            )
        if raw_exists and not bytes_match:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_MFIX_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "artifact_id": artifact_id,
                    "issue": "byte_count_mismatch",
                    "detail": f"declared={declared_bytes}; actual={actual_bytes}",
                }
            )
        if raw_exists and not sha256_match:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_MFIX_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "artifact_id": artifact_id,
                    "issue": "sha256_mismatch",
                    "detail": f"declared={declared_sha}; actual={actual_sha}",
                }
            )
        if not requested_official_scope or not final_official_scope:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_MFIX_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "artifact_id": artifact_id,
                    "issue": "official_scope_violation",
                    "detail": f"requested={requested_url}; final={final_url}",
                }
            )
        if is_top_primary_full_list and not primary_parse_ready:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_MFIX_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "artifact_id": artifact_id,
                    "issue": "top_primary_full_list_not_parse_ready",
                    "detail": f"xlsx_valid={xlsx_valid_zip}; stock_rows={primary_parseable_stock_rows}; stock_code_col={has_stock_code_column}; name_col={has_name_column}",
                }
            )

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    artifacts_total = len(artifact_audit_rows)
    raw_files_exist_count = sum(1 for row in artifact_audit_rows if row["raw_exists"])
    headers_exist_count = sum(1 for row in artifact_audit_rows if row["headers_exists"])
    nonempty_raw_count = sum(1 for row in artifact_audit_rows if to_int(row["actual_bytes"]) > 0)
    bytes_match_count = sum(1 for row in artifact_audit_rows if row["bytes_match"])
    sha256_match_count = sum(1 for row in artifact_audit_rows if row["sha256_match"])
    http_success_count = sum(1 for row in artifact_audit_rows if row["http_success"])
    official_scope_violations = sum(
        1 for row in artifact_audit_rows
        if not row["requested_official_scope"] or not row["final_official_scope"]
    )
    xlsx_valid_count = sum(1 for row in artifact_audit_rows if row["xlsx_valid_zip"])
    xls_ole_valid_count = sum(1 for row in artifact_audit_rows if row["xls_ole_header_valid"])
    primary_parse_ready_count = sum(1 for row in parse_readiness_rows if row["primary_parse_ready"])
    support_structured_valid_count = sum(1 for row in parse_readiness_rows if row["support_structured_valid"])
    extraction_dry_run_allowed_count = sum(1 for row in parse_readiness_rows if row["extraction_dry_run_allowed"])
    critical_issue_count = sum(1 for row in issue_audit_rows if row["severity"] == "critical")
    warning_issue_count = sum(1 for row in issue_audit_rows if row["severity"] == "warning")

    top_primary = next(
        (row for row in parse_readiness_rows if row["is_top_primary_full_list"]),
        {},
    )

    top_primary_parse_ready = bool(top_primary.get("primary_parse_ready", False))
    top_primary_stock_rows = to_int(top_primary.get("primary_parseable_stock_code_rows", 0))

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19l_fix_report_exists", V219L_FIX_JSON.exists(), "critical", str(V219L_FIX_JSON))
    add_check("v2_19l_fix_status_expected", v219l_fix.get("status") == EXPECTED_V219L_FIX_STATUS, "critical", str(v219l_fix.get("status", "")))
    add_check("repair_manifest_exists", V219L_FIX_MANIFEST_CSV.exists(), "critical", str(V219L_FIX_MANIFEST_CSV))
    add_check("repair_manifest_rows_expected", len(manifest_rows) == 9, "critical", f"manifest_rows={len(manifest_rows)}")
    add_check("repair_artifact_index_exists", V219L_FIX_ARTIFACT_INDEX_CSV.exists(), "critical", str(V219L_FIX_ARTIFACT_INDEX_CSV))
    add_check("repair_artifact_index_rows_expected", len(artifact_index_rows) == 9, "critical", f"artifact_index_rows={len(artifact_index_rows)}")
    add_check("repair_source_diagnostics_exists", V219L_FIX_SOURCE_DIAGNOSTICS_CSV.exists(), "critical", str(V219L_FIX_SOURCE_DIAGNOSTICS_CSV))
    add_check("repair_selected_downloads_exists", V219L_FIX_SELECTED_DOWNLOADS_CSV.exists(), "critical", str(V219L_FIX_SELECTED_DOWNLOADS_CSV))
    add_check("repair_selected_downloads_rows_expected", len(selected_download_rows) == 9, "critical", f"selected_download_rows={len(selected_download_rows)}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("artifact_audit_rows_expected", artifacts_total == 9, "critical", f"artifact_audit_rows={artifacts_total}")
    add_check("raw_files_exist", raw_files_exist_count == artifacts_total, "critical", f"raw_files_exist={raw_files_exist_count}/{artifacts_total}")
    add_check("headers_exist", headers_exist_count == artifacts_total, "critical", f"headers_exist={headers_exist_count}/{artifacts_total}")
    add_check("raw_files_nonempty", nonempty_raw_count == artifacts_total, "critical", f"nonempty_raw_count={nonempty_raw_count}/{artifacts_total}")
    add_check("bytes_match", bytes_match_count == artifacts_total, "critical", f"bytes_match={bytes_match_count}/{artifacts_total}")
    add_check("sha256_match", sha256_match_count == artifacts_total, "critical", f"sha256_match={sha256_match_count}/{artifacts_total}")
    add_check("http_success", http_success_count == artifacts_total, "critical", f"http_success={http_success_count}/{artifacts_total}")
    add_check("official_scope_no_violations", official_scope_violations == 0, "critical", f"official_scope_violations={official_scope_violations}")
    add_check("xlsx_valid_count_documented", xlsx_valid_count >= 1, "critical", f"xlsx_valid_count={xlsx_valid_count}")
    add_check("xls_ole_valid_count_documented", xls_ole_valid_count >= 1, "warning", f"xls_ole_valid_count={xls_ole_valid_count}")
    add_check("top_primary_full_list_parse_ready", top_primary_parse_ready, "critical", f"top_primary_parse_ready={top_primary_parse_ready}; stock_rows={top_primary_stock_rows}")
    add_check("primary_parse_ready_count_positive", primary_parse_ready_count >= 1, "critical", f"primary_parse_ready_count={primary_parse_ready_count}")
    add_check("extraction_dry_run_allowed_count_positive", extraction_dry_run_allowed_count >= 1, "critical", f"extraction_dry_run_allowed_count={extraction_dry_run_allowed_count}")
    add_check("support_structured_valid_count_documented", support_structured_valid_count >= 1, "warning", f"support_structured_valid_count={support_structured_valid_count}")
    add_check("critical_issue_count_zero", critical_issue_count == 0, "critical", f"critical_issue_count={critical_issue_count}")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("network_not_used_by_repaired_raw_validation", True, "critical", "network_download_performed=False")
    add_check("raw_files_read", True, "critical", "raw_files_read=True")
    add_check("raw_files_written_false", True, "critical", "raw_files_written=False")
    add_check("repaired_raw_validation_performed", True, "critical", "repaired_raw_validation_performed=True")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed == 0 and top_primary_parse_ready:
        status = STATUS_EXTRACTION_READY
        recommended_next_phase = NEXT_PHASE_EXTRACTION
    elif critical_failed == 0:
        status = STATUS_REPAIR_REQUIRED
        recommended_next_phase = NEXT_PHASE_REPAIR_REVIEW
    else:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_VALIDATION_REVIEW

    next_actions_rows: list[dict[str, Any]]
    if recommended_next_phase == NEXT_PHASE_EXTRACTION:
        next_actions_rows = [
            {
                "action_order": 1,
                "action_scope": "HKEX",
                "action": "run_candidate_extraction_dry_run",
                "priority": "high",
                "reason": "ListOfSecurities.xlsx validated as primary parse-ready source.",
                "recommended_phase": NEXT_PHASE_EXTRACTION,
                "guardrails": "dry run only; do not modify canonical; do not replace active universe",
            },
            {
                "action_order": 2,
                "action_scope": "HKEX",
                "action": "extract_from_primary_full_list_only_first",
                "priority": "high",
                "reason": "The primary full list has parseable stock-code rows and detected name/code schema.",
                "recommended_phase": NEXT_PHASE_EXTRACTION,
                "guardrails": "separate extraction from canonical validation",
            },
            {
                "action_order": 3,
                "action_scope": "50k",
                "action": "preserve_quality_gate",
                "priority": "high",
                "reason": "Current candidate universe remains 40,996; rows needed to 50k remain 9,004.",
                "recommended_phase": NEXT_PHASE_EXTRACTION,
                "guardrails": "do not launch full59k",
            },
        ]
    else:
        next_actions_rows = [
            {
                "action_order": 1,
                "action_scope": "HKEX",
                "action": "review_repaired_raw_schema",
                "priority": "high",
                "reason": "Repaired raw artifacts did not satisfy primary parse-ready gate.",
                "recommended_phase": recommended_next_phase,
                "guardrails": "no candidate extraction",
            }
        ]

    validation_summary = {
        "manifest_rows": len(manifest_rows),
        "artifact_audit_rows": artifacts_total,
        "raw_files_exist_count": raw_files_exist_count,
        "headers_exist_count": headers_exist_count,
        "nonempty_raw_count": nonempty_raw_count,
        "bytes_match_count": bytes_match_count,
        "sha256_match_count": sha256_match_count,
        "http_success_count": http_success_count,
        "official_scope_violations": official_scope_violations,
        "xlsx_valid_count": xlsx_valid_count,
        "xls_ole_valid_count": xls_ole_valid_count,
        "primary_parse_ready_count": primary_parse_ready_count,
        "support_structured_valid_count": support_structured_valid_count,
        "extraction_dry_run_allowed_count": extraction_dry_run_allowed_count,
        "top_primary_full_list_parse_ready": top_primary_parse_ready,
        "top_primary_parseable_stock_code_rows": top_primary_stock_rows,
        "critical_issue_count": critical_issue_count,
        "warning_issue_count": warning_issue_count,
        "critical_failed_checks": critical_failed,
        "current_validated_candidate_rows": current_candidate_rows,
        "rows_needed_to_50k": rows_needed_to_50k,
        "final_50k_candidate_gate": "BLOCKED",
        "full59k": "DEPRECATED_DEFERRED",
    }

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
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "current_candidate_sha256_before": candidate_sha_before,
            "current_candidate_sha256_after": candidate_sha_after,
        },
        "v2_19l_fix_context": {
            "status": v219l_fix.get("status"),
            "phase_type": v219l_fix.get("phase_type"),
            "selected_download_rows": v219l_fix.get("repair_summary", {}).get("selected_download_rows"),
            "artifacts_written_count": v219l_fix.get("repair_summary", {}).get("artifacts_written_count"),
            "structured_extension_count": v219l_fix.get("repair_summary", {}).get("structured_extension_count"),
            "top_primary_full_list_captured": v219l_fix.get("repair_summary", {}).get("top_primary_full_list_captured"),
            "recommended_next_phase": v219l_fix.get("recommended_next_phase"),
        },
        "validation_summary": validation_summary,
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
            "repaired_raw_validation_performed": True,
            "raw_files_read": True,
            "raw_files_written": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": candidate_sha_before == candidate_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
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

    write_csv(
        ARTIFACT_AUDIT_CSV,
        artifact_audit_rows,
        [
            "artifact_id",
            "source_id",
            "label",
            "raw_path",
            "headers_path",
            "extension",
            "content_type",
            "raw_exists",
            "headers_exists",
            "declared_bytes",
            "actual_bytes",
            "bytes_match",
            "declared_sha256",
            "actual_sha256",
            "sha256_match",
            "http_status",
            "http_success",
            "requested_official_scope",
            "final_official_scope",
            "xlsx_valid_zip",
            "xls_ole_header_valid",
            "is_top_primary_full_list",
        ],
    )
    write_csv(
        WORKBOOK_INVENTORY_CSV,
        workbook_inventory_rows,
        [
            "artifact_id",
            "source_id",
            "label",
            "extension",
            "xlsx_valid_zip",
            "xlsx_error",
            "xls_ole_header_valid",
            "sheet_count",
            "max_data_rows",
            "total_data_rows",
            "primary_sheet_name",
            "primary_sheet_path",
            "primary_header_row_number",
            "primary_header_score",
            "primary_parseable_stock_code_rows",
            "primary_headers_joined",
        ],
    )
    write_csv(
        SHEET_SCHEMA_CSV,
        sheet_schema_rows,
        [
            "artifact_id",
            "source_id",
            "label",
            "sheet_name",
            "sheet_path",
            "data_rows",
            "header_row_number",
            "header_score",
            "parseable_stock_code_rows",
            "has_stock_code_column",
            "has_stock_short_name_column",
            "has_issuer_or_name_column",
            "has_board_lot_column",
            "has_security_type_column",
            "has_isin_column",
            "detected_columns_json",
            "headers_joined",
        ],
    )
    write_csv(
        PARSE_READINESS_CSV,
        parse_readiness_rows,
        [
            "artifact_id",
            "source_id",
            "label",
            "is_top_primary_full_list",
            "primary_parse_ready",
            "support_structured_valid",
            "readiness_status",
            "extension",
            "xlsx_valid_zip",
            "xls_ole_header_valid",
            "primary_sheet_name",
            "primary_header_score",
            "primary_parseable_stock_code_rows",
            "has_stock_code_column",
            "has_name_column",
            "extraction_dry_run_allowed",
            "candidate_extraction_phase",
        ],
    )
    write_csv(ISSUE_AUDIT_CSV, issue_audit_rows, ["issue_id", "severity", "artifact_id", "issue", "detail"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    parse_lines = "\n".join(
        f"- `{row['artifact_id']}` — {row['readiness_status']} — extraction_allowed `{row['extraction_dry_run_allowed']}` — rows `{row['primary_parseable_stock_code_rows']}`"
        for row in parse_readiness_rows
    )

    workbook_lines = "\n".join(
        f"- `{row['artifact_id']}` — ext `{row['extension']}` — sheets `{row['sheet_count']}` — primary rows `{row['primary_parseable_stock_code_rows']}`"
        for row in workbook_inventory_rows
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

v2.19M_FIX validates the repaired HKEX structured raw files captured in v2.19L_FIX.

This phase performs repaired raw validation only. It reads repaired raw files and inspects workbook/container structure. It does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

- Manifest rows: `{len(manifest_rows)}`
- Artifact audit rows: `{artifacts_total}`
- Raw files exist: `{raw_files_exist_count}/{artifacts_total}`
- Headers exist: `{headers_exist_count}/{artifacts_total}`
- Non-empty raw files: `{nonempty_raw_count}/{artifacts_total}`
- Bytes match: `{bytes_match_count}/{artifacts_total}`
- SHA256 match: `{sha256_match_count}/{artifacts_total}`
- HTTP success: `{http_success_count}/{artifacts_total}`
- Official scope violations: `{official_scope_violations}`
- XLSX valid count: `{xlsx_valid_count}`
- XLS OLE valid count: `{xls_ole_valid_count}`
- Primary parse-ready count: `{primary_parse_ready_count}`
- Extraction dry-run allowed count: `{extraction_dry_run_allowed_count}`
- Top primary parse-ready: `{top_primary_parse_ready}`
- Top primary parseable stock-code rows: `{top_primary_stock_rows}`
- Critical issue count: `{critical_issue_count}`
- Warning issue count: `{warning_issue_count}`

## Workbook inventory

{workbook_lines}

## Parse readiness

{parse_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Repaired raw validation performed: true
- Raw files read: true
- Raw files written: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{candidate_sha_before == candidate_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
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

    print("v2.19M_FIX HKEX repaired raw validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in validation_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("PARSE_READINESS:")
    for row in parse_readiness_rows:
        print(f"- {row['artifact_id']}: readiness={row['readiness_status']} primary_parse_ready={row['primary_parse_ready']} extraction_allowed={row['extraction_dry_run_allowed']} rows={row['primary_parseable_stock_code_rows']}")
    print("")
    print("WORKBOOK_INVENTORY:")
    for row in workbook_inventory_rows:
        print(f"- {row['artifact_id']}: ext={row['extension']} xlsx_valid={row['xlsx_valid_zip']} xls_ole={row['xls_ole_header_valid']} sheets={row['sheet_count']} primary_rows={row['primary_parseable_stock_code_rows']}")
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
