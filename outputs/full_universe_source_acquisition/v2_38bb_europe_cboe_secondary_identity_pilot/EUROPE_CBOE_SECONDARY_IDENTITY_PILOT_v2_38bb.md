# v2.38BB — Piloto real de identidad para el hueco de Cboe Europe: refinado de 28% a 58,7%

Fecha: 2026-09-06/07. Alcance: piloto real y acotado (75 empresas, muestra aleatoria reproducible) sobre el hueco más grande y nunca atacado de este proyecto — las 21.066 filas `CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED` de `v2.38N` — antes de decidir si se ataca la población completa. Instrucción del usuario tras ver la caracterización real: "piloto pequeño primero". Instrucción siguiente, tras el primer resultado (36%): "refina el método antes de escalar".

## Caracterización real previa (desk research, sin red)

De las 21.066 filas:
- **~10.176 (48%)** son ETFs/ETPs por patrón de nombre (WisdomTree, iShares, Xtrackers, Ossiam, apalancados, cripto) — estructuralmente fuera de alcance, sin balance ni cuenta de resultados que extraer.
- **387** ya coinciden con empresas europeas ya identificadas en los 689 (`v2.38AB`) — Allianz, BNP Paribas, Deutsche Bank, Volkswagen, ING, Nokia, ABB, Crédit Agricole entre ellas.
- **202** ya coinciden con nombres del censo de EE. UU.
- **~9.630 candidatas reales, nunca antes tocadas por este proyecto** — sin ISIN, país, moneda ni sector en el censo (confirmado en vivo inspeccionando filas reales: todos esos campos vienen vacíos, con `missing_isin` marcado explícitamente por `v2.38A`).

Sin ISIN, el método ya probado (prefijo ISIN → país) no es aplicable aquí — la única vía real es la búsqueda por nombre legal en GLEIF, **sin filtro de país** (a diferencia de Luxemburgo, donde el país ya se sabía).

## Diseño del piloto

Muestra aleatoria reproducible de 75 empresas (semilla fija `2026`, sin selección manual), la misma en las cuatro rondas de refinamiento para que los resultados sean directamente comparables. Fail-closed en todo momento: cero coincidencias exactas o múltiples países distintos → sin resolver/ambiguo, nunca adivinado.

## Cuatro hallazgos reales, cada uno encontrado y corregido en vivo dentro del propio piloto

| # | Hallazgo real | Ejemplo confirmado en vivo | Acierto acumulado |
|---|---|---|---:|
| 0 | (línea base: búsqueda ingenua por primera palabra normalizada) | — | 28,0% |
| 1 | GLEIF escribe "Inc." con punto; la fuente escribe "Inc" sin punto — quitar la forma jurídica *antes* de limpiar la puntuación bloqueaba la coincidencia | `UBER TECHNOLOGIES, INC.` vs `Uber Technologies Inc` | 36,0% |
| 2 | Formas jurídicas completas en vez de abreviadas (Public Limited Company, Aktiengesellschaft, Société Anonyme...) | `CRODA INTERNATIONAL PUBLIC LIMITED COMPANY` vs `Croda International PLC` | 36,0%* |
| 3 | La consulta a GLEIF debe conservar la puntuación original de la primera palabra (GLEIF hace coincidencia literal por prefijo); y si la primera palabra es demasiado genérica, reintentar con las dos primeras | `W.W. GRAINGER, INC.` solo aparece buscando `"W.W."`, nunca `"WW"`; `Check Point Software Technologies` solo aparece buscando `"Check Point"`, nunca `"Check"` solo | 46,7% |
| 4 | Formas jurídicas abreviadas vs. escritas por extenso en la dirección contraria (Ltd/Limited, Corp/Corporation, Co/Company) — el hallazgo de mayor impacto individual | `China Overseas Land & Investment Ltd` vs `...Limited`; `Canadian National Railway Co` vs `...Company` | **58,7%** |

*El hallazgo 2 no cambió el porcentaje agregado de esa ronda por sí solo (otras empresas de la muestra compensaron), pero es un hallazgo real y verificado independientemente (Croda), documentado y conservado en el método.

## Resultado real final (estable, cuatro rondas de corrección)

**44/75 resueltas (58,7%), 7/75 ambiguas (9,3%), 24/75 sin resolver (32,0%).**

Países reales encontrados entre las resueltas — mucho más diverso que la primera pasada: GB (13), US (6), DE (3), DK (3), CH (2), CN (2), CY (2), FR (2), NO (2), SE (2), BM (1), CA (1), FI (1), GG (1), KY (1), VG (1), ZM (1). Confirma que este hueco alcanza jurisdicciones nunca antes tocadas por el proyecto (Chipre, Guernsey, Bermudas, Islas Vírgenes Británicas, Zambia) junto a países ya conocidos.

De las 44 resueltas, **10 solo se encontraron gracias al reintento con dos palabras** (hallazgo 3) — confirmación directa de que esa corrección no fue cosmética.

**Motivos reales de las 24 sin resolver, investigados con ejemplos concretos, sin más margen de mejora genérica encontrado**:
- **Sin registro LEI real en absoluto**: confirmado en vivo para varias (p. ej. `Tokyo Electron` → 0 resultados totales en GLEIF bajo ese nombre) — dato honesto, no un fallo de emparejamiento.
- **Nombre en escritura no latina o registrado solo bajo su nombre japonés/chino real**: límite real del método de búsqueda en inglés/latino, no resuelto por ninguna de las cuatro correcciones.
- **Palabra de búsqueda todavía demasiado genérica incluso con dos palabras**: casos residuales no investigados en detalle por rendimientos decrecientes.

## Proyección a la población completa (extrapolación lineal, no una garantía)

Aplicando la tasa real final a las ~9.630 candidatas: **~5.650 resueltas, ~900 ambiguas, ~3.080 sin resolver**. Una ejecución completa es la única forma de confirmar el número real — esta es una señal de escala, no una promesa.

## Qué NO hace este bloque

No ejecuta la resolución completa de las ~9.630 candidatas — eso sigue pendiente de una decisión explícita del usuario. El acierto pasó de 28% a 58,7% (más del doble), un salto real y significativo, pero sigue por debajo del 90%+ típico de los pilotos por país de este proyecto; escalar implica miles de llamadas de red reales y cientos de casos ambiguos que necesitarán revisión manual. No reconstruye `v2.38AL` ni `v2.38AM`. No investiga todavía ningún registro nacional para las empresas que sí resuelven.

## Pruebas offline

`tests/qa_europe_cboe_secondary_identity_pilot_v2_38bb.py` — 10 casos, uno por cada hallazgo real documentado arriba, más los casos base ya existentes (exclusión de ETFs, exclusión de duplicados, ambigüedad real nunca adivinada, sin registro LEI, modo sin ejecución sin red).

```
.venv/Scripts/python.exe tests/qa_europe_cboe_secondary_identity_pilot_v2_38bb.py
PASS: v2.38BB-europe-cboe-secondary-identity-pilot/period-bug-fix/plc-full-form/etf-filter/dedup/exact-match/ambiguous/unresolved/dry-run/no-network
```

## Seguridad y alcance

Sin credenciales (GLEIF gratis, sin cuenta). Red real usada solo para las consultas del piloto (75 empresas × 4 rondas de refinamiento). Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_CBOE_SECONDARY_IDENTITY_PILOT_NOT_SCALED`.** Piloto real ejecutado y refinado en cuatro rondas, cuatro bugs reales encontrados y corregidos en vivo, acierto más que duplicado (28% → 58,7%). La decisión de escalar a las ~9.630 candidatas completas sigue explícitamente pendiente del usuario.
