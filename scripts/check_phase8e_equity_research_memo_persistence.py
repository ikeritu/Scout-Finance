"""Checker for Scout Finance Phase 8E Equity Research Memo Persistence."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUTPUT_DIR / "phase8e_equity_research_memo_persistence_summary.json"
REPORT_PATH = OUTPUT_DIR / "phase8e_equity_research_memo_persistence_report.md"
PERSISTED_JSON = OUTPUT_DIR / "phase8e_persisted_equity_research_memos.json"
PERSISTED_CSV = OUTPUT_DIR / "phase8e_persisted_equity_research_memos.csv"
DB_AUDIT_JSON = OUTPUT_DIR / "phase8e_equity_research_memo_db_audit.json"
TABLE_NAME = "equity_research_memos"
REQUIRED_DB_COLUMNS = [
    "run_id", "ticker", "company_name", "ranking_position", "quant_score", "memo_status",
    "financial_health_score", "moat_score", "valuation_score", "growth_score", "risk_score",
    "institutional_score", "data_gaps", "objective_data_json", "ai_interpretation_json",
    "prompt_version", "schema_version", "estimated_cost", "model_used",
]

errors: List[str] = []


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")
    errors.append(msg)


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def require_file(path: Path) -> None:
    if path.exists():
        ok(f"File exists: {path}")
    else:
        fail(f"Missing file: {path}")


def check() -> None:
    print("Scout Finance — Phase 8E Equity Research Memo Persistence checker")
    print("=" * 92)

    for path in [SUMMARY_PATH, REPORT_PATH, PERSISTED_JSON, PERSISTED_CSV, DB_AUDIT_JSON, ROOT / "src" / "phase8e_equity_research_memo_persistence.py"]:
        require_file(path)

    summary: Dict[str, Any] = read_json(SUMMARY_PATH, {})
    audit: Dict[str, Any] = read_json(DB_AUDIT_JSON, {})
    persisted = read_json(PERSISTED_JSON, [])

    if summary.get("phase") == "8E": ok("Summary phase is 8E")
    else: fail("Summary phase is not 8E")

    if summary.get("status") == "OK": ok("Summary status OK")
    else: fail("Summary status is not OK")

    if summary.get("default_top_n") == 3: ok("Default TOP N OK: 3")
    else: fail("Default TOP N is not 3")

    controls = summary.get("controls", {})
    for key in ["openai_called", "api_called", "yfinance_called", "pipeline_recalculated", "app_modified", "filters_modified", "release_modified"]:
        if controls.get(key) is False:
            ok(f"Control OK: {key}=False")
        else:
            fail(f"Control not false: {key}")

    if isinstance(persisted, list):
        ok("Persisted JSON is a list")
        if len(persisted) <= 3:
            ok(f"Persisted count <= 3: {len(persisted)}")
        else:
            fail(f"Persisted count > 3: {len(persisted)}")
    else:
        fail("Persisted JSON is not a list")
        persisted = []

    db_path = Path(summary.get("database_path", ""))
    run_id = summary.get("run_id")
    if db_path.exists():
        ok(f"Database exists: {db_path}")
        with sqlite3.connect(db_path) as conn:
            table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_NAME,)).fetchone()
            if table:
                ok(f"Table exists: {TABLE_NAME}")
            else:
                fail(f"Table missing: {TABLE_NAME}")

            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({TABLE_NAME})").fetchall()] if table else []
            for col in REQUIRED_DB_COLUMNS:
                if col in cols:
                    ok(f"DB column OK: {col}")
                else:
                    fail(f"DB column missing: {col}")

            if run_id and table:
                count = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE run_id=?", (run_id,)).fetchone()[0]
                if count == summary.get("memos_persisted"):
                    ok(f"Rows for run match summary: {count}")
                else:
                    fail(f"Rows for run mismatch: db={count} summary={summary.get('memos_persisted')}")
                if count <= 3:
                    ok(f"Rows for run <= 3: {count}")
                else:
                    fail(f"Rows for run > 3: {count}")
    else:
        fail(f"Database missing: {db_path}")

    if audit.get("table_name") == TABLE_NAME:
        ok("Audit table name OK")
    else:
        fail("Audit table name mismatch")

    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else ""
    for phrase in ["Phase 8E", "equity_research_memos", "No inventar datos", "OpenAI called", "Objective data", "AI interpretation", "8F"]:
        if phrase in report:
            ok(f"Report contains: {phrase}")
        else:
            fail(f"Report missing: {phrase}")

    print("\nResult")
    print("-" * 92)
    if errors:
        print("FAIL Phase 8E Equity Research Memo Persistence is not valid")
        sys.exit(1)
    print("OK   Phase 8E Equity Research Memo Persistence is valid")


if __name__ == "__main__":
    check()
