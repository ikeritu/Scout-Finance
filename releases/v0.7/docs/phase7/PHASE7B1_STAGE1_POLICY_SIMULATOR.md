# Scout Finance — Fase 7B.1: simulador de política Stage 1

## Objetivo

Simular escenarios de filtros sin modificar el código real.

## Escenarios

```text
current_base
conservative
balanced
aggressive
```

## Qué genera

```text
outputs/scouting/stage1_policy_simulation_report.json
outputs/scouting/stage1_policy_simulation_report.md
outputs/scouting/stage1_policy_simulation_summary.csv
outputs/scouting/stage1_policy_simulation_decisions.csv
outputs/scouting/stage1_policy_simulation_bucket_summary.csv
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

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.simulate_stage1_policy
.\.venv\Scripts\python.exe scripts/check_phase7b1_policy_simulation.py
```

## Siguiente fase

```text
Fase 7B.2 — Decidir política Stage 1 candidata
```
