from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "stage1_balanced_exact_implementation_summary.json"
REPORT_PATH = OUT_DIR / "stage1_balanced_exact_implementation_report.md"
COMPARISON_PATH = OUT_DIR / "stage1_balanced_exact_implementation_comparison.csv"
FILTER_PATH = ROOT / "src" / "filter_stage1.py"
BACKUP_PATH = ROOT / "src" / "filter_stage1_before_phase7b8_1_exact.py"

def ok(message: str) -> None:
    print(f"OK   {message}")

def fail(message: str) -> None:
    print(f"FAIL {message}")

def main() -> int:
    print("Scout Finance — Phase 7B.8.1 exact implementation checker")
    print("=" * 82)
    for path in [SUMMARY_PATH, REPORT_PATH, COMPARISON_PATH, FILTER_PATH, BACKUP_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    if summary.get("phase") != "7B.8.1":
        fail(f"Summary phase is not 7B.8.1: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7B.8.1")
    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")
    if summary.get("matches_expected") is not True:
        fail("Implementation does not match dry-run expected counts")
        return 1
    ok("Implementation matches dry-run expected counts")
    expected = summary.get("expected", {})
    actual = summary.get("actual", {})
    for key in ["passed", "watchlist", "rejected"]:
        if int(actual.get(key) or 0) != int(expected.get(key) or -1):
            fail(f"{key} mismatch: actual={actual.get(key)} expected={expected.get(key)}")
            return 1
        ok(f"{key} count OK: {actual.get(key)}")
    for flag, expected_value, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", False, "app.py was not modified"),
        ("release_modified", False, "release was not modified"),
        ("filter_modified", True, "filter_stage1.py was modified"),
    ]:
        if summary.get(flag) is expected_value:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1
    text = FILTER_PATH.read_text(encoding="utf-8", errors="replace")
    required_markers = [
        "# PHASE 7B.8.1 EXACT BALANCED STAGE 1 POLICY APPLIED",
        '"min_market_cap_pass": 500_000_000',
        '"min_market_cap_watchlist": 150_000_000',
        '"min_price_watchlist": 1.5',
        '"min_dollar_volume_pass": 5_000_000',
        '"min_dollar_volume_watchlist": 1_000_000',
        "PRICE_STRONG_WATCHLIST_RANGE",
        "PRICE_WEAK_WATCHLIST_RANGE",
    ]
    for marker in required_markers:
        if marker not in text:
            fail(f"Missing marker/content in filter_stage1.py: {marker}")
            return 1
        ok(f"Filter content present: {marker}")
    print()
    print("Result")
    print("-" * 82)
    ok("Phase 7B.8.1 exact guarded implementation is valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
