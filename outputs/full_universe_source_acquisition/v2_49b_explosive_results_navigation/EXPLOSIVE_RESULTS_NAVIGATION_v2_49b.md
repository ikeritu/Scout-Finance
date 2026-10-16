# v2.49B — paginación y búsqueda en los resultados explosivos, y alcance explícito

Estado: `EXPLOSIVE_RESULTS_NAVIGATION_COMPLETED`. Solo presentación y filtrado de lo ya calculado (`app_v2_37.py`); no cambia el score ni los datos. Responde a los hallazgos UX-01, UX-02, UX-04 y UX-05 de un informe de UX (UX-03 y UX-06 ya los resolvió v2.49A).

## Qué cambia
| Hallazgo | Cambio |
|---|---|
| UX-01: máximo de 24 tarjetas, sin paginación ni búsqueda | Fila de filtros visible: **Buscar empresa o ticker** (nombre, ticker, ticker estadounidense o id), **Nivel**, **Señal** y **Por página** (9 / 18 / 24). Paginación «← Anteriores · Página x de y · Siguientes →». Cualquier empresa se puede abrir sin otro modo. |
| UX-02: no se explica la preselección | Frase bajo el botón, antes de buscar: «Alcance: las 141 empresas que ya cumplen el criterio de calidad fundamental (sin 12 entidades financieras). La búsqueda añade sus señales de mercado; no recorre las 43,089 empresas del censo.» |
| UX-04: «51 visibles», se muestran 9 | «Mostrando 1–9 de 140 empresas». Al cambiar búsqueda, filtros, tamaño o página, el conteo y las tarjetas coinciden. |
| UX-05: el Top 3 ignora los filtros | Se mantiene sobre todas las empresas con datos, pero ahora lo dice: «Top 3 por score explosivo (sobre 100) · de todas las empresas con datos», y con 0 candidatos añade «Mayor puntuación disponible: ninguna supera el umbral explosivo». |
| Vacío sin salida | «No hay resultados para estos filtros.» con botón «Restablecer filtros»; el botón también aparece cuando hay filtros activos. |

Los filtros dejan de estar en un desplegable cerrado. «Nivel» usa etiquetas en español (Alto, Medio o superior, Bajo o superior, En vigilancia, Sin datos).

## Estado que se conserva
La página, la búsqueda y los filtros se conservan al abrir una ficha y volver. Streamlit descarta el estado de los widgets que no se dibujan y la ficha no los dibuja, así que se espejan en claves normales (`saved_*`) y se restauran antes de volver a dibujarlos, además de mantenerlos vivos mientras la ficha está abierta. Cualquier cambio de búsqueda, filtro o tamaño vuelve a la página 1.

## Verificado
- En un navegador real, con datos reales de Yahoo (140 empresas): página 2 → abrir ficha → volver deja «Mostrando 10–18» y «Página 2 de 16»; buscar «PLTR» deja 1 empresa (Palantir), oculta la paginación y muestra «Restablecer filtros»; el texto «PLTR» sobrevive a abrir la ficha y volver; una búsqueda sin coincidencias muestra el mensaje y «Restablecer» devuelve las 140.
- `tests/qa_explosive_search_page_v2_49a.py`, ampliada de 7 a 13 casos (alcance, paginación y último página, búsqueda por ticker, vacío y restablecer, estado mientras la ficha está abierta, etiqueta del Top 3).
- Limitación de la prueba: el motor de pruebas de Streamlit conserva widgets obsoletos tras un `st.rerun()` y por eso no puede juzgar el camino de **vuelta** desde una ficha (pierde los filtros aunque en el navegador real se conservan). La prueba comprueba el estado mientras la ficha está abierta y la restauración se verificó a mano en el navegador.

## Pendiente del informe de UX
UX-07 (etiquetas «candidatos» frente a «vigilancia»), UX-08 (separar fecha de cálculo fundamental y fecha/fuente de mercado), UX-09 (jerga técnica restante) y UX-10 (pestañas largas en móvil).
