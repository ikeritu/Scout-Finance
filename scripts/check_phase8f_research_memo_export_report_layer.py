"""Checker for Scout Finance Phase 8F Research Memo Export/Report Layer."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "scouting"
REPORTS_DIR = OUTPUT_DIR / "research_memos"
PHASE = "8F"
DEFAULT_TOP_N = 3

REQUIRED_FILES = [
    OUTPUT_DIR / "phase8f_research_memo_export_report_layer_summary.json",
    OUTPUT_DIR / "phase8f_research_memo_export_report_layer_report.md",
    OUTPUT_DIR / "phase8f_research_memo_export_report_layer_export.json",
    OUTPUT_DIR / "phase8f_research_memo_export_report_layer_index.csv",
    OUTPUT_DIR / "phase8f_research_memo_export_report_layer_audit.json",
    PROJECT_ROOT / "src" / "phase8f_research_memo_export_report_layer.py",
]

REQUIRED_REPORT_PHRASES = [
    "Phase 8F",
    "Reports created",
    "No inventar datos",
    "data_insufficient",
    "Objective data",
    "AI interpretation",
    "8G",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    raise AssertionError(msg)


def assert_true(condition: bool, msg: str) -> None:
    if condition:
        ok(msg)
    else:
        fail(msg)


def main() -> None:
    print("Scout Finance — Phase 8F Research Memo Export/Report Layer checker")
    print("=" * 92)

    for path in REQUIRED_FILES:
        assert_true(path.exists(), f"File exists: {path}")

    summary = load_json(OUTPUT_DIR / "phase8f_research_memo_export_report_layer_summary.json")
    export = load_json(OUTPUT_DIR / "phase8f_research_memo_export_report_layer_export.json")
    audit = load_json(OUTPUT_DIR / "phase8f_research_memo_export_report_layer_audit.json")

    assert_true(summary.get("phase") == PHASE, "Summary phase is 8F")
    assert_true(summary.get("status") == "OK", "Summary status OK")
    assert_true(summary.get("default_top_n") == DEFAULT_TOP_N, "Default TOP N OK: 3")
    assert_true(summary.get("source") is not None, "Source is bound")
    assert_true(summary.get("memos_loaded", 0) >= 1, f"Memos loaded >= 1: {summary.get('memos_loaded')}")
    assert_true(summary.get("reports_created", 0) >= 1, f"Reports created >= 1: {summary.get('reports_created')}")
    assert_true(summary.get("reports_created", 0) <= DEFAULT_TOP_N, f"Reports created <= 3: {summary.get('reports_created')}")

    controls = summary.get("controls", {})
    for key in [
        "openai_called",
        "api_called",
        "yfinance_called",
        "pipeline_recalculated",
        "app_modified",
        "filters_modified",
        "release_modified",
    ]:
        assert_true(controls.get(key) is False, f"Control OK: {key}=False")

    assert_true(isinstance(export, list), "Export JSON is a list")
    assert_true(len(export) == summary.get("reports_created"), "Export count matches reports_created")
    assert_true(len(export) <= DEFAULT_TOP_N, f"Export count <= 3: {len(export)}")

    required_memo_fields = [
        "ticker",
        "company_name",
        "ranking_position",
        "quant_score",
        "memo_status",
        "scores",
        "data_gaps",
        "objective_data",
        "ai_interpretation",
        "estimated_cost",
        "model_used",
        "report_path",
    ]
    for memo in export:
        ticker = memo.get("ticker", "UNKNOWN")
        for field in required_memo_fields:
            assert_true(field in memo, f"Memo field OK: {ticker}::{field}")
        assert_true(memo.get("estimated_cost") == 0.0, f"Memo cost OK: {ticker}")
        assert_true(memo.get("model_used") is None, f"Memo model_used OK: {ticker}")
        report_path = Path(memo.get("report_path"))
        assert_true(report_path.exists(), f"Memo report exists: {ticker}")
        text = report_path.read_text(encoding="utf-8")
        for phrase in ["Equity Research Memo", "Objective data", "AI interpretation", "Data gaps", "OpenAI called: False"]:
            assert_true(phrase in text, f"Memo report contains {phrase}: {ticker}")

    assert_true(REPORTS_DIR.exists(), f"Reports directory exists: {REPORTS_DIR}")

    with (OUTPUT_DIR / "phase8f_research_memo_export_report_layer_index.csv").open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert_true(len(rows) == len(export), "Index CSV row count matches export")

    assert_true(audit.get("phase") == PHASE, "Audit phase OK")
    assert_true(audit.get("status") == "OK", "Audit status OK")
    assert_true(len(audit.get("reports", [])) == len(export), "Audit reports count matches export")
    for row in audit.get("reports", []):
        assert_true(row.get("report_exists") is True, f"Audit report exists: {row.get('ticker')}")
        assert_true(bool(row.get("report_sha256")), f"Audit report sha256 present: {row.get('ticker')}")

    report_text = (OUTPUT_DIR / "phase8f_research_memo_export_report_layer_report.md").read_text(encoding="utf-8")
    for phrase in REQUIRED_REPORT_PHRASES:
        assert_true(phrase in report_text, f"Report contains: {phrase}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 8F Research Memo Export/Report Layer is valid")


if __name__ == "__main__":
    main()
