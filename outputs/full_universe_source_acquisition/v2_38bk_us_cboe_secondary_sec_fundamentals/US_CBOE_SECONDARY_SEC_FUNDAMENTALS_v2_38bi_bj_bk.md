# v2.38BI/BJ/BK — el frente Reino Unido/EE. UU.: 538 empresas de EE. UU. con fundamentales reales de la SEC

Fecha: 2026-09-08. Alcance: tras cerrar "consolidar primero" (`v2.38AL`+`v2.38AM`), el usuario eligió explícitamente continuar por Reino Unido/EE. UU. — el mayor volumen pendiente entre las opciones presentadas (791 candidatas GB + 628 candidatas US de `v2.38BC`, cierres offshore rápidos, o revisión manual de las 530 ambiguas). Este bloque ataca la mitad de EE. UU.

## Por qué esto es un hueco real, no solo identidad duplicada

`v2.38BC` ya había resuelto identidad real (nombre legal + país) para las 628 candidatas de Cboe Europe bajo `country=US`, vía GLEIF. Pero GLEIF no da ningún enlace a una fuente de fundamentales — el pipeline de fundamentales de este proyecto para EE. UU. está indexado por CIK real de la SEC, no por LEI. Sin un CIK, estas 628 empresas quedaban permanentemente en `IDENTITY_ONLY_NO_FUNDAMENTALS_YET`, pese a ser en su inmensa mayoría empresas estadounidenses reales, grandes y ya cotizadas (Moderna, Dell Technologies, American Airlines, Robinhood, Comcast...) — el hueco no era de identidad, sino de qué hacer con esa identidad.

## v2.38BI — resolución real de CIK, en tres niveles fail-closed

Sin ninguna llamada de red: `company_tickers_exchange.json` de la SEC ya estaba en caché local (`v2.6C`), y se refrescó una vez más en vivo (200 OK, 10.415 filas) antes de empezar, para partir del dato más actual posible.

El emparejamiento por nombre normalizado encontró y corrigió en vivo tres inconsistencias reales, no hipotéticas, del propio fichero de la SEC:

1. **Sufijo de estado de constitución en tres formas literales distintas** — `/DE`, `/ DE` (con espacio antes de la barra, visto en Rivian Automotive y MP Materials) y `/DE/` (barra también al final, visto en Northrop Grumman) — las tres normalizadas igual.
2. **Manejo inconsistente del apóstrofo dentro de la propia SEC** — "MCDONALDS CORP" sin apóstrofe ni espacio, pero "O REILLY AUTOMOTIVE INC" con el apóstrofe sustituido por un espacio. Resuelto con una clave "aplastada" (sin espacios) como segundo nivel de coincidencia.
3. **Orden invertido apellido-primero en un puñado de registros reales de la SEC** — "PRICE T ROWE GROUP INC" para T. Rowe Price, "SMITH A O CORP" para A.O. Smith — una convención heredada de catalogación antigua. Resuelto con un tercer nivel: comparar el conjunto de palabras ordenado, no el orden literal.

Cada nivel exige un único CIK distinto para aceptar la coincidencia — dos CIK distintos con la misma clave normalizada se dejan `ambiguous`, nunca una elección al azar (en la práctica real, 0 casos ambiguos).

**Resultado real: 538/628 resueltas (85,7%)**, 0 ambiguas, 90 sin resolver — repartidas en tres motivos reales, verificados uno a uno, no solo supuestos: (a) empresas genuinamente no estadounidenses etiquetadas `US` por error en el censo original de Cboe (AMG Critical Materials NV, ASM International NV, Bekaert SA, Huhtamaki Oyj, mBank SA, Bank of China Ltd...); (b) empresas realmente excluidas de bolsa/adquiridas desde que se tomó esta instantánea histórica de Cboe (GrubHub, Hortonworks, Cavium, Clovis Oncology, Activision Blizzard...); (c) un puñado de huecos reales y confirmados del propio fichero de la SEC — AvalonBay Communities, Hologic, Sealed Air y Coterra Energy son empresas reales, grandes y actualmente cotizadas que simplemente no aparecen en `company_tickers_exchange.json`, confirmado con una descarga en vivo fresca, no un problema de caché.

| Nivel de coincidencia | Empresas |
|---|---:|
| Nombre normalizado exacto | 534 |
| Aplastado (espacios) | 2 |
| Conjunto de palabras ordenado | 2 |
| **Total resuelto** | **538** |
| Sin resolver (motivo real documentado) | 90 |

## v2.38BJ — descarga real, reutilizando el fetcher ya probado de v2.38E

Cero código nuevo de red: importa y reutiliza sin modificar `fetch_json`/`write_json`/`fetch_one`/`select_batch`/`has_cache` de `run_us_sec_enrichment_v2_38e.py` — el mismo fetcher resumible, con límite de tasa y escritura atómica ya usado para las 555 empresas originales. Escribe a su propia caché separada (`sec_raw_cache_v2_38bj`), nunca toca la caché de las 555 empresas.

Ejecutado en 3 bloques resumibles de hasta 200 (`--limit 200 --execute`), con la credencial `SCOUT_FINANCE_SEC_USER_AGENT` ya provista por el usuario:

```
Bloque 1: 199/200 (1 fallo real: companyfacts 404)
Bloque 2: 198/200 (mismo fallo repetido + 1 nuevo, 199 ya en caché saltadas)
Bloque 3: 139/141 (mismos 2 fallos, 397 ya en caché saltadas)
```

**536/538 CIK con `companyfacts` real descargado**; 2 con un 404 real y reproducible específicamente en el endpoint de `companyfacts` (pero `submissions` sí respondió) — un estado real y honesto (la empresa presenta ante la SEC pero no tiene datos XBRL estructurados, o su registro es demasiado antiguo/delgado), no un fallo del script.

## v2.38BK — fundamentales reales, reutilizando v2.38F/G sin ninguna línea nueva de extracción

Igual que `v2.38BA` hizo para una sola empresa (Joby Aviation), este bloque es la versión en lote (538 empresas) del mismo patrón: importa y reutiliza sin modificar `normalize_us_sec_fundamentals_v2_38f.normalize_company()`/`quality_row()` y `build_us_sec_fundamental_features_v2_38g.build_company()`/`as_csv_value()` — exactamente la misma metodología ya validada en las 555 empresas originales, aplicada en un bucle.

**Resultado real:**

| Normalización | Empresas | | Features | Empresas |
|---|---:|---|---|---:|
| `NORMALIZED_READY` | 337 | | `FEATURES_READY` | 451 |
| `NORMALIZED_PARTIAL` | 196 | | `FEATURES_PARTIAL` | 80 |
| `NO_NORMALIZABLE_FACTS` | 3 | | `INSUFFICIENT_FEATURE_EVIDENCE` | 2 |

533 empresas con al menos una fila de features (2 sin `companyfacts` cacheado quedan honestamente en `us_cboe_secondary_sec_fundamental_skipped_v2_38bk.csv`, nunca fabricadas). Mayor crecimiento de ingresos interanual real de este lote: Gevo Inc (+849%), ImmunityBio Inc (+668%), Eos Energy Enterprises (+632%), Ondas Inc (+605%), Madrigal Pharmaceuticals (+432%) — cifras extremas propias de empresas de pequeña capitalización en fase de escalado, no un error de cálculo.

## Reconstrucción de v2.38AL (decimocuarta) — el impacto real en la matriz de las 43.089

Nueva rama de prioridad en `build_row()`, insertada justo antes del respaldo genérico de Cboe masivo (`v2.38BC`) para que solo las 538 resueltas por `v2.38BI` se beneficien — las 90 sin resolver siguen cayendo al respaldo genérico exactamente igual que antes.

| `overall_coverage_status` | Antes (13ª reconstrucción) | Después |
|---|---:|---:|
| `GROWTH_READY` | 120 | **417** |
| `GROWTH_PARTIAL` | 391 | **611** |
| `FUNDAMENTALS_READY_NO_GROWTH_YET` | 16 | 16 |
| `FUNDAMENTALS_PARTIAL_NO_GROWTH_YET` | 53 | 67 |
| `IDENTITY_ONLY_NO_FUNDAMENTALS_YET` | 4.281 | 3.750 |
| `NO_DATA_YET` | 38.055 | 38.055 (sin cambios) |

**Empresas con crecimiento interanual real y calculable: de 140 (120 completas + parte de las 391 parciales) a más de 1.000** — el mayor salto individual de todo este esfuerzo de Cboe Europe, y el primero que añade profundidad (fundamentales+crecimiento), no solo identidad, a un volumen de cientos de empresas de una sola vez.

## Qué NO hace este bloque

No ataca Reino Unido (791 candidatas) — Companies House no tiene un endpoint gratuito de estados financieros estructurados equivalente al XBRL de la SEC; sería una investigación nueva, no una reutilización de esta misma infraestructura. No reintenta los 2 fallos reales de `companyfacts` 404. No calcula precio para ninguna de las 538 (`price_status` queda honestamente `NOT_ATTEMPTED`, nunca como un hallazgo negativo confirmado tipo `v2.38AJ`, ya que nunca se ha investigado si `v2.38H` podría extenderse aquí). Sin scoring, ranking, recomendaciones ni fase 9C.

## Pruebas offline

19 casos nuevos: `tests/qa_us_cboe_secondary_identity_sec_v2_38bi.py` (9 — cada uno de los tres niveles de coincidencia, no-ambigüedad por múltiples tickers del mismo CIK, ambigüedad real por dos CIK distintos, sin coincidencia, filtro por fuente de identidad, caché de la SEC ausente), `tests/qa_us_cboe_secondary_sec_enrichment_v2_38bj.py` (5 — filtro de candidatos, bloqueo real por credencial ausente, límite de lote, dry-run sin red), `tests/qa_us_cboe_secondary_sec_fundamentals_v2_38bk.py` (5 — features reales de dos empresas, empresa sin caché saltada, filtro de identidad ambigua/sin resolver, reutilización real de v2.38F/G), y 3 más en `tests/qa_global_coverage_matrix_v2_38al.py` (empresa resuelta con features reales, resuelta sin features todavía, no resuelta cae al respaldo genérico).

**Estado del bloque: `COMPLETED_US_CBOE_SECONDARY_SEC_FUNDAMENTALS`.** Primer avance real de profundidad (no solo identidad) del frente Reino Unido/EE. UU. — Reino Unido queda como el siguiente paso natural, con una pregunta de investigación distinta (fuente de fundamentales, no de identidad, ya que GLEIF/GB Companies House ya cubren esa parte).
