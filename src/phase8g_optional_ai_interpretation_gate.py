from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PHASE = "8G"
TITLE = "Optional AI Interpretation Gate and Cost Guardrails"
DEFAULT_TOP_N = 3
MAX_TOP_N = 3
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_MAX_ESTIMATED_COST_USD = 0.50
SCHEMA_VERSION = "phase8g_ai_gate_v0_1"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError:
        return default


def load_8f_export(root: Path) -> List[Dict[str, Any]]:
    candidates = [
        root / "outputs" / "scouting" / "phase8f_research_memo_export.json",
        root / "outputs" / "scouting" / "phase8f_exported_research_memos.json",
        root / "outputs" / "scouting" / "phase8e_persisted_equity_research_memos.json",
        root / "outputs" / "scouting" / "phase8d_candidate_source_bound_memos.json",
    ]
    for path in candidates:
        data = read_json(path, None)
        if isinstance(data, list):
            return data[:MAX_TOP_N]
    return []


def normalize_memo(memo: Dict[str, Any], index: int) -> Dict[str, Any]:
    ticker = memo.get("ticker") or memo.get("symbol") or f"UNKNOWN_{index}"
    return {
        "ticker": ticker,
        "company_name": memo.get("company_name") or memo.get("name") or ticker,
        "ranking_position": memo.get("ranking_position") or index,
        "quant_score": memo.get("quant_score"),
        "memo_status": memo.get("memo_status") or "data_insufficient",
        "data_gaps_count": len(memo.get("data_gaps") or []),
        "report_path": memo.get("report_path"),
    }


def build_gate_decision(memos: List[Dict[str, Any]]) -> Dict[str, Any]:
    enable_openai = env_bool("ENABLE_OPENAI", False)
    explicit_ai_gate = env_bool("ENABLE_AI_RESEARCH_MEMO", False)
    allow_spend = env_bool("ALLOW_AI_SPEND", False)
    max_cost = env_float("AI_RESEARCH_MEMO_MAX_COST_USD", DEFAULT_MAX_ESTIMATED_COST_USD)
    model = os.getenv("AI_RESEARCH_MEMO_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    hard_blockers = []
    if not enable_openai:
        hard_blockers.append("ENABLE_OPENAI is not True")
    if not explicit_ai_gate:
        hard_blockers.append("ENABLE_AI_RESEARCH_MEMO is not True")
    if not allow_spend:
        hard_blockers.append("ALLOW_AI_SPEND is not True")
    if len(memos) > MAX_TOP_N:
        hard_blockers.append("Memo count exceeds MAX_TOP_N")
    if max_cost <= 0:
        hard_blockers.append("AI_RESEARCH_MEMO_MAX_COST_USD must be positive")

    ai_allowed = len(hard_blockers) == 0
    return {
        "ai_allowed": ai_allowed,
        "gate_status": "open" if ai_allowed else "closed",
        "reason": "All explicit AI and spend gates enabled" if ai_allowed else "; ".join(hard_blockers),
        "hard_blockers": hard_blockers,
        "settings": {
            "ENABLE_OPENAI": enable_openai,
            "ENABLE_AI_RESEARCH_MEMO": explicit_ai_gate,
            "ALLOW_AI_SPEND": allow_spend,
            "AI_RESEARCH_MEMO_MODEL": model,
            "AI_RESEARCH_MEMO_MAX_COST_USD": max_cost,
            "DEFAULT_TOP_N": DEFAULT_TOP_N,
            "MAX_TOP_N": MAX_TOP_N,
        },
    }


def main() -> None:
    root = project_root()
    outputs = root / "outputs" / "scouting"
    phase_dir = outputs / "phase8g"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S%z")

    raw_memos = load_8f_export(root)
    memos = [normalize_memo(memo, i + 1) for i, memo in enumerate(raw_memos[:MAX_TOP_N])]
    gate = build_gate_decision(memos)

    interpretation_plan = []
    for memo in memos:
        interpretation_plan.append({
            **memo,
            "ai_interpretation_status": "eligible_but_not_executed" if gate["ai_allowed"] else "blocked_by_gate",
            "estimated_cost": 0.0,
            "model_used": None,
            "openai_called": False,
            "objective_data_required": True,
            "no_invented_data_rule": True,
        })

    controls = {
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "pipeline_recalculated": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": False,
    }

    source_files = {
        "app.py": str(root / "app.py"),
        "src/filters.py": str(root / "src" / "filters.py"),
        "v0.7_zip": str(root / "releases" / "Scout_Finance_v0.7.0_candidate_FREEZE.zip"),
    }
    signatures = {name: sha256_file(Path(path)) for name, path in source_files.items()}

    summary = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": now,
        "schema_version": SCHEMA_VERSION,
        "default_top_n": DEFAULT_TOP_N,
        "max_top_n": MAX_TOP_N,
        "memos_loaded": len(memos),
        "ai_gate_status": gate["gate_status"],
        "ai_allowed": gate["ai_allowed"],
        "gate_reason": gate["reason"],
        "estimated_cost": 0.0,
        "model_used": None,
        "next": "8H — Prompt packaging and dry-run AI memo preview",
        **controls,
    }

    audit = {
        "phase": PHASE,
        "status": "OK",
        "summary": summary,
        "gate": gate,
        "controls": controls,
        "signatures": signatures,
        "memos": interpretation_plan,
    }

    report_lines = [
        "# Scout Finance — Phase 8G Optional AI Interpretation Gate and Cost Guardrails",
        "",
        "## Status",
        "",
        f"- Status: {summary['status']}",
        f"- Memos loaded: {len(memos)}",
        f"- Default TOP N: {DEFAULT_TOP_N}",
        f"- MAX TOP N: {MAX_TOP_N}",
        f"- AI gate status: {gate['gate_status']}",
        f"- AI allowed: {gate['ai_allowed']}",
        f"- Gate reason: {gate['reason']}",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "- Estimated cost: 0.0",
        "- Model used: null",
        "",
        "## Guardrails",
        "",
        "- ENABLE_OPENAI must be true.",
        "- ENABLE_AI_RESEARCH_MEMO must be true.",
        "- ALLOW_AI_SPEND must be true.",
        "- TOP N is capped at 3.",
        "- No inventar datos.",
        "- Objective data must stay separated from AI interpretation.",
        "- data_insufficient must be preserved when facts are missing.",
        "- This phase does not call OpenAI; it only decides whether a later phase may be allowed to do so.",
        "",
        "## Memos considered",
        "",
    ]
    if interpretation_plan:
        for row in interpretation_plan:
            report_lines.append(f"- {row['ranking_position']}. {row['ticker']} — {row['company_name']} — {row['ai_interpretation_status']}")
    else:
        report_lines.append("- No memos found from 8F/8E/8D outputs.")
    report_lines += [
        "",
        "## Next",
        "",
        "8H — Prompt packaging and dry-run AI memo preview.",
    ]

    write_json(outputs / "phase8g_optional_ai_interpretation_gate_summary.json", summary)
    write_json(outputs / "phase8g_ai_interpretation_gate_decision.json", gate)
    write_json(outputs / "phase8g_ai_interpretation_plan.json", interpretation_plan)
    write_json(outputs / "phase8g_ai_gate_audit.json", audit)
    write_json(phase_dir / "audit.json", audit)
    write_csv(
        outputs / "phase8g_ai_interpretation_plan.csv",
        interpretation_plan,
        [
            "ranking_position", "ticker", "company_name", "quant_score", "memo_status",
            "data_gaps_count", "ai_interpretation_status", "estimated_cost", "model_used", "openai_called", "report_path"
        ],
    )
    (outputs / "phase8g_optional_ai_interpretation_gate_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("Scout Finance — Phase 8G Optional AI Interpretation Gate and Cost Guardrails")
    print("=" * 92)
    print()
    print("AI gate")
    print("-" * 92)
    print(f"Status: {summary['status']}")
    print(f"Memos loaded: {len(memos)}")
    print(f"Default TOP N: {DEFAULT_TOP_N}")
    print(f"AI gate status: {gate['gate_status']}")
    print(f"AI allowed: {gate['ai_allowed']}")
    print(f"Gate reason: {gate['reason']}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 8G optional AI interpretation gate and cost guardrails is complete.")


if __name__ == "__main__":
    main()
