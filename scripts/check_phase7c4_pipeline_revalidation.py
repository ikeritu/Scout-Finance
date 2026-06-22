
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"

SUMMARY_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_summary.json"
REPORT_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_report.md"
EVIDENCE_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_evidence.csv"
TOP_CANDIDATES_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_top_candidates.csv"
POLICY_STATUS_PATH = OUT_DIR / "active_pipeline_policy_status.json"

EXPECTED = {
    "stage1": {"passed": 182, "watchlist": 84, "rejected": 234},
    "stage2": {"passed": 63, "watchlist": 81, "rejected": 38},
    "stage3": {"passed": 6, "watchlist": 28, "rejected": 29},
    "funnel_path": "500 → 182 → 63 → 6",
}


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7C.4 pipeline revalidation closure checker")
    print("=" * 88)

    for path in [SUMMARY_PATH, REPORT_PATH, EVIDENCE_PATH, TOP_CANDIDATES_PATH, POLICY_STATUS_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7C.4":
        fail(f"Summary phase is not 7C.4: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7C.4")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("ready_for_next_phase") is not True:
        fail("Not ready for next phase")
        return 1
    ok("Ready for next phase")

    stage_counts = summary.get("stage_counts", {})
    for stage in ["stage1", "stage2", "stage3"]:
        if stage_counts.get(stage) != EXPECTED[stage]:
            fail(f"{stage} counts mismatch: {stage_counts.get(stage)} != {EXPECTED[stage]}")
            return 1
        ok(f"{stage} counts OK: {EXPECTED[stage]}")

    funnel = summary.get("funnel", {})
    if funnel.get("path") != EXPECTED["funnel_path"]:
        fail(f"Funnel path mismatch: {funnel.get('path')}")
        return 1
    ok(f"Funnel path OK: {EXPECTED['funnel_path']}")

    checks = summary.get("checks", {})
    for key in ["counts_match_expected", "stage2_policy_ok", "stage3_ok", "export_ok"]:
        if checks.get(key) is not True:
            fail(f"Check failed: {key}={checks.get(key)}")
            return 1
        ok(f"Check OK: {key}")

    evidence = pd.read_csv(EVIDENCE_PATH)
    if evidence.empty:
        fail("Evidence CSV is empty")
        return 1
    ok("Evidence CSV has rows")

    if "exists" not in evidence.columns:
        fail("Evidence CSV missing exists column")
        return 1
    if not evidence["exists"].astype(bool).all():
        missing = evidence.loc[~evidence["exists"].astype(bool), "label"].tolist()
        fail(f"Some evidence files missing: {missing}")
        return 1
    ok("All evidence files exist")

    top = pd.read_csv(TOP_CANDIDATES_PATH)
    if top.empty:
        fail("Top candidates evidence is empty")
        return 1
    ok("Top candidates evidence has rows")

    policy = json.loads(POLICY_STATUS_PATH.read_text(encoding="utf-8"))
    if policy.get("ready_for_dashboard_integration") is not True:
        fail("Policy status not ready for dashboard integration")
        return 1
    ok("Policy status ready for dashboard integration")

    for flag, expected, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", False, "app.py was not modified"),
        ("release_modified", False, "release was not modified"),
    ]:
        if summary.get(flag) is expected:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1

    print()
    print("Summary")
    print("-" * 88)
    print(f"Funnel: {funnel.get('path')}")
    print(f"Next: {summary.get('recommended_next_phase')}")

    print()
    print("Result")
    print("-" * 88)
    ok("Phase 7C.4 pipeline revalidation closure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
