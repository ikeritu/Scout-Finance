
"""
Scout Finance — Phase 6B fundamental coverage checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase6b_fundamental_coverage.py

This checker does not call OpenAI and does not call external APIs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

COVERAGE_JSON = PROJECT_ROOT / "outputs" / "scouting" / "fundamental_coverage_report.json"
COVERAGE_CSV = PROJECT_ROOT / "outputs" / "scouting" / "fundamental_coverage_report.csv"
MISSING_BY_COMPANY = PROJECT_ROOT / "outputs" / "scouting" / "fundamental_missing_by_company.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 6B fundamental coverage checker")
    print("=" * 66)

    for path in [COVERAGE_JSON, COVERAGE_CSV, MISSING_BY_COMPANY]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    try:
        report = json.loads(COVERAGE_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read report JSON: {exc}")
        return 1

    if report.get("phase") != "6B":
        fail("Report phase is not 6B")
        return 1

    ok("Report phase is 6B")

    if report.get("openai_called") is False:
        ok("OpenAI was not called")
    else:
        fail("Report indicates OpenAI was called")
        return 1

    if report.get("api_called") is False:
        ok("External API was not called")
    else:
        fail("Report indicates external API was called")
        return 1

    coverage_df = pd.read_csv(COVERAGE_CSV)
    missing_df = pd.read_csv(MISSING_BY_COMPANY)

    required_columns = [
        "category",
        "column",
        "exists",
        "present_count",
        "missing_count",
        "coverage_percent",
    ]

    missing_cols = [column for column in required_columns if column not in coverage_df.columns]

    if missing_cols:
        fail("Coverage CSV missing columns:")
        for column in missing_cols:
            print(f"   - {column}")
        return 1

    ok("Coverage CSV columns OK")

    if "ticker" not in missing_df.columns:
        fail("Missing-by-company CSV has no ticker column")
        return 1

    ok("Missing-by-company CSV columns OK")

    print()
    print("Summary")
    print("-" * 66)
    print(f"Input companies: {report.get('input_companies')}")
    print(f"Average core Stage 2 coverage: {report.get('average_core_stage2_coverage_percent')}%")
    print(f"Companies ready for Stage 2: {report.get('companies_ready_for_stage2')}")
    print(f"Companies not ready for Stage 2: {report.get('companies_not_ready_for_stage2')}")

    print()
    print("Result")
    print("-" * 66)
    ok("Phase 6B fundamental coverage report is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
