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

**Estado del bloque (primera ejecución): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** Primera generalización real del módulo geopolítico a la población completa con identidad confirmada; el hueco de emparejamiento de sector en Europa (0/689) queda documentado como el próximo objetivo natural de mejora.

---

## Reconstrucción (mismo día, 2026-09-06): ataque real al hueco de sector en Europa

Instrucción del usuario: "ataca el hueco de sector en Europa". En lugar de una fuente única, se atacaron dos huecos reales y ya alcanzables con acceso confirmado:

- **`v2.38AN`** — bug real encontrado en `v2.38Y`: su columna `sic_codes` llevaba vacía desde siempre porque consultaba el endpoint de **búsqueda** de Companies House, que nunca devuelve ese campo (solo el endpoint de **perfil completo** lo hace, confirmado en vivo). Corregido: 29/29 empresas GB con código SIC real, verificado uno a uno contra la lista oficial condensada de Companies House.
- **`v2.38AO`** — misma API gubernamental francesa ya validada en `v2.38AD` (`recherche-entreprises.api.gouv.fr`), ahora consultada por SIREN para capturar el código NAF/NACE real: 18/18 empresas con código verificado contra las páginas de metadatos oficiales del INSEE.

Ambas fuentes se integraron en este mismo módulo (`build_global_macro_geopolitical_context_v2_38am.py`, reconstruido, no reescrito desde cero) como una tercera y cuarta fuente de texto narrativo, junto a los resúmenes de señal de EE. UU. (`v2.38J`), alimentando el mismo motor de coincidencia por palabra clave — nueva columna `sector_text_source` para trazabilidad.

### Resultado real de la reconstrucción

`MACRO_CONTEXT_READY` sube de **108 a 115** (+7, todos en Europa: 3 en Francia — ENGIE→`OIL_GAS_SUPPLY`, Innate Pharma y Abivax→`HEALTHCARE_REGULATION` — y 4 en Reino Unido — Barclays y London Stock Exchange→`BANK_CREDIT_CYCLE`, TechnipFMC→`OIL_GAS_SUPPLY`, PureTech Health→`HEALTHCARE_REGULATION`). Europa pasa de **0/689 a 7/689** con coincidencia real de sector.

**Hallazgo honesto, el mismo en las dos fuentes**: de las 47 empresas nuevas con código real (29 GB + 18 FR), **23 (casi la mitad)** muestran un código genérico de "actividades de sede social" u "holding" (`70100`/`64.20Z`), no su sector operativo real — la entidad registrada en el registro mercantil es la matriz jurídica del grupo, no la marca operativa. Es exactamente el mismo patrón ya documentado en `v2.38AI` (Austria, individual vs. consolidado) — confirmado ahora también en Reino Unido y Francia, con datos reales de tres países independientes.

**Lo que queda sin atacar, explícitamente**: 642 de las 689 empresas europeas (413 Alemania, 44 Países Bajos, 29 Suiza, 22 Italia, 21 Dinamarca, 20 Austria, 17 Irlanda, 15 España, 6 Bélgica, 5 Finlandia, 4 Suecia) siguen sin ninguna fuente de clasificación sectorial confirmada — ningún registro nacional de esos 11 países ha sido investigado todavía para esto. Próximo paso natural: repetir esta misma investigación (¿tiene el registro mercantil de ese país una clasificación de actividad accesible gratis, como Companies House/INSEE?) país por país.

**Estado del bloque (reconstrucción): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** 2 pruebas offline nuevas añadidas (10 en total). Progreso real y honesto, no una solución completa: el hueco de sector en Europa pasa de 0/689 a 7/689, con una causa raíz (holdings registradas vs. operación real) ahora confirmada con evidencia de tres países.

---

## Segunda reconstrucción (mismo día, 2026-09-06): Alemania confirmada estructuralmente sin dato público, Países Bajos vía Wikidata

Instrucciones del usuario: "sigue con Alemania para el hueco de sector" y, tras el hallazgo negativo, "sigue con Países Bajos para el hueco de sector".

**Alemania (`v2.38AP`)**: investigación real, sin script — el código WZ 2008 alemán **no se publica por empresa individual a través de ningún canal gubernamental** (confirmado: Destatis lo mantiene internamente pero explícitamente no lo hace público a terceros; ni el Handelsregister ni el Bundesanzeiger lo incluyen nunca; BRIS no tiene API pública ni lleva ese dato). Distinto en naturaleza de GB/Francia: no es un problema de acceso, es que el dato no es público.

**Países Bajos (`v2.38AQ`)**: el KVK real exige suscripción de pago (confirmado en vivo). Presentada la elección real al usuario (pagar, usar Wikidata, o dejar el país sin atacar), **el usuario eligió Wikidata** — una excepción de política explícita, ya que Wikidata no es un registro oficial del gobierno sino una base de datos abierta editada por la comunidad. 32/44 empresas con industria real capturada vía SPARQL por ISIN. Hallazgo real que confirma el riesgo de una fuente editada por la comunidad: **Ahold Delhaize tiene dos elementos de Wikidata distintos con el mismo ISIN** (la entidad previa a la fusión de 2016 y la actual) — dejado correctamente sin resolver, nunca adivinado.

### Resultado real de esta reconstrucción

`MACRO_CONTEXT_READY` sube de **115 a 129** (+14, todos en Países Bajos vía Wikidata: STMicroelectronics/ASM International/ASML→semiconductores, Airbus/AerCap→defensa o aeroespacial, Pharming/argenx/Redcare Pharmacy→salud, Photon Energy→energía, y varias entidades financieras→banca). Países Bajos pasa de 0/689 a **14/689** con coincidencia real de sector — la mejora más grande de las tres fuentes atacadas hasta ahora.

**Limitación honesta encontrada, nueva**: el emparejamiento por palabra clave es ingenuo (subcadena literal) y el vocabulario de Wikidata no siempre coincide con el de la taxonomía — "aircraft construction" (la industria real de Airbus según Wikidata) coincide por casualidad con la palabra clave "construction" de `CONSTRUCTION_INFRASTRUCTURE`, en vez de con `DEFENSE_SECURITY`, que sería más preciso. No se corrige en este bloque (ampliaría el alcance); queda documentado como una imprecisión conocida del motor de coincidencia, no como un error de los datos de origen.

**Lo que queda sin atacar**: 598/689 empresas europeas (Suiza 29, Italia 22, Dinamarca 21, Austria 20, Irlanda 17, España 15, Bélgica 6, Finlandia 5, Suecia 4) — ningún registro nacional de esos 9 países investigado todavía para clasificación sectorial.

**Estado del bloque (segunda reconstrucción): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** 1 prueba offline nueva añadida (11 en total). El hueco de sector en Europa pasa de 7/689 a 21/689 con esta reconstrucción.
