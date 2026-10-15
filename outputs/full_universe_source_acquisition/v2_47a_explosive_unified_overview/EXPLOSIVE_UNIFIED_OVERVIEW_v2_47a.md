# v2.47A — un solo lenguaje visual en la vista de Unicornio explosivo

Estado: `EXPLOSIVE_UNIFIED_OVERVIEW_COMPLETED`. Solo presentación (`app_v2_37.py`); no cambia el score explosivo, los datos de mercado ni ningún fichero de salida.

## El problema
La vista "Unicornio explosivo" mostraba, uno debajo del otro, dos paneles de resumen que decían casi lo mismo con dos estilos distintos:
1. Una tarjeta clara "Cockpit de candidatos explosivos" con 5 números (High/Medium/Low/Watch/Sin datos).
2. Justo debajo, un "trading desk" oscuro (fondo casi negro, radar cian, tarjetas con acento ámbar) que repetía 4 de esos 5 números y el Top 3.

El desplegable "Filtros de exploración y métricas técnicas" volvía a mostrar los mismos números por tercera vez. Resultado (ya señalado en la auditoría de UI/UX): dos sistemas visuales en la misma pantalla y una cifra («0 evaluables») que contradecía visualmente al Top 3 de al lado.

## El cambio
- `render_explosive_cockpit_summary`, `render_explosive_trading_desk_skin` y `render_explosive_trading_desk_hero` se sustituyen por una única función, `render_explosive_overview`: un panel claro con acento ámbar a la izquierda (mismos bordes, tipografía y espaciado que las tarjetas de "Calidad fundamental"). Muestra el nº de candidatos explosivos, las 5 categorías **una sola vez** y el Top 3 por score (sobre 100).
- El ámbar es un acento semántico (distingue la lente explosiva de la de calidad, que usa teal) sobre el mismo tema claro, no un tema aparte.
- El titular pasa de «N evaluables ahora» a «N candidatos explosivos»: es lo que cuenta de verdad (`unicorn_semantic_summary` cuenta filas con tier `EXPLOSIVE_CANDIDATE_*`).
- Se quitó la fila de métricas duplicada del desplegable de filtros, que pasa a llamarse «Filtros de exploración»; el control «Cards» pasa a «Empresas a mostrar».
- El grid de 5 cifras usa `auto-fit` en vez de 5 columnas fijas: en 375 px se reparte en dos filas (3+2) en lugar de desbordar la página (con columnas fijas había 11 elementos fuera de pantalla; con `auto-fit`, 5, ya solo la barra de herramientas del gráfico de velas).

## Compatibilidad con los PRs ya mergeados
Portado sobre `origin/phase9b-global-enrichment-v2-38b` (incluye #2–#6): la vista a pantalla completa de cada candidato (#6), el modo simple `?modo=unicornios` (#5) y los gráficos de la ficha (#4) siguen funcionando. El parche se aplicó sin conflictos de contenido; la fusión a 3 vías duplicó `render_explosive_candidate_fullpage` y se eliminó el duplicado a mano.

## Verificado en vivo (worktree limpio, datos reales tras el refresh de mercado)
141 unicornios; 51 empresas con datos de mercado, 90 bloqueadas; un único panel y 0 excepciones en la vista normal, en `?modo=unicornios` y en móvil (375 px). «Ver a pantalla completa» abre la ficha con velas y «Volver al dashboard» regresa.

## Pruebas
`tests/qa_explosive_unified_overview_v2_47a.py` (funciones oscuras eliminadas, cada cifra renderizada una vez, acento ámbar sobre tema claro, cifras reales del Top 3, grid responsivo, filtros sin repetir métricas). `tests/qa_unicorns_primary_screen_v2_44b.py` actualizado: lo que fijaba el tema oscuro ahora exige lo contrario. `pytest`: solo las 3 fallas previas de `test_expanded_universe_post_closure_v2_14j.py`.

## Pendiente
- La vista a pantalla completa de un candidato sigue mostrando el panel resumen encima (comportamiento previo, ya ocurría con el cockpit y el hero).
- Los tres desplegables por tarjeta («Por qué puntúa así» / «Ficha explosiva profesional» / «Precio y velas OHLCV») podrían ser pestañas, como en la ficha de «Calidad fundamental».
