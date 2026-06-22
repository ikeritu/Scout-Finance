# Scout Finance — Fase 7B.6: dry-run protegido de política equilibrada

## Objetivo

Ejecutar la política equilibrada sin tocar producción.

## Outputs

```text
outputs/scouting/stage1_balanced_dry_run/balanced_dry_run_passed.csv
outputs/scouting/stage1_balanced_dry_run/balanced_dry_run_watchlist.csv
outputs/scouting/stage1_balanced_dry_run/balanced_dry_run_rejected.csv
outputs/scouting/stage1_balanced_dry_run/balanced_dry_run_transitions.csv
outputs/scouting/stage1_balanced_dry_run/balanced_dry_run_summary.json
outputs/scouting/stage1_balanced_dry_run/balanced_dry_run_report.md
```

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.run_stage1_balanced_dry_run
.\.venv\Scripts\python.exe scripts/check_phase7b6_balanced_dry_run.py
```
