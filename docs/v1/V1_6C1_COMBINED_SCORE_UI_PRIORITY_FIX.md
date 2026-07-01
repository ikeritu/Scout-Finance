# v1.6C1 — Combined Score UI Priority Fix

## Objetivo

Corregir la mezcla visual tras v1.6C: el módulo combinado valida, pero algunas zonas de la UI siguen priorizando `score/local_score_v0`.

## Cambio

La UI prioriza:

1. `combined_score_v1`
2. `score`
3. `local_score_v0`

## Resultado esperado

- Ranking muestra score combinado.
- Ranking muestra categoría combinada.
- Ficha muestra `Score combinado v1`.
- Ficha mantiene fundamentales y lectura del ranking.

## No toca

- OpenAI
- broker
- yfinance
- APIs externas
