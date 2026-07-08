from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET


VERSION = "v2.13D"
PHASE = "JPX Validation"
PHASE_TYPE = "validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "jpx_v2_13c"
DATASET_DIR = RAW_DIR / "datasets"

MANIFEST_JSON = OUTPUT_DIR / "jpx_download_manifest_v2_13c.json"
BASELINE_EXPANDED = OUTPUT_DIR / "expanded_universe_v2_12e.csv"

VALIDATION_JSON = OUTPUT_DIR / "jpx_validation_v2_13d.json"
VALIDATION_MD = OUTPUT_DIR / "jpx_validation_report_v2_13d.md"
WORKBOOK_PROFILE_CSV = OUTPUT_DIR / "jpx_workbook_profile_v2_13d.csv"
CATEGORY_PROFILE_CSV = OUTPUT_DIR / "jpx_security_category_profile_v2_13d.csv"
BASELINE_COMPARE_CSV = OUTPUT_DIR / "jpx_baseline_compare_v2_13d.csv"
DECISION_CSV = OUTPUT_DIR / "jpx_validation_decision_v2_13d.csv"
CANDIDATE_PREVIEW_CSV = OUTPUT_DIR / "jpx_candidate_preview_diagnostic_v2_13d.csv"

CURRENT_EXPANDED_ROWS = 33158
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_FULL_SOURCE = 16842

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        VALIDATION_JSON,
        VALIDATION_MD,
        WORKBOOK_PROFILE_CSV,
        CATEGORY_PROFILE_CSV,
        BASELINE_COMPARE_CSV,
        DECISION_CSV,
        CANDIDATE_PREVIEW_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.13D outputs:\n"
            + "\n".join(existing)
        )


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_header_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def looks_like_xlsx(path: Path) -> bool:
    return path.exists() and path.read_bytes()[:2] == b"PK"


def looks_like_xls(path: Path) -> bool:
    return path.exists() and path.read_bytes()[:4] == b"\xd0\xcf\x11\xe0"


def col_index_from_ref(cell_ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    result = 0
    for char in letters:
        result = result * 26 + (ord(char) - ord("A") + 1)
    return max(result - 1, 0)


def load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []

    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []

    for si in root.findall(f"{{{NS_MAIN}}}si"):
        text_parts = []
        for t in si.findall(f".//{{{NS_MAIN}}}t"):
            text_parts.append(t.text or "")
        strings.append("".join(text_parts))

    return strings


def workbook_sheet_paths(zf: zipfile.ZipFile) -> list[dict]:
    workbook_root = ET.fromstring(zf.read("xl/workbook.xml"))
    rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))

    rel_map = {}
    for rel in rels_root.findall(f"{{{NS_PKG_REL}}}Relationship"):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target", "")
        if rel_id:
            if target.startswith("/"):
                path = target.lstrip("/")
            elif target.startswith("xl/"):
                path = target
            else:
                path = "xl/" + target
            rel_map[rel_id] = path

    sheets = []
    for sheet in workbook_root.findall(f".//{{{NS_MAIN}}}sheets/{{{NS_MAIN}}}sheet"):
        name = sheet.attrib.get("name", "")
        sheet_id = sheet.attrib.get("sheetId", "")
        rid = sheet.attrib.get(f"{{{NS_REL}}}id", "")
        sheets.append(
            {
                "sheet_name": name,
                "sheet_id": sheet_id,
                "relationship_id": rid,
                "xml_path": rel_map.get(rid, ""),
            }
        )

    return sheets


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")

    if cell_type == "inlineStr":
        parts = []
        for text_node in cell.findall(f".//{{{NS_MAIN}}}t"):
            parts.append(text_node.text or "")
        return normalize_text("".join(parts))

    value_node = cell.find(f"{{{NS_MAIN}}}v")
    raw = "" if value_node is None else (value_node.text or "")

    if cell_type == "s":
        try:
            return normalize_text(shared_strings[int(raw)])
        except Exception:
            return normalize_text(raw)

    return normalize_text(raw)


def read_xlsx_sheet_rows(path: Path) -> list[dict]:
    parsed = []
    with zipfile.ZipFile(path, "r") as zf:
        shared_strings = load_shared_strings(zf)
        sheets = workbook_sheet_paths(zf)

        for sheet in sheets:
            xml_path = sheet["xml_path"]
            if not xml_path or xml_path not in zf.namelist():
                continue

            root = ET.fromstring(zf.read(xml_path))
            rows = []
            for row in root.findall(f".//{{{NS_MAIN}}}sheetData/{{{NS_MAIN}}}row"):
                cell_map: dict[int, str] = {}
                max_idx = -1

                for cell in row.findall(f"{{{NS_MAIN}}}c"):
                    ref = cell.attrib.get("r", "")
                    idx = col_index_from_ref(ref)
                    max_idx = max(max_idx, idx)
                    cell_map[idx] = cell_value(cell, shared_strings)

                if max_idx < 0:
                    rows.append([])
                else:
                    rows.append([cell_map.get(i, "") for i in range(max_idx + 1)])

            parsed.append(
                {
                    "file_path": str(path),
                    "file_name": path.name,
                    "file_type": "xlsx",
                    "sheet_name": sheet["sheet_name"],
                    "sheet_id": sheet["sheet_id"],
                    "rows": rows,
                    "parser": "stdlib_zip_xml",
                    "parser_error": "",
                }
            )

    return parsed


def read_xls_sheet_rows(path: Path) -> list[dict]:
    try:
        import xlrd
    except Exception as exc:
        raise SystemExit(
            "MISSING_DEPENDENCY: xlrd is required to parse JPX legacy .xls files. "
            "Run: .\\.venv\\Scripts\\python.exe -m pip install xlrd==2.0.1"
        ) from exc

    parsed = []
    workbook = xlrd.open_workbook(str(path), formatting_info=False)

    for sheet in workbook.sheets():
        rows = []
        for row_idx in range(sheet.nrows):
            values = []
            for col_idx in range(sheet.ncols):
                cell = sheet.cell(row_idx, col_idx)
                value = cell.value

                if cell.ctype == xlrd.XL_CELL_NUMBER:
                    if float(value).is_integer():
                        values.append(str(int(value)))
                    else:
                        values.append(str(value))
                else:
                    values.append(normalize_text(value))

            rows.append(values)

        parsed.append(
            {
                "file_path": str(path),
                "file_name": path.name,
                "file_type": "xls",
                "sheet_name": sheet.name,
                "sheet_id": "",
                "rows": rows,
                "parser": "xlrd",
                "parser_error": "",
            }
        )

    return parsed


HEADER_ALIASES = {
    "local_code": [
        "code",
        "localcode",
        "securitiescode",
        "issuecode",
        "stockcode",
        "codeoflistedissues",
    ],
    "company_name": [
        "name",
        "issuesname",
        "issuername",
        "companyname",
        "nameoflistedissues",
        "nameofissues",
        "securityname",
    ],
    "market_segment": [
        "market",
        "marketsegment",
        "section",
        "marketdivision",
        "newmarketsegment",
    ],
    "security_type": [
        "type",
        "securitytype",
        "producttype",
        "category",
        "typeofsecurities",
    ],
    "industry": [
        "industry",
        "33sector",
        "sector",
        "industryclassification",
    ],
    "isin": [
        "isin",
        "isincode",
    ],
    "date": [
        "date",
        "listingdate",
    ],
}


def detect_header(rows: list[list[str]]) -> dict:
    best = {
        "header_row_index_zero_based": -1,
        "score": 0,
        "headers": [],
        "canonical_columns": {},
        "original_columns": {},
    }

    for idx, row in enumerate(rows[:80]):
        normalized = [normalize_header_key(value) for value in row]
        canonical_columns: dict[str, int] = {}
        original_columns: dict[str, str] = {}

        for col_idx, key in enumerate(normalized):
            for canonical, aliases in HEADER_ALIASES.items():
                if canonical in canonical_columns:
                    continue
                if key in aliases or any(alias in key for alias in aliases):
                    canonical_columns[canonical] = col_idx
                    original_columns[canonical] = row[col_idx]

        score = 0
        if "local_code" in canonical_columns:
            score += 5
        if "company_name" in canonical_columns:
            score += 5
        if "market_segment" in canonical_columns:
            score += 3
        if "security_type" in canonical_columns:
            score += 2
        if "industry" in canonical_columns:
            score += 1
        if "isin" in canonical_columns:
            score += 2

        if score > best["score"]:
            best = {
                "header_row_index_zero_based": idx,
                "score": score,
                "headers": row,
                "canonical_columns": canonical_columns,
                "original_columns": original_columns,
            }

    return best


def row_get(row: list[str], col_idx: int | None) -> str:
    if col_idx is None or col_idx < 0 or col_idx >= len(row):
        return ""
    return normalize_text(row[col_idx])


def normalize_local_code(value: str) -> str:
    value = normalize_text(value)
    if re.fullmatch(r"\d+\.0", value):
        value = value[:-2]
    return value


def classify_jpx_security(market_segment: str, security_type: str, company_name: str) -> str:
    blob = f"{market_segment} {security_type} {company_name}".lower()

    non_common_tokens = [
        "etf",
        "etn",
        "reit",
        "infrastructure fund",
        "preferred",
        "preferred stock",
        "foreign stock",
        "foreign share",
        "beneficiary",
        "investment trust",
        "fund",
        "warrant",
        "bond",
        "debt",
        "subscription warrant",
        "certificate",
    ]

    if any(token in blob for token in non_common_tokens):
        return "NON_ORDINARY_OR_REVIEW_REQUIRED"

    equity_tokens = [
        "prime",
        "standard",
        "growth",
        "tokyo stock exchange",
        "tse",
        "domestic stock",
        "common stock",
        "stock",
    ]

    if any(token in blob for token in equity_tokens):
        return "EQUITY_CANDIDATE_DIAGNOSTIC_ONLY"

    return "UNKNOWN_REVIEW_REQUIRED"


def parse_dataset_file(path: Path) -> list[dict]:
    if looks_like_xlsx(path):
        return read_xlsx_sheet_rows(path)
    if looks_like_xls(path):
        return read_xls_sheet_rows(path)

    return [
        {
            "file_path": str(path),
            "file_name": path.name,
            "file_type": path.suffix.lower().lstrip(".") or "unknown",
            "sheet_name": "",
            "sheet_id": "",
            "rows": [],
            "parser": "unsupported",
            "parser_error": "Unsupported container for validation parser.",
        }
    ]


def extract_candidates_from_sheet(sheet_data: dict) -> tuple[dict, list[dict], Counter]:
    rows = sheet_data["rows"]
    header = detect_header(rows)
    header_idx = int(header["header_row_index_zero_based"])
    cols = header["canonical_columns"]

    candidates = []
    category_counter: Counter[tuple[str, str, str]] = Counter()

    if header_idx >= 0 and "local_code" in cols and "company_name" in cols:
        for row_number, row in enumerate(rows[header_idx + 1 :], start=header_idx + 2):
            local_code = normalize_local_code(row_get(row, cols.get("local_code")))
            company_name = row_get(row, cols.get("company_name"))
            market_segment = row_get(row, cols.get("market_segment"))
            security_type = row_get(row, cols.get("security_type"))
            industry = row_get(row, cols.get("industry"))
            isin = row_get(row, cols.get("isin"))

            if not local_code and not company_name:
                continue

            if not local_code:
                continue

            diagnostic_class = classify_jpx_security(market_segment, security_type, company_name)

            item = {
                "file_name": sheet_data["file_name"],
                "sheet_name": sheet_data["sheet_name"],
                "row_number": row_number,
                "local_code_raw_text": local_code,
                "company_name": company_name,
                "market_segment": market_segment,
                "security_type": security_type,
                "industry": industry,
                "isin": isin,
                "diagnostic_security_class": diagnostic_class,
            }

            candidates.append(item)
            category_counter[(market_segment, security_type, diagnostic_class)] += 1

    profile = {
        "file_name": sheet_data["file_name"],
        "file_path": sheet_data["file_path"],
        "file_type": sheet_data["file_type"],
        "sheet_name": sheet_data["sheet_name"],
        "sheet_id": sheet_data.get("sheet_id", ""),
        "parser": sheet_data.get("parser", ""),
        "parser_error": sheet_data.get("parser_error", ""),
        "total_rows_read": len(rows),
        "header_row_index_zero_based": header_idx,
        "header_score": header["score"],
        "detected_columns": "|".join(sorted(cols.keys())),
        "original_column_labels_json": json.dumps(header["original_columns"], ensure_ascii=False),
        "data_rows_after_header": max(len(rows) - header_idx - 1, 0) if header_idx >= 0 else 0,
        "candidate_rows_with_local_code": len(candidates),
    }

    return profile, candidates, category_counter


def load_baseline(path: Path) -> dict:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "rows": 0,
            "exchange_ticker_keys": set(),
            "isins": set(),
            "tickers": set(),
        }

    exchange_ticker_keys = set()
    isins = set()
    tickers = set()
    rows = 0

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = {field.lower(): field for field in (reader.fieldnames or [])}

        ticker_field = fields.get("ticker") or fields.get("symbol")
        exchange_field = fields.get("exchange")
        isin_field = fields.get("isin")

        for row in reader:
            rows += 1
            ticker = normalize_text(row.get(ticker_field, "")) if ticker_field else ""
            exchange = normalize_text(row.get(exchange_field, "")) if exchange_field else ""
            isin = normalize_text(row.get(isin_field, "")) if isin_field else ""

            if ticker:
                tickers.add(ticker.upper())
                if exchange:
                    exchange_ticker_keys.add((exchange.upper(), ticker.upper()))

            if isin:
                isins.add(isin.upper())

    return {
        "path": str(path),
        "exists": True,
        "rows": rows,
        "exchange_ticker_keys": exchange_ticker_keys,
        "isins": isins,
        "tickers": tickers,
    }


def main() -> None:
    no_overwrite_guard()

    manifest = read_json(MANIFEST_JSON)

    dataset_files = sorted(
        [
            path
            for path in DATASET_DIR.glob("*")
            if path.is_file() and path.suffix.lower() in {".xls", ".xlsx", ".csv"}
        ]
    )

    if not dataset_files:
        raise SystemExit(f"No JPX dataset files found under {DATASET_DIR}")

    workbook_profile: list[dict] = []
    all_candidate_rows: list[dict] = []
    category_counter: Counter[tuple[str, str, str]] = Counter()

    for dataset_file in dataset_files:
        parsed_sheets = parse_dataset_file(dataset_file)

        for sheet_data in parsed_sheets:
            profile, candidates, sheet_category_counter = extract_candidates_from_sheet(sheet_data)
            workbook_profile.append(profile)
            all_candidate_rows.extend(candidates)
            category_counter.update(sheet_category_counter)

    selected_profile = max(
        workbook_profile,
        key=lambda item: (
            int(item.get("candidate_rows_with_local_code", 0)),
            int(item.get("header_score", 0)),
            int(item.get("total_rows_read", 0)),
        ),
        default={},
    )

    # Use candidates from the best file/sheet only to avoid mixing monthly full list and update files.
    selected_file_name = selected_profile.get("file_name", "")
    selected_sheet_name = selected_profile.get("sheet_name", "")
    candidate_rows = [
        row
        for row in all_candidate_rows
        if row["file_name"] == selected_file_name and row["sheet_name"] == selected_sheet_name
    ]

    selected_category_counter = Counter(
        (
            row["market_segment"],
            row["security_type"],
            row["diagnostic_security_class"],
        )
        for row in candidate_rows
    )

    baseline = load_baseline(BASELINE_EXPANDED)

    unique_local_codes = {row["local_code_raw_text"].upper() for row in candidate_rows if row["local_code_raw_text"]}
    unique_isins = {row["isin"].upper() for row in candidate_rows if row["isin"]}

    jpx_exchange_keys = {("JPX", code) for code in unique_local_codes}

    exchange_key_overlap = jpx_exchange_keys.intersection(baseline["exchange_ticker_keys"])
    ticker_text_overlap = unique_local_codes.intersection(baseline["tickers"])
    isin_overlap = unique_isins.intersection(baseline["isins"])

    diagnostic_not_in_baseline_by_exchange_key = len(unique_local_codes) - len(exchange_key_overlap)
    projected_rows_if_all_unique_jpx_codes_added = CURRENT_EXPANDED_ROWS + max(diagnostic_not_in_baseline_by_exchange_key, 0)
    full_source_unlocked_if_all_unique_jpx_codes_added = projected_rows_if_all_unique_jpx_codes_added >= FULL_SOURCE_THRESHOLD

    classification_counts = Counter(row["diagnostic_security_class"] for row in candidate_rows)

    local_code_lengths = [len(code) for code in unique_local_codes if code]
    local_code_min_length = min(local_code_lengths) if local_code_lengths else 0
    local_code_max_length = max(local_code_lengths) if local_code_lengths else 0
    possible_leading_zero_risk_codes = sum(1 for code in unique_local_codes if code.isdigit() and len(code) < 4)

    critical_checks = {
        "manifest_exists": MANIFEST_JSON.exists(),
        "baseline_expanded_exists": baseline["exists"],
        "dataset_files_found": len(dataset_files) > 0,
        "workbook_profiled": len(workbook_profile) > 0,
        "selected_sheet_or_table_found": bool(selected_file_name),
        "local_code_column_detected": "local_code" in str(selected_profile.get("detected_columns", "")),
        "company_name_column_detected": "company_name" in str(selected_profile.get("detected_columns", "")),
        "candidate_rows_with_local_code_gt_1000": len(candidate_rows) > 1000,
        "unique_local_codes_gt_1000": len(unique_local_codes) > 1000,
        "duplicate_exchange_ticker_keys_would_be_zero_if_exchange_jpx": len(exchange_key_overlap) == 0,
    }

    critical_passed = all(critical_checks.values())

    if critical_passed:
        validation_decision = "JPX_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW_FULL_SOURCE_STILL_BLOCKED"
        rebuild_allowed_by_validation = True
        recommended_next_phase = "v2.13E - Rebuild Expanded Source With JPX"
    elif len(candidate_rows) > 0 and len(unique_local_codes) > 0:
        validation_decision = "JPX_VALID_BUT_REQUIRES_MANUAL_REVIEW_BEFORE_REBUILD"
        rebuild_allowed_by_validation = False
        recommended_next_phase = "v2.13D_MANUAL_REVIEW_OR_PROVIDER_FALLBACK"
    else:
        validation_decision = "JPX_VALIDATION_FAILED_OR_REFERENCE_ONLY"
        rebuild_allowed_by_validation = False
        recommended_next_phase = "v2.13A_FALLBACK_PROVIDER_ROUTE_REVIEW"

    hard_guards = {
        "phase_type": PHASE_TYPE,
        "network_download_performed": False,
        "raw_files_modified": False,
        "workbook_or_csv_parsed_for_validation": True,
        "normalization_performed": False,
        "net_new_filtering_performed": False,
        "diagnostic_baseline_compare_performed": True,
        "expanded_universe_rebuilt": False,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
    }

    category_profile = [
        {
            "market_segment": market_segment,
            "security_type": security_type,
            "diagnostic_security_class": diagnostic_class,
            "rows": count,
        }
        for (market_segment, security_type, diagnostic_class), count in selected_category_counter.most_common()
    ]

    baseline_compare = [
        {"metric": "baseline_expanded_path", "value": baseline["path"]},
        {"metric": "baseline_expanded_exists", "value": baseline["exists"]},
        {"metric": "baseline_rows", "value": baseline["rows"]},
        {"metric": "dataset_files_found", "value": len(dataset_files)},
        {"metric": "workbook_sheets_or_tables_profiled", "value": len(workbook_profile)},
        {"metric": "selected_file_name", "value": selected_file_name},
        {"metric": "selected_sheet_name", "value": selected_sheet_name},
        {"metric": "candidate_rows_with_local_code", "value": len(candidate_rows)},
        {"metric": "candidate_unique_local_codes", "value": len(unique_local_codes)},
        {"metric": "candidate_unique_isins", "value": len(unique_isins)},
        {"metric": "candidate_exchange_key_overlap_with_baseline", "value": len(exchange_key_overlap)},
        {"metric": "candidate_ticker_text_overlap_with_baseline_diagnostic_only", "value": len(ticker_text_overlap)},
        {"metric": "candidate_isin_overlap_with_baseline", "value": len(isin_overlap)},
        {"metric": "diagnostic_not_in_baseline_by_exchange_key", "value": diagnostic_not_in_baseline_by_exchange_key},
        {"metric": "projected_rows_if_all_unique_jpx_codes_added", "value": projected_rows_if_all_unique_jpx_codes_added},
        {"metric": "full_source_unlocked_if_all_unique_jpx_codes_added", "value": full_source_unlocked_if_all_unique_jpx_codes_added},
        {"metric": "rows_still_needed_after_jpx_projection", "value": max(FULL_SOURCE_THRESHOLD - projected_rows_if_all_unique_jpx_codes_added, 0)},
        {"metric": "possible_leading_zero_risk_codes_diagnostic", "value": possible_leading_zero_risk_codes},
    ]

    decision_row = {
        "version": VERSION,
        "phase_type": PHASE_TYPE,
        "validation_decision": validation_decision,
        "rebuild_allowed_by_validation": rebuild_allowed_by_validation,
        "recommended_next_phase": recommended_next_phase,
        "candidate_rows_with_local_code": len(candidate_rows),
        "candidate_unique_local_codes": len(unique_local_codes),
        "candidate_unique_isins": len(unique_isins),
        "diagnostic_not_in_baseline_by_exchange_key": diagnostic_not_in_baseline_by_exchange_key,
        "current_expanded_rows": CURRENT_EXPANDED_ROWS,
        "projected_rows_if_all_unique_jpx_codes_added": projected_rows_if_all_unique_jpx_codes_added,
        "full_source_threshold": FULL_SOURCE_THRESHOLD,
        "full_source_unlocked_if_all_unique_jpx_codes_added": full_source_unlocked_if_all_unique_jpx_codes_added,
        "full_59k_universe_launched": False,
    }

    validation_payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": validation_decision,
        "generated_at_utc": utc_now(),
        "rebuild_allowed_by_validation": rebuild_allowed_by_validation,
        "recommended_next_phase": recommended_next_phase,
        "hard_guards": hard_guards,
        "manifest_counts_from_v2_13c": manifest.get("counts", {}),
        "selected_dataset": selected_profile,
        "critical_checks": critical_checks,
        "counts": {
            "dataset_files_found": len(dataset_files),
            "workbook_sheets_or_tables_profiled": len(workbook_profile),
            "candidate_rows_with_local_code": len(candidate_rows),
            "candidate_unique_local_codes": len(unique_local_codes),
            "candidate_unique_isins": len(unique_isins),
            "equity_candidate_diagnostic_only": classification_counts.get("EQUITY_CANDIDATE_DIAGNOSTIC_ONLY", 0),
            "non_ordinary_or_review_required": classification_counts.get("NON_ORDINARY_OR_REVIEW_REQUIRED", 0),
            "unknown_review_required": classification_counts.get("UNKNOWN_REVIEW_REQUIRED", 0),
            "local_code_min_length": local_code_min_length,
            "local_code_max_length": local_code_max_length,
            "possible_leading_zero_risk_codes_diagnostic": possible_leading_zero_risk_codes,
        },
        "baseline_compare": {row["metric"]: row["value"] for row in baseline_compare},
        "decision": decision_row,
        "important_scope_note": (
            "v2.13D validates raw JPX acquisition. It does not create accepted rows, "
            "does not normalize into the expanded universe, does not filter final net-new rows, "
            "does not rebuild, does not score, does not call OpenAI or broker APIs, "
            "and does not launch full 59k."
        ),
    }

    write_json(VALIDATION_JSON, validation_payload)

    write_csv(
        WORKBOOK_PROFILE_CSV,
        workbook_profile,
        [
            "file_name",
            "file_path",
            "file_type",
            "sheet_name",
            "sheet_id",
            "parser",
            "parser_error",
            "total_rows_read",
            "header_row_index_zero_based",
            "header_score",
            "detected_columns",
            "original_column_labels_json",
            "data_rows_after_header",
            "candidate_rows_with_local_code",
        ],
    )

    write_csv(
        CATEGORY_PROFILE_CSV,
        category_profile,
        ["market_segment", "security_type", "diagnostic_security_class", "rows"],
    )

    write_csv(BASELINE_COMPARE_CSV, baseline_compare, ["metric", "value"])

    write_csv(
        DECISION_CSV,
        [decision_row],
        [
            "version",
            "phase_type",
            "validation_decision",
            "rebuild_allowed_by_validation",
            "recommended_next_phase",
            "candidate_rows_with_local_code",
            "candidate_unique_local_codes",
            "candidate_unique_isins",
            "diagnostic_not_in_baseline_by_exchange_key",
            "current_expanded_rows",
            "projected_rows_if_all_unique_jpx_codes_added",
            "full_source_threshold",
            "full_source_unlocked_if_all_unique_jpx_codes_added",
            "full_59k_universe_launched",
        ],
    )

    write_csv(
        CANDIDATE_PREVIEW_CSV,
        candidate_rows[:200],
        [
            "file_name",
            "sheet_name",
            "row_number",
            "local_code_raw_text",
            "company_name",
            "market_segment",
            "security_type",
            "industry",
            "isin",
            "diagnostic_security_class",
        ],
    )

    critical_lines = "\n".join(
        f"- {key}: {value}" for key, value in critical_checks.items()
    )

    baseline_lines = "\n".join(
        f"- {row['metric']}: {row['value']}" for row in baseline_compare
    )

    guard_lines = "\n".join(
        f"- {key}: {value}" for key, value in hard_guards.items()
    )

    md = f"""# {VERSION} - {PHASE}

Status: **{validation_decision}**

Phase type: **validation-only**

Generated at UTC: `{validation_payload["generated_at_utc"]}`

## Decision

- Rebuild allowed by validation: **{rebuild_allowed_by_validation}**
- Recommended next phase: **{recommended_next_phase}**
- Full 59k launched: **false**

## Selected dataset

- File: `{selected_file_name}`
- Sheet/table: `{selected_sheet_name}`
- Parser: `{selected_profile.get("parser", "")}`
- Header row index zero-based: {selected_profile.get("header_row_index_zero_based", -1)}
- Header score: {selected_profile.get("header_score", 0)}
- Detected columns: `{selected_profile.get("detected_columns", "")}`
- Candidate rows with local code: {len(candidate_rows)}

## Counts

- Dataset files found: {len(dataset_files)}
- Workbook sheets/tables profiled: {len(workbook_profile)}
- Candidate rows with local code: {len(candidate_rows)}
- Candidate unique local codes: {len(unique_local_codes)}
- Candidate unique ISINs: {len(unique_isins)}
- Equity candidate diagnostic only: {classification_counts.get("EQUITY_CANDIDATE_DIAGNOSTIC_ONLY", 0)}
- Non-ordinary or review required: {classification_counts.get("NON_ORDINARY_OR_REVIEW_REQUIRED", 0)}
- Unknown review required: {classification_counts.get("UNKNOWN_REVIEW_REQUIRED", 0)}
- Local code min length: {local_code_min_length}
- Local code max length: {local_code_max_length}
- Possible leading-zero risk codes diagnostic: {possible_leading_zero_risk_codes}

## Baseline comparison

{baseline_lines}

## Critical checks

{critical_lines}

## Hard guards

{guard_lines}

## Scope note

v2.13D validates raw JPX acquisition only.

It does not create accepted rows, does not normalize into the expanded universe, does not perform final net-new filtering, does not rebuild, does not score, does not call OpenAI or broker APIs, and does not launch full 59k.

## Outputs

- `{VALIDATION_JSON}`
- `{VALIDATION_MD}`
- `{WORKBOOK_PROFILE_CSV}`
- `{CATEGORY_PROFILE_CSV}`
- `{BASELINE_COMPARE_CSV}`
- `{DECISION_CSV}`
- `{CANDIDATE_PREVIEW_CSV}`
"""

    VALIDATION_MD.write_text(md, encoding="utf-8")

    print("v2.13D JPX validation-only completed.")
    print(f"- validation json: {VALIDATION_JSON}")
    print(f"- validation report: {VALIDATION_MD}")
    print(f"- workbook profile csv: {WORKBOOK_PROFILE_CSV}")
    print(f"- category profile csv: {CATEGORY_PROFILE_CSV}")
    print(f"- baseline compare csv: {BASELINE_COMPARE_CSV}")
    print(f"- decision csv: {DECISION_CSV}")
    print(f"- candidate preview csv: {CANDIDATE_PREVIEW_CSV}")
    print("")
    print("DECISION:")
    print(f"- status: {validation_decision}")
    print(f"- rebuild_allowed_by_validation: {rebuild_allowed_by_validation}")
    print(f"- recommended_next_phase: {recommended_next_phase}")
    print("")
    print("COUNTS:")
    for key, value in validation_payload["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("BASELINE_COMPARE:")
    for row in baseline_compare:
        print(f"- {row['metric']}: {row['value']}")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
