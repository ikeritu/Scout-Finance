# v2.47C — dos fallos que hacían caer la pantalla de Unicornios en «Calidad fundamental»

Estado: `UNICORN_SCREEN_CRASH_FIXES_COMPLETED`. Corrige dos excepciones que ya estaban en la rama principal; no cambia datos, criterios ni diseño.

## Qué fallaba
| Fallo | Dónde | Origen |
|---|---|---|
| `StreamlitDuplicateElementKey: unicorn_median_bars_<id>` | Vista por defecto («Analítica visual»), «Cockpit limpio» y «Fichas completas» | PR #4 (gráfico de medianas en la ficha). El gráfico lleva una clave por empresa y la sección «Por qué es unicornio» del final de la pantalla, que se pinta en todas las vistas, vuelve a dibujar el mismo gráfico para la misma empresa. |
| `NameError: name 'score_label' is not defined` | «Fichas completas» | v2.46B (mío). Sustituí `k1.metric("Posibilidad", …)` por `k1.metric(score_label, score_value)` sin definir esas dos variables en esa función, y no probé esa vista en vivo. |

En la práctica, la primera pantalla que se abre al entrar en Unicornios (calidad fundamental, vista por defecto) mostraba la excepción en lugar de la ficha.

## Arreglo
- `render_unicorn_key_figures(row, key_prefix=...)`: cada punto de llamada usa su propio prefijo (`unicorn_median_bars` en la ficha, `_catalog`, `_cockpit`, `_detail`), así que la misma empresa puede aparecer en la vista y en el detalle sin chocar.
- `render_unicorn_full_catalog`: define `score_label, score_value = unicorn_display_score(selected_row)` antes de usarlos, igual que los otros puntos de llamada.

## Por qué no se vio antes
Las pruebas de la pantalla eran de lectura de código fuente (comprueban que ciertos textos existen), no ejecutan la app. Un nombre sin definir o una clave repetida solo aparecen al ejecutar. `tests/qa_unicorns_screen_runs_v2_47c.py` ejecuta la app de verdad con el motor de pruebas de Streamlit (`AppTest`, sin navegador ni red, ~15 s) y falla ante cualquier excepción: vista por defecto, las seis vistas y el modo «Unicornio explosivo». Comprobado que falla sobre el código anterior (clave duplicada) y pasa con el arreglo.

## Verificado además con la misma técnica
Las 12 pantallas de la app cargan sin excepciones; en Unicornios, los 7 filtros rápidos, las 7 opciones de orden y la casilla «Incluir entidades financieras» también.

## Pruebas
`tests/qa_unicorns_screen_runs_v2_47c.py` (nueva) y el resto de QA de unicornios; `pytest`: solo las 3 fallas previas de `test_expanded_universe_post_closure_v2_14j.py`.
