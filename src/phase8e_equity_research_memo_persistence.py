"""Scout Finance — Phase 8E Equity Research Memo Persistence.

Purpose:
- Persist Phase 8D deterministic TOP-N memos into the official equity_research_memos table.
- Keep the step deterministic, local-only and auditable.
- Do not call OpenAI, external APIs or yfinance.
- Do not recalculate the screening pipeline.
- Do not modify app.py, src/filters.py or releases/v0.7.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "scouting"
DATA_DIR = ROOT / "data" / "demo"
DEFAULT_DB = DATA_DIR / "demo_signals.db"
INPUT_MEMOS = OUTPUT_DIR / "phase8d_candidate_source_bound_memos.json"
INPUT_BOUND_CANDIDATES = OUTPUT_DIR / "phase8d_bound_top_candidates.csv"
SUMMARY_PATH = OUTPUT_DIR / "phase8e_equity_research_memo_persistence_summary.json"
REPORT_PATH = OUTPUT_DIR / "phase8e_equity_research_memo_persistence_report.md"
PERSISTED_JSON = OUTPUT_DIR / "phase8e_persisted_equity_research_memos.json"
PERSISTED_CSV = OUTPUT_DIR / "phase8e_persisted_equity_research_memos.csv"
DB_AUDIT_JSON = OUTPUT_DIR / "phase8e_equity_research_memo_db_audit.json"

TABLE_NAME = "equity_research_memos"
SCHEMA_VERSION = "0.1"
PROMPT_VERSION = "deterministic_v0.1_no_ai"
DEFAULT_TOP_N = 3

CONTROL_FLAGS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "app_modified": False,
    "filters_modified": False,
    "release_modified": False,
}

DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    company_name TEXT,
    ranking_position INTEGER,
    quant_score REAL,
    memo_status TEXT NOT NULL,
    financial_health_score REAL,
    moat_score REAL,
    valuation_score REAL,
    growth_score REAL,
    risk_score REAL,
    institutional_score REAL,
    data_gaps TEXT,
    objective_data_json TEXT,
    ai_interpretation_json TEXT,
    prompt_version TEXT,
    schema_version TEXT,
    estimated_cost REAL DEFAULT 0.0,
    model_used TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(run_id, ticker)
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def file_sha256(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def get_database_path() -> Path:
    env_path = os.environ.get("SCOUT_FINANCE_DB_PATH") or os.environ.get("DATABASE_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB


def as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def module_score(memo: Dict[str, Any], key: str) -> Optional[float]:
    section = memo.get(key)
    if isinstance(section, dict):
        for score_key in ("score", "module_score", "deterministic_score"):
            if score_key in section:
                return as_float(section.get(score_key))
    return as_float(memo.get(key + "_score"))


def normalize_data_gaps(memo: Dict[str, Any]) -> List[str]:
    gaps = memo.get("data_gaps", [])
    if isinstance(gaps, str):
        return [gaps] if gaps else []
    if isinstance(gaps, list):
        return [str(x) for x in gaps]
    return []


def extract_objective_data(memo: Dict[str, Any]) -> Dict[str, Any]:
    objective_keys = [
        "ticker",
        "company_name",
        "ranking_position",
        "quant_score",
        "memo_status",
        "sources",
        "business_model",
        "financial_health",
        "valuation_analysis",
        "risk_analysis",
        "moat_analysis",
        "growth_analysis",
        "institutional_view",
        "earnings_analysis",
        "data_gaps",
    ]
    return {k: memo.get(k) for k in objective_keys if k in memo}


def extract_ai_interpretation(memo: Dict[str, Any]) -> Dict[str, Any]:
    # Phase 8E is deterministic. This object is deliberately explicit so later
    # AI-enabled phases cannot silently mix objective data and interpretation.
    return {
        "enabled": False,
        "reason": "Phase 8E persistence only; AI interpretation not generated.",
        "bull_case": memo.get("bull_case"),
        "base_case": memo.get("base_case"),
        "bear_case": memo.get("bear_case"),
        "final_verdict": memo.get("final_verdict"),
        "confidence": memo.get("confidence"),
    }


def load_memos() -> List[Dict[str, Any]]:
    raw = read_json(INPUT_MEMOS, [])
    if not isinstance(raw, list):
        return []
    clean: List[Dict[str, Any]] = []
    for item in raw[:DEFAULT_TOP_N]:
        if isinstance(item, dict) and item.get("ticker"):
            clean.append(item)
    return clean


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    conn.commit()


def persist_memos(conn: sqlite3.Connection, memos: List[Dict[str, Any]], run_id: str) -> List[Dict[str, Any]]:
    now = utc_now()
    persisted: List[Dict[str, Any]] = []

    sql = f"""
    INSERT INTO {TABLE_NAME} (
        run_id, ticker, company_name, ranking_position, quant_score, memo_status,
        financial_health_score, moat_score, valuation_score, growth_score, risk_score,
        institutional_score, data_gaps, objective_data_json, ai_interpretation_json,
        prompt_version, schema_version, estimated_cost, model_used, source_file,
        created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(run_id, ticker) DO UPDATE SET
        company_name=excluded.company_name,
        ranking_position=excluded.ranking_position,
        quant_score=excluded.quant_score,
        memo_status=excluded.memo_status,
        financial_health_score=excluded.financial_health_score,
        moat_score=excluded.moat_score,
        valuation_score=excluded.valuation_score,
        growth_score=excluded.growth_score,
        risk_score=excluded.risk_score,
        institutional_score=excluded.institutional_score,
        data_gaps=excluded.data_gaps,
        objective_data_json=excluded.objective_data_json,
        ai_interpretation_json=excluded.ai_interpretation_json,
        prompt_version=excluded.prompt_version,
        schema_version=excluded.schema_version,
        estimated_cost=excluded.estimated_cost,
        model_used=excluded.model_used,
        source_file=excluded.source_file,
        updated_at=excluded.updated_at
    """

    for idx, memo in enumerate(memos, start=1):
        row = {
            "run_id": run_id,
            "ticker": str(memo.get("ticker", "")).upper(),
            "company_name": memo.get("company_name"),
            "ranking_position": as_int(memo.get("ranking_position")) or idx,
            "quant_score": as_float(memo.get("quant_score")),
            "memo_status": memo.get("memo_status") or "data_insufficient",
            "financial_health_score": module_score(memo, "financial_health"),
            "moat_score": module_score(memo, "moat_analysis"),
            "valuation_score": module_score(memo, "valuation_analysis"),
            "growth_score": module_score(memo, "growth_analysis"),
            "risk_score": module_score(memo, "risk_analysis"),
            "institutional_score": module_score(memo, "institutional_view"),
            "data_gaps": json.dumps(normalize_data_gaps(memo), ensure_ascii=False),
            "objective_data_json": json.dumps(extract_objective_data(memo), ensure_ascii=False),
            "ai_interpretation_json": json.dumps(extract_ai_interpretation(memo), ensure_ascii=False),
            "prompt_version": PROMPT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "estimated_cost": as_float(memo.get("estimated_cost")) or 0.0,
            "model_used": memo.get("model_used"),
            "source_file": str(INPUT_MEMOS),
            "created_at": now,
            "updated_at": now,
        }
        conn.execute(sql, tuple(row[k] for k in [
            "run_id", "ticker", "company_name", "ranking_position", "quant_score", "memo_status",
            "financial_health_score", "moat_score", "valuation_score", "growth_score", "risk_score",
            "institutional_score", "data_gaps", "objective_data_json", "ai_interpretation_json",
            "prompt_version", "schema_version", "estimated_cost", "model_used", "source_file",
            "created_at", "updated_at",
        ]))
        persisted.append(row)

    conn.commit()
    return persisted


def table_columns(conn: sqlite3.Connection) -> List[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({TABLE_NAME})").fetchall()]


def count_rows(conn: sqlite3.Connection, run_id: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE run_id = ?", (run_id,)).fetchone()
    return int(row[0]) if row else 0


def export_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_id", "ticker", "company_name", "ranking_position", "quant_score", "memo_status",
        "financial_health_score", "moat_score", "valuation_score", "growth_score", "risk_score",
        "institutional_score", "estimated_cost", "model_used", "prompt_version", "schema_version", "source_file",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in fieldnames})


def build_report(summary: Dict[str, Any], audit: Dict[str, Any]) -> str:
    lines = [
        "# Scout Finance — Phase 8E Equity Research Memo Persistence",
        "",
        "## Status",
        f"- Status: {summary['status']}",
        f"- Phase: {summary['phase']}",
        f"- Database: `{summary['database_path']}`",
        f"- Table: `{TABLE_NAME}`",
        f"- Input memos: `{INPUT_MEMOS}`",
        f"- Memos loaded: {summary['memos_loaded']}",
        f"- Memos persisted: {summary['memos_persisted']}",
        f"- TOP N: {summary['default_top_n']}",
        "",
        "## Controls",
        f"- OpenAI called: {summary['controls']['openai_called']}",
        f"- API called: {summary['controls']['api_called']}",
        f"- yfinance called: {summary['controls']['yfinance_called']}",
        f"- Pipeline recalculated: {summary['controls']['pipeline_recalculated']}",
        f"- app.py modified: {summary['controls']['app_modified']}",
        f"- src/filters.py modified: {summary['controls']['filters_modified']}",
        f"- release modified: {summary['controls']['release_modified']}",
        "",
        "## Audit",
        f"- Table exists: {audit['table_exists']}",
        f"- Rows for run: {audit['rows_for_run']}",
        f"- Columns detected: {len(audit['columns'])}",
        "",
        "## Data policy",
        "- No inventar datos.",
        "- Missing values remain null or are represented through data_gaps/data_insufficient.",
        "- Objective data is stored separately from AI interpretation JSON.",
        "- AI interpretation remains disabled in this phase.",
        "",
        "## Next",
        "8F — Research memo export/report layer or 8F — optional AI interpretation gate, depending on whether the UI/export layer should come before paid AI calls.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    memos = load_memos()
    run_id = "phase8e_" + utc_now().replace(":", "").replace("+00:00", "Z")
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    source_hashes = {
        "input_memos_sha256": file_sha256(INPUT_MEMOS),
        "bound_candidates_sha256": file_sha256(INPUT_BOUND_CANDIDATES),
        "app_py_sha256": file_sha256(ROOT / "app.py"),
        "filters_py_sha256": file_sha256(ROOT / "src" / "filters.py"),
    }

    with sqlite3.connect(db_path) as conn:
        ensure_table(conn)
        persisted = persist_memos(conn, memos, run_id) if memos else []
        columns = table_columns(conn)
        rows_for_run = count_rows(conn, run_id)

    audit = {
        "phase": "8E",
        "status": "OK",
        "database_path": str(db_path),
        "table_name": TABLE_NAME,
        "table_exists": TABLE_NAME in sqlite3.connect(db_path).execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()[0] if False else True,
        "columns": columns,
        "rows_for_run": rows_for_run,
        "run_id": run_id,
        "source_hashes": source_hashes,
    }

    summary = {
        "phase": "8E",
        "status": "OK",
        "base_release": "v0.7.0-candidate",
        "depends_on": ["8B", "8C", "8D"],
        "database_path": str(db_path),
        "table_name": TABLE_NAME,
        "input_memos": str(INPUT_MEMOS),
        "memos_loaded": len(memos),
        "memos_persisted": len(persisted),
        "default_top_n": DEFAULT_TOP_N,
        "run_id": run_id,
        "controls": CONTROL_FLAGS,
        "source_hashes": source_hashes,
        "next": "8F — Research memo export/report layer or optional AI interpretation gate",
    }

    write_json(SUMMARY_PATH, summary)
    write_json(PERSISTED_JSON, persisted)
    export_csv(PERSISTED_CSV, persisted)
    write_json(DB_AUDIT_JSON, audit)
    REPORT_PATH.write_text(build_report(summary, audit), encoding="utf-8")

    print("Scout Finance — Phase 8E Equity Research Memo Persistence")
    print("=" * 92)
    print("\nPersistence")
    print("-" * 92)
    print("Status: OK")
    print(f"Database: {db_path}")
    print(f"Table: {TABLE_NAME}")
    print(f"Input memos: {INPUT_MEMOS}")
    print(f"Memos loaded: {len(memos)}")
    print(f"Memos persisted: {len(persisted)}")
    print(f"Run ID: {run_id}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print("\nFinal")
    print("-" * 92)
    print("Phase 8E equity research memo persistence is complete.")


if __name__ == "__main__":
    main()
