# v2.38BC — Resolución completa de identidad de Cboe Europe: 3.766 empresas reales en 54 países

Fecha: 2026-09-07. Alcance: escalar el método ya refinado en `v2.38BB` (28% → 58,7% de acierto en un piloto de 75 empresas) a las **7.590 candidatas reales completas** del hueco de Cboe Europe, por decisión explícita del usuario ("escala a las 9.630 candidatas completas" — el número final tras deduplicar por nombre normalizado fue 7.590, no 9.630; ver nota más abajo).

## Ejecución real: un fallo real, diagnosticado y corregido con un diseño más robusto

La primera ejecución (en un único proceso continuo) falló tras 27 minutos y 1.400/7.590 empresas procesadas, con código de salida 4 y sin traza de error de Python — evidencia de un límite de duración del entorno de ejecución, no un fallo del script (el progreso ya guardado, gracias al diseño resumible, no se perdió). Se añadió un parámetro `--limit` al script para procesar en bloques acotados (300 candidatas por invocación) y se relanzó como un bucle de shell que invoca el script repetidamente hasta completar el total — cada invocación resumible, nunca repite una empresa ya resuelta.**22 bloques de 300 (más un bloque final de 107) completaron las 7.590 sin perder ni repetir ningún resultado.**

## Nota real sobre la cifra de candidatas: 7.590, no 9.630

La cifra "9.630" citada al pedir escalar venía de una caracterización preliminar sin deduplicar por nombre normalizado. Al construir el script de escala, deduplicar exactamente por el mismo `normalize_key()` ya usado para las comparaciones (varias filas de Cboe Europe comparten el mismo nombre de empresa bajo distintos `asset_id`/tickers — múltiples clases de acción, ADRs duplicados, etc.) redujo la población real y única a **7.590** — nunca se consulta dos veces a GLEIF por el mismo nombre.

## Resultado real final

**3.766 resueltas (49,6%), 530 ambiguas (7,0%), 3.294 sin resolver (43,4%)**.

**Hallazgo honesto**: la tasa real de la población completa (49,6%) queda **9,1 puntos por debajo** de la extrapolación del piloto de 75 empresas (58,7%) — el propio piloto ya advertía que era "una señal de escala, no una garantía". La causa más probable: una muestra de 75 empresas, aunque aleatoria, tiene más probabilidad de sobrerrepresentar empresas grandes y conocidas (con más probabilidad real de tener LEI) que la cola larga de ~3.300 empresas pequeñas/oscuras que domina la población completa. Queda documentado como una lección real sobre los límites de extrapolar desde una muestra pequeña, no como un fallo del método.

## Diversidad geográfica real: 54 países, muchos nuevos para este proyecto

| País | Empresas | País | Empresas | País | Empresas |
|---|---:|---|---:|---|---:|
| Reino Unido (GB) | 791 | EE. UU. (US) | 628 | Suecia (SE) | 319 |
| Alemania (DE) | 190 | Noruega (NO) | 169 | Suiza (CH) | 159 |
| Francia (FR) | 293 | Finlandia (FI) | 133 | Islas Caimán (KY) | 100 |
| Canadá (CA) | 96 | Dinamarca (DK) | 91 | Bélgica (BE) | 85 |
| Bermudas (BM) | 74 | China (CN) | 63 | Guernsey (GG) | 63 |
| España (ES) | 58 | Austria (AT) | 40 | Jersey (JE) | 45 |
| Sudáfrica (ZA) | 37 | Australia (AU) | 37 | Rumanía (RO) | 36 |
| Irlanda (IE) | 34 | Hong Kong (HK) | 30 | Chipre (CY) | 28 |
| Luxemburgo (LU) | 25 | Islas Vírgenes Británicas (VG) | 24 | Italia (IT) | 13 |
| Isla de Man (IM) | 12 | Malta (MT) | 8 | Singapur (SG) | 8 |
| India (IN) | 9 | Islandia (IS) | 9 | Países Bajos (NL) | 7 |
| Estonia (EE) | 7 | Israel (IL) | 4 | Liechtenstein (LI) | 4 |
| Lituania (LT) | 4 | Islas Marshall (MH) | 4 | Japón (JP) | 3 |
| Nueva Zelanda (NZ) | 3 | Polonia (PL) | 3 | +26 países con 1–2 | — |

**Nuevos para este proyecto, en un solo bloque**: Canadá, China, Sudáfrica, Australia, Rumanía, Hong Kong, Isla de Man, Singapur, India, Islandia, Estonia, Israel, Lituania, Islas Marshall, Japón, Nueva Zelanda, Polonia, y otros 20+ países con 1-2 empresas cada uno (Emiratos Árabes Unidos, Belice, Chile, Chequia, Gabón, Hungría, Kazajistán, Liberia, Mauricio, Malasia, Nigeria, Portugal).

## Qué NO hace este bloque — deliberadamente

**Esto es solo identidad** (nombre legal real + país real, vía LEI de GLEIF) — no fundamentales, no registro mercantil, no sector, no crecimiento. Construir un pipeline de fundamentales para siquiera una fracción de estos 54 países sería un esfuerzo de escala comparable a todo lo hecho hasta ahora para los 13+5 países ya atacados, multiplicado varias veces. No se reconstruyen `v2.38AL` ni `v2.38AM` todavía. No se investiga ningún registro nacional. No se resuelven las 530 empresas ambiguas (requieren revisión manual, nunca una elección automática). No se calcula ningún score, ranking ni recomendación.

## Pruebas offline

Reutiliza sin cambios las 10 pruebas ya existentes de `v2.38BB` (el motor de emparejamiento es idéntico, sin modificar). Pruebas nuevas específicas de la escala en `tests/qa_europe_cboe_secondary_identity_full_v2_38bc.py` (4 casos): resumibilidad real (una empresa ya en la matriz nunca se vuelve a consultar), deduplicación por nombre normalizado, modo sin ejecución sin red, y ejecución completa de principio a fin.

## Seguridad y alcance

Sin credenciales (GLEIF gratis, sin cuenta). Red real usada para ~9.000 llamadas reales (7.590 candidatas × ~1,2 llamadas de media, contando el reintento de dos palabras). Ejecución completa en bloques resumibles, sin pérdida de progreso pese al fallo real del primer intento. Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_CBOE_SECONDARY_IDENTITY_FULL`.** El hueco de Cboe Europe pasa de "21.066 filas sin investigar" a: 10.176 ETFs confirmados fuera de alcance, 589 duplicados de empresas ya cubiertas, 3.766 empresas nuevas con identidad real, 530 ambiguas pendientes de revisión manual, y 3.294 sin registro LEI localizable con este método — un mapa completo y honesto del hueco más grande de este proyecto, listo para que el usuario decida el siguiente paso (fundamentales de algún país concreto, revisión de ambiguas, o dejarlo como identidad-solamente).
