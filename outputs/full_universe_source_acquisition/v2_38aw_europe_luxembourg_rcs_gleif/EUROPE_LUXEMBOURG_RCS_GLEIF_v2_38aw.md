# v2.38AW — Número RCS real de Luxemburgo para 18/20 empresas, vía GLEIF por nombre

Fecha: 2026-09-06. Alcance: obtener el número de registro RCS ("B" + dígitos) real de cada una de las 20 empresas luxemburguesas identificadas en `v2.38AV`, como paso previo indispensable para leer los ficheros masivos de cuentas anuales de la Centrale des Bilans (STATEC) — que indexan cada depósito precisamente por ese número.

## Hallazgo real: GLEIF por ISIN no cubre ninguna de las 20 empresas

El método ya probado y de confianza para CH/IT/DK/AT/BE/FI/SE (`v2.38AF`) y Países Bajos (`v2.38AE`) — ISIN → LEI vía GLEIF — se comprobó en vivo contra los 20 ISIN de Luxemburgo: **0/20 con cobertura**, la llamada devuelve `"total":0` para cada uno. Es la misma clase de hallazgo ya documentado para Finlandia en `v2.38AF` (GLEIF simplemente nunca recibió el mapeo ISIN para estos valores) — no un fallo del método, un hueco real y confirmado de la propia base de datos de GLEIF.

## Método alternativo: búsqueda por nombre legal, acotada a Luxemburgo

`scripts/resolve_europe_luxembourg_rcs_gleif_v2_38aw.py` usa el filtro `filter[entity.legalName]` de GLEIF (confirmado en vivo que hace coincidencia por prefijo sobre la cadena completa, no una búsqueda difusa) más `filter[entity.legalAddress.country]=LU`. Se comprobó en vivo que buscar la frase completa y abreviada tal como la escribe Xetra (p. ej. "MILLICOM INTL CELL.") no encuentra nada — ningún nombre real empieza literalmente por esa abreviatura. Se adoptó el mismo patrón ya usado en Finlandia (`v2.38AU`): consultar solo con la **primera palabra** (siempre la marca real, nunca abreviada en este lote) y dejar que la comparación palabra-por-palabra de este script haga el emparejamiento preciso entre los candidatos devueltos.

Tres tipos reales de ruido de Xetra, resueltos con reglas genéricas, nunca por empresa:

1. **Truncamiento con punto final** (p. ej. "PROPERT." por "Properties", "CELL." por "Cellular"): la última palabra, si termina en punto, se compara como prefijo, no por igualdad exacta.
2. **Abreviatura estándar sin punto** (p. ej. "INTL" por "International", "GRP" por "Group"): tabla pequeña y genérica de abreviaturas de diccionario, la misma disciplina que la tabla de transliteración AE/OE ya usada para nombres alemanes/fineses.
3. **Forma jurídica con o sin puntos** (confirmado en vivo: "Aroundtown SA" sin puntos, frente a "ArcelorMittal S.A." con puntos) — la expresión regular acepta ambas grafías.

## Resultado real

**18/20 resueltos, 0 ambiguos.** Números RCS reales verificables de forma independiente:

| Empresa | RCS | Empresa | RCS |
|---|---|---|---|
| ArcelorMittal | B82454 | RTL Group S.A. | B10807 |
| Spotify Technology S.A. | B123052 | Tenaris S.A. | B85203 |
| Aroundtown SA | B217868 | Grand City Properties S.A. | B165560 |
| Global Fashion Group S.A. | B190907 | Millicom International Cellular S.A. | B40630 |
| CPI Property Group | B102254 | Eleving Group | B174457 |
| Adler Group S.A. | B197554 | H2APEX Group SCA | B148525 |
| Logwin AG | B40890 | Befesa S.A. | B177697 |
| Hometogo SE | B249273 | Tonies SE | B252939 |
| Novem Group S.A. | B162537 | Marley Spoon Group SE | B257664 |

**2 quedan honestamente sin resolver, cada una por un motivo real y distinto, nunca adivinado**:

- **Corestate Capital** → el nombre real es "Corestate Capital **Holding** S.A." — Xetra eliminó la palabra "Holding" por completo, sin ningún marcador de truncamiento que lo indique. Sin esa señal, insertar la palabra sería una suposición, no una inferencia — queda sin resolver.
- **Learnd SE** → confirmado en vivo que GLEIF no tiene ningún registro LEI para "Learnd" en Luxemburgo (`"total":0`) — no es un fallo de emparejamiento, es que la empresa no tiene (o no tiene todavía) un LEI registrado.

## Qué NO hace este bloque

No descarga ni lee ningún fichero de cuentas anuales todavía — eso es `v2.38AX`, que usa estos 18 números RCS como clave de búsqueda directa contra los ficheros trimestrales de STATEC.

## Pruebas offline

`tests/qa_europe_luxembourg_rcs_gleif_v2_38aw.py` — 7 casos: coincidencia exacta de una sola palabra (ArcelorMittal), truncamiento con punto (Grand City Properties), abreviatura estándar sin punto (Millicom), palabra completa eliminada sin marcador (Corestate, queda sin resolver), sin registro LEI en absoluto (Learnd), forma jurídica sin puntos (Aroundtown), y filas de otros países nunca consultadas.

```
.venv/Scripts/python.exe tests/qa_europe_luxembourg_rcs_gleif_v2_38aw.py
PASS: v2.38AW-europe-luxembourg-rcs-gleif/exact-match/truncation/abbreviation/dropped-word/no-record/dotless-sa/country-filter/no-network
```

## Seguridad y alcance

Sin credenciales (GLEIF es gratis y sin cuenta). Red real usada solo para consultar GLEIF (nunca para descargar cuentas anuales todavía). Sin scoring, ranking, recomendaciones, fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_LUXEMBOURG_RCS_GLEIF`.** 18/20 empresas con número RCS real confirmado, listas para la extracción de fundamentales en `v2.38AX`.
