
from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
BACKUP_PATH = ROOT / "app_before_phase7d_dashboard_revalidated_funnel.py"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7d_dashboard_revalidated_funnel_summary.json"
REPORT_PATH = OUT_DIR / "phase7d_dashboard_revalidated_funnel_report.md"
PIPELINE_STATUS_PATH = OUT_DIR / "active_pipeline_policy_status.json"
PIPELINE_SUMMARY_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_summary.json"
TOP_CANDIDATES_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_top_candidates.csv"

REQUIRED_TEXT = [
    "# PHASE 7D REVALIDATED FUNNEL DASHBOARD APPLIED",
    "# >>> PHASE 7D REVALIDATED FUNNEL DASHBOARD HELPERS",
    "Funnel real revalidado",
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
    print("Scout Finance — Phase 7D v2 dashboard revalidated funnel checker")
    print("=" * 88)

    for path in [APP_PATH, BACKUP_PATH, SUMMARY_PATH, REPORT_PATH, PIPELINE_STATUS_PATH, PIPELINE_SUMMARY_PATH, TOP_CANDIDATES_PATH]:
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
    for marker in REQUIRED_TEXT:
        if marker not in text:
            fail(f"Required dashboard text missing in app.py: {marker}")
            return 1
        ok(f"Required dashboard text present: {marker}")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    if summary.get("phase") != "7D":
        fail(f"Summary phase is not 7D: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7D")

    if summary.get("version") != "v2":
        fail(f"Summary version is not v2: {summary.get('version')}")
        return 1
    ok("Summary version is v2")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("funnel_path") != "500 → 182 → 63 → 6":
        fail(f"Unexpected funnel path: {summary.get('funnel_path')}")
        return 1
    ok("Funnel path OK: 500 → 182 → 63 → 6")

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
    print("-" * 88)
    ok("Phase 7D v2 dashboard revalidated funnel integration is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
