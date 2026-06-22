
"""
Scout Finance — Phase 6C fundamentals enrichment checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase6c_fundamentals_enrichment.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENRICHED = PROJECT_ROOT / "data" / "stages" / "stage1_passed_enriched.csv"
SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "fundamentals_enrichment_summary.json"


REQUIRED_COLUMNS = [
    "ticker",
    "revenue_ttm",
    "operating_margin",
    "fcf_margin",
    "net_debt_to_ebitda",
    "shares_dilution_3y",
    "financial_data_date",
    "data_completeness_score",
    "special_case",
]


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 6C fundamentals enrichment checker")
    print("=" * 66)

    if not ENRICHED.exists():
        fail(f"Missing enriched file: {ENRICHED}")
        return 1
    ok(f"Enriched file exists: {ENRICHED}")

    if not SUMMARY.exists():
        fail(f"Missing summary: {SUMMARY}")
        return 1
    ok(f"Summary exists: {SUMMARY}")

    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read summary JSON: {exc}")
        return 1

    if summary.get("phase") != "6C":
        fail("Summary phase is not 6C")
        return 1
    ok("Summary phase is 6C")

    if summary.get("api_called") is False:
        ok("External API was not called")
    else:
        fail("Summary indicates external API was called")
        return 1

    if summary.get("openai_called") is False:
        ok("OpenAI was not called")
    else:
        fail("Summary indicates OpenAI was called")
        return 1

    df = pd.read_csv(ENRICHED)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        fail("Enriched CSV missing columns:")
        for column in missing_columns:
            print(f"   - {column}")
        return 1
    ok("Required fundamental columns present")

    print()
    print("Summary")
    print("-" * 66)
    print(f"Stage 1 companies: {summary.get('input_stage1_companies')}")
    print(f"Fundamentals rows: {summary.get('fundamentals_rows')}")
    print(f"Matched companies with revenue: {summary.get('matched_companies_with_revenue')}")
    print(f"Match rate: {summary.get('match_rate_percent')}%")
    print(f"Stage1 passed overwritten: {summary.get('stage1_passed_overwritten')}")

    print()
    print("Result")
    print("-" * 66)
    ok("Phase 6C fundamentals enrichment is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
