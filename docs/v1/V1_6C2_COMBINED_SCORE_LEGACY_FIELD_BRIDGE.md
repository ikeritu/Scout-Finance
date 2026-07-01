# v1.6C2 — Combined Score Legacy Field Bridge

## Objetivo

Corregir que partes antiguas de la UI sigan leyendo campos legacy como `local_score_v0`, `score`, `category_final` o `stage3_status`.

## Cambio principal

Cuando se ejecuta `src.combined_scoring_v1 --score`, el CSV activo queda con:

- `combined_score_v1`
- `score`
- `local_score_v0`
- `score_final`
- `display_score`

apuntando al score combinado.

También deja:

- `local_score_v0_previous`
- `score_previous`

para no perder el score anterior.

## Resultado esperado

- Ranking muestra score combinado.
- Ranking muestra categoría combinada.
- Ficha muestra score combinado.
- Aviso y estado muestran `Score combinado v1`.
- Lectura combinada se mantiene.

## No toca

- OpenAI
- broker
- yfinance
- APIs externas
