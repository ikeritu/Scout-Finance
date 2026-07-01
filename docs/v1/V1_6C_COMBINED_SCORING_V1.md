# v1.6C — Combined Scoring v1

## Objetivo

Crear el primer score combinado usando tres módulos:

- metadata_score_component
- market_data_score_component
- fundamentals_score_component

## Pesos v1

- Metadata: 20%
- Market data: 35%
- Fundamentals: 45%

## Comando

```powershell
.\.venv\Scripts\python.exe -m src.combined_scoring_v1 --score
```

## Outputs

- `outputs/scouting/combined_score_v1_candidates.csv`
- `outputs/scouting/active_real_universe_top_candidates.csv`
- `outputs/scoring/combined_score_v1_breakdown.csv`
- `outputs/scoring/combined_score_v1_summary.json`
- `outputs/scoring/combined_score_v1_report.md`

## UI

Añade un panel `Combined scoring v1` en Dashboard.

Cuando se ejecuta el módulo, el ranking activo pasa a mostrar:

- `combined_score_v1`
- categoría combinada
- estado `Score combinado v1`
- componentes metadata / market data / fundamentales

## Controles

- OpenAI called: False
- Broker called: False
- yfinance called: False
- Fundamentals API called: False

## Nota

No es recomendación financiera. Es un scoring local de priorización para investigación.
