
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_report.md"
SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_summary.csv"
DECISIONS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_decisions.csv"
ALIGNMENT_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_current_base_alignment.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def main() -> int:
    print("Scout Finance — Phase 7B.4 final simulator checker")
    print("=" * 74)
    for path in [REPORT_JSON, REPORT_MD, SUMMARY_CSV, DECISIONS_CSV, ALIGNMENT_CSV]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    if report.get("phase") != "7B.4":
        fail(f"Report phase is not 7B.4: {report.get('phase')}")
        return 1
    ok("Report phase is 7B.4")
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

    summary = pd.read_csv(SUMMARY_CSV)
    required_scenarios = {"current_base", "conservative", "balanced", "aggressive"}
    found = set(summary["scenario"].astype(str).tolist())
    missing = required_scenarios - found
    if missing:
        fail(f"Missing scenarios: {missing}")
        return 1
    ok("All required scenarios present")

    alignment = report.get("alignment", {})
    mismatched = int(alignment.get("mismatched") or 0)
    if mismatched == 0:
        ok("current_base aligned exactly with real Stage 1")
    else:
        warn(f"current_base still has mismatches: {mismatched}")

    print()
    print("Summary")
    print("-" * 74)
    print(summary[["scenario", "passed", "watchlist", "rejected", "pass_rate_percent", "watchlist_rate_percent", "rejection_rate_percent"]].to_string(index=False))
    print(f"Alignment: {alignment}")
    print()
    print("Result")
    print("-" * 74)
    ok("Phase 7B.4 final simulator is valid")
    return 0 if mismatched == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
