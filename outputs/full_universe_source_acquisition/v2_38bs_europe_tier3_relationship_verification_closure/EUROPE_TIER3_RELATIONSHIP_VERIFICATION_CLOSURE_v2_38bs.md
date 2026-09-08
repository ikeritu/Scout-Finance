# v2.38BS — Nivel 3 por relaciones de GLEIF: investigado en vivo, cierre honesto sin promoción

Fecha: 2026-09-08. Alcance: el usuario pidió continuar con las 174 candidatas "sin confirmar" (Nivel 2) que dejó abiertas `v2.38BQ`. Se investigó si los datos reales de relaciones matriz-filial que GLEIF publica (`direct-parent`, `ultimate-parent`) podían servir como una tercera señal, independiente del nombre, capaz de confirmar o corregir alguna de esas 174 candidatas sin adivinar nunca entre dos empresas reales y distintas.

## Hallazgo inicial real, prometedor pero de un solo caso

Comprobado a mano contra la API real de GLEIF: **DANONE** (Francia, LEI `969500KMUQ2B6CBAF162`) devuelve un **404 real** en `GET /lei-records/{lei}/direct-parent`, mientras que **DANONE SA** (España, LEI `213800S18Y5XNF6TLB35`, la candidata que `v2.38BQ` había marcado como Nivel 2) tiene una relación `direct-parent` real que **resuelve exactamente a la matriz francesa**. Esto confirmaba de forma independiente, sin usar el nombre en absoluto, que la elección del Nivel 2 (España) era la equivocada — el mismo caso que ya había obligado a bajar de categoría el Nivel 2 en `v2.38BQ`.

## El piloto real de 30 casos no reprodujo el hallazgo a escala

Se construyó un piloto real (mismo endpoint, mismo ritmo de `v2.38BB`/`BQ`) contra las primeras 30 candidatas reales de las 174, replicando exactamente la misma lógica: para cada candidata `ISSUED` del mismo nombre exacto, se excluye si su `direct-parent` resuelve a otra candidata del mismo conjunto (filial confirmada de una hermana), y se comprueba si sobrevive exactamente una.

**Resultado real**: 10/30 "confirman" la elección del Nivel 2 (nunca la cambian ni añaden información nueva — ver más abajo), 0/30 corrigen de verdad una elección, y 20/30 siguen con más de un superviviente tras el filtro — incluido, sorprendentemente, el propio caso de Danone.

## Diagnóstico real de por qué Danone no se repitió en el piloto automático

Repitiendo el caso de Danone con el mismo código exacto del piloto, con salida detallada, se encontró que la comprobación manual original solo había revisado 2 de las candidatas reales — pero el conjunto real completo de candidatas `ISSUED` con el nombre exacto "DANONE" tiene **5 miembros**, no 2:

| LEI | País | Resultado real de `direct-parent` |
|---|---|---|
| `969500KMUQ2B6CBAF162` | FR | 404 (sin relación registrada) |
| `213800KHX6QZIXORTF05` | GB | 404 (sin relación registrada) |
| `213800U8U23QO33EER24` | SE | 200 — resuelve a un LEI que **no está** en este mismo conjunto de candidatas (una entidad holding sueca intermedia) |
| `213800S18Y5XNF6TLB35` | ES | 200 — resuelve a la propia FR (**sí** está en el conjunto) → excluida correctamente |
| `21380014E7T1VOHJ8N85` | DK | 404 (sin relación registrada) |

Con la regla "excluir solo si el padre resuelve a otra candidata del mismo conjunto", sobreviven FR, GB, SE y DK — cuatro, no uno. El caso manual pareció limpio solo porque, por casualidad, las dos únicas candidatas comprobadas a mano fueron precisamente la que tiene una relación real que apunta fuera (ES→FR) y la que no tiene ninguna relación registrada (FR). Con las 5 candidatas reales visibles, la ambigüedad no desaparece — cambia de forma.

## La causa real, no un error de programación

Un `404` en este endpoint significa "GLEIF no tiene ningún registro de relación matriz-filial para este LEI" — y eso cubre dos situaciones muy distintas que el endpoint no distingue por sí solo: (a) la entidad está confirmada como la cima de su propio árbol societario (una "reporting exception" real y declarada), o (b) simplemente nadie ha presentado nunca esa relación ante GLEIF, algo frecuente porque el reporte de relaciones matriz-filial en GLEIF es voluntario y muchas filiales reales — sobre todo las más antiguas o las de países con menor exigencia de reporte — no tienen ningún dato de relación cargado. El piloto no puede diferenciar (a) de (b) sin consultar el objeto `relationships` completo del registro LEI (que si existe una "reporting exception" real, la expone con un código de motivo específico) — y aunque se hiciera esa distinción más fina, no habría resuelto el caso real de Danone: GB y DK no tienen ninguna relación cargada (ni real "sin padre" ni real "con padre"), así que seguirían sobreviviendo como candidatas indistinguibles.

## Ni siquiera los 10 "confirmados" añaden información real nueva

Revisando los 10 casos que el piloto marcó como "confirma Nivel 2" (Agilyx ASA, Autoliv Inc, Alleima AB, Assa Abloy AB, Aroundtown SA, Bloomsbury Publishing PLC, Bong AB, Sartorius Stedim Biotech, eBay Inc, Elma Electronic AG): en ningún caso el filtro por relaciones señaló una empresa distinta a la que el Nivel 2 ya había elegido por coincidencia de forma jurídica — el resultado es siempre el mismo dato que ya se tenía, nunca una verificación independiente nueva. El Nivel 3 no aportó una sola confirmación ni corrección real que no viniera ya del propio Nivel 2.

## Conclusión real

Los datos de relaciones matriz-filial de GLEIF son reales y correctos cuando existen, pero su cobertura es demasiado incompleta — por ser un reporte voluntario — para servir como una señal de verificación fiable a esta escala. El hallazgo inicial de Danone fue una coincidencia de qué dos candidatas se comprobaron a mano, no una propiedad general del método. Construir esto en producción no está justificado: 0 correcciones reales sobre 30 casos reales probados, y ni siquiera las "confirmaciones" añaden certeza que el propio Nivel 2 no tuviera ya.

## Qué NO hace este bloque

No modifica `v2.38BQ` ni su clasificación de 200 resueltas / 174 candidatas sin confirmar / 156 ambiguas. No promueve ninguna de las 174 a identidad resuelta. No construye ningún script de producción — el piloto queda como investigación desechada, documentada aquí con su evidencia real, no como código del proyecto. Las 174 candidatas sin confirmar y las 156 ambiguas siguen exactamente donde `v2.38BQ` las dejó: disponibles para revisión manual humana, nunca mezcladas con identidad confirmada.

## Seguridad y alcance

Red real usada solo contra la API pública de GLEIF (mismo endpoint y ritmo ya aprobados en `v2.38BB`/`BC`/`BF`/`BQ`), sobre una muestra real de 30 de las 174 candidatas más un caso adicional (Atos) fuera de la muestra para explorar un modo de fallo distinto. Sin credenciales. Sin scoring, ranking, recomendaciones ni fase 9C.

**Estado del bloque: `COMPLETED_NO_PROMOTION`.** Investigación real completada con evidencia en vivo; el Nivel 3 por relaciones de GLEIF no se incorpora al pipeline porque no supera, en una muestra real, la barra de aportar información nueva y fiable más allá del Nivel 2 ya existente.
