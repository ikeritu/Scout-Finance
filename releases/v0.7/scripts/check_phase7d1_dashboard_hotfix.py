
from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
BACKUP_PATH = ROOT / "app_before_phase7d1_dashboard_hotfix.py"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7d1_dashboard_hotfix_summary.json"
REPORT_PATH = OUT_DIR / "phase7d1_dashboard_hotfix_report.md"

HELPER_START = "# >>> PHASE 7D REVALIDATED FUNNEL DASHBOARD HELPERS"
HOTFIX_MARKER = "# PHASE 7D.1 DASHBOARD HOTFIX APPLIED"


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
    print("Scout Finance — Phase 7D.1 dashboard hotfix checker")
    print("=" * 80)

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

    if HOTFIX_MARKER not in text:
        fail("Hotfix marker missing from app.py")
        return 1
    ok("Hotfix marker present")

    if HELPER_START not in text:
        fail("Helper block missing from app.py")
        return 1
    ok("Helper block present")

    helper_idx = text.find(HELPER_START)
    call_idx = text.find("_render_phase7d_revalidated_funnel_dashboard()", helper_idx)

    if call_idx <= helper_idx:
        fail("Render call does not appear after helper definition")
        return 1
    ok("Render call appears after helper definition")

    old_bad_idx = text.find("# PHASE 7D REVALIDATED FUNNEL DASHBOARD APPLIED")
    if old_bad_idx != -1 and old_bad_idx < helper_idx:
        fail("Old bad render call still appears before helper definition")
        return 1
    ok("Old bad render call is not before helper definition")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7D.1":
        fail(f"Summary phase is not 7D.1: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7D.1")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    for flag, expected, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", True, "app.py was modified"),
        ("filters_modified", False, "filters were not modified"),
        ("release_modified", False, "release was not modified"),
    ]:
        if summary.get(flag) is expected:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1

    print()
    print("Result")
    print("-" * 80)
    ok("Phase 7D.1 dashboard hotfix is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
