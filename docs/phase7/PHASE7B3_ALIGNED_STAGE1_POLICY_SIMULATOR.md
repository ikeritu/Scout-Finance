# Scout Finance — Fase 7B.3: simulador Stage 1 alineado

## Objetivo

Reparar el simulador para que `current_base` reproduzca Stage 1 real.

## Regla corregida

```text
PRICE_WATCHLIST_RANGE no convierte una empresa en WATCHLIST por sí solo.
```

Una acción con precio entre mínimo y watch puede pasar si tiene:

```text
market cap suficiente
dollar volume suficiente
sin fallos duros
```

## Outputs

```text
outputs/scouting/stage1_policy_simulation_aligned_report.json
outputs/scouting/stage1_policy_simulation_aligned_report.md
outputs/scouting/stage1_policy_simulation_aligned_summary.csv
outputs/scouting/stage1_policy_simulation_aligned_decisions.csv
outputs/scouting/stage1_policy_simulation_aligned_current_base_alignment.csv
```

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.simulate_stage1_policy_aligned
.\.venv\Scripts\python.exe scripts/check_phase7b3_aligned_simulator.py
```

## Siguiente fase

```text
Fase 7B.4 — Decidir política candidata Stage 1
```
