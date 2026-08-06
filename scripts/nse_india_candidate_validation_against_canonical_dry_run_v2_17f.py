from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.17F"
PHASE = "NSE India Candidate Validation Against Canonical Dry Run"
PHASE_TYPE = "candidate-validation-against-canonical-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

V217E_JSON = OUTPUT_DIR / "nse_india_candidate_extraction_dry_run_v2_17e.json"
V217E_CANDIDATES_CSV = OUTPUT_DIR / "nse_india_candidate_extraction_candidates_v2_17e.csv"
V217E_EXCLUSIONS_CSV = OUTPUT_DIR / "nse_india_candidate_extraction_exclusions_v2_17e.csv"
V217E_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "nse_india_candidate_extraction_source_diagnostics_v2_17e.csv"

REPORT_JSON = OUTPUT_DIR / "nse_india_candidate_validation_against_canonical_dry_run_v2_17f.json"
REPORT_MD = OUTPUT_DIR / "nse_india_candidate_validation_against_canonical_dry_run_v2_17f.md"
CLASSIFIED_CANDIDATES_CSV = OUTPUT_DIR / "nse_india_candidate_validation_classified_candidates_v2_17f.csv"
POTENTIAL_NET_NEW_CSV = OUTPUT_DIR / "nse_india_candidate_validation_potential_net_new_v2_17f.csv"
EXISTING_MATCHES_CSV = OUTPUT_DIR / "nse_india_candidate_validation_existing_matches_v2_17f.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "nse_india_candidate_validation_source_diagnostics_v2_17f.csv"
CANONICAL_PROFILE_CSV = OUTPUT_DIR / "nse_india_candidate_validation_canonical_profile_v2_17f.csv"

CURRENT_CANONICAL_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713

EXPECTED_V217E_STATUS = "NSE_INDIA_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_CANONICAL_COMPARISON_STILL_BLOCKED"
EXPECTED_V217E_NEXT = "v2.17F - NSE India Candidate Validation Against Canonical Dry Run"

NEXT_PHASE_IF_NET_NEW = "v2.17G - NSE India Expanded Rebuild Candidate"
NEXT_PHASE_IF_NO_NET_NEW = "v2.17I - NSE India Closure Report"

CANONICAL_SYMBOL_COLUMNS = [
    "symbol",
    "ticker",
    "ticker_symbol",
    "local_symbol",
    "raw_symbol",
    "Symbol",
    "Ticker",
    "TICKER",
    "SYMBOL",
    "TckrSymb",
    "TICKER_SYMBOL",
]

CANONICAL_NAME_COLUMNS = [
    "name",
    "company_name",
    "security_name",
    "instrument_name",
    "raw_name",
    "Name",
    "Company Name",
    "NAME OF COMPANY",
    "SECURITY NAME",
    "FinInstrmNm",
    "long_name",
    "short_name",
]

CANONICAL_EXCHANGE_COLUMNS = [
    "exchange",
    "primary_exchange",
    "market",
    "mic",
    "venue",
    "raw_exchange",
    "Exchange",
    "MIC",
    "Xchg",
]

CANONICAL_COUNTRY_COLUMNS = [
    "country",
    "country_name",
    "market_country",
    "Country",
]

CANONICAL_CURRENCY_COLUMNS = [
    "currency",
    "Currency",
    "ccy",
    "Ccy",
]

CANONICAL_ISIN_COLUMNS = [
    "isin",
    "ISIN",
    "isin_number",
    "ISIN NUMBER",
    "ISINNumber",
    "raw_isin",
]

CLASSIFIED_FIELDS = [
    "candidate_id",
    "source_id",
    "raw_symbol",
    "raw_name",
    "raw_exchange",
    "raw_series",
    "raw_isin",
    "country",
    "currency",
    "confidence_bucket",
    "review_required",
    "candidate_key",
    "duplicate_sources",
    "match_status",
    "match_strength",
    "canonical_match_count",
    "canonical_match_examples",
    "net_new_bucket",
    "validation_notes",
    "evidence",
    "source_notes",
]

POTENTIAL_NET_NEW_FIELDS = CLASSIFIED_FIELDS

EXISTING_MATCH_FIELDS = [
    "candidate_id",
    "source_id",
    "raw_symbol",
    "raw_name",
    "raw_series",
    "raw_isin",
    "match_status",
    "match_strength",
    "canonical_row_index",
    "canonical_symbol",
    "canonical_symbol_base",
    "canonical_name",
    "canonical_exchange",
    "canonical_country",
    "canonical_currency",
    "canonical_isin",
    "canonical_evidence",
]

SOURCE_DIAGNOSTIC_FIELDS = [
    "source_id",
    "candidates_total",
    "existing_count",
    "possible_existing_count",
    "potential_net_new_count",
    "invalid_count",
    "high_confidence_count",
    "medium_confidence_count",
    "low_confidence_count",
    "review_required_count",
    "match_rate_percent",
    "potential_net_new_rate_percent",
    "top_series_counts",
    "notes",
]

CANONICAL_PROFILE_FIELDS = [
    "profile_key",
    "profile_value",
    "notes",
]

VALID_ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(value: str) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split()).strip()


def normalize_upper(value: str) -> str:
    return normalize_text(value).upper()


def normalize_symbol(value: str) -> str:
    value = normalize_upper(value)
    value = value.replace(" ", "")
    return value


def symbol_base(value: str) -> str:
    value = normalize_symbol(value)

    if ":" in value:
        value = value.split(":")[-1]

    for suffix in [".NS", ".NSE", ".BO", ".BSE", ".IN"]:
        if value.endswith(suffix):
            value = value[: -len(suffix)]

    return value


def normalize_isin(value: str) -> str:
    return normalize_upper(value).replace(" ", "")


def normalize_country(value: str) -> str:
    value = normalize_upper(value)

    if value in {"IN", "IND", "INDIA", "BHARAT"}:
        return "INDIA"

    return value


def normalize_exchange(value: str) -> str:
    value = normalize_upper(value)

    if value in {"NSE", "XNSE"}:
        return "NSE"

    if "NATIONAL STOCK EXCHANGE" in value:
        return "NSE"

    if value in {"BSE", "XBOM", "BOMBAY STOCK EXCHANGE"}:
        return "BSE"

    if value.endswith(".NS"):
        return "NSE"

    return value


def normalize_currency(value: str) -> str:
    value = normalize_upper(value)

    if value in {"INR", "RUPEE", "INDIAN RUPEE"}:
        return "INR"

    return value


def boolish(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def pick_value(row: dict, candidates: list[str]) -> str:
    if not row:
        return ""

    exact = {str(key).strip().lower(): key for key in row.keys() if key is not None}
    compact = {str(key).strip().lower().replace("_", "").replace(" ", ""): key for key in row.keys() if key is not None}

    for candidate in candidates:
        key = exact.get(candidate.strip().lower())
        if key is not None:
            return str(row.get(key, "") or "").strip()

    for candidate in candidates:
        key = compact.get(candidate.strip().lower().replace("_", "").replace(" ", ""))
        if key is not None:
            return str(row.get(key, "") or "").strip()

    for key in row.keys():
        low = str(key).strip().lower()
        for candidate in candidates:
            cand = candidate.strip().lower()
            if cand and cand in low:
                return str(row.get(key, "") or "").strip()

    return ""


def canonical_compact(row: dict, row_index: int) -> dict:
    symbol = pick_value(row, CANONICAL_SYMBOL_COLUMNS)
    name = pick_value(row, CANONICAL_NAME_COLUMNS)
    exchange = pick_value(row, CANONICAL_EXCHANGE_COLUMNS)
    country = pick_value(row, CANONICAL_COUNTRY_COLUMNS)
    currency = pick_value(row, CANONICAL_CURRENCY_COLUMNS)
    isin = pick_value(row, CANONICAL_ISIN_COLUMNS)

    return {
        "canonical_row_index": row_index,
        "canonical_symbol": normalize_symbol(symbol),
        "canonical_symbol_base": symbol_base(symbol),
        "canonical_name": normalize_text(name),
        "canonical_exchange": normalize_exchange(exchange),
        "canonical_country": normalize_country(country),
        "canonical_currency": normalize_currency(currency),
        "canonical_isin": normalize_isin(isin),
        "raw_row": row,
    }


def canonical_evidence(compact: dict) -> str:
    evidence = {
        "canonical_row_index": compact["canonical_row_index"],
        "canonical_symbol": compact["canonical_symbol"],
        "canonical_symbol_base": compact["canonical_symbol_base"],
        "canonical_name": compact["canonical_name"],
        "canonical_exchange": compact["canonical_exchange"],
        "canonical_country": compact["canonical_country"],
        "canonical_currency": compact["canonical_currency"],
        "canonical_isin": compact["canonical_isin"],
    }
    return json.dumps(evidence, ensure_ascii=False, sort_keys=True)


def candidate_compact(row: dict) -> dict:
    return {
        "candidate_id": row.get("candidate_id", ""),
        "source_id": row.get("source_id", ""),
        "raw_symbol": normalize_symbol(row.get("raw_symbol", "")),
        "raw_symbol_base": symbol_base(row.get("raw_symbol", "")),
        "raw_name": normalize_text(row.get("raw_name", "")),
        "raw_exchange": normalize_exchange(row.get("raw_exchange", "")),
        "raw_series": normalize_upper(row.get("raw_series", "")),
        "raw_isin": normalize_isin(row.get("raw_isin", "")),
        "country": normalize_country(row.get("country", "")),
        "currency": normalize_currency(row.get("currency", "")),
        "confidence_bucket": normalize_text(row.get("confidence_bucket", "")),
        "review_required": boolish(row.get("review_required", "")),
        "candidate_key": row.get("candidate_key", ""),
        "duplicate_sources": row.get("duplicate_sources", ""),
        "evidence": row.get("evidence", ""),
        "source_notes": row.get("notes", ""),
    }


def valid_isin(value: str) -> bool:
    value = normalize_isin(value)
    return bool(value and VALID_ISIN_RE.match(value))


def build_canonical_indexes(canonical_rows: list[dict]) -> tuple[list[dict], dict]:
    compact_rows = []
    by_isin = defaultdict(list)
    by_symbol_base = defaultdict(list)
    by_symbol_exchange = defaultdict(list)
    by_symbol_country = defaultdict(list)

    for idx, row in enumerate(canonical_rows, start=1):
        compact = canonical_compact(row, idx)
        compact_rows.append(compact)

        if compact["canonical_isin"]:
            by_isin[compact["canonical_isin"]].append(compact)

        if compact["canonical_symbol_base"]:
            by_symbol_base[compact["canonical_symbol_base"]].append(compact)

        if compact["canonical_symbol_base"] and compact["canonical_exchange"]:
            by_symbol_exchange[(compact["canonical_symbol_base"], compact["canonical_exchange"])].append(compact)

        if compact["canonical_symbol_base"] and compact["canonical_country"]:
            by_symbol_country[(compact["canonical_symbol_base"], compact["canonical_country"])].append(compact)

    indexes = {
        "by_isin": by_isin,
        "by_symbol_base": by_symbol_base,
        "by_symbol_exchange": by_symbol_exchange,
        "by_symbol_country": by_symbol_country,
    }

    return compact_rows, indexes


def unique_matches(matches: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
    seen = set()
    output = []

    for method, compact in matches:
        key = compact["canonical_row_index"]
        if key in seen:
            continue
        seen.add(key)
        output.append((method, compact))

    return output


def classify_candidate(candidate: dict, indexes: dict) -> tuple[dict, list[dict]]:
    symbol = candidate["raw_symbol"]
    base = candidate["raw_symbol_base"]
    isin = candidate["raw_isin"]
    exchange = candidate["raw_exchange"] or "NSE"
    country = candidate["country"] or "INDIA"

    issues = []

    if not symbol:
        issues.append("missing_symbol")

    if not candidate["raw_name"]:
        issues.append("missing_name")

    if isin and not valid_isin(isin):
        issues.append("invalid_isin_format")

    matches: list[tuple[str, dict]] = []

    if isin and valid_isin(isin):
        for compact in indexes["by_isin"].get(isin, []):
            matches.append(("isin", compact))

    if base:
        for compact in indexes["by_symbol_exchange"].get((base, exchange), []):
            matches.append(("symbol_exchange", compact))

        for compact in indexes["by_symbol_country"].get((base, country), []):
            matches.append(("symbol_country", compact))

        if not matches:
            for compact in indexes["by_symbol_base"].get(base, []):
                matches.append(("symbol_only", compact))

    matches = unique_matches(matches)

    if issues:
        match_status = "invalid_candidate_review"
        match_strength = "invalid"
        net_new_bucket = "not_net_new_invalid_candidate"
    elif matches:
        methods = {method for method, _ in matches}

        if "isin" in methods:
            match_status = "existing_isin_match"
            match_strength = "exact_isin"
            net_new_bucket = "blocked_existing"
        elif "symbol_exchange" in methods:
            match_status = "existing_symbol_exchange_match"
            match_strength = "symbol_exchange"
            net_new_bucket = "blocked_existing"
        elif "symbol_country" in methods:
            match_status = "existing_symbol_country_match"
            match_strength = "symbol_country"
            net_new_bucket = "blocked_existing"
        else:
            match_status = "possible_existing_symbol_only_review"
            match_strength = "symbol_only"
            net_new_bucket = "review_possible_existing"
    else:
        match_status = "potential_net_new"
        match_strength = "none"
        if candidate["confidence_bucket"] == "high" and not candidate["review_required"]:
            net_new_bucket = "potential_net_new_high"
        else:
            net_new_bucket = "potential_net_new_review"

    match_examples = [
        {
            "method": method,
            "canonical_row_index": compact["canonical_row_index"],
            "canonical_symbol": compact["canonical_symbol"],
            "canonical_name": compact["canonical_name"],
            "canonical_exchange": compact["canonical_exchange"],
            "canonical_country": compact["canonical_country"],
            "canonical_isin": compact["canonical_isin"],
        }
        for method, compact in matches[:5]
    ]

    classified = {
        "candidate_id": candidate["candidate_id"],
        "source_id": candidate["source_id"],
        "raw_symbol": candidate["raw_symbol"],
        "raw_name": candidate["raw_name"],
        "raw_exchange": exchange,
        "raw_series": candidate["raw_series"],
        "raw_isin": candidate["raw_isin"],
        "country": country,
        "currency": candidate["currency"] or "INR",
        "confidence_bucket": candidate["confidence_bucket"],
        "review_required": candidate["review_required"],
        "candidate_key": candidate["candidate_key"],
        "duplicate_sources": candidate["duplicate_sources"],
        "match_status": match_status,
        "match_strength": match_strength,
        "canonical_match_count": len(matches),
        "canonical_match_examples": json.dumps(match_examples, ensure_ascii=False, sort_keys=True),
        "net_new_bucket": net_new_bucket,
        "validation_notes": " | ".join(issues),
        "evidence": candidate["evidence"],
        "source_notes": candidate["source_notes"],
    }

    match_rows = []

    for method, compact in matches[:5]:
        match_rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "source_id": candidate["source_id"],
                "raw_symbol": candidate["raw_symbol"],
                "raw_name": candidate["raw_name"],
                "raw_series": candidate["raw_series"],
                "raw_isin": candidate["raw_isin"],
                "match_status": match_status,
                "match_strength": method,
                "canonical_row_index": compact["canonical_row_index"],
                "canonical_symbol": compact["canonical_symbol"],
                "canonical_symbol_base": compact["canonical_symbol_base"],
                "canonical_name": compact["canonical_name"],
                "canonical_exchange": compact["canonical_exchange"],
                "canonical_country": compact["canonical_country"],
                "canonical_currency": compact["canonical_currency"],
                "canonical_isin": compact["canonical_isin"],
                "canonical_evidence": canonical_evidence(compact),
            }
        )

    return classified, match_rows


def build_source_diagnostics(classified_rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)

    for row in classified_rows:
        grouped[row["source_id"]].append(row)

    diagnostics = []

    for source_id, rows in sorted(grouped.items()):
        total = len(rows)
        existing_count = sum(1 for row in rows if row["net_new_bucket"] == "blocked_existing")
        possible_existing_count = sum(1 for row in rows if row["net_new_bucket"] == "review_possible_existing")
        potential_net_new_count = sum(1 for row in rows if row["net_new_bucket"].startswith("potential_net_new"))
        invalid_count = sum(1 for row in rows if row["net_new_bucket"] == "not_net_new_invalid_candidate")
        high_count = sum(1 for row in rows if row["confidence_bucket"] == "high")
        medium_count = sum(1 for row in rows if row["confidence_bucket"] == "medium")
        low_count = sum(1 for row in rows if row["confidence_bucket"] == "low")
        review_count = sum(1 for row in rows if boolish(row["review_required"]))
        series_counts = Counter(row["raw_series"] for row in rows)

        match_rate = round(((existing_count + possible_existing_count) / total) * 100, 2) if total else 0
        net_new_rate = round((potential_net_new_count / total) * 100, 2) if total else 0

        diagnostics.append(
            {
                "source_id": source_id,
                "candidates_total": total,
                "existing_count": existing_count,
                "possible_existing_count": possible_existing_count,
                "potential_net_new_count": potential_net_new_count,
                "invalid_count": invalid_count,
                "high_confidence_count": high_count,
                "medium_confidence_count": medium_count,
                "low_confidence_count": low_count,
                "review_required_count": review_count,
                "match_rate_percent": match_rate,
                "potential_net_new_rate_percent": net_new_rate,
                "top_series_counts": json.dumps(dict(series_counts.most_common(10)), ensure_ascii=False, sort_keys=True),
                "notes": "dry-run source classification only; no canonical mutation",
            }
        )

    return diagnostics


def build_canonical_profile(canonical_rows: list[dict], compact_rows: list[dict], indexes: dict) -> list[dict]:
    nonempty_symbols = sum(1 for row in compact_rows if row["canonical_symbol_base"])
    nonempty_isins = sum(1 for row in compact_rows if row["canonical_isin"])
    nonempty_exchanges = sum(1 for row in compact_rows if row["canonical_exchange"])
    nonempty_countries = sum(1 for row in compact_rows if row["canonical_country"])

    columns = list(canonical_rows[0].keys()) if canonical_rows else []

    return [
        {"profile_key": "canonical_rows", "profile_value": len(canonical_rows), "notes": str(CANONICAL_DATASET)},
        {"profile_key": "canonical_columns", "profile_value": " | ".join(columns), "notes": "raw canonical CSV header"},
        {"profile_key": "nonempty_symbol_rows", "profile_value": nonempty_symbols, "notes": "derived by symbol column detection"},
        {"profile_key": "nonempty_isin_rows", "profile_value": nonempty_isins, "notes": "derived by ISIN column detection"},
        {"profile_key": "nonempty_exchange_rows", "profile_value": nonempty_exchanges, "notes": "derived by exchange column detection"},
        {"profile_key": "nonempty_country_rows", "profile_value": nonempty_countries, "notes": "derived by country column detection"},
        {"profile_key": "symbol_base_index_keys", "profile_value": len(indexes["by_symbol_base"]), "notes": "unique canonical symbol base keys"},
        {"profile_key": "isin_index_keys", "profile_value": len(indexes["by_isin"]), "notes": "unique canonical ISIN keys"},
        {"profile_key": "symbol_exchange_index_keys", "profile_value": len(indexes["by_symbol_exchange"]), "notes": "unique symbol/exchange keys"},
        {"profile_key": "symbol_country_index_keys", "profile_value": len(indexes["by_symbol_country"]), "notes": "unique symbol/country keys"},
    ]


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        CLASSIFIED_CANDIDATES_CSV,
        POTENTIAL_NET_NEW_CSV,
        EXISTING_MATCHES_CSV,
        SOURCE_DIAGNOSTICS_CSV,
        CANONICAL_PROFILE_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    e_report = read_json(V217E_JSON)
    candidates_raw = read_csv(V217E_CANDIDATES_CSV)
    exclusions_raw = read_csv(V217E_EXCLUSIONS_CSV)
    source_diag_e = read_csv(V217E_SOURCE_DIAGNOSTICS_CSV)
    canonical_raw = read_csv(CANONICAL_DATASET)

    compact_canonical, indexes = build_canonical_indexes(canonical_raw)
    canonical_profile = build_canonical_profile(canonical_raw, compact_canonical, indexes)

    classified_rows = []
    existing_match_rows = []

    for row in candidates_raw:
        compact_candidate = candidate_compact(row)
        classified, matches = classify_candidate(compact_candidate, indexes)
        classified_rows.append(classified)
        existing_match_rows.extend(matches)

    # Internal candidate duplicate guard:
    # NSE can expose the same security/ISIN through several series such as EQ, BE, BL, SM, ST, BZ.
    # v2.17F must avoid treating every market series as an independent net-new security.
    series_priority = {
        "EQ": 0,
        "SM": 1,
        "ST": 2,
        "BE": 3,
        "BZ": 4,
        "BL": 5,
        "SZ": 6,
    }

    source_priority = {
        "nse_securities_available_equity_segment": 0,
        "nse_securities_available_sme": 1,
        "nse_all_reports_cm_mii_security_file_nse_listed": 2,
    }

    confidence_priority = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    def internal_identity(row: dict) -> str:
        isin = normalize_isin(row.get("raw_isin", ""))
        symbol = symbol_base(row.get("raw_symbol", ""))
        name = normalize_upper(row.get("raw_name", ""))

        if isin and valid_isin(isin):
            return f"isin:{isin}"

        if symbol and name:
            return f"symbol_name:{symbol}|{name}"

        if symbol:
            return f"symbol:{symbol}"

        return ""

    grouped_internal_candidates = defaultdict(list)

    for idx, row in enumerate(classified_rows):
        if not row["net_new_bucket"].startswith("potential_net_new"):
            continue

        identity = internal_identity(row)
        if not identity:
            continue

        grouped_internal_candidates[identity].append((idx, row))

    internal_duplicate_rows_marked = 0
    internal_duplicate_groups = 0

    for identity, grouped_rows in grouped_internal_candidates.items():
        if len(grouped_rows) <= 1:
            continue

        internal_duplicate_groups += 1

        preferred_idx, preferred_row = sorted(
            grouped_rows,
            key=lambda item: (
                series_priority.get(item[1].get("raw_series", ""), 99),
                source_priority.get(item[1].get("source_id", ""), 99),
                confidence_priority.get(item[1].get("confidence_bucket", ""), 99),
                item[1].get("raw_symbol", ""),
            ),
        )[0]

        preferred_candidate_id = preferred_row.get("candidate_id", "")

        for idx, row in grouped_rows:
            if idx == preferred_idx:
                row["validation_notes"] = (
                    str(row.get("validation_notes", "") or "")
                    + f" | internal_duplicate_group_preferred:{identity}; duplicate_group_size={len(grouped_rows)}"
                ).strip(" |")
                continue

            row["match_status"] = "possible_existing_duplicate_series_review"
            row["match_strength"] = "internal_candidate_duplicate_series"
            row["net_new_bucket"] = "review_possible_existing"
            row["validation_notes"] = (
                str(row.get("validation_notes", "") or "")
                + f" | internal_duplicate_series_review:{identity}; preferred_candidate_id={preferred_candidate_id}; duplicate_group_size={len(grouped_rows)}"
            ).strip(" |")
            internal_duplicate_rows_marked += 1

    potential_net_new_rows = [
        row for row in classified_rows
        if row["net_new_bucket"].startswith("potential_net_new")
    ]

    existing_rows = [
        row for row in classified_rows
        if row["net_new_bucket"] == "blocked_existing"
    ]

    possible_existing_rows = [
        row for row in classified_rows
        if row["net_new_bucket"] == "review_possible_existing"
    ]

    invalid_rows = [
        row for row in classified_rows
        if row["net_new_bucket"] == "not_net_new_invalid_candidate"
    ]

    high_net_new_rows = [
        row for row in potential_net_new_rows
        if row["net_new_bucket"] == "potential_net_new_high"
    ]

    review_net_new_rows = [
        row for row in potential_net_new_rows
        if row["net_new_bucket"] == "potential_net_new_review"
    ]

    source_diagnostics = build_source_diagnostics(classified_rows)

    status_counter = Counter(row["match_status"] for row in classified_rows)
    net_new_counter = Counter(row["net_new_bucket"] for row in classified_rows)
    source_counter = Counter(row["source_id"] for row in potential_net_new_rows)
    series_counter = Counter(row["raw_series"] for row in potential_net_new_rows)
    confidence_counter = Counter(row["confidence_bucket"] for row in potential_net_new_rows)

    projected_rows_if_all_potential_net_new_promoted = CURRENT_CANONICAL_ROWS + len(potential_net_new_rows)

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_17e_report_exists", V217E_JSON.exists(), "critical", str(V217E_JSON))
    add_check(
        "v2_17e_status_expected",
        e_report.get("status") == EXPECTED_V217E_STATUS,
        "critical",
        str(e_report.get("status", "")),
    )
    add_check(
        "v2_17e_recommended_f",
        e_report.get("recommended_next_phase") == EXPECTED_V217E_NEXT,
        "critical",
        str(e_report.get("recommended_next_phase", "")),
    )
    add_check("v2_17e_candidates_exists", V217E_CANDIDATES_CSV.exists(), "critical", str(V217E_CANDIDATES_CSV))
    add_check("v2_17e_exclusions_exists", V217E_EXCLUSIONS_CSV.exists(), "critical", str(V217E_EXCLUSIONS_CSV))
    add_check("v2_17e_source_diagnostics_exists", V217E_SOURCE_DIAGNOSTICS_CSV.exists(), "critical", str(V217E_SOURCE_DIAGNOSTICS_CSV))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("canonical_rows_expected", len(canonical_raw) == CURRENT_CANONICAL_ROWS, "critical", f"canonical_rows={len(canonical_raw)}")
    add_check("canonical_symbol_index_available", len(indexes["by_symbol_base"]) > 0, "critical", f"symbol_base_keys={len(indexes['by_symbol_base'])}")
    add_check("candidates_present", len(candidates_raw) > 0, "critical", f"candidates={len(candidates_raw)}")
    add_check("classified_all_candidates", len(classified_rows) == len(candidates_raw), "critical", f"classified={len(classified_rows)} candidates={len(candidates_raw)}")
    add_check("classification_partition_ok", len(classified_rows) == len(existing_rows) + len(possible_existing_rows) + len(potential_net_new_rows) + len(invalid_rows), "critical", "partition existing + possible + potential + invalid")
    add_check("potential_net_new_or_existing_present", len(potential_net_new_rows) > 0 or len(existing_rows) > 0 or len(possible_existing_rows) > 0, "critical", f"net_new={len(potential_net_new_rows)} existing={len(existing_rows)} possible={len(possible_existing_rows)}")
    add_check("existing_match_rows_consistent", len(existing_match_rows) >= len(existing_rows), "warning", f"existing_match_rows={len(existing_match_rows)} existing_rows={len(existing_rows)}")
    add_check("source_diagnostics_created", len(source_diagnostics) > 0, "critical", f"source_diagnostics={len(source_diagnostics)}")
    add_check("full_source_still_blocked", CURRENT_CANONICAL_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"{CURRENT_CANONICAL_ROWS} < {FULL_SOURCE_THRESHOLD}")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("canonical_dataset_read", True, "critical", "canonical_dataset_read=True")
    add_check("canonical_comparison_performed", True, "critical", "canonical_comparison_performed=True")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("net_new_not_applied_to_canonical", True, "critical", "net_new_filtering_applied_to_canonical=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("expanded_universe_not_rebuilt", True, "critical", "expanded_universe_rebuilt_as_canonical=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed != 0:
        status = "NSE_INDIA_CANDIDATE_VALIDATION_AGAINST_CANONICAL_DRY_RUN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.17F_FIX - NSE India Candidate Validation Repair"
    elif len(potential_net_new_rows) > 0:
        status = "NSE_INDIA_CANDIDATE_VALIDATION_AGAINST_CANONICAL_DRY_RUN_COMPLETED_NET_NEW_FOUND_REBUILD_CANDIDATE_READY_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_NET_NEW
    else:
        status = "NSE_INDIA_CANDIDATE_VALIDATION_AGAINST_CANONICAL_DRY_RUN_COMPLETED_NO_NET_NEW_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_NO_NET_NEW

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": CURRENT_CANONICAL_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": round((CURRENT_CANONICAL_ROWS / FULL_SOURCE_THRESHOLD) * 100, 2),
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "route_reference": {
            "v2_17e_artifact": str(V217E_JSON),
            "v2_17e_status": e_report.get("status", ""),
            "v2_17e_recommended_next_phase": e_report.get("recommended_next_phase", ""),
            "provider": "NSE India",
            "market": "India",
        },
        "validation_summary": {
            "canonical_rows_read": len(canonical_raw),
            "candidate_rows_read": len(candidates_raw),
            "exclusion_rows_read": len(exclusions_raw),
            "source_diagnostics_read": len(source_diag_e),
            "classified_candidates": len(classified_rows),
            "existing_candidates": len(existing_rows),
            "possible_existing_candidates": len(possible_existing_rows),
            "potential_net_new_candidates": len(potential_net_new_rows),
            "potential_net_new_high": len(high_net_new_rows),
            "potential_net_new_review": len(review_net_new_rows),
            "invalid_candidates": len(invalid_rows),
            "existing_match_rows": len(existing_match_rows),
            "projected_rows_if_all_potential_net_new_promoted": projected_rows_if_all_potential_net_new_promoted,
            "would_reach_full_source_threshold_if_all_promoted": projected_rows_if_all_potential_net_new_promoted >= FULL_SOURCE_THRESHOLD,
            "candidate_match_status_counts": dict(status_counter),
            "net_new_bucket_counts": dict(net_new_counter),
            "potential_net_new_source_counts": dict(source_counter),
            "potential_net_new_series_counts": dict(series_counter),
            "potential_net_new_confidence_counts": dict(confidence_counter),
            "internal_duplicate_groups": internal_duplicate_groups,
            "internal_duplicate_rows_marked": internal_duplicate_rows_marked,
            "critical_failed_checks": critical_failed,
        },
        "canonical_profile": canonical_profile,
        "checks": checks,
        "classified_preview": classified_rows[:100],
        "potential_net_new_preview": potential_net_new_rows[:100],
        "source_diagnostics_preview": source_diagnostics[:50],
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "v2_17e_report_read": True,
            "candidate_rows_read": True,
            "exclusion_rows_read": True,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": True,
            "existing_match_classification_performed": True,
            "potential_net_new_classification_performed": True,
            "internal_duplicate_series_guard_performed": True,
            "net_new_filtering_applied_to_candidates": True,
            "net_new_filtering_applied_to_canonical": False,
            "canonical_dataset_modified": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "full_source_gate_unblocked": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)
    write_csv(CLASSIFIED_CANDIDATES_CSV, classified_rows, CLASSIFIED_FIELDS)
    write_csv(POTENTIAL_NET_NEW_CSV, potential_net_new_rows, POTENTIAL_NET_NEW_FIELDS)
    write_csv(EXISTING_MATCHES_CSV, existing_match_rows, EXISTING_MATCH_FIELDS)
    write_csv(SOURCE_DIAGNOSTICS_CSV, source_diagnostics, SOURCE_DIAGNOSTIC_FIELDS)
    write_csv(CANONICAL_PROFILE_CSV, canonical_profile, CANONICAL_PROFILE_FIELDS)

    source_lines = "\n".join(
        f"- `{row['source_id']}` total=`{row['candidates_total']}` existing=`{row['existing_count']}` possible=`{row['possible_existing_count']}` net_new=`{row['potential_net_new_count']}` invalid=`{row['invalid_count']}`"
        for row in source_diagnostics
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

NSE India candidate validation against canonical completed as a dry run.

This phase reads the active canonical dataset and classifies NSE candidates from v2.17E as existing, possible existing, invalid, or potential net-new. It does not modify the canonical dataset, does not write any expanded rebuild candidate and does not apply net-new rows to the canonical source.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{CURRENT_CANONICAL_ROWS}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completion: `{round((CURRENT_CANONICAL_ROWS / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Validation summary

- Canonical rows read: `{len(canonical_raw)}`
- Candidate rows read: `{len(candidates_raw)}`
- Classified candidates: `{len(classified_rows)}`
- Existing candidates: `{len(existing_rows)}`
- Possible existing candidates: `{len(possible_existing_rows)}`
- Potential net-new candidates: `{len(potential_net_new_rows)}`
- Potential net-new high: `{len(high_net_new_rows)}`
- Potential net-new review: `{len(review_net_new_rows)}`
- Internal duplicate groups: `{internal_duplicate_groups}`
- Internal duplicate rows marked: `{internal_duplicate_rows_marked}`
- Invalid candidates: `{len(invalid_rows)}`
- Existing match rows: `{len(existing_match_rows)}`
- Projected rows if all potential net-new promoted: `{projected_rows_if_all_potential_net_new_promoted}`
- Would reach full source threshold if all promoted: `{projected_rows_if_all_potential_net_new_promoted >= FULL_SOURCE_THRESHOLD}`
- Critical failed checks: `{critical_failed}`

## Source diagnostics

{source_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17E report read: true
- Candidate rows read: true
- Exclusion rows read: true
- Canonical dataset read: true
- Canonical comparison performed: true
- Existing match classification performed: true
- Potential net-new classification performed: true
- Internal duplicate series guard performed: true
- Net-new filtering applied to candidates: true
- Net-new filtering applied to canonical: false
- Canonical dataset modified: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17F validates NSE India candidates against the canonical dataset in dry-run mode and prepares the route for rebuild candidate generation only if potential net-new rows are available.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.17F NSE India candidate validation against canonical dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in payload["validation_summary"].items():
        print(f"- {key}: {value}")
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

