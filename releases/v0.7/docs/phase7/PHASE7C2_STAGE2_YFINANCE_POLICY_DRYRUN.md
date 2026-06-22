# Scout Finance — Fase 7C.2: Stage 2 yfinance policy dry-run

## Objetivo

Simular una política Stage 2 compatible con yfinance sin modificar `filter_stage2.py`.

Cambio simulado:

```text
MISSING_SHARES_DILUTION
→ MISSING_SHARES_DILUTION_PROVIDER_LIMITATION
```

La limitación de proveedor no bloquea PASSED por sí sola.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m src.simulate_stage2_yfinance_policy
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7c2_stage2_yfinance_policy.py
```

## Ver informe

```powershell
Get-Content ".\outputs\scouting\stage2_yfinance_policy_dryrun_report.md" -Encoding UTF8
```
