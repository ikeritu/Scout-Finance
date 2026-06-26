# v1.4A — Real Universe Refresh / Data Source Transparency

## Objetivo

Explicar dentro de la interfaz por qué aparecen siempre las mismas empresas y qué fuente local alimenta el ranking.

## Cambios

- Añade panel `Fuente de datos activa` en Dashboard.
- Detecta si la app usa:
  - último run válido,
  - fallback de funnel revalidado,
  - o sin datos.
- Muestra modo, run activo, filas visibles y explicación.
- Audita archivos locales relevantes:
  - `outputs/scouting/phase7c4_pipeline_revalidation_top_candidates.csv`
  - `outputs/scouting/top_100_candidates.csv`
  - `outputs/scouting/top_20_deep_research.csv`
  - `outputs/scouting/top_50_watchlist.csv`
  - `outputs/analyses`
  - `data/demo`
  - `data/real`
- Muestra filas, tamaño, fecha de modificación y top tickers cuando sea posible.
- Añade ayuda: `Cómo conseguir empresas distintas`.

## No toca

- Scoring
- Filtros
- Pipeline
- OpenAI
- APIs externas
- yfinance
- Broker/trading

## Validación

```powershell
.\.venv\Scripts\python.exe scripts/check_v1_4a_real_universe_refresh.py
```

## Prueba manual

1. Arrancar Streamlit.
2. Abrir Dashboard.
3. Revisar `Fuente de datos activa`.
4. Abrir `Auditar archivos que alimentan la interfaz`.
5. Confirmar qué archivo provoca que se repitan empresas.
6. Abrir Ranking y Análisis empresa para comprobar que siguen funcionando.
