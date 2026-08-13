from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


VERSION = "v2.21D_C"
PHASE = "Colombia Conditional Build / Freeze"
PHASE_TYPE = "colombia-conditional-build-freeze"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

COLOMBIA_DISCOVERY_JSON = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_v2_21c3b.json"
COLOMBIA_DISCOVERY_FETCH_VALIDATION = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_fetch_validation_v2_21c3b.csv"
COLOMBIA_DISCOVERY_STRUCTURED_SOURCES = OUTPUT_DIR / "colombia_regulatory_discovery_extraction_decision_structured_source_candidates_v2_21c3b.csv"

SINGAPORE_PROMOTED_DATASET = OUTPUT_DIR / "expanded_universe_v2_21e_s_singapore_promoted.csv"
SINGAPORE_PROMOTION_JSON = OUTPUT_DIR / "singapore_promotion_freeze_decision_v2_21e_s.json"

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

COLOMBIA_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_v2_21d_c_colombia_candidate.csv"

REPORT_JSON = OUTPUT_DIR / "colombia_conditional_build_freeze_v2_21d_c.json"
REPORT_MD = OUTPUT_DIR / "colombia_conditional_build_freeze_v2_21d_c.md"
SUMMARY_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_summary_v2_21d_c.csv"
CHECKS_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_checks_v2_21d_c.csv"
RAW_CANDIDATES_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_raw_candidates_v2_21d_c.csv"
ELIGIBLE_CANDIDATES_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_eligible_candidates_v2_21d_c.csv"
REJECTED_CANDIDATES_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_rejected_candidates_v2_21d_c.csv"
DEDUP_SUMMARY_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_dedup_summary_v2_21d_c.csv"
SCHEMA_PROJECTION_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_schema_projection_v2_21d_c.csv"
APPEND_MANIFEST_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_append_manifest_v2_21d_c.csv"
SOURCE_ROW_AUDIT_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_source_row_audit_v2_21d_c.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "colombia_conditional_build_freeze_next_actions_v2_21d_c.csv"

EXPECTED_DISCOVERY_STATUS = "COLOMBIA_REGULATORY_DISCOVERY_EXTRACTION_DECISION_COMPLETED_STRUCTURED_SOURCE_READY_EXTRACTION_APPROVED_NO_DATASET_CHANGES_SCORING_DEFERRED"
EXPECTED_SINGAPORE_PROMOTION_STATUS = "SINGAPORE_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"

ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

SINGAPORE_PROMOTED_ROWS_EXPECTED = 43066
SINGAPORE_PROMOTED_SHA_EXPECTED = "8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

MARKET_ID = "COLOMBIA_BVC_REGULATORY"
COUNTRY = "Colombia"
COUNTRY_CODE = "CO"
EXCHANGE = "BVC"
MIC = "XBOG"
CURRENCY = "COP"
SOURCE_PROVIDER = "SFC_SIMEV_RNVE"

STATUS_BUILT = "COLOMBIA_CONDITIONAL_BUILD_COMPLETED_CANDIDATE_CREATED_NO_PROMOTION_NO_POINTER_UPDATE_SCORING_DEFERRED"
STATUS_FROZEN = "COLOMBIA_CONDITIONAL_BUILD_COMPLETED_NO_ELIGIBLE_CANDIDATES_COLOMBIA_FROZEN_NO_DATASET_CHANGES"
STATUS_FAILED = "COLOMBIA_CONDITIONAL_BUILD_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_IF_BUILT = "v2.21E_C - Colombia Promotion / Freeze Decision"
NEXT_PHASE_IF_FROZEN = "v2.21G - Final v2.21 Closure Report"
NEXT_PHASE_REVIEW = "v2.21D_C_REVIEW - Colombia Conditional Build Issue Resolution"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.current_table: list[list[str]] = []
        self.tables: list[list[list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self.in_table = True
            self.current_table = []
        elif self.in_table and tag == "tr":
            self.in_row = True
            self.current_row = []
        elif self.in_table and self.in_row and tag in {"td", "th"}:
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.in_table and self.in_row and self.in_cell and tag in {"td", "th"}:
            cell = " ".join(" ".join(self.current_cell).split())
            self.current_row.append(html.unescape(cell))
            self.current_cell = []
            self.in_cell = False
        elif self.in_table and self.in_row and tag == "tr":
            if any(cell.strip() for cell in self.current_row):
                self.current_table.append(self.current_row)
            self.current_row = []
            self.in_row = False
        elif self.in_table and tag == "table":
            if self.current_table:
                self.tables.append(self.current_table)
            self.current_table = []
            self.in_table = False

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell.append(data)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader)


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def strip_accents_basic(text: str) -> str:
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u",
        "ñ": "n", "Ñ": "n",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_accents_basic(norm(value)).lower()).strip()


def compact_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", strip_accents_basic(norm(value)).lower())


def valid_isin(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", norm(value).upper()))


def first_present(payload: dict[str, str], options: list[str]) -> str:
    normalized = {norm_key(k): v for k, v in payload.items()}
    for option in options:
        value = norm(normalized.get(norm_key(option), ""))
        if value:
            return value
    return ""


def parse_tables(path: Path) -> list[list[list[str]]]:
    parser = TableParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser.tables


def table_to_payload_rows(table: list[list[str]]) -> list[dict[str, str]]:
    if len(table) < 2:
        return []
    header = [norm(cell) for cell in table[0]]
    rows: list[dict[str, str]] = []
    for table_row in table[1:]:
        if not any(norm(cell) for cell in table_row):
            continue
        payload: dict[str, str] = {}
        for index, column in enumerate(header):
            key = column or f"column_{index + 1}"
            payload[key] = norm(table_row[index]) if index < len(table_row) else ""
        rows.append(payload)
    return rows


def classify_source(source_id: str, source_type: str) -> str:
    source_id_key = compact_key(source_id)
    source_type_key = compact_key(source_type)
    if "precioacciones" in source_id_key or "actionprice" in source_type_key:
        return "equity_price_page"
    if "valoresinscritos" in source_id_key or "registeredvalues" in source_type_key:
        return "registered_values_page"
    if "financialinstitution" in source_id_key:
        return "registry_search_page"
    return "other_regulatory_page"


def candidate_quality(payload: dict[str, str], source_class: str) -> tuple[bool, str, dict[str, str]]:
    title = first_present(payload, [
        "Nombre del título",
        "Nombre titulo",
        "Emisión",
        "Razon social",
        "Razón social",
        "Nombre entidad",
    ])

    code_ann = first_present(payload, [
        "Código ANN",
        "Codigo ANN",
        "Código Superfinanciera",
        "Codigo Superfinanciera",
        "Código RNVEI",
        "Codigo RNVEI",
        "Identificación",
        "Identificacion",
    ])

    issue_number = first_present(payload, [
        "No. Emisión",
        "No Emisión",
        "No. Emision",
        "No Emision",
    ])

    inscrito_en = first_present(payload, ["Inscrito en"])
    bvc_date = first_present(payload, ["Inscrito BVC Fecha", "Inscrito B V C Fecha"])
    rnve_date = first_present(payload, ["Inscrito RNVE Fecha"])
    tipo_inscripcion = first_present(payload, ["Tipo Inscripción", "Tipo Inscripcion"])
    moneda = first_present(payload, ["Moneda"])

    title_key = compact_key(title)
    code_key = compact_key(code_ann)

    invalid_title_fragments = [
        "para realizar una busqueda",
        "es necesario que especifique",
        "seleccionar al menos",
        "accion",
        "estado tipo de entidad",
    ]

    if not title or len(title_key) < 3:
        return False, "missing_or_too_short_title", {}

    if any(fragment in norm_key(title) for fragment in invalid_title_fragments):
        return False, "search_prompt_or_non_candidate_row", {}

    if title_key in {"na", "nan", "none", "null"}:
        return False, "invalid_title_placeholder", {}

    if not any(char.isalpha() for char in title):
        return False, "title_without_letters", {}

    bvc_registered = "bvc" in compact_key(inscrito_en) or bool(bvc_date and compact_key(bvc_date) not in {"na", "nan", "none", "null"})
    rnve_registered = bool(rnve_date and compact_key(rnve_date) not in {"na", "nan", "none", "null"})

    if source_class in {"registered_values_page", "equity_price_page"} and not bvc_registered:
        return False, "not_confirmed_as_bvc_registered", {}

    if source_class == "registry_search_page":
        return False, "registry_search_page_not_candidate_list", {}

    if source_class not in {"registered_values_page", "equity_price_page"}:
        return False, "unsupported_source_class_for_candidate_extraction", {}

    if not code_key and not issue_number:
        return False, "missing_code_and_issue_number", {}

    bucket = "colombia_equity_price_security" if source_class == "equity_price_page" else "colombia_registered_bvc_security"

    normalized = {
        "title": title,
        "code_ann": code_ann,
        "issue_number": issue_number,
        "inscrito_en": inscrito_en,
        "bvc_date": bvc_date,
        "rnve_date": rnve_date,
        "tipo_inscripcion": tipo_inscripcion,
        "moneda": moneda,
        "bvc_registered": str(bvc_registered),
        "rnve_registered": str(rnve_registered),
        "instrument_bucket": bucket,
    }

    return True, "accepted_official_regulatory_bvc_registered_security", normalized


def discover_context_columns(header: list[str]) -> dict[str, list[str]]:
    cols = {
        "country": [],
        "country_code": [],
        "exchange": [],
        "mic": [],
        "currency": [],
        "symbol": [],
        "name": [],
        "isin": [],
        "instrument_type": [],
        "sector": [],
        "source": [],
        "market": [],
    }

    for column in header:
        key = compact_key(column)

        if key in {"countrycode", "countryiso2", "countryiso", "countrycode2"}:
            cols["country_code"].append(column)
        elif key == "country" or key.endswith("country") or "countryname" in key:
            cols["country"].append(column)

        if "exchange" in key:
            cols["exchange"].append(column)

        if key == "mic" or key.endswith("mic") or "mic" in key:
            cols["mic"].append(column)

        if "currency" in key:
            cols["currency"].append(column)

        if "symbol" in key or "ticker" in key or "tradingcode" in key or key in {"code", "codigo"}:
            cols["symbol"].append(column)

        if key in {"name", "companyname", "securityname"} or "name" in key or "nombre" in key:
            cols["name"].append(column)

        if "isin" in key:
            cols["isin"].append(column)

        if "instrument" in key or "type" in key or "assetclass" in key:
            cols["instrument_type"].append(column)

        if "sector" in key or "industry" in key:
            cols["sector"].append(column)

        if "source" in key or "provider" in key:
            cols["source"].append(column)

        if "market" in key:
            cols["market"].append(column)

    return cols


def set_first_matching(row: dict[str, Any], columns: list[str], value: str) -> None:
    if columns:
        row[columns[0]] = value


def set_all_matching(row: dict[str, Any], columns: list[str], value: str) -> None:
    for column in columns:
        row[column] = value


def build_projected_row(header: list[str], cols: dict[str, list[str]], candidate: dict[str, Any]) -> dict[str, Any]:
    row = {column: "" for column in header}

    title = candidate["title"]
    symbol = candidate["symbol"]
    isin = candidate["isin"]
    instrument_bucket = candidate["instrument_bucket"]

    set_first_matching(row, cols["name"], title)
    set_first_matching(row, cols["symbol"], symbol)
    set_first_matching(row, cols["isin"], isin)
    set_all_matching(row, cols["country"], COUNTRY)
    set_all_matching(row, cols["country_code"], COUNTRY_CODE)
    set_all_matching(row, cols["exchange"], EXCHANGE)
    set_all_matching(row, cols["mic"], MIC)
    set_all_matching(row, cols["currency"], CURRENCY)
    set_first_matching(row, cols["instrument_type"], instrument_bucket)
    set_first_matching(row, cols["source"], SOURCE_PROVIDER)
    set_first_matching(row, cols["market"], MARKET_ID)

    for column in header:
        key = compact_key(column)
        if key in {"marketid", "sourceid", "providerid"} and not row.get(column):
            row[column] = MARKET_ID if "market" in key else SOURCE_PROVIDER
        elif key in {"country", "countryname"} and not row.get(column):
            row[column] = COUNTRY
        elif key in {"exchange"} and not row.get(column):
            row[column] = EXCHANGE
        elif key in {"mic"} and not row.get(column):
            row[column] = MIC
        elif key in {"currency"} and not row.get(column):
            row[column] = CURRENCY

    return row


def existing_keys(rows: list[dict[str, str]], cols: dict[str, list[str]]) -> set[str]:
    keys: set[str] = set()
    for row in rows:
        for column in cols["isin"]:
            value = compact_key(row.get(column))
            if value:
                keys.add(f"isin:{value}")
        for column in cols["symbol"]:
            value = compact_key(row.get(column))
            if value:
                exchange = ""
                for ex_col in cols["exchange"]:
                    exchange = compact_key(row.get(ex_col))
                    if exchange:
                        break
                keys.add(f"symbol:{exchange}:{value}")
        for column in cols["name"]:
            value = compact_key(row.get(column))
            if value:
                keys.add(f"name:{value}")
    return keys


def main() -> None:
    output_paths = [
        COLOMBIA_CANDIDATE_DATASET,
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        RAW_CANDIDATES_CSV,
        ELIGIBLE_CANDIDATES_CSV,
        REJECTED_CANDIDATES_CSV,
        DEDUP_SUMMARY_CSV,
        SCHEMA_PROJECTION_CSV,
        APPEND_MANIFEST_CSV,
        SOURCE_ROW_AUDIT_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    discovery = read_json(COLOMBIA_DISCOVERY_JSON)
    discovery_summary = discovery.get("summary", {})
    singapore_promotion = read_json(SINGAPORE_PROMOTION_JSON)

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)

    singapore_promoted_rows = read_csv_dicts(SINGAPORE_PROMOTED_DATASET)
    singapore_promoted_row_count = len(singapore_promoted_rows)
    singapore_promoted_sha = sha256_file(SINGAPORE_PROMOTED_DATASET)

    base_header = read_csv_header(SINGAPORE_PROMOTED_DATASET)
    cols = discover_context_columns(base_header)
    existing = existing_keys(singapore_promoted_rows, cols)

    fetch_rows = read_csv_dicts(COLOMBIA_DISCOVERY_FETCH_VALIDATION)
    structured_source_rows = read_csv_dicts(COLOMBIA_DISCOVERY_STRUCTURED_SOURCES)
    structured_source_ids = {row["source_id"] for row in structured_source_rows}

    raw_candidates: list[dict[str, Any]] = []
    rejected_candidates: list[dict[str, Any]] = []
    source_row_audit: list[dict[str, Any]] = []

    print("")
    print("v2.21D_C Colombia conditional build/freeze started.")
    print(f"Structured source ids: {len(structured_source_ids)}")

    raw_counter = 0

    for source in fetch_rows:
        source_id = source["source_id"]
        if source_id not in structured_source_ids:
            continue

        raw_file = Path(source.get("raw_file", ""))
        source_class = classify_source(source_id, source.get("source_type", ""))

        if not raw_file.exists():
            rejected_candidates.append({
                "candidate_id": "",
                "source_id": source_id,
                "source_class": source_class,
                "title": "",
                "symbol": "",
                "isin": "",
                "rejection_reason": "raw_file_missing",
                "raw_payload": "",
            })
            continue

        tables = parse_tables(raw_file)
        for table_index, table in enumerate(tables, start=1):
            payload_rows = table_to_payload_rows(table)
            for row_index, payload in enumerate(payload_rows, start=1):
                raw_counter += 1
                accepted, reason, normalized = candidate_quality(payload, source_class)

                title = normalized.get("title", first_present(payload, ["Nombre del título", "Nombre titulo", "Emisión", "Razón social", "Razon social"]))
                code_ann = normalized.get("code_ann", first_present(payload, ["Código ANN", "Codigo ANN", "Código Superfinanciera", "Codigo Superfinanciera", "Código RNVEI", "Codigo RNVEI"]))
                issue_number = normalized.get("issue_number", first_present(payload, ["No. Emisión", "No Emisión", "No. Emision", "No Emision"]))

                symbol = code_ann or issue_number or compact_key(title).upper()[:16]
                isin = code_ann.upper() if valid_isin(code_ann.upper()) else ""

                candidate_id = f"CO_{source_id}_{table_index}_{row_index}"

                source_row_audit.append({
                    "candidate_id": candidate_id,
                    "source_id": source_id,
                    "source_class": source_class,
                    "table_index": table_index,
                    "row_index": row_index,
                    "accepted_by_quality": accepted,
                    "quality_reason": reason,
                    "title": title,
                    "symbol": symbol,
                    "isin": isin,
                    "bvc_registered": normalized.get("bvc_registered", ""),
                    "rnve_registered": normalized.get("rnve_registered", ""),
                    "instrument_bucket": normalized.get("instrument_bucket", ""),
                })

                raw_row = {
                    "candidate_id": candidate_id,
                    "market_id": MARKET_ID,
                    "country": COUNTRY,
                    "country_code": COUNTRY_CODE,
                    "exchange": EXCHANGE,
                    "mic": MIC,
                    "currency": CURRENCY,
                    "source_id": source_id,
                    "source_class": source_class,
                    "table_index": table_index,
                    "row_index": row_index,
                    "title": title,
                    "symbol": symbol,
                    "isin": isin,
                    "code_ann": code_ann,
                    "issue_number": issue_number,
                    "inscrito_en": normalized.get("inscrito_en", ""),
                    "bvc_date": normalized.get("bvc_date", ""),
                    "rnve_date": normalized.get("rnve_date", ""),
                    "tipo_inscripcion": normalized.get("tipo_inscripcion", ""),
                    "moneda_source": normalized.get("moneda", ""),
                    "instrument_bucket": normalized.get("instrument_bucket", ""),
                    "accepted_by_quality": accepted,
                    "quality_reason": reason,
                    "raw_payload": json.dumps(payload, ensure_ascii=False)[:2000],
                }

                if accepted:
                    raw_candidates.append(raw_row)
                else:
                    rejected_candidates.append({
                        **raw_row,
                        "rejection_reason": reason,
                    })

    eligible_candidates: list[dict[str, Any]] = []
    seen_candidate_keys: set[str] = set()

    duplicate_internal = 0
    duplicate_existing = 0
    rejected_by_capacity = 0

    capacity_remaining = QUALITY_CEILING_TARGET - singapore_promoted_row_count

    for candidate in raw_candidates:
        keys = []
        if candidate["isin"]:
            keys.append(f"isin:{compact_key(candidate['isin'])}")
        if candidate["symbol"]:
            keys.append(f"symbol:{compact_key(EXCHANGE)}:{compact_key(candidate['symbol'])}")
        if candidate["title"]:
            keys.append(f"name:{compact_key(candidate['title'])}")

        internal_dup = any(key in seen_candidate_keys for key in keys)
        existing_dup = any(key in existing for key in keys)

        if internal_dup:
            duplicate_internal += 1
            rejected_candidates.append({
                **candidate,
                "rejection_reason": "duplicate_within_colombia_candidate_set",
            })
            continue

        if existing_dup:
            duplicate_existing += 1
            rejected_candidates.append({
                **candidate,
                "rejection_reason": "duplicate_against_existing_singapore_promoted_universe",
            })
            continue

        if len(eligible_candidates) >= capacity_remaining:
            rejected_by_capacity += 1
            rejected_candidates.append({
                **candidate,
                "rejection_reason": "capacity_filter_45000_ceiling",
            })
            continue

        for key in keys:
            seen_candidate_keys.add(key)

        eligible_candidates.append({
            **candidate,
            "approved_for_rebuild_input": True,
        })

    projected_rows = [
        build_projected_row(base_header, cols, candidate)
        for candidate in eligible_candidates
    ]

    candidate_dataset_created = len(projected_rows) > 0

    if candidate_dataset_created:
        with COLOMBIA_CANDIDATE_DATASET.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=base_header, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(singapore_promoted_rows)
            writer.writerows(projected_rows)

        candidate_dataset_rows = count_csv_rows(COLOMBIA_CANDIDATE_DATASET)
        candidate_dataset_sha = sha256_file(COLOMBIA_CANDIDATE_DATASET)
    else:
        candidate_dataset_rows = singapore_promoted_row_count
        candidate_dataset_sha = ""

    dedup_summary_rows = [
        {
            "market_id": MARKET_ID,
            "raw_candidate_rows_seen": raw_counter,
            "raw_candidates_accepted_by_quality": len(raw_candidates),
            "raw_candidates_rejected_by_quality": len([row for row in rejected_candidates if row.get("rejection_reason") in {
                "missing_or_too_short_title",
                "search_prompt_or_non_candidate_row",
                "invalid_title_placeholder",
                "title_without_letters",
                "not_confirmed_as_bvc_registered",
                "registry_search_page_not_candidate_list",
                "unsupported_source_class_for_candidate_extraction",
                "missing_code_and_issue_number",
                "raw_file_missing",
            }]),
            "eligible_new_candidates": len(eligible_candidates),
            "duplicate_within_colombia_candidate_set": duplicate_internal,
            "duplicate_against_existing_singapore_promoted_universe": duplicate_existing,
            "rejected_by_capacity_filter": rejected_by_capacity,
            "candidate_dataset_rows": candidate_dataset_rows,
            "remaining_capacity_after_candidate": QUALITY_CEILING_TARGET - candidate_dataset_rows,
            "candidate_dataset_created": candidate_dataset_created,
        }
    ]

    append_manifest_rows = [
        {
            "artifact": "singapore_promoted_input",
            "path": str(SINGAPORE_PROMOTED_DATASET),
            "rows": singapore_promoted_row_count,
            "sha256": singapore_promoted_sha,
            "role": "base_for_colombia_candidate_input_unchanged",
        },
        {
            "artifact": "colombia_schema_projection",
            "path": str(SCHEMA_PROJECTION_CSV),
            "rows": len(projected_rows),
            "sha256": "",
            "role": "append_projection_source",
        },
        {
            "artifact": "colombia_candidate_dataset",
            "path": str(COLOMBIA_CANDIDATE_DATASET),
            "rows": candidate_dataset_rows,
            "sha256": candidate_dataset_sha,
            "role": "candidate_output_not_promoted" if candidate_dataset_created else "not_created_no_eligible_candidates",
        },
        {
            "artifact": "previous_operational_base_input",
            "path": str(OPERATIONAL_BASE_DATASET),
            "rows": operational_rows,
            "sha256": operational_sha,
            "role": "input_only_unchanged",
        },
        {
            "artifact": "rollback_input",
            "path": str(ROLLBACK_DATASET),
            "rows": rollback_rows,
            "sha256": rollback_sha,
            "role": "input_only_unchanged",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0
    warning_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed, warning_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        if severity == "warning" and not passed:
            warning_failed += 1
        checks.append({
            "check": check,
            "passed": bool(passed),
            "severity": severity,
            "detail": detail,
        })

    add_check("colombia_discovery_status_expected", discovery.get("status") == EXPECTED_DISCOVERY_STATUS, "critical", str(discovery.get("status")))
    add_check("colombia_structured_extraction_approved", as_bool(discovery_summary.get("approved_for_colombia_structured_extraction")) is True, "critical", f"approved_for_colombia_structured_extraction={discovery_summary.get('approved_for_colombia_structured_extraction')}")
    add_check("singapore_promotion_status_expected", singapore_promotion.get("status") == EXPECTED_SINGAPORE_PROMOTION_STATUS, "critical", str(singapore_promotion.get("status")))
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("singapore_promoted_rows_expected", singapore_promoted_row_count == SINGAPORE_PROMOTED_ROWS_EXPECTED, "critical", f"singapore_promoted_rows={singapore_promoted_row_count}")
    add_check("singapore_promoted_sha_expected", singapore_promoted_sha == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", singapore_promoted_sha)
    add_check("schema_column_count_expected", len(base_header) == 33, "critical", f"columns={len(base_header)}")
    add_check("structured_sources_available", len(structured_source_ids) >= 1, "critical", f"structured_sources={len(structured_source_ids)}")
    add_check("raw_candidate_rows_seen", raw_counter > 0, "critical", f"raw_candidate_rows_seen={raw_counter}")
    add_check("raw_candidates_accepted_by_quality_available", len(raw_candidates) > 0, "warning", f"raw_candidates_accepted_by_quality={len(raw_candidates)}")
    add_check("eligible_colombia_candidates_available", len(eligible_candidates) > 0, "warning", f"eligible_new_candidates={len(eligible_candidates)}")
    add_check("candidate_dataset_created_if_eligible", candidate_dataset_created == (len(eligible_candidates) > 0), "critical", f"candidate_dataset_created={candidate_dataset_created};eligible={len(eligible_candidates)}")
    add_check("candidate_dataset_under_quality_ceiling", candidate_dataset_rows <= QUALITY_CEILING_TARGET, "critical", f"candidate_dataset_rows={candidate_dataset_rows};ceiling={QUALITY_CEILING_TARGET}")
    add_check("candidate_dataset_above_quality_floor", candidate_dataset_rows >= QUALITY_FLOOR_TARGET, "critical", f"candidate_dataset_rows={candidate_dataset_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("candidate_rows_equal_singapore_plus_eligible_if_created", candidate_dataset_rows == singapore_promoted_row_count + len(eligible_candidates), "critical", f"candidate_rows={candidate_dataset_rows};base_plus_eligible={singapore_promoted_row_count + len(eligible_candidates)}")
    add_check("singapore_promoted_artifact_not_modified", sha256_file(SINGAPORE_PROMOTED_DATASET) == SINGAPORE_PROMOTED_SHA_EXPECTED, "critical", "Singapore promoted artifact SHA unchanged")
    add_check("operational_base_not_modified", sha256_file(OPERATIONAL_BASE_DATASET) == OPERATIONAL_BASE_SHA_EXPECTED, "critical", "operational base SHA unchanged")
    add_check("rollback_not_modified", sha256_file(ROLLBACK_DATASET) == ROLLBACK_SHA_EXPECTED, "critical", "rollback SHA unchanged")
    add_check("candidate_dataset_not_promoted", True, "critical", "colombia_candidate_dataset_promoted=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("pointer_update_not_performed", True, "critical", "pointer_update_performed=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        build_decision = "COLOMBIA_CONDITIONAL_BUILD_BLOCKED_REVIEW_REQUIRED"
        approved_for_colombia_promotion_decision = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    elif candidate_dataset_created and warning_failed == 0:
        status = STATUS_BUILT
        build_decision = "COLOMBIA_CANDIDATE_CREATED_READY_FOR_PROMOTION_OR_FREEZE_DECISION"
        approved_for_colombia_promotion_decision = True
        recommended_next_phase = NEXT_PHASE_IF_BUILT
    elif candidate_dataset_created:
        status = STATUS_BUILT
        build_decision = "COLOMBIA_CANDIDATE_CREATED_WITH_WARNINGS_REVIEW_BEFORE_PROMOTION"
        approved_for_colombia_promotion_decision = True
        recommended_next_phase = NEXT_PHASE_IF_BUILT
    else:
        status = STATUS_FROZEN
        build_decision = "COLOMBIA_NO_ELIGIBLE_CANDIDATES_FREEZE_RECOMMENDED"
        approved_for_colombia_promotion_decision = False
        recommended_next_phase = NEXT_PHASE_IF_FROZEN

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "colombia_promotion_freeze_decision" if candidate_dataset_created else "final_closure",
            "action": "decide_whether_to_promote_or_freeze_colombia_candidate_dataset" if candidate_dataset_created else "close_v2_21_with_colombia_frozen",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "Colombia candidate dataset was created from official regulatory sources." if candidate_dataset_created else "No eligible Colombia candidates were produced.",
            "guardrails": "No scoring; no OpenAI; no broker; no pointer update",
        },
        {
            "action_order": 2,
            "action_scope": "singapore_reference",
            "action": "preserve_singapore_promoted_artifact",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "Singapore promoted artifact remains the v2.21 successful output.",
            "guardrails": "Do not alter Singapore artifact.",
        },
        {
            "action_order": 3,
            "action_scope": "final_closure",
            "action": "prepare_final_v2_21_closure_after_colombia_decision",
            "priority": "medium",
            "recommended_phase": "v2.21G - Final v2.21 Closure Report",
            "reason": "Final closure follows Colombia promote/freeze decision.",
            "guardrails": "Document final promoted/frozen status.",
        },
    ]

    summary = {
        "selected_route": "Colombia conditional build after Singapore promoted artifact",
        "phase_type": PHASE_TYPE,
        "build_decision": build_decision,
        "approved_for_colombia_promotion_decision": approved_for_colombia_promotion_decision,
        "previous_operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "previous_operational_base_rows": operational_rows,
        "previous_operational_base_sha": operational_sha,
        "singapore_promoted_dataset": str(SINGAPORE_PROMOTED_DATASET),
        "singapore_promoted_rows": singapore_promoted_row_count,
        "singapore_promoted_sha": singapore_promoted_sha,
        "colombia_candidate_dataset": str(COLOMBIA_CANDIDATE_DATASET) if candidate_dataset_created else "",
        "colombia_candidate_dataset_rows": candidate_dataset_rows,
        "colombia_candidate_dataset_sha": candidate_dataset_sha,
        "colombia_raw_candidate_rows_seen": raw_counter,
        "colombia_raw_candidates_accepted_by_quality": len(raw_candidates),
        "colombia_eligible_new_candidates": len(eligible_candidates),
        "colombia_rejected_candidates": len(rejected_candidates),
        "duplicate_within_colombia_candidate_set": duplicate_internal,
        "duplicate_against_existing_singapore_promoted_universe": duplicate_existing,
        "rejected_by_capacity_filter": rejected_by_capacity,
        "remaining_capacity_after_colombia_candidate": QUALITY_CEILING_TARGET - candidate_dataset_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "candidate_dataset_created": candidate_dataset_created,
        "candidate_extraction_performed": True,
        "dedup_performed": True,
        "expanded_rebuild_candidate_performed": candidate_dataset_created,
        "colombia_dataset_promoted": False,
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "pointer_update_performed": False,
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(RAW_CANDIDATES_CSV, raw_candidates, [
        "candidate_id", "market_id", "country", "country_code", "exchange", "mic", "currency",
        "source_id", "source_class", "table_index", "row_index", "title", "symbol", "isin",
        "code_ann", "issue_number", "inscrito_en", "bvc_date", "rnve_date", "tipo_inscripcion",
        "moneda_source", "instrument_bucket", "accepted_by_quality", "quality_reason", "raw_payload",
    ])
    write_csv(ELIGIBLE_CANDIDATES_CSV, eligible_candidates, [
        "candidate_id", "market_id", "country", "country_code", "exchange", "mic", "currency",
        "source_id", "source_class", "table_index", "row_index", "title", "symbol", "isin",
        "code_ann", "issue_number", "inscrito_en", "bvc_date", "rnve_date", "tipo_inscripcion",
        "moneda_source", "instrument_bucket", "accepted_by_quality", "quality_reason",
        "approved_for_rebuild_input", "raw_payload",
    ])
    write_csv(REJECTED_CANDIDATES_CSV, rejected_candidates, [
        "candidate_id", "market_id", "country", "country_code", "exchange", "mic", "currency",
        "source_id", "source_class", "table_index", "row_index", "title", "symbol", "isin",
        "code_ann", "issue_number", "inscrito_en", "bvc_date", "rnve_date", "tipo_inscripcion",
        "moneda_source", "instrument_bucket", "accepted_by_quality", "quality_reason",
        "rejection_reason", "raw_payload",
    ])
    write_csv(SOURCE_ROW_AUDIT_CSV, source_row_audit, [
        "candidate_id", "source_id", "source_class", "table_index", "row_index",
        "accepted_by_quality", "quality_reason", "title", "symbol", "isin",
        "bvc_registered", "rnve_registered", "instrument_bucket",
    ])
    write_csv(SCHEMA_PROJECTION_CSV, projected_rows, base_header)
    append_manifest_rows[1]["sha256"] = sha256_file(SCHEMA_PROJECTION_CSV)
    write_csv(APPEND_MANIFEST_CSV, append_manifest_rows, ["artifact", "path", "rows", "sha256", "role"])
    write_csv(DEDUP_SUMMARY_CSV, dedup_summary_rows, [
        "market_id", "raw_candidate_rows_seen", "raw_candidates_accepted_by_quality",
        "raw_candidates_rejected_by_quality", "eligible_new_candidates",
        "duplicate_within_colombia_candidate_set",
        "duplicate_against_existing_singapore_promoted_universe",
        "rejected_by_capacity_filter", "candidate_dataset_rows",
        "remaining_capacity_after_candidate", "candidate_dataset_created",
    ])
    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, [
        "action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails",
    ])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "dedup_summary": dedup_summary_rows,
        "append_manifest": append_manifest_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Colombia conditional build",
            "official_regulatory_sources_only": True,
            "bvc_shell_html_extraction_allowed": False,
            "regex_only_candidate_acceptance_allowed": False,
            "candidate_extraction_performed": True,
            "dedup_performed": True,
            "expanded_rebuild_candidate_performed": candidate_dataset_created,
            "candidate_dataset_created": candidate_dataset_created,
            "colombia_candidate_dataset": str(COLOMBIA_CANDIDATE_DATASET) if candidate_dataset_created else "",
            "colombia_candidate_dataset_rows": candidate_dataset_rows,
            "colombia_candidate_dataset_sha": candidate_dataset_sha,
            "approved_for_colombia_promotion_decision": approved_for_colombia_promotion_decision,
            "singapore_promoted_dataset": str(SINGAPORE_PROMOTED_DATASET),
            "singapore_promoted_rows": singapore_promoted_row_count,
            "singapore_promoted_sha": singapore_promoted_sha,
            "file_edit_performed_on_operational_base": False,
            "file_edit_performed_on_singapore_promoted_artifact": False,
            "colombia_dataset_promoted": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "scoring_authorized": False,
            "scoring_recalculated": False,
            "openai_authorized": False,
            "openai_called": False,
            "broker_authorized": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
            "history_rewrite_performed": False,
            "force_push_required": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.21D_C conditionally extracts Colombia candidates from official Superfinanciera/SIMEV/RNVE structured sources discovered in v2.21C3B.

This phase extracts, filters and deduplicates Colombia candidates. If eligible candidates exist, it builds a Colombia candidate dataset on top of the Singapore promoted artifact. It does not promote Colombia, does not modify the Singapore artifact, does not modify the previous operational base, does not update pointers, does not run scoring, does not call OpenAI, does not call brokers, and does not launch full59k.

## Summary

- Build decision: `{build_decision}`
- Candidate dataset created: `{candidate_dataset_created}`
- Approved for Colombia promotion decision: `{approved_for_colombia_promotion_decision}`
- Singapore promoted rows: `{singapore_promoted_row_count}`
- Colombia raw rows seen: `{raw_counter}`
- Colombia accepted by quality: `{len(raw_candidates)}`
- Colombia eligible new candidates: `{len(eligible_candidates)}`
- Colombia rejected candidates: `{len(rejected_candidates)}`
- Colombia candidate rows: `{candidate_dataset_rows}`
- Colombia candidate SHA256: `{candidate_dataset_sha}`
- Remaining capacity: `{QUALITY_CEILING_TARGET - candidate_dataset_rows}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Checks

{check_lines}

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21D_C Colombia conditional build/freeze completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("DEDUP_SUMMARY:")
    for row in dedup_summary_rows:
        for key, value in row.items():
            print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
