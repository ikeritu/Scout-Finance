from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET


VERSION = "v2.12D"
PHASE = "HKEX Validation"
PHASE_TYPE = "validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "hkex_v2_12c"

MANIFEST_JSON = OUTPUT_DIR / "hkex_download_manifest_v2_12c.json"
RAW_XLSX = RAW_DIR / "ListOfSecurities.xlsx"
RAW_HTML = RAW_DIR / "securities_lists_page.html"
BASELINE_EXPANDED = OUTPUT_DIR / "expanded_universe_v2_11e.csv"

VALIDATION_JSON = OUTPUT_DIR / "hkex_validation_v2_12d.json"
VALIDATION_MD = OUTPUT_DIR / "hkex_validation_report_v2_12d.md"
WORKBOOK_PROFILE_CSV = OUTPUT_DIR / "hkex_workbook_profile_v2_12d.csv"
CATEGORY_PROFILE_CSV = OUTPUT_DIR / "hkex_security_category_profile_v2_12d.csv"
BASELINE_COMPARE_CSV = OUTPUT_DIR / "hkex_baseline_compare_v2_12d.csv"
DECISION_CSV = OUTPUT_DIR / "hkex_validation_decision_v2_12d.csv"
CANDIDATE_PREVIEW_CSV = OUTPUT_DIR / "hkex_candidate_preview_diagnostic_v2_12d.csv"

CURRENT_EXPANDED_ROWS = 30354
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_FULL_SOURCE = 19646

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
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.12D outputs:\n"
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
    ns = {"m": NS_MAIN}

    for si in root.findall("m:si", ns):
        text_parts = []
        for t in si.findall(".//m:t", ns):
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

    ns = {"m": NS_MAIN, "r": NS_REL}
    sheets = []
    for sheet in workbook_root.findall(".//m:sheets/m:sheet", ns):
        name = sheet.attrib.get("name", "")
        sheet_id = sheet.attrib.get("sheetId", "")
        rid = sheet.attrib.get(f"{{{NS_REL}}}id", "")
        path = rel_map.get(rid, "")
        sheets.append(
            {
                "sheet_name": name,
                "sheet_id": sheet_id,
                "relationship_id": rid,
                "xml_path": path,
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


def read_sheet_rows(zf: zipfile.ZipFile, xml_path: str, shared_strings: list[str]) -> list[list[str]]:
    if not xml_path or xml_path not in zf.namelist():
        return []

    root = ET.fromstring(zf.read(xml_path))
    rows: list[list[str]] = []

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

    return rows


HEADER_ALIASES = {
    "stock_code": ["stockcode", "stockcodes", "stockcodeoflistedsecurities", "code"],
    "name_of_securities": ["nameofsecurities", "securityname", "securitiesname", "nameofsecurity"],
    "category": ["category", "securitycategory"],
    "subcategory": ["subcategory", "subcat", "subtype", "typeofsecurities"],
    "isin": ["isin", "isincode"],
    "board_lot": ["boardlot", "boardlotsize"],
    "currency": ["currency", "tradingcurrency"],
}


def detect_header(rows: list[list[str]]) -> dict:
    best = {
        "header_row_index_zero_based": -1,
        "score": 0,
        "headers": [],
        "canonical_columns": {},
        "original_columns": {},
    }

    for idx, row in enumerate(rows[:100]):
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
        if "stock_code" in canonical_columns:
            score += 4
        if "name_of_securities" in canonical_columns:
            score += 4
        if "category" in canonical_columns:
            score += 2
        if "subcategory" in canonical_columns:
            score += 1
        if "isin" in canonical_columns:
            score += 2
        if "board_lot" in canonical_columns:
            score += 1
        if "currency" in canonical_columns:
            score += 1

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


def classify_security(category: str, subcategory: str, name: str) -> str:
    blob = f"{category} {subcategory} {name}".lower()

    non_equity_tokens = [
        "exchange traded fund",
        "etf",
        "leveraged",
        "inverse product",
        "warrant",
        "cbbc",
        "debt",
        "bond",
        "derivative",
        "structured",
        "inline warrant",
        "real estate investment trust",
        "reit",
        "depositary receipt",
        "stapled security",
    ]

    if any(token in blob for token in non_equity_tokens):
        return "NON_ORDINARY_OR_REVIEW_REQUIRED"

    equity_tokens = [
        "equity",
        "ordinary",
        "shares",
        "stock",
    ]

    if any(token in blob for token in equity_tokens):
        return "EQUITY_CANDIDATE_DIAGNOSTIC_ONLY"

    return "UNKNOWN_REVIEW_REQUIRED"


def parse_workbook(path: Path) -> tuple[list[dict], dict, list[dict], list[dict]]:
    workbook_profile: list[dict] = []
    candidate_rows: list[dict] = []
    category_counter: Counter[tuple[str, str, str]] = Counter()

    selected_sheet_summary = {
        "selected_sheet_name": "",
        "selected_sheet_xml_path": "",
        "header_row_index_zero_based": -1,
        "header_score": 0,
        "data_rows_after_header": 0,
        "candidate_rows_with_stock_code": 0,
    }

    with zipfile.ZipFile(path, "r") as zf:
        shared_strings = load_shared_strings(zf)
        sheets = workbook_sheet_paths(zf)

        parsed_sheets = []
        for sheet in sheets:
            rows = read_sheet_rows(zf, sheet["xml_path"], shared_strings)
            header = detect_header(rows)
            header_idx = int(header["header_row_index_zero_based"])
            data_rows_after_header = max(len(rows) - header_idx - 1, 0) if header_idx >= 0 else 0

            stock_col = header["canonical_columns"].get("stock_code")
            name_col = header["canonical_columns"].get("name_of_securities")
            category_col = header["canonical_columns"].get("category")
            subcategory_col = header["canonical_columns"].get("subcategory")
            isin_col = header["canonical_columns"].get("isin")
            board_lot_col = header["canonical_columns"].get("board_lot")
            currency_col = header["canonical_columns"].get("currency")

            sheet_candidates = []

            if header_idx >= 0 and stock_col is not None and name_col is not None:
                for row_number, row in enumerate(rows[header_idx + 1 :], start=header_idx + 2):
                    stock_code = row_get(row, stock_col)
                    name = row_get(row, name_col)
                    category = row_get(row, category_col)
                    subcategory = row_get(row, subcategory_col)
                    isin = row_get(row, isin_col)
                    board_lot = row_get(row, board_lot_col)
                    currency = row_get(row, currency_col)

                    if not stock_code and not name:
                        continue

                    if not stock_code:
                        continue

                    diagnostic_class = classify_security(category, subcategory, name)

                    item = {
                        "sheet_name": sheet["sheet_name"],
                        "row_number": row_number,
                        "stock_code_raw_text": stock_code,
                        "name_of_securities": name,
                        "category": category,
                        "subcategory": subcategory,
                        "isin": isin,
                        "board_lot": board_lot,
                        "currency": currency,
                        "diagnostic_security_class": diagnostic_class,
                    }
                    sheet_candidates.append(item)

                    category_counter[(category, subcategory, diagnostic_class)] += 1

            workbook_profile.append(
                {
                    "sheet_name": sheet["sheet_name"],
                    "sheet_id": sheet["sheet_id"],
                    "xml_path": sheet["xml_path"],
                    "total_rows_read": len(rows),
                    "header_row_index_zero_based": header_idx,
                    "header_score": header["score"],
                    "detected_columns": "|".join(sorted(header["canonical_columns"].keys())),
                    "original_column_labels_json": json.dumps(header["original_columns"], ensure_ascii=False),
                    "data_rows_after_header": data_rows_after_header,
                    "candidate_rows_with_stock_code": len(sheet_candidates),
                }
            )

            parsed_sheets.append(
                {
                    "sheet": sheet,
                    "rows": rows,
                    "header": header,
                    "sheet_candidates": sheet_candidates,
                    "profile": workbook_profile[-1],
                }
            )

        selected = max(
            parsed_sheets,
            key=lambda item: (
                int(item["profile"]["candidate_rows_with_stock_code"]),
                int(item["profile"]["header_score"]),
                int(item["profile"]["total_rows_read"]),
            ),
            default=None,
        )

        if selected:
            candidate_rows = selected["sheet_candidates"]
            selected_sheet_summary = {
                "selected_sheet_name": selected["sheet"]["sheet_name"],
                "selected_sheet_xml_path": selected["sheet"]["xml_path"],
                "header_row_index_zero_based": selected["header"]["header_row_index_zero_based"],
                "header_score": selected["header"]["score"],
                "data_rows_after_header": selected["profile"]["data_rows_after_header"],
                "candidate_rows_with_stock_code": len(candidate_rows),
                "detected_columns": selected["profile"]["detected_columns"],
                "original_column_labels_json": selected["profile"]["original_column_labels_json"],
            }

    category_profile = [
        {
            "category": category,
            "subcategory": subcategory,
            "diagnostic_security_class": diagnostic_class,
            "rows": count,
        }
        for (category, subcategory, diagnostic_class), count in category_counter.most_common()
    ]

    return workbook_profile, selected_sheet_summary, category_profile, candidate_rows


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

    if not RAW_XLSX.exists():
        raise SystemExit(f"Missing raw XLSX: {RAW_XLSX}")

    workbook_profile, selected_sheet, category_profile, candidate_rows = parse_workbook(RAW_XLSX)
    baseline = load_baseline(BASELINE_EXPANDED)

    unique_stock_codes = {row["stock_code_raw_text"].upper() for row in candidate_rows if row["stock_code_raw_text"]}
    unique_isins = {row["isin"].upper() for row in candidate_rows if row["isin"]}

    hkex_exchange_keys = {("HKEX", code) for code in unique_stock_codes}

    exchange_key_overlap = hkex_exchange_keys.intersection(baseline["exchange_ticker_keys"])
    ticker_text_overlap = unique_stock_codes.intersection(baseline["tickers"])
    isin_overlap = unique_isins.intersection(baseline["isins"])

    diagnostic_not_in_baseline_by_exchange_key = len(unique_stock_codes) - len(exchange_key_overlap)
    projected_rows_if_all_unique_hkex_codes_added = CURRENT_EXPANDED_ROWS + max(diagnostic_not_in_baseline_by_exchange_key, 0)
    full_source_unlocked_if_all_unique_hkex_codes_added = projected_rows_if_all_unique_hkex_codes_added >= FULL_SOURCE_THRESHOLD

    classification_counts = Counter(row["diagnostic_security_class"] for row in candidate_rows)

    stock_code_lengths = [len(code) for code in unique_stock_codes if code]
    stock_code_min_length = min(stock_code_lengths) if stock_code_lengths else 0
    stock_code_max_length = max(stock_code_lengths) if stock_code_lengths else 0
    possible_leading_zero_risk_codes = sum(1 for code in unique_stock_codes if code.isdigit() and len(code) < 5)

    critical_checks = {
        "manifest_exists": MANIFEST_JSON.exists(),
        "raw_xlsx_exists": RAW_XLSX.exists(),
        "raw_html_exists": RAW_HTML.exists(),
        "baseline_expanded_exists": baseline["exists"],
        "workbook_has_selected_sheet": bool(selected_sheet.get("selected_sheet_name")),
        "stock_code_column_detected": "stock_code" in str(selected_sheet.get("detected_columns", "")),
        "name_column_detected": "name_of_securities" in str(selected_sheet.get("detected_columns", "")),
        "candidate_rows_with_stock_code_gt_1000": len(candidate_rows) > 1000,
        "unique_stock_codes_gt_1000": len(unique_stock_codes) > 1000,
        "duplicate_exchange_ticker_keys_would_be_zero_if_exchange_hkex": len(exchange_key_overlap) == 0,
    }

    critical_passed = all(critical_checks.values())

    if critical_passed:
        validation_decision = "HKEX_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW_FULL_SOURCE_STILL_BLOCKED"
        rebuild_allowed_by_validation = True
        recommended_next_phase = "v2.12E — Rebuild Expanded Source With HKEX"
    elif len(candidate_rows) > 0 and len(unique_stock_codes) > 0:
        validation_decision = "HKEX_VALID_BUT_REQUIRES_MANUAL_REVIEW_BEFORE_REBUILD"
        rebuild_allowed_by_validation = False
        recommended_next_phase = "v2.12D_MANUAL_REVIEW_OR_PROVIDER_FALLBACK"
    else:
        validation_decision = "HKEX_VALIDATION_FAILED_OR_REFERENCE_ONLY"
        rebuild_allowed_by_validation = False
        recommended_next_phase = "v2.12A_FALLBACK_PROVIDER_ROUTE_REVIEW"

    hard_guards = {
        "phase_type": PHASE_TYPE,
        "network_download_performed": False,
        "raw_files_modified": False,
        "workbook_parsed_for_validation": True,
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

    baseline_compare = [
        {
            "metric": "baseline_expanded_path",
            "value": baseline["path"],
        },
        {
            "metric": "baseline_expanded_exists",
            "value": baseline["exists"],
        },
        {
            "metric": "baseline_rows",
            "value": baseline["rows"],
        },
        {
            "metric": "candidate_rows_with_stock_code",
            "value": len(candidate_rows),
        },
        {
            "metric": "candidate_unique_stock_codes",
            "value": len(unique_stock_codes),
        },
        {
            "metric": "candidate_unique_isins",
            "value": len(unique_isins),
        },
        {
            "metric": "candidate_exchange_key_overlap_with_baseline",
            "value": len(exchange_key_overlap),
        },
        {
            "metric": "candidate_ticker_text_overlap_with_baseline_diagnostic_only",
            "value": len(ticker_text_overlap),
        },
        {
            "metric": "candidate_isin_overlap_with_baseline",
            "value": len(isin_overlap),
        },
        {
            "metric": "diagnostic_not_in_baseline_by_exchange_key",
            "value": diagnostic_not_in_baseline_by_exchange_key,
        },
        {
            "metric": "projected_rows_if_all_unique_hkex_codes_added",
            "value": projected_rows_if_all_unique_hkex_codes_added,
        },
        {
            "metric": "full_source_unlocked_if_all_unique_hkex_codes_added",
            "value": full_source_unlocked_if_all_unique_hkex_codes_added,
        },
        {
            "metric": "rows_still_needed_after_hkex_projection",
            "value": max(FULL_SOURCE_THRESHOLD - projected_rows_if_all_unique_hkex_codes_added, 0),
        },
        {
            "metric": "possible_leading_zero_risk_codes_diagnostic",
            "value": possible_leading_zero_risk_codes,
        },
    ]

    decision_row = {
        "version": VERSION,
        "phase_type": PHASE_TYPE,
        "validation_decision": validation_decision,
        "rebuild_allowed_by_validation": rebuild_allowed_by_validation,
        "recommended_next_phase": recommended_next_phase,
        "candidate_rows_with_stock_code": len(candidate_rows),
        "candidate_unique_stock_codes": len(unique_stock_codes),
        "candidate_unique_isins": len(unique_isins),
        "diagnostic_not_in_baseline_by_exchange_key": diagnostic_not_in_baseline_by_exchange_key,
        "current_expanded_rows": CURRENT_EXPANDED_ROWS,
        "projected_rows_if_all_unique_hkex_codes_added": projected_rows_if_all_unique_hkex_codes_added,
        "full_source_threshold": FULL_SOURCE_THRESHOLD,
        "full_source_unlocked_if_all_unique_hkex_codes_added": full_source_unlocked_if_all_unique_hkex_codes_added,
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
        "manifest_counts_from_v2_12c": manifest.get("counts", {}),
        "selected_sheet": selected_sheet,
        "critical_checks": critical_checks,
        "counts": {
            "workbook_sheets_profiled": len(workbook_profile),
            "candidate_rows_with_stock_code": len(candidate_rows),
            "candidate_unique_stock_codes": len(unique_stock_codes),
            "candidate_unique_isins": len(unique_isins),
            "equity_candidate_diagnostic_only": classification_counts.get("EQUITY_CANDIDATE_DIAGNOSTIC_ONLY", 0),
            "non_ordinary_or_review_required": classification_counts.get("NON_ORDINARY_OR_REVIEW_REQUIRED", 0),
            "unknown_review_required": classification_counts.get("UNKNOWN_REVIEW_REQUIRED", 0),
            "stock_code_min_length": stock_code_min_length,
            "stock_code_max_length": stock_code_max_length,
            "possible_leading_zero_risk_codes_diagnostic": possible_leading_zero_risk_codes,
        },
        "baseline_compare": {row["metric"]: row["value"] for row in baseline_compare},
        "decision": decision_row,
        "important_scope_note": (
            "v2.12D validates raw HKEX acquisition. It does not create accepted rows, "
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
            "sheet_name",
            "sheet_id",
            "xml_path",
            "total_rows_read",
            "header_row_index_zero_based",
            "header_score",
            "detected_columns",
            "original_column_labels_json",
            "data_rows_after_header",
            "candidate_rows_with_stock_code",
        ],
    )

    write_csv(
        CATEGORY_PROFILE_CSV,
        category_profile,
        ["category", "subcategory", "diagnostic_security_class", "rows"],
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
            "candidate_rows_with_stock_code",
            "candidate_unique_stock_codes",
            "candidate_unique_isins",
            "diagnostic_not_in_baseline_by_exchange_key",
            "current_expanded_rows",
            "projected_rows_if_all_unique_hkex_codes_added",
            "full_source_threshold",
            "full_source_unlocked_if_all_unique_hkex_codes_added",
            "full_59k_universe_launched",
        ],
    )

    preview_rows = candidate_rows[:200]
    write_csv(
        CANDIDATE_PREVIEW_CSV,
        preview_rows,
        [
            "sheet_name",
            "row_number",
            "stock_code_raw_text",
            "name_of_securities",
            "category",
            "subcategory",
            "isin",
            "board_lot",
            "currency",
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

    md = f"""# {VERSION} — {PHASE}

Status: **{validation_decision}**

Phase type: **validation-only**

Generated at UTC: `{validation_payload["generated_at_utc"]}`

## Decision

- Rebuild allowed by validation: **{rebuild_allowed_by_validation}**
- Recommended next phase: **{recommended_next_phase}**
- Full 59k launched: **false**

## Selected sheet

- Sheet: `{selected_sheet.get("selected_sheet_name", "")}`
- XML path: `{selected_sheet.get("selected_sheet_xml_path", "")}`
- Header row index zero-based: {selected_sheet.get("header_row_index_zero_based", -1)}
- Header score: {selected_sheet.get("header_score", 0)}
- Detected columns: `{selected_sheet.get("detected_columns", "")}`
- Candidate rows with stock code: {len(candidate_rows)}

## Counts

- Workbook sheets profiled: {len(workbook_profile)}
- Candidate rows with stock code: {len(candidate_rows)}
- Candidate unique stock codes: {len(unique_stock_codes)}
- Candidate unique ISINs: {len(unique_isins)}
- Equity candidate diagnostic only: {classification_counts.get("EQUITY_CANDIDATE_DIAGNOSTIC_ONLY", 0)}
- Non-ordinary or review required: {classification_counts.get("NON_ORDINARY_OR_REVIEW_REQUIRED", 0)}
- Unknown review required: {classification_counts.get("UNKNOWN_REVIEW_REQUIRED", 0)}
- Stock code min length: {stock_code_min_length}
- Stock code max length: {stock_code_max_length}
- Possible leading-zero risk codes diagnostic: {possible_leading_zero_risk_codes}

## Baseline comparison

{baseline_lines}

## Critical checks

{critical_lines}

## Hard guards

{guard_lines}

## Scope note

v2.12D validates raw HKEX acquisition only.

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

    print("v2.12D HKEX validation-only completed.")
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
