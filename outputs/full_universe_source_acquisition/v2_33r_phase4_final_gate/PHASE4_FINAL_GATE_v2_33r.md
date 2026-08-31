# Scout Finance v2.33R — gate final y cierre de la fase 4 (Bloque H)

Fecha: 2026-08-31. Este documento cierra la fase 4 (precios históricos y arquitectura multifuente) con base en la evidencia acumulada de v2.33D1 a v2.33Q. No autoriza fundamentales, scoring, rankings, recomendaciones, interfaz de datos reales, ni el inicio de la fase 5.

## H1 — Matriz final

| Mercado | Fuente | Estado | Profundidad | Retraso | Ajustado | Licencia | Cobertura (activos con datos reales) | Decisión |
|---|---|---|---:|---:|---|---|---:|---|
| JPX (Japón) | J-Quants (oficial) | `CONDITIONAL` | ~2 años | 12 semanas | Sí | Personal, confirmada compatible (v2.33N) | 42 / 3.701 | `PASS_FOR_NEXT_CONTROLLED_PILOT` (v2.33G), licencia confirmada (v2.33N), ampliación bloqueada por umbral de 500 |
| TWSE (Taiwán) | STOCK_DAY oficial | `CONDITIONAL` | ~16 años (desde 2010-01-04) | Ninguno | No | Open Government Data License v1.0 | 8 / 696 | `PASS_FOR_NEXT_CONTROLLED_PILOT` (v2.33I), sustituye a EODHD (v2.33O), ampliación bloqueada por umbral de 500 |
| NASDAQ | Twelve Data (candidata, no probada) | `CONDITIONAL` | No confirmada | No confirmado | Parcial (parámetro `adjust` existe, no probado) | Uso personal permitido; plazo de caché no localizado | 0 / 3.016 | `BLOCKED_USER_ACTION_REQUIRED` (v2.33M) |
| NYSE | Twelve Data (candidata, no probada) | `CONDITIONAL` | No confirmada | No confirmado | Parcial | Igual que NASDAQ | 0 / 1.761 | `BLOCKED_USER_ACTION_REQUIRED` (v2.33M) |
| NYSE American | Twelve Data (candidata, no probada) | `CONDITIONAL` | No confirmada | No confirmado | Parcial | Igual que NASDAQ | 0 / 233 | `BLOCKED_USER_ACTION_REQUIRED` (v2.33M) |
| Cboe BZX | Twelve Data (candidata, no probada) | `CONDITIONAL` | No confirmada | No confirmado | Parcial | Igual que NASDAQ | 0 / 1 | `BLOCKED_USER_ACTION_REQUIRED` (v2.33M) |
| Cboe Europe | Ninguna accionable | `EXCLUDED_USER_DECISION` | n/a | n/a | n/a | n/a | 0 / 10.483 | `PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE` (v2.33H), bloqueado indefinidamente |
| ASX | Ninguna gratuita | `EXCLUDED_NO_FREE_SOURCE` | n/a | n/a | n/a | Acceso oficial exige licencia de pago | 0 / 1.271 | `NO_FREE_SOURCE_FOUND` (v2.33J) |
| BVC | SFC (insuficiente) | `EXCLUDED_USER_DECISION` | n/a | n/a | n/a | n/a | 0 / 3 | Cerrado por decisión del usuario (v2.33K) |
| Xetra | Ninguna fuente de precios investigada | `BLOCKED_METADATA_CORRUPTION` (identidad 88,2 % reparada, v2.33P) | n/a | n/a | n/a | n/a | 0 / 1.424 (fuera del censo elegible) | Metadatos reparados; sin fuente de precios evaluada |
| SGX | Ninguna fuente de precios investigada | `BLOCKED_METADATA_CORRUPTION` (identidad 100 % reparada, v2.33P) | n/a | n/a | n/a | n/a | 0 / 358 (fuera del censo elegible) | Metadatos reparados; sin fuente de precios evaluada |

## H2 — Cobertura real (calculada, no estimada a ojo)

Reproducible ejecutando la consulta sobre `eligibility_census_v2_33b2.csv.xz` + las decisiones publicadas en v2.33G–v2.33Q.

- **Candidatos elegibles iniciales:** 21.165 (censo canónico v2.33B2, confirmado en v2.33L).
- **Candidatos con datos reales ya descargados y validados:** **50** (42 JPX + 8 TWSE) — **0,24 % del universo elegible**. Esta es la cobertura operativa real hoy, no una proyección.
- **Candidatos en mercados `CONDITIONAL`** (con fuente candidata o validada, pendientes de ampliación o de una acción del usuario): **9.408 (44,45 %)** — techo teórico, no cobertura ya alcanzada.
- **Candidatos en mercados `EXCLUDED_*`:** **11.757 (55,55 %)** — Cboe Europe, ASX, BVC.
- **Candidatos retenidos por corrupción de metadatos, fuera del censo elegible de 21.165:** 1.782 (Xetra 1.424, SGX 358) — identidad mayoritariamente reparada en v2.33P, sin fuente de precios evaluada.

**Sesgo geográfico:** el universo `CONDITIONAL` (el único con camino realista a corto plazo) se concentra en EE. UU., Japón y Taiwán. Europa continental, Reino Unido (vía Cboe Europe) y Australia quedan `EXCLUDED`. Esto es una limitación estructural del proyecto en su estado actual, no un efecto secundario accidental — debe quedar visible en cualquier interfaz o informe futuro que use este universo, para no penalizar implícitamente a empresas europeas o australianas por la ausencia de datos.

**Activos sin datos y motivo:** todo activo fuera de los 50 con datos reales tiene un motivo de bloqueo o condición explícito y trazable a un cierre publicado (tabla H1) — ninguno queda como "pendiente" sin razón documentada.

## H3 — Decisión

**`COMPLETED_SCOPED_OPERATIONAL_UNIVERSE`**

Justificación, punto por punto contra los 14 requisitos de la sección 3 del encargo:

1. Universo operativo de mercados expresamente definido — sí (v2.33L, H1).
2. Lista definitiva de mercados incluidos/condicionados/excluidos — sí (H1).
3. Al menos una fuente de precios validada por mercado incluido — sí, para los dos únicos mercados con cobertura real (JPX, TWSE); los mercados `CONDITIONAL` sin datos reales todavía (EE. UU.) no tienen fuente validada, solo candidata, y quedan etiquetados como tal, no como "incluidos".
4. Contrato OHLCV común — sí (v2.33Q, `PriceRecord`).
5. Adaptadores reproducibles por proveedor incluido — sí (v2.33Q, J-Quants y TWSE), verificados contra datos reales.
6. Reglas de ajustado/no ajustado — sí, explícitas por proveedor (JPX ajustado, TWSE no ajustado y marcado como tal).
7. Cobertura, profundidad, calidad y licencia documentadas — sí (H1, H2).
8. Actualización incremental, reanudación, rate limiting, trazabilidad — sí, ya implementados en cada descargador (v2.33G, v2.33I) y formalizados como política en v2.33Q (F5); política de frecuencia operativa continua todavía no definida (correctamente fuera de alcance, ningún proveedor ha pasado de piloto a operación continua todavía).
9. QA sin red por adaptador — sí (v2.33G, v2.33I, v2.33P, v2.33Q).
10. Validación controlada con datos reales cuando autorizada — sí (v2.33G: 42/42, v2.33I: 8/8).
11. Manifiesto de cobertura por mercado — sí (v2.33Q, `coverage_manifest_v2_33q.json`).
12. Gate final explícito — este documento.
13. Documentación y versionado coherentes — sí, bloques A–F cerrados con commits separados y verificables.
14. Cero mercados como "pendiente" sin motivo — sí (H1: todo mercado tiene un estado y una razón trazable).

**Esta decisión no implica que la cobertura actual sea amplia.** Es explícitamente **0,24 % de cobertura real hoy**, con un techo teórico del 44,45 % si se resuelven las acciones pendientes (cuenta de Twelve Data, autorización de ampliación de JPX/TWSE) y un 55,55 % del universo excluido de forma permanente en el estado actual de la investigación. Scout Finance trabaja, y seguirá trabajando en el corto plazo, con un **subconjunto muy limitado de mercados**, no con cobertura mundial.

## H4 — Autorización posterior

Aunque la fase 4 se cierra con la decisión anterior:

- **No se inicia la fase 5.**
- **No se promociona scoring.**
- **No se generan rankings reales.**
- **No se modifica la interfaz.**
- **No se calculan recomendaciones.**

El paso a la fase 5 requiere una autorización nueva y explícita del usuario, después de leer este informe.

## Puntos que requieren intervención del usuario (no resueltos en este cierre)

1. **Crear una cuenta gratuita en Twelve Data** (v2.33M) para desbloquear la evaluación real del bloque EE. UU. — no se ha creado, corresponde solo al usuario.
2. **Autorizar la ampliación de JPX** de 42 a hasta 3.701 activos (v2.33N) — estimada en ~31 horas de ejecución acumulada; no ejecutada sin autorización.
3. **Autorizar la ampliación de TWSE** de 8 a hasta 696 activos (v2.33O) — estimada en ~31 horas de ejecución acumulada; no ejecutada sin autorización.
4. **Decidir si se invierte en construir el algoritmo de ajuste de TWSE** usando el endpoint oficial `TWT49U` ya confirmado (v2.33O) — no implementado en este cierre.
5. **Decidir si se investiga una fuente de precios para SGX/Xetra** ahora que su identidad está mayoritariamente reparada (v2.33P), o si se acepta que quedan fuera del universo operativo indefinidamente.

Estos cinco puntos son independientes entre sí y no bloquean unos a otros.

## Seguridad y alcance

- No se ha creado ninguna cuenta, no se ha usado ninguna credencial fuera de la ya existente de J-Quants (sin uso real en este cierre más allá de lo ya publicado en v2.33G), no se ha gastado dinero.
- No se ha descargado ningún precio nuevo en los Bloques A, B (desk research), C (desk research), D (desk research + 1 sondeo sin credenciales), F. El Bloque E usó OpenFIGI (sin cuenta) para reparación de identidad, no de precios.
- Los 6 archivos locales protegidos permanecen intactos y sin versionar (verificado explícitamente en este cierre).
- Escaneo de secretos sobre el diff completo desde el commit base canónico: sin coincidencias.
- Todas las carpetas de datos brutos por proveedor permanecen ignoradas en Git.
- `production_scoring_authorized: false`, `allow_ranking: false` en todos los informes generados.

## Estado del roadmap

- **Fase 4: cerrada** con la decisión `COMPLETED_SCOPED_OPERATIONAL_UNIVERSE`.
- Progreso global: 3/8 fases cerradas + fase 4 cerrada = **4/8 fases cerradas**.
- Interfaz estable: `v2.32F` (sin cambios).
- **Fase 5: no iniciada, no autorizada.** Requiere decisión explícita nueva del usuario tras leer este informe.
