
"""
Scout Finance — Phase 6D Stage 2 enriched-input checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase6d_stage2_enriched.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STAGE1_PASSED = PROJECT_ROOT / "data" / "stages" / "stage1_passed.csv"
STAGE1_PASSED_ENRICHED = PROJECT_ROOT / "data" / "stages" / "stage1_passed_enriched.csv"

STAGE2_PASSED = PROJECT_ROOT / "data" / "stages" / "stage2_passed.csv"
STAGE2_WATCHLIST = PROJECT_ROOT / "data" / "stages" / "stage2_watchlist.csv"
STAGE2_REJECTED = PROJECT_ROOT / "data" / "stages" / "stage2_rejected.csv"
STAGE2_REJECTION_LOG = PROJECT_ROOT / "data" / "stages" / "stage2_rejection_log.csv"
STAGE2_SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "stage2_summary.json"


REQUIRED_FUNDAMENTAL_COLUMNS = [
    "revenue_ttm",
    "operating_margin",
    "fcf_margin",
    "net_debt_to_ebitda",
    "shares_dilution_3y",
    "data_completeness_score",
    "financial_data_date",
    "special_case",
]


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def _count_rows(path: Path) -> int:
    if not path.exists():
        return 0

    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return 0


def main() -> int:
    print("Scout Finance — Phase 6D Stage 2 enriched-input checker")
    print("=" * 68)

    if not STAGE1_PASSED.exists():
        fail(f"Missing Stage 1 passed file: {STAGE1_PASSED}")
        return 1

    ok(f"Stage 1 clean file exists: {STAGE1_PASSED}")

    if not STAGE1_PASSED_ENRICHED.exists():
        fail(f"Missing enriched Stage 1 file: {STAGE1_PASSED_ENRICHED}")
        return 1

    ok(f"Enriched Stage 1 file exists: {STAGE1_PASSED_ENRICHED}")

    enriched_df = pd.read_csv(STAGE1_PASSED_ENRICHED)

    missing_columns = [
        column for column in REQUIRED_FUNDAMENTAL_COLUMNS
        if column not in enriched_df.columns
    ]

    if missing_columns:
        fail("Enriched Stage 1 file is missing fundamental columns:")
        for column in missing_columns:
            print(f"   - {column}")
        return 1

    ok("Enriched Stage 1 file has required fundamental columns")

    output_files = [
        STAGE2_PASSED,
        STAGE2_WATCHLIST,
        STAGE2_REJECTED,
        STAGE2_REJECTION_LOG,
        STAGE2_SUMMARY,
    ]

    for path in output_files:
        if not path.exists():
            fail(f"Missing Stage 2 output: {path}")
            return 1
        ok(f"Stage 2 output exists: {path}")

    try:
        summary = json.loads(STAGE2_SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read Stage 2 summary JSON: {exc}")
        return 1

    if summary.get("stage") != "stage2":
        fail("Stage 2 summary stage is not stage2")
        return 1

    ok("Stage 2 summary stage OK")

    total_outputs = _count_rows(STAGE2_PASSED) + _count_rows(STAGE2_WATCHLIST) + _count_rows(STAGE2_REJECTED)

    if total_outputs != summary.get("input_companies"):
        fail("Stage 2 outputs do not sum to input companies")
        return 1

    ok("Stage 2 output counts are consistent")

    print()
    print("Summary")
    print("-" * 68)
    print(f"Enriched input rows: {len(enriched_df)}")
    print(f"Stage 2 input companies: {summary.get('input_companies')}")
    print(f"PASSED: {summary.get('passed_companies')}")
    print(f"WATCHLIST: {summary.get('watchlist_companies')}")
    print(f"REJECTED: {summary.get('rejected_companies')}")

    if len(enriched_df) != summary.get("input_companies"):
        warn(
            "Stage 2 input count differs from enriched file rows. "
            "Check whether Stage 2 was run after the latest enrichment."
        )
    else:
        ok("Stage 2 input count matches enriched file rows")

    print()
    print("Result")
    print("-" * 68)
    ok("Phase 6D Stage 2 enriched-input flow is valid")
    print("No API call. No OpenAI call. app.py not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
