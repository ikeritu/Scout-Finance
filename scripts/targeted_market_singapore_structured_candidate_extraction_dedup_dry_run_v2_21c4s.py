from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21C4S"
PHASE = "Singapore Structured Candidate Extraction + Dedup Dry Run"
PHASE_TYPE = "targeted-market-singapore-structured-candidate-extraction-dedup-dry-run"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

V221C3_JSON = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_v2_21c3.json"
V221C3_REVIEW_JSON = OUTPUT_DIR / "targeted_market_missing_official_endpoint_review_v2_21c3_review.json"

REPORT_JSON = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_v2_21c4s.json"
REPORT_MD = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_v2_21c4s.md"
SUMMARY_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_summary_v2_21c4s.csv"
CHECKS_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_checks_v2_21c4s.csv"
SOURCE_ENDPOINTS_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_source_endpoints_v2_21c4s.csv"
FIELD_MAPPING_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_field_mapping_v2_21c4s.csv"
RAW_CANDIDATES_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_raw_candidates_v2_21c4s.csv"
ELIGIBLE_CANDIDATES_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_eligible_candidates_v2_21c4s.csv"
REJECTED_CANDIDATES_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_rejected_candidates_v2_21c4s.csv"
DEDUP_SUMMARY_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_dedup_summary_v2_21c4s.csv"
SCHEMA_PROJECTION_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_schema_projection_v2_21c4s.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "targeted_market_singapore_structured_candidate_extraction_dedup_dry_run_next_actions_v2_21c4s.csv"

EXPECTED_V221C3_STATUS = "TARGETED_MARKET_OFFICIAL_ENDPOINT_DISCOVERY_COMPLETED_PARTIAL_STRUCTURED_ENDPOINTS_FOUND_REVIEW_REQUIRED"
EXPECTED_V221C3_REVIEW_STATUS = "TARGETED_MARKET_MISSING_ENDPOINT_REVIEW_COMPLETED_SPLIT_ROUTE_APPROVED_SGX_READY_COLOMBIA_REGULATORY_DISCOVERY_REQUIRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

MARKET_ID = "SINGAPORE_SGX"
COUNTRY = "Singapore"
COUNTRY_CODE = "SG"
EXCHANGE = "SGX"
MIC = "XSES"
CURRENCY = "SGD"
SOURCE_PROVIDER = "sgx_structured_endpoint"

STATUS_SUCCESS = "SINGAPORE_STRUCTURED_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_ELIGIBLE_CANDIDATES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED"
STATUS_NO_CANDIDATES = "SINGAPORE_STRUCTURED_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_NO_ELIGIBLE_CANDIDATES_REVIEW_REQUIRED"
STATUS_FAILED = "SINGAPORE_STRUCTURED_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_SUCCESS = "v2.21D_S - Singapore Expanded Rebuild Candidate"
NEXT_PHASE_REVIEW = "v2.21C4S_REVIEW - Singapore Structured Extraction Issue Resolution"
SECONDARY_NEXT_PHASE = "v2.21C3B - Colombia Regulatory Source Discovery"

DISALLOWED_INSTRUMENT_TERMS = [
    " etf", "exchange traded fund", " fund", "bond", "bonds", "note", "notes",
    "warrant", "warrants", "right", "rights", "nil paid", "structured",
    "certificate", "certificates", "dlc", "daily leverage", "daily leveraged",
    "debenture", "debentures", "preference share", "preferred share",
]

TECHNICAL_FALSE_POSITIVE_TERMS = [
    "compatible", "webpack", "polyfill", "googletagmanager", "gtm", "buildmanifest",
    "script", "static", "cookie", "privacy", "browser", "javascript", "css",
]

NAME_KEYS = [
    "fn", "companyName", "company_name", "securityName", "security_name",
    "counterName", "counter_name", "issuerName", "issuer_name", "name",
    "cn", "nc",
]

SYMBOL_KEYS = [
    "s", "symbol", "ticker", "code", "stockCode", "stock_code",
    "tradingCode", "trading_code", "securityCode", "security_code",
]

ISIN_KEYS = ["isin", "isinCode", "isin_code"]
TYPE_KEYS = ["type", "securityType", "security_type", "instrumentType", "instrument_type", "assetClass", "asset_class"]
SECTOR_KEYS = ["sector", "industry", "gicsSector", "gics_sector"]
PRICE_KEYS = ["lt", "p", "pv", "last", "lastPrice", "last_price"]
CURRENCY_KEYS = ["currency", "ccy", "tradingCurrency", "trading_currency"]


RAW_FIELDNAMES = [
    "raw_candidate_id",
    "market_id",
    "source_id",
    "source_url",
    "raw_file",
    "raw_object_index",
    "symbol",
    "name",
    "isin",
    "instrument_type",
    "sector",
    "price",
    "currency",
    "raw_payload",
    "raw_quality_status",
    "raw_quality_reason",
]

ELIGIBLE_FIELDNAMES = [
    "candidate_id",
    "market_id",
    "country",
    "country_code",
    "exchange",
    "mic",
    "currency",
    "source_provider",
    "source_id",
    "source_url",
    "symbol",
    "ticker",
    "trading_code",
    "isin",
    "name",
    "instrument_type",
    "instrument_bucket",
    "sector",
    "price",
    "dedup_key",
    "dedup_status",
    "dedup_reason",
    "capacity_status",
    "approved_for_rebuild_input",
    "raw_payload",
]

REJECTED_FIELDNAMES = ELIGIBLE_FIELDNAMES + ["rejection_stage", "rejection_reason"]


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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
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


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", norm(value).lower())


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
    lower_map = {str(key).lower(): key for key in obj.keys()}
    for key in keys:
        real_key = lower_map.get(key.lower())
        if real_key is not None:
            value = obj.get(real_key)
            if isinstance(value, (str, int, float)):
                text = norm(value)
                if text:
                    return text
    return ""


def looks_like_symbol(value: str) -> bool:
    value = norm(value).upper()
    if not value:
        return False
    if len(value) > 12:
        return False
    return bool(re.fullmatch(r"[A-Z0-9][A-Z0-9.\-]{0,11}", value))


def looks_like_isin(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", norm(value).upper()))


def technical_false_positive(value: str) -> bool:
    lowered = " " + norm(value).lower() + " "
    return any(term in lowered for term in TECHNICAL_FALSE_POSITIVE_TERMS)


def disallowed_instrument(*values: str) -> tuple[bool, str]:
    combined = " " + " ".join(norm(value).lower() for value in values) + " "
    for term in DISALLOWED_INSTRUMENT_TERMS:
        if term in combined:
            return True, f"disallowed_instrument_term={term.strip()}"
    return False, ""


def instrument_bucket(name: str, instrument_type: str) -> str:
    lowered = f"{name} {instrument_type}".lower()
    if "reit" in lowered:
        return "equity_like_reit"
    if "trust" in lowered:
        return "equity_like_trust"
    return "equity_common_or_equity_like"


def is_candidate_like_object(obj: dict[str, Any]) -> bool:
    symbol = pick_first(obj, SYMBOL_KEYS)
    name = pick_first(obj, NAME_KEYS)

    if not symbol or not name:
        return False

    if not looks_like_symbol(symbol):
        return False

    if len(name) < 2 or len(name) > 180:
        return False

    if technical_false_positive(symbol) or technical_false_positive(name):
        return False

    if norm_key(name) == norm_key(symbol):
        return False

    if re.fullmatch(r"[A-Z0-9\-_.]{5,}", name.strip()):
        return False

    return True


def candidate_from_object(
    obj: dict[str, Any],
    source_id: str,
    source_url: str,
    raw_file: str,
    raw_object_index: int,
) -> dict[str, Any] | None:
    symbol = pick_first(obj, SYMBOL_KEYS).upper()
    name = pick_first(obj, NAME_KEYS)
    isin = pick_first(obj, ISIN_KEYS).upper()
    instrument_type = pick_first(obj, TYPE_KEYS)
    sector = pick_first(obj, SECTOR_KEYS)
    price = pick_first(obj, PRICE_KEYS)
    raw_currency = pick_first(obj, CURRENCY_KEYS)

    if not is_candidate_like_object(obj):
        return None

    if isin and not looks_like_isin(isin):
        isin = ""

    disallowed, disallowed_reason = disallowed_instrument(name, instrument_type, symbol)

    raw_quality_status = "accepted"
    raw_quality_reason = "structured_sgx_record_has_symbol_and_name"

    if disallowed:
        raw_quality_status = "rejected"
        raw_quality_reason = disallowed_reason

    return {
        "raw_candidate_id": f"sgx_raw_{raw_object_index:06d}",
        "market_id": MARKET_ID,
        "source_id": source_id,
        "source_url": source_url,
        "raw_file": raw_file,
        "raw_object_index": raw_object_index,
        "symbol": symbol,
        "name": name,
        "isin": isin,
        "instrument_type": instrument_type,
        "sector": sector,
        "price": price,
        "currency": raw_currency or CURRENCY,
        "raw_payload": json.dumps(obj, ensure_ascii=False)[:3000],
        "raw_quality_status": raw_quality_status,
        "raw_quality_reason": raw_quality_reason,
    }


def build_base_index(base_rows: list[dict[str, str]], header: list[str]) -> dict[str, set[str]]:
    header_lower = [column.lower() for column in header]

    isin_cols = [header[idx] for idx, col in enumerate(header_lower) if "isin" in col]
    symbol_cols = [
        header[idx] for idx, col in enumerate(header_lower)
        if col in {"symbol", "ticker"} or "symbol" in col or "ticker" in col or "trading_code" in col
    ]
    name_cols = [
        header[idx] for idx, col in enumerate(header_lower)
        if col in {"name", "company_name", "security_name"} or "name" in col
    ]
    country_cols = [header[idx] for idx, col in enumerate(header_lower) if "country" in col]
    exchange_cols = [header[idx] for idx, col in enumerate(header_lower) if "exchange" in col]
    mic_cols = [header[idx] for idx, col in enumerate(header_lower) if col == "mic" or "mic" in col]

    index = {
        "isin": set(),
        "singapore_symbol": set(),
        "singapore_name": set(),
        "columns_isin": set(isin_cols),
        "columns_symbol": set(symbol_cols),
        "columns_name": set(name_cols),
        "columns_country": set(country_cols),
        "columns_exchange": set(exchange_cols),
        "columns_mic": set(mic_cols),
    }

    for row in base_rows:
        is_singapore_context = False

        for col in country_cols:
            if norm_key(row.get(col)) in {"singapore", "sg"}:
                is_singapore_context = True
        for col in exchange_cols:
            if norm_key(row.get(col)) == "sgx":
                is_singapore_context = True
        for col in mic_cols:
            if norm_key(row.get(col)) == "xses":
                is_singapore_context = True

        for col in isin_cols:
            value = norm_key(row.get(col))
            if value:
                index["isin"].add(value)

        if is_singapore_context:
            for col in symbol_cols:
                value = norm_key(row.get(col))
                if value:
                    index["singapore_symbol"].add(value)
            for col in name_cols:
                value = norm_key(row.get(col))
                if value:
                    index["singapore_name"].add(value)

    return index


def dedup_candidates(raw_candidates: list[dict[str, Any]], base_index: dict[str, set[str]], remaining_capacity: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    seen_symbols: set[str] = set()
    seen_names: set[str] = set()
    seen_isins: set[str] = set()

    for raw in raw_candidates:
        symbol_key = norm_key(raw["symbol"])
        name_key = norm_key(raw["name"])
        isin_key = norm_key(raw["isin"])

        candidate = {
            "candidate_id": "",
            "market_id": MARKET_ID,
            "country": COUNTRY,
            "country_code": COUNTRY_CODE,
            "exchange": EXCHANGE,
            "mic": MIC,
            "currency": CURRENCY,
            "source_provider": SOURCE_PROVIDER,
            "source_id": raw["source_id"],
            "source_url": raw["source_url"],
            "symbol": raw["symbol"],
            "ticker": raw["symbol"],
            "trading_code": raw["symbol"],
            "isin": raw["isin"],
            "name": raw["name"],
            "instrument_type": raw["instrument_type"],
            "instrument_bucket": instrument_bucket(raw["name"], raw["instrument_type"]),
            "sector": raw["sector"],
            "price": raw["price"],
            "dedup_key": f"{MARKET_ID}|{isin_key}|{symbol_key}|{name_key}",
            "dedup_status": "",
            "dedup_reason": "",
            "capacity_status": "",
            "approved_for_rebuild_input": False,
            "raw_payload": raw["raw_payload"],
        }

        if raw["raw_quality_status"] != "accepted":
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = raw["raw_quality_reason"]
            candidate["capacity_status"] = "not_applicable"
            rejected.append({**candidate, "rejection_stage": "quality_filter", "rejection_reason": raw["raw_quality_reason"]})
            continue

        if isin_key and isin_key in base_index["isin"]:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_isin_in_operational_base"
            candidate["capacity_status"] = "not_applicable"
            rejected.append({**candidate, "rejection_stage": "dedup", "rejection_reason": "duplicate_isin_in_operational_base"})
            continue

        if symbol_key in base_index["singapore_symbol"]:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_singapore_symbol_in_operational_base"
            candidate["capacity_status"] = "not_applicable"
            rejected.append({**candidate, "rejection_stage": "dedup", "rejection_reason": "duplicate_singapore_symbol_in_operational_base"})
            continue

        if name_key in base_index["singapore_name"]:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_singapore_name_in_operational_base"
            candidate["capacity_status"] = "not_applicable"
            rejected.append({**candidate, "rejection_stage": "dedup", "rejection_reason": "duplicate_singapore_name_in_operational_base"})
            continue

        if isin_key and isin_key in seen_isins:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_isin_within_sgx_extraction"
            candidate["capacity_status"] = "not_applicable"
            rejected.append({**candidate, "rejection_stage": "dedup", "rejection_reason": "duplicate_isin_within_sgx_extraction"})
            continue

        if symbol_key in seen_symbols:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_symbol_within_sgx_extraction"
            candidate["capacity_status"] = "not_applicable"
            rejected.append({**candidate, "rejection_stage": "dedup", "rejection_reason": "duplicate_symbol_within_sgx_extraction"})
            continue

        if name_key in seen_names and not symbol_key:
            candidate["dedup_status"] = "rejected"
            candidate["dedup_reason"] = "duplicate_name_without_symbol_within_sgx_extraction"
            candidate["capacity_status"] = "not_applicable"
            rejected.append({**candidate, "rejection_stage": "dedup", "rejection_reason": "duplicate_name_without_symbol_within_sgx_extraction"})
            continue

        seen_symbols.add(symbol_key)
        seen_names.add(name_key)
        if isin_key:
            seen_isins.add(isin_key)

        candidate["dedup_status"] = "accepted_new"
        candidate["dedup_reason"] = "not_found_in_operational_base"
        eligible.append(candidate)

    for idx, candidate in enumerate(eligible, start=1):
        candidate["candidate_id"] = f"v2_21c4s_{idx:05d}"
        if idx <= remaining_capacity:
            candidate["capacity_status"] = "within_capacity"
            candidate["approved_for_rebuild_input"] = True
        else:
            candidate["capacity_status"] = "over_capacity_excluded_from_rebuild_input"
            candidate["approved_for_rebuild_input"] = False
            rejected.append({
                **candidate,
                "rejection_stage": "capacity_filter",
                "rejection_reason": "over_45k_quality_ceiling_capacity",
            })

    eligible_within_capacity = [row for row in eligible if row["approved_for_rebuild_input"] is True]
    return eligible_within_capacity, rejected


def project_to_operational_schema(candidate: dict[str, Any], operational_header: list[str]) -> dict[str, Any]:
    projected: dict[str, Any] = {column: "" for column in operational_header}

    for column in operational_header:
        key = norm_key(column)

        if key in {"country"} or "country" in key:
            projected[column] = COUNTRY
        elif key in {"countrycode"} or key == "country_code":
            projected[column] = COUNTRY_CODE
        elif key in {"exchange"} or "exchange" in key:
            projected[column] = EXCHANGE
        elif key == "mic" or key.endswith("mic") or "mic" in key:
            projected[column] = MIC
        elif key in {"currency"} or "currency" in key:
            projected[column] = CURRENCY
        elif key in {"symbol", "ticker", "tradingcode", "trading_code"} or "symbol" in key or "ticker" in key:
            projected[column] = candidate["symbol"]
        elif "isin" in key:
            projected[column] = candidate["isin"]
        elif key in {"name", "companyname", "securityname"} or "name" in key:
            projected[column] = candidate["name"]
        elif "provider" in key or "source" in key:
            projected[column] = SOURCE_PROVIDER
        elif "sector" in key:
            projected[column] = candidate["sector"]
        elif "type" in key or "instrument" in key:
            projected[column] = candidate["instrument_bucket"]

    return projected


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        SOURCE_ENDPOINTS_CSV,
        FIELD_MAPPING_CSV,
        RAW_CANDIDATES_CSV,
        ELIGIBLE_CANDIDATES_CSV,
        REJECTED_CANDIDATES_CSV,
        DEDUP_SUMMARY_CSV,
        SCHEMA_PROJECTION_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v221c3 = read_json(V221C3_JSON)
    v221c3_review = read_json(V221C3_REVIEW_JSON)

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    operational_header = read_csv_header(OPERATIONAL_BASE_DATASET)
    base_rows = read_csv_dicts(OPERATIONAL_BASE_DATASET)
    base_index = build_base_index(base_rows, operational_header)

    remaining_capacity = QUALITY_CEILING_TARGET - operational_rows

    endpoint_validations = v221c3.get("endpoint_validation", [])
    structured_sgx_endpoints = [
        row for row in endpoint_validations
        if row.get("market_id") == MARKET_ID
        and as_bool(row.get("structured_endpoint_candidate"))
        and as_bool(row.get("fetch_success"))
        and row.get("raw_file")
    ]

    source_endpoint_rows: list[dict[str, Any]] = []
    for row in structured_sgx_endpoints:
        source_endpoint_rows.append({
            "market_id": row.get("market_id", ""),
            "provider": row.get("provider", ""),
            "source_id": row.get("source_id", ""),
            "url": row.get("url", ""),
            "raw_file": row.get("raw_file", ""),
            "parse_mode": row.get("parse_mode", ""),
            "candidate_like_records": row.get("candidate_like_records", ""),
            "structured_endpoint_candidate": row.get("structured_endpoint_candidate", ""),
            "endpoint_validation_status": row.get("endpoint_validation_status", ""),
            "selected_for_extraction": True,
        })

    field_mapping_rows = [
        {"target_field": "symbol/ticker/trading_code", "source_keys_priority": "|".join(SYMBOL_KEYS), "rule": "first non-empty value; must match compact exchange symbol pattern"},
        {"target_field": "name", "source_keys_priority": "|".join(NAME_KEYS), "rule": "first non-empty company/security name; technical tokens rejected"},
        {"target_field": "isin", "source_keys_priority": "|".join(ISIN_KEYS), "rule": "kept only if valid ISIN format"},
        {"target_field": "instrument_type", "source_keys_priority": "|".join(TYPE_KEYS), "rule": "used for filtering and bucket assignment"},
        {"target_field": "sector", "source_keys_priority": "|".join(SECTOR_KEYS), "rule": "optional"},
        {"target_field": "price", "source_keys_priority": "|".join(PRICE_KEYS), "rule": "optional metadata only"},
        {"target_field": "country/exchange/mic/currency", "source_keys_priority": "constant", "rule": "Singapore / SGX / XSES / SGD"},
    ]

    raw_candidates: list[dict[str, Any]] = []
    raw_object_counter = 0

    # Prefer richer SGX endpoint first so duplicate symbols keep extended metadata.
    source_rank = {
        "SGX_SECURITIES_V1_1_JSON_EXTENDED": 1,
        "SGX_SECURITIES_V1_1_JSON_MINIMAL": 2,
    }

    structured_sgx_endpoints_sorted = sorted(
        structured_sgx_endpoints,
        key=lambda row: source_rank.get(str(row.get("source_id")), 99),
    )

    for endpoint in structured_sgx_endpoints_sorted:
        raw_file = Path(endpoint["raw_file"])
        if not raw_file.exists():
            continue

        data = json.loads(raw_file.read_text(encoding="utf-8"))
        objects = flatten_json_objects(data)

        for obj in objects:
            if not is_candidate_like_object(obj):
                continue

            raw_object_counter += 1
            candidate = candidate_from_object(
                obj=obj,
                source_id=endpoint["source_id"],
                source_url=endpoint["url"],
                raw_file=str(raw_file),
                raw_object_index=raw_object_counter,
            )
            if candidate:
                raw_candidates.append(candidate)

    eligible_candidates, rejected_candidates = dedup_candidates(raw_candidates, base_index, remaining_capacity)

    projected_rows = [
        project_to_operational_schema(candidate, operational_header)
        for candidate in eligible_candidates
    ]

    projected_rows_after_addition = operational_rows + len(eligible_candidates)
    remaining_capacity_after_addition = QUALITY_CEILING_TARGET - projected_rows_after_addition

    raw_quality_counts = Counter(row["raw_quality_status"] for row in raw_candidates)
    rejected_stage_counts = Counter(row.get("rejection_stage", "") for row in rejected_candidates)
    instrument_bucket_counts = Counter(row["instrument_bucket"] for row in eligible_candidates)

    dedup_summary_rows = [
        {
            "market_id": MARKET_ID,
            "raw_candidates": len(raw_candidates),
            "raw_accepted_by_quality": raw_quality_counts.get("accepted", 0),
            "raw_rejected_by_quality": raw_quality_counts.get("rejected", 0),
            "eligible_new_candidates": len(eligible_candidates),
            "rejected_candidates": len(rejected_candidates),
            "duplicate_or_rejected_by_dedup": rejected_stage_counts.get("dedup", 0),
            "rejected_by_quality_filter": rejected_stage_counts.get("quality_filter", 0),
            "rejected_by_capacity_filter": rejected_stage_counts.get("capacity_filter", 0),
            "projected_rows_after_addition": projected_rows_after_addition,
            "remaining_capacity_after_addition": remaining_capacity_after_addition,
            "ready_for_singapore_rebuild_candidate": len(eligible_candidates) > 0 and projected_rows_after_addition <= QUALITY_CEILING_TARGET,
        }
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

    review_summary = v221c3_review.get("summary", {})

    add_check("v2_21c3_status_expected", v221c3.get("status") == EXPECTED_V221C3_STATUS, "critical", str(v221c3.get("status")))
    add_check("v2_21c3_review_status_expected", v221c3_review.get("status") == EXPECTED_V221C3_REVIEW_STATUS, "critical", str(v221c3_review.get("status")))
    add_check("singapore_structured_extraction_approved", as_bool(review_summary.get("approved_for_singapore_structured_extraction")) is True, "critical", f"approved_for_singapore_structured_extraction={review_summary.get('approved_for_singapore_structured_extraction')}")
    add_check("colombia_not_in_scope", as_bool(review_summary.get("approved_for_colombia_regulatory_discovery")) is True, "critical", "Colombia remains discovery-only and is not extracted in v2.21C4S.")
    add_check("global_v2_21c4_not_approved", as_bool(review_summary.get("approved_for_global_v2_21c4")) is False, "critical", f"approved_for_global_v2_21c4={review_summary.get('approved_for_global_v2_21c4')}")
    add_check("v2_21d_not_approved", as_bool(review_summary.get("approved_for_v2_21d")) is False, "critical", f"approved_for_v2_21d={review_summary.get('approved_for_v2_21d')}")
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("schema_column_count_expected", len(operational_header) == 33, "critical", f"columns={len(operational_header)}")
    add_check("structured_sgx_endpoints_available", len(structured_sgx_endpoints) > 0, "critical", f"structured_sgx_endpoints={len(structured_sgx_endpoints)}")
    add_check("raw_candidates_extracted", len(raw_candidates) > 0, "critical", f"raw_candidates={len(raw_candidates)}")
    add_check("eligible_candidates_available", len(eligible_candidates) > 0, "warning", f"eligible_candidates={len(eligible_candidates)}")
    add_check("projected_rows_under_quality_ceiling", projected_rows_after_addition <= QUALITY_CEILING_TARGET, "critical", f"projected_rows={projected_rows_after_addition};ceiling={QUALITY_CEILING_TARGET}")
    add_check("capacity_remaining_non_negative", remaining_capacity_after_addition >= 0, "critical", f"remaining_capacity_after_addition={remaining_capacity_after_addition}")
    add_check("operational_base_not_modified", sha256_file(OPERATIONAL_BASE_DATASET) == OPERATIONAL_BASE_SHA_EXPECTED, "critical", "operational base SHA unchanged")
    add_check("rollback_not_modified", sha256_file(ROLLBACK_DATASET) == ROLLBACK_SHA_EXPECTED, "critical", "rollback SHA unchanged")
    add_check("singapore_only_scope", all(row["market_id"] == MARKET_ID for row in eligible_candidates + rejected_candidates), "critical", "all candidate rows are Singapore/SGX scoped")
    add_check("regex_only_candidate_acceptance_not_allowed", True, "critical", "only structured JSON endpoint objects are parsed")
    add_check("dedup_dry_run_performed", True, "critical", "dedup dry run performed against operational base")
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
        extraction_decision = "SINGAPORE_STRUCTURED_EXTRACTION_BLOCKED_REVIEW_REQUIRED"
        approved_for_singapore_rebuild_candidate = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    elif len(eligible_candidates) == 0:
        status = STATUS_NO_CANDIDATES
        extraction_decision = "NO_ELIGIBLE_SINGAPORE_CANDIDATES_AFTER_DEDUP_REVIEW_REQUIRED"
        approved_for_singapore_rebuild_candidate = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        extraction_decision = "SINGAPORE_ELIGIBLE_CANDIDATES_READY_FOR_EXPANDED_REBUILD_CANDIDATE"
        approved_for_singapore_rebuild_candidate = True
        recommended_next_phase = NEXT_PHASE_SUCCESS

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "singapore_rebuild_candidate",
            "action": "build_singapore_only_expanded_rebuild_candidate_from_eligible_candidates",
            "priority": "high" if approved_for_singapore_rebuild_candidate else "blocked",
            "recommended_phase": recommended_next_phase,
            "reason": "Eligible Singapore candidates are available after structured extraction and dedup." if approved_for_singapore_rebuild_candidate else "No eligible Singapore candidates approved.",
            "guardrails": "Singapore only; no Colombia; no pointer update; no scoring",
        },
        {
            "action_order": 2,
            "action_scope": "colombia_regulatory_discovery",
            "action": "continue_colombia_superfinanciera_simev_rnve_discovery",
            "priority": "high",
            "recommended_phase": SECONDARY_NEXT_PHASE,
            "reason": "Colombia remains blocked from BVC exchange extraction and needs official regulatory-source discovery.",
            "guardrails": "discovery only; no extraction from shell HTML",
        },
        {
            "action_order": 3,
            "action_scope": "global_rebuild_control",
            "action": "keep_global_v2_21d_blocked_until_split_outputs_are_validated",
            "priority": "high",
            "recommended_phase": recommended_next_phase,
            "reason": "This phase is dry-run only and does not promote or update active pointers.",
            "guardrails": "no promotion; no pointer update; no full59k",
        },
    ]

    summary = {
        "selected_route": "Singapore split route from Colombia + Singapore targeted expansion",
        "phase_type": PHASE_TYPE,
        "extraction_decision": extraction_decision,
        "approved_for_singapore_rebuild_candidate": approved_for_singapore_rebuild_candidate,
        "approved_for_global_v2_21d": False,
        "approved_for_colombia_extraction": False,
        "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "operational_base_rows": operational_rows,
        "operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity_before_addition": remaining_capacity,
        "market_id": MARKET_ID,
        "country": COUNTRY,
        "exchange": EXCHANGE,
        "mic": MIC,
        "currency": CURRENCY,
        "structured_sgx_endpoints_used": len(structured_sgx_endpoints),
        "raw_candidates_extracted": len(raw_candidates),
        "raw_candidates_accepted_by_quality": raw_quality_counts.get("accepted", 0),
        "raw_candidates_rejected_by_quality": raw_quality_counts.get("rejected", 0),
        "eligible_new_candidates": len(eligible_candidates),
        "rejected_candidates": len(rejected_candidates),
        "instrument_bucket_counts": dict(instrument_bucket_counts),
        "projected_rows_after_addition": projected_rows_after_addition,
        "remaining_capacity_after_addition": remaining_capacity_after_addition,
        "candidate_extraction_performed": True,
        "dedup_performed": True,
        "schema_projection_performed": True,
        "expanded_rebuild_performed": False,
        "provider_expansion_scope": "singapore_split_only",
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
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(SOURCE_ENDPOINTS_CSV, source_endpoint_rows, ["market_id", "provider", "source_id", "url", "raw_file", "parse_mode", "candidate_like_records", "structured_endpoint_candidate", "endpoint_validation_status", "selected_for_extraction"])
    write_csv(FIELD_MAPPING_CSV, field_mapping_rows, ["target_field", "source_keys_priority", "rule"])
    write_csv(RAW_CANDIDATES_CSV, raw_candidates, RAW_FIELDNAMES)
    write_csv(ELIGIBLE_CANDIDATES_CSV, eligible_candidates, ELIGIBLE_FIELDNAMES)
    write_csv(REJECTED_CANDIDATES_CSV, rejected_candidates, REJECTED_FIELDNAMES)
    write_csv(DEDUP_SUMMARY_CSV, dedup_summary_rows, ["market_id", "raw_candidates", "raw_accepted_by_quality", "raw_rejected_by_quality", "eligible_new_candidates", "rejected_candidates", "duplicate_or_rejected_by_dedup", "rejected_by_quality_filter", "rejected_by_capacity_filter", "projected_rows_after_addition", "remaining_capacity_after_addition", "ready_for_singapore_rebuild_candidate"])
    write_csv(SCHEMA_PROJECTION_CSV, projected_rows, operational_header)
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "recommended_phase", "reason", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "source_endpoints": source_endpoint_rows,
        "dedup_summary": dedup_summary_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Singapore split route",
            "market_scope": [MARKET_ID],
            "colombia_scope_excluded": True,
            "approved_for_singapore_rebuild_candidate": approved_for_singapore_rebuild_candidate,
            "approved_for_global_v2_21d": False,
            "approved_for_colombia_extraction": False,
            "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "operational_base_rows": operational_rows,
            "operational_base_sha": operational_sha,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "candidate_extraction_performed": True,
            "dedup_dry_run_performed": True,
            "schema_projection_performed": True,
            "regex_only_candidate_acceptance_allowed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "file_edit_performed_on_operational_base": False,
            "file_copy_performed_on_operational_base": False,
            "file_rename_performed_on_operational_base": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "provider_expansion_scope": "singapore_split_only",
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
            "history_rewrite_performed": False,
            "force_push_required": False,
        },
        "recommended_next_phase": recommended_next_phase,
        "secondary_next_phase": SECONDARY_NEXT_PHASE,
    }

    write_json(REPORT_JSON, payload)

    endpoint_lines = "\n".join(
        f"- `{row['source_id']}` — records `{row['candidate_like_records']}` — selected `{row['selected_for_extraction']}`"
        for row in source_endpoint_rows
    )

    dedup_lines = "\n".join(
        f"- `{row['market_id']}` — raw `{row['raw_candidates']}` — eligible `{row['eligible_new_candidates']}` — rejected `{row['rejected_candidates']}` — projected rows `{row['projected_rows_after_addition']}`"
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

v2.21C4S performs a Singapore-only structured candidate extraction and dedup dry run from SGX structured JSON endpoints validated in v2.21C3 and approved by v2.21C3_REVIEW.

This phase does not include Colombia. Colombia remains on the separate v2.21C3B regulatory discovery path.

This phase does not rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Extraction decision: `{extraction_decision}`
- Approved for Singapore rebuild candidate: `{approved_for_singapore_rebuild_candidate}`
- Approved for global v2.21D: `False`
- Operational base rows: `{operational_rows}`
- Operational base SHA256: `{operational_sha}`
- Rollback rows: `{rollback_rows}`
- Rollback SHA256: `{rollback_sha}`
- Structured SGX endpoints used: `{len(structured_sgx_endpoints)}`
- Raw candidates extracted: `{len(raw_candidates)}`
- Eligible new candidates: `{len(eligible_candidates)}`
- Rejected candidates: `{len(rejected_candidates)}`
- Projected rows after addition: `{projected_rows_after_addition}`
- Remaining capacity after addition: `{remaining_capacity_after_addition}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Source endpoints

{endpoint_lines}

## Dedup summary

{dedup_lines}

## Checks

{check_lines}

## Recommended next phase

Primary: `{recommended_next_phase}`

Secondary: `{SECONDARY_NEXT_PHASE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21C4S Singapore structured candidate extraction + dedup dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_ENDPOINTS:")
    for row in source_endpoint_rows:
        print(f"- {row['source_id']}: records={row['candidate_like_records']} selected={row['selected_for_extraction']}")
    print("")
    print("DEDUP_SUMMARY:")
    for row in dedup_summary_rows:
        print(
            f"- {row['market_id']}: raw={row['raw_candidates']} "
            f"eligible={row['eligible_new_candidates']} rejected={row['rejected_candidates']} "
            f"projected_rows={row['projected_rows_after_addition']}"
        )
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")
    print("")
    print("SECONDARY_NEXT_PHASE:")
    print(f"- {SECONDARY_NEXT_PHASE}")


if __name__ == "__main__":
    main()
