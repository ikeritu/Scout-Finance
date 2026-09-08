# v2.38BU — Fase 9C, bloque 1: operating_margin, eps_basic y book_value_per_share, cero red nueva

Fecha: 2026-09-08. Alcance: el usuario autorizó explícitamente la Fase 9C. Antes de calcular ningún score hace falta un dato real que el pipeline nuevo (`v2.38F`/`v2.38G`) nunca extrajo: el motor de scoring ya validado del producto antiguo (`scripts/scoring_engine/core.py`, contrato `config/scoring_factor_contract_v1.json`, v2.35A3) necesita `operating_margin` (el factor de mayor peso de "calidad", 0,10), y `eps_basic`/`book_value_per_share` (toda la vertical de "valoración", 0,20 de peso combinado).

## Verificación real antes de escribir código

Antes de asumir que hacía falta una nueva descarga de la SEC, se comprobó directamente el fichero real ya cacheado localmente (`CIK0000002488.json`, parte de `sec_raw_cache_v2_38e`): los tres conceptos existen de verdad en los datos ya descargados — `OperatingIncomeLoss`, `CommonStockSharesOutstanding` bajo `us-gaap`, y `eps_basic`/`eps_diluted` ya estaban siendo extraídos por `v2.38F` desde el principio, solo que `v2.38G` nunca los llevó a su fichero de salida. **Cero llamadas de red nuevas en todo este bloque.**

## Cero lógica de extracción nueva — reutilización real, no reescritura

Este bloque reutiliza sin cambios `normalize_us_sec_fundamentals_v2_38f.normalize_company()` (la misma función real que `v2.38BK` ya reutiliza para las 538 empresas de Cboe Europe secundaria) y `build_us_sec_fundamental_features_v2_38g.selected_annual()`/`ratio()`/`rounded()`. La única extensión real es añadir dos conceptos SEC nuevos al mapa `METRIC_CONCEPTS` de `v2.38F` — hecho mediante *monkeypatch* sobre el objeto del módulo cargado dinámicamente, **nunca editando el fichero de `v2.38F` en disco**, el mismo criterio que `v2.38BQ` ya aplicó al bug de "S.P.A." para no alterar retroactivamente fases ya completadas y citadas en otros sitios.

## Un bug real encontrado y corregido en el camino

La primera ejecución real devolvió `book_value_per_share` vacío para las 1.089 empresas, sin ninguna excepción. Diagnóstico real: `v2.38F` tiene su propia función `supported_unit()`, que solo acepta unidades `"USD"` o que terminen en `"/shares"` (pensada para conceptos en dólares y para ratios por acción como `eps_basic`) — pero un **recuento** bruto de acciones (`CommonStockSharesOutstanding`) reporta su unidad real en los datos de la SEC como la cadena `"shares"` a secas, ni `"USD"` ni `"*/shares"`, confirmado contra el propio JSON real ya cacheado. Corregido con el mismo criterio de *monkeypatch* aditivo: se envuelve `supported_unit()` sobre el objeto del módulo cargado, aceptando `"shares"` solo para el nuevo concepto `shares_outstanding`, sin tocar el comportamiento real de ningún otro concepto ya validado por `v2.38F` (revenue, net_income, eps_basic...) — verificado con una prueba explícita que confirma que el comportamiento original sigue exactamente igual para todo lo demás.

## Resultado real

Sobre las 1.089 empresas reales de origen EE. UU. con CIK conocido (555 originales + 538 nuevas de Cboe Europe secundaria + Joby Aviation):

| Estado | Empresas |
|---|---:|
| `READY` (los 3 campos reales) | **564** |
| `PARTIAL` (1 o 2 de los 3) | 494 |
| `NO_CONCEPTS_AVAILABLE` | 14 |
| `INSUFFICIENT_EVIDENCE` (sin ningún periodo anual normalizable) | 17 |

Ejemplos reales verificados a mano: Apple Inc. — margen operativo real 31,97%, EPS real 7,49, valor contable por acción real 4,99 (bajo por las recompras masivas de Apple, un hecho real conocido, no un error); American Airlines Group — valor contable por acción real **negativo** (-5,64), un hecho real y correcto sobre una aerolínea con patrimonio neto negativo por su deuda, no un fallo del script.

## Qué NO hace este bloque

No calcula ningún score, ranking ni recomendación. No modifica `v2.38F` ni `v2.38G` en su sitio — es una extensión aditiva nueva, en su propio fichero, que el siguiente bloque (`v2.38BV`) unirá por `asset_id`. No cubre Luxemburgo ni Austria (fuentes europeas, sin caché SEC — su propia vertical de valoración, si la tienen, tendría que salir de sus fuentes reales respectivas, fuera del alcance de este bloque).

## Pruebas offline

6 casos en `tests/qa_us_sec_valuation_features_extension_v2_38bu.py`: los 3 conceptos presentes dan `READY` con los valores reales exactos, el bug real de la unidad `"shares"` se reproduce y se confirma corregido, un concepto real ausente deja su campo en blanco sin estimar nada, una empresa sin ningún periodo anual normalizable queda `INSUFFICIENT_EVIDENCE`, una fila sin CIK se salta sin fallar, y una prueba dedicada confirma que el comportamiento original de `supported_unit()` de `v2.38F` sigue exactamente igual para todo lo demás.

## Seguridad y alcance

Cero red, cero credenciales nuevas. Solo lectura de la caché SEC ya descargada y ya usada por fases anteriores de este mismo proyecto.

**Estado del bloque: `COMPLETED_US_SEC_VALUATION_FEATURES_EXTENSION_NOT_SCORING`.** Bloque 1 de 3 de la Fase 9C. Sigue `v2.38BV`: aplicar el motor de scoring real ya validado a todo el universo elegible.
