
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "scouting"

SUMMARY = OUT / "stage1_balanced_official_closure_summary.json"
REPORT = OUT / "stage1_balanced_official_closure_report.md"
EVIDENCE = OUT / "stage1_balanced_official_closure_evidence.csv"
POLICY = OUT / "active_stage1_policy_status.json"
FILTER = ROOT / "src" / "filter_stage1.py"
BACKUP = ROOT / "src" / "filter_stage1_before_phase7b8_1_exact.py"


def ok(msg): print(f"OK   {msg}")
def fail(msg): print(f"FAIL {msg}")


def main() -> int:
    print("Scout Finance — Phase 7B.9 official closure checker")
    print("=" * 82)

    for path in [SUMMARY, REPORT, EVIDENCE, POLICY, FILTER, BACKUP]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    if summary.get("phase") != "7B.9":
        fail(f"Summary phase is not 7B.9: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7B.9")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("active_stage1_policy") != "balanced":
        fail(f"Active policy is not balanced: {summary.get('active_stage1_policy')}")
        return 1
    ok("Active policy is balanced")

    expected = {"passed": 182, "watchlist": 84, "rejected": 234}
    actual = summary.get("actual_counts", {})
    for key, val in expected.items():
        if int(actual.get(key) or 0) != val:
            fail(f"{key} count mismatch: {actual.get(key)} != {val}")
            return 1
        ok(f"{key} count OK: {val}")

    evidence = pd.read_csv(EVIDENCE)
    if evidence.empty:
        fail("Evidence CSV is empty")
        return 1
    ok("Evidence CSV has rows")

    failed = evidence[evidence["status"].astype(str) == "FAIL"]
    if not failed.empty:
        fail(f"Evidence contains failures: {failed.to_dict(orient='records')}")
        return 1
    ok("Evidence has no FAIL rows")

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if policy.get("active_stage1_policy") != "balanced":
        fail("Policy status JSON does not confirm balanced")
        return 1
    ok("Policy status JSON confirms balanced")

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

    print()
    print("Result")
    print("-" * 82)
    ok("Phase 7B.9 Stage 1 Balanced official closure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
