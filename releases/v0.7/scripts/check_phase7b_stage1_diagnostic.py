
"""
Scout Finance — Phase 7B Stage 1 diagnostic checker.

Run:
    ./.venv/Scripts/python.exe scripts/check_phase7b_stage1_diagnostic.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_professional_diagnostic_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_professional_diagnostic_report.md"
REJECTION_REASONS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_professional_rejection_reasons.csv"
BUCKETS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_professional_bucket_summary.csv"
WATCHLIST_REVIEW_CSV = SCOUTING_OUTPUTS_DIR / "stage1_professional_watchlist_review.csv"
PASSED_SAMPLE_CSV = SCOUTING_OUTPUTS_DIR / "stage1_professional_passed_sample.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7B Stage 1 diagnostic checker")
    print("=" * 74)

    for path in [
        REPORT_JSON,
        REPORT_MD,
        REJECTION_REASONS_CSV,
        BUCKETS_CSV,
        WATCHLIST_REVIEW_CSV,
        PASSED_SAMPLE_CSV,
    ]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    try:
        report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read report JSON: {exc}")
        return 1

    if report.get("phase") != "7B":
        fail(f"Report phase is not 7B: {report.get('phase')}")
        return 1

    ok("Report phase is 7B")

    if report.get("status") != "OK":
        fail(f"Report status is not OK: {report.get('status')}")
        return 1

    ok("Report status OK")

    for flag, label in [
        ("openai_called", "OpenAI was not called"),
        ("api_called", "API was not called"),
        ("yfinance_called", "yfinance was not called"),
        ("app_modified", "app.py was not modified"),
        ("release_v0_6_modified", "release v0.6 was not modified"),
    ]:
        if report.get(flag) is False:
            ok(label)
        else:
            fail(f"Invalid flag: {flag}")
            return 1

    total = (
        int(report.get("stage1_passed") or 0)
        + int(report.get("stage1_watchlist") or 0)
        + int(report.get("stage1_rejected") or 0)
    )

    if total != int(report.get("stage1_input") or 0):
        fail("Stage 1 passed/watchlist/rejected does not sum to input")
        return 1

    ok("Stage 1 counts are consistent")

    buckets = pd.read_csv(BUCKETS_CSV)

    if buckets.empty:
        fail("Bucket summary CSV is empty")
        return 1

    ok("Bucket summary CSV has rows")

    reasons = pd.read_csv(REJECTION_REASONS_CSV)

    if reasons.empty:
        fail("Rejection reasons CSV is empty")
        return 1

    ok("Rejection reasons CSV has rows")

    print()
    print("Summary")
    print("-" * 74)
    print(f"Stage 1 input: {report.get('stage1_input')}")
    print(f"Passed / Watchlist / Rejected: {report.get('stage1_passed')} / {report.get('stage1_watchlist')} / {report.get('stage1_rejected')}")
    print(f"Rates: {report.get('stage1_pass_rate_percent')}% / {report.get('stage1_watchlist_rate_percent')}% / {report.get('stage1_rejection_rate_percent')}%")

    print()
    print("Result")
    print("-" * 74)
    ok("Phase 7B Stage 1 diagnostic is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
