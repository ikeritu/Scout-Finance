
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

STAGE1_PASSED = ROOT / "data" / "stages" / "stage1_passed.csv"
ENRICHED_PATH = ROOT / "data" / "stages" / "stage1_passed_enriched.csv"
RAW_FUNDAMENTALS = ROOT / "data" / "raw" / "fundamentals_source_yfinance.csv"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "fundamentals_yfinance_enrichment_summary.json"
FAILURES_PATH = OUT_DIR / "fundamentals_yfinance_failures.csv"
COVERAGE_PATH = OUT_DIR / "fundamentals_yfinance_enrichment_coverage.csv"
REPORT_PATH = OUT_DIR / "fundamentals_yfinance_enrichment_report.md"

REQUIRED_COLUMNS = [
    "ticker", "revenue_ttm", "operating_margin", "fcf_margin", "net_debt_to_ebitda",
    "shares_dilution_3y", "data_completeness_score", "financial_data_date", "special_case",
]

EXPECTED_STAGE1_BALANCED_ROWS = 182


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def main() -> int:
    print("Scout Finance — Phase 7C.1 yfinance fundamentals enrichment checker")
    print("=" * 82)

    for path in [STAGE1_PASSED, ENRICHED_PATH, RAW_FUNDAMENTALS, SUMMARY_PATH, FAILURES_PATH, COVERAGE_PATH, REPORT_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7C.1":
        fail(f"Summary phase is not 7C.1: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7C.1")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    stage1 = pd.read_csv(STAGE1_PASSED)
    enriched = pd.read_csv(ENRICHED_PATH)
    raw = pd.read_csv(RAW_FUNDAMENTALS)

    if len(stage1) != EXPECTED_STAGE1_BALANCED_ROWS:
        fail(f"Stage 1 Balanced rows expected {EXPECTED_STAGE1_BALANCED_ROWS}, got {len(stage1)}")
        return 1
    ok(f"Stage 1 Balanced row count OK: {len(stage1)}")

    if len(enriched) != len(stage1):
        fail(f"Enriched rows do not match Stage 1 rows: {len(enriched)} != {len(stage1)}")
        return 1
    ok("Enriched rows match Stage 1 rows")

    if len(raw) != len(stage1):
        fail(f"Raw fundamentals rows do not match Stage 1 rows: {len(raw)} != {len(stage1)}")
        return 1
    ok("Raw fundamentals rows match Stage 1 rows")

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in enriched.columns]
    if missing_cols:
        fail(f"Missing required enriched columns: {missing_cols}")
        return 1
    ok("Enriched file has required Stage 2 columns")

    for flag, expected_value, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External paid API was not called"),
        ("yfinance_called", True, "yfinance was called"),
        ("app_modified", False, "app.py was not modified"),
        ("release_modified", False, "release was not modified"),
    ]:
        if summary.get(flag) is expected_value:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1

    coverage = pd.read_csv(COVERAGE_PATH)
    if coverage.empty:
        fail("Coverage CSV is empty")
        return 1
    ok("Coverage CSV has rows")

    print()
    print("Summary")
    print("-" * 82)
    print(f"Input companies: {summary.get('input_companies')}")
    print(f"yfinance successful rows: {summary.get('yf_success_rows')}")
    print(f"yfinance failed rows: {summary.get('yf_failed_rows')}")
    print(f"Companies ready for Stage 2: {summary.get('companies_ready_for_stage2')}")
    print(f"Companies not ready for Stage 2: {summary.get('companies_not_ready_for_stage2')}")
    print(f"Average core Stage 2 coverage: {summary.get('average_core_stage2_coverage_percent')}%")

    print()
    print("Result")
    print("-" * 82)
    ok("Phase 7C.1 yfinance fundamentals enrichment is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
