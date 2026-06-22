# Scout Finance — Fase 7A.3: Institutional Universe Cleaning

## Objetivo

Subir el estándar del universo inicial a nivel profesional/institucional.

Antes de enriquecer market data, el sistema separa:

```text
acciones analizables
instrumentos fuera de universo
SPACs / blank check
warrants
rights
units
preferred
ETFs / ETNs / fondos
deuda / notes
```

## Por qué es importante

Un banco, broker o equipo profesional no debería ver:

```text
Rights rechazados por market cap
Warrants rechazados por precio
Units mezcladas con common stocks
SPACs pre-deal dentro del mismo embudo
```

Eso no es rechazo financiero. Es clasificación de universo.

## Input

```text
data/raw/universe_source_real.csv
```

## Outputs

```text
data/raw/universe_source_real_clean.csv
data/raw/universe_source_real_excluded.csv
outputs/scouting/universe_cleaning_summary.json
outputs/scouting/universe_cleaning_exclusion_log.csv
```

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.clean_universe_institutional
.\.venv\Scripts\python.exe scripts/check_phase7a3_institutional_universe_cleaning.py
```

## Después

Enriquecer solo el universo limpio:

```powershell
.\.venv\Scripts\python.exe -m src.enrich_market_data_yfinance --input data/raw/universe_source_real_clean.csv --output data/raw/universe_source_real_clean_market_enriched.csv --limit 100 --sleep 0.3
```

Ejecutar piloto:

```powershell
.\.venv\Scripts\python.exe -m src.run_real_universe_pilot --input data/raw/universe_source_real_clean_market_enriched.csv --limit 100 --source yfinance_clean_market_data
```

## Principio institucional

Una empresa puede ser rechazada por filtros financieros.

Un warrant, right, unit o ETF no debería ser “rechazado”: debe ser clasificado como fuera del universo inicial.
