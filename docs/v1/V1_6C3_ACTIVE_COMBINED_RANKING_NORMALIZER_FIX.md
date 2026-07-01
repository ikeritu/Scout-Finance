# v1.6C3 — Active Combined Ranking Normalizer Fix

## Objetivo

Corregir que el CSV activo ya contenía `COMBINED_SCORE_V1`, pero la app lo seguía mostrando como `INPUT_ONLY/METADATA_SCORE` y como score local.

## Causa

La función de normalización interna de la app para `active_real_universe_top_candidates.csv`:

- no preservaba `combined_score_v1`
- priorizaba columnas legacy
- marcaba cualquier `active_real_universe_top_candidates.csv` como `real_universe_input`
- mostraba aviso amarillo antiguo

## Cambios

- Si `combined_score_v1` existe, se fuerza:
  - `score_priority`
  - `score`
  - `combined_score_v1`
- Se preservan:
  - `category_final`
  - `stage3_status`
  - `score_reason`
  - componentes de score
- Si el status contiene `COMBINED_SCORE_V1`, la fuente UI pasa a:
  - `combined_score_v1`
- El aviso superior cambia a mensaje informativo de ranking activo combinado.

## Resultado esperado

- Ranking muestra score combinado.
- Ranking muestra categoría combinada.
- Ficha muestra score combinado.
- Aviso superior deja de decir `INPUT_ONLY/METADATA_SCORE`.
- Dashboard puede reconocer el ranking combinado activo.
