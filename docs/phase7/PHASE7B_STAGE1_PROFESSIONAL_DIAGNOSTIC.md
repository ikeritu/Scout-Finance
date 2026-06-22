# Scout Finance — Fase 7B: diagnóstico profesional de Stage 1

## Objetivo

Analizar si Stage 1 se comporta de forma profesional y defendible tras el lote limpio de 500 empresas.

## Qué analiza

```text
passed
watchlist
rejected
motivos de rechazo
distribución por market cap
distribución por precio
distribución por dollar volume
perfil de watchlist
```

## Qué NO hace

```text
No cambia filtros
No modifica app.py
No llama OpenAI
No llama APIs
No llama yfinance
No modifica releases/v0.6
```

## Outputs

```text
outputs/scouting/stage1_professional_diagnostic_report.json
outputs/scouting/stage1_professional_diagnostic_report.md
outputs/scouting/stage1_professional_rejection_reasons.csv
outputs/scouting/stage1_professional_bucket_summary.csv
outputs/scouting/stage1_professional_watchlist_review.csv
outputs/scouting/stage1_professional_passed_sample.csv
```

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.diagnose_stage1_professional
.\.venv\Scripts\python.exe scripts/check_phase7b_stage1_diagnostic.py
```

## Siguiente fase

```text
Fase 7B.1 — Propuesta de ajustes Stage 1 sin aplicar cambios
```
