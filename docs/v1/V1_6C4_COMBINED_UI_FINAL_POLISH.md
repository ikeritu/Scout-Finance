# v1.6C4 — Combined UI Final Polish

## Objetivo

Pulir los restos visuales legacy tras v1.6C3.

## Problemas corregidos

- Dashboard podía seguir mostrando `Fuente: Fallback...`.
- La sección `Razón cuantitativa` podía seguir mostrando `LOCAL_SCORE_V0`.

## Cambios

- Añade `_sf16c4_active_source_label`.
- Añade `_sf16c4_active_reason`.
- Hace que `reason_to_pass_quant` y `local_score_reason` apunten al resumen combinado cuando se ejecuta v1.6C.

## Resultado esperado

- Fuente visual: `Score combinado v1`.
- Razón cuantitativa: `COMBINED_SCORE_V1 ...`.
- Ranking, ficha, fundamentales y lectura se mantienen.

## No toca

- OpenAI
- broker
- yfinance
- APIs externas
