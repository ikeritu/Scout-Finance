
from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APP_PATH = ROOT / "app.py"
BACKUP_PATH = ROOT / "app_before_phase7d2_institutional_count_hotfix.py"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7d2_institutional_count_hotfix_summary.json"
REPORT_PATH = OUT_DIR / "phase7d2_institutional_count_hotfix_report.md"

PATCH_MARKER = "# PHASE 7D.2 INSTITUTIONAL COUNT HOTFIX APPLIED"


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
    print("Scout Finance — Phase 7D.2 institutional Count/Nº hotfix checker")
    print("=" * 84)

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

    if PATCH_MARKER not in text:
        fail("Patch marker missing from app.py")
        return 1
    ok("Patch marker present")

    target_function = "def _render_institutional_universe_dashboard"
    start = text.find(target_function)
    if start == -1:
        fail("_render_institutional_universe_dashboard not found")
        return 1

    next_def = text.find("\ndef ", start + len(target_function))
    if next_def == -1:
        next_def = len(text)

    block = text[start:next_def]

    if '.sort_values("Count", ascending=False)' in block or ".sort_values('Count', ascending=False)" in block:
        fail("Institutional dashboard still sorts by Count")
        return 1
    ok("Institutional dashboard no longer sorts by Count")

    if '.sort_values("Nº", ascending=False)' not in block and ".sort_values('Nº', ascending=False)" not in block:
        fail("Institutional dashboard does not sort by Nº")
        return 1
    ok("Institutional dashboard sorts by Nº")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7D.2":
        fail(f"Summary phase is not 7D.2: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7D.2")

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
    print("-" * 84)
    ok("Phase 7D.2 institutional Count/Nº hotfix is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
