from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, List

PHASE = "8G"
DEFAULT_TOP_N = 3
MAX_TOP_N = 3


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    raise AssertionError(message)


def require_file(path: Path) -> None:
    if not path.exists():
        fail(f"Missing file: {path}")
    ok(f"File exists: {path}")


def require_contains(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        fail(f"Report missing text: {text}")
    ok(f"Report contains: {text}")


def main() -> None:
    base = root()
    outputs = base / "outputs" / "scouting"
    summary_path = outputs / "phase8g_optional_ai_interpretation_gate_summary.json"
    report_path = outputs / "phase8g_optional_ai_interpretation_gate_report.md"
    decision_path = outputs / "phase8g_ai_interpretation_gate_decision.json"
    plan_json_path = outputs / "phase8g_ai_interpretation_plan.json"
    plan_csv_path = outputs / "phase8g_ai_interpretation_plan.csv"
    audit_path = outputs / "phase8g_ai_gate_audit.json"

    print("Scout Finance — Phase 8G Optional AI Interpretation Gate checker")
    print("=" * 92)

    for path in [summary_path, report_path, decision_path, plan_json_path, plan_csv_path, audit_path]:
        require_file(path)

    require_file(base / "src" / "phase8g_optional_ai_interpretation_gate.py")
    require_file(base / "src" / "research_memo.py")

    summary = load_json(summary_path)
    decision = load_json(decision_path)
    plan = load_json(plan_json_path)
    audit = load_json(audit_path)

    if summary.get("phase") != PHASE:
        fail("Summary phase is not 8G")
    ok("Summary phase is 8G")

    if summary.get("status") != "OK":
        fail("Summary status is not OK")
    ok("Summary status OK")

    if summary.get("default_top_n") != DEFAULT_TOP_N:
        fail("Default TOP N is not 3")
    ok("Default TOP N OK: 3")

    if summary.get("max_top_n") != MAX_TOP_N:
        fail("MAX TOP N is not 3")
    ok("MAX TOP N OK: 3")

    for key in ["openai_called", "api_called", "yfinance_called", "pipeline_recalculated", "app_modified", "filters_modified", "release_modified"]:
        if summary.get(key) is not False:
            fail(f"Control not false: {key}")
        ok(f"Control OK: {key}=False")

    if not isinstance(plan, list):
        fail("Interpretation plan is not a list")
    ok("Interpretation plan is a list")

    if len(plan) > MAX_TOP_N:
        fail("Interpretation plan exceeds TOP 3")
    ok(f"Interpretation plan count <= 3: {len(plan)}")

    if summary.get("memos_loaded") != len(plan):
        fail("Summary memos_loaded does not match plan count")
    ok("Summary memos_loaded matches plan count")

    if not isinstance(decision, dict):
        fail("Decision is not a dict")
    ok("Decision is a dict")

    for field in ["ai_allowed", "gate_status", "reason", "hard_blockers", "settings"]:
        if field not in decision:
            fail(f"Decision missing field: {field}")
        ok(f"Decision field OK: {field}")

    if decision.get("settings", {}).get("MAX_TOP_N") != MAX_TOP_N:
        fail("Decision MAX_TOP_N is not 3")
    ok("Decision MAX_TOP_N OK")

    for row in plan:
        ticker = row.get("ticker", "UNKNOWN")
        for field in ["ticker", "company_name", "ranking_position", "memo_status", "ai_interpretation_status", "estimated_cost", "model_used", "openai_called"]:
            if field not in row:
                fail(f"Memo missing field {ticker}::{field}")
            ok(f"Memo field OK: {ticker}::{field}")
        if row.get("estimated_cost") != 0.0:
            fail(f"Memo estimated_cost is not 0.0: {ticker}")
        ok(f"Memo cost OK: {ticker}")
        if row.get("model_used") is not None:
            fail(f"Memo model_used is not null: {ticker}")
        ok(f"Memo model_used OK: {ticker}")
        if row.get("openai_called") is not False:
            fail(f"Memo openai_called is not false: {ticker}")
        ok(f"Memo openai_called OK: {ticker}")

    with plan_csv_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != len(plan):
        fail("CSV row count does not match plan JSON")
    ok("CSV row count matches plan JSON")

    if audit.get("phase") != PHASE:
        fail("Audit phase is not 8G")
    ok("Audit phase OK")
    if audit.get("status") != "OK":
        fail("Audit status is not OK")
    ok("Audit status OK")

    for text in [
        "Phase 8G",
        "AI gate status",
        "OpenAI called: False",
        "No inventar datos",
        "data_insufficient",
        "Objective data",
        "AI interpretation",
        "8H",
    ]:
        require_contains(report_path, text)

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 8G Optional AI Interpretation Gate and Cost Guardrails is valid")


if __name__ == "__main__":
    main()
