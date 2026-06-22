
from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APP_PATH = ROOT / "app.py"
BACKUP_PATH = ROOT / "app_before_phase7d3_fundamental_coverage_dashboard_fix.py"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7d3_fundamental_coverage_dashboard_fix_summary.json"
REPORT_PATH = OUT_DIR / "phase7d3_fundamental_coverage_dashboard_fix_report.md"

PATCH_MARKER = "# PHASE 7D.3 FUNDAMENTAL COVERAGE DASHBOARD FIX APPLIED"

REQUIRED_TEXT = [
    PATCH_MARKER,
    "Cobertura yfinance 7C.1 activa",
    "147 ready Stage 2",
    "35 not ready",
    "83.17%",
    "shares_dilution_3y",
]


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def compile_file(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    print("Scout Finance — Phase 7D.3 fundamental coverage dashboard fix checker")
    print("=" * 88)

    for path in [APP_PATH, BACKUP_PATH, SUMMARY_PATH, REPORT_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    good, error = compile_file(APP_PATH)
    if not good:
        fail(f"app.py does not compile: {error}")
        return 1
    ok("app.py compiles")

    text = APP_PATH.read_text(encoding="utf-8", errors="replace")

    for required in REQUIRED_TEXT:
        if required not in text:
            fail(f"Required text missing from app.py: {required}")
            return 1
        ok(f"Required text present: {required}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7D.3":
        fail(f"Summary phase is not 7D.3: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7D.3")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    expected = summary.get("expected_visual_values", {})
    if expected.get("stage1_passed") != 182:
        fail("Expected stage1_passed is not 182")
        return 1
    ok("Expected Stage 1 passed is 182")

    if expected.get("ready_stage2") != 147:
        fail("Expected ready_stage2 is not 147")
        return 1
    ok("Expected ready Stage 2 is 147")

    for flag, expected_value, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", True, "app.py was modified"),
        ("filters_modified", False, "filters were not modified"),
        ("release_modified", False, "release was not modified"),
    ]:
        if summary.get(flag) is expected_value:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1

    print()
    print("Result")
    print("-" * 88)
    ok("Phase 7D.3 fundamental coverage dashboard fix is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
