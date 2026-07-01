# v1.6C6 — Dashboard Combined Warning Final Fix

## Objetivo

Eliminar el último residuo visual del Dashboard cuando `COMBINED_SCORE_V1` está activo.

## Problema

Aunque el ranking y la ficha ya estaban correctos, el Dashboard aún podía mostrar el aviso amarillo legacy:

`La vista final del último run está vacía... funnel revalidado local...`

## Cambio

Cuando `_sf16c5_is_combined_active()` detecta ranking combinado activo, se muestra:

`Ranking activo generado por COMBINED_SCORE_V1...`

## Resultado esperado

- El Dashboard no debe confundir `COMBINED_SCORE_V1` con fallback local.
- El ranking, ficha, fundamentales y comparación siguen igual.

## No toca

- scoring
- outputs
- OpenAI
- broker
- yfinance
- APIs externas
