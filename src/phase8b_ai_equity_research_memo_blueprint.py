
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"
SCHEMAS_DIR = ROOT / "schemas"
SUMMARY_PATH = OUT_DIR / "phase8b_ai_equity_research_memo_blueprint_summary.json"
REPORT_PATH = OUT_DIR / "phase8b_ai_equity_research_memo_blueprint_report.md"
MODULE_MATRIX_PATH = OUT_DIR / "phase8b_ai_equity_research_memo_modules_matrix.csv"
DB_SCHEMA_PATH = OUT_DIR / "phase8b_equity_research_memos_table_schema.json"
MEMO_SCHEMA_PATH = SCHEMAS_DIR / "equity_research_memo_schema_v0_1.json"
APP_PATH = ROOT / "app.py"
FILTERS_PATH = ROOT / "src" / "filters.py"
RELEASE_LOCK_PATH = ROOT / "releases" / "v0.7" / "RELEASE_LOCK_v0.7.json"
PHASE8A_SUMMARY_PATH = OUT_DIR / "phase8a_dashboard_final_design_summary.json"

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def sig(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "size": None, "mtime": None}
    s = path.stat()
    return {"exists": True, "size": s.st_size, "mtime": s.st_mtime}

def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    lines = [",".join(headers)]
    for r in rows:
        lines.append(",".join(f'"{str(r.get(h, "")).replace(chr(34), chr(34)*2)}"' for h in headers))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def memo_schema() -> dict:
    return {
        "schema_name": "equity_research_memo",
        "schema_version": "0.1",
        "default_scope": "TOP_3_RANKING_CANDIDATES",
        "memo_status_allowed_values": ["completed", "ai_disabled", "data_insufficient", "error", "draft"],
        "confidence_allowed_values": ["low", "medium", "high"],
        "verdict_allowed_values": ["strong_research_candidate", "watchlist", "avoid", "data_insufficient"],
        "required_fields": [
            "ticker", "company_name", "memo_status", "ranking_position", "quant_score",
            "business_model", "revenue_sources", "sector_trends", "financial_health",
            "moat_analysis", "valuation_analysis", "growth_analysis", "risk_analysis",
            "institutional_view", "bull_case", "base_case", "bear_case",
            "final_verdict", "confidence", "data_gaps", "sources", "created_at",
            "model_used", "estimated_cost"
        ],
        "anti_hallucination_rules": [
            "Never invent missing financial data.",
            "If a field is unavailable, return data_insufficient.",
            "Separate objective data, interpretation and AI opinion.",
            "Every final verdict must include data_gaps and confidence.",
            "No DCF in v0.1 except as future placeholder.",
            "No buy/sell language. Use research_candidate/watchlist/avoid."
        ],
        "sections": {
            "objective_data": ["market_cap", "sector", "industry", "price", "revenue_growth", "net_income", "free_cash_flow", "margins", "debt_metrics", "valuation_multiples", "data_quality_flags"],
            "interpretation": ["financial_health_summary", "valuation_summary", "growth_summary", "moat_summary", "institutional_summary"],
            "ai_opinion": ["bull_case", "base_case", "bear_case", "anti_thesis", "final_verdict", "confidence"],
            "risk_analysis": ["economic_risks", "competitive_risks", "regulatory_risks", "debt_risks", "valuation_risks", "technology_disruption_risks", "risk_ranking"]
        }
    }

def db_schema() -> dict:
    fields = [
        ("run_id","TEXT",True), ("ticker","TEXT",True), ("company_name","TEXT",True),
        ("ranking_position","INTEGER",True), ("quant_score","REAL",False),
        ("memo_status","TEXT",True), ("business_model","TEXT",False),
        ("financial_health_score","REAL",False), ("moat_score","REAL",False),
        ("valuation_score","REAL",False), ("growth_score","REAL",False),
        ("risk_score","REAL",False), ("institutional_score","REAL",False),
        ("bull_case","TEXT",False), ("base_case","TEXT",False), ("bear_case","TEXT",False),
        ("final_verdict","TEXT",True), ("confidence","TEXT",True), ("data_quality","TEXT",True),
        ("data_gaps","JSON",True), ("objective_data_json","JSON",True),
        ("ai_interpretation_json","JSON",False), ("risk_ranking_json","JSON",False),
        ("valuation_summary_json","JSON",False), ("sources","JSON",True),
        ("created_at","TEXT",True), ("updated_at","TEXT",False), ("model_used","TEXT",False),
        ("prompt_version","TEXT",False), ("schema_version","TEXT",True), ("estimated_cost","REAL",False)
    ]
    return {
        "table_name": "equity_research_memos",
        "schema_version": "0.1",
        "purpose": "Persist structured qualitative and fundamental research memos for top ranked Scout Finance candidates.",
        "primary_key_candidate": ["run_id", "ticker", "created_at"],
        "fields": [{"name": n, "type": t, "required": r} for n,t,r in fields],
        "indexes_recommended": [["ticker"], ["run_id"], ["created_at"], ["final_verdict"], ["memo_status"]],
    }

def modules() -> list[dict]:
    return [
        {"module":"src/research_memo.py","priority":1,"role":"orchestrator","ai_usage":"controlled_optional","responsibility":"Generate structured memo for TOP 3 ranking candidates.","phase":"8D"},
        {"module":"src/fundamentals.py","priority":4,"role":"deterministic_analysis","ai_usage":"none","responsibility":"Analyze revenue, income, FCF, margins, debt and financial deterioration.","phase":"8C"},
        {"module":"src/valuation.py","priority":3,"role":"deterministic_analysis","ai_usage":"none","responsibility":"Analyze PE, sector PE, EV/EBITDA, P/S, FCF yield and valuation conclusion.","phase":"8C"},
        {"module":"src/risk_analysis.py","priority":2,"role":"mandatory_anti_thesis","ai_usage":"controlled_optional","responsibility":"Explain why NOT to invest and rank risks by severity.","phase":"8C"},
        {"module":"src/moat_analysis.py","priority":5,"role":"qualitative_scoring","ai_usage":"controlled_optional","responsibility":"Score moat 1-10: brand, network effects, switching costs, costs, patents, tech, scale.","phase":"8C/8D"},
        {"module":"src/growth_analysis.py","priority":6,"role":"qualitative_growth","ai_usage":"controlled_optional","responsibility":"Analyze market size, sector growth, expansion, products, AI/tech and 5-10 year potential.","phase":"8C/8D"},
        {"module":"src/institutional_view.py","priority":7,"role":"institutional_lens","ai_usage":"controlled_optional","responsibility":"Why institutions might buy or avoid the company.","phase":"8D"},
        {"module":"src/earnings_analysis.py","priority":8,"role":"future_stub","ai_usage":"disabled_until_reliable_data","responsibility":"Future earnings vs expectations, guidance, market reaction and management comments.","phase":"future"},
    ]

def report(summary: dict, mods: list[dict], ms: dict, ds: dict) -> str:
    mod_rows = "\n".join(f"| {m['module']} | {m['priority']} | {m['role']} | {m['ai_usage']} | {m['phase']} |" for m in mods)
    db_rows = "\n".join(f"| {f['name']} | {f['type']} | {f['required']} |" for f in ds["fields"])
    required = "\n".join(ms["required_fields"])
    return f"""# Scout Finance — PHASE 8B: AI Equity Research Memo Blueprint

Fecha: `{summary["created_at"]}`

## Estado de partida

```text
v0.7 congelada: {summary["phase7g_frozen"]}
Fase 8A válida: {summary["phase8a_valid"]}
Funnel base: {summary["validated_funnel"]}
```

## Objetivo

Incorporar una capa de research fundamental y cualitativo estructurado para las mejores empresas detectadas por el ranking.

```text
Scout Finance pasa de ranking cuantitativo a ranking cuantitativo + tesis razonada por empresa.
```

## Regla de coste

```text
Analizar TOP 3 empresas por defecto.
No analizar todo el universo.
No llamar OpenAI salvo ENABLE_OPENAI=True.
Guardar estimated_cost.
```

## Regla anti-invención

```text
No inventar datos.
Si falta un dato: data_insufficient.
Separar datos objetivos, interpretación y opinión IA.
Toda conclusión debe incluir confidence y data_gaps.
```

## Estados oficiales del memo

```text
completed
ai_disabled
data_insufficient
error
draft
```

## Módulos propuestos

| Módulo | Prioridad | Rol | Uso IA | Fase |
|---|---:|---|---|---|
{mod_rows}

## Contrato JSON oficial

Archivo:

```text
schemas/equity_research_memo_schema_v0_1.json
```

Campos obligatorios principales:

```text
{required}
```

## Tabla propuesta: equity_research_memos

| Campo | Tipo | Obligatorio |
|---|---|---:|
{db_rows}

## Decisiones de arquitectura

### 1. Determinista antes que IA
Los módulos de valoración y fundamentales calculan datos cuando existan. La IA interpreta, no inventa.

### 2. Risk analysis obligatorio
Ningún memo queda completo sin explicar por qué NO invertir.

### 3. Earnings analysis queda como módulo futuro
Se define, pero no se activa hasta tener fuente fiable de earnings/guidance.

### 4. Modo demo obligatorio
Con OpenAI desactivado, el sistema debe devolver memo_status=`ai_disabled` y estructura mínima.

## Roadmap recomendado

```text
8C — Crear módulos fundamentals, valuation y risk_analysis sin IA
8D — Crear research_memo.py orquestador TOP 3
8E — Crear persistencia equity_research_memos
8F — Integrar memo en Ficha de empresa
8G — Comparador de candidatas con datos del memo
8H — Export HTML/PDF del memo
```

## Controles

```text
OpenAI llamado: False
API externa llamada: False
yfinance llamado: False
app.py modificado: False
filters.py modificado: False
pipeline recalculado: False
release v0.7 modificada: False
```

## Resultado

```text
PHASE 8B completada: blueprint del AI Equity Research Memo documentado y validado.
```
"""

def main() -> int:
    print("Scout Finance — Phase 8B AI Equity Research Memo Blueprint")
    print("=" * 92)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

    before_app, before_filters = sig(APP_PATH), sig(FILTERS_PATH)
    phase8a = read_json(PHASE8A_SUMMARY_PATH)
    lock = read_json(RELEASE_LOCK_PATH)
    ms, ds, mods = memo_schema(), db_schema(), modules()

    MEMO_SCHEMA_PATH.write_text(json.dumps(ms, indent=2, ensure_ascii=False), encoding="utf-8")
    DB_SCHEMA_PATH.write_text(json.dumps(ds, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(MODULE_MATRIX_PATH, mods, ["module","priority","role","ai_usage","responsibility","phase"])

    summary = {
        "phase": "8B", "status": "OK", "created_at": utc_now(),
        "goal": "ai_equity_research_memo_blueprint",
        "base_release": lock.get("release", "v0.7.0-candidate"),
        "phase7g_frozen": lock.get("status") == "FROZEN",
        "phase8a_valid": phase8a.get("status") == "OK",
        "validated_funnel": phase8a.get("validated_funnel", "500 → 182 → 63 → 6"),
        "default_top_n": 3, "memo_schema_version": ms["schema_version"],
        "db_schema_version": ds["schema_version"], "modules_count": len(mods),
        "table_name": ds["table_name"],
        "recommended_next_phase": "8C — Deterministic fundamentals, valuation and risk modules",
        "outputs": {"summary": str(SUMMARY_PATH), "report": str(REPORT_PATH), "module_matrix": str(MODULE_MATRIX_PATH), "db_schema": str(DB_SCHEMA_PATH), "memo_schema": str(MEMO_SCHEMA_PATH)},
        "controls": {"openai_called": False, "api_called": False, "yfinance_called": False, "app_modified": False, "filters_modified": False, "pipeline_recalculated": False, "release_modified": False},
        "signatures_before": {"app.py": before_app, "src/filters.py": before_filters},
        "signatures_after": {"app.py": sig(APP_PATH), "src/filters.py": sig(FILTERS_PATH)},
    }
    REPORT_PATH.write_text(report(summary, mods, ms, ds), encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("Blueprint")
    print("-" * 92)
    print(f"Status: {summary['status']}")
    print(f"Base release: {summary['base_release']}")
    print(f"v0.7 frozen: {summary['phase7g_frozen']}")
    print(f"8A valid: {summary['phase8a_valid']}")
    print(f"Default TOP N: {summary['default_top_n']}")
    print(f"Modules proposed: {summary['modules_count']}")
    print(f"Table: {summary['table_name']}")
    print(f"Next: {summary['recommended_next_phase']}")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 8B AI Equity Research Memo Blueprint is complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
