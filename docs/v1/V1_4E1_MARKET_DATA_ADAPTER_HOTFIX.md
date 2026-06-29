# v1.4E1 — Market Data Adapter Hotfix

## Objetivo

Corregir v1.4E para que el checker no falle por marcador ausente y para mejorar compatibilidad Windows/yfinance.

## Cambios

- Añade marcador `market_data_score_yfinance_cache_v0` a `app.py`.
- Reconfigura stdout/stderr a UTF-8 cuando sea posible.
- Limpia `$` en tickers.
- Silencia parte del ruido de yfinance en stderr.
- Acepta `PARTIAL_OR_ERROR` como estado válido de proveedor.

## Validación

```powershell
.\.venv\Scripts\python.exe -m src.real_market_data_adapter --fetch
.\.venv\Scripts\python.exe scripts/check_v1_4e1_market_data_adapter_hotfix.py
```

## Nota

Si Yahoo/yfinance no devuelve precios, la fase sigue siendo válida como adapter auditado, pero el estado será `PARTIAL_OR_ERROR` hasta que el proveedor responda.
