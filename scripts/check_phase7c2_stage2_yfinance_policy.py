
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"

SUMMARY_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_summary.json"
REPORT_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_report.md"
RESULTS_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_results.csv"
REASONS_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_reasons.csv"
TRANSITIONS_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_transition_summary.csv"

INPUT_PATH = ROOT / "data" / "stages" / "stage1_passed_enriched.csv"


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def main() -> int:
    print("Scout Finance — Phase 7C.2 Stage 2 yfinance policy dry-run checker")
    print("=" * 82)

    for path in [INPUT_PATH, SUMMARY_PATH, REPORT_PATH, RESULTS_PATH, REASONS_PATH, TRANSITIONS_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7C.2":
        fail(f"Summary phase is not 7C.2: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7C.2")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    input_df = pd.read_csv(INPUT_PATH)
    results_df = pd.read_csv(RESULTS_PATH)
    reasons_df = pd.read_csv(REASONS_PATH)

    if len(input_df) != 182:
        fail(f"Input rows expected 182, got {len(input_df)}")
        return 1
    ok("Input rows are 182")

    if len(results_df) != len(input_df):
        fail(f"Result rows do not match input rows: {len(results_df)} != {len(input_df)}")
        return 1
    ok("Result rows match input rows")

    counts = summary.get("simulated_counts", {})
    total = int(counts.get("passed", 0)) + int(counts.get("watchlist", 0)) + int(counts.get("rejected", 0))
    if total != 182:
        fail(f"Simulated counts do not sum to 182: {counts}")
        return 1
    ok("Simulated counts sum to 182")

    if "MISSING_SHARES_DILUTION" in set(reasons_df.get("reason_code", pd.Series(dtype=str)).dropna().astype(str)):
        fail("Dry-run reasons still contain old blocking MISSING_SHARES_DILUTION")
        return 1
    ok("Old blocking MISSING_SHARES_DILUTION reason is absent")

    if "MISSING_SHARES_DILUTION_PROVIDER_LIMITATION" not in set(reasons_df.get("reason_code", pd.Series(dtype=str)).dropna().astype(str)):
        fail("Provider limitation reason is missing")
        return 1
    ok("Provider limitation reason is present")

    for flag, expected, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called by dry-run"),
        ("app_modified", False, "app.py was not modified"),
        ("filter_stage2_modified", False, "filter_stage2.py was not modified"),
        ("release_modified", False, "release was not modified"),
    ]:
        if summary.get(flag) is expected:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1

    print()
    print("Summary")
    print("-" * 82)
    print(f"Current Stage 2 counts: {summary.get('current_stage2_counts')}")
    print(f"Simulated counts: {summary.get('simulated_counts')}")
    print(f"Decision: {summary.get('recommended_decision')}")
    print(f"Next: {summary.get('recommended_next_phase')}")

    print()
    print("Result")
    print("-" * 82)
    ok("Phase 7C.2 Stage 2 yfinance policy dry-run is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
