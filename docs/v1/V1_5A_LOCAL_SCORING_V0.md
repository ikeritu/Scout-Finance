# v1.5A — Local Scoring v0

## Objetivo

Crear un score local determinista que combine metadatos y market data.

## Fórmula

- Metadata: 15%
- Market data completeness: 25%
- Liquidity: 20%
- Momentum: 15%
- Data quality: 25%
- Penalties: resta ponderada

## Inputs

- `outputs/scouting/active_real_universe_top_candidates.csv`

## Outputs

- `outputs/scouting/local_score_v0_candidates.csv`
- `outputs/scouting/active_real_universe_top_candidates.csv`
- `outputs/scoring/local_score_v0_breakdown.csv`
- `outputs/scoring/local_score_v0_summary.json`
- `outputs/scoring/local_score_v0_report.md`

## Flujo

```powershell
.\.venv\Scripts\python.exe -m src.local_scoring_v0 --score
.\.venv\Scripts\python.exe scripts/check_v1_5a_local_scoring_v0.py
```

## No toca

- OpenAI
- Broker
- yfinance
- Pipeline
- Estados financieros
- Recomendación financiera
