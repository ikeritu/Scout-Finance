# v2.38AM — Módulo geopolítico generalizado a las 1.244 empresas con identidad real (EE. UU. + Europa)

Fecha: 2026-09-06. Alcance: generalizar `v2.38M` (contexto macro/geopolítico estático, aplicado hasta ahora solo a las 50 empresas de la shortlist estadounidense antigua) a **toda** la población con identidad real confirmada por `v2.38AL`: 1.244 empresas (555 EE. UU. + 689 Europa).

## Por qué este bloque

El objetivo original del usuario incluía explícitamente razones geopolíticas junto a la lógica económica ("Además de lógicas económicas también se deben tener en cuenta razones geopolíticas"). `v2.38M` ya construyó el motor correcto — una taxonomía estática, offline, sin noticias en vivo, sin llamada a red, sin clasificación por LLM en tiempo de ejecución — pero solo lo aplicó a un subconjunto de 50 empresas de EE. UU. ya obsoleto respecto al resto del pipeline. Este bloque reutiliza ese mismo motor (misma disciplina: `STATIC_TAXONOMY`, `OFFLINE_STATIC_NO_LIVE_NEWS`) y lo generaliza, siguiendo el mismo patrón de generalización ya aplicado varias veces esta sesión (GLEIF, resolución de identidad, alias de conceptos contables).

## Qué cambia respecto a v2.38M

1. **Población**: de 50 empresas (shortlist antigua) a 1.244 (toda empresa con `identity_status=RESOLVED` en `v2.38AL`) — nunca se inventa contexto para una empresa sin identidad confirmada.
2. **Cuatro temas nuevos, condicionados por país real**: `EU_SINGLE_MARKET_REGULATION` (los 11 países UE reales del alcance: DE/FR/NL/IT/AT/BE/ES/IE/FI/SE/DK), `EUROZONE_ECB_MONETARY_POLICY` (los 9 que realmente usan el euro, excluyendo SE/DK), `UK_POST_BREXIT_TRADE_FRICTION` (solo GB), `CHF_SAFE_HAVEN_DYNAMICS` (solo CH). Son hechos jurisdiccionales estables y verificables, no afirmaciones sobre eventos con fecha — misma disciplina que los temas ya existentes de v2.38M (tipos de interés, inflación).
3. **Limitación honesta explícita y nueva**: EE. UU. tiene texto narrativo real (`v2.38J`: resúmenes de señal fundamental/precio/riesgo) para el emparejamiento por palabra clave; Europa **no capturó nunca** ningún campo narrativo en su extracción de fundamentales — su emparejamiento de sector depende solo del `company_name`. Esto se refleja en `macro_limitations` de cada fila, con un mensaje distinto cuando no hay texto narrativo disponible frente a cuando sí lo hay pero no coincide.

## Resultado real

**1.244/1.244 empresas procesadas, 0 rechazadas.** `MACRO_CONTEXT_READY` (coincidencia de sector real): **108**, todas EE. UU. — **ninguna empresa europea coincidió con ningún tema de sector solo por su nombre**, un hallazgo real y honesto que confirma la limitación anticipada: los nombres legales europeos (p. ej. "OMV AKTIENGESELLSCHAFT", que es realmente una petrolera) no contienen las palabras clave en inglés que usa la taxonomía. El resto, **1.136**, queda en `MACRO_CONTEXT_PARTIAL` (solo temas generales + temas de país cuando aplican).

Verificación real por país: `OMV AG` (Austria, petrolera real) → `EU_SINGLE_MARKET_REGULATION` + `EUROZONE_ECB_MONETARY_POLICY` correctamente aplicados, pero sin tema de sector (esperado, por la limitación documentada). `Kingfisher plc` y `Softcat plc` (GB) → `UK_POST_BREXIT_TRADE_FRICTION` correctamente aplicado, nunca los temas UE/Eurozona (GB no es miembro de ninguno de los dos desde el Brexit).

## Salvaguardas

Idénticas a `v2.38M`: sin red, sin noticias en vivo, sin clasificación por LLM en tiempo de ejecución, sin modificar ningún score/ranking/feature ya calculado, sin recomendaciones, sin fase 9C. 8 pruebas offline nuevas, todas con datos sintéticos.

**Estado del bloque: `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** Primera generalización real del módulo geopolítico a la población completa con identidad confirmada; el hueco de emparejamiento de sector en Europa (0/689) queda documentado como el próximo objetivo natural de mejora — probablemente exigirá una fuente real de clasificación sectorial (GICS/NACE) en vez de depender solo del nombre legal, algo que este bloque señala pero no resuelve.
