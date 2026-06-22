
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7f1_release_v07_integrity_summary.json"
REPORT_PATH = OUT_DIR / "phase7f1_release_v07_integrity_report.md"
FILES_AUDIT_PATH = OUT_DIR / "phase7f1_release_v07_files_audit.csv"

def ok(msg: str) -> None:
    print(f"OK   {msg}")

def fail(msg: str) -> None:
    print(f"FAIL {msg}")

def main() -> int:
    print("Scout Finance — Phase 7F.1 release v0.7 integrity checker")
    print("=" * 92)

    for path in [SUMMARY_PATH, REPORT_PATH, FILES_AUDIT_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7F.1":
        fail(f"Summary phase is not 7F.1: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7F.1")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("release_freeze_approved") is not True:
        fail("release_freeze_approved is not True")
        return 1
    ok("Release freeze approved")

    if summary.get("validated_funnel") != "500 → 182 → 63 → 6":
        fail(f"Unexpected funnel: {summary.get('validated_funnel')}")
        return 1
    ok("Funnel OK: 500 → 182 → 63 → 6")

    for key, expected in {"stage1_passed":182, "stage2_passed":63, "stage3_passed":6}.items():
        actual = summary.get("counts", {}).get(key)
        if actual != expected:
            fail(f"{key} mismatch: {actual} != {expected}")
            return 1
        ok(f"{key} OK: {expected}")

    if summary.get("counts", {}).get("stage3_candidates_for_ranking", 0) < 10:
        fail("stage3_candidates_for_ranking below 10")
        return 1
    ok(f"stage3_candidates_for_ranking OK: {summary.get('counts', {}).get('stage3_candidates_for_ranking')}")

    for key, value in summary.get("checks", {}).items():
        if value is not True:
            fail(f"Check failed: {key}={value}")
            return 1
        ok(f"Check OK: {key}")

    audit = pd.read_csv(FILES_AUDIT_PATH)
    if audit.empty:
        fail("Files audit CSV is empty")
        return 1
    ok(f"Files audit rows: {len(audit)}")

    if summary.get("manifest_check", {}).get("missing_from_disk"):
        fail(f"Manifest files missing from disk: {summary.get('manifest_check', {}).get('missing_from_disk')}")
        return 1
    ok("All manifest files exist on disk")

    for flag, expected, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", False, "app.py was not modified"),
        ("filters_modified", False, "filters were not modified"),
        ("release_modified", False, "release was not modified by validator"),
    ]:
        if summary.get(flag) is expected:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1

    print()
    print("Result")
    print("-" * 92)
    ok("Scout Finance v0.7.0-candidate integrity validation is complete")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
