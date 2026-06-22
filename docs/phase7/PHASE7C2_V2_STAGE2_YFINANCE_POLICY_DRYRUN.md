# Scout Finance — Fase 7C.2 v2: Stage 2 yfinance policy dry-run

## Objetivo

Simular una política Stage 2 compatible con yfinance sin modificar `filter_stage2.py`.

Esta versión no depende de funciones internas de `filter_stage2.py`. Usa los outputs reales de Stage 2:

```text
data/stages/stage2_rejection_log.csv
data/stages/stage2_watchlist.csv
data/stages/stage2_rejected.csv
```

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m src.simulate_stage2_yfinance_policy_v2
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7c2_v2_stage2_yfinance_policy.py
```

## Ver informe

```powershell
Get-Content ".\outputs\scouting\stage2_yfinance_policy_dryrun_report.md" -Encoding UTF8
```
