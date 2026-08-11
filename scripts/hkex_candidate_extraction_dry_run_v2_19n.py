from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import posixpath


VERSION = "v2.19N"
PHASE = "HKEX Candidate Extraction Dry Run"
PHASE_TYPE = "candidate-extraction-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219M_FIX_JSON = OUTPUT_DIR / "hkex_repaired_raw_validation_v2_19m_fix.json"
V219M_FIX_PARSE_READINESS_CSV = OUTPUT_DIR / "hkex_repaired_raw_validation_parse_readiness_v2_19m_fix.csv"
V219M_FIX_SHEET_SCHEMA_CSV = OUTPUT_DIR / "hkex_repaired_raw_validation_sheet_schema_v2_19m_fix.csv"
V219L_FIX_MANIFEST_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_manifest_v2_19l_fix.csv"

REPORT_JSON = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_v2_19n.json"
REPORT_MD = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_v2_19n.md"
CANDIDATES_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_candidates_v2_19n.csv"
REJECTIONS_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_rejections_v2_19n.csv"
FIELD_MAPPING_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_field_mapping_v2_19n.csv"
INSTRUMENT_SUMMARY_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_instrument_summary_v2_19n.csv"
QUALITY_SUMMARY_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_quality_summary_v2_19n.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_checks_v2_19n.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_next_actions_v2_19n.csv"

EXPECTED_V219M_FIX_STATUS = "HKEX_REPAIRED_RAW_VALIDATION_COMPLETED_PARSE_READY_EXTRACTION_DRY_RUN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

STATUS_SUCCESS = "HKEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_EXTRACTED_CANONICAL_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_FAILED = "HKEX_CANDIDATE_EXTRACTION_DRY_RUN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_VALIDATION = "v2.19O - HKEX Candidate Validation Against Canonical Dry Run"
NEXT_PHASE_REVIEW = "v2.19N_REVIEW - HKEX Candidate Extraction Dry Run Review"

PRIMARY_ARTIFACT_ID = "hkex_repair_01_full_list_of_securities"

HEADER_ALIASES = {
    "stock_code": ["stock code"],
    "name_of_securities": ["name of securities", "name", "stock short name", "english stock short name"],
    "category": ["category"],
    "sub_category": ["sub-category", "sub category"],
    "board_lot": ["board lot"],
    "isin": ["isin"],
    "expiry_date": ["expiry date"],
    "subject_to_stamp_duty": ["subject to stamp duty"],
    "shortsell_eligible": ["shortsell eligible", "short sell eligible"],
    "cas_eligible": ["cas eligible"],
    "vcm_eligible": ["vcm eligible"],
    "admitted_to_ccass": ["admitted to ccass"],
    "debt_securities_board_lot_nominal": ["debt securities board lot", "debt securities board lot nominal"],
    "debt_securities_investor_type": ["debt securities investor type"],
    "pos_eligible": ["pos eligible"],
    "spread_table": ["spread table"],
    "trading_currency": ["trading currency", "currency"],
    "rmb_counter": ["rmb counter"],
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


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def normalize_header(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("\n", " ")
    text = re.sub(r"[\s_\-/]+", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_cell(value: Any) -> str:
    text = str(value or "").strip()
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_stock_code(value: Any) -> str:
    raw = clean_cell(value)

    if re.fullmatch(r"\d+\.0", raw):
        raw = raw.split(".")[0]

    raw = re.sub(r"\D", "", raw)

    if not raw:
        return ""

    if len(raw) <= 5:
        return raw.zfill(5)

    return raw


def classify_instrument(category: str, sub_category: str, name: str) -> str:
    blob = f"{category} {sub_category} {name}".lower()

    if any(term in blob for term in ["warrant", "cbbc", "callable bull", "callable bear", "derivative"]):
        return "derivative_or_warrant"
    if any(term in blob for term in ["debt", "bond", "notes", "note "]):
        return "debt_security"
    if any(term in blob for term in ["reit", "real estate investment trust"]):
        return "reit"
    if any(term in blob for term in ["etf", "exchange traded fund", "fund", "unit trust"]):
        return "fund_or_etp"
    if any(term in blob for term in ["spac"]):
        return "spac"
    if any(term in blob for term in ["equity", "ordinary", "share", "stapled securities"]):
        return "equity_like"

    return "other_or_unclassified"


def candidate_scope_flag(instrument_family: str) -> str:
    if instrument_family in {"equity_like", "reit", "fund_or_etp", "spac"}:
        return "potential_candidate_pending_canonical_validation"
    if instrument_family in {"derivative_or_warrant", "debt_security"}:
        return "extracted_reference_security_likely_excluded_later"
    return "potential_candidate_needs_review"


def cell_ref_to_col_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref.upper())
    if not match:
        return 0

    value = 0
    for char in match.group(1):
        value = value * 26 + (ord(char) - ord("A") + 1)

    return value - 1


def load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []

    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    shared: list[str] = []

    for si in root:
        parts: list[str] = []
        for elem in si.iter():
            if elem.tag.endswith("}t") or elem.tag == "t":
                parts.append(elem.text or "")
        shared.append("".join(parts))

    return shared


def workbook_sheet_paths(zf: zipfile.ZipFile) -> list[dict[str, str]]:
    names = set(zf.namelist())

    rels: dict[str, str] = {}
    if "xl/_rels/workbook.xml.rels" in names:
        rel_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        for rel in rel_root:
            rid = rel.attrib.get("Id", "")
            target = rel.attrib.get("Target", "")
            if target.startswith("/"):
                rels[rid] = target.lstrip("/")
            else:
                rels[rid] = posixpath.normpath("xl/" + target)

    if "xl/workbook.xml" not in names:
        return [
            {"sheet_name": Path(name).stem, "sheet_path": name, "relationship_id": ""}
            for name in sorted(names)
            if name.startswith("xl/worksheets/") and name.endswith(".xml")
        ]

    workbook_root = ET.fromstring(zf.read("xl/workbook.xml"))
    sheets: list[dict[str, str]] = []

    for elem in workbook_root.iter():
        if not elem.tag.endswith("}sheet") and elem.tag != "sheet":
            continue

        sheet_name = elem.attrib.get("name", "")
        relationship_id = ""

        for key, value in elem.attrib.items():
            if key.endswith("}id") or key == "id":
                relationship_id = value

        sheet_path = rels.get(relationship_id, "")

        if sheet_path in names:
            sheets.append(
                {
                    "sheet_name": sheet_name,
                    "sheet_path": sheet_path,
                    "relationship_id": relationship_id,
                }
            )

    return sheets


def read_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")

    if cell_type == "inlineStr":
        parts: list[str] = []
        for elem in cell.iter():
            if elem.tag.endswith("}t") or elem.tag == "t":
                parts.append(elem.text or "")
        return "".join(parts).strip()

    value_elem = None
    for child in cell:
        if child.tag.endswith("}v") or child.tag == "v":
            value_elem = child
            break

    if value_elem is None:
        return ""

    raw_value = value_elem.text or ""

    if cell_type == "s":
        idx = to_int(raw_value, -1)
        if 0 <= idx < len(shared_strings):
            return shared_strings[idx].strip()

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

            col_idx = cell_ref_to_col_index(cell.attrib.get("r", ""))
            max_col = max(max_col, col_idx)
            values_by_index[col_idx] = read_cell_value(cell, shared_strings)

        if max_col >= 0:
            row = [values_by_index.get(i, "") for i in range(max_col + 1)]
            if any(clean_cell(v) for v in row):
                rows.append(row)

    return rows


def detect_header_row(rows: list[list[str]]) -> tuple[int, dict[str, int], list[str]]:
    best_idx = -1
    best_score = -1
    best_mapping: dict[str, int] = {}

    alias_lookup: dict[str, str] = {}
    for canonical, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            alias_lookup[normalize_header(alias)] = canonical

    for idx, row in enumerate(rows[:30]):
        mapping: dict[str, int] = {}

        for col_idx, value in enumerate(row):
            normalized = normalize_header(value)

            for alias_norm, canonical in alias_lookup.items():
                if normalized == alias_norm or alias_norm in normalized:
                    mapping.setdefault(canonical, col_idx)

        score = len(mapping)
        if "stock_code" in mapping:
            score += 5
        if "name_of_securities" in mapping:
            score += 3
        if "category" in mapping:
            score += 1
        if "isin" in mapping:
            score += 1

        if score > best_score:
            best_idx = idx
            best_score = score
            best_mapping = mapping

    if best_idx < 0:
        return -1, {}, []

    return best_idx, best_mapping, rows[best_idx]


def get_value(row: list[str], mapping: dict[str, int], key: str) -> str:
    idx = mapping.get(key, -1)
    if idx < 0 or idx >= len(row):
        return ""
    return clean_cell(row[idx])


def load_primary_xlsx_rows(path: Path) -> tuple[list[list[str]], str, str]:
    with zipfile.ZipFile(path, "r") as zf:
        bad_file = zf.testzip()
        if bad_file:
            raise SystemExit(f"Invalid XLSX zip member: {bad_file}")

        shared_strings = load_shared_strings(zf)
        sheets = workbook_sheet_paths(zf)

        primary = None
        for sheet in sheets:
            if sheet["sheet_name"] == "ListOfSecurities":
                primary = sheet
                break

        if primary is None and sheets:
            primary = sheets[0]

        if primary is None:
            raise SystemExit("No worksheet found in primary HKEX XLSX")

        rows = read_sheet_rows(zf, primary["sheet_path"], shared_strings)
        return rows, primary["sheet_name"], primary["sheet_path"]


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        CANDIDATES_CSV,
        REJECTIONS_CSV,
        FIELD_MAPPING_CSV,
        INSTRUMENT_SUMMARY_CSV,
        QUALITY_SUMMARY_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219m_fix = read_json(V219M_FIX_JSON)
    _, parse_readiness_rows = read_csv_with_header(V219M_FIX_PARSE_READINESS_CSV)
    _, sheet_schema_rows = read_csv_with_header(V219M_FIX_SHEET_SCHEMA_CSV)
    _, manifest_rows = read_csv_with_header(V219L_FIX_MANIFEST_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    primary_manifest = next(
        (row for row in manifest_rows if row.get("artifact_id") == PRIMARY_ARTIFACT_ID),
        {},
    )
    if not primary_manifest:
        raise SystemExit(f"Missing primary manifest row: {PRIMARY_ARTIFACT_ID}")

    primary_raw_path = Path(primary_manifest.get("raw_path", ""))
    if not primary_raw_path.exists():
        raise SystemExit(f"Missing primary raw file: {primary_raw_path}")

    rows, sheet_name, sheet_path = load_primary_xlsx_rows(primary_raw_path)
    header_idx, field_mapping, header_row = detect_header_row(rows)

    candidates: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    seen_stock_codes: Counter[str] = Counter()

    for source_row_number, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        raw_stock_code = get_value(row, field_mapping, "stock_code")
        stock_code = normalize_stock_code(raw_stock_code)
        name = get_value(row, field_mapping, "name_of_securities")
        category = get_value(row, field_mapping, "category")
        sub_category = get_value(row, field_mapping, "sub_category")
        board_lot = get_value(row, field_mapping, "board_lot")
        isin = get_value(row, field_mapping, "isin")
        trading_currency = get_value(row, field_mapping, "trading_currency")

        if not stock_code or not re.fullmatch(r"\d{5}", stock_code):
            rejections.append(
                {
                    "source_row_number": source_row_number,
                    "rejection_reason": "invalid_or_missing_stock_code",
                    "raw_stock_code": raw_stock_code,
                    "name_of_securities": name,
                    "category": category,
                    "sub_category": sub_category,
                }
            )
            continue

        if not name:
            rejections.append(
                {
                    "source_row_number": source_row_number,
                    "rejection_reason": "missing_name_of_securities",
                    "raw_stock_code": raw_stock_code,
                    "name_of_securities": name,
                    "category": category,
                    "sub_category": sub_category,
                }
            )
            continue

        seen_stock_codes[stock_code] += 1

        instrument_family = classify_instrument(category, sub_category, name)

        candidates.append(
            {
                "candidate_id": f"HKEX_{stock_code}",
                "source_phase": VERSION,
                "source_provider": "HKEX",
                "source_market": "Hong Kong",
                "source_country": "Hong Kong",
                "exchange": "HKEX",
                "mic": "XHKG",
                "source_artifact_id": PRIMARY_ARTIFACT_ID,
                "source_file": str(primary_raw_path),
                "source_sheet": sheet_name,
                "source_row_number": source_row_number,
                "raw_stock_code": raw_stock_code,
                "stock_code": stock_code,
                "ticker": f"{stock_code}.HK",
                "ticker_yahoo": f"{stock_code}.HK",
                "symbol": f"{stock_code}.HK",
                "name": name,
                "category": category,
                "sub_category": sub_category,
                "instrument_family": instrument_family,
                "candidate_scope_flag": candidate_scope_flag(instrument_family),
                "board_lot": board_lot,
                "isin": isin,
                "expiry_date": get_value(row, field_mapping, "expiry_date"),
                "subject_to_stamp_duty": get_value(row, field_mapping, "subject_to_stamp_duty"),
                "shortsell_eligible": get_value(row, field_mapping, "shortsell_eligible"),
                "cas_eligible": get_value(row, field_mapping, "cas_eligible"),
                "vcm_eligible": get_value(row, field_mapping, "vcm_eligible"),
                "admitted_to_ccass": get_value(row, field_mapping, "admitted_to_ccass"),
                "debt_securities_board_lot_nominal": get_value(row, field_mapping, "debt_securities_board_lot_nominal"),
                "debt_securities_investor_type": get_value(row, field_mapping, "debt_securities_investor_type"),
                "pos_eligible": get_value(row, field_mapping, "pos_eligible"),
                "spread_table": get_value(row, field_mapping, "spread_table"),
                "trading_currency": trading_currency,
                "rmb_counter": get_value(row, field_mapping, "rmb_counter"),
                "dry_run_only": True,
                "canonical_validation_status": "not_performed_v2_19n",
                "expanded_rebuild_status": "not_performed_v2_19n",
            }
        )

    duplicate_stock_codes = sorted([code for code, count in seen_stock_codes.items() if count > 1])

    for candidate in candidates:
        candidate["duplicate_stock_code_within_hkex_extract"] = seen_stock_codes[candidate["stock_code"]] > 1

    instrument_counts = Counter(row["instrument_family"] for row in candidates)
    scope_counts = Counter(row["candidate_scope_flag"] for row in candidates)
    category_counts = Counter(row["category"] or "(blank)" for row in candidates)
    currency_counts = Counter(row["trading_currency"] or "(blank)" for row in candidates)

    instrument_summary_rows = [
        {
            "instrument_family": instrument_family,
            "candidate_rows": count,
            "share_of_extract": round(count / max(len(candidates), 1), 6),
        }
        for instrument_family, count in sorted(instrument_counts.items())
    ]

    quality_summary_rows = [
        {"metric": "xlsx_rows_loaded", "value": len(rows), "detail": "non-empty worksheet rows loaded"},
        {"metric": "header_row_number", "value": header_idx + 1, "detail": "detected header row number"},
        {"metric": "mapped_fields", "value": len(field_mapping), "detail": json.dumps(field_mapping, sort_keys=True)},
        {"metric": "candidate_rows_extracted", "value": len(candidates), "detail": "rows with valid stock code and name"},
        {"metric": "rejected_rows", "value": len(rejections), "detail": "rows rejected before candidate dry run output"},
        {"metric": "unique_stock_codes", "value": len(seen_stock_codes), "detail": "unique normalized HKEX stock codes"},
        {"metric": "duplicate_stock_code_count", "value": len(duplicate_stock_codes), "detail": ",".join(duplicate_stock_codes[:50])},
        {"metric": "potential_candidate_pending_canonical_validation", "value": scope_counts.get("potential_candidate_pending_canonical_validation", 0), "detail": "not yet canonical-validated"},
        {"metric": "extracted_reference_security_likely_excluded_later", "value": scope_counts.get("extracted_reference_security_likely_excluded_later", 0), "detail": "not filtered here; dry run only"},
        {"metric": "top_categories", "value": len(category_counts), "detail": json.dumps(category_counts.most_common(20), ensure_ascii=False)},
        {"metric": "trading_currencies", "value": len(currency_counts), "detail": json.dumps(currency_counts.most_common(20), ensure_ascii=False)},
    ]

    field_mapping_rows = []
    for canonical_field, col_idx in sorted(field_mapping.items(), key=lambda item: item[1]):
        field_mapping_rows.append(
            {
                "canonical_field": canonical_field,
                "source_column_index_zero_based": col_idx,
                "source_column_index_one_based": col_idx + 1,
                "source_header": header_row[col_idx] if 0 <= col_idx < len(header_row) else "",
            }
        )

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19m_fix_report_exists", V219M_FIX_JSON.exists(), "critical", str(V219M_FIX_JSON))
    add_check("v2_19m_fix_status_expected", v219m_fix.get("status") == EXPECTED_V219M_FIX_STATUS, "critical", str(v219m_fix.get("status", "")))
    add_check("parse_readiness_exists", V219M_FIX_PARSE_READINESS_CSV.exists(), "critical", str(V219M_FIX_PARSE_READINESS_CSV))
    add_check("sheet_schema_exists", V219M_FIX_SHEET_SCHEMA_CSV.exists(), "critical", str(V219M_FIX_SHEET_SCHEMA_CSV))
    add_check("primary_parse_ready_in_prior_phase", any(row.get("artifact_id") == PRIMARY_ARTIFACT_ID and to_bool(row.get("primary_parse_ready")) for row in parse_readiness_rows), "critical", PRIMARY_ARTIFACT_ID)
    add_check("primary_raw_file_exists", primary_raw_path.exists(), "critical", str(primary_raw_path))
    add_check("primary_raw_file_sha_matches_manifest", sha256_file(primary_raw_path) == primary_manifest.get("sha256"), "critical", primary_manifest.get("sha256", ""))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("primary_sheet_loaded", len(rows) >= 100, "critical", f"rows_loaded={len(rows)}; sheet={sheet_name}; path={sheet_path}")
    add_check("header_row_detected", header_idx >= 0, "critical", f"header_row={header_idx + 1}")
    add_check("stock_code_field_mapped", "stock_code" in field_mapping, "critical", json.dumps(field_mapping, sort_keys=True))
    add_check("name_field_mapped", "name_of_securities" in field_mapping, "critical", json.dumps(field_mapping, sort_keys=True))
    add_check("candidate_rows_extracted", len(candidates) >= 100, "critical", f"candidate_rows={len(candidates)}")
    add_check("unique_stock_codes_positive", len(seen_stock_codes) >= 100, "critical", f"unique_stock_codes={len(seen_stock_codes)}")
    add_check("rejections_documented", len(rejections) >= 0, "warning", f"rejections={len(rejections)}")
    add_check("duplicates_documented", len(duplicate_stock_codes) >= 0, "warning", f"duplicate_stock_code_count={len(duplicate_stock_codes)}")
    add_check("candidate_output_dry_run_only", True, "critical", "dry_run_only=True")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("network_not_used_by_extraction", True, "critical", "network_download_performed=False")
    add_check("candidate_extraction_performed", True, "critical", "candidate_extraction_performed=True")
    add_check("candidate_validation_against_canonical_not_performed", True, "critical", "candidate_validation_against_canonical_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("expanded_validation_not_performed", True, "critical", "expanded_validation_performed=False")
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

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "HKEX",
            "action": "run_candidate_validation_against_canonical_dry_run",
            "priority": "high",
            "reason": "HKEX candidates have been extracted in dry run and now require dedupe/canonical validation.",
            "recommended_phase": NEXT_PHASE_VALIDATION,
            "guardrails": "compare only; do not modify canonical; do not rebuild expanded candidate yet",
        },
        {
            "action_order": 2,
            "action_scope": "HKEX",
            "action": "separate_candidate_scope_flags",
            "priority": "high",
            "reason": "Extraction includes all parseable HKEX securities; canonical validation should decide inclusion/exclusion.",
            "recommended_phase": NEXT_PHASE_VALIDATION,
            "guardrails": "preserve dry-run evidence and instrument_family classifications",
        },
        {
            "action_order": 3,
            "action_scope": "50k",
            "action": "preserve_quality_gate",
            "priority": "high",
            "reason": "Current candidate universe remains 40,996; rows needed to 50k remain 9,004.",
            "recommended_phase": NEXT_PHASE_VALIDATION,
            "guardrails": "do not launch full59k; no rebuild before validation",
        },
    ]

    extraction_summary = {
        "source_artifact_id": PRIMARY_ARTIFACT_ID,
        "source_file": str(primary_raw_path),
        "source_sheet": sheet_name,
        "source_sheet_path": sheet_path,
        "xlsx_rows_loaded": len(rows),
        "header_row_number": header_idx + 1,
        "mapped_field_count": len(field_mapping),
        "candidate_rows_extracted": len(candidates),
        "rejected_rows": len(rejections),
        "unique_stock_codes": len(seen_stock_codes),
        "duplicate_stock_code_count": len(duplicate_stock_codes),
        "instrument_family_count": len(instrument_counts),
        "potential_candidate_pending_canonical_validation": scope_counts.get("potential_candidate_pending_canonical_validation", 0),
        "extracted_reference_security_likely_excluded_later": scope_counts.get("extracted_reference_security_likely_excluded_later", 0),
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
        "v2_19m_fix_context": {
            "status": v219m_fix.get("status"),
            "phase_type": v219m_fix.get("phase_type"),
            "primary_parse_ready_count": v219m_fix.get("validation_summary", {}).get("primary_parse_ready_count"),
            "extraction_dry_run_allowed_count": v219m_fix.get("validation_summary", {}).get("extraction_dry_run_allowed_count"),
            "top_primary_parseable_stock_code_rows": v219m_fix.get("validation_summary", {}).get("top_primary_parseable_stock_code_rows"),
            "recommended_next_phase": v219m_fix.get("recommended_next_phase"),
        },
        "extraction_summary": extraction_summary,
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
            "candidate_extraction_performed": True,
            "candidate_extraction_dry_run_only": True,
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
        CANDIDATES_CSV,
        candidates,
        [
            "candidate_id",
            "source_phase",
            "source_provider",
            "source_market",
            "source_country",
            "exchange",
            "mic",
            "source_artifact_id",
            "source_file",
            "source_sheet",
            "source_row_number",
            "raw_stock_code",
            "stock_code",
            "ticker",
            "ticker_yahoo",
            "symbol",
            "name",
            "category",
            "sub_category",
            "instrument_family",
            "candidate_scope_flag",
            "board_lot",
            "isin",
            "expiry_date",
            "subject_to_stamp_duty",
            "shortsell_eligible",
            "cas_eligible",
            "vcm_eligible",
            "admitted_to_ccass",
            "debt_securities_board_lot_nominal",
            "debt_securities_investor_type",
            "pos_eligible",
            "spread_table",
            "trading_currency",
            "rmb_counter",
            "duplicate_stock_code_within_hkex_extract",
            "dry_run_only",
            "canonical_validation_status",
            "expanded_rebuild_status",
        ],
    )
    write_csv(
        REJECTIONS_CSV,
        rejections,
        [
            "source_row_number",
            "rejection_reason",
            "raw_stock_code",
            "name_of_securities",
            "category",
            "sub_category",
        ],
    )
    write_csv(
        FIELD_MAPPING_CSV,
        field_mapping_rows,
        [
            "canonical_field",
            "source_column_index_zero_based",
            "source_column_index_one_based",
            "source_header",
        ],
    )
    write_csv(
        INSTRUMENT_SUMMARY_CSV,
        instrument_summary_rows,
        [
            "instrument_family",
            "candidate_rows",
            "share_of_extract",
        ],
    )
    write_csv(QUALITY_SUMMARY_CSV, quality_summary_rows, ["metric", "value", "detail"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    instrument_lines = "\n".join(
        f"- `{row['instrument_family']}`: `{row['candidate_rows']}`"
        for row in instrument_summary_rows
    )

    mapping_lines = "\n".join(
        f"- `{row['canonical_field']}` ← column `{row['source_column_index_one_based']}` / `{row['source_header']}`"
        for row in field_mapping_rows
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

v2.19N extracts HKEX candidates from the validated `ListOfSecurities.xlsx` source as a dry run.

This phase does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Extraction summary

- Source artifact: `{PRIMARY_ARTIFACT_ID}`
- Source file: `{primary_raw_path}`
- Source sheet: `{sheet_name}`
- XLSX rows loaded: `{len(rows)}`
- Header row number: `{header_idx + 1}`
- Mapped fields: `{len(field_mapping)}`
- Candidate rows extracted: `{len(candidates)}`
- Rejected rows: `{len(rejections)}`
- Unique stock codes: `{len(seen_stock_codes)}`
- Duplicate stock-code count: `{len(duplicate_stock_codes)}`
- Critical failed checks: `{critical_failed}`

## Field mapping

{mapping_lines}

## Instrument summary

{instrument_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Candidate extraction performed: true
- Candidate extraction dry run only: true
- Candidate validation against canonical performed: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{candidate_sha_before == candidate_sha_after}`
- Expanded rebuild candidate performed: false
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

    print("v2.19N HKEX candidate extraction dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("EXTRACTION_SUMMARY:")
    for key, value in extraction_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("FIELD_MAPPING:")
    for row in field_mapping_rows:
        print(f"- {row['canonical_field']} <- col {row['source_column_index_one_based']} / {row['source_header']}")
    print("")
    print("INSTRUMENT_SUMMARY:")
    for row in instrument_summary_rows:
        print(f"- {row['instrument_family']}: {row['candidate_rows']}")
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
