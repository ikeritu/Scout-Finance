# Scout Finance — PHASE 8B: AI Equity Research Memo Blueprint

Fecha: `2026-06-17T14:40:28+00:00`

## Estado de partida

```text
v0.7 congelada: True
Fase 8A válida: True
Funnel base: 500 → 182 → 63 → 6
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
| src/research_memo.py | 1 | orchestrator | controlled_optional | 8D |
| src/fundamentals.py | 4 | deterministic_analysis | none | 8C |
| src/valuation.py | 3 | deterministic_analysis | none | 8C |
| src/risk_analysis.py | 2 | mandatory_anti_thesis | controlled_optional | 8C |
| src/moat_analysis.py | 5 | qualitative_scoring | controlled_optional | 8C/8D |
| src/growth_analysis.py | 6 | qualitative_growth | controlled_optional | 8C/8D |
| src/institutional_view.py | 7 | institutional_lens | controlled_optional | 8D |
| src/earnings_analysis.py | 8 | future_stub | disabled_until_reliable_data | future |

## Contrato JSON oficial

Archivo:

```text
schemas/equity_research_memo_schema_v0_1.json
```

Campos obligatorios principales:

```text
ticker
company_name
memo_status
ranking_position
quant_score
business_model
revenue_sources
sector_trends
financial_health
moat_analysis
valuation_analysis
growth_analysis
risk_analysis
institutional_view
bull_case
base_case
bear_case
final_verdict
confidence
data_gaps
sources
created_at
model_used
estimated_cost
```

## Tabla propuesta: equity_research_memos

| Campo | Tipo | Obligatorio |
|---|---|---:|
| run_id | TEXT | True |
| ticker | TEXT | True |
| company_name | TEXT | True |
| ranking_position | INTEGER | True |
| quant_score | REAL | False |
| memo_status | TEXT | True |
| business_model | TEXT | False |
| financial_health_score | REAL | False |
| moat_score | REAL | False |
| valuation_score | REAL | False |
| growth_score | REAL | False |
| risk_score | REAL | False |
| institutional_score | REAL | False |
| bull_case | TEXT | False |
| base_case | TEXT | False |
| bear_case | TEXT | False |
| final_verdict | TEXT | True |
| confidence | TEXT | True |
| data_quality | TEXT | True |
| data_gaps | JSON | True |
| objective_data_json | JSON | True |
| ai_interpretation_json | JSON | False |
| risk_ranking_json | JSON | False |
| valuation_summary_json | JSON | False |
| sources | JSON | True |
| created_at | TEXT | True |
| updated_at | TEXT | False |
| model_used | TEXT | False |
| prompt_version | TEXT | False |
| schema_version | TEXT | True |
| estimated_cost | REAL | False |

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
