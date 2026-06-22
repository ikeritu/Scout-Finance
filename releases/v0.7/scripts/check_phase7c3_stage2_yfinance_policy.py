
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"

SUMMARY_PATH = OUT_DIR / "stage2_yfinance_policy_implementation_summary.json"
REPORT_PATH = OUT_DIR / "stage2_yfinance_policy_implementation_report.md"
COMPARISON_PATH = OUT_DIR / "stage2_yfinance_policy_implementation_comparison.csv"

FILTER_PATH = ROOT / "src" / "filter_stage2.py"
BACKUP_PATH = ROOT / "src" / "filter_stage2_before_phase7c3_yfinance_policy.py"
LOG_PATH = ROOT / "data" / "stages" / "stage2_rejection_log.csv"

EXPECTED = {"passed": 63, "watchlist": 81, "rejected": 38}


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7C.3 Stage 2 yfinance policy implementation checker")
    print("=" * 92)

    for path in [SUMMARY_PATH, REPORT_PATH, COMPARISON_PATH, FILTER_PATH, BACKUP_PATH, LOG_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7C.3":
        fail(f"Summary phase is not 7C.3: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7C.3")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("matches_expected") is not True:
        fail("Implementation does not match 7C.2 dry-run counts")
        return 1
    ok("Implementation matches 7C.2 dry-run counts")

    actual = summary.get("actual", {})
    for key, value in EXPECTED.items():
        if int(actual.get(key) or 0) != value:
            fail(f"{key} mismatch: actual={actual.get(key)} expected={value}")
            return 1
        ok(f"{key} count OK: {value}")

    text = FILTER_PATH.read_text(encoding="utf-8", errors="replace")
    required_text = [
        "# PHASE 7C.3 YFINANCE STAGE 2 POLICY APPLIED",
        "MISSING_SHARES_DILUTION_PROVIDER_LIMITATION",
        "provider limitation",
    ]
    for marker in required_text:
        if marker not in text:
            fail(f"Missing filter marker/text: {marker}")
            return 1
        ok(f"Filter content present: {marker}")

    log = pd.read_csv(LOG_PATH)
    reason_codes = set(log["reason_code"].dropna().astype(str)) if "reason_code" in log.columns else set()

    if "MISSING_SHARES_DILUTION" in reason_codes:
        fail("Old blocking MISSING_SHARES_DILUTION still present in Stage 2 log")
        return 1
    ok("Old blocking MISSING_SHARES_DILUTION absent from Stage 2 log")

    if "MISSING_SHARES_DILUTION_PROVIDER_LIMITATION" not in reason_codes:
        fail("New provider limitation reason missing from Stage 2 log")
        return 1
    ok("New provider limitation reason present in Stage 2 log")

    for flag, expected_value, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called by implementation script"),
        ("app_modified", False, "app.py was not modified"),
        ("filter_stage2_modified", True, "filter_stage2.py was modified"),
        ("release_modified", False, "release was not modified"),
    ]:
        if summary.get(flag) is expected_value:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1

    print()
    print("Result")
    print("-" * 92)
    ok("Phase 7C.3 Stage 2 yfinance policy implementation is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
