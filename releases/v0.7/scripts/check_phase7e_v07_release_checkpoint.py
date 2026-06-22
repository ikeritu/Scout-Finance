
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"

SUMMARY_PATH = OUT_DIR / "phase7e_v07_release_checkpoint_summary.json"
REPORT_PATH = OUT_DIR / "phase7e_v07_release_checkpoint_report.md"
EVIDENCE_PATH = OUT_DIR / "phase7e_v07_release_checkpoint_evidence.csv"


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def main() -> int:
    print("Scout Finance — Phase 7E v0.7 release checkpoint checker")
    print("=" * 88)

    for path in [SUMMARY_PATH, REPORT_PATH, EVIDENCE_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7E":
        fail(f"Summary phase is not 7E: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7E")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("ready_for_v07_release") is not True:
        fail("Not ready for v0.7 release")
        return 1
    ok("Ready for v0.7 release")

    if summary.get("validated_funnel") != "500 → 182 → 63 → 6":
        fail(f"Unexpected funnel: {summary.get('validated_funnel')}")
        return 1
    ok("Validated funnel OK: 500 → 182 → 63 → 6")

    counts = summary.get("counts", {})
    for key, expected in {
        "stage1_passed_rows": 182,
        "stage2_passed_rows": 63,
        "stage3_passed_rows": 6,
    }.items():
        if counts.get(key) != expected:
            fail(f"{key} mismatch: {counts.get(key)} != {expected}")
            return 1
        ok(f"{key} OK: {expected}")

    checks = summary.get("checks", {})
    for key in [
        "app_compiles",
        "counts_ok",
        "markers_ok",
        "required_files_ok",
        "stage2_policy_ok",
        "dashboard_hotfixes_ok",
        "phase7c4_ok",
    ]:
        if checks.get(key) is not True:
            fail(f"Check failed: {key}={checks.get(key)}")
            return 1
        ok(f"Check OK: {key}")

    evidence = pd.read_csv(EVIDENCE_PATH)
    if evidence.empty:
        fail("Evidence CSV is empty")
        return 1
    ok("Evidence CSV has rows")

    if not evidence["exists"].astype(bool).all():
        missing = evidence.loc[~evidence["exists"].astype(bool), "label"].tolist()
        fail(f"Some evidence files are missing: {missing}")
        return 1
    ok("All evidence files exist")

    for flag, expected, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", False, "app.py was not modified"),
        ("filters_modified", False, "filters were not modified"),
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
    print(f"Funnel: {summary.get('validated_funnel')}")
    print(f"Next: {summary.get('recommended_next_phase')}")

    print()
    print("Result")
    print("-" * 88)
    ok("Phase 7E v0.7 release checkpoint is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
