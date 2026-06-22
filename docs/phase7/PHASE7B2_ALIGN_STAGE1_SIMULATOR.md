# Scout Finance — Fase 7B.2: alinear simulador con Stage 1 real

## Objetivo

Comparar la simulación `current_base` contra el Stage 1 real.

La diferencia actual esperada era:

```text
Stage 1 real:       226 / 66 / 208
Sim current_base:   213 / 79 / 208
```

## Qué genera

```text
outputs/scouting/stage1_simulator_alignment_report.json
outputs/scouting/stage1_simulator_alignment_report.md
outputs/scouting/stage1_simulator_alignment_mismatches.csv
outputs/scouting/stage1_simulator_alignment_mismatch_summary.csv
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
.\.venv\Scripts\python.exe -m src.align_stage1_simulator
.\.venv\Scripts\python.exe scripts/check_phase7b2_simulator_alignment.py
```

## Siguiente fase

```text
Fase 7B.3 — Reparar simulador base si procede
```
