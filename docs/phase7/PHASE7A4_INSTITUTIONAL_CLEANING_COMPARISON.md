# Scout Finance — Fase 7A.4: comparativa antes/después de limpieza institucional

## Objetivo

Demostrar con datos que la limpieza institucional mejora el pipeline.

## Qué compara

Antes:

```text
50 símbolos
34 con market data completo
15 passed
4 watchlist
31 rejected
```

Después:

```text
100 símbolos
100 con market data completo
48 passed
10 watchlist
42 rejected
```

## Qué genera

```text
outputs/scouting/institutional_cleaning_comparison_report.json
outputs/scouting/institutional_cleaning_comparison_metrics.csv
outputs/scouting/institutional_cleaning_comparison_report.md
```

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.compare_institutional_cleaning_impact
.\.venv\Scripts\python.exe scripts/check_phase7a4_institutional_cleaning_comparison.py
```

## Siguiente fase

```text
Fase 7A.5 — Dashboard institucional del universo
```
