from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.6D"
METHOD = "sec_company_tickers_exchange_validation_v1"

PROVIDER_ID = "sec_company_tickers_exchange"

SEC_CSV = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID / "sec_company_tickers_exchange.csv"
SEC_RAW_JSON = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID / "company_tickers_exchange.json"

EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_4b.csv"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "sec_company_tickers_exchange_validation_v2_6d.json"
OUT_MD = OUT_DIR / "sec_company_tickers_exchange_validation_v2_6d.md"
OUT_EXCHANGE_BREAKDOWN_CSV = OUT_DIR / "sec_company_tickers_exchange_validation_exchange_breakdown_v2_6d.csv"
OUT_OVERLAP_CSV = OUT_DIR / "sec_company_tickers_exchange_validation_overlap_sample_v2_6d.csv"
OUT_NEW_SAMPLE_CSV = OUT_DIR / "sec_company_tickers_exchange_validation_new_sample_v2_6d.csv"
OUT_EXCLUSION_SAMPLE_CSV = OUT_DIR / "sec_company_tickers_exchange_validation_exclusion_sample_v2_6d.csv"

ACQUISITION_JSON = OUT_DIR / "sec_company_tickers_exchange_acquisition_real_v2_6c.json"

REQUIRED_SEC_COLUMNS = [
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
    "raw_cik",
    "raw_exchange",
]

PRIMARY_EXCHANGES = {"NASDAQ", "NYSE", "CBOE"}
EXCLUDED_OR_ENRICHMENT_EXCHANGES = {"OTC", "None", ""}

CURRENT_INCLUDED_ROWS = 5648
TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000


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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm_ticker(value: str) -> str:
    return (value or "").strip().upper()


def norm_exchange(value: str) -> str:
    return (value or "").strip()


def key_exchange_ticker(row: dict[str, str]) -> tuple[str, str]:
    return (norm_exchange(row.get("exchange", "")), norm_ticker(row.get("ticker", "")))


def key_ticker_only(row: dict[str, str]) -> str:
    return norm_ticker(row.get("ticker", ""))


def classify_sec_row(row: dict[str, str]) -> str:
    exchange = norm_exchange(row.get("exchange", ""))

    if exchange in PRIMARY_EXCHANGES:
        return "PRIMARY_EXCHANGE_CANDIDATE"

    if exchange in EXCLUDED_OR_ENRICHMENT_EXCHANGES:
        return "ENRICHMENT_OR_EXCLUSION_CANDIDATE"

    return "UNKNOWN_EXCHANGE_REVIEW_REQUIRED"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    acquisition = read_json(ACQUISITION_JSON)

    if not acquisition.get("_exists"):
        blockers.append(f"Missing v2.6C acquisition artifact: {rel(ACQUISITION_JSON)}")
    else:
        positives.append(f"v2.6C acquisition artifact found: {rel(ACQUISITION_JSON)}")

    acquisition_status = acquisition.get("acquisition_status")
    if acquisition_status == "SEC_COMPANY_TICKERS_EXCHANGE_ACQUISITION_COMPLETED":
        positives.append(f"v2.6C acquisition status accepted: {acquisition_status}")
    else:
        blockers.append(f"Unexpected v2.6C acquisition status: {acquisition_status}")

    if not SEC_RAW_JSON.exists():
        blockers.append(f"Missing SEC raw JSON: {rel(SEC_RAW_JSON)}")
    else:
        positives.append(f"SEC raw JSON found: {rel(SEC_RAW_JSON)}")

    sec_rows = read_csv(SEC_CSV)
    expanded_rows = read_csv(EXPANDED_CSV)

    if not sec_rows:
        blockers.append(f"SEC normalized CSV missing or empty: {rel(SEC_CSV)}")
        sec_columns: list[str] = []
    else:
        positives.append(f"SEC normalized CSV found: {rel(SEC_CSV)}")
        sec_columns = list(sec_rows[0].keys())

    if not expanded_rows:
        blockers.append(f"Expanded universe CSV missing or empty: {rel(EXPANDED_CSV)}")
        expanded_columns: list[str] = []
    else:
        positives.append(f"Expanded universe CSV found: {rel(EXPANDED_CSV)}")
        expanded_columns = list(expanded_rows[0].keys())

    missing_sec_columns = [col for col in REQUIRED_SEC_COLUMNS if col not in sec_columns]
    if missing_sec_columns:
        blockers.append(f"Missing required SEC columns: {missing_sec_columns}")
    elif sec_rows:
        positives.append("SEC canonical schema validated.")

    sec_row_count = len(sec_rows)
    expanded_row_count = len(expanded_rows)

    exchange_counts: Counter[str] = Counter()
    classification_counts: Counter[str] = Counter()
    empty_counts = {
        "ticker": 0,
        "company_name": 0,
        "exchange": 0,
        "raw_cik": 0,
        "source_provider": 0,
    }

    sec_key_counter: Counter[tuple[str, str]] = Counter()
    sec_ticker_counter: Counter[str] = Counter()

    primary_exchange_rows: list[dict[str, str]] = []
    enrichment_or_exclusion_rows: list[dict[str, str]] = []
    unknown_exchange_rows: list[dict[str, str]] = []

    for row in sec_rows:
        exchange = norm_exchange(row.get("exchange", ""))
        ticker = norm_ticker(row.get("ticker", ""))
        classification = classify_sec_row(row)

        exchange_counts[exchange] += 1
        classification_counts[classification] += 1

        if not ticker:
            empty_counts["ticker"] += 1
        if not (row.get("company_name") or "").strip():
            empty_counts["company_name"] += 1
        if not exchange:
            empty_counts["exchange"] += 1
        if not (row.get("raw_cik") or "").strip():
            empty_counts["raw_cik"] += 1
        if (row.get("source_provider") or "").strip() != PROVIDER_ID:
            empty_counts["source_provider"] += 1

        if ticker and exchange:
            sec_key_counter[(exchange, ticker)] += 1
        if ticker:
            sec_ticker_counter[ticker] += 1

        if classification == "PRIMARY_EXCHANGE_CANDIDATE":
            primary_exchange_rows.append(row)
        elif classification == "ENRICHMENT_OR_EXCLUSION_CANDIDATE":
            enrichment_or_exclusion_rows.append(row)
        else:
            unknown_exchange_rows.append(row)

    duplicate_exchange_ticker_keys = {
        f"{exchange}|{ticker}": count
        for (exchange, ticker), count in sec_key_counter.items()
        if count > 1
    }

    duplicate_ticker_only = {
        ticker: count for ticker, count in sec_ticker_counter.items() if count > 1
    }

    expanded_keys = {key_exchange_ticker(row) for row in expanded_rows if key_exchange_ticker(row)[0] and key_exchange_ticker(row)[1]}
    expanded_tickers = {key_ticker_only(row) for row in expanded_rows if key_ticker_only(row)}

    sec_keys = {key_exchange_ticker(row) for row in sec_rows if key_exchange_ticker(row)[0] and key_exchange_ticker(row)[1]}
    sec_tickers = {key_ticker_only(row) for row in sec_rows if key_ticker_only(row)}

    overlap_by_exchange_ticker = sec_keys & expanded_keys
    new_by_exchange_ticker = sec_keys - expanded_keys

    overlap_by_ticker = sec_tickers & expanded_tickers
    new_by_ticker = sec_tickers - expanded_tickers

    primary_keys = {key_exchange_ticker(row) for row in primary_exchange_rows if key_exchange_ticker(row)[0] and key_exchange_ticker(row)[1]}
    primary_new_keys = primary_keys - expanded_keys

    primary_tickers = {key_ticker_only(row) for row in primary_exchange_rows if key_ticker_only(row)}
    primary_new_tickers = primary_tickers - expanded_tickers

    for field, count in empty_counts.items():
        if count:
            warnings.append(f"Empty or invalid {field} count: {count}")

    if duplicate_exchange_ticker_keys:
        warnings.append(f"Duplicate SEC exchange+ticker keys: {len(duplicate_exchange_ticker_keys)}")
    else:
        positives.append("No duplicate SEC exchange+ticker keys detected.")

    if unknown_exchange_rows:
        warnings.append(f"Unknown exchange rows require review: {len(unknown_exchange_rows)}")

    if enrichment_or_exclusion_rows:
        warnings.append(f"OTC/None/blank SEC rows should be treated as enrichment or exclusion candidates: {len(enrichment_or_exclusion_rows)}")

    if primary_exchange_rows:
        positives.append(f"Primary exchange SEC candidates detected: {len(primary_exchange_rows)}")

    exchange_breakdown_rows = []
    for exchange, count in exchange_counts.most_common():
        exchange_breakdown_rows.append(
            {
                "exchange": exchange,
                "row_count": count,
                "route_classification": (
                    "PRIMARY_EXCHANGE_CANDIDATE"
                    if exchange in PRIMARY_EXCHANGES
                    else "ENRICHMENT_OR_EXCLUSION_CANDIDATE"
                    if exchange in EXCLUDED_OR_ENRICHMENT_EXCHANGES
                    else "UNKNOWN_EXCHANGE_REVIEW_REQUIRED"
                ),
            }
        )

    write_csv(
        OUT_EXCHANGE_BREAKDOWN_CSV,
        exchange_breakdown_rows,
        ["exchange", "row_count", "route_classification"],
    )

    overlap_sample = []
    new_sample = []
    exclusion_sample = []

    for row in sec_rows:
        key = key_exchange_ticker(row)
        ticker = key_ticker_only(row)
        sample_row = {
            "ticker": ticker,
            "company_name": row.get("company_name", ""),
            "exchange": row.get("exchange", ""),
            "raw_cik": row.get("raw_cik", ""),
            "sec_classification": classify_sec_row(row),
        }

        if key in overlap_by_exchange_ticker and len(overlap_sample) < 100:
            overlap_sample.append(sample_row)

        if key in new_by_exchange_ticker and classify_sec_row(row) == "PRIMARY_EXCHANGE_CANDIDATE" and len(new_sample) < 100:
            new_sample.append(sample_row)

        if classify_sec_row(row) == "ENRICHMENT_OR_EXCLUSION_CANDIDATE" and len(exclusion_sample) < 100:
            exclusion_sample.append(sample_row)

    sample_fields = ["ticker", "company_name", "exchange", "raw_cik", "sec_classification"]
    write_csv(OUT_OVERLAP_CSV, overlap_sample, sample_fields)
    write_csv(OUT_NEW_SAMPLE_CSV, new_sample, sample_fields)
    write_csv(OUT_EXCLUSION_SAMPLE_CSV, exclusion_sample, sample_fields)

    sec_primary_candidate_rows = len(primary_exchange_rows)
    sec_enrichment_or_exclusion_rows = len(enrichment_or_exclusion_rows)
    sec_unknown_exchange_rows = len(unknown_exchange_rows)

    max_possible_rows_after_primary_sec_merge = expanded_row_count + len(primary_new_keys)
    rows_needed_first_expansion_after_primary_sec = max(TARGET_FIRST_EXPANSION_ROWS - max_possible_rows_after_primary_sec_merge, 0)
    rows_needed_full_source_after_primary_sec = max(MIN_FULL_SOURCE_ROWS - max_possible_rows_after_primary_sec_merge, 0)

    if blockers:
        validation_status = "SEC_COMPANY_TICKERS_EXCHANGE_VALIDATION_BLOCKED"
        readiness_score = 0
        sec_route_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        if sec_primary_candidate_rows > 0 and len(primary_new_keys) > 0:
            validation_status = "SEC_COMPANY_TICKERS_EXCHANGE_VALIDATED_WITH_PRIMARY_CANDIDATES"
            readiness_score = 85
            sec_route_decision = "USABLE_AS_PARTIAL_PROVIDER_AND_IDENTIFIER_ENRICHMENT"
            recommended_next_phase = "v2.6E ? SEC Incremental Coverage Analysis"
        elif sec_primary_candidate_rows > 0:
            validation_status = "SEC_COMPANY_TICKERS_EXCHANGE_VALIDATED_ENRICHMENT_ONLY"
            readiness_score = 75
            sec_route_decision = "USABLE_AS_IDENTIFIER_ENRICHMENT_ONLY"
            recommended_next_phase = "v2.6E ? SEC Incremental Coverage Analysis"
        else:
            validation_status = "SEC_COMPANY_TICKERS_EXCHANGE_VALIDATED_NOT_USEFUL_FOR_PRIMARY_UNIVERSE"
            readiness_score = 60
            sec_route_decision = "NOT_USEFUL_FOR_PRIMARY_UNIVERSE"
            recommended_next_phase = "v2.8A ? Cboe Listed Symbols Route Plan"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "sec_route_decision": sec_route_decision,
        "recommended_next_phase": recommended_next_phase,
        "inputs": {
            "sec_csv": rel(SEC_CSV),
            "sec_raw_json": rel(SEC_RAW_JSON),
            "expanded_universe_csv": rel(EXPANDED_CSV),
            "acquisition_json": rel(ACQUISITION_JSON),
        },
        "schema": {
            "required_sec_columns": REQUIRED_SEC_COLUMNS,
            "detected_sec_columns": sec_columns,
            "missing_sec_columns": missing_sec_columns,
            "detected_expanded_columns": expanded_columns,
        },
        "summary": {
            "sec_rows": sec_row_count,
            "expanded_rows": expanded_row_count,
            "sec_primary_candidate_rows": sec_primary_candidate_rows,
            "sec_enrichment_or_exclusion_rows": sec_enrichment_or_exclusion_rows,
            "sec_unknown_exchange_rows": sec_unknown_exchange_rows,
            "sec_exchange_counts": dict(exchange_counts),
            "sec_classification_counts": dict(classification_counts),
            "empty_counts": empty_counts,
            "duplicate_exchange_ticker_keys": len(duplicate_exchange_ticker_keys),
            "duplicate_ticker_only": len(duplicate_ticker_only),
            "overlap_by_exchange_ticker": len(overlap_by_exchange_ticker),
            "new_by_exchange_ticker": len(new_by_exchange_ticker),
            "overlap_by_ticker": len(overlap_by_ticker),
            "new_by_ticker": len(new_by_ticker),
            "primary_new_exchange_ticker_keys": len(primary_new_keys),
            "primary_new_tickers": len(primary_new_tickers),
            "max_possible_rows_after_primary_sec_merge": max_possible_rows_after_primary_sec_merge,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "rows_needed_first_expansion_after_primary_sec": rows_needed_first_expansion_after_primary_sec,
            "rows_needed_full_source_after_primary_sec": rows_needed_full_source_after_primary_sec,
        },
        "outputs": {
            "exchange_breakdown_csv": rel(OUT_EXCHANGE_BREAKDOWN_CSV),
            "overlap_sample_csv": rel(OUT_OVERLAP_CSV),
            "new_sample_csv": rel(OUT_NEW_SAMPLE_CSV),
            "exclusion_sample_csv": rel(OUT_EXCLUSION_SAMPLE_CSV),
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
        },
        "recommendation": (
            "Proceed to v2.6E to quantify incremental coverage and decide whether a controlled rebuild plan is justified."
            if not blockers
            else "Resolve blockers before incremental coverage analysis."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.6D SEC Company Tickers Exchange Validation")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- SEC route decision: **{sec_route_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Inputs")
    md.append("")
    md.append(f"- SEC CSV: `{rel(SEC_CSV)}`")
    md.append(f"- SEC raw JSON: `{rel(SEC_RAW_JSON)}`")
    md.append(f"- Expanded universe CSV: `{rel(EXPANDED_CSV)}`")
    md.append("")
    md.append("## Row summary")
    md.append("")
    md.append(f"- SEC rows: {sec_row_count}")
    md.append(f"- Expanded universe rows: {expanded_row_count}")
    md.append(f"- SEC primary exchange candidate rows: {sec_primary_candidate_rows}")
    md.append(f"- SEC enrichment/exclusion candidate rows: {sec_enrichment_or_exclusion_rows}")
    md.append(f"- SEC unknown exchange rows: {sec_unknown_exchange_rows}")
    md.append("")
    md.append("## SEC exchange counts")
    md.append("")
    for exchange, count in exchange_counts.most_common():
        md.append(f"- {exchange}: {count}")
    md.append("")
    md.append("## Overlap and new coverage")
    md.append("")
    md.append(f"- Overlap by exchange+ticker: {len(overlap_by_exchange_ticker)}")
    md.append(f"- New by exchange+ticker: {len(new_by_exchange_ticker)}")
    md.append(f"- Overlap by ticker only: {len(overlap_by_ticker)}")
    md.append(f"- New by ticker only: {len(new_by_ticker)}")
    md.append(f"- Primary new exchange+ticker keys: {len(primary_new_keys)}")
    md.append(f"- Primary new tickers: {len(primary_new_tickers)}")
    md.append("")
    md.append("## Rebuild impact estimate")
    md.append("")
    md.append(f"- Current expanded rows: {expanded_row_count}")
    md.append(f"- Max possible rows after primary SEC merge: {max_possible_rows_after_primary_sec_merge}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Rows still needed for first expansion after primary SEC merge: {rows_needed_first_expansion_after_primary_sec}")
    md.append(f"- Rows still needed for full-source after primary SEC merge: {rows_needed_full_source_after_primary_sec}")
    md.append("")
    md.append("## Data quality")
    md.append("")
    md.append(f"- Missing SEC columns: {missing_sec_columns}")
    md.append(f"- Empty ticker: {empty_counts['ticker']}")
    md.append(f"- Empty company_name: {empty_counts['company_name']}")
    md.append(f"- Empty exchange: {empty_counts['exchange']}")
    md.append(f"- Empty raw_cik: {empty_counts['raw_cik']}")
    md.append(f"- Invalid source_provider: {empty_counts['source_provider']}")
    md.append(f"- Duplicate exchange+ticker keys: {len(duplicate_exchange_ticker_keys)}")
    md.append(f"- Duplicate ticker-only values: {len(duplicate_ticker_only)}")
    md.append("")
    md.append("## Outputs")
    md.append("")
    md.append(f"- Exchange breakdown CSV: `{rel(OUT_EXCHANGE_BREAKDOWN_CSV)}`")
    md.append(f"- Overlap sample CSV: `{rel(OUT_OVERLAP_CSV)}`")
    md.append(f"- New sample CSV: `{rel(OUT_NEW_SAMPLE_CSV)}`")
    md.append(f"- Exclusion sample CSV: `{rel(OUT_EXCLUSION_SAMPLE_CSV)}`")
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
    md.append("Important: v2.6D is a validation-only step. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.6D SEC Company Tickers Exchange Validation")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   SEC route decision: {sec_route_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   SEC rows: {sec_row_count}")
    print(f"OK   Expanded rows: {expanded_row_count}")
    print(f"OK   SEC primary candidate rows: {sec_primary_candidate_rows}")
    print(f"OK   SEC enrichment/exclusion rows: {sec_enrichment_or_exclusion_rows}")
    print(f"OK   SEC unknown exchange rows: {sec_unknown_exchange_rows}")
    print(f"OK   Overlap exchange+ticker: {len(overlap_by_exchange_ticker)}")
    print(f"OK   New exchange+ticker: {len(new_by_exchange_ticker)}")
    print(f"OK   Primary new exchange+ticker keys: {len(primary_new_keys)}")
    print(f"OK   Max possible rows after primary SEC merge: {max_possible_rows_after_primary_sec_merge}")
    print(f"OK   Rows still needed first expansion: {rows_needed_first_expansion_after_primary_sec}")
    print(f"OK   Rows still needed full source: {rows_needed_full_source_after_primary_sec}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
