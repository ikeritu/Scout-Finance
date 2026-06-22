# Scout Finance — Fase 7A.2: enriquecimiento gratuito de market data

## Objetivo

Añadir datos mínimos de mercado al universo real gratuito:

```text
price
market_cap
volume / avg_volume
sector
industry
```

## Entrada

```text
data/raw/universe_source_real.csv
```

## Salida

```text
data/raw/universe_source_real_market_enriched.csv
outputs/scouting/market_data_enrichment_summary.json
outputs/scouting/market_data_enrichment_failures.csv
```

## Dependencia

Instalar yfinance:

```powershell
.\.venv\Scripts\python.exe -m pip install yfinance
```

Opcionalmente añadir a `requirements.txt`:

```text
yfinance
```

## Ejecución prudente

Primero 50:

```powershell
.\.venv\Scripts\python.exe -m src.enrich_market_data_yfinance --limit 50 --sleep 0.3
```

Luego 100:

```powershell
.\.venv\Scripts\python.exe -m src.enrich_market_data_yfinance --limit 100 --sleep 0.3
```

Luego 500:

```powershell
.\.venv\Scripts\python.exe -m src.enrich_market_data_yfinance --limit 500 --sleep 0.3
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7a2_market_data_enrichment.py
```

## Ejecutar piloto con datos enriquecidos

```powershell
.\.venv\Scripts\python.exe -m src.run_real_universe_pilot --input data/raw/universe_source_real_market_enriched.csv --limit 100 --source yfinance_market_data
.\.venv\Scripts\python.exe scripts/check_phase7a_real_universe_pilot.py
```

## Limitaciones

`yfinance` es útil para pruebas locales gratuitas, pero no es una API oficial garantizada. Por eso esta fase usa:

```text
limit
sleep
cache local
failure log
```

## Siguiente fase

```text
Fase 7A.3 — Ajustar filtro Stage 1 con market data real
```
