
"""
Scout Finance — Phase 7B.1 policy simulation checker.

Run:
    ./.venv/Scripts/python.exe scripts/check_phase7b1_policy_simulation.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_report.md"
SCENARIO_SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_summary.csv"
SCENARIO_DECISIONS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_decisions.csv"
SCENARIO_BUCKETS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_bucket_summary.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7B.1 policy simulation checker")
    print("=" * 74)

    for path in [
        REPORT_JSON,
        REPORT_MD,
        SCENARIO_SUMMARY_CSV,
        SCENARIO_DECISIONS_CSV,
        SCENARIO_BUCKETS_CSV,
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

    if report.get("phase") != "7B.1":
        fail(f"Report phase is not 7B.1: {report.get('phase')}")
        return 1

    ok("Report phase is 7B.1")

    if report.get("status") != "OK":
        fail(f"Report status is not OK: {report.get('status')}")
        return 1

    ok("Report status OK")

    for flag, label in [
        ("openai_called", "OpenAI was not called"),
        ("api_called", "API was not called"),
        ("yfinance_called", "yfinance was not called"),
        ("app_modified", "app.py was not modified"),
        ("filters_modified", "filters were not modified"),
        ("release_v0_6_modified", "release v0.6 was not modified"),
    ]:
        if report.get(flag) is False:
            ok(label)
        else:
            fail(f"Invalid flag: {flag}")
            return 1

    summary_df = pd.read_csv(SCENARIO_SUMMARY_CSV)
    decisions_df = pd.read_csv(SCENARIO_DECISIONS_CSV)

    required_scenarios = {"current_base", "conservative", "balanced", "aggressive"}
    found_scenarios = set(summary_df["scenario"].astype(str).tolist())

    missing = required_scenarios - found_scenarios

    if missing:
        fail(f"Missing scenarios: {missing}")
        return 1

    ok("All required scenarios present")

    if decisions_df.empty:
        fail("Scenario decisions CSV is empty")
        return 1

    ok("Scenario decisions CSV has rows")

    print()
    print("Summary")
    print("-" * 74)
    print(summary_df[["scenario", "passed", "watchlist", "rejected", "pass_rate_percent", "watchlist_rate_percent", "rejection_rate_percent"]].to_string(index=False))

    print()
    print("Result")
    print("-" * 74)
    ok("Phase 7B.1 Stage 1 policy simulation is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
