from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


CANONICAL_DATASET = Path("outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv")
VALIDATION_JSON = Path("outputs/full_universe_source_acquisition/deutsche_boerse_xetra_expanded_validation_v2_14f.json")
CLOSURE_JSON = Path("outputs/full_universe_source_acquisition/deutsche_boerse_xetra_closure_report_v2_14g.json")

EXPECTED_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
EXPECTED_ROWS_NEEDED = 11713
EXPECTED_SOURCE_TO_50K = 76.6

EXPECTED_PROVIDER_COUNTS = {
    "cboe_europe_reference_data": 21154,
    "jpx_listed_securities": 3705,
    "nasdaq_trader_nasdaqlisted": 3244,
    "hkex_securities_list": 2804,
    "nasdaq_trader_otherlisted": 2404,
    "sec_company_tickers_exchange": 2359,
    "deutsche_boerse_xetra_all_tradable_instruments": 1424,
    "cboe_listed_symbols": 1193,
}

EXPECTED_CLOSURE_STATUS = "DEUTSCHE_BOERSE_XETRA_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED"
EXPECTED_VALIDATION_STATUS = "DEUTSCHE_BOERSE_XETRA_EXPANDED_VALIDATION_PASSED_FULL_SOURCE_STILL_BLOCKED"


def compact(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def find_col(headers: list[str], exact_candidates: list[str], fuzzy_candidates: list[str] | None = None) -> str:
    fuzzy_candidates = fuzzy_candidates or exact_candidates
    compact_headers = {compact(header): header for header in headers}

    for candidate in exact_candidates:
        c = compact(candidate)
        if c in compact_headers:
            return compact_headers[c]

    for header in headers:
        h_low = header.lower()
        h_cmp = compact(header)
        for candidate in fuzzy_candidates:
            c_low = candidate.lower()
            c_cmp = compact(candidate)
            if c_low in h_low or c_cmp in h_cmp:
                return header

    return ""


def read_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def summarize_dataset() -> dict:
    rows = read_csv_rows(CANONICAL_DATASET)
    headers = list(rows[0].keys()) if rows else []

    ticker_col = find_col(headers, ["ticker"], ["ticker", "symbol", "mnemonic"])
    exchange_col = find_col(headers, ["exchange"], ["exchange", "mic", "venue", "market"])
    provider_col = find_col(headers, ["source_provider"], ["source_provider", "provider"])
    company_col = find_col(headers, ["company_name"], ["company_name", "security_name", "issuer_name", "name"])
    isin_col = find_col(headers, ["isin"], ["isin"])

    provider_counts = Counter()
    exchange_ticker_counts = Counter()

    blank_ticker = 0
    blank_exchange = 0
    blank_provider = 0
    blank_company_name = 0
    blank_isin = 0

    for row in rows:
        ticker = clean(row.get(ticker_col, "")).upper().replace(" ", "") if ticker_col else ""
        exchange = clean(row.get(exchange_col, "")).upper().replace(" ", "") if exchange_col else ""
        provider = clean(row.get(provider_col, "")) if provider_col else ""
        company = clean(row.get(company_col, "")) if company_col else ""
        isin = clean(row.get(isin_col, "")).upper().replace(" ", "") if isin_col else ""

        blank_ticker += int(not ticker)
        blank_exchange += int(not exchange)
        blank_provider += int(not provider)
        blank_company_name += int(not company)
        blank_isin += int(not isin)

        provider_counts[provider or "(blank)"] += 1

        if exchange and ticker:
            exchange_ticker_counts[f"{exchange}|{ticker}"] += 1

    duplicate_exchange_ticker_keys = [
        key for key, count in exchange_ticker_counts.items() if count > 1
    ]

    row_count = len(rows)

    return {
        "columns": {
            "ticker_col": ticker_col,
            "exchange_col": exchange_col,
            "provider_col": provider_col,
            "company_col": company_col,
            "isin_col": isin_col,
        },
        "counts": {
            "rows": row_count,
            "rows_needed_to_50k": max(0, FULL_SOURCE_THRESHOLD - row_count),
            "source_to_50k_percent": round((row_count / FULL_SOURCE_THRESHOLD) * 100, 1),
            "duplicate_exchange_ticker_keys": len(duplicate_exchange_ticker_keys),
            "blank_ticker": blank_ticker,
            "blank_exchange": blank_exchange,
            "blank_provider": blank_provider,
            "blank_company_name": blank_company_name,
            "blank_isin": blank_isin,
        },
        "provider_counts": dict(provider_counts),
    }


def test_canonical_files_exist():
    assert CANONICAL_DATASET.exists()
    assert VALIDATION_JSON.exists()
    assert CLOSURE_JSON.exists()


def test_row_count_and_source_gate():
    summary = summarize_dataset()
    assert summary["counts"]["rows"] == EXPECTED_ROWS
    assert summary["counts"]["rows_needed_to_50k"] == EXPECTED_ROWS_NEEDED
    assert summary["counts"]["source_to_50k_percent"] == EXPECTED_SOURCE_TO_50K
    assert summary["counts"]["rows"] < FULL_SOURCE_THRESHOLD


def test_required_columns_and_required_non_blank_fields():
    summary = summarize_dataset()
    assert summary["columns"]["ticker_col"]
    assert summary["columns"]["exchange_col"]
    assert summary["columns"]["provider_col"]
    assert summary["columns"]["company_col"]
    assert summary["columns"]["isin_col"]

    assert summary["counts"]["blank_ticker"] == 0
    assert summary["counts"]["blank_exchange"] == 0
    assert summary["counts"]["blank_provider"] == 0


def test_duplicate_exchange_ticker_keys_zero():
    summary = summarize_dataset()
    assert summary["counts"]["duplicate_exchange_ticker_keys"] == 0


def test_provider_breakdown_exact():
    summary = summarize_dataset()
    assert summary["provider_counts"] == EXPECTED_PROVIDER_COUNTS


def test_closure_and_validation_statuses():
    validation = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    closure = json.loads(CLOSURE_JSON.read_text(encoding="utf-8"))

    assert validation.get("status") == EXPECTED_VALIDATION_STATUS
    assert closure.get("closure_status") == EXPECTED_CLOSURE_STATUS
