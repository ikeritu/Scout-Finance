# v2.38AQ — Países Bajos: clasificación sectorial vía Wikidata (excepción de política aprobada por el usuario)

Fecha: 2026-09-06. Alcance: continuar el ataque al hueco de sector europeo con Países Bajos (44/689 activos, identidad ya resuelta al 100% desde `v2.38AB`).

## La decisión real, no asumida unilateralmente

El registro oficial neerlandés (KVK) sí tiene el código SBI real de cada empresa — pero su API real de producción **exige suscripción de pago**, confirmado en vivo (`developers.kvk.nl`, enero 2026): 6,40€/mes de cuota base más una pequeña tarifa por consulta, incluso para el endpoint de búsqueda más básico. Su dataset abierto gratuito existe (`kvk.nl`, licencia CC BY 4.0) pero está **anonimizado** — sin nombre de empresa ni número KVK, inútil para identificar el sector de una empresa concreta como ASML o Heineken.

Antes de decidir, se comprobó en vivo una alternativa gratuita real: Wikidata, consultado por ISIN (propiedad P946) para obtener la industria (P452) de cada empresa — **35/44 con coincidencia real de industria en inglés en la comprobación inicial** (p. ej. ASML→"semiconductor industry", Heineken→"brewing industry"). Se presentó la elección real al usuario (pagar el KVK, usar Wikidata, o dejar el país sin atacar) — **el usuario eligió Wikidata**.

## Por qué esto es una excepción de política, no la norma

Wikidata **no es un registro oficial del gobierno** — es una base de datos abierta, sin ánimo de lucro (Fundación Wikimedia), editada por la comunidad. Es una categoría distinta a los casos ya usados en este pipeline: más parecida a OffeneRegister.de (reutilización cívica sin ánimo de lucro, ya considerada aceptable en principio en `v2.38AC`, aunque esa estaba técnicamente caída) que a Companies House o SIRENE (registros oficiales) — y también distinta de firmenakte.at (excepción comercial de pago aprobada en `v2.38AI`). Cada fila de este bloque lleva un campo `non_official_source_caveat` explícito, y `v2.38AM` nunca trata esta fuente con la misma confianza que GB/Francia.

## Resultado real

**32/44 empresas con industria real capturada, 0 errores.** Desglose honesto de las 12 restantes: 6 con item de Wikidata pero sin la propiedad de industria (`no_industry`), 3 sin ningún item de Wikidata que use ese ISIN (`no_wikidata_match`), **3 genuinamente ambiguas** — un hallazgo real que confirma exactamente el riesgo que motiva el diseño fail-closed de este script: **Ahold Delhaize** tiene DOS elementos de Wikidata distintos (`Q795473` "Ahold", la entidad previa a la fusión de 2016, y `Q20539261` "Ahold Delhaize", la entidad actual) que comparten el mismo ISIN real — comprobado en vivo. Ninguno de los dos se elige arbitrariamente; la fila queda sin industria, documentada como ambigua, nunca adivinada.

## Salvaguardas

Bloqueado por defecto; requiere `--execute` (sin credencial, la consulta SPARQL pública de Wikidata no la necesita). 7 pruebas offline nuevas, incluida una que reproduce exactamente el caso real de Ahold Delhaize. Sin scoring, sin ranking, sin recomendaciones.

**Estado del bloque: `COMPLETED_EUROPE_NETHERLANDS_WIKIDATA_SECTOR`.** Alimenta la tercera reconstrucción de `v2.38AM` (contexto geopolítico), con el campo `non_official_source_caveat` propagado a `macro_limitations` para cada empresa neerlandesa.
