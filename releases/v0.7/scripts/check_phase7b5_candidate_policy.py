
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_candidate_policy_decision_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_candidate_policy_decision_report.md"
COMPARISON_CSV = SCOUTING_OUTPUTS_DIR / "stage1_candidate_policy_comparison.csv"
DECISION_CSV = SCOUTING_OUTPUTS_DIR / "stage1_candidate_policy_decision.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7B.5 candidate policy checker")
    print("=" * 74)

    for path in [REPORT_JSON, REPORT_MD, COMPARISON_CSV, DECISION_CSV]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))

    if report.get("phase") != "7B.5":
        fail(f"Report phase is not 7B.5: {report.get('phase')}")
        return 1
    ok("Report phase is 7B.5")

    if report.get("status") != "OK":
        fail(f"Report status is not OK: {report.get('status')}")
        return 1
    ok("Report status OK")

    if report.get("recommended_policy") != "balanced":
        fail(f"Recommended policy is not balanced: {report.get('recommended_policy')}")
        return 1
    ok("Balanced policy selected as candidate")

    if report.get("apply_to_production_now") is False:
        ok("Production application is disabled")
    else:
        fail("Report would apply policy to production")
        return 1

    for flag, label in [
        ("openai_called", "OpenAI was not called"),
        ("api_called", "API was not called"),
        ("yfinance_called", "yfinance was not called"),
        ("app_modified", "app.py was not modified"),
        ("filters_modified", "filters were not modified"),
        ("release_modified", "release was not modified"),
    ]:
        if report.get(flag) is False:
            ok(label)
        else:
            fail(f"Invalid flag: {flag}")
            return 1

    comparison = pd.read_csv(COMPARISON_CSV)
    decision = pd.read_csv(DECISION_CSV)

    if comparison.empty:
        fail("Comparison CSV is empty")
        return 1
    ok("Comparison CSV has rows")

    if decision.empty:
        fail("Decision CSV is empty")
        return 1
    ok("Decision CSV has decision row")

    print()
    print("Summary")
    print("-" * 74)
    print(comparison[["scenario", "scenario_label", "decision_score", "recommendation"]].to_string(index=False))
    print()
    print("Result")
    print("-" * 74)
    ok("Phase 7B.5 candidate policy decision is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
