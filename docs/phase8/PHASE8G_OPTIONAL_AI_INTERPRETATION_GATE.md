# Scout Finance — PHASE 8G Optional AI Interpretation Gate and Cost Guardrails

## Objetivo

Crear una puerta explícita para la futura interpretación IA de los Equity Research Memos sin ejecutar ninguna llamada real a OpenAI, APIs externas o yfinance.

## Reglas

- No llamar OpenAI.
- No llamar APIs externas.
- No llamar yfinance.
- No recalcular el pipeline.
- No tocar `app.py`.
- No tocar `src/filters.py`.
- No tocar `releases/v0.7`.
- TOP N máximo: 3.
- No inventar datos.
- Mantener separados datos objetivos e interpretación IA.
- Preservar `data_insufficient` cuando falten datos.

## Variables de entorno futuras

La puerta solo se abrirá si todas estas variables están activadas:

```text
ENABLE_OPENAI=True
ENABLE_AI_RESEARCH_MEMO=True
ALLOW_AI_SPEND=True
```

Además, se audita:

```text
AI_RESEARCH_MEMO_MODEL
AI_RESEARCH_MEMO_MAX_COST_USD
```

En esta fase, aunque la puerta se abra, no se ejecuta ninguna llamada. Solo se genera el plan y la auditoría.

## Outputs

- `outputs/scouting/phase8g_optional_ai_interpretation_gate_summary.json`
- `outputs/scouting/phase8g_optional_ai_interpretation_gate_report.md`
- `outputs/scouting/phase8g_ai_interpretation_gate_decision.json`
- `outputs/scouting/phase8g_ai_interpretation_plan.json`
- `outputs/scouting/phase8g_ai_interpretation_plan.csv`
- `outputs/scouting/phase8g_ai_gate_audit.json`

## Siguiente fase

8H — Prompt packaging and dry-run AI memo preview.
