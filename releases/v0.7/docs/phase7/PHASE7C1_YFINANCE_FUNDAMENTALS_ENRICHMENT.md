# Scout Finance — Fase 7C.1: yfinance fundamentals enrichment

## Objetivo

Enriquecer los 182 PASSED de Stage 1 Balanced con fundamentales gratuitos desde yfinance.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m src.enrich_fundamentals_yfinance
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7c1_yfinance_fundamentals.py
```

## Recalcular cobertura y probar Stage 2

```powershell
.\.venv\Scripts\python.exe -m src.fundamental_coverage_report
.\.venv\Scripts\python.exe scripts/check_phase6b_fundamental_coverage.py
.\.venv\Scripts\python.exe -m src.run_stage2_filter_enriched
.\.venv\Scripts\python.exe scripts/check_phase6d_stage2_enriched.py
```
