"""
Scout Finance — Phase 8F Research Memo Export/Report Layer

Purpose:
- Read persisted equity research memos from Phase 8E outputs / SQLite DB.
- Export readable deterministic memo reports for the TOP 3.
- Produce Markdown, CSV index, JSON export, and summary/report audit files.

Hard constraints:
- No OpenAI calls.
- No external APIs.
- No yfinance calls.
- No pipeline recalculation.
- Do not modify app.py, src/filters.py, or releases/v0.7.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "scouting"
REPORTS_DIR = OUTPUT_DIR / "research_memos"
DB_PATH = PROJECT_ROOT / "data" / "demo" / "demo_signals.db"
TABLE_NAME = "equity_research_memos"
DEFAULT_TOP_N = 3
PHASE = "8F"

CONTROL_FLAGS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "app_modified": False,
    "filters_modified": False,
    "release_modified": False,
}


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S+0000")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def file_sha256(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def safe_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except Exception:
        return None


def parse_json_field(value: Any, fallback: Any) -> Any:
    if value is None or value == "":
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return fallback


def load_persisted_memos() -> Dict[str, Any]:
    """Prefer the Phase 8E JSON output. Fall back to the SQLite table if needed."""
    source_json = OUTPUT_DIR / "phase8e_persisted_equity_research_memos.json"
    memos = read_json(source_json, default=[])
    if isinstance(memos, list) and memos:
        return {"source": str(source_json), "source_type": "phase8e_json", "memos": memos[:DEFAULT_TOP_N]}

    if not DB_PATH.exists():
        return {"source": None, "source_type": None, "memos": []}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_NAME,)
        ).fetchone()
        if not table_exists:
            return {"source": None, "source_type": None, "memos": []}

        rows = conn.execute(
            f"""
            SELECT *
            FROM {TABLE_NAME}
            ORDER BY COALESCE(ranking_position, 999999), COALESCE(quant_score, -999999) DESC
            LIMIT ?
            """,
            (DEFAULT_TOP_N,),
        ).fetchall()
    finally:
        conn.close()

    db_memos: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["objective_data"] = parse_json_field(item.get("objective_data_json"), {})
        item["ai_interpretation"] = parse_json_field(item.get("ai_interpretation_json"), {})
        item["data_gaps"] = parse_json_field(item.get("data_gaps"), [])
        db_memos.append(item)
    return {"source": str(DB_PATH), "source_type": "sqlite_table", "memos": db_memos}


def normalize_memo(raw: Dict[str, Any], index: int) -> Dict[str, Any]:
    objective_data = raw.get("objective_data") or parse_json_field(raw.get("objective_data_json"), {})
    ai_interpretation = raw.get("ai_interpretation") or parse_json_field(raw.get("ai_interpretation_json"), {})
    data_gaps = raw.get("data_gaps")
    if isinstance(data_gaps, str):
        data_gaps = parse_json_field(data_gaps, [data_gaps] if data_gaps else [])
    if not isinstance(data_gaps, list):
        data_gaps = []

    ticker = str(raw.get("ticker") or "UNKNOWN").upper()
    company_name = str(raw.get("company_name") or ticker)
    ranking_position = safe_int(raw.get("ranking_position")) or index
    quant_score = safe_float(raw.get("quant_score"))

    scores = {
        "financial_health_score": safe_float(raw.get("financial_health_score")),
        "moat_score": safe_float(raw.get("moat_score")),
        "valuation_score": safe_float(raw.get("valuation_score")),
        "growth_score": safe_float(raw.get("growth_score")),
        "risk_score": safe_float(raw.get("risk_score")),
        "institutional_score": safe_float(raw.get("institutional_score")),
    }

    memo_status = raw.get("memo_status") or "data_insufficient"
    estimated_cost = safe_float(raw.get("estimated_cost"))
    if estimated_cost is None:
        estimated_cost = 0.0

    model_used = raw.get("model_used")
    if model_used in ("", "None"):
        model_used = None

    sources = raw.get("sources")
    if isinstance(sources, str):
        sources = parse_json_field(sources, [sources] if sources else [])
    if not isinstance(sources, list):
        sources = []

    return {
        "ticker": ticker,
        "company_name": company_name,
        "ranking_position": ranking_position,
        "quant_score": quant_score,
        "memo_status": memo_status,
        "scores": scores,
        "data_gaps": data_gaps,
        "objective_data": objective_data if isinstance(objective_data, dict) else {},
        "ai_interpretation": ai_interpretation if isinstance(ai_interpretation, dict) else {},
        "sources": sources,
        "estimated_cost": estimated_cost,
        "model_used": model_used,
        "schema_version": raw.get("schema_version"),
        "prompt_version": raw.get("prompt_version"),
        "run_id": raw.get("run_id"),
    }


def fmt_value(value: Any) -> str:
    if value is None:
        return "data_insufficient"
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False) + "`"
    return str(value)


def render_memo_markdown(memo: Dict[str, Any]) -> str:
    scores = memo["scores"]
    data_gaps = memo["data_gaps"] or ["No explicit data gaps listed, but memo remains deterministic-only."]
    objective_data = memo["objective_data"]
    ai_interpretation = memo["ai_interpretation"]
    sources = memo["sources"] or ["phase8d_candidate_source_bound_memos.json / equity_research_memos"]

    lines: List[str] = []
    lines.append(f"# Equity Research Memo — {memo['ticker']}")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Company: {memo['company_name']}")
    lines.append(f"- Ranking position: {fmt_value(memo['ranking_position'])}")
    lines.append(f"- Quant score: {fmt_value(memo['quant_score'])}")
    lines.append(f"- Memo status: `{memo['memo_status']}`")
    lines.append(f"- Estimated AI cost: {fmt_value(memo['estimated_cost'])}")
    lines.append(f"- Model used: {fmt_value(memo['model_used'])}")
    lines.append("")
    lines.append("## Deterministic module scores")
    lines.append("")
    lines.append("| Module | Score |")
    lines.append("|---|---:|")
    for key, value in scores.items():
        lines.append(f"| {key} | {fmt_value(value)} |")
    lines.append("")
    lines.append("## Objective data")
    lines.append("")
    if objective_data:
        for key in sorted(objective_data.keys()):
            lines.append(f"- {key}: {fmt_value(objective_data.get(key))}")
    else:
        lines.append("- data_insufficient: No objective data payload available beyond ranking fields.")
    lines.append("")
    lines.append("## AI interpretation")
    lines.append("")
    if ai_interpretation:
        for key in sorted(ai_interpretation.keys()):
            lines.append(f"- {key}: {fmt_value(ai_interpretation.get(key))}")
    else:
        lines.append("- Not generated. ENABLE_OPENAI was not used in this phase.")
    lines.append("")
    lines.append("## Data gaps")
    lines.append("")
    for gap in data_gaps:
        lines.append(f"- {fmt_value(gap)}")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    for source in sources:
        lines.append(f"- {fmt_value(source)}")
    lines.append("")
    lines.append("## Controls")
    lines.append("")
    lines.append("- OpenAI called: False")
    lines.append("- API called: False")
    lines.append("- yfinance called: False")
    lines.append("- Pipeline recalculated: False")
    lines.append("- No inventar datos: enforced by data_insufficient reporting")
    lines.append("")
    return "\n".join(lines)


def write_csv_index(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ranking_position",
        "ticker",
        "company_name",
        "quant_score",
        "memo_status",
        "report_path",
        "estimated_cost",
        "model_used",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in fieldnames})


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    source_payload = load_persisted_memos()
    raw_memos = source_payload["memos"]
    normalized = [normalize_memo(m, i + 1) for i, m in enumerate(raw_memos[:DEFAULT_TOP_N])]

    exported: List[Dict[str, Any]] = []
    for memo in normalized:
        report_name = f"equity_research_memo_{memo['ranking_position']:02d}_{memo['ticker']}.md"
        report_path = REPORTS_DIR / report_name
        report_path.write_text(render_memo_markdown(memo), encoding="utf-8")
        exported.append({**memo, "report_path": str(report_path)})

    run_id = f"phase8f_{utc_now_compact()}"
    summary = {
        "phase": PHASE,
        "status": "OK",
        "run_id": run_id,
        "default_top_n": DEFAULT_TOP_N,
        "source": source_payload["source"],
        "source_type": source_payload["source_type"],
        "memos_loaded": len(raw_memos),
        "reports_created": len(exported),
        "reports_dir": str(REPORTS_DIR),
        "top_tickers": [m["ticker"] for m in exported],
        "controls": CONTROL_FLAGS,
        "signatures": {
            "app_py_sha256": file_sha256(PROJECT_ROOT / "app.py"),
            "filters_py_sha256": file_sha256(PROJECT_ROOT / "src" / "filters.py"),
        },
        "next_phase": "8G — Optional AI interpretation gate and cost guardrails",
    }

    write_json(OUTPUT_DIR / "phase8f_research_memo_export_report_layer_summary.json", summary)
    write_json(OUTPUT_DIR / "phase8f_research_memo_export_report_layer_export.json", exported)
    write_csv_index(OUTPUT_DIR / "phase8f_research_memo_export_report_layer_index.csv", exported)

    audit = {
        "phase": PHASE,
        "status": "OK",
        "reports": [
            {
                "ticker": item["ticker"],
                "ranking_position": item["ranking_position"],
                "report_path": item["report_path"],
                "report_exists": Path(item["report_path"]).exists(),
                "report_sha256": file_sha256(Path(item["report_path"])),
            }
            for item in exported
        ],
        "controls": CONTROL_FLAGS,
    }
    write_json(OUTPUT_DIR / "phase8f_research_memo_export_report_layer_audit.json", audit)

    report_lines = [
        "# Scout Finance — Phase 8F Research Memo Export/Report Layer",
        "",
        "## Status",
        "",
        "Phase 8F completed with status: OK.",
        "",
        "## Input",
        "",
        f"- Source: {source_payload['source']}",
        f"- Source type: {source_payload['source_type']}",
        f"- Memos loaded: {len(raw_memos)}",
        "",
        "## Output",
        "",
        f"- Reports created: {len(exported)}",
        f"- Reports directory: {REPORTS_DIR}",
        f"- Index CSV: {OUTPUT_DIR / 'phase8f_research_memo_export_report_layer_index.csv'}",
        "",
        "## Controls",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "- app.py modified: False",
        "- src/filters.py modified: False",
        "- releases/v0.7 modified: False",
        "",
        "## Notes",
        "",
        "- No inventar datos: missing information remains marked as data_insufficient.",
        "- Objective data and AI interpretation remain separated.",
        "- This phase creates readable deterministic reports before enabling any optional AI layer.",
        "",
        "## Next",
        "",
        "8G — Optional AI interpretation gate and cost guardrails.",
        "",
    ]
    (OUTPUT_DIR / "phase8f_research_memo_export_report_layer_report.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    print("Scout Finance — Phase 8F Research Memo Export/Report Layer")
    print("=" * 92)
    print()
    print("Export/report")
    print("-" * 92)
    print("Status: OK")
    print(f"Source: {source_payload['source']}")
    print(f"Source type: {source_payload['source_type']}")
    print(f"Memos loaded: {len(raw_memos)}")
    print(f"Reports created: {len(exported)}")
    print(f"Reports dir: {REPORTS_DIR}")
    print(f"Top tickers: {', '.join(summary['top_tickers']) if summary['top_tickers'] else 'None'}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 8F research memo export/report layer is complete.")


if __name__ == "__main__":
    main()
