"""
Scout Finance — Phase 5D Stage 2 checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase5d_stage2.py

This script does not call OpenAI and does not modify files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PASSED = PROJECT_ROOT / "data" / "stages" / "stage2_passed.csv"
WATCHLIST = PROJECT_ROOT / "data" / "stages" / "stage2_watchlist.csv"
REJECTED = PROJECT_ROOT / "data" / "stages" / "stage2_rejected.csv"
REJECTION_LOG = PROJECT_ROOT / "data" / "stages" / "stage2_rejection_log.csv"
SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "stage2_summary.json"


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
    print("Scout Finance — Phase 5D Stage 2 checker")
    print("=" * 54)

    required_outputs = [PASSED, WATCHLIST, REJECTED, REJECTION_LOG, SUMMARY]

    missing = [path for path in required_outputs if not path.exists()]

    if missing:
        for path in missing:
            fail(f"Missing output: {path}")
        return 1

    for path in required_outputs:
        ok(f"Output exists: {path}")

    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Could not read summary: {exc}")
        return 1

    print()
    print("Summary")
    print("-" * 54)
    print(f"Input companies: {summary.get('input_companies')}")
    print(f"PASSED: {summary.get('passed_companies')}")
    print(f"WATCHLIST: {summary.get('watchlist_companies')}")
    print(f"REJECTED: {summary.get('rejected_companies')}")
    print(f"Pass rate: {summary.get('pass_rate'):.2%}")
    print(f"Watchlist rate: {summary.get('watchlist_rate'):.2%}")
    print(f"Rejection rate: {summary.get('rejection_rate'):.2%}")

    passed_rows = _count_rows(PASSED)
    watchlist_rows = _count_rows(WATCHLIST)
    rejected_rows = _count_rows(REJECTED)

    if passed_rows != summary.get("passed_companies"):
        warn("Passed CSV row count does not match summary.")

    if watchlist_rows != summary.get("watchlist_companies"):
        warn("Watchlist CSV row count does not match summary.")

    if rejected_rows != summary.get("rejected_companies"):
        warn("Rejected CSV row count does not match summary.")

    total_rows = passed_rows + watchlist_rows + rejected_rows

    if total_rows != summary.get("input_companies"):
        fail("Output row counts do not sum to input companies.")
        return 1

    ok("Stage 2 outputs are consistent")

    print()
    print("Expected demo behavior after enrichment")
    print("-" * 54)
    print("AAPL should normally be PASSED")
    print("MSFT should normally be PASSED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
