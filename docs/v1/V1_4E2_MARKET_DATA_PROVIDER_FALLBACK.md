# v1.4E2 — Market Data Provider Fallback

Evita depender solo de Yahoo/yfinance.

## Flujo

```powershell
.\.venv\Scripts\python.exe -m src.market_data_provider_fallback --init-template
Copy-Item .\data\real\manual_market_data_template.csv .\data\real\manual_market_data.csv -Force
notepad .\data\real\manual_market_data.csv
.\.venv\Scripts\python.exe -m src.market_data_provider_fallback --merge
.\.venv\Scripts\python.exe scripts/check_v1_4e2_market_data_provider_fallback.py
```

## Estados

- MARKET_DATA_SCORE_MANUAL
- MARKET_DATA_SCORE_YFINANCE
- METADATA_SCORE_FALLBACK

## No toca

- OpenAI
- Broker
- Pipeline
- yfinance fetch nuevo
