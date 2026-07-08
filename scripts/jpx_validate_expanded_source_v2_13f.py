from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.13F"
PHASE = "Validate Expanded Source With JPX"
PHASE_TYPE = "validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

BASELINE_EXPANDED = OUTPUT_DIR / "expanded_universe_v2_12e.csv"
EXPANDED_INPUT = OUTPUT_DIR / "expanded_universe_v2_13e.csv"
REBUILD_JSON = OUTPUT_DIR / "jpx_rebuild_summary_v2_13e.json"
REBUILD_DECISION_CSV = OUTPUT_DIR / "jpx_rebuild_decision_v2_13e.csv"
ACCEPTED_ROWS_CSV = OUTPUT_DIR / "jpx_accepted_rows_v2_13e.csv"
EXCLUDED_ROWS_CSV = OUTPUT_DIR / "jpx_excluded_rows_v2_13e.csv"

VALIDATION_JSON = OUTPUT_DIR / "jpx_expanded_validation_v2_13f.json"
VALIDATION_MD = OUTPUT_DIR / "jpx_expanded_validation_report_v2_13f.md"
CHECKS_CSV = OUTPUT_DIR / "jpx_expanded_validation_checks_v2_13f.csv"
PROVIDER_BREAKDOWN_CSV = OUTPUT_DIR / "provider_breakdown_validation_v2_13f.csv"
DUPLICATE_KEYS_CSV = OUTPUT_DIR / "jpx_duplicate_exchange_ticker_keys_v2_13f.csv"
JPX_SAMPLE_CSV = OUTPUT_DIR / "jpx_rows_sample_v2_13f.csv"
BLANK_FIELDS_CSV = OUTPUT_DIR / "jpx_blank_field_diagnostics_v2_13f.csv"

EXPECTED_BASELINE_ROWS = 33158
EXPECTED_JPX_ROWS_ADDED = 3705
EXPECTED_JPX_ROWS_EXCLUDED = 732
EXPECTED_EXPANDED_ROWS = 36863
FULL_SOURCE_THRESHOLD = 50000

JPX_PROVIDER = "jpx_listed_securities"
JPX_EXCHANGE = "JPX"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        VALIDATION_JSON,
        VALIDATION_MD,
        CHECKS_CSV,
        PROVIDER_BREAKDOWN_CSV,
        DUPLICATE_KEYS_CSV,
        JPX_SAMPLE_CSV,
        BLANK_FIELDS_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.13F outputs:\n"
            + "\n".join(existing)
        )


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_header_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]

    if not fieldnames:
        raise SystemExit(f"CSV has no header: {path}")

    return fieldnames, rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def find_field(fieldnames: list[str], candidates: list[str]) -> str | None:
    lower_map = {field.lower(): field for field in fieldnames}

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    for field in fieldnames:
        normalized = normalize_header_key(field)
        for candidate in candidates:
            if normalize_header_key(candidate) == normalized:
                return field

    return None


def provider_value(row: dict, provider_field: str | None, source_field: str | None) -> str:
    if provider_field:
        value = normalize_text(row.get(provider_field, ""))
        if value:
            return value

    if source_field:
        value = normalize_text(row.get(source_field, ""))
        if value:
            return value

    return "UNKNOWN"


def bool_text(value: bool) -> str:
    return "True" if bool(value) else "False"


def add_check(
    checks: list[dict],
    *,
    name: str,
    severity: str,
    expected: object,
    actual: object,
    passed: bool,
    note: str = "",
) -> None:
    checks.append(
        {
            "check_name": name,
            "severity": severity,
            "expected": str(expected),
            "actual": str(actual),
            "passed": bool_text(passed),
            "note": note,
        }
    )


def main() -> None:
    no_overwrite_guard()

    rebuild = read_json(REBUILD_JSON)

    baseline_fieldnames, baseline_rows = read_csv(BASELINE_EXPANDED)
    expanded_fieldnames, expanded_rows = read_csv(EXPANDED_INPUT)
    accepted_fieldnames, accepted_rows = read_csv(ACCEPTED_ROWS_CSV)
    excluded_fieldnames, excluded_rows = read_csv(EXCLUDED_ROWS_CSV)

    if baseline_fieldnames != expanded_fieldnames:
        schema_match = False
    else:
        schema_match = True

    ticker_field = find_field(expanded_fieldnames, ["ticker", "symbol"])
    exchange_field = find_field(expanded_fieldnames, ["exchange"])
    company_field = find_field(expanded_fieldnames, ["company_name", "name", "security_name"])
    provider_field = find_field(expanded_fieldnames, ["source_provider", "provider", "data_provider"])
    source_field = find_field(expanded_fieldnames, ["source"])
    country_field = find_field(expanded_fieldnames, ["country", "country_code"])
    currency_field = find_field(expanded_fieldnames, ["currency"])
    market_segment_field = find_field(expanded_fieldnames, ["market_segment", "market"])

    if not ticker_field:
        raise SystemExit("EXPANDED_SCHEMA_ERROR: could not identify ticker/symbol field")
    if not exchange_field:
        raise SystemExit("EXPANDED_SCHEMA_ERROR: could not identify exchange field")
    if not company_field:
        raise SystemExit("EXPANDED_SCHEMA_ERROR: could not identify company/name field")

    duplicate_counter: Counter[tuple[str, str]] = Counter()
    blank_diagnostics_counter: Counter[tuple[str, str]] = Counter()
    provider_counter: Counter[str] = Counter()

    duplicate_rows = []

    for index, row in enumerate(expanded_rows, start=2):
        ticker = normalize_text(row.get(ticker_field, "")).upper()
        exchange = normalize_text(row.get(exchange_field, "")).upper()
        company = normalize_text(row.get(company_field, ""))
        provider = provider_value(row, provider_field, source_field)

        provider_counter[provider] += 1

        if not ticker:
            blank_diagnostics_counter[(provider, "blank_ticker")] += 1
        if not exchange:
            blank_diagnostics_counter[(provider, "blank_exchange")] += 1
        if not company:
            blank_diagnostics_counter[(provider, "blank_company_name")] += 1

        if ticker and exchange:
            duplicate_counter[(exchange, ticker)] += 1

    for (exchange, ticker), count in duplicate_counter.items():
        if count > 1:
            duplicate_rows.append(
                {
                    "exchange": exchange,
                    "ticker": ticker,
                    "count": count,
                }
            )

    jpx_rows = [
        row
        for row in expanded_rows
        if provider_value(row, provider_field, source_field) == JPX_PROVIDER
    ]

    jpx_blank_ticker = sum(1 for row in jpx_rows if not normalize_text(row.get(ticker_field, "")))
    jpx_blank_exchange = sum(1 for row in jpx_rows if not normalize_text(row.get(exchange_field, "")))
    jpx_blank_company = sum(1 for row in jpx_rows if not normalize_text(row.get(company_field, "")))

    jpx_exchange_not_jpx = sum(
        1
        for row in jpx_rows
        if normalize_text(row.get(exchange_field, "")).upper() != JPX_EXCHANGE
    )

    jpx_market_counter = Counter()
    if market_segment_field:
        jpx_market_counter = Counter(
            normalize_text(row.get(market_segment_field, ""))
            for row in jpx_rows
        )

    jpx_country_counter = Counter()
    if country_field:
        jpx_country_counter = Counter(
            normalize_text(row.get(country_field, ""))
            for row in jpx_rows
        )

    jpx_currency_counter = Counter()
    if currency_field:
        jpx_currency_counter = Counter(
            normalize_text(row.get(currency_field, ""))
            for row in jpx_rows
        )

    full_source_unlocked = len(expanded_rows) >= FULL_SOURCE_THRESHOLD
    rows_needed_after_jpx = max(FULL_SOURCE_THRESHOLD - len(expanded_rows), 0)

    rebuild_counts = rebuild.get("counts", {})
    rebuild_status = rebuild.get("status", "")

    hard_guards = {
        "phase_type": PHASE_TYPE,
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
    }

    checks: list[dict] = []

    add_check(
        checks,
        name="baseline_file_exists",
        severity="critical",
        expected=True,
        actual=BASELINE_EXPANDED.exists(),
        passed=BASELINE_EXPANDED.exists(),
    )
    add_check(
        checks,
        name="expanded_file_exists",
        severity="critical",
        expected=True,
        actual=EXPANDED_INPUT.exists(),
        passed=EXPANDED_INPUT.exists(),
    )
    add_check(
        checks,
        name="schema_matches_baseline",
        severity="critical",
        expected=True,
        actual=schema_match,
        passed=schema_match,
    )
    add_check(
        checks,
        name="baseline_rows_match_expected",
        severity="critical",
        expected=EXPECTED_BASELINE_ROWS,
        actual=len(baseline_rows),
        passed=len(baseline_rows) == EXPECTED_BASELINE_ROWS,
    )
    add_check(
        checks,
        name="expanded_rows_match_expected",
        severity="critical",
        expected=EXPECTED_EXPANDED_ROWS,
        actual=len(expanded_rows),
        passed=len(expanded_rows) == EXPECTED_EXPANDED_ROWS,
    )
    add_check(
        checks,
        name="expanded_delta_equals_expected_jpx_added",
        severity="critical",
        expected=EXPECTED_JPX_ROWS_ADDED,
        actual=len(expanded_rows) - len(baseline_rows),
        passed=(len(expanded_rows) - len(baseline_rows)) == EXPECTED_JPX_ROWS_ADDED,
    )
    add_check(
        checks,
        name="accepted_jpx_rows_match_expected",
        severity="critical",
        expected=EXPECTED_JPX_ROWS_ADDED,
        actual=len(accepted_rows),
        passed=len(accepted_rows) == EXPECTED_JPX_ROWS_ADDED,
    )
    add_check(
        checks,
        name="excluded_jpx_rows_match_expected",
        severity="critical",
        expected=EXPECTED_JPX_ROWS_EXCLUDED,
        actual=len(excluded_rows),
        passed=len(excluded_rows) == EXPECTED_JPX_ROWS_EXCLUDED,
    )
    add_check(
        checks,
        name="jpx_provider_rows_match_expected",
        severity="critical",
        expected=EXPECTED_JPX_ROWS_ADDED,
        actual=len(jpx_rows),
        passed=len(jpx_rows) == EXPECTED_JPX_ROWS_ADDED,
    )
    add_check(
        checks,
        name="duplicate_exchange_ticker_keys_zero",
        severity="critical",
        expected=0,
        actual=len(duplicate_rows),
        passed=len(duplicate_rows) == 0,
    )
    add_check(
        checks,
        name="jpx_blank_ticker_zero",
        severity="critical",
        expected=0,
        actual=jpx_blank_ticker,
        passed=jpx_blank_ticker == 0,
    )
    add_check(
        checks,
        name="jpx_blank_exchange_zero",
        severity="critical",
        expected=0,
        actual=jpx_blank_exchange,
        passed=jpx_blank_exchange == 0,
    )
    add_check(
        checks,
        name="jpx_blank_company_zero",
        severity="critical",
        expected=0,
        actual=jpx_blank_company,
        passed=jpx_blank_company == 0,
    )
    add_check(
        checks,
        name="jpx_exchange_is_jpx",
        severity="critical",
        expected=0,
        actual=jpx_exchange_not_jpx,
        passed=jpx_exchange_not_jpx == 0,
    )
    add_check(
        checks,
        name="full_source_unlocked_false",
        severity="critical",
        expected=False,
        actual=full_source_unlocked,
        passed=full_source_unlocked is False,
    )
    add_check(
        checks,
        name="rows_needed_after_jpx_expected",
        severity="critical",
        expected=13137,
        actual=rows_needed_after_jpx,
        passed=rows_needed_after_jpx == 13137,
    )
    add_check(
        checks,
        name="full_59k_universe_not_launched",
        severity="critical",
        expected=False,
        actual=hard_guards["full_59k_universe_launched"],
        passed=hard_guards["full_59k_universe_launched"] is False,
    )
    add_check(
        checks,
        name="rebuild_status_is_expected",
        severity="critical",
        expected="JPX_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED",
        actual=rebuild_status,
        passed=rebuild_status == "JPX_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED",
    )
    add_check(
        checks,
        name="rebuild_json_expanded_rows_matches_validation",
        severity="critical",
        expected=rebuild_counts.get("expanded_rows"),
        actual=len(expanded_rows),
        passed=int(rebuild_counts.get("expanded_rows", -1)) == len(expanded_rows),
    )
    add_check(
        checks,
        name="rebuild_json_jpx_added_matches_validation",
        severity="critical",
        expected=rebuild_counts.get("jpx_rows_added"),
        actual=len(jpx_rows),
        passed=int(rebuild_counts.get("jpx_rows_added", -1)) == len(jpx_rows),
    )

    critical_failed = [
        check
        for check in checks
        if check["severity"] == "critical" and check["passed"] != "True"
    ]

    warning_failed = [
        check
        for check in checks
        if check["severity"] == "warning" and check["passed"] != "True"
    ]

    status = (
        "JPX_EXPANDED_VALIDATION_PASSED_FULL_SOURCE_STILL_BLOCKED"
        if not critical_failed and not full_source_unlocked
        else "JPX_EXPANDED_VALIDATION_REVIEW_REQUIRED"
    )

    provider_breakdown = [
        {"provider": provider, "rows": count}
        for provider, count in provider_counter.most_common()
    ]

    blank_diagnostics = [
        {"provider": provider, "field_issue": field_issue, "rows": count}
        for (provider, field_issue), count in blank_diagnostics_counter.most_common()
    ]

    write_csv(CHECKS_CSV, checks, ["check_name", "severity", "expected", "actual", "passed", "note"])
    write_csv(PROVIDER_BREAKDOWN_CSV, provider_breakdown, ["provider", "rows"])
    write_csv(DUPLICATE_KEYS_CSV, duplicate_rows, ["exchange", "ticker", "count"])
    write_csv(BLANK_FIELDS_CSV, blank_diagnostics, ["provider", "field_issue", "rows"])

    sample_fieldnames = expanded_fieldnames
    write_csv(JPX_SAMPLE_CSV, jpx_rows[:200], sample_fieldnames)

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "input_expanded": str(EXPANDED_INPUT),
        "baseline_input": str(BASELINE_EXPANDED),
        "source_rebuild_commit": "feaa354",
        "hard_guards": hard_guards,
        "counts": {
            "baseline_rows": len(baseline_rows),
            "expanded_rows": len(expanded_rows),
            "expanded_delta": len(expanded_rows) - len(baseline_rows),
            "jpx_provider_rows": len(jpx_rows),
            "accepted_jpx_rows": len(accepted_rows),
            "excluded_jpx_rows": len(excluded_rows),
            "duplicate_exchange_ticker_keys": len(duplicate_rows),
            "jpx_blank_ticker": jpx_blank_ticker,
            "jpx_blank_exchange": jpx_blank_exchange,
            "jpx_blank_company": jpx_blank_company,
            "jpx_exchange_not_jpx": jpx_exchange_not_jpx,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_after_jpx": rows_needed_after_jpx,
            "full_59k_universe_launched": False,
            "critical_failed_checks": len(critical_failed),
            "warning_failed_checks": len(warning_failed),
        },
        "provider_breakdown": provider_breakdown,
        "jpx_market_segment_breakdown": dict(jpx_market_counter),
        "jpx_country_breakdown": dict(jpx_country_counter),
        "jpx_currency_breakdown": dict(jpx_currency_counter),
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "checks": checks,
        "recommended_next_phase": "v2.13G - JPX Closure Report",
        "scope_note": (
            "v2.13F validates expanded_universe_v2_13e.csv only. It does not download, "
            "modify raw files, normalize, rebuild, score, call OpenAI, call broker APIs "
            "or launch full 59k."
        ),
    }

    write_json(VALIDATION_JSON, payload)

    check_lines = "\n".join(
        f"- {row['check_name']}: {row['passed']} — expected `{row['expected']}`, actual `{row['actual']}`"
        for row in checks
    )

    provider_lines = "\n".join(
        f"- {row['provider']}: {row['rows']}"
        for row in provider_breakdown
    )

    guard_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in hard_guards.items()
    )

    market_lines = "\n".join(
        f"- {segment}: {count}"
        for segment, count in jpx_market_counter.most_common()
    ) if jpx_market_counter else "- Market segment field not present in expanded schema."

    md = f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **validation-only**

Generated at UTC: `{payload["generated_at_utc"]}`

## Decision

- Recommended next phase: **v2.13G - JPX Closure Report**
- Full source unlocked: **{full_source_unlocked}**
- Full 59k universe launched: **false**

## Counts

- Baseline rows: {len(baseline_rows)}
- Expanded rows: {len(expanded_rows)}
- Expanded delta: {len(expanded_rows) - len(baseline_rows)}
- JPX provider rows: {len(jpx_rows)}
- Accepted JPX rows: {len(accepted_rows)}
- Excluded JPX rows: {len(excluded_rows)}
- Duplicate exchange+ticker keys: {len(duplicate_rows)}
- JPX blank ticker: {jpx_blank_ticker}
- JPX blank exchange: {jpx_blank_exchange}
- JPX blank company name: {jpx_blank_company}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Rows needed after JPX: {rows_needed_after_jpx}
- Critical failed checks: {len(critical_failed)}
- Warning failed checks: {len(warning_failed)}

## Provider breakdown

{provider_lines}

## JPX market segment breakdown

{market_lines}

## Checks

{check_lines}

## Hard guards

{guard_lines}

## Scope note

v2.13F is validation-only.

It does not download anything, does not modify raw files, does not normalize, does not rebuild, does not score, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Outputs

- `{VALIDATION_JSON}`
- `{VALIDATION_MD}`
- `{CHECKS_CSV}`
- `{PROVIDER_BREAKDOWN_CSV}`
- `{DUPLICATE_KEYS_CSV}`
- `{JPX_SAMPLE_CSV}`
- `{BLANK_FIELDS_CSV}`
"""

    VALIDATION_MD.write_text(md, encoding="utf-8")

    print("v2.13F JPX expanded validation-only completed.")
    print(f"- validation json: {VALIDATION_JSON}")
    print(f"- validation report: {VALIDATION_MD}")
    print(f"- checks csv: {CHECKS_CSV}")
    print(f"- provider breakdown csv: {PROVIDER_BREAKDOWN_CSV}")
    print(f"- duplicate keys csv: {DUPLICATE_KEYS_CSV}")
    print(f"- JPX sample csv: {JPX_SAMPLE_CSV}")
    print(f"- blank diagnostics csv: {BLANK_FIELDS_CSV}")
    print("")
    print("DECISION:")
    print(f"- status: {status}")
    print("- recommended_next_phase: v2.13G - JPX Closure Report")
    print("")
    print("COUNTS:")
    for key, value in payload["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
