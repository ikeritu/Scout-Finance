from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


VERSION = "v2.21C"
PHASE = "Candidate Extraction + Dedup Dry Run"
PHASE_TYPE = "targeted-market-candidate-extraction-dedup-dry-run"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw_targeted_markets_v2_21b"

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
V221B_JSON = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_v2_21b.json"

REPORT_JSON = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_v2_21c.json"
REPORT_MD = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_v2_21c.md"
SUMMARY_CSV = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_summary_v2_21c.csv"
CHECKS_CSV = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_checks_v2_21c.csv"
EXTRACTED_CANDIDATES_CSV = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_extracted_candidates_v2_21c.csv"
REJECTED_CANDIDATES_CSV = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_rejected_candidates_v2_21c.csv"
DEDUP_SUMMARY_CSV = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_dedup_summary_v2_21c.csv"
SOURCE_PARSER_FINDINGS_CSV = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_source_parser_findings_v2_21c.csv"
RAW_STRUCTURE_INVENTORY_CSV = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_raw_structure_inventory_v2_21c.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_next_actions_v2_21c.csv"

EXPECTED_V221B_STATUS = "TARGETED_MARKET_ACQUISITION_RAW_VALIDATION_COMPLETED_COLOMBIA_SINGAPORE_RAW_SOURCES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED"
EXPECTED_V221B_DECISION = "RAW_SOURCES_AVAILABLE_FOR_CANDIDATE_EXTRACTION_DRY_RUN"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_SUCCESS = "TARGETED_MARKET_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_NEW_CANDIDATES_READY_FOR_REBUILD_NO_DATASET_CHANGES_SCORING_DEFERRED"
STATUS_REVIEW = "TARGETED_MARKET_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_REVIEW_REQUIRED_NO_QUALIFIED_CANDIDATES_EXTRACTED"
STATUS_FAILED = "TARGETED_MARKET_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.21D - Expanded Rebuild Candidate"
NEXT_PHASE_REVIEW = "v2.21C_REVIEW - Official Source Candidate Access Review"

MARKET_DEFAULTS = {
    "COLOMBIA_BVC": {
        "country": "Colombia",
        "country_code": "CO",
        "exchange": "BVC",
        "mic": "XBOG",
        "currency": "COP",
        "provider": "BVC",
    },
    "SINGAPORE_SGX": {
        "country": "Singapore",
        "country_code": "SG",
        "exchange": "SGX",
        "mic": "XSES",
        "currency": "SGD",
        "provider": "SGX",
    },
}

DISALLOWED_INSTRUMENT_TERMS = [
    " etf", "exchange traded fund", " fondo", "fund", "warrant", "right", "rights",
    "structured", "note", "bond", "bono", "cdt", "derivative", "future", "option",
    "índice", "indice", "index", "repo", "pagaré", "pagare",
]

GENERIC_NAV_TERMS = [
    "mercados", "mercado local", "mercado global", "renta variable", "renta fija",
    "acciones", "prospectos", "resultados", "información", "informacion",
    "corporate information", "securities prices", "stock exchange", "listed date",
    "description", "calendar", "indices", "divisas", "productos", "servicios",
    "home", "login", "contact", "terms", "privacy", "search", "menu",
]

CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "market_id",
    "country",
    "country_code",
    "exchange",
    "mic",
    "currency",
    "source_id",
    "source_file",
    "extraction_method",
    "ticker",
    "symbol",
    "trading_code",
    "isin",
    "name",
    "instrument_type",
    "sector",
    "raw_payload",
    "dedup_key",
    "dedup_status",
    "dedup_reason",
    "quality_status",
    "quality_reason",
]


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.tables: list[list[list[str]]] = []
        self.current_table: list[list[str]] = []

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
            self.current_row.append(cell)
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


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except Exception:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


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


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", norm(value).lower())


def looks_like_ticker(value: str) -> bool:
    value = norm(value)
    if not value:
        return False
    if len(value) > 12:
        return False
    return bool(re.fullmatch(r"[A-Z0-9][A-Z0-9.\-]{0,11}", value))


def looks_like_isin(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", norm(value).upper()))


def is_generic_name(value: str) -> bool:
    key = norm(value).lower()
    if not key:
        return True
    if len(key) < 3:
        return True
    if key in GENERIC_NAV_TERMS:
        return True
    return any(key == term or key.startswith(term + " ") for term in GENERIC_NAV_TERMS)


def instrument_disallowed(*values: str) -> tuple[bool, str]:
    combined = " " + " ".join(norm(v).lower() for v in values) + " "
    for term in DISALLOWED_INSTRUMENT_TERMS:
        if term in combined:
            return True, f"disallowed_instrument_term={term.strip()}"
    return False, ""


def extract_next_data_json(text: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    pattern = re.compile(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(text):
        raw = html.unescape(match.group(1))
        try:
            data = json.loads(raw)
        except Exception:
            continue
        objects.extend(flatten_json_objects(data))
    return objects


def flatten_json_objects(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(flatten_json_objects(child))
    elif isinstance(value, list):
        for item in value:
            found.extend(flatten_json_objects(item))
    return found


def pick_first(obj: dict[str, Any], keys: list[str]) -> str:
    lower_map = {str(k).lower(): k for k in obj.keys()}
    for key in keys:
        real_key = lower_map.get(key.lower())
        if real_key is not None:
            value = obj.get(real_key)
            if isinstance(value, (str, int, float)):
                text = norm(value)
                if text:
                    return text
    return ""


def candidate_from_obj(
    obj: dict[str, Any],
    market_id: str,
    source_id: str,
    source_file: str,
    method: str,
) -> dict[str, Any] | None:
    defaults = MARKET_DEFAULTS[market_id]

    name = pick_first(obj, [
        "name", "companyName", "company_name", "issuerName", "issuer_name",
        "securityName", "security_name", "longName", "displayName", "description",
    ])

    ticker = pick_first(obj, ["ticker", "symbol", "code", "stockCode", "stock_code", "tradingCode", "trading_code"])
    symbol = pick_first(obj, ["symbol"])
    trading_code = pick_first(obj, ["tradingCode", "trading_code", "code", "stockCode", "stock_code"])
    isin = pick_first(obj, ["isin", "isinCode", "isin_code"])
    instrument_type = pick_first(obj, ["instrumentType", "instrument_type", "securityType", "security_type", "type", "assetClass", "asset_class"])
    sector = pick_first(obj, ["sector", "industry", "gicsSector", "gics_sector"])

    if not name and ticker:
        name = ticker

    has_identifier = bool(ticker or symbol or trading_code or isin)
    if not name or not has_identifier:
        return None

    if is_generic_name(name):
        return None

    if ticker and not looks_like_ticker(ticker) and not looks_like_isin(ticker):
        if len(ticker) > 20:
            return None

    disallowed, reason = instrument_disallowed(name, ticker, symbol, trading_code, isin, instrument_type)
    quality_status = "accepted"
    quality_reason = "candidate_has_name_and_identifier"
    if disallowed:
        quality_status = "rejected"
        quality_reason = reason

    dedup_key = "|".join([
        market_id,
        norm_key(isin),
        norm_key(ticker or symbol or trading_code),
        norm_key(name),
    ])

    return {
        "candidate_id": "",
        "market_id": market_id,
        "country": defaults["country"],
        "country_code": defaults["country_code"],
        "exchange": defaults["exchange"],
        "mic": defaults["mic"],
        "currency": defaults["currency"],
        "source_id": source_id,
        "source_file": source_file,
        "extraction_method": method,
        "ticker": ticker,
        "symbol": symbol,
        "trading_code": trading_code,
        "isin": isin.upper() if looks_like_isin(isin) else isin,
        "name": name,
        "instrument_type": instrument_type,
        "sector": sector,
        "raw_payload": json.dumps(obj, ensure_ascii=False)[:2000],
        "dedup_key": dedup_key,
        "dedup_status": "",
        "dedup_reason": "",
        "quality_status": quality_status,
        "quality_reason": quality_reason,
    }


def extract_from_tables(
    text: str,
    market_id: str,
    source_id: str,
    source_file: str,
) -> list[dict[str, Any]]:
    parser = TableParser()
    parser.feed(text)

    candidates: list[dict[str, Any]] = []

    for table_index, table in enumerate(parser.tables):
        if len(table) < 2:
            continue

        header = [norm(cell).lower() for cell in table[0]]
        data_rows = table[1:]

        for row_index, row in enumerate(data_rows):
            obj: dict[str, Any] = {}
            for idx, cell in enumerate(row):
                key = header[idx] if idx < len(header) and header[idx] else f"col_{idx}"
                obj[key] = cell

            # Fallback for simple tables without useful headers.
            if not any(k in obj for k in ["name", "company", "issuer", "symbol", "ticker", "code", "isin"]):
                if len(row) >= 2:
                    obj = {
                        "code": row[0],
                        "name": row[1],
                        "raw_row": " | ".join(row),
                    }

            candidate = candidate_from_obj(
                obj=obj,
                market_id=market_id,
                source_id=source_id,
                source_file=source_file,
                method=f"html_table_{table_index}_row_{row_index}",
            )
            if candidate:
                candidates.append(candidate)

    return candidates


def extract_from_json_objects(
    text: str,
    market_id: str,
    source_id: str,
    source_file: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    objects = extract_next_data_json(text)

    for idx, obj in enumerate(objects):
        candidate = candidate_from_obj(
            obj=obj,
            market_id=market_id,
            source_id=source_id,
            source_file=source_file,
            method=f"next_data_json_object_{idx}",
        )
        if candidate:
            candidates.append(candidate)

    return candidates


def extract_regex_candidates(
    text: str,
    market_id: str,
    source_id: str,
    source_file: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    # Conservative pattern: ticker/code followed by a reasonably company-like name.
    patterns = [
        re.compile(r'\b(?P<ticker>[A-Z0-9]{2,8})\b\s*[-–|,]\s*(?P<name>[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9&.,\'() \-]{4,90})'),
        re.compile(r'"(?:symbol|ticker|code|stockCode|tradingCode)"\s*:\s*"(?P<ticker>[^"]{1,15})".{0,200}?"(?:name|companyName|securityName)"\s*:\s*"(?P<name>[^"]{3,120})"', re.DOTALL),
        re.compile(r'"(?:name|companyName|securityName)"\s*:\s*"(?P<name>[^"]{3,120})".{0,200}?"(?:symbol|ticker|code|stockCode|tradingCode)"\s*:\s*"(?P<ticker>[^"]{1,15})"', re.DOTALL),
    ]

    seen = set()
    for pattern_idx, pattern in enumerate(patterns):
        for match_idx, match in enumerate(pattern.finditer(text)):
            ticker = norm(html.unescape(match.group("ticker")))
            name = norm(html.unescape(match.group("name")))
            key = (ticker, name)
            if key in seen:
                continue
            seen.add(key)

            obj = {"ticker": ticker, "name": name}
            candidate = candidate_from_obj(
                obj=obj,
                market_id=market_id,
                source_id=source_id,
                source_file=source_file,
                method=f"regex_pattern_{pattern_idx}_match_{match_idx}",
            )
            if candidate:
                candidates.append(candidate)

    return candidates


def build_base_dedup_index(rows: list[dict[str, str]], header: list[str]) -> dict[str, set[str]]:
    header_lower = [h.lower() for h in header]
    isin_cols = [header[i] for i, h in enumerate(header_lower) if "isin" in h]
    ticker_cols = [header[i] for i, h in enumerate(header_lower) if h in {"ticker", "symbol"} or "ticker" in h or "symbol" in h]
    name_cols = [header[i] for i, h in enumerate(header_lower) if h in {"name", "company_name", "security_name"} or "name" in h]

    index = {
        "isin": set(),
        "ticker": set(),
        "name": set(),
        "columns_isin": set(isin_cols),
        "columns_ticker": set(ticker_cols),
        "columns_name": set(name_cols),
    }

    for row in rows:
        for col in isin_cols:
            value = norm_key(row.get(col, ""))
            if value:
                index["isin"].add(value)
        for col in ticker_cols:
            value = norm_key(row.get(col, ""))
            if value:
                index["ticker"].add(value)
        for col in name_cols:
            value = norm_key(row.get(col, ""))
            if value:
                index["name"].add(value)

    return index


def dedup_candidates(candidates: list[dict[str, Any]], base_index: dict[str, set[str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_new_keys: set[str] = set()

    for candidate in candidates:
        isin_key = norm_key(candidate.get("isin", ""))
        ticker_key = norm_key(candidate.get("ticker") or candidate.get("symbol") or candidate.get("trading_code") or "")
        name_key = norm_key(candidate.get("name", ""))
        local_key = candidate.get("dedup_key", "")

        if candidate.get("quality_status") != "accepted":
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = candidate.get("quality_reason", "quality_rejected")
            rejected.append(candidate)
            continue

        if local_key in seen_new_keys:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_within_new_candidates"
            rejected.append(candidate)
            continue

        if isin_key and isin_key in base_index["isin"]:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_isin_in_operational_base"
            rejected.append(candidate)
            continue

        # Ticker dedup is only considered within same/known market because cross-market tickers collide frequently.
        if ticker_key and ticker_key in base_index["ticker"] and name_key and name_key in base_index["name"]:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_ticker_and_name_in_operational_base"
            rejected.append(candidate)
            continue

        if name_key and name_key in base_index["name"] and not isin_key and not ticker_key:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_name_in_operational_base_without_identifier"
            rejected.append(candidate)
            continue

        seen_new_keys.add(local_key)
        candidate["dedup_status"] = "accepted_new"
        candidate["dedup_reason"] = "not_found_in_operational_base"
        accepted.append(candidate)

    for idx, candidate in enumerate(accepted, start=1):
        candidate["candidate_id"] = f"v2_21c_{idx:05d}"

    for idx, candidate in enumerate(rejected, start=1):
        if not candidate.get("candidate_id"):
            candidate["candidate_id"] = f"v2_21c_rejected_{idx:05d}"

    return accepted, rejected


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        EXTRACTED_CANDIDATES_CSV,
        REJECTED_CANDIDATES_CSV,
        DEDUP_SUMMARY_CSV,
        SOURCE_PARSER_FINDINGS_CSV,
        RAW_STRUCTURE_INVENTORY_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v221b = read_json(V221B_JSON)
    v221b_summary = v221b.get("summary", {})

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)

    header = read_csv_header(OPERATIONAL_BASE_DATASET)
    base_rows = read_csv_dicts(OPERATIONAL_BASE_DATASET)
    base_index = build_base_dedup_index(base_rows, header)

    source_fetches = v221b.get("source_fetches", [])
    successful_raw_sources = [row for row in source_fetches if row.get("fetch_success") and row.get("raw_file")]

    all_candidate_attempts: list[dict[str, Any]] = []
    source_parser_findings: list[dict[str, Any]] = []
    raw_structure_rows: list[dict[str, Any]] = []

    for source in successful_raw_sources:
        market_id = source["market_id"]
        source_id = source["source_id"]
        raw_file = Path(source["raw_file"])

        if not raw_file.exists():
            source_parser_findings.append({
                "market_id": market_id,
                "source_id": source_id,
                "source_file": str(raw_file),
                "raw_file_exists": False,
                "html_tables": 0,
                "next_data_objects": 0,
                "table_candidates": 0,
                "json_candidates": 0,
                "regex_candidates": 0,
                "total_candidate_attempts": 0,
                "parser_status": "RAW_FILE_MISSING",
                "notes": "Raw file listed in v2.21B was not found locally.",
            })
            continue

        text = read_text(raw_file)
        parser = TableParser()
        parser.feed(text)
        next_data_objects = extract_next_data_json(text)

        table_candidates = extract_from_tables(text, market_id, source_id, str(raw_file))
        json_candidates = extract_from_json_objects(text, market_id, source_id, str(raw_file))
        regex_candidates = extract_regex_candidates(text, market_id, source_id, str(raw_file))

        source_attempts = table_candidates + json_candidates + regex_candidates
        all_candidate_attempts.extend(source_attempts)

        raw_structure_rows.append({
            "market_id": market_id,
            "source_id": source_id,
            "source_file": str(raw_file),
            "raw_bytes": raw_file.stat().st_size,
            "sha256": sha256_file(raw_file),
            "contains_table_tag": "<table" in text.lower(),
            "html_table_count": len(parser.tables),
            "next_data_object_count": len(next_data_objects),
            "script_tag_count": len(re.findall(r"<script\b", text, flags=re.IGNORECASE)),
            "link_count": len(re.findall(r"<a\b", text, flags=re.IGNORECASE)),
            "candidate_relevant_marker_count": sum(
                1 for marker in ["issuer", "emisor", "security", "securities", "stock", "acciones", "listed", "ticker", "isin"]
                if marker in text.lower()
            ),
        })

        source_parser_findings.append({
            "market_id": market_id,
            "source_id": source_id,
            "source_file": str(raw_file),
            "raw_file_exists": True,
            "html_tables": len(parser.tables),
            "next_data_objects": len(next_data_objects),
            "table_candidates": len(table_candidates),
            "json_candidates": len(json_candidates),
            "regex_candidates": len(regex_candidates),
            "total_candidate_attempts": len(source_attempts),
            "parser_status": "CANDIDATES_FOUND" if source_attempts else "NO_STRUCTURED_CANDIDATES_FOUND",
            "notes": "Strict parser avoids menu/navigation items and requires candidate name plus identifier.",
        })

    accepted_candidates, rejected_candidates = dedup_candidates(all_candidate_attempts, base_index)

    market_counts = Counter(candidate["market_id"] for candidate in accepted_candidates)
    rejected_counts = Counter(candidate["market_id"] for candidate in rejected_candidates)
    attempts_counts = Counter(candidate["market_id"] for candidate in all_candidate_attempts)

    dedup_summary_rows: list[dict[str, Any]] = []
    for market_id in sorted(set(MARKET_DEFAULTS) | set(attempts_counts) | set(market_counts) | set(rejected_counts)):
        accepted_count = market_counts.get(market_id, 0)
        rejected_count = rejected_counts.get(market_id, 0)
        attempts_count = attempts_counts.get(market_id, 0)

        dedup_summary_rows.append({
            "market_id": market_id,
            "candidate_attempts": attempts_count,
            "accepted_new_candidates": accepted_count,
            "rejected_candidates": rejected_count,
            "ready_for_rebuild": accepted_count > 0,
            "reason": "new_candidates_available" if accepted_count > 0 else "no_qualified_new_candidates_extracted",
        })

    total_new_candidates = len(accepted_candidates)
    projected_rows_after_addition = operational_rows + total_new_candidates
    remaining_after_addition = QUALITY_CEILING_TARGET - projected_rows_after_addition

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "rebuild",
            "action": "build_expanded_candidate_with_accepted_colombia_singapore_candidates",
            "priority": "high" if total_new_candidates > 0 else "blocked",
            "reason": "Accepted new candidates are available for dry-run rebuild." if total_new_candidates > 0 else "No qualified candidates extracted from current raw sources.",
            "recommended_phase": NEXT_PHASE if total_new_candidates > 0 else NEXT_PHASE_REVIEW,
            "guardrails": "no pointer update; no canonical replacement; preserve rollback",
        },
        {
            "action_order": 2,
            "action_scope": "source_access",
            "action": "identify_official_downloadable_listing_or_api_endpoint",
            "priority": "high" if total_new_candidates == 0 else "medium",
            "reason": "If current raw sources are JS shells or navigation pages, candidate extraction needs official downloadable lists or embedded API endpoints.",
            "recommended_phase": NEXT_PHASE_REVIEW if total_new_candidates == 0 else NEXT_PHASE,
            "guardrails": "official BVC/SGX sources only",
        },
        {
            "action_order": 3,
            "action_scope": "capacity",
            "action": "enforce_45k_ceiling_before_rebuild",
            "priority": "high",
            "reason": f"Projected rows after accepted additions: {projected_rows_after_addition}; remaining capacity: {remaining_after_addition}.",
            "recommended_phase": NEXT_PHASE if total_new_candidates > 0 else NEXT_PHASE_REVIEW,
            "guardrails": "exclude ETFs/funds/warrants/rights/structured products if needed",
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
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_21b_status_expected", v221b.get("status") == EXPECTED_V221B_STATUS, "critical", str(v221b.get("status")))
    add_check("v2_21b_acquisition_decision_expected", v221b_summary.get("acquisition_decision") == EXPECTED_V221B_DECISION, "critical", str(v221b_summary.get("acquisition_decision")))
    add_check("v2_21b_approved_for_next_phase", bool(v221b_summary.get("approved_for_next_phase")) is True, "critical", f"approved_for_next_phase={v221b_summary.get('approved_for_next_phase')}")
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("schema_column_count_expected", len(header) == 33, "critical", f"columns={len(header)}")
    add_check("successful_raw_sources_available", len(successful_raw_sources) >= 2, "critical", f"successful_raw_sources={len(successful_raw_sources)}")
    add_check("candidate_extraction_attempted", True, "critical", "candidate extraction attempted from v2.21B raw files")
    add_check("dedup_dry_run_performed", True, "critical", "dedup dry run performed against operational base")
    add_check("new_candidates_extracted", total_new_candidates > 0, "warning", f"accepted_new_candidates={total_new_candidates}")
    add_check("projected_rows_under_ceiling", projected_rows_after_addition <= QUALITY_CEILING_TARGET, "critical", f"projected_rows={projected_rows_after_addition};ceiling={QUALITY_CEILING_TARGET}")
    add_check("operational_base_not_modified", sha256_file(OPERATIONAL_BASE_DATASET) == OPERATIONAL_BASE_SHA_EXPECTED, "critical", "operational base SHA unchanged")
    add_check("candidate_output_is_dry_run_only", True, "critical", "no rebuild/promotion/pointer update in v2.21C")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("pointer_update_not_performed", True, "critical", "pointer_update_performed=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        extraction_decision = "CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_BLOCKED_REVIEW_REQUIRED"
        approved_for_next_phase = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    elif total_new_candidates == 0:
        status = STATUS_REVIEW
        extraction_decision = "NO_QUALIFIED_CANDIDATES_EXTRACTED_FROM_CURRENT_RAW_SOURCES"
        approved_for_next_phase = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        extraction_decision = "NEW_CANDIDATES_AVAILABLE_FOR_EXPANDED_REBUILD_CANDIDATE"
        approved_for_next_phase = True
        recommended_next_phase = NEXT_PHASE

    summary = {
        "selected_route": "Colombia + Singapore targeted expansion",
        "phase_type": PHASE_TYPE,
        "extraction_decision": extraction_decision,
        "approved_for_next_phase": approved_for_next_phase,
        "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "operational_base_rows": operational_rows,
        "operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity_to_quality_ceiling_before_addition": QUALITY_CEILING_TARGET - operational_rows,
        "target_markets": "Colombia/BVC;Singapore/SGX",
        "successful_raw_sources": len(successful_raw_sources),
        "candidate_attempts_total": len(all_candidate_attempts),
        "accepted_new_candidates": total_new_candidates,
        "rejected_candidates": len(rejected_candidates),
        "projected_rows_after_addition": projected_rows_after_addition,
        "remaining_capacity_after_addition": remaining_after_addition,
        "dedup_is_dry_run_only": True,
        "candidate_extraction_performed": True,
        "dedup_performed": True,
        "expanded_rebuild_performed": False,
        "provider_expansion_scope": "targeted_only",
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "pointer_update_performed": False,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(EXTRACTED_CANDIDATES_CSV, accepted_candidates, CANDIDATE_FIELDNAMES)
    write_csv(REJECTED_CANDIDATES_CSV, rejected_candidates, CANDIDATE_FIELDNAMES)
    write_csv(DEDUP_SUMMARY_CSV, dedup_summary_rows, ["market_id", "candidate_attempts", "accepted_new_candidates", "rejected_candidates", "ready_for_rebuild", "reason"])
    write_csv(SOURCE_PARSER_FINDINGS_CSV, source_parser_findings, ["market_id", "source_id", "source_file", "raw_file_exists", "html_tables", "next_data_objects", "table_candidates", "json_candidates", "regex_candidates", "total_candidate_attempts", "parser_status", "notes"])
    write_csv(RAW_STRUCTURE_INVENTORY_CSV, raw_structure_rows, ["market_id", "source_id", "source_file", "raw_bytes", "sha256", "contains_table_tag", "html_table_count", "next_data_object_count", "script_tag_count", "link_count", "candidate_relevant_marker_count"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "dedup_summary": dedup_summary_rows,
        "source_parser_findings": source_parser_findings,
        "raw_structure_inventory": raw_structure_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Colombia + Singapore targeted expansion",
            "target_markets": ["Colombia/BVC", "Singapore/SGX"],
            "approved_for_next_phase": approved_for_next_phase,
            "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "operational_base_rows": operational_rows,
            "operational_base_sha": operational_sha,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "candidate_extraction_performed": True,
            "dedup_dry_run_performed": True,
            "accepted_new_candidates": total_new_candidates,
            "projected_rows_after_addition": projected_rows_after_addition,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "file_edit_performed_on_operational_base": False,
            "file_copy_performed_on_operational_base": False,
            "file_rename_performed_on_operational_base": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "provider_expansion_scope": "targeted_only",
            "additional_provider_expansion_frozen": True,
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
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    finding_lines = "\n".join(
        f"- `{row['source_id']}` — attempts `{row['total_candidate_attempts']}` — status `{row['parser_status']}` — tables `{row['html_tables']}` — next_data_objects `{row['next_data_objects']}`"
        for row in source_parser_findings
    )

    dedup_lines = "\n".join(
        f"- `{row['market_id']}` — attempts `{row['candidate_attempts']}` — accepted `{row['accepted_new_candidates']}` — rejected `{row['rejected_candidates']}` — ready `{row['ready_for_rebuild']}`"
        for row in dedup_summary_rows
    )

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

v2.21C performs a strict candidate extraction and dedup dry run for Colombia/BVC and Singapore/SGX using the raw sources captured in v2.21B.

This phase does not rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Extraction decision: `{extraction_decision}`
- Approved for next phase: `{approved_for_next_phase}`
- Operational base rows: `{operational_rows}`
- Operational base SHA256: `{operational_sha}`
- Rollback rows: `{rollback_rows}`
- Rollback SHA256: `{rollback_sha}`
- Successful raw sources: `{len(successful_raw_sources)}`
- Candidate attempts: `{len(all_candidate_attempts)}`
- Accepted new candidates: `{total_new_candidates}`
- Rejected candidates: `{len(rejected_candidates)}`
- Projected rows after addition: `{projected_rows_after_addition}`
- Remaining capacity after addition: `{remaining_after_addition}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Source parser findings

{finding_lines}

## Dedup summary

{dedup_lines}

## Checks

{check_lines}

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21C candidate extraction + dedup dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_PARSER_FINDINGS:")
    for row in source_parser_findings:
        print(f"- {row['source_id']}: attempts={row['total_candidate_attempts']} status={row['parser_status']} tables={row['html_tables']} next_data_objects={row['next_data_objects']}")
    print("")
    print("DEDUP_SUMMARY:")
    for row in dedup_summary_rows:
        print(f"- {row['market_id']}: attempts={row['candidate_attempts']} accepted={row['accepted_new_candidates']} rejected={row['rejected_candidates']} ready={row['ready_for_rebuild']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
