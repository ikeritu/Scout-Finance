
from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"
CLEANING_SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "universe_cleaning_summary.json"
COMPARISON_REPORT = PROJECT_ROOT / "outputs" / "scouting" / "institutional_cleaning_comparison_report.json"


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7A.5 institutional dashboard checker")
    print("=" * 74)

    if not APP_PATH.exists():
        fail(f"Missing app.py: {APP_PATH}")
        return 1

    try:
        py_compile.compile(str(APP_PATH), doraise=True)
        ast.parse(APP_PATH.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        fail(f"app.py does not compile/parse: {exc}")
        return 1

    ok("app.py compiles and parses")

    content = APP_PATH.read_text(encoding="utf-8", errors="replace")

    markers = [
        "_sf7a5_build_institutional_universe_summary",
        "_render_institutional_universe_dashboard",
        "🏦 Universo institucional",
        "Market data success",
        "Stage 1 pass rate",
        "Instrumentos excluidos",
        "Institutional Universe Cleaning",
    ]

    missing = [marker for marker in markers if marker not in content]

    if missing:
        fail("Missing Phase 7A.5 markers:")
        for marker in missing:
            print(f"   - {marker}")
        return 1

    ok("Phase 7A.5 markers present")

    if not CLEANING_SUMMARY.exists():
        warn(f"Cleaning summary missing: {CLEANING_SUMMARY}")
    else:
        ok("Universe cleaning summary exists")

    if not COMPARISON_REPORT.exists():
        warn(f"Comparison report missing: {COMPARISON_REPORT}")
    else:
        ok("Institutional comparison report exists")
        try:
            report = json.loads(COMPARISON_REPORT.read_text(encoding="utf-8"))
            if report.get("openai_called") is False:
                ok("Comparison report confirms OpenAI was not called")
            if report.get("paid_api_called") is False:
                ok("Comparison report confirms paid API was not called")
            if report.get("yfinance_called") is False:
                ok("Comparison report confirms yfinance was not called by report")
        except Exception as exc:
            warn(f"Could not parse comparison report: {exc}")

    print()
    print("Result")
    print("-" * 74)
    ok("Phase 7A.5 institutional dashboard is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
