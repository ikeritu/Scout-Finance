# v1.5B — Ranking Explainability

## Objetivo

Añadir explicabilidad local al ranking actual.

## Añade

- `positive_factors`
- `negative_factors`
- `missing_data_flags`
- `review_flags`
- `explainability_badges`
- `explainability_summary`

## Inputs

- `outputs/scouting/active_real_universe_top_candidates.csv`

## Outputs

- `outputs/scouting/ranking_explainability_candidates.csv`
- `outputs/scouting/active_real_universe_top_candidates.csv`
- `outputs/scoring/ranking_explainability_factors.csv`
- `outputs/scoring/ranking_explainability_summary.json`
- `outputs/scoring/ranking_explainability_report.md`

## Flujo

```powershell
.\.venv\Scripts\python.exe -m src.ranking_explainability --explain
.\.venv\Scripts\python.exe scripts/check_v1_5b_ranking_explainability.py
```

## No toca

- OpenAI
- Broker
- yfinance
- Pipeline
- Recomendación financiera
