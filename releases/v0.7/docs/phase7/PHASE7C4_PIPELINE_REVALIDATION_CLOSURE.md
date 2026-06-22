# Scout Finance — Fase 7C.4: cierre de revalidación del pipeline

## Objetivo

Cerrar formalmente la revalidación del pipeline tras:

```text
Stage 1 Balanced
Stage 2 yfinance-aligned
Stage 3 scoring
```

Funnel esperado:

```text
500 → 182 → 63 → 6
```

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m src.close_phase7c4_pipeline_revalidation
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7c4_pipeline_revalidation.py
```

## Ver informe

```powershell
Get-Content ".\outputs\scouting\phase7c4_pipeline_revalidation_report.md" -Encoding UTF8
```
