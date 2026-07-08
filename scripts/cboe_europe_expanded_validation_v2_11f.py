from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.11F"
PHASE = "Validate Expanded Source With Cboe Europe"
PHASE_TYPE = "validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

EXPANDED_IN = OUTPUT_DIR / "expanded_universe_v2_11e.csv"
CANDIDATES_IN = OUTPUT_DIR / "cboe_europe_normalized_candidates_v2_11e.csv"
EXCLUSIONS_IN = OUTPUT_DIR / "expanded_universe_exclusions_v2_11e.csv"
REBUILD_REPORT_IN = OUTPUT_DIR / "cboe_europe_rebuild_report_v2_11e.json"

VALIDATION_JSON = OUTPUT_DIR / "cboe_europe_expanded_validation_v2_11f.json"
VALIDATION_MD = OUTPUT_DIR / "cboe_europe_expanded_validation_report_v2_11f.md"
INTEGRITY_CHECKS_CSV = OUTPUT_DIR / "cboe_europe_expanded_integrity_checks_v2_11f.csv"
PROVIDER_BREAKDOWN_CSV = OUTPUT_DIR / "cboe_europe_provider_breakdown_v2_11f.csv"
COLUMN_QUALITY_CSV = OUTPUT_DIR / "cboe_europe_column_quality_v2_11f.csv"

FIRST_EXPANSION_THRESHOLD = 15000
FULL_SOURCE_THRESHOLD = 50000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        VALIDATION_JSON,
        VALIDATION_MD,
        INTEGRITY_CHECKS_CSV,
        PROVIDER_BREAKDOWN_CSV,
        COLUMN_QUALITY_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.11F outputs:\n"
            + "\n".join(existing)
        )


def read_csv_dicts(path: Path) -> tuple[list[dict], list[str]]:
    if not path.exists():
        raise SystemExit(f"MISSING_INPUT: {path}")

    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        headers = reader.fieldnames or []

    return rows, headers


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"MISSING_INPUT: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def find_col(headers: list[str], candidates: list[str]) -> str:
    lowered = {h.lower(): h for h in headers}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return ""


def cell(row: dict, col: str) -> str:
    if not col:
        return ""
    return str(row.get(col, "")).strip()


def count_duplicate_keys(rows: list[dict], exchange_col: str, ticker_col: str) -> tuple[int, int]:
    keys = []
    for row in rows:
        exchange = cell(row, exchange_col).upper()
        ticker = cell(row, ticker_col).upper()
        if exchange and ticker:
            keys.append((exchange, ticker))

    counts = Counter(keys)
    duplicate_keys = sum(1 for count in counts.values() if count > 1)
    duplicate_rows = sum(count - 1 for count in counts.values() if count > 1)

    return duplicate_keys, duplicate_rows


def provider_value(row: dict, provider_col: str, exchange_col: str) -> str:
    provider = cell(row, provider_col)
    exchange = cell(row, exchange_col)

    if provider:
        return provider

    if exchange == "CBOE_EUROPE":
        return "cboe_europe_reference_data"

    return "UNKNOWN_PROVIDER"


def build_provider_breakdown(rows: list[dict], provider_col: str, exchange_col: str) -> list[dict]:
    counter = Counter(provider_value(row, provider_col, exchange_col) for row in rows)

    return [
        {"provider": provider, "rows": count}
        for provider, count in sorted(counter.items())
    ]


def count_blank(rows: list[dict], col: str) -> int:
    if not col:
        return len(rows)
    return sum(1 for row in rows if not cell(row, col))


def build_column_quality(rows: list[dict], headers: list[str]) -> tuple[list[dict], dict]:
    column_groups = {
        "ticker": ["ticker", "symbol"],
        "exchange": ["exchange", "market"],
        "company_name": ["company_name", "name", "issuer_name", "security_name"],
        "provider": ["provider", "source", "source_provider"],
        "isin": ["isin", "isin_code"],
        "currency": ["currency", "trading_currency", "price_currency"],
        "mic": ["mic", "venue"],
        "asset_class": ["asset_class", "asset type", "security_type", "instrument_type"],
    }

    quality_rows = []
    resolved_cols = {}

    for logical_name, candidates in column_groups.items():
        col = find_col(headers, candidates)
        resolved_cols[logical_name] = col

        blank_count = count_blank(rows, col)
        non_blank_count = len(rows) - blank_count if col else 0

        quality_rows.append(
            {
                "logical_column": logical_name,
                "resolved_column": col,
                "exists": bool(col),
                "non_blank_rows": non_blank_count,
                "blank_rows": blank_count,
                "total_rows": len(rows),
            }
        )

    return quality_rows, resolved_cols


def detect_cboe_rows(rows: list[dict], provider_col: str, exchange_col: str) -> list[dict]:
    cboe_rows = []

    for row in rows:
        provider = cell(row, provider_col).lower()
        exchange = cell(row, exchange_col).upper()

        if provider == "cboe_europe_reference_data" or exchange == "CBOE_EUROPE":
            cboe_rows.append(row)

    return cboe_rows


def add_check(checks: list[dict], name: str, expected: str, actual: str, passed: bool, severity: str) -> None:
    checks.append(
        {
            "check_name": name,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "severity": severity,
        }
    )


def main() -> None:
    no_overwrite_guard()

    expanded_rows, expanded_headers = read_csv_dicts(EXPANDED_IN)
    candidate_rows, candidate_headers = read_csv_dicts(CANDIDATES_IN)
    exclusion_rows, exclusion_headers = read_csv_dicts(EXCLUSIONS_IN)
    rebuild_report = read_json(REBUILD_REPORT_IN)

    rebuild_counts = rebuild_report.get("counts", {})

    expected_baseline_rows = int(rebuild_counts.get("baseline_rows", 0))
    expected_cboe_added = int(rebuild_counts.get("cboe_rows_added", 0))
    expected_new_expanded_rows = int(rebuild_counts.get("new_expanded_rows", 0))
    expected_duplicate_keys = int(rebuild_counts.get("duplicate_exchange_ticker_keys", -1))

    quality_rows, resolved_cols = build_column_quality(expanded_rows, expanded_headers)

    ticker_col = resolved_cols["ticker"]
    exchange_col = resolved_cols["exchange"]
    company_col = resolved_cols["company_name"]
    provider_col = resolved_cols["provider"]
    isin_col = resolved_cols["isin"]
    currency_col = resolved_cols["currency"]
    mic_col = resolved_cols["mic"]

    provider_breakdown_rows = build_provider_breakdown(expanded_rows, provider_col, exchange_col)
    cboe_rows = detect_cboe_rows(expanded_rows, provider_col, exchange_col)

    duplicate_exchange_ticker_keys, duplicate_exchange_ticker_rows = count_duplicate_keys(
        expanded_rows,
        exchange_col,
        ticker_col,
    )

    accepted_candidate_rows = [
        row for row in candidate_rows
        if str(row.get("decision", "")).strip() == "ACCEPTED_FOR_REBUILD_CANDIDATE"
    ]

    actual_rows = len(expanded_rows)
    actual_cboe_rows = len(cboe_rows)
    actual_exclusion_rows = len(exclusion_rows)

    first_expansion_unlocked = actual_rows >= FIRST_EXPANSION_THRESHOLD
    full_source_unlocked = actual_rows >= FULL_SOURCE_THRESHOLD

    rows_needed_full_source = max(FULL_SOURCE_THRESHOLD - actual_rows, 0)

    checks: list[dict] = []

    add_check(
        checks,
        "expanded_row_count_matches_rebuild_report",
        str(expected_new_expanded_rows),
        str(actual_rows),
        actual_rows == expected_new_expanded_rows,
        "critical",
    )

    add_check(
        checks,
        "cboe_added_rows_match_rebuild_report",
        str(expected_cboe_added),
        str(actual_cboe_rows),
        actual_cboe_rows == expected_cboe_added,
        "critical",
    )

    add_check(
        checks,
        "accepted_candidates_match_cboe_rows",
        str(len(accepted_candidate_rows)),
        str(actual_cboe_rows),
        len(accepted_candidate_rows) == actual_cboe_rows,
        "critical",
    )

    add_check(
        checks,
        "duplicate_exchange_ticker_keys",
        "0",
        str(duplicate_exchange_ticker_keys),
        duplicate_exchange_ticker_keys == 0,
        "critical",
    )

    add_check(
        checks,
        "duplicate_exchange_ticker_rows",
        "0",
        str(duplicate_exchange_ticker_rows),
        duplicate_exchange_ticker_rows == 0,
        "critical",
    )

    add_check(
        checks,
        "first_expansion_threshold_unlocked",
        "True",
        str(first_expansion_unlocked),
        first_expansion_unlocked is True,
        "critical",
    )

    add_check(
        checks,
        "full_source_threshold_remains_blocked",
        "False",
        str(full_source_unlocked),
        full_source_unlocked is False,
        "info",
    )

    add_check(
        checks,
        "ticker_column_exists",
        "exists",
        ticker_col or "MISSING",
        bool(ticker_col),
        "critical",
    )

    add_check(
        checks,
        "exchange_column_exists",
        "exists",
        exchange_col or "MISSING",
        bool(exchange_col),
        "critical",
    )

    add_check(
        checks,
        "company_name_column_exists",
        "exists",
        company_col or "MISSING",
        bool(company_col),
        "critical",
    )

    add_check(
        checks,
        "blank_ticker_rows",
        "0",
        str(count_blank(expanded_rows, ticker_col)),
        count_blank(expanded_rows, ticker_col) == 0,
        "critical",
    )

    add_check(
        checks,
        "blank_exchange_rows",
        "0",
        str(count_blank(expanded_rows, exchange_col)),
        count_blank(expanded_rows, exchange_col) == 0,
        "critical",
    )

    add_check(
        checks,
        "blank_company_name_rows",
        "0",
        str(count_blank(expanded_rows, company_col)),
        count_blank(expanded_rows, company_col) == 0,
        "warning",
    )

    critical_failures = [
        check for check in checks
        if check["severity"] == "critical" and not check["passed"]
    ]

    warning_failures = [
        check for check in checks
        if check["severity"] == "warning" and not check["passed"]
    ]

    if critical_failures:
        decision = "CBOE_EUROPE_EXPANDED_SOURCE_VALIDATION_FAILED"
        recommended_next_phase = "FIX_V2_11E_OR_CLOSE_WITH_FAILURE"
        validation_passed = False
    else:
        decision = "CBOE_EUROPE_EXPANDED_SOURCE_VALIDATED_FIRST_EXPANSION_READY"
        recommended_next_phase = "v2.11G_CBOE_EUROPE_CLOSURE_REPORT"
        validation_passed = True

    validation = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "CBOE_EUROPE_EXPANDED_VALIDATION_COMPLETED",
        "generated_at_utc": utc_now(),
        "decision": {
            "decision": decision,
            "validation_passed": validation_passed,
            "recommended_next_phase": recommended_next_phase,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_full_source": rows_needed_full_source,
        },
        "hard_guards": {
            "network_download_performed": False,
            "raw_files_modified": False,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "inputs": {
            "expanded_universe": str(EXPANDED_IN),
            "candidates": str(CANDIDATES_IN),
            "exclusions": str(EXCLUSIONS_IN),
            "rebuild_report": str(REBUILD_REPORT_IN),
        },
        "counts": {
            "expected_baseline_rows_from_v2_11e": expected_baseline_rows,
            "expected_cboe_added_from_v2_11e": expected_cboe_added,
            "expected_expanded_rows_from_v2_11e": expected_new_expanded_rows,
            "actual_expanded_rows": actual_rows,
            "actual_cboe_rows_detected": actual_cboe_rows,
            "accepted_candidate_rows": len(accepted_candidate_rows),
            "actual_exclusion_rows": actual_exclusion_rows,
            "duplicate_exchange_ticker_keys": duplicate_exchange_ticker_keys,
            "duplicate_exchange_ticker_rows": duplicate_exchange_ticker_rows,
            "first_expansion_threshold": FIRST_EXPANSION_THRESHOLD,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_full_source": rows_needed_full_source,
            "critical_failures": len(critical_failures),
            "warning_failures": len(warning_failures),
        },
        "resolved_columns": resolved_cols,
        "checks": checks,
        "provider_breakdown": provider_breakdown_rows,
        "column_quality": quality_rows,
    }

    write_json(VALIDATION_JSON, validation)

    write_csv(
        INTEGRITY_CHECKS_CSV,
        checks,
        ["check_name", "expected", "actual", "passed", "severity"],
    )

    write_csv(
        PROVIDER_BREAKDOWN_CSV,
        provider_breakdown_rows,
        ["provider", "rows"],
    )

    write_csv(
        COLUMN_QUALITY_CSV,
        quality_rows,
        ["logical_column", "resolved_column", "exists", "non_blank_rows", "blank_rows", "total_rows"],
    )

    failed_checks_md = "\n".join(
        f"- {check['check_name']}: expected `{check['expected']}`, actual `{check['actual']}`, severity={check['severity']}"
        for check in checks
        if not check["passed"]
    ) or "- None"

    provider_breakdown_md = "\n".join(
        f"- {row['provider']}: {row['rows']}"
        for row in provider_breakdown_rows
    )

    md = f"""# {VERSION} - {PHASE}

Status: **CBOE_EUROPE_EXPANDED_VALIDATION_COMPLETED**

Phase type: **validation-only**

Generated at UTC: `{validation["generated_at_utc"]}`

## Hard guards

- Network download performed: false
- Raw files modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Inputs

- Expanded universe: `{EXPANDED_IN}`
- Candidates: `{CANDIDATES_IN}`
- Exclusions: `{EXCLUSIONS_IN}`
- Rebuild report: `{REBUILD_REPORT_IN}`

## Counts

- Expected baseline rows from v2.11E: {expected_baseline_rows}
- Expected Cboe rows added from v2.11E: {expected_cboe_added}
- Expected expanded rows from v2.11E: {expected_new_expanded_rows}
- Actual expanded rows: {actual_rows}
- Actual Cboe rows detected: {actual_cboe_rows}
- Accepted candidate rows: {len(accepted_candidate_rows)}
- Actual exclusion rows: {actual_exclusion_rows}
- Duplicate exchange+ticker keys: {duplicate_exchange_ticker_keys}
- Duplicate exchange+ticker rows: {duplicate_exchange_ticker_rows}

## Thresholds

- First expansion threshold: {FIRST_EXPANSION_THRESHOLD}
- First expansion unlocked: {first_expansion_unlocked}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Full source unlocked: {full_source_unlocked}
- Rows still needed for full source: {rows_needed_full_source}

## Provider breakdown

{provider_breakdown_md}

## Failed checks

{failed_checks_md}

## Decision

- Decision: **{decision}**
- Validation passed: **{validation_passed}**
- Recommended next phase: **{recommended_next_phase}**

## Important scope note

v2.11F validates the rebuilt expanded source only.

It does not rebuild, score, call OpenAI, call broker APIs, or launch the full 59k universe.

## Outputs

- `{VALIDATION_JSON}`
- `{VALIDATION_MD}`
- `{INTEGRITY_CHECKS_CSV}`
- `{PROVIDER_BREAKDOWN_CSV}`
- `{COLUMN_QUALITY_CSV}`
"""

    VALIDATION_MD.write_text(md, encoding="utf-8")

    print("v2.11F validation-only completed.")
    print(f"- validation json: {VALIDATION_JSON}")
    print(f"- validation report: {VALIDATION_MD}")
    print(f"- integrity checks: {INTEGRITY_CHECKS_CSV}")
    print(f"- provider breakdown: {PROVIDER_BREAKDOWN_CSV}")
    print(f"- column quality: {COLUMN_QUALITY_CSV}")
    print("")
    print("DECISION:")
    for key, value in validation["decision"].items():
        print(f"- {key}: {value}")
    print("")
    print("COUNTS:")
    for key, value in validation["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in validation["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
