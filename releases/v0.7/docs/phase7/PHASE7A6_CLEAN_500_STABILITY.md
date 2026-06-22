# Scout Finance — Fase 7A.6: lote limpio de 500 empresas y estabilidad

## Objetivo

Validar que el flujo institucional aguanta un lote mayor:

```text
universo limpio
↓
market data enrichment 500
↓
Stage 1
↓
informe de estabilidad
```

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.run_clean_500_stability_pilot --limit 500 --sleep 0.3
.\.venv\Scripts\python.exe scripts/check_phase7a6_clean_500_stability.py
```

## Ver informe

```powershell
Get-Content ".\outputs\scouting\clean_500_stability_report.md" -Encoding UTF8
```

## Siguiente fase

```text
Fase 7B — Diagnóstico y ajuste profesional de Stage 1
```
