from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.8C"
METHOD = "cboe_listed_symbols_validation_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

ACQUISITION_JSON = OUT_DIR / "cboe_listed_symbols_acquisition_real_v2_8b.json"
DISCOVERED_LINKS_CSV = OUT_DIR / "cboe_listed_symbols_discovered_links_v2_8b.csv"
SCHEMA_PROBE_CSV = OUT_DIR / "cboe_listed_symbols_schema_probe_v2_8b.csv"

EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_7b.csv"

PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / "cboe_listed_symbols"

RAW_LISTED_CSV = PROVIDER_DIR / "cboe_listed_symbols_raw.csv"
RAW_LISTED_XML = PROVIDER_DIR / "cboe_listed_symbols_raw.xml"
RAW_SYMBOLS_TRADED_CSV = PROVIDER_DIR / "cboe_symbols_traded_raw.csv"
RAW_SYMBOLS_TRADED_XML = PROVIDER_DIR / "cboe_symbols_traded_raw.xml"

OUT_JSON = OUT_DIR / "cboe_listed_symbols_validation_v2_8c.json"
OUT_MD = OUT_DIR / "cboe_listed_symbols_validation_v2_8c.md"
OUT_SCHEMA_DETAIL_CSV = OUT_DIR / "cboe_listed_symbols_schema_detail_v2_8c.csv"
OUT_NORMALIZED_CANDIDATE_CSV = OUT_DIR / "cboe_listed_symbols_normalized_candidate_v2_8c.csv"
OUT_NET_NEW_CSV = OUT_DIR / "cboe_listed_symbols_net_new_candidates_v2_8c.csv"
OUT_SAMPLE_CSV = OUT_DIR / "cboe_listed_symbols_validation_sample_v2_8c.csv"

CURRENT_EXPANDED_ROWS = 8007
TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000


NORMALIZED_COLUMNS = [
    "ticker",
    "company_name",
    "exchange",
    "country",
    "source_provider",
    "source_file",
    "instrument_type",
    "instrument_scope",
    "classification_confidence",
    "classification_reason",
    "sector",
    "industry",
    "market_cap",
    "raw_symbol",
    "raw_name",
    "raw_exchange",
    "raw_listing_market",
    "route_id",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_text_lines(path: Path, limit: int = 40) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return text.splitlines()[:limit]


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def score_header(fields: list[str]) -> int:
    normalized = [normalize_header(f) for f in fields]
    joined = " ".join(normalized)

    score = 0

    symbol_terms = [
        "symbol",
        "ticker",
        "security_symbol",
        "cboe_symbol",
        "root_symbol",
        "product_symbol",
    ]

    name_terms = [
        "name",
        "company",
        "company_name",
        "security_name",
        "issue_name",
        "description",
    ]

    exchange_terms = [
        "exchange",
        "market",
        "listing_market",
        "primary_listing_market",
        "listed_exchange",
    ]

    if any(term in normalized for term in symbol_terms):
        score += 50
    if any(term in joined for term in symbol_terms):
        score += 25

    if any(term in normalized for term in name_terms):
        score += 20
    if any(term in joined for term in name_terms):
        score += 10

    if any(term in normalized for term in exchange_terms):
        score += 10
    if any(term in joined for term in exchange_terms):
        score += 5

    if 2 <= len(fields) <= 40:
        score += 10

    if len(fields) == 1:
        score -= 15

    return score


def parse_csv_with_best_header(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "path": rel(path),
            "best_header_line": None,
            "fieldnames": [],
            "rows": [],
            "row_count": 0,
            "parse_error": "file_not_found",
            "first_lines": [],
        }

    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    first_lines = lines[:15]

    best: dict[str, Any] | None = None

    max_header_scan = min(25, len(lines))

    for header_line in range(max_header_scan):
        candidate_text = "\n".join(lines[header_line:])
        if not candidate_text.strip():
            continue

        try:
            sample = candidate_text[:4096]
            try:
                dialect = csv.Sniffer().sniff(sample)
            except Exception:
                dialect = csv.excel

            reader = csv.DictReader(candidate_text.splitlines(), dialect=dialect)
            rows = list(reader)
            fieldnames = list(reader.fieldnames or [])
            score = score_header(fieldnames)

            candidate = {
                "exists": True,
                "path": rel(path),
                "best_header_line": header_line,
                "fieldnames": fieldnames,
                "rows": rows,
                "row_count": len(rows),
                "score": score,
                "parse_error": "",
                "first_lines": first_lines,
            }

            if best is None or candidate["score"] > best["score"]:
                best = candidate
        except Exception as exc:
            continue

    if best is None:
        return {
            "exists": True,
            "path": rel(path),
            "best_header_line": None,
            "fieldnames": [],
            "rows": [],
            "row_count": 0,
            "score": 0,
            "parse_error": "unable_to_parse_csv",
            "first_lines": first_lines,
        }

    return best


def parse_xml_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "path": rel(path),
            "root_tag": "",
            "top_tags": {},
            "sample_leaf_tags": [],
            "parse_error": "file_not_found",
        }

    try:
        root = ET.parse(path).getroot()
        tag_counter: Counter[str] = Counter()
        leaf_tags: list[str] = []

        for elem in root.iter():
            tag = elem.tag.split("}")[-1]
            tag_counter[tag] += 1
            if len(elem) == 0 and elem.text and elem.text.strip():
                leaf_tags.append(tag)

        return {
            "exists": True,
            "path": rel(path),
            "root_tag": root.tag.split("}")[-1],
            "top_tags": dict(tag_counter.most_common(25)),
            "sample_leaf_tags": list(dict.fromkeys(leaf_tags[:50])),
            "parse_error": "",
        }
    except Exception as exc:
        return {
            "exists": True,
            "path": rel(path),
            "root_tag": "",
            "top_tags": {},
            "sample_leaf_tags": [],
            "parse_error": f"{type(exc).__name__}: {exc}",
        }


def find_field(fieldnames: list[str], candidates: list[str]) -> str | None:
    normalized_to_original = {normalize_header(f): f for f in fieldnames}

    for candidate in candidates:
        normalized_candidate = normalize_header(candidate)
        if normalized_candidate in normalized_to_original:
            return normalized_to_original[normalized_candidate]

    for original in fieldnames:
        norm = normalize_header(original)
        for candidate in candidates:
            if normalize_header(candidate) in norm:
                return original

    return None


def looks_like_ticker(value: str) -> bool:
    v = value.strip().upper()
    if not v:
        return False
    if len(v) > 12:
        return False
    if re.fullmatch(r"[A-Z0-9.\-_/]+", v) is None:
        return False
    if v in {"N/A", "NA", "NULL", "NONE"}:
        return False
    return True


def normalize_from_csv_parse(parse_result: dict[str, Any], route_id: str, source_file: Path) -> tuple[list[dict[str, str]], list[str], dict[str, str]]:
    warnings: list[str] = []
    rows: list[dict[str, str]] = parse_result.get("rows", [])
    fieldnames: list[str] = parse_result.get("fieldnames", [])

    symbol_field = find_field(
        fieldnames,
        [
            "symbol",
            "ticker",
            "security symbol",
            "cboe symbol",
            "product symbol",
            "root symbol",
            "underlying symbol",
        ],
    )

    name_field = find_field(
        fieldnames,
        [
            "name",
            "company name",
            "company",
            "security name",
            "issue name",
            "description",
            "product name",
        ],
    )

    exchange_field = find_field(
        fieldnames,
        [
            "exchange",
            "listing market",
            "primary listing market",
            "market",
            "listed exchange",
            "listing exchange",
        ],
    )

    type_field = find_field(
        fieldnames,
        [
            "type",
            "security type",
            "product type",
            "issue type",
            "asset class",
        ],
    )

    if not symbol_field:
        warnings.append(f"No symbol/ticker field detected for {rel(source_file)}")
        return [], warnings, {
            "symbol_field": "",
            "name_field": name_field or "",
            "exchange_field": exchange_field or "",
            "type_field": type_field or "",
        }

    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        raw_symbol = (row.get(symbol_field, "") or "").strip()
        ticker = raw_symbol.upper()

        if not looks_like_ticker(ticker):
            continue

        company_name = (row.get(name_field, "") if name_field else "").strip()
        raw_exchange = (row.get(exchange_field, "") if exchange_field else "").strip()
        raw_type = (row.get(type_field, "") if type_field else "").strip()

        exchange = raw_exchange or "CBOE"
        key = (exchange.upper(), ticker)

        if key in seen:
            continue
        seen.add(key)

        if "listed" in route_id:
            confidence = "MEDIUM"
            scope = "CANDIDATE_LISTED_SECURITY_PENDING_VALIDATION"
            reason = "Cboe listed-symbols route parsed with symbol field; requires net-new and semantic validation before rebuild."
        else:
            confidence = "LOW"
            scope = "REFERENCE_TRADED_SYMBOL_PENDING_VALIDATION"
            reason = "Cboe symbols-traded/secondary route parsed; may represent traded symbols or lot-size reference, not primary listing."

        normalized.append(
            {
                "ticker": ticker,
                "company_name": company_name,
                "exchange": exchange,
                "country": "USA",
                "source_provider": "cboe_listed_symbols",
                "source_file": rel(source_file),
                "instrument_type": raw_type or "UNKNOWN_PENDING_CLASSIFICATION",
                "instrument_scope": scope,
                "classification_confidence": confidence,
                "classification_reason": reason,
                "sector": "",
                "industry": "",
                "market_cap": "",
                "raw_symbol": raw_symbol,
                "raw_name": company_name,
                "raw_exchange": raw_exchange,
                "raw_listing_market": raw_exchange,
                "route_id": route_id,
            }
        )

    return normalized, warnings, {
        "symbol_field": symbol_field or "",
        "name_field": name_field or "",
        "exchange_field": exchange_field or "",
        "type_field": type_field or "",
    }


def load_existing_exchange_ticker_keys(path: Path) -> set[tuple[str, str]]:
    rows = read_csv_rows(path)
    keys: set[tuple[str, str]] = set()

    for row in rows:
        ticker = (row.get("ticker", "") or "").strip().upper()
        exchange = (row.get("exchange", "") or "").strip().upper()
        if ticker and exchange:
            keys.add((exchange, ticker))

    return keys


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    acquisition = read_json(ACQUISITION_JSON)

    if not acquisition.get("_exists"):
        blockers.append(f"Missing v2.8B acquisition artifact: {rel(ACQUISITION_JSON)}")
    else:
        positives.append(f"v2.8B acquisition artifact found: {rel(ACQUISITION_JSON)}")

    acquisition_status = acquisition.get("acquisition_status")
    if acquisition_status in {
        "CBOE_LISTED_SYMBOLS_ACQUISITION_COMPLETED_WITH_REVIEW_REQUIRED",
        "CBOE_LISTED_SYMBOLS_ACQUISITION_RAW_HTML_ONLY_REVIEW_REQUIRED",
    }:
        positives.append(f"v2.8B acquisition status accepted: {acquisition_status}")
    else:
        blockers.append(f"Unexpected v2.8B acquisition status: {acquisition_status}")

    required_files = [
        RAW_LISTED_CSV,
        RAW_LISTED_XML,
        RAW_SYMBOLS_TRADED_CSV,
        RAW_SYMBOLS_TRADED_XML,
        DISCOVERED_LINKS_CSV,
        SCHEMA_PROBE_CSV,
        EXPANDED_CSV,
    ]

    for path in required_files:
        if path.exists():
            positives.append(f"Required validation input available: {rel(path)}")
        else:
            blockers.append(f"Missing validation input: {rel(path)}")

    listed_csv_parse = parse_csv_with_best_header(RAW_LISTED_CSV)
    symbols_traded_csv_parse = parse_csv_with_best_header(RAW_SYMBOLS_TRADED_CSV)

    listed_xml_summary = parse_xml_summary(RAW_LISTED_XML)
    symbols_traded_xml_summary = parse_xml_summary(RAW_SYMBOLS_TRADED_XML)

    schema_rows: list[dict[str, Any]] = []

    csv_parse_map = [
        ("cboe_us_equities_listed_symbols", RAW_LISTED_CSV, listed_csv_parse),
        ("cboe_us_equities_symbols_traded_downloaded", RAW_SYMBOLS_TRADED_CSV, symbols_traded_csv_parse),
    ]

    normalized_all: list[dict[str, str]] = []
    detected_fields_by_route: dict[str, dict[str, str]] = {}

    for route_id, path, parse_result in csv_parse_map:
        fields = parse_result.get("fieldnames", [])
        rows = parse_result.get("rows", [])

        normalized, route_warnings, detected_fields = normalize_from_csv_parse(parse_result, route_id, path)
        warnings.extend(route_warnings)
        detected_fields_by_route[route_id] = detected_fields

        if normalized:
            positives.append(f"{route_id} normalized candidate rows: {len(normalized)}")
            normalized_all.extend(normalized)

        schema_rows.append(
            {
                "route_id": route_id,
                "file_type": "csv",
                "path": rel(path),
                "exists": str(parse_result.get("exists")),
                "best_header_line": parse_result.get("best_header_line"),
                "row_count": parse_result.get("row_count"),
                "score": parse_result.get("score"),
                "parse_error": parse_result.get("parse_error"),
                "field_count": len(fields),
                "fieldnames": "|".join(fields),
                "symbol_field": detected_fields.get("symbol_field", ""),
                "name_field": detected_fields.get("name_field", ""),
                "exchange_field": detected_fields.get("exchange_field", ""),
                "type_field": detected_fields.get("type_field", ""),
                "first_lines": " || ".join(parse_result.get("first_lines", [])[:5]),
            }
        )

    xml_summaries = [
        ("cboe_us_equities_listed_symbols", RAW_LISTED_XML, listed_xml_summary),
        ("cboe_us_equities_symbols_traded_downloaded", RAW_SYMBOLS_TRADED_XML, symbols_traded_xml_summary),
    ]

    for route_id, path, summary in xml_summaries:
        schema_rows.append(
            {
                "route_id": route_id,
                "file_type": "xml",
                "path": rel(path),
                "exists": str(summary.get("exists")),
                "best_header_line": "",
                "row_count": "",
                "score": "",
                "parse_error": summary.get("parse_error"),
                "field_count": len(summary.get("sample_leaf_tags", [])),
                "fieldnames": "|".join(summary.get("sample_leaf_tags", [])),
                "symbol_field": "",
                "name_field": "",
                "exchange_field": "",
                "type_field": "",
                "first_lines": f"root={summary.get('root_tag')}; top_tags={summary.get('top_tags')}",
            }
        )

    write_csv(
        OUT_SCHEMA_DETAIL_CSV,
        schema_rows,
        [
            "route_id",
            "file_type",
            "path",
            "exists",
            "best_header_line",
            "row_count",
            "score",
            "parse_error",
            "field_count",
            "fieldnames",
            "symbol_field",
            "name_field",
            "exchange_field",
            "type_field",
            "first_lines",
        ],
    )

    existing_keys = load_existing_exchange_ticker_keys(EXPANDED_CSV)
    if not existing_keys:
        warnings.append("No existing exchange+ticker keys loaded from expanded_universe_v2_7b.csv.")

    normalized_unique: list[dict[str, str]] = []
    seen_norm: set[tuple[str, str]] = set()

    for row in normalized_all:
        key = ((row.get("exchange") or "").strip().upper(), (row.get("ticker") or "").strip().upper())
        if not key[0] or not key[1]:
            continue
        if key in seen_norm:
            continue
        seen_norm.add(key)
        normalized_unique.append(row)

    net_new_rows: list[dict[str, str]] = []

    for row in normalized_unique:
        key = ((row.get("exchange") or "").strip().upper(), (row.get("ticker") or "").strip().upper())
        if key not in existing_keys:
            net_new_rows.append(row)

    if normalized_unique:
        write_csv(OUT_NORMALIZED_CANDIDATE_CSV, normalized_unique, NORMALIZED_COLUMNS)
        write_csv(OUT_SAMPLE_CSV, normalized_unique[:50], NORMALIZED_COLUMNS)
        positives.append(f"Normalized candidate CSV written: {rel(OUT_NORMALIZED_CANDIDATE_CSV)}")
    else:
        warnings.append("No normalized candidate rows produced from Cboe CSVs.")

    if net_new_rows:
        write_csv(OUT_NET_NEW_CSV, net_new_rows, NORMALIZED_COLUMNS)
        positives.append(f"Net-new candidate CSV written: {rel(OUT_NET_NEW_CSV)}")
    else:
        warnings.append("No net-new Cboe rows calculated; either no normalized rows or all overlap.")

    listed_rows = len(listed_csv_parse.get("rows", []))
    symbols_traded_rows = len(symbols_traded_csv_parse.get("rows", []))
    normalized_rows = len(normalized_unique)
    net_new_count = len(net_new_rows)

    discovered_links = read_csv_rows(DISCOVERED_LINKS_CSV)
    proper_symbols_traded_links = [
        row for row in discovered_links
        if "symbols_traded" in (row.get("url", "") or "").lower()
        and (row.get("file_type", "") or "").lower() == "csv"
    ]

    downloaded_symbols_traded_url = ""
    try:
        for item in acquisition.get("candidate_downloads", []):
            if item.get("route_id") == "cboe_us_equities_symbols_traded_edgx" and item.get("file_type") == "csv":
                downloaded_symbols_traded_url = item.get("url", "")
                break
    except Exception:
        downloaded_symbols_traded_url = ""

    if downloaded_symbols_traded_url and "lot_size" in downloaded_symbols_traded_url.lower():
        warnings.append("v2.8B downloaded Cboe lot-size CSV into symbols_traded slot before the real symbols_traded CSV. v2.8D/v2.8B2 may need corrected download priority.")

    if proper_symbols_traded_links:
        positives.append(f"Discovered proper symbols_traded CSV link candidates: {len(proper_symbols_traded_links)}")

    if normalized_rows > 0 and net_new_count > 0:
        validation_status = "CBOE_VALIDATED_WITH_NET_NEW_CANDIDATES"
        readiness_score = 85
        cboe_decision = "CBOE_USABLE_AS_CANDIDATE_PROVIDER_PENDING_REBUILD_PLAN"
        recommended_next_phase = "v2.8D ? Rebuild Expanded Source With Cboe Plan"
    elif normalized_rows > 0 and net_new_count == 0:
        validation_status = "CBOE_VALIDATED_REFERENCE_OR_OVERLAP_ONLY"
        readiness_score = 75
        cboe_decision = "CBOE_REFERENCE_OR_OVERLAP_ONLY"
        recommended_next_phase = "v2.8D ? Cboe Closure Or Corrected Symbols Traded Acquisition"
    elif not blockers:
        validation_status = "CBOE_VALIDATION_SCHEMA_REVIEW_REQUIRED"
        readiness_score = 65
        cboe_decision = "CBOE_DEFERRED_SCHEMA_REVIEW_REQUIRED"
        recommended_next_phase = "v2.8D ? Correct Cboe Download Priority Or Close Cboe As Review Required"
    else:
        validation_status = "CBOE_VALIDATION_BLOCKED"
        readiness_score = 0
        cboe_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "cboe_decision": cboe_decision,
        "recommended_next_phase": recommended_next_phase,
        "inputs": {
            "acquisition_json": rel(ACQUISITION_JSON),
            "discovered_links_csv": rel(DISCOVERED_LINKS_CSV),
            "schema_probe_csv": rel(SCHEMA_PROBE_CSV),
            "expanded_csv": rel(EXPANDED_CSV),
            "raw_listed_csv": rel(RAW_LISTED_CSV),
            "raw_listed_xml": rel(RAW_LISTED_XML),
            "raw_symbols_traded_csv": rel(RAW_SYMBOLS_TRADED_CSV),
            "raw_symbols_traded_xml": rel(RAW_SYMBOLS_TRADED_XML),
        },
        "schema_summary": {
            "listed_csv_rows": listed_rows,
            "listed_csv_fields": listed_csv_parse.get("fieldnames", []),
            "listed_csv_best_header_line": listed_csv_parse.get("best_header_line"),
            "listed_detected_fields": detected_fields_by_route.get("cboe_us_equities_listed_symbols", {}),
            "symbols_traded_csv_rows": symbols_traded_rows,
            "symbols_traded_csv_fields": symbols_traded_csv_parse.get("fieldnames", []),
            "symbols_traded_csv_best_header_line": symbols_traded_csv_parse.get("best_header_line"),
            "symbols_traded_detected_fields": detected_fields_by_route.get("cboe_us_equities_symbols_traded_downloaded", {}),
            "listed_xml_root": listed_xml_summary.get("root_tag"),
            "symbols_traded_xml_root": symbols_traded_xml_summary.get("root_tag"),
        },
        "coverage_summary": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "existing_exchange_ticker_keys": len(existing_keys),
            "normalized_candidate_rows": normalized_rows,
            "net_new_exchange_ticker_rows": net_new_count,
            "projected_rows_if_added": CURRENT_EXPANDED_ROWS + net_new_count,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "first_expansion_unlocked_if_added": (CURRENT_EXPANDED_ROWS + net_new_count) >= TARGET_FIRST_EXPANSION_ROWS,
            "full_source_unlocked_if_added": (CURRENT_EXPANDED_ROWS + net_new_count) >= MIN_FULL_SOURCE_ROWS,
        },
        "download_review": {
            "downloaded_symbols_traded_url": downloaded_symbols_traded_url,
            "proper_symbols_traded_csv_link_candidates": proper_symbols_traded_links,
        },
        "outputs": {
            "schema_detail_csv": rel(OUT_SCHEMA_DETAIL_CSV),
            "normalized_candidate_csv": rel(OUT_NORMALIZED_CANDIDATE_CSV) if OUT_NORMALIZED_CANDIDATE_CSV.exists() else None,
            "net_new_candidates_csv": rel(OUT_NET_NEW_CSV) if OUT_NET_NEW_CSV.exists() else None,
            "sample_csv": rel(OUT_SAMPLE_CSV) if OUT_SAMPLE_CSV.exists() else None,
        },
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "network_download_performed": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
            "validation_only": True,
        },
        "recommendation": (
            "Use v2.8D to plan rebuild only if net-new candidates are meaningful; otherwise correct Cboe download priority or close Cboe as reference/review-required."
            if not blockers
            else "Resolve blockers before Cboe decision."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.8C Cboe Listed Symbols Validation")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Cboe decision: **{cboe_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Schema summary")
    md.append("")
    md.append(f"- Listed CSV rows: {listed_rows}")
    md.append(f"- Listed CSV best header line: {listed_csv_parse.get('best_header_line')}")
    md.append(f"- Listed CSV fields: `{', '.join(listed_csv_parse.get('fieldnames', []))}`")
    md.append(f"- Listed detected fields: `{detected_fields_by_route.get('cboe_us_equities_listed_symbols', {})}`")
    md.append("")
    md.append(f"- Symbols traded/downloaded CSV rows: {symbols_traded_rows}")
    md.append(f"- Symbols traded/downloaded CSV best header line: {symbols_traded_csv_parse.get('best_header_line')}")
    md.append(f"- Symbols traded/downloaded CSV fields: `{', '.join(symbols_traded_csv_parse.get('fieldnames', []))}`")
    md.append(f"- Symbols traded/downloaded detected fields: `{detected_fields_by_route.get('cboe_us_equities_symbols_traded_downloaded', {})}`")
    md.append("")
    md.append(f"- Listed XML root: `{listed_xml_summary.get('root_tag')}`")
    md.append(f"- Symbols traded XML root: `{symbols_traded_xml_summary.get('root_tag')}`")
    md.append("")
    md.append("## Coverage summary")
    md.append("")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Existing exchange+ticker keys loaded: {len(existing_keys)}")
    md.append(f"- Normalized candidate rows: {normalized_rows}")
    md.append(f"- Net-new exchange+ticker rows: {net_new_count}")
    md.append(f"- Projected rows if added: {CURRENT_EXPANDED_ROWS + net_new_count}")
    md.append(f"- First expansion unlocked if added: {(CURRENT_EXPANDED_ROWS + net_new_count) >= TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Full source unlocked if added: {(CURRENT_EXPANDED_ROWS + net_new_count) >= MIN_FULL_SOURCE_ROWS}")
    md.append("")
    md.append("## Download review")
    md.append("")
    md.append(f"- Downloaded symbols_traded CSV URL: `{downloaded_symbols_traded_url}`")
    md.append(f"- Proper symbols_traded CSV link candidates discovered: {len(proper_symbols_traded_links)}")
    for row in proper_symbols_traded_links[:5]:
        md.append(f"  - `{row.get('url')}`")
    md.append("")
    md.append("## Outputs")
    md.append("")
    for key, value in payload["outputs"].items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Network download performed: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("- Validation only: true")
    md.append("")
    md.append("## Positives")
    md.append("")
    if positives:
        for item in positives:
            md.append(f"- {item}")
    else:
        md.append("- No positives detected.")
    md.append("")
    md.append("## Blockers")
    md.append("")
    if blockers:
        for item in blockers:
            md.append(f"- {item}")
    else:
        md.append("- No blockers detected.")
    md.append("")
    md.append("## Warnings")
    md.append("")
    if warnings:
        for item in warnings:
            md.append(f"- {item}")
    else:
        md.append("- No warnings detected.")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.8C is validation-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.8C Cboe Listed Symbols Validation")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Cboe decision: {cboe_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Listed CSV rows: {listed_rows}")
    print(f"OK   Listed CSV fields: {len(listed_csv_parse.get('fieldnames', []))}")
    print(f"OK   Symbols traded/downloaded CSV rows: {symbols_traded_rows}")
    print(f"OK   Symbols traded/downloaded CSV fields: {len(symbols_traded_csv_parse.get('fieldnames', []))}")
    print(f"OK   Normalized candidate rows: {normalized_rows}")
    print(f"OK   Net-new exchange+ticker rows: {net_new_count}")
    print(f"OK   Projected rows if added: {CURRENT_EXPANDED_ROWS + net_new_count}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Schema detail written: {OUT_SCHEMA_DETAIL_CSV}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
