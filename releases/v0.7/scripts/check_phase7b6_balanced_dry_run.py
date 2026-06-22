
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRY_RUN_DIR = PROJECT_ROOT / "outputs" / "scouting" / "stage1_balanced_dry_run"

PASSED_OUT = DRY_RUN_DIR / "balanced_dry_run_passed.csv"
WATCHLIST_OUT = DRY_RUN_DIR / "balanced_dry_run_watchlist.csv"
REJECTED_OUT = DRY_RUN_DIR / "balanced_dry_run_rejected.csv"
TRANSITIONS_OUT = DRY_RUN_DIR / "balanced_dry_run_transitions.csv"
SUMMARY_JSON = DRY_RUN_DIR / "balanced_dry_run_summary.json"
REPORT_MD = DRY_RUN_DIR / "balanced_dry_run_report.md"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7B.6 balanced dry-run checker")
    print("=" * 74)

    for path in [PASSED_OUT, WATCHLIST_OUT, REJECTED_OUT, TRANSITIONS_OUT, SUMMARY_JSON, REPORT_MD]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))

    if summary.get("phase") != "7B.6":
        fail(f"Summary phase is not 7B.6: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7B.6")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    for flag, label in [
        ("openai_called", "OpenAI was not called"),
        ("api_called", "API was not called"),
        ("yfinance_called", "yfinance was not called"),
        ("app_modified", "app.py was not modified"),
        ("filters_modified", "filters were not modified"),
        ("production_stage1_overwritten", "production Stage 1 was not overwritten"),
        ("release_modified", "release was not modified"),
    ]:
        if summary.get(flag) is False:
            ok(label)
        else:
            fail(f"Invalid flag: {flag}")
            return 1

    passed = pd.read_csv(PASSED_OUT)
    watchlist = pd.read_csv(WATCHLIST_OUT)
    rejected = pd.read_csv(REJECTED_OUT)
    transitions = pd.read_csv(TRANSITIONS_OUT)

    total = len(passed) + len(watchlist) + len(rejected)

    if total != int(summary.get("input_companies") or 0):
        fail("Dry-run passed/watchlist/rejected counts do not sum to input")
        return 1
    ok("Dry-run counts are consistent")

    if len(transitions) != int(summary.get("input_companies") or 0):
        fail("Transitions row count does not match input")
        return 1
    ok("Transition count matches input")

    print()
    print("Summary")
    print("-" * 74)
    print(f"Passed / Watchlist / Rejected: {len(passed)} / {len(watchlist)} / {len(rejected)}")
    print(f"Passed moved to watchlist: {summary.get('passed_to_watchlist')}")
    print(f"Passed moved to rejected: {summary.get('passed_to_rejected')}")
    print()
    print("Result")
    print("-" * 74)
    ok("Phase 7B.6 balanced dry-run is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
