from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


PHASE = "8I"
DEFAULT_TOP_N = 3
MAX_TOP_N = 3
PROMPT_VERSION = "research_memo_ai_prompt_v0_1"
SCHEMA_VERSION = "equity_research_memo_schema_v0_1"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def now_run_id() -> str:
    return "phase8i_" + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S%z")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def env_true(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "y", "on"}


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def load_prompt_packages(root: Path) -> List[Dict[str, Any]]:
    out = root / "outputs" / "scouting"
    packages = read_json(out / "phase8h_ai_prompt_packages.json", [])
    if not isinstance(packages, list):
        return []
    clean = []
    for item in packages[:MAX_TOP_N]:
        if isinstance(item, dict):
            clean.append(item)
    return clean


def build_gate_decision(root: Path) -> Dict[str, Any]:
    out = root / "outputs" / "scouting"
    previous_gate = read_json(out / "phase8g_ai_interpretation_gate_decision.json", {})
    enable_openai = env_true("ENABLE_OPENAI")
    enable_ai_research_memo = env_true("ENABLE_AI_RESEARCH_MEMO")
    allow_ai_spend = env_true("ALLOW_AI_SPEND")

    # Extra deliberate hard switch for this sandbox phase. This prevents accidental real execution
    # even if the three normal switches are enabled.
    allow_real_execution = env_true("SCOUT_FINANCE_ALLOW_REAL_AI_EXECUTION")

    max_cost_usd = env_float("AI_RESEARCH_MEMO_MAX_COST_USD", 0.0)
    model = os.getenv("AI_RESEARCH_MEMO_MODEL", "").strip() or None

    hard_blockers = []
    if not enable_openai:
        hard_blockers.append("ENABLE_OPENAI is not True")
    if not enable_ai_research_memo:
        hard_blockers.append("ENABLE_AI_RESEARCH_MEMO is not True")
    if not allow_ai_spend:
        hard_blockers.append("ALLOW_AI_SPEND is not True")
    if not allow_real_execution:
        hard_blockers.append("SCOUT_FINANCE_ALLOW_REAL_AI_EXECUTION is not True")
    if max_cost_usd <= 0:
        hard_blockers.append("AI_RESEARCH_MEMO_MAX_COST_USD must be > 0 for real execution")
    if not model:
        hard_blockers.append("AI_RESEARCH_MEMO_MODEL is not configured")

    ai_allowed = len(hard_blockers) == 0
    gate_status = "open" if ai_allowed else "closed"

    return {
        "phase": PHASE,
        "gate_status": gate_status,
        "ai_allowed": ai_allowed,
        "reason": "; ".join(hard_blockers) if hard_blockers else "All explicit AI execution switches are enabled",
        "hard_blockers": hard_blockers,
        "settings": {
            "ENABLE_OPENAI": enable_openai,
            "ENABLE_AI_RESEARCH_MEMO": enable_ai_research_memo,
            "ALLOW_AI_SPEND": allow_ai_spend,
            "SCOUT_FINANCE_ALLOW_REAL_AI_EXECUTION": allow_real_execution,
            "AI_RESEARCH_MEMO_MODEL": model,
            "AI_RESEARCH_MEMO_MAX_COST_USD": max_cost_usd,
            "DEFAULT_TOP_N": DEFAULT_TOP_N,
            "MAX_TOP_N": MAX_TOP_N,
            "previous_gate_status": previous_gate.get("gate_status"),
            "previous_ai_allowed": previous_gate.get("ai_allowed"),
        },
    }


def make_sandbox_execution(package: Dict[str, Any], gate: Dict[str, Any]) -> Dict[str, Any]:
    ticker = str(package.get("ticker", "")).strip().upper()
    company_name = package.get("company_name") or ticker
    user_prompt = package.get("user_prompt", {})
    system_prompt = package.get("system_prompt", "")

    prompt_payload = {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "required_output_contract": {
            "ticker": ticker,
            "memo_status": "complete | data_insufficient",
            "business_model": "objective/interpreted summary based only on supplied data",
            "financial_health": "must separate objective facts from interpretation",
            "valuation_analysis": "must mark data_insufficient if valuation inputs are missing",
            "risk_analysis": "mandatory",
            "bull_case": "must cite supplied inputs",
            "base_case": "must cite supplied inputs",
            "bear_case": "must cite supplied inputs",
            "final_verdict": "not financial advice",
            "confidence": "low | medium | high",
            "data_gaps": "explicit list",
        },
    }

    # Critical: this phase never calls OpenAI. It only prepares the execution envelope.
    if gate.get("ai_allowed"):
        execution_status = "sandbox_ready_but_not_executed"
        skip_reason = "Real AI call intentionally disabled in Phase 8I package; execution envelope only"
    else:
        execution_status = "skipped_gate_closed"
        skip_reason = gate.get("reason") or "AI gate closed"

    simulated_response = {
        "ticker": ticker,
        "memo_status": package.get("memo_status", "data_insufficient"),
        "ai_interpretation_status": execution_status,
        "summary": "No AI response generated. Phase 8I is an execution sandbox and guardrail validation phase.",
        "data_policy": {
            "no_inventar_datos": True,
            "mark_data_insufficient": True,
            "objective_data_only": True,
        },
        "data_gaps": package.get("dry_run_preview", {}).get("data_gaps", []),
    }

    return {
        "phase": PHASE,
        "prompt_version": package.get("prompt_version", PROMPT_VERSION),
        "schema_version": package.get("schema_version", SCHEMA_VERSION),
        "ticker": ticker,
        "company_name": company_name,
        "ranking_position": package.get("ranking_position"),
        "quant_score": package.get("quant_score"),
        "memo_status": package.get("memo_status"),
        "ai_gate_status": gate.get("gate_status"),
        "ai_allowed": bool(gate.get("ai_allowed")),
        "execution_status": execution_status,
        "skip_reason": skip_reason,
        "prompt_payload": prompt_payload,
        "prompt_sha256": sha256_text(json.dumps(prompt_payload, sort_keys=True, ensure_ascii=False)),
        "simulated_response": simulated_response,
        "estimated_cost": 0.0,
        "model_used": None,
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
    }


def write_execution_markdown(path: Path, execution: Dict[str, Any]) -> None:
    ticker = execution.get("ticker", "UNKNOWN")
    lines = [
        f"# AI Execution Sandbox — {ticker}",
        "",
        f"- Phase: {PHASE}",
        f"- Company: {execution.get('company_name')}",
        f"- Ranking position: {execution.get('ranking_position')}",
        f"- Quant score: {execution.get('quant_score')}",
        f"- AI gate status: {execution.get('ai_gate_status')}",
        f"- AI allowed: {execution.get('ai_allowed')}",
        f"- Execution status: {execution.get('execution_status')}",
        f"- Estimated cost: {execution.get('estimated_cost')}",
        f"- Model used: {execution.get('model_used')}",
        f"- OpenAI called: {execution.get('openai_called')}",
        "",
        "## Skip reason",
        "",
        str(execution.get("skip_reason")),
        "",
        "## Safety rules",
        "",
        "- No inventar datos",
        "- Marcar data_insufficient cuando falten datos",
        "- Separar Objective data y AI interpretation",
        "- No financial advice",
        "- TOP N limitado a 3",
        "",
        "## Simulated response",
        "",
        "```json",
        json.dumps(execution.get("simulated_response", {}), indent=2, ensure_ascii=False),
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "ticker",
        "company_name",
        "ranking_position",
        "quant_score",
        "memo_status",
        "ai_gate_status",
        "ai_allowed",
        "execution_status",
        "estimated_cost",
        "model_used",
        "openai_called",
        "execution_json_path",
        "execution_md_path",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def main() -> None:
    root = project_root()
    out = root / "outputs" / "scouting"
    sandbox_dir = out / "research_memo_ai_execution_sandbox"
    run_id = now_run_id()

    packages = load_prompt_packages(root)
    gate = build_gate_decision(root)

    executions: List[Dict[str, Any]] = []
    index_rows: List[Dict[str, Any]] = []

    for idx, package in enumerate(packages[:MAX_TOP_N], start=1):
        execution = make_sandbox_execution(package, gate)
        ticker = execution.get("ticker") or f"UNKNOWN_{idx}"
        json_path = sandbox_dir / f"ai_execution_sandbox_{idx:02d}_{ticker}.json"
        md_path = sandbox_dir / f"ai_execution_sandbox_{idx:02d}_{ticker}.md"

        execution["execution_json_path"] = str(json_path)
        execution["execution_md_path"] = str(md_path)

        write_json(json_path, execution)
        write_execution_markdown(md_path, execution)
        executions.append(execution)

        index_rows.append({
            "ticker": execution.get("ticker"),
            "company_name": execution.get("company_name"),
            "ranking_position": execution.get("ranking_position"),
            "quant_score": execution.get("quant_score"),
            "memo_status": execution.get("memo_status"),
            "ai_gate_status": execution.get("ai_gate_status"),
            "ai_allowed": execution.get("ai_allowed"),
            "execution_status": execution.get("execution_status"),
            "estimated_cost": execution.get("estimated_cost"),
            "model_used": execution.get("model_used"),
            "openai_called": execution.get("openai_called"),
            "execution_json_path": str(json_path),
            "execution_md_path": str(md_path),
        })

    summary = {
        "phase": PHASE,
        "status": "OK",
        "run_id": run_id,
        "default_top_n": DEFAULT_TOP_N,
        "max_top_n": MAX_TOP_N,
        "prompt_packages_loaded": len(packages),
        "sandbox_executions_created": len(executions),
        "ai_gate_status": gate.get("gate_status"),
        "ai_allowed": gate.get("ai_allowed"),
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "pipeline_recalculated": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": False,
        "next": "8J — AI memo integration readiness and final v0.8 candidate audit",
    }

    audit = {
        "phase": PHASE,
        "status": "OK",
        "run_id": run_id,
        "sandbox_directory": str(sandbox_dir),
        "executions_count": len(executions),
        "executions": [
            {
                "ticker": item.get("ticker"),
                "json_path": item.get("execution_json_path"),
                "json_sha256": hashlib.sha256(Path(item.get("execution_json_path")).read_bytes()).hexdigest() if item.get("execution_json_path") and Path(item.get("execution_json_path")).exists() else None,
                "markdown_path": item.get("execution_md_path"),
                "markdown_sha256": hashlib.sha256(Path(item.get("execution_md_path")).read_bytes()).hexdigest() if item.get("execution_md_path") and Path(item.get("execution_md_path")).exists() else None,
                "openai_called": item.get("openai_called"),
                "estimated_cost": item.get("estimated_cost"),
            }
            for item in executions
        ],
    }

    report = f"""# Phase 8I — Optional AI Execution Sandbox

Status: **OK**

## Summary

- Prompt packages loaded: {len(packages)}
- Sandbox executions created: {len(executions)}
- Default TOP N: {DEFAULT_TOP_N}
- MAX TOP N: {MAX_TOP_N}
- AI gate status: {gate.get("gate_status")}
- AI allowed: {gate.get("ai_allowed")}
- OpenAI called: False
- API called: False
- yfinance called: False
- Pipeline recalculated: False

## Scope

Phase 8I creates an execution sandbox envelope for AI memo interpretation.

It does **not** call OpenAI. It does **not** call APIs. It does **not** call yfinance.

## Safety rules

- No inventar datos.
- Mark `data_insufficient` when data is missing.
- Separate Objective data from AI interpretation.
- Keep estimated cost at 0.0 in this phase.
- Keep model_used as null in this phase.
- TOP N remains capped at 3.

## Gate reason

{gate.get("reason")}

## Outputs

- `phase8i_optional_ai_execution_sandbox_summary.json`
- `phase8i_ai_execution_sandbox_decision.json`
- `phase8i_ai_execution_sandbox_results.json`
- `phase8i_ai_execution_sandbox_index.csv`
- `phase8i_ai_execution_sandbox_audit.json`
- `research_memo_ai_execution_sandbox/`

## Next

8J — AI memo integration readiness and final v0.8 candidate audit.
"""

    write_json(out / "phase8i_optional_ai_execution_sandbox_summary.json", summary)
    write_json(out / "phase8i_ai_execution_sandbox_decision.json", gate)
    write_json(out / "phase8i_ai_execution_sandbox_results.json", executions)
    write_csv(out / "phase8i_ai_execution_sandbox_index.csv", index_rows)
    write_json(out / "phase8i_ai_execution_sandbox_audit.json", audit)
    (out / "phase8i_optional_ai_execution_sandbox_report.md").write_text(report, encoding="utf-8")

    print("Scout Finance — Phase 8I Optional AI Execution Sandbox")
    print("=" * 92)
    print()
    print("AI execution sandbox")
    print("-" * 92)
    print(f"Status: OK")
    print(f"Prompt packages loaded: {len(packages)}")
    print(f"Default TOP N: {DEFAULT_TOP_N}")
    print(f"Sandbox executions created: {len(executions)}")
    print(f"AI gate status: {gate.get('gate_status')}")
    print(f"AI allowed: {gate.get('ai_allowed')}")
    print(f"OpenAI called: False")
    print(f"API called: False")
    print(f"yfinance called: False")
    print(f"Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 8I optional AI execution sandbox is complete.")


if __name__ == "__main__":
    main()
