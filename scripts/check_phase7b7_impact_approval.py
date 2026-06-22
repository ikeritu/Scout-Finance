
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_approval_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_approval_report.md"
TRANSITION_SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_transition_summary.csv"
REASON_SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_reason_summary.csv"
APPROVAL_CSV = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_approval_decision.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7B.7 impact approval checker")
    print("=" * 74)

    for path in [REPORT_JSON, REPORT_MD, TRANSITION_SUMMARY_CSV, REASON_SUMMARY_CSV, APPROVAL_CSV]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))

    if report.get("phase") != "7B.7":
        fail(f"Report phase is not 7B.7: {report.get('phase')}")
        return 1
    ok("Report phase is 7B.7")

    if report.get("status") != "OK":
        fail(f"Report status is not OK: {report.get('status')}")
        return 1
    ok("Report status OK")

    if report.get("decision") != "APPROVE_FOR_GUARDED_APPLICATION":
        fail(f"Decision is not guarded approval: {report.get('decision')}")
        return 1
    ok("Guarded application approval decision present")

    if report.get("apply_to_production_now") is False:
        ok("Production application disabled")
    else:
        fail("Report would apply to production now")
        return 1

    if int(report.get("passed_to_rejected") or 0) == 0:
        ok("No PASSED company moves directly to REJECTED")
    else:
        fail("Some PASSED companies move directly to REJECTED")
        return 1

    for flag, label in [
        ("openai_called", "OpenAI was not called"),
        ("api_called", "API was not called"),
        ("yfinance_called", "yfinance was not called"),
        ("app_modified", "app.py was not modified"),
        ("filters_modified", "filters were not modified"),
        ("production_stage1_overwritten", "production Stage 1 was not overwritten"),
        ("release_modified", "release was not modified"),
    ]:
        if report.get(flag) is False:
            ok(label)
        else:
            fail(f"Invalid flag: {flag}")
            return 1

    transition_summary = pd.read_csv(TRANSITION_SUMMARY_CSV)
    approval = pd.read_csv(APPROVAL_CSV)

    if transition_summary.empty:
        fail("Transition summary is empty")
        return 1
    ok("Transition summary has rows")

    if approval.empty:
        fail("Approval CSV is empty")
        return 1
    ok("Approval CSV has row")

    print()
    print("Summary")
    print("-" * 74)
    print(f"Decision: {report.get('decision')}")
    print(f"Balanced passed/watchlist/rejected: {report.get('balanced_passed')} / {report.get('balanced_watchlist')} / {report.get('balanced_rejected')}")
    print(f"Passed to watchlist: {report.get('passed_to_watchlist')}")
    print(f"Passed to rejected: {report.get('passed_to_rejected')}")
    print(f"Watchlist to rejected: {report.get('watchlist_to_rejected')}")
    print()
    print("Result")
    print("-" * 74)
    ok("Phase 7B.7 impact approval is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
