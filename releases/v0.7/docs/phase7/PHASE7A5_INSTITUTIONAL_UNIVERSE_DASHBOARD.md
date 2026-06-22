# Scout Finance — Fase 7A.5: Dashboard institucional del universo

## Objetivo

Mostrar dentro de la app la mejora institucional del universo:

```text
universo bruto
universo limpio
instrumentos excluidos
market data success antes/después
Stage 1 pass rate antes/después
Stage 1 rejection rate antes/después
```

## Qué lee

```text
outputs/scouting/universe_cleaning_summary.json
outputs/scouting/institutional_cleaning_comparison_report.json
outputs/scouting/institutional_cleaning_comparison_metrics.csv
```

## Qué añade al Dashboard

Nuevo bloque:

```text
🏦 Universo institucional
```

## Qué NO hace

```text
No llama OpenAI
No llama APIs
No llama yfinance
No modifica releases/v0.6
No ejecuta el embudo
```

## Comandos

```powershell
.\.venv\Scripts\python.exe scripts/apply_phase7a5_institutional_dashboard.py
.\.venv\Scripts\python.exe scripts/check_phase7a5_institutional_dashboard.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```
