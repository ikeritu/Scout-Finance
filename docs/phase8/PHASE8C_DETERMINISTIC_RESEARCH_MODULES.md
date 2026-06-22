# Scout Finance — PHASE 8C Deterministic Research Modules

## Objetivo

Crear la capa determinista previa al AI Equity Research Memo de v0.8.

Esta fase implementa módulos offline para:

- fundamentals
- valuation
- risk analysis
- moat analysis
- growth analysis
- institutional view
- earnings analysis
- research memo assembly

## Reglas

- No llamar OpenAI.
- No llamar APIs externas.
- No llamar yfinance.
- No tocar `app.py`.
- No tocar `src/filters.py`.
- No tocar `releases/v0.7`.
- No recalcular pipeline.
- Analizar TOP 3 por defecto.
- No inventar datos.
- Si faltan datos, marcar `data_insufficient`.
- Separar datos objetivos, interpretación determinista e interpretación IA futura.
- Coste estimado siempre `0.0`.

## Archivos creados

- `src/research_memo.py`
- `src/fundamentals.py`
- `src/valuation.py`
- `src/risk_analysis.py`
- `src/moat_analysis.py`
- `src/growth_analysis.py`
- `src/institutional_view.py`
- `src/earnings_analysis.py`
- `src/phase8c_deterministic_research_modules.py`
- `scripts/check_phase8c_deterministic_research_modules.py`

## Outputs

- `outputs/scouting/phase8c_deterministic_research_modules_summary.json`
- `outputs/scouting/phase8c_deterministic_research_modules_report.md`
- `outputs/scouting/phase8c_deterministic_research_memos.json`
- `outputs/scouting/phase8c_deterministic_research_memos.csv`
- `outputs/scouting/phase8c_deterministic_modules_matrix.csv`

## Siguiente fase

8D — Memo persistence and integration adapter.
