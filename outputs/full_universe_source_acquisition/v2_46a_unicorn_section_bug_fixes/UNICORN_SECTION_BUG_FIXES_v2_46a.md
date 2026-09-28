# v2.46A — revisión de bugs del apartado de Unicornios (10 arreglos)

Fecha: 2026-09-28. El usuario pidió revisar el apartado de Unicornios en busca de bugs y arreglarlos. Cada bug se reprodujo primero con datos reales o en vivo en la app; después se corrigió, se escribió un test de regresión y se verificó de nuevo en el navegador. Ningún arreglo llama a la red ni toca datos del usuario.

## Arreglos

| # | Bug reproducido | Arreglo |
|---|---|---|
| 1 | Las notas/estado/comentario del cockpit y de la ficha de detalle usaban claves de widget fijas: el texto escrito para una empresa aparecía (y se guardaba) en la siguiente. | Clave por empresa (`..._{asset_id}`). Verificado en vivo. |
| 2 | 8 empresas figuraban dos veces entre los 161 unicornios (mismo CIK de la SEC en NASDAQ y en Cboe: ACADIA, Adobe, ADTRAN, AMD, Digital Turbine, CarGurus, Check Point, Bel Fuse). | v2.38BT deduplica por CIK: la cotización secundaria pasa a `DUPLICATE_LISTING` (45 en todo el universo). **153 unicornios únicos** (152 de EE. UU. + 1 de Austria). |
| 3 | «25 explosivos evaluables» según un módulo y 0 según el score (todos `WATCH_ONLY`); «Short squeeze» para Casey's (22.000 M$) y «Multibagger» por buscar «micro» en el nombre (AMD, Micron). | El estado semántico sale ahora del tier del score. «Short squeeze» exige short interest ≥ 15 %; «Multibagger» exige micro-cap real. |
| 4 | El «Ranking interno» era alfabético (105 empresas empatan al 96 %) y ninguna ficha mostraba cifras reales. | Desempate por crecimiento real de ingresos; nueva ordenación «Crecimiento de ingresos»; cifras reales (ingresos, beneficio, margen neto) en tarjetas, fichas, detalle y CSV. |
| 5 | Filtros rápidos: `US` y `USA` eran países distintos (99 americanos aparecían en «Europa»). | País normalizado; «Europa» significa países europeos. |
| 6 | Nombres de tier inexistentes (`REVIEW_REQUIRED`, `SCORE_ELIGIBLE_FULL`): el filtro «Revisión requerida» devolvía siempre 0 y los ajustes de probabilidad nunca se aplicaban. | Se usan los tiers reales de v2.38BO. |
| 7 | Entidades financieras entre los unicornios como «Muy respaldado»; el heurístico por nombre no detectaba «Bankshares». | Clasificación por código SIC de la SEC (60–64), ya descargado: **12 unicornios financieros**, marcados «Requiere revisión». |
| 8 | 100 de 161 unicornios no podían recibir datos de mercado (tickers locales de Cboe como `AMDd`). | v2.38BT extrae el ticker estadounidense real de las submissions de la SEC (los 92 unicornios solo-Cboe lo tienen); solo ese ticker se envía a Yahoo. |
| 9 | Las velas y la regresión no podían dibujarse nunca: los CSV de v2.38I solo guardan cierre y volumen. | «Actualizar datos reales» guarda ahora las barras OHLCV que yfinance ya devuelve (`data/explosive_ohlcv_cache_v2_46a/`); sin OHLC real no se inventa nada. |
| 10 | Menores: texto «nan» en fichas; «Estado: Se mantiene» fijo; tracebacks de pyarrow en cada render; el caché de mercado se sobrescribía entero al cambiar de proveedor; `float_shares` de Polygon era en realidad acciones en circulación; escrituras no atómicas de notas con descarte silencioso de un JSON dañado; `Timestamp.utcnow` obsoleto. | Celdas vacías (NaN) tratadas como ausentes; métrica real de crecimiento en lugar del texto fijo; columna «Dato» como texto; fusión del caché por activo y proveedor; `float_shares` de Polygon vacío; escritura atómica y copia `.corrupt-<fecha>` del fichero dañado; `Timestamp.now(tz="UTC")`. |

## Fuera de alcance (decisión pendiente)

El ranking global v2.38BV sigue contando dos veces las 44 empresas con doble cotización (mismo CIK) y v2.38BO no se ha modificado: corregirlos cambiaría cifras ya citadas en las auditorías v2.43A/v2.44A. Queda como decisión explícita.

## Pruebas

`tests/qa_unicorn_section_fixes_v2_46a.py` (14 casos, ejecuta las funciones reales de la app) y ampliación de `tests/qa_global_unicorn_flag_v2_38bt.py` (deduplicación, SIC, ticker real, cifras de crecimiento). Los escenarios de los bugs 3, 6 y 8 se comprobaron además contra la versión anterior del código: fallaban exactamente como se describe.
