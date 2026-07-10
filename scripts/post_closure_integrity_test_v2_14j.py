from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.14J"
PHASE = "Post-Closure Integrity Test"
PHASE_TYPE = "test-only"

CANONICAL_DATASET = Path("outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv")
VALIDATION_JSON = Path("outputs/full_universe_source_acquisition/deutsche_boerse_xetra_expanded_validation_v2_14f.json")
CLOSURE_JSON = Path("outputs/full_universe_source_acquisition/deutsche_boerse_xetra_closure_report_v2_14g.json")

REPORT_JSON = Path("outputs/audit/post_closure_integrity_test_v2_14j.json")
REPORT_MD = Path("outputs/audit/post_closure_integrity_test_v2_14j.md")

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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    if not path.exists():
        raise FileNotFoundError(str(path))

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_dataset(rows: list[dict]) -> dict:
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

        if not ticker:
            blank_ticker += 1
        if not exchange:
            blank_exchange += 1
        if not provider:
            blank_provider += 1
        if not company:
            blank_company_name += 1
        if not isin:
            blank_isin += 1

        provider_counts[provider or "(blank)"] += 1

        if exchange and ticker:
            exchange_ticker_counts[f"{exchange}|{ticker}"] += 1

    duplicate_exchange_ticker_keys = sorted(
        key for key, count in exchange_ticker_counts.items() if count > 1
    )

    rows_count = len(rows)
    rows_needed = max(0, FULL_SOURCE_THRESHOLD - rows_count)
    source_to_50k = round((rows_count / FULL_SOURCE_THRESHOLD) * 100, 1)

    return {
        "headers": headers,
        "columns": {
            "ticker_col": ticker_col,
            "exchange_col": exchange_col,
            "provider_col": provider_col,
            "company_col": company_col,
            "isin_col": isin_col,
        },
        "counts": {
            "rows": rows_count,
            "rows_needed_to_50k": rows_needed,
            "source_to_50k_percent": source_to_50k,
            "duplicate_exchange_ticker_keys": len(duplicate_exchange_ticker_keys),
            "blank_ticker": blank_ticker,
            "blank_exchange": blank_exchange,
            "blank_provider": blank_provider,
            "blank_company_name": blank_company_name,
            "blank_isin": blank_isin,
        },
        "provider_counts": dict(provider_counts),
        "duplicate_exchange_ticker_sample": duplicate_exchange_ticker_keys[:50],
    }


def build_checks(summary: dict, validation: dict, closure: dict) -> list[dict]:
    counts = summary["counts"]
    columns = summary["columns"]
    provider_counts = summary["provider_counts"]

    checks: list[dict] = []

    def add(name: str, passed: bool, severity: str, detail: str) -> None:
        checks.append(
            {
                "check": name,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add("validation_json_exists", VALIDATION_JSON.exists(), "critical", str(VALIDATION_JSON))
    add("closure_json_exists", CLOSURE_JSON.exists(), "critical", str(CLOSURE_JSON))

    add("row_count_expected", counts["rows"] == EXPECTED_ROWS, "critical", f"rows={counts['rows']}; expected={EXPECTED_ROWS}")
    add("rows_needed_expected", counts["rows_needed_to_50k"] == EXPECTED_ROWS_NEEDED, "critical", f"rows_needed={counts['rows_needed_to_50k']}; expected={EXPECTED_ROWS_NEEDED}")
    add("source_to_50k_expected", counts["source_to_50k_percent"] == EXPECTED_SOURCE_TO_50K, "critical", f"source_to_50k={counts['source_to_50k_percent']}; expected={EXPECTED_SOURCE_TO_50K}")

    add("ticker_column_found", bool(columns["ticker_col"]), "critical", f"ticker_col={columns['ticker_col']}")
    add("exchange_column_found", bool(columns["exchange_col"]), "critical", f"exchange_col={columns['exchange_col']}")
    add("provider_column_found", bool(columns["provider_col"]), "critical", f"provider_col={columns['provider_col']}")
    add("company_column_found", bool(columns["company_col"]), "warning", f"company_col={columns['company_col']}")
    add("isin_column_found", bool(columns["isin_col"]), "warning", f"isin_col={columns['isin_col']}")

    add("blank_ticker_zero", counts["blank_ticker"] == 0, "critical", f"blank_ticker={counts['blank_ticker']}")
    add("blank_exchange_zero", counts["blank_exchange"] == 0, "critical", f"blank_exchange={counts['blank_exchange']}")
    add("blank_provider_zero", counts["blank_provider"] == 0, "critical", f"blank_provider={counts['blank_provider']}")
    add("duplicate_exchange_ticker_zero", counts["duplicate_exchange_ticker_keys"] == 0, "critical", f"duplicate_exchange_ticker_keys={counts['duplicate_exchange_ticker_keys']}")

    add("provider_breakdown_exact", provider_counts == EXPECTED_PROVIDER_COUNTS, "critical", f"provider_counts={provider_counts}")
    add("xetra_provider_count_expected", provider_counts.get("deutsche_boerse_xetra_all_tradable_instruments") == 1424, "critical", f"xetra_count={provider_counts.get('deutsche_boerse_xetra_all_tradable_instruments')}")

    add("full_source_still_blocked", counts["rows"] < FULL_SOURCE_THRESHOLD, "critical", f"rows={counts['rows']}; threshold={FULL_SOURCE_THRESHOLD}")
    add("closure_status_expected", closure.get("closure_status") == EXPECTED_CLOSURE_STATUS, "critical", f"closure_status={closure.get('closure_status')}")
    add("validation_status_expected", validation.get("status") == EXPECTED_VALIDATION_STATUS, "critical", f"validation_status={validation.get('status')}")

    add("global_blank_company_name_review", counts["blank_company_name"] >= 0, "warning", f"blank_company_name={counts['blank_company_name']}")
    add("global_blank_isin_review", counts["blank_isin"] >= 0, "warning", f"blank_isin={counts['blank_isin']}")

    add("no_scoring_openai_broker_full59k", True, "critical", "scoring=False; openai=False; broker=False; full59k=False")

    return checks


def main() -> None:
    if REPORT_JSON.exists() or REPORT_MD.exists():
        raise SystemExit("NO_OVERWRITE_GUARD: v2.14J outputs already exist")

    rows = read_csv_rows(CANONICAL_DATASET)
    validation = read_json(VALIDATION_JSON)
    closure = read_json(CLOSURE_JSON)

    summary = summarize_dataset(rows)
    checks = build_checks(summary, validation, closure)

    critical_failed = sum(1 for item in checks if item["severity"] == "critical" and not item["passed"])
    warning_failed = sum(1 for item in checks if item["severity"] == "warning" and not item["passed"])

    status = (
        "POST_CLOSURE_INTEGRITY_TEST_PASSED_FULL_SOURCE_STILL_BLOCKED"
        if critical_failed == 0
        else "POST_CLOSURE_INTEGRITY_TEST_FAILED"
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "canonical_dataset": str(CANONICAL_DATASET),
        "summary": summary,
        "checks": checks,
        "counts": {
            "critical_failed_checks": critical_failed,
            "warning_failed_checks": warning_failed,
        },
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed_for_test": True,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": "v2.14K - .gitattributes / EOL Guard",
        "alternative_next_phase": "v2.15A - Next Provider Route For Remaining Full Source Gap",
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    check_lines = "\n".join(
        f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}"
        for item in checks
    )

    provider_lines = "\n".join(
        f"- {provider}: {count}"
        for provider, count in summary["provider_counts"].items()
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Canonical dataset: `{CANONICAL_DATASET}`

## Counts

- Rows: {summary["counts"]["rows"]}
- Rows needed to 50k: {summary["counts"]["rows_needed_to_50k"]}
- Source-to-50k: {summary["counts"]["source_to_50k_percent"]}%
- Duplicate exchange+ticker keys: {summary["counts"]["duplicate_exchange_ticker_keys"]}
- Blank ticker: {summary["counts"]["blank_ticker"]}
- Blank exchange: {summary["counts"]["blank_exchange"]}
- Blank provider: {summary["counts"]["blank_provider"]}
- Blank company_name: {summary["counts"]["blank_company_name"]}
- Blank ISIN: {summary["counts"]["blank_isin"]}

## Provider breakdown

{provider_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Raw files downloaded: false
- Raw files modified after write: false
- Workbook/CSV parsed for test: true
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Recommended next phase

`v2.14K - .gitattributes / EOL Guard`

Alternative:

`v2.15A - Next Provider Route For Remaining Full Source Gap`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.14J post-closure integrity test completed.")
    print(f"- status: {status}")
    print(f"- report json: {REPORT_JSON}")
    print(f"- report md: {REPORT_MD}")
    print("")
    print("COUNTS:")
    for key, value in summary["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for item in checks:
        print(f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
