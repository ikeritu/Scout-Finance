# v1.4D — Real Universe Scoring Bridge

## Objetivo

Crear un puente entre `INPUT_ONLY` y un futuro scoring financiero real.

Esta fase genera un `METADATA_SCORE` local usando solo campos disponibles en `data/real/real_universe.csv`.

## Importante

Esto **no es scoring financiero real**.

No usa:

- precio
- market cap
- fundamentales
- ratios financieros
- OpenAI
- APIs
- yfinance
- broker/trading

## Archivos añadidos

- `src/real_universe_scoring_bridge.py`
- `scripts/check_v1_4d_real_universe_scoring_bridge.py`
- `docs/v1/V1_4D_REAL_UNIVERSE_SCORING_BRIDGE.md`

## Outputs generados

- `outputs/scouting/real_universe_scored_candidates.csv`
- `outputs/scouting/active_real_universe_top_candidates.csv`
- `outputs/scouting/real_universe_scoring_bridge_summary.json`
- `outputs/scouting/real_universe_scoring_bridge_report.md`

## Score local

Componentes:

- completitud de metadatos
- exchange conocido
- país / mercado desarrollado proxy
- sector presente o high-signal
- industria presente
- desempate estable por orden

## Flujo

```powershell
.\.venv\Scripts\python.exe -m src.real_universe_scoring_bridge --score
.\.venv\Scripts\python.exe scripts/check_v1_4d_real_universe_scoring_bridge.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Qué probar

- Dashboard muestra panel `Scoring bridge universo real`.
- Ranking sigue mostrando empresas del universo real.
- `active_real_universe_top_candidates.csv` contiene `METADATA_SCORE`.
- La interfaz no presenta el score como recomendación financiera.

## Próxima fase

v1.4E — Real Market Data Adapter, probablemente con yfinance opcional y controlado.
