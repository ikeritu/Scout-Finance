from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.12F"
PHASE = "Validate Expanded Source With HKEX"
PHASE_TYPE = "validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

BASELINE_EXPANDED = OUTPUT_DIR / "expanded_universe_v2_11e.csv"
EXPANDED_V2_12E = OUTPUT_DIR / "expanded_universe_v2_12e.csv"
HKEX_REBUILD_JSON = OUTPUT_DIR / "hkex_rebuild_report_v2_12e.json"
HKEX_NORMALIZED_CANDIDATES = OUTPUT_DIR / "hkex_normalized_candidates_v2_12e.csv"
HKEX_EXCLUSIONS = OUTPUT_DIR / "expanded_universe_exclusions_v2_12e.csv"

VALIDATION_JSON = OUTPUT_DIR / "hkex_expanded_validation_v2_12f.json"
VALIDATION_MD = OUTPUT_DIR / "hkex_expanded_validation_report_v2_12f.md"
INTEGRITY_CHECKS_CSV = OUTPUT_DIR / "hkex_expanded_integrity_checks_v2_12f.csv"
PROVIDER_BREAKDOWN_CSV = OUTPUT_DIR / "hkex_provider_breakdown_v2_12f.csv"
COLUMN_QUALITY_CSV = OUTPUT_DIR / "hkex_column_quality_v2_12f.csv"
HKEX_ACCEPTANCE_BREAKDOWN_CSV = OUTPUT_DIR / "hkex_acceptance_breakdown_v2_12f.csv"

FULL_SOURCE_THRESHOLD = 50000
FIRST_EXPANSION_THRESHOLD = 15000

ACCEPTED_HKEX_EQUITY_SUBCATEGORIES = {
    "Equity Securities (Main Board)",
    "Equity Securities (GEM)",
    "Investment Companies",
    "Trading Only Securities",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        VALIDATION_JSON,
        VALIDATION_MD,
        INTEGRITY_CHECKS_CSV,
        PROVIDER_BREAKDOWN_CSV,
        COLUMN_QUALITY_CSV,
        HKEX_ACCEPTANCE_BREAKDOWN_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.12F outputs:\n"
            + "\n".join(existing)
        )


def normalize_text(value: object) -> str:
    return str(value or "").strip()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    return fieldnames, rows


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def field_lookup(fieldnames: list[str]) -> dict[str, str]:
    return {field.lower(): field for field in fieldnames}


def get_field_value(row: dict, lookup: dict[str, str], *candidates: str) -> str:
    for candidate in candidates:
        field = lookup.get(candidate.lower())
        if field:
            return normalize_text(row.get(field, ""))
    return ""


def duplicate_exchange_ticker_count(rows: list[dict], lookup: dict[str, str]) -> tuple[int, int]:
    counter = Counter()

    for row in rows:
        ticker = get_field_value(row, lookup, "ticker", "symbol").upper()
        exchange = get_field_value(row, lookup, "exchange").upper()

        if ticker and exchange:
            counter[(exchange, ticker)] += 1

    duplicate_keys = sum(1 for count in counter.values() if count > 1)
    duplicate_rows = sum(count - 1 for count in counter.values() if count > 1)

    return duplicate_keys, duplicate_rows


def blank_count(rows: list[dict], lookup: dict[str, str], *candidates: str) -> int:
    return sum(1 for row in rows if not get_field_value(row, lookup, *candidates))


def provider_breakdown(rows: list[dict], lookup: dict[str, str]) -> list[dict]:
    counter = Counter()

    for row in rows:
        provider = get_field_value(row, lookup, "source_provider", "provider", "source")
        counter[provider or "__BLANK__"] += 1

    return [
        {
            "source_provider": provider,
            "rows": count,
        }
        for provider, count in counter.most_common()
    ]


def column_quality_rows(fieldnames: list[str], rows: list[dict]) -> list[dict]:
    quality = []

    for field in fieldnames:
        blank = sum(1 for row in rows if not normalize_text(row.get(field, "")))
        non_blank = len(rows) - blank
        quality.append(
            {
                "column": field,
                "rows": len(rows),
                "non_blank": non_blank,
                "blank": blank,
                "blank_pct": round((blank / len(rows) * 100), 4) if rows else 0,
            }
        )

    return quality


def group_hkex_acceptance(rows: list[dict]) -> list[dict]:
    counter = Counter()

    for row in rows:
        status = normalize_text(row.get("rebuild_candidate_status"))
        category = normalize_text(row.get("category"))
        subcategory = normalize_text(row.get("subcategory"))
        reason = normalize_text(row.get("decision_reason"))
        counter[(status, category, subcategory, reason)] += 1

    return [
        {
            "rebuild_candidate_status": status,
            "category": category,
            "subcategory": subcategory,
            "decision_reason": reason,
            "rows": count,
        }
        for (status, category, subcategory, reason), count in counter.most_common()
    ]


def add_check(
    checks: list[dict],
    *,
    check_id: str,
    description: str,
    expected: object,
    actual: object,
    passed: bool,
    severity: str,
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "description": description,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "severity": severity,
        }
    )


def main() -> None:
    no_overwrite_guard()

    rebuild_report = read_json(HKEX_REBUILD_JSON)

    baseline_fields, baseline_rows = read_csv_rows(BASELINE_EXPANDED)
    expanded_fields, expanded_rows = read_csv_rows(EXPANDED_V2_12E)
    normalized_fields, normalized_rows = read_csv_rows(HKEX_NORMALIZED_CANDIDATES)
    exclusion_fields, exclusion_rows = read_csv_rows(HKEX_EXCLUSIONS)

    expanded_lookup = field_lookup(expanded_fields)
    baseline_lookup = field_lookup(baseline_fields)

    counts = rebuild_report.get("counts", {})

    expected_baseline_rows = int(counts.get("baseline_rows", 0))
    expected_hkex_rows_added = int(counts.get("hkex_rows_added", 0))
    expected_exclusions = int(counts.get("exclusions", 0))
    expected_new_expanded_rows = int(counts.get("new_expanded_rows", 0))
    expected_duplicate_keys = int(counts.get("duplicate_exchange_ticker_keys", -1))
    expected_full_source_unlocked = bool(counts.get("full_source_unlocked", False))
    expected_rows_needed_full_source = int(counts.get("rows_needed_full_source", 0))

    duplicate_keys, duplicate_rows = duplicate_exchange_ticker_count(expanded_rows, expanded_lookup)

    provider_rows = provider_breakdown(expanded_rows, expanded_lookup)
    provider_map = {row["source_provider"]: int(row["rows"]) for row in provider_rows}

    hkex_rows_in_expanded = provider_map.get("hkex_securities_list", 0)

    accepted_normalized = [
        row for row in normalized_rows
        if normalize_text(row.get("rebuild_candidate_status")) == "ACCEPTED_FOR_REBUILD_CANDIDATE"
    ]

    excluded_normalized = [
        row for row in normalized_rows
        if normalize_text(row.get("rebuild_candidate_status")) == "EXCLUDED"
    ]

    hkex_expanded_rows = [
        row for row in expanded_rows
        if get_field_value(row, expanded_lookup, "source_provider", "provider", "source") == "hkex_securities_list"
    ]

    hkex_disallowed_rows = []
    for row in hkex_expanded_rows:
        category = get_field_value(row, expanded_lookup, "hkex_category", "category")
        subcategory = get_field_value(row, expanded_lookup, "hkex_subcategory", "subcategory")

        if category != "Equity" or subcategory not in ACCEPTED_HKEX_EQUITY_SUBCATEGORIES:
            hkex_disallowed_rows.append(row)

    baseline_blank_company = blank_count(baseline_rows, baseline_lookup, "company_name", "name")
    expanded_blank_company = blank_count(expanded_rows, expanded_lookup, "company_name", "name")

    blank_ticker_rows = blank_count(expanded_rows, expanded_lookup, "ticker", "symbol")
    blank_exchange_rows = blank_count(expanded_rows, expanded_lookup, "exchange")
    blank_company_rows = expanded_blank_company

    first_expansion_unlocked = len(expanded_rows) >= FIRST_EXPANSION_THRESHOLD
    full_source_unlocked = len(expanded_rows) >= FULL_SOURCE_THRESHOLD
    rows_needed_full_source = max(FULL_SOURCE_THRESHOLD - len(expanded_rows), 0)

    checks: list[dict] = []

    add_check(
        checks,
        check_id="C001",
        description="Baseline row count matches v2.12E rebuild report",
        expected=expected_baseline_rows,
        actual=len(baseline_rows),
        passed=len(baseline_rows) == expected_baseline_rows,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C002",
        description="Expanded row count matches v2.12E rebuild report",
        expected=expected_new_expanded_rows,
        actual=len(expanded_rows),
        passed=len(expanded_rows) == expected_new_expanded_rows,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C003",
        description="HKEX rows in expanded match v2.12E rebuild report",
        expected=expected_hkex_rows_added,
        actual=hkex_rows_in_expanded,
        passed=hkex_rows_in_expanded == expected_hkex_rows_added,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C004",
        description="Accepted normalized HKEX candidates match HKEX rows added",
        expected=expected_hkex_rows_added,
        actual=len(accepted_normalized),
        passed=len(accepted_normalized) == expected_hkex_rows_added,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C005",
        description="Exclusions count matches v2.12E rebuild report",
        expected=expected_exclusions,
        actual=len(exclusion_rows),
        passed=len(exclusion_rows) == expected_exclusions,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C006",
        description="Excluded normalized rows match exclusions file",
        expected=len(exclusion_rows),
        actual=len(excluded_normalized),
        passed=len(excluded_normalized) == len(exclusion_rows),
        severity="critical",
    )

    add_check(
        checks,
        check_id="C007",
        description="Duplicate exchange+ticker keys remain zero",
        expected=0,
        actual=duplicate_keys,
        passed=duplicate_keys == 0 and duplicate_rows == 0 and expected_duplicate_keys == 0,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C008",
        description="Blank ticker rows remain zero",
        expected=0,
        actual=blank_ticker_rows,
        passed=blank_ticker_rows == 0,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C009",
        description="Blank exchange rows remain zero",
        expected=0,
        actual=blank_exchange_rows,
        passed=blank_exchange_rows == 0,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C010",
        description="Known blank company_name warning did not increase versus baseline",
        expected=f"<= {baseline_blank_company}",
        actual=blank_company_rows,
        passed=blank_company_rows <= baseline_blank_company,
        severity="warning",
    )

    add_check(
        checks,
        check_id="C011",
        description="HKEX expanded rows respect conservative equity allowlist",
        expected=0,
        actual=len(hkex_disallowed_rows),
        passed=len(hkex_disallowed_rows) == 0,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C012",
        description="First expansion threshold remains unlocked",
        expected=True,
        actual=first_expansion_unlocked,
        passed=first_expansion_unlocked is True,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C013",
        description="Full source threshold remains blocked",
        expected=False,
        actual=full_source_unlocked,
        passed=full_source_unlocked is False and expected_full_source_unlocked is False,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C014",
        description="Rows needed full source matches v2.12E rebuild report",
        expected=expected_rows_needed_full_source,
        actual=rows_needed_full_source,
        passed=rows_needed_full_source == expected_rows_needed_full_source,
        severity="critical",
    )

    add_check(
        checks,
        check_id="C015",
        description="Full 59k universe was not launched",
        expected=False,
        actual=bool(rebuild_report.get("hard_guards", {}).get("full_59k_universe_launched", False)),
        passed=bool(rebuild_report.get("hard_guards", {}).get("full_59k_universe_launched", False)) is False,
        severity="critical",
    )

    critical_failed = [
        check for check in checks
        if check["severity"] == "critical" and not bool(check["passed"])
    ]

    warning_failed = [
        check for check in checks
        if check["severity"] == "warning" and not bool(check["passed"])
    ]

    validation_passed = len(critical_failed) == 0

    if validation_passed:
        status = "HKEX_EXPANDED_VALIDATION_PASSED_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = "v2.12G - HKEX Closure Report"
    else:
        status = "HKEX_EXPANDED_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.12E_REVIEW_OR_REBUILD_FIX_REQUIRED"

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

    column_quality = column_quality_rows(expanded_fields, expanded_rows)
    acceptance_breakdown = group_hkex_acceptance(normalized_rows)

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "validation_passed": validation_passed,
        "generated_at_utc": utc_now(),
        "recommended_next_phase": recommended_next_phase,
        "counts": {
            "baseline_rows": len(baseline_rows),
            "expanded_rows": len(expanded_rows),
            "hkex_rows_in_expanded": hkex_rows_in_expanded,
            "accepted_normalized_hkex_candidates": len(accepted_normalized),
            "exclusions": len(exclusion_rows),
            "duplicate_exchange_ticker_keys": duplicate_keys,
            "duplicate_exchange_ticker_rows": duplicate_rows,
            "blank_ticker_rows": blank_ticker_rows,
            "blank_exchange_rows": blank_exchange_rows,
            "blank_company_name_rows": blank_company_rows,
            "baseline_blank_company_name_rows": baseline_blank_company,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_full_source": rows_needed_full_source,
            "critical_failed_checks": len(critical_failed),
            "warning_failed_checks": len(warning_failed),
        },
        "provider_breakdown": provider_rows,
        "integrity_checks": checks,
        "hard_guards": hard_guards,
        "outputs": {
            "validation_json": str(VALIDATION_JSON),
            "validation_report": str(VALIDATION_MD),
            "integrity_checks_csv": str(INTEGRITY_CHECKS_CSV),
            "provider_breakdown_csv": str(PROVIDER_BREAKDOWN_CSV),
            "column_quality_csv": str(COLUMN_QUALITY_CSV),
            "hkex_acceptance_breakdown_csv": str(HKEX_ACCEPTANCE_BREAKDOWN_CSV),
        },
    }

    write_json(VALIDATION_JSON, payload)

    write_csv(
        INTEGRITY_CHECKS_CSV,
        checks,
        ["check_id", "description", "expected", "actual", "passed", "severity"],
    )

    write_csv(
        PROVIDER_BREAKDOWN_CSV,
        provider_rows,
        ["source_provider", "rows"],
    )

    write_csv(
        COLUMN_QUALITY_CSV,
        column_quality,
        ["column", "rows", "non_blank", "blank", "blank_pct"],
    )

    write_csv(
        HKEX_ACCEPTANCE_BREAKDOWN_CSV,
        acceptance_breakdown,
        ["rebuild_candidate_status", "category", "subcategory", "decision_reason", "rows"],
    )

    provider_lines = "\n".join(
        f"- {row['source_provider']}: {row['rows']}"
        for row in provider_rows
    )

    check_lines = "\n".join(
        f"- {row['check_id']} [{row['severity']}]: {row['description']} -> expected={row['expected']}; actual={row['actual']}; passed={row['passed']}"
        for row in checks
    )

    guard_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in hard_guards.items()
    )

    md = f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **validation-only**

Validation passed: **{validation_passed}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Recommended next phase

**{recommended_next_phase}**

## Counts

- Baseline rows: {len(baseline_rows)}
- Expanded rows: {len(expanded_rows)}
- HKEX rows in expanded: {hkex_rows_in_expanded}
- Accepted normalized HKEX candidates: {len(accepted_normalized)}
- Exclusions: {len(exclusion_rows)}
- Duplicate exchange+ticker keys: {duplicate_keys}
- Duplicate exchange+ticker rows: {duplicate_rows}
- Blank ticker rows: {blank_ticker_rows}
- Blank exchange rows: {blank_exchange_rows}
- Blank company_name rows: {blank_company_rows}
- Baseline blank company_name rows: {baseline_blank_company}
- First expansion unlocked: {first_expansion_unlocked}
- Full source unlocked: {full_source_unlocked}
- Rows needed full source: {rows_needed_full_source}
- Critical failed checks: {len(critical_failed)}
- Warning failed checks: {len(warning_failed)}

## Provider breakdown

{provider_lines}

## Integrity checks

{check_lines}

## Hard guards

{guard_lines}

## Scope note

v2.12F validates the expanded source created by v2.12E.

It does not rebuild, normalize, filter net-new rows, score, call OpenAI, call broker APIs, or launch full 59k.

Full 59k remains blocked.
"""

    VALIDATION_MD.write_text(md, encoding="utf-8")

    print("v2.12F HKEX expanded validation-only completed.")
    print(f"- validation json: {VALIDATION_JSON}")
    print(f"- validation report: {VALIDATION_MD}")
    print(f"- integrity checks csv: {INTEGRITY_CHECKS_CSV}")
    print(f"- provider breakdown csv: {PROVIDER_BREAKDOWN_CSV}")
    print(f"- column quality csv: {COLUMN_QUALITY_CSV}")
    print(f"- hkex acceptance breakdown csv: {HKEX_ACCEPTANCE_BREAKDOWN_CSV}")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print(f"- validation_passed: {validation_passed}")
    print(f"- recommended_next_phase: {recommended_next_phase}")
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
