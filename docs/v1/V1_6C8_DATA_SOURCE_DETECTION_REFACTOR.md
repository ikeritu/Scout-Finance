# v1.6C8 — Data Source Detection Refactor for Combined Score

## Objetivo

Corregir el fallo real de v1.6C en la capa legacy del Dashboard.

## Problema

El ranking activo y la ficha ya funcionaban con `COMBINED_SCORE_V1`, pero el panel `Fuente de datos activa` seguía usando la lógica antigua de v1.4A:

- `latest_final_view`
- `real_universe_input`
- `revalidated_funnel_fallback`

No existía un caso nativo para:

- `combined_score_v1`

Además, `_sf14a_render_data_source_panel()` había quedado dependiendo de variables frágiles como `source` o `final_df`, que no pertenecen a esa función.

## Cambio

Se reemplazan de forma controlada dos funciones completas:

- `_sf14a_detect_active_source()`
- `_sf14a_render_data_source_panel()`

## Nueva lógica

1. Carga primero el ranking activo/fallback con `_sf12a_load_revalidated_candidates()`.
2. Si detecta `combined_score_v1` o `COMBINED_SCORE_V1`, devuelve:

```python
{
    "active_source": "combined_score_v1",
    "label": "Score combinado v1",
    ...
}
```

3. Solo si no hay ranking combinado, sigue con las rutas legacy:

- `latest_final_view`
- `real_universe_input`
- `revalidated_funnel_fallback`
- `empty`

## Resultado esperado

- Dashboard muestra `Fuente: Score combinado v1`.
- Dashboard muestra mensaje azul de `COMBINED_SCORE_V1`.
- Ya no muestra aviso amarillo de funnel revalidado cuando el ranking activo es combinado.
- Ranking, ficha, fundamentales y comparación siguen igual.

## No toca

- scoring
- outputs
- OpenAI
- broker
- yfinance
- APIs externas
