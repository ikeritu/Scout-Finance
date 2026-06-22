"""
Scout Finance — Phase 5E Stage 3 checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase5e_stage3.py

This script does not call OpenAI and does not modify files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PASSED = PROJECT_ROOT / "data" / "stages" / "stage3_passed.csv"
WATCHLIST = PROJECT_ROOT / "data" / "stages" / "stage3_watchlist.csv"
REJECTED = PROJECT_ROOT / "data" / "stages" / "stage3_rejected.csv"
REJECTION_LOG = PROJECT_ROOT / "data" / "stages" / "stage3_rejection_log.csv"
SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "stage3_summary.json"
TOP20 = PROJECT_ROOT / "outputs" / "scouting" / "top_20_deep_research.csv"
TOP50 = PROJECT_ROOT / "outputs" / "scouting" / "top_50_watchlist.csv"
TOP100 = PROJECT_ROOT / "outputs" / "scouting" / "top_100_candidates.csv"


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
    print("Scout Finance — Phase 5E Stage 3 checker")
    print("=" * 54)

    required_outputs = [PASSED, WATCHLIST, REJECTED, REJECTION_LOG, SUMMARY, TOP20, TOP50, TOP100]
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

    total_rows = _count_rows(PASSED) + _count_rows(WATCHLIST) + _count_rows(REJECTED)
    if total_rows != summary.get("input_companies"):
        fail("Output row counts do not sum to input companies.")
        return 1

    combined = pd.concat(
        [
            pd.read_csv(PASSED),
            pd.read_csv(WATCHLIST),
            pd.read_csv(REJECTED),
        ],
        ignore_index=True,
    )

    required_score_columns = [
        "business_quality_score",
        "financial_health_score",
        "growth_score",
        "valuation_score",
        "risk_score",
        "moat_proxy_score",
        "momentum_score",
        "liquidity_score",
        "data_quality_score",
        "final_stage3_score",
        "stage3_category",
        "stage3_status",
    ]

    missing_score_columns = [column for column in required_score_columns if column not in combined.columns]
    if missing_score_columns:
        fail("Missing score columns:")
        for column in missing_score_columns:
            print(f"   - {column}")
        return 1

    ok("Stage 3 outputs are consistent")
    ok("Score columns are present")

    print()
    print("Top candidates")
    print("-" * 54)
    top100 = pd.read_csv(TOP100)
    if top100.empty:
        warn("Top 100 candidates file is empty.")
    else:
        display_cols = [
            col for col in ["ticker", "name", "final_stage3_score", "stage3_category"]
            if col in top100.columns
        ]
        print(top100[display_cols].head(10).to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
