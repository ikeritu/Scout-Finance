"""Checker for Scout Finance Phase 8C deterministic research modules."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "scouting"

REQUIRED_FILES = [
    OUTPUT_DIR / "phase8c_deterministic_research_modules_summary.json",
    OUTPUT_DIR / "phase8c_deterministic_research_modules_report.md",
    OUTPUT_DIR / "phase8c_deterministic_research_memos.json",
    OUTPUT_DIR / "phase8c_deterministic_research_memos.csv",
    OUTPUT_DIR / "phase8c_deterministic_modules_matrix.csv",
    PROJECT_ROOT / "src" / "research_memo.py",
    PROJECT_ROOT / "src" / "fundamentals.py",
    PROJECT_ROOT / "src" / "valuation.py",
    PROJECT_ROOT / "src" / "risk_analysis.py",
    PROJECT_ROOT / "src" / "moat_analysis.py",
    PROJECT_ROOT / "src" / "growth_analysis.py",
    PROJECT_ROOT / "src" / "institutional_view.py",
    PROJECT_ROOT / "src" / "earnings_analysis.py",
]

REQUIRED_MEMO_FIELDS = [
    "ticker",
    "company_name",
    "memo_status",
    "financial_health",
    "moat_analysis",
    "valuation_analysis",
    "growth_analysis",
    "risk_analysis",
    "institutional_view",
    "earnings_analysis",
    "bull_case",
    "base_case",
    "bear_case",
    "final_verdict",
    "confidence",
    "data_gaps",
    "sources",
    "model_used",
    "estimated_cost",
]

REQUIRED_MODULES = [
    "src/research_memo.py",
    "src/fundamentals.py",
    "src/valuation.py",
    "src/risk_analysis.py",
    "src/moat_analysis.py",
    "src/growth_analysis.py",
    "src/institutional_view.py",
    "src/earnings_analysis.py",
]


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")
    raise SystemExit(1)


def main() -> int:
    print("Scout Finance — Phase 8C Deterministic Research Modules checker")
    print("=" * 92)

    for path in REQUIRED_FILES:
        if not path.exists():
            fail(f"File missing: {path}")
        ok(f"File exists: {path}")

    summary = json.loads((OUTPUT_DIR / "phase8c_deterministic_research_modules_summary.json").read_text(encoding="utf-8"))
    if summary.get("phase") != "8C":
        fail("Summary phase is not 8C")
    ok("Summary phase is 8C")

    if summary.get("status") != "OK":
        fail("Summary status is not OK")
    ok("Summary status OK")

    if summary.get("default_top_n") != 3:
        fail("Default TOP N is not 3")
    ok("Default TOP N OK: 3")

    modules = summary.get("modules_created", [])
    for module in REQUIRED_MODULES:
        if module not in modules:
            fail(f"Module not declared in summary: {module}")
        ok(f"Module declared: {module}")

    controls = summary.get("controls", {})
    for control in ["openai_called", "api_called", "yfinance_called", "pipeline_recalculated"]:
        if controls.get(control) is not False:
            fail(f"Control expected False: {control}")
        ok(f"Control OK: {control}=False")

    for control in ["app_modified", "filters_modified", "release_modified"]:
        if controls.get(control) is not False:
            fail(f"Forbidden modification detected: {control}")
        ok(f"Control OK: {control}=False")

    memos = json.loads((OUTPUT_DIR / "phase8c_deterministic_research_memos.json").read_text(encoding="utf-8"))
    if not isinstance(memos, list):
        fail("Memos JSON is not a list")
    ok("Memos JSON is a list")

    if len(memos) > 3:
        fail("More than TOP 3 memos created")
    ok(f"Memos count <= 3: {len(memos)}")

    for memo in memos:
        ticker = memo.get("ticker", "<missing>")
        for field in REQUIRED_MEMO_FIELDS:
            if field not in memo:
                fail(f"Memo {ticker} missing field: {field}")
            ok(f"Memo {ticker} field OK: {field}")

        if memo.get("estimated_cost") != 0.0:
            fail(f"Memo {ticker} estimated_cost is not 0.0")
        ok(f"Memo {ticker} estimated_cost OK")

        if memo.get("model_used") is not None:
            fail(f"Memo {ticker} model_used is not None")
        ok(f"Memo {ticker} model_used OK")

        if "data_gaps" not in memo or not isinstance(memo["data_gaps"], list):
            fail(f"Memo {ticker} data_gaps is not a list")
        ok(f"Memo {ticker} data_gaps list OK")

    matrix_text = (OUTPUT_DIR / "phase8c_deterministic_modules_matrix.csv").read_text(encoding="utf-8")
    for module in REQUIRED_MODULES:
        if module not in matrix_text:
            fail(f"Module missing in matrix: {module}")
        ok(f"Module in matrix: {module}")

    report = (OUTPUT_DIR / "phase8c_deterministic_research_modules_report.md").read_text(encoding="utf-8")
    for phrase in [
        "Phase 8C",
        "No inventar datos",
        "data_insufficient",
        "OpenAI called",
        "TOP N",
        "8D",
    ]:
        if phrase not in report:
            fail(f"Report missing phrase: {phrase}")
        ok(f"Report contains: {phrase}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 8C Deterministic Research Modules is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
