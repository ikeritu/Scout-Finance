# Scout Finance — Fase 7B.5: selección de política candidata Stage 1

## Objetivo

Seleccionar formalmente una política candidata para Stage 1 sin modificar producción.

## Decisión esperada

```text
selected_policy = balanced
decision = SELECT_FOR_DRY_RUN
apply_to_production_now = False
```

## Outputs

```text
outputs/scouting/stage1_candidate_policy_decision_report.json
outputs/scouting/stage1_candidate_policy_decision_report.md
outputs/scouting/stage1_candidate_policy_comparison.csv
outputs/scouting/stage1_candidate_policy_decision.csv
```

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.select_stage1_candidate_policy
.\.venv\Scripts\python.exe scripts/check_phase7b5_candidate_policy.py
```

## Siguiente fase

```text
Fase 7B.6 — Dry-run protegido de política equilibrada
```
