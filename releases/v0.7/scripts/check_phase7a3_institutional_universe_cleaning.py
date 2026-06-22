
"""
Scout Finance — Phase 7A.3 Institutional Universe Cleaning checker.

Run:
    ./.venv/Scripts/python.exe scripts/check_phase7a3_institutional_universe_cleaning.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CLEAN = PROJECT_ROOT / "data" / "raw" / "universe_source_real_clean.csv"
EXCLUDED = PROJECT_ROOT / "data" / "raw" / "universe_source_real_excluded.csv"
SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "universe_cleaning_summary.json"
EXCLUSION_LOG = PROJECT_ROOT / "outputs" / "scouting" / "universe_cleaning_exclusion_log.csv"


REQUIRED_CLEAN_COLUMNS = [
    "Symbol",
    "Name",
    "Exchange",
    "Country",
    "Sector",
    "Industry",
    "Market Cap",
    "Last Sale",
    "Volume",
    "Source",
    "instrument_type",
    "instrument_scope",
    "classification_confidence",
    "classification_reason",
]


REQUIRED_EXCLUSION_COLUMNS = REQUIRED_CLEAN_COLUMNS + [
    "decision",
    "reason_code",
    "reason_category",
    "business_explanation",
    "severity",
    "recoverable",
    "decision_layer",
]


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7A.3 Institutional Universe Cleaning checker")
    print("=" * 78)

    for path in [CLEAN, EXCLUDED, SUMMARY, EXCLUSION_LOG]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read summary: {exc}")
        return 1

    if summary.get("phase") != "7A.3":
        fail(f"Summary phase is not 7A.3: {summary.get('phase')}")
        return 1

    ok("Summary phase is 7A.3")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1

    ok("Summary status OK")

    for flag, label in [
        ("openai_called", "OpenAI was not called"),
        ("paid_api_called", "Paid API was not called"),
        ("app_modified", "app.py was not modified"),
        ("release_v0_6_modified", "release v0.6 was not modified"),
    ]:
        if summary.get(flag) is False:
            ok(label)
        else:
            fail(f"Summary flag invalid: {flag}")
            return 1

    clean_df = pd.read_csv(CLEAN)
    excluded_df = pd.read_csv(EXCLUDED)

    missing_clean = [column for column in REQUIRED_CLEAN_COLUMNS if column not in clean_df.columns]

    if missing_clean:
        fail("Clean CSV missing columns:")
        for column in missing_clean:
            print(f"   - {column}")
        return 1

    ok("Clean CSV required columns present")

    missing_excluded = [column for column in REQUIRED_EXCLUSION_COLUMNS if column not in excluded_df.columns]

    if missing_excluded:
        fail("Excluded CSV missing columns:")
        for column in missing_excluded:
            print(f"   - {column}")
        return 1

    ok("Excluded CSV required columns present")

    total = len(clean_df) + len(excluded_df)

    if total != summary.get("input_rows"):
        fail("Clean + excluded rows do not match input_rows in summary")
        return 1

    ok("Clean + excluded row counts match input rows")

    if not clean_df.empty:
        out_of_scope_in_clean = clean_df[clean_df["instrument_scope"] != "IN_SCOPE"]

        if len(out_of_scope_in_clean) > 0:
            fail("Clean universe contains out-of-scope instruments")
            return 1

        ok("Clean universe only contains IN_SCOPE instruments")

    if len(excluded_df) > 0:
        missing_decision = excluded_df["decision"].isna().sum()

        if missing_decision > 0:
            fail("Some excluded rows have no decision")
            return 1

        ok("Excluded rows contain decisions")

    print()
    print("Summary")
    print("-" * 78)
    print(f"Input rows: {summary.get('input_rows')}")
    print(f"Clean rows: {summary.get('clean_rows')} ({summary.get('clean_rate_percent')}%)")
    print(f"Excluded rows: {summary.get('excluded_rows')} ({summary.get('excluded_rate_percent')}%)")
    print(f"Instrument distribution: {summary.get('instrument_distribution')}")
    print(f"Excluded distribution: {summary.get('excluded_distribution')}")

    print()
    print("Result")
    print("-" * 78)
    ok("Phase 7A.3 institutional universe cleaning is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
