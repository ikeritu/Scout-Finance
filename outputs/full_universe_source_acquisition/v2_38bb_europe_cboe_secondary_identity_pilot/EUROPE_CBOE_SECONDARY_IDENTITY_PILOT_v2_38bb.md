# v2.38BB — Piloto real de identidad para el hueco de Cboe Europe: 36% resuelto, 5% ambiguo

Fecha: 2026-09-06/07. Alcance: piloto real y acotado (75 empresas, muestra aleatoria reproducible) sobre el hueco más grande y nunca atacado de este proyecto — las 21.066 filas `CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED` de `v2.38N` — antes de decidir si se ataca la población completa. Instrucción del usuario tras ver la caracterización real: "piloto pequeño primero".

## Caracterización real previa (desk research, sin red)

De las 21.066 filas:
- **~10.176 (48%)** son ETFs/ETPs por patrón de nombre (WisdomTree, iShares, Xtrackers, Ossiam, apalancados, cripto) — estructuralmente fuera de alcance, sin balance ni cuenta de resultados que extraer.
- **387** ya coinciden con empresas europeas ya identificadas en los 689 (`v2.38AB`) — Allianz, BNP Paribas, Deutsche Bank, Volkswagen, ING, Nokia, ABB, Crédit Agricole entre ellas.
- **202** ya coinciden con nombres del censo de EE. UU.
- **9.634 candidatas reales, nunca antes tocadas por este proyecto** — sin ISIN, país, moneda ni sector en el censo (confirmado en vivo inspeccionando filas reales: todos esos campos vienen vacíos, con `missing_isin` marcado explícitamente por `v2.38A`).

Sin ISIN, el método ya probado (prefijo ISIN → país) no es aplicable aquí — la única vía real es la búsqueda por nombre legal en GLEIF, **sin filtro de país** (a diferencia de Luxemburgo, donde el país ya se sabía).

## Diseño del piloto

Muestra aleatoria reproducible de 75 empresas (semilla fija `2026`, sin selección manual) sobre las 9.634 candidatas reales. Búsqueda GLEIF por primera palabra del nombre (mismo patrón de Finlandia/Luxemburgo), verificación exacta tras normalizar forma jurídica y puntuación, fail-closed: cero o múltiples países distintos → sin resolver/ambiguo, nunca adivinado.

## Dos hallazgos reales que mejoraron el piloto en vivo

1. **Bug real de normalización, encontrado y corregido**: GLEIF escribe "Inc." con punto final; la fuente de Cboe escribe "Inc" sin punto. El código original quitaba la forma jurídica *antes* de limpiar la puntuación, así que el punto final bloqueaba la coincidencia (`"UBER TECHNOLOGIES, INC."` nunca convergía con `"Uber Technologies Inc"`). Corregido invirtiendo el orden: puntuación primero, forma jurídica después. **Resultado: sube de 28% a 36% de acierto.**
2. **Formas jurídicas completas no reconocidas**: GLEIF a veces usa la forma legal completa ("Public Limited Company") donde la fuente usa la abreviatura ("PLC") — confirmado en vivo con Croda International (`CRODA INTERNATIONAL PUBLIC LIMITED COMPANY` en GLEIF vs `Croda International PLC` en Cboe). Añadidas alias genéricas y verificables (Public Limited Company, Aktiengesellschaft, Aktiebolag, Naamloze Vennootschap, Société Anonyme, Allmennaksjeselskap, Società per Azioni) — mismo principio que la tabla de abreviaturas ya usada en Luxemburgo.

## Resultado real del piloto (tras ambas correcciones)

**27/75 resueltas (36%), 4/75 ambiguas (5,3%), 44/75 sin resolver (58,7%)** — números estables tras dos rondas de corrección, no una casualidad de la primera pasada.

Países reales encontrados entre las resueltas: GB (10), US (5), CH (3), DK (2), SE (2), DE (1), FI (1), FR (1), NO (1), KY (1) — confirmando que este hueco toca países ya conocidos y también nuevos para el proyecto (Noruega, Suiza ya visto, Islas Caimán ya visto).

**Motivos reales de las 44 sin resolver, investigados con ejemplos concretos**:
- **Sin registro LEI real en absoluto** (empresas pequeñas, AIM, fondos cerrados): confirmado en vivo para varias — dato honesto, no un fallo de emparejamiento.
- **Palabra de búsqueda genérica satura el resultado**: `US BANCORP` → primera palabra "US" es demasiado genérica, no localiza el banco real entre resultados poco relacionados.
- **Nombre en escritura no latina**: Canon Inc. (Japón) no aparece con un nombre romanizado reconocible entre los primeros resultados de "CANON" — un límite real del método de búsqueda por nombre en inglés/latino.
- **Puntuación dentro de la primera palabra**: "W.W. Grainger" — la coincidencia por prefijo de GLEIF no encuentra la primera palabra limpia "WW" contra el original con puntos.

## Proyección a la población completa (extrapolación lineal, no una garantía)

Aplicando la tasa real del piloto a las 9.634 candidatas: **~3.468 resueltas, ~514 ambiguas, ~5.652 sin resolver**. Una ejecución completa es la única forma de confirmar el número real — esta es una señal de escala, no una promesa.

## Qué NO hace este bloque

No ejecuta la resolución completa de las 9.634 candidatas — eso queda pendiente de una decisión explícita del usuario, dado el coste real (horas de llamadas a red) y la tasa de acierto moderada (36%, no el 90%+ visto en los pilotos por país). No reconstruye `v2.38AL` ni `v2.38AM`. No investiga todavía ningún registro nacional para las empresas que sí resuelven.

## Pruebas offline

`tests/qa_europe_cboe_secondary_identity_pilot_v2_38bb.py` — 8 casos: convergencia de normalización pese a puntuación distinta (el bug real corregido), forma jurídica completa reconocida, exclusión de ETFs, exclusión de duplicados ya conocidos, coincidencia exacta, ambigüedad real nunca adivinada, sin registro LEI, y modo sin ejecución sin red.

```
.venv/Scripts/python.exe tests/qa_europe_cboe_secondary_identity_pilot_v2_38bb.py
PASS: v2.38BB-europe-cboe-secondary-identity-pilot/period-bug-fix/plc-full-form/etf-filter/dedup/exact-match/ambiguous/unresolved/dry-run/no-network
```

## Seguridad y alcance

Sin credenciales (GLEIF gratis, sin cuenta). Red real usada solo para las 75 consultas del piloto. Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_CBOE_SECONDARY_IDENTITY_PILOT_NOT_SCALED`.** Piloto real ejecutado, dos bugs reales corregidos en vivo, tasa de acierto real y estable medida (36%). La decisión de escalar a las 9.634 candidatas completas queda explícitamente pendiente del usuario.
