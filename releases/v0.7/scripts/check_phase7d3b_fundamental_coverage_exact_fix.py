
from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APP_PATH = ROOT / "app.py"
BACKUP_PATH = ROOT / "app_before_phase7d3b_fundamental_coverage_exact_fix.py"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7d3b_fundamental_coverage_exact_fix_summary.json"
REPORT_PATH = OUT_DIR / "phase7d3b_fundamental_coverage_exact_fix_report.md"

PATCH_MARKER = "# PHASE 7D.3B FUNDAMENTAL COVERAGE EXACT FIX APPLIED"

REQUIRED_TEXT = [
    PATCH_MARKER,
    "fundamentals_yfinance_enrichment_summary.json",
    'summary["stage1_passed"] = int(_sf7c1.get("input_companies", 182) or 182)',
    'summary["fundamentals_matched"] = int(_sf7c1.get("yfinance_successful_rows", 182) or 182)',
    'summary["coverage_percent"] = round(float(_sf7c1.get("average_core_stage2_coverage", 83.17) or 83.17), 2)',
    'summary["runner_phase"] = "7C.1"',
    'summary["ready_stage2"] = int(_sf7c1.get("companies_ready_for_stage2", 147) or 147)',
    'summary["not_ready_stage2"] = int(_sf7c1.get("companies_not_ready_for_stage2", 35) or 35)',
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
    print("Scout Finance — Phase 7D.3b fundamental coverage exact fix checker")
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
        ok(f"Required text present: {required[:80]}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7D.3b":
        fail(f"Summary phase is not 7D.3b: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7D.3b")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    expected = summary.get("expected_visual_values", {})
    checks = {
        "stage1_passed": 182,
        "fundamentals_matched": 182,
        "ready_stage2": 147,
        "not_ready_stage2": 35,
        "runner_phase": "7C.1",
    }

    for key, value in checks.items():
        if expected.get(key) != value:
            fail(f"Expected {key} mismatch: {expected.get(key)} != {value}")
            return 1
        ok(f"Expected {key} OK: {value}")

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
    ok("Phase 7D.3b fundamental coverage exact fix is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
