# v1.4C — Regenerate Candidates From Real Universe

## Objetivo

Crear candidatos visibles en la interfaz a partir de `data/real/real_universe.csv`.

## Importante

Esta fase **no hace scoring financiero real**.

Genera una lista `INPUT_ONLY` para probar el flujo visual con tickers reales nuevos. Sirve para confirmar que la interfaz deja de depender de los CSV antiguos AUPH/BZ/ADBE.

## Archivos añadidos

- `src/real_universe_candidates.py`
- `scripts/check_v1_4c_regenerate_candidates_real_universe.py`
- `docs/v1/V1_4C_REGENERATE_CANDIDATES_REAL_UNIVERSE.md`

## Outputs generados

- `outputs/scouting/real_universe_candidates.csv`
- `outputs/scouting/active_real_universe_top_candidates.csv`
- `outputs/scouting/real_universe_candidates_summary.json`
- `outputs/scouting/real_universe_candidates_report.md`

## Cambio en app.py

La función de fallback prioriza ahora:

1. `outputs/scouting/active_real_universe_top_candidates.csv`
2. `outputs/scouting/real_universe_candidates.csv`
3. `outputs/scouting/phase7c4_pipeline_revalidation_top_candidates.csv`
4. `outputs/scouting/top_100_candidates.csv`

## Flujo

```powershell
.\.venv\Scripts\python.exe -m src.real_universe_candidates --generate
.\.venv\Scripts\python.exe scripts/check_v1_4c_regenerate_candidates_real_universe.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Qué probar

- Dashboard debe mostrar candidatos desde universo real.
- Ranking debe mostrar AAPL/MSFT/ASML si ese es tu CSV.
- Análisis empresa debe poder cargar esos tickers.
- La fuente activa debe mostrar `active_real_universe_top_candidates.csv`.

## No toca

- Scoring financiero
- Filtros
- Pipeline
- OpenAI
- APIs externas
- yfinance
- Broker/trading
