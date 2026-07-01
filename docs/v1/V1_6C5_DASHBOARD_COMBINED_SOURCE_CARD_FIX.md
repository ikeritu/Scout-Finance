# v1.6C5 — Dashboard Combined Source Card Fix

## Objetivo

Corregir el último residuo visual tras v1.6C4:

- Dashboard seguía mostrando `Fuente: Fallback...`.
- El aviso amarillo del Dashboard seguía hablando del funnel revalidado local.

## Cambio

Añade helpers que detectan si el ranking activo es `COMBINED_SCORE_V1` leyendo:

- `outputs/scoring/combined_score_v1_summary.json`
- `outputs/scouting/active_real_universe_top_candidates.csv`

y muestra:

- `Fuente: Score combinado v1`
- aviso informativo de ranking activo combinado

## No toca

- scoring
- outputs
- OpenAI
- broker
- yfinance
- APIs externas
