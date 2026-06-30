# v1.4F2 — Manual Market Data Percent Normalization

## Objetivo

Evitar confusión en `manual_market_data.csv`.

- Antes: `0.5` podía mostrarse como `50%`.
- Ahora: `0.5` significa `0.5%`.

El adaptador convierte internamente los porcentajes humanos a ratios de app:

- `0.5` → `0.005`
- `1.2` → `0.012`
- `3.5` → `0.035`

## Nueva plantilla

Columnas nuevas:

- `change_1d_pct`
- `change_5d_pct`
- `change_20d_pct`

## Flujo

```powershell
.\.venv\Scripts\python.exe -m src.market_data_provider_fallback --init-template
Copy-Item .\dataeal\manual_market_data_template.csv .\dataeal\manual_market_data.csv -Force
.\.venv\Scripts\python.exe -m src.market_data_provider_fallback --merge
.\.venv\Scripts\python.exe scripts/check_v1_4f2_manual_market_data_percent_normalization.py
```

## No toca

- OpenAI
- Broker
- yfinance fetch
- Pipeline
- Scoring financiero completo
