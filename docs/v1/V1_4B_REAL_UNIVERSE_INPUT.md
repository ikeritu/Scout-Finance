# v1.4B — Real Universe Input MVP

## Objetivo

Preparar una entrada controlada para cargar un universo real de empresas sin tocar todavía el pipeline ni llamar APIs.

## Archivos añadidos

- `data/real/universe_template.csv`
- `src/real_universe_input.py`
- `scripts/check_v1_4b_real_universe_input.py`
- `docs/v1/V1_4B_REAL_UNIVERSE_INPUT.md`

## Formato CSV

```text
ticker,name,exchange,country,sector,industry
```

## Flujo recomendado

```powershell
.\.venv\Scripts\python.exe -m src.real_universe_input --init-template
Copy-Item .\data\real\universe_template.csv .\data\real\real_universe.csv -Force
notepad .\data\real\real_universe.csv
.\.venv\Scripts\python.exe -m src.real_universe_input --validate
.\.venv\Scripts\python.exe scripts/check_v1_4b_real_universe_input.py
```

## Outputs

- `outputs/scouting/real_universe_input_summary.json`
- `outputs/scouting/real_universe_input_report.md`

## Validaciones

- Archivo existe.
- Columnas mínimas.
- Tickers no vacíos.
- Formato básico de ticker.
- Duplicados.
- Exchange vacío.
- Country vacío.
- Conteo de filas y tickers válidos.

## No toca

- Scoring
- Filtros
- Pipeline
- OpenAI
- APIs externas
- yfinance
- Broker/trading

## Próxima fase

v1.4C — Regenerate Candidates From Real Universe.
