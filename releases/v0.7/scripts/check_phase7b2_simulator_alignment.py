
"""
Scout Finance — Phase 7B.2 simulator alignment checker.

Run:
    ./.venv/Scripts/python.exe scripts/check_phase7b2_simulator_alignment.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_simulator_alignment_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_simulator_alignment_report.md"
MISMATCHES_CSV = SCOUTING_OUTPUTS_DIR / "stage1_simulator_alignment_mismatches.csv"
MISMATCH_SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_simulator_alignment_mismatch_summary.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7B.2 simulator alignment checker")
    print("=" * 76)

    for path in [REPORT_JSON, REPORT_MD, MISMATCHES_CSV, MISMATCH_SUMMARY_CSV]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    try:
        report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read report JSON: {exc}")
        return 1

    if report.get("phase") != "7B.2":
        fail(f"Report phase is not 7B.2: {report.get('phase')}")
        return 1

    ok("Report phase is 7B.2")

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

    total = int(report.get("total_companies_compared") or 0)
    matched = int(report.get("matched") or 0)
    mismatched = int(report.get("mismatched") or 0)

    if matched + mismatched != total:
        fail("Matched + mismatched does not equal total")
        return 1

    ok("Alignment counts are consistent")

    mismatches = pd.read_csv(MISMATCHES_CSV)

    if mismatched > 0 and mismatches.empty:
        fail("Report says mismatches exist but mismatches CSV is empty")
        return 1

    if mismatched == 0:
        ok("No mismatches found")
    else:
        warn(f"Mismatches found: {mismatched}. Inspect CSV before applying filter changes.")

    print()
    print("Summary")
    print("-" * 76)
    print(f"Compared: {total}")
    print(f"Matched: {matched}")
    print(f"Mismatched: {mismatched}")
    print(f"Match rate: {report.get('match_rate_percent')}%")
    print(f"Real counts: {report.get('real_counts')}")
    print(f"Sim counts: {report.get('simulated_current_base_counts')}")

    print()
    print("Result")
    print("-" * 76)
    ok("Phase 7B.2 simulator alignment report is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
