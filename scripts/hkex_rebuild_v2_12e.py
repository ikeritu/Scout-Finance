from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET


VERSION = "v2.12E"
PHASE = "Rebuild Expanded Source With HKEX"
PHASE_TYPE = "rebuild-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_XLSX = OUTPUT_DIR / "raw" / "hkex_v2_12c" / "ListOfSecurities.xlsx"
BASELINE_EXPANDED = OUTPUT_DIR / "expanded_universe_v2_11e.csv"
VALIDATION_DECISION_CSV = OUTPUT_DIR / "hkex_validation_decision_v2_12d.csv"

EXPANDED_OUT = OUTPUT_DIR / "expanded_universe_v2_12e.csv"
EXCLUSIONS_OUT = OUTPUT_DIR / "expanded_universe_exclusions_v2_12e.csv"
NORMALIZED_CANDIDATES_OUT = OUTPUT_DIR / "hkex_normalized_candidates_v2_12e.csv"
REBUILD_JSON = OUTPUT_DIR / "hkex_rebuild_report_v2_12e.json"
REBUILD_MD = OUTPUT_DIR / "hkex_rebuild_report_v2_12e.md"

FULL_SOURCE_THRESHOLD = 50000
FIRST_EXPANSION_THRESHOLD = 15000

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

HKEX_SOURCE_URL = "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx"

ACCEPTED_HKEX_EQUITY_SUBCATEGORIES = {
    "Equity Securities (Main Board)",
    "Equity Securities (GEM)",
    "Investment Companies",
    "Trading Only Securities",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        EXPANDED_OUT,
        EXCLUSIONS_OUT,
        NORMALIZED_CANDIDATES_OUT,
        REBUILD_JSON,
        REBUILD_MD,
    ]
    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.12E outputs:\n"
            + "\n".join(existing)
        )


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


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_validation_gate(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing validation decision: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise SystemExit(f"Validation decision is empty: {path}")

    decision = rows[0]
    status = decision.get("validation_decision", "")
    allowed = str(decision.get("rebuild_allowed_by_validation", "")).strip().lower() == "true"

    expected = "HKEX_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW_FULL_SOURCE_STILL_BLOCKED"
    if status != expected or not allowed:
        raise SystemExit(
            "VALIDATION_GATE_BLOCKED: v2.12E requires v2.12D rebuild_allowed_by_validation=True "
            f"and validation_decision={expected}. Got status={status!r}, allowed={allowed!r}"
        )

    return decision


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


def parse_hkex_candidates(path: Path) -> tuple[dict, list[dict]]:
    if not path.exists():
        raise SystemExit(f"Missing HKEX raw XLSX: {path}")

    selected_sheet = {}
    candidates: list[dict] = []

    with zipfile.ZipFile(path, "r") as zf:
        shared_strings = load_shared_strings(zf)
        sheets = workbook_sheet_paths(zf)

        best = None

        for sheet in sheets:
            rows = read_sheet_rows(zf, sheet["xml_path"], shared_strings)
            header = detect_header(rows)
            header_idx = int(header["header_row_index_zero_based"])
            cols = header["canonical_columns"]

            sheet_candidates: list[dict] = []

            if header_idx >= 0 and "stock_code" in cols and "name_of_securities" in cols:
                for row_number, row in enumerate(rows[header_idx + 1 :], start=header_idx + 2):
                    stock_code = row_get(row, cols.get("stock_code"))
                    name = row_get(row, cols.get("name_of_securities"))
                    category = row_get(row, cols.get("category"))
                    subcategory = row_get(row, cols.get("subcategory"))
                    isin = row_get(row, cols.get("isin"))
                    board_lot = row_get(row, cols.get("board_lot"))
                    currency = row_get(row, cols.get("currency"))

                    if not stock_code and not name:
                        continue

                    sheet_candidates.append(
                        {
                            "sheet_name": sheet["sheet_name"],
                            "row_number": row_number,
                            "stock_code_raw_text": stock_code,
                            "ticker": stock_code,
                            "company_name": name,
                            "exchange": "HKEX",
                            "isin": isin,
                            "currency": currency,
                            "board_lot": board_lot,
                            "category": category,
                            "subcategory": subcategory,
                            "source_provider": "hkex_securities_list",
                            "source_version": VERSION,
                            "source_file": str(path),
                            "source_url": HKEX_SOURCE_URL,
                        }
                    )

            profile = {
                "sheet_name": sheet["sheet_name"],
                "sheet_id": sheet["sheet_id"],
                "xml_path": sheet["xml_path"],
                "total_rows_read": len(rows),
                "header_row_index_zero_based": header_idx,
                "header_score": header["score"],
                "detected_columns": "|".join(sorted(cols.keys())),
                "candidate_rows": len(sheet_candidates),
            }

            candidate = {
                "profile": profile,
                "rows": sheet_candidates,
            }

            if best is None:
                best = candidate
            else:
                best_key = (
                    int(best["profile"]["candidate_rows"]),
                    int(best["profile"]["header_score"]),
                    int(best["profile"]["total_rows_read"]),
                )
                new_key = (
                    int(candidate["profile"]["candidate_rows"]),
                    int(candidate["profile"]["header_score"]),
                    int(candidate["profile"]["total_rows_read"]),
                )
                if new_key > best_key:
                    best = candidate

        if best:
            selected_sheet = best["profile"]
            candidates = best["rows"]

    return selected_sheet, candidates


def load_baseline_rows(path: Path) -> tuple[list[str], list[dict], set[tuple[str, str]], set[str], set[str]]:
    if not path.exists():
        raise SystemExit(f"Missing baseline expanded universe: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    field_lookup = {field.lower(): field for field in fieldnames}

    ticker_field = field_lookup.get("ticker") or field_lookup.get("symbol")
    exchange_field = field_lookup.get("exchange")
    isin_field = field_lookup.get("isin")

    if not ticker_field:
        raise SystemExit("BASELINE_SCHEMA_ERROR: missing ticker/symbol column")
    if not exchange_field:
        raise SystemExit("BASELINE_SCHEMA_ERROR: missing exchange column")

    exchange_ticker_keys: set[tuple[str, str]] = set()
    tickers: set[str] = set()
    isins: set[str] = set()

    for row in rows:
        ticker = normalize_text(row.get(ticker_field, "")).upper()
        exchange = normalize_text(row.get(exchange_field, "")).upper()
        isin = normalize_text(row.get(isin_field, "")).upper() if isin_field else ""

        if ticker:
            tickers.add(ticker)
            if exchange:
                exchange_ticker_keys.add((exchange, ticker))

        if isin:
            isins.add(isin)

    return fieldnames, rows, exchange_ticker_keys, tickers, isins


def accepted_by_hkex_allowlist(row: dict) -> tuple[bool, str]:
    category = normalize_text(row.get("category"))
    subcategory = normalize_text(row.get("subcategory"))
    name = normalize_text(row.get("company_name"))
    stock_code = normalize_text(row.get("ticker"))

    if not stock_code:
        return False, "MISSING_STOCK_CODE"
    if not name:
        return False, "MISSING_COMPANY_NAME"

    if category != "Equity":
        if not category:
            return False, "MISSING_CATEGORY_REVIEW_REQUIRED"
        return False, "NON_EQUITY_CATEGORY_EXCLUDED"

    if subcategory not in ACCEPTED_HKEX_EQUITY_SUBCATEGORIES:
        return False, "EQUITY_SUBCATEGORY_NOT_IN_ALLOWLIST"

    return True, "ACCEPTED_HKEX_EQUITY_ALLOWLIST"


def ensure_output_fieldnames(baseline_fieldnames: list[str]) -> list[str]:
    required = [
        "ticker",
        "company_name",
        "exchange",
        "isin",
        "currency",
        "mic",
        "country",
        "source_provider",
        "source_version",
        "source_file",
        "source_url",
        "hkex_category",
        "hkex_subcategory",
        "hkex_board_lot",
    ]

    out = list(baseline_fieldnames)
    lower_existing = {field.lower(): field for field in out}

    for field in required:
        if field.lower() not in lower_existing:
            out.append(field)

    return out


def make_expanded_row(output_fields: list[str], hkex_row: dict) -> dict:
    out = {field: "" for field in output_fields}
    lower_to_actual = {field.lower(): field for field in output_fields}

    def set_if_present(field: str, value: object) -> None:
        actual = lower_to_actual.get(field.lower())
        if actual:
            out[actual] = normalize_text(value)

    set_if_present("ticker", hkex_row.get("ticker"))
    set_if_present("symbol", hkex_row.get("ticker"))
    set_if_present("company_name", hkex_row.get("company_name"))
    set_if_present("name", hkex_row.get("company_name"))
    set_if_present("exchange", "HKEX")
    set_if_present("isin", hkex_row.get("isin"))
    set_if_present("currency", hkex_row.get("currency"))
    set_if_present("mic", "XHKG")
    set_if_present("country", "Hong Kong")
    set_if_present("source_provider", "hkex_securities_list")
    set_if_present("provider", "hkex_securities_list")
    set_if_present("source", "hkex_securities_list")
    set_if_present("source_version", VERSION)
    set_if_present("source_file", str(RAW_XLSX))
    set_if_present("source_url", HKEX_SOURCE_URL)
    set_if_present("hkex_category", hkex_row.get("category"))
    set_if_present("hkex_subcategory", hkex_row.get("subcategory"))
    set_if_present("hkex_board_lot", hkex_row.get("board_lot"))

    return out


def duplicate_key_count(rows: list[dict], ticker_field: str, exchange_field: str) -> int:
    counter = Counter()
    for row in rows:
        ticker = normalize_text(row.get(ticker_field, "")).upper()
        exchange = normalize_text(row.get(exchange_field, "")).upper()
        if ticker and exchange:
            counter[(exchange, ticker)] += 1
    return sum(count - 1 for count in counter.values() if count > 1)


def main() -> None:
    no_overwrite_guard()

    validation_decision = read_validation_gate(VALIDATION_DECISION_CSV)

    baseline_fieldnames, baseline_rows, baseline_exchange_keys, baseline_tickers, baseline_isins = load_baseline_rows(
        BASELINE_EXPANDED
    )
    selected_sheet, hkex_candidates = parse_hkex_candidates(RAW_XLSX)

    output_fields = ensure_output_fieldnames(baseline_fieldnames)
    lower_fields = {field.lower(): field for field in output_fields}
    ticker_field = lower_fields.get("ticker") or lower_fields.get("symbol")
    exchange_field = lower_fields.get("exchange")

    normalized_candidates: list[dict] = []
    exclusions: list[dict] = []
    accepted_rows_for_expanded: list[dict] = []

    seen_hkex_codes: set[str] = set()

    exclusion_counter = Counter()
    accepted_subcategory_counter = Counter()
    rejected_category_counter = Counter()

    for candidate in hkex_candidates:
        stock_code = normalize_text(candidate.get("ticker"))
        stock_code_upper = stock_code.upper()
        isin = normalize_text(candidate.get("isin")).upper()
        category = normalize_text(candidate.get("category"))
        subcategory = normalize_text(candidate.get("subcategory"))

        allowed, reason = accepted_by_hkex_allowlist(candidate)

        if allowed:
            if ("HKEX", stock_code_upper) in baseline_exchange_keys:
                allowed = False
                reason = "BASELINE_EXCHANGE_TICKER_ALREADY_PRESENT"
            elif isin and isin in baseline_isins:
                allowed = False
                reason = "BASELINE_ISIN_ALREADY_PRESENT"
            elif stock_code_upper in seen_hkex_codes:
                allowed = False
                reason = "DUPLICATE_HKEX_STOCK_CODE"
            else:
                seen_hkex_codes.add(stock_code_upper)

        status = "ACCEPTED_FOR_REBUILD_CANDIDATE" if allowed else "EXCLUDED"

        normalized = {
            "version": VERSION,
            "phase_type": PHASE_TYPE,
            "sheet_name": candidate.get("sheet_name", ""),
            "row_number": candidate.get("row_number", ""),
            "stock_code_raw_text": stock_code,
            "ticker": stock_code,
            "company_name": candidate.get("company_name", ""),
            "exchange": "HKEX",
            "isin": candidate.get("isin", ""),
            "currency": candidate.get("currency", ""),
            "board_lot": candidate.get("board_lot", ""),
            "category": category,
            "subcategory": subcategory,
            "source_provider": "hkex_securities_list",
            "rebuild_candidate_status": status,
            "decision_reason": reason,
        }
        normalized_candidates.append(normalized)

        if allowed:
            accepted_subcategory_counter[(category, subcategory)] += 1
            accepted_rows_for_expanded.append(make_expanded_row(output_fields, candidate))
        else:
            exclusion_counter[reason] += 1
            rejected_category_counter[(category, subcategory, reason)] += 1
            exclusions.append(normalized)

    expanded_rows = []
    for row in baseline_rows:
        expanded_rows.append({field: row.get(field, "") for field in output_fields})
    expanded_rows.extend(accepted_rows_for_expanded)

    duplicate_exchange_ticker_keys = duplicate_key_count(expanded_rows, ticker_field, exchange_field)

    baseline_row_count = len(baseline_rows)
    hkex_rows_added = len(accepted_rows_for_expanded)
    new_expanded_rows = len(expanded_rows)

    first_expansion_unlocked = new_expanded_rows >= FIRST_EXPANSION_THRESHOLD
    full_source_unlocked = new_expanded_rows >= FULL_SOURCE_THRESHOLD
    rows_needed_full_source = max(FULL_SOURCE_THRESHOLD - new_expanded_rows, 0)

    hard_guards = {
        "phase_type": PHASE_TYPE,
        "network_download_performed": False,
        "raw_files_modified": False,
        "workbook_parsed_from_existing_raw": True,
        "normalization_performed": True,
        "net_new_filtering_performed": True,
        "expanded_universe_rebuilt": True,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
    }

    status = "HKEX_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED"
    if full_source_unlocked:
        status = "HKEX_REBUILD_COMPLETED_FULL_SOURCE_UNLOCKED_REQUIRES_GATE_BEFORE_FULL_59K"

    report = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "validation_gate": {
            "decision_file": str(VALIDATION_DECISION_CSV),
            "validation_decision": validation_decision.get("validation_decision", ""),
            "rebuild_allowed_by_validation": validation_decision.get("rebuild_allowed_by_validation", ""),
        },
        "selected_sheet": selected_sheet,
        "accepted_hkex_equity_subcategories": sorted(ACCEPTED_HKEX_EQUITY_SUBCATEGORIES),
        "counts": {
            "baseline_rows": baseline_row_count,
            "hkex_candidate_rows_reviewed": len(hkex_candidates),
            "hkex_rows_added": hkex_rows_added,
            "exclusions": len(exclusions),
            "new_expanded_rows": new_expanded_rows,
            "duplicate_exchange_ticker_keys": duplicate_exchange_ticker_keys,
            "first_expansion_threshold": FIRST_EXPANSION_THRESHOLD,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_full_source": rows_needed_full_source,
        },
        "accepted_subcategory_breakdown": [
            {
                "category": category,
                "subcategory": subcategory,
                "rows": count,
            }
            for (category, subcategory), count in accepted_subcategory_counter.most_common()
        ],
        "exclusion_reason_breakdown": [
            {
                "reason": reason,
                "rows": count,
            }
            for reason, count in exclusion_counter.most_common()
        ],
        "hard_guards": hard_guards,
        "outputs": {
            "expanded_universe": str(EXPANDED_OUT),
            "exclusions": str(EXCLUSIONS_OUT),
            "normalized_candidates": str(NORMALIZED_CANDIDATES_OUT),
            "report_json": str(REBUILD_JSON),
            "report_md": str(REBUILD_MD),
        },
        "important_scope_note": (
            "v2.12E rebuilds expanded source with a conservative HKEX equity allowlist. "
            "It does not score, call OpenAI, call broker APIs or launch full 59k."
        ),
    }

    write_csv(EXPANDED_OUT, expanded_rows, output_fields)

    normalized_fields = [
        "version",
        "phase_type",
        "sheet_name",
        "row_number",
        "stock_code_raw_text",
        "ticker",
        "company_name",
        "exchange",
        "isin",
        "currency",
        "board_lot",
        "category",
        "subcategory",
        "source_provider",
        "rebuild_candidate_status",
        "decision_reason",
    ]

    write_csv(NORMALIZED_CANDIDATES_OUT, normalized_candidates, normalized_fields)
    write_csv(EXCLUSIONS_OUT, exclusions, normalized_fields)
    write_json(REBUILD_JSON, report)

    accepted_lines = "\n".join(
        f"- {item['category']} / {item['subcategory']}: {item['rows']}"
        for item in report["accepted_subcategory_breakdown"]
    )

    exclusion_lines = "\n".join(
        f"- {item['reason']}: {item['rows']}"
        for item in report["exclusion_reason_breakdown"]
    )

    guard_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in hard_guards.items()
    )

    md = f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **rebuild-only**

Generated at UTC: `{report["generated_at_utc"]}`

## Validation gate

- Decision file: `{VALIDATION_DECISION_CSV}`
- Validation decision: `{validation_decision.get("validation_decision", "")}`
- Rebuild allowed by validation: `{validation_decision.get("rebuild_allowed_by_validation", "")}`

## Conservative HKEX allowlist

Accepted only:

{chr(10).join(f"- Equity / {item}" for item in sorted(ACCEPTED_HKEX_EQUITY_SUBCATEGORIES))}

Excluded all non-equity, derivative, debt, ETF, REIT, warrant, CBBC and review-required rows.

## Counts

- Baseline rows: {baseline_row_count}
- HKEX candidate rows reviewed: {len(hkex_candidates)}
- HKEX rows added: {hkex_rows_added}
- Exclusions: {len(exclusions)}
- New expanded rows: {new_expanded_rows}
- Duplicate exchange+ticker keys: {duplicate_exchange_ticker_keys}
- First expansion threshold: {FIRST_EXPANSION_THRESHOLD}
- First expansion unlocked: {first_expansion_unlocked}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Full source unlocked: {full_source_unlocked}
- Rows needed full source: {rows_needed_full_source}

## Accepted subcategory breakdown

{accepted_lines}

## Exclusion reason breakdown

{exclusion_lines}

## Hard guards

{guard_lines}

## Outputs

- `{EXPANDED_OUT}`
- `{EXCLUSIONS_OUT}`
- `{NORMALIZED_CANDIDATES_OUT}`
- `{REBUILD_JSON}`
- `{REBUILD_MD}`

## Scope note

v2.12E does not score, call OpenAI, call broker APIs or launch full 59k.

Full 59k remains blocked unless the expanded source reaches the source-complete gate and receives explicit approval.
"""

    REBUILD_MD.write_text(md, encoding="utf-8")

    print("v2.12E HKEX rebuild-only completed.")
    print(f"- expanded universe: {EXPANDED_OUT}")
    print(f"- exclusions: {EXCLUSIONS_OUT}")
    print(f"- normalized candidates: {NORMALIZED_CANDIDATES_OUT}")
    print(f"- report json: {REBUILD_JSON}")
    print(f"- report md: {REBUILD_MD}")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("COUNTS:")
    for key, value in report["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("ACCEPTED_SUBCATEGORIES:")
    for item in report["accepted_subcategory_breakdown"]:
        print(f"- {item['category']} / {item['subcategory']}: {item['rows']}")
    print("")
    print("EXCLUSION_REASONS:")
    for item in report["exclusion_reason_breakdown"]:
        print(f"- {item['reason']}: {item['rows']}")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
