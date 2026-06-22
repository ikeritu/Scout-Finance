
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "scouting"

SUMMARY = OUT / "stage1_balanced_guarded_implementation_summary.json"
REPORT = OUT / "stage1_balanced_guarded_implementation_report.md"
COMPARISON = OUT / "stage1_balanced_guarded_implementation_comparison.csv"
FILTER = ROOT / "src" / "filter_stage1.py"
BACKUP = ROOT / "src" / "filter_stage1_before_phase7b8_balanced.py"


def ok(msg): print(f"OK   {msg}")
def fail(msg): print(f"FAIL {msg}")


def main():
    print("Scout Finance — Phase 7B.8 guarded implementation checker")
    print("=" * 78)

    for path in [SUMMARY, REPORT, COMPARISON, FILTER, BACKUP]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    if summary.get("phase") != "7B.8":
        fail(f"Summary phase is not 7B.8: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7B.8")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("matches_expected") is not True:
        fail("Implementation does not match dry-run")
        return 1
    ok("Implementation matches dry-run expected counts")

    for key in ["passed", "watchlist", "rejected"]:
        actual = int(summary.get("actual", {}).get(key) or 0)
        expected = int(summary.get("expected", {}).get(key) or -1)
        if actual != expected:
            fail(f"{key} mismatch: actual={actual} expected={expected}")
            return 1
        ok(f"{key} count OK: {actual}")

    for flag, expected, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", False, "app.py was not modified"),
        ("release_modified", False, "release was not modified"),
        ("filter_modified", True, "filter_stage1.py was modified"),
    ]:
        if summary.get(flag) is expected:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1

    print()
    print("Result")
    print("-" * 78)
    ok("Phase 7B.8 guarded implementation is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
