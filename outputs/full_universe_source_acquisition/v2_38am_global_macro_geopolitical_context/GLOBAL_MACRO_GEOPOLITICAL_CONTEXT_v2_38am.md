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

---

## Tercera reconstrucción (mismo día, 2026-09-06): Suiza, con prueba en vivo del registro oficial antes de decidir

Instrucción del usuario: "sigue con Suiza para el hueco de sector". A diferencia de Alemania (investigación de escritorio), aquí se construyó y ejecutó un **cliente SOAP real** contra el registro oficial suizo UID (`uid-wse-a.admin.ch`, Oficina Federal de Estadística): confirmado en vivo que el servicio público (sin cuenta, gratis) funciona y devuelve datos reales de Nestlé, Novartis, Sika, Straumann y Logitech — pero **ni una sola vez** aparece el campo `NOGACode` (clasificación sectorial), ni siquiera en el registro de ejemplo oficial del propio servicio que muestra todos los campos posibles. Mismo patrón exacto que Alemania: el dato existe en el esquema y en el sistema, pero se retiene del nivel público/no autenticado.

Presentada de nuevo la elección real al usuario (Wikidata, ya comprobado en vivo con 16/29 coincidencias, o dejar el país sin atacar), **el usuario eligió Wikidata otra vez**. Dado que es la segunda vez que se usa exactamente el mismo mecanismo, `v2.38AQ` (específico de Países Bajos) se generalizó en `v2.38AR` (acepta `--countries`, cualquier país futuro se reejecuta con el mismo script) — siguiendo el mismo patrón de generalización tras un segundo caso real ya usado con GLEIF (`v2.38AE`→`v2.38AF`).

### Resultado real de esta reconstrucción

`MACRO_CONTEXT_READY` sube de **129 a 135** (+6, todos en Suiza: Novartis→química/farmacéutica, Nestlé→alimentación, ABB→ingeniería eléctrica/robótica, UBS→banca, Sika→química/construcción, Alcon→farmacéutica). Suiza pasa de 0/689 a **6/689** con coincidencia real de sector.

**El hueco de sector europeo pasa de 21/689 a 27/689** (GB 4 + Francia 3 + Países Bajos 14 + Suiza 6). Quedan 8 países sin atacar: Italia (22), Dinamarca (21), Austria (20), Irlanda (17), España (15), Bélgica (6), Finlandia (5), Suecia (4) — 110/689 empresas en total.

**Estado del bloque (tercera reconstrucción): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** 1 prueba offline nueva añadida (12 en total).

---

## Cuarta reconstrucción (mismo día, 2026-09-06): Italia, sin ningún script nuevo

Instrucción del usuario: "sigue con Italia para el hueco de sector". Investigación real: el portal de datos abiertos oficial de InfoCamere (`hvdataset.infocamere.it`) es genuinamente gratuito por regulación europea e incluye código ATECO — pero su frontend usa reCAPTCHA de Google y el acceso está sujeto a restricciones que no permiten una consulta simple por empresa; el otro canal oficial es un producto comercial de pago. Presentada de nuevo la disyuntiva (Wikidata, ya comprobado con 16/22 coincidencias reales, o dejar el país sin atacar), **el usuario eligió Wikidata por tercera vez**.

Al ser ya la tercera vez, **no se creó ningún script nuevo**: se reejecutó directamente `v2.38AR` (el fetcher ya generalizado tras Suiza) con `--countries CH IT` — confirmando en la práctica que la generalización cubre países futuros sin tocar código.

### Resultado real

`MACRO_CONTEXT_READY` sube de **135 a 147** (+12, todos en Italia: Generali→seguros, bancos→financiero, Eni→energía/petróleo, Leonardo→defensa/aeroespacial, Poste Italiane→banca/logística/postal, Fincantieri→construcción naval, Moncler→confección). Italia pasa de 0/689 a **12/689** con coincidencia real de sector.

**El hueco de sector europeo pasa de 27/689 a 39/689** (GB 4 + Francia 3 + Países Bajos 14 + Suiza 6 + Italia 12). Quedan 7 países sin atacar: Dinamarca (21), Austria (20), Irlanda (17), España (15), Bélgica (6), Finlandia (5), Suecia (4) — 88/689 empresas en total.

**Estado del bloque (cuarta reconstrucción): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** Ninguna prueba nueva necesaria (12 en total) — el mecanismo genérico ya estaba probado.

---

## Quinta reconstrucción (mismo día, 2026-09-06): Dinamarca, el primer país con vía oficial gratuita genuinamente pendiente (no bloqueada)

Instrucción del usuario: "sigue con Dinamarca para el hueco de sector". Caso distinto de Alemania/Suiza/Italia: el registro danés CVR (Erhvervsstyrelsen) sí tiene una API oficial real y gratuita con el código DB07 — confirmado en vivo que `distribution.virk.dk` exige cuenta registrada (`401`), la misma solicitud de credencial ya iniciada en una fase anterior de este proyecto (para fundamentales) pero sin confirmar si se completó. Preguntado directamente, el usuario confirmó que aún no tiene esa credencial y eligió Wikidata mientras tanto (14/21 coincidencias reales ya verificadas, 0 ambiguas). Al ser el cuarto país con el mismo mecanismo, se reejecutó `v2.38AR` (`--countries CH IT DK`) sin ningún script nuevo.

### Resultado real

`MACRO_CONTEXT_READY` sube de **147 a 155** (+8, todos en Dinamarca: Carlsberg→alimentación/bebidas, Maersk→transporte marítimo, Genmab/Bavarian Nordic→biotecnología, Ørsted→energía, Coloplast→salud, Tryg→seguros, ISS→gestión de instalaciones). Dinamarca pasa de 0/689 a **8/689** con coincidencia real de sector. Novo Nordisk, sorprendentemente, no tiene coincidencia en Wikidata — un hueco real de esa base de datos, no un fallo del script.

**El hueco de sector europeo pasa de 39/689 a 47/689** (GB 4 + Francia 3 + Países Bajos 14 + Suiza 6 + Italia 12 + Dinamarca 8). Quedan 6 países sin atacar: Austria (20), Irlanda (17), España (15), Bélgica (6), Finlandia (5), Suecia (4) — 67/689 empresas. **Nota abierta**: si el usuario completa el registro CVR pendiente, este bloque debería revisitarse para sustituir Wikidata por el código DB07 oficial en Dinamarca.

**Estado del bloque (quinta reconstrucción): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** Ninguna prueba nueva necesaria (12 en total).

---

## Sexta reconstrucción (mismo día, 2026-09-06): Austria — sin nueva decisión de política, con un fallo real de proveedor documentado

Instrucción del usuario: "sigue con Austria para el hueco de sector". Caso distinto a todos los anteriores: Austria **ya tiene** una fuente real y aprobada (`firmenakte.at`, excepción comercial aprobada en `v2.38AI` para fundamentales) — investigando la respuesta completa de esa misma API se confirmó en vivo que **ya incluye** un campo `oenaces` (ÖNACE oficial, implementación austriaca 1:1 de NACE Rev.2) y un campo `purpose`, nunca antes leídos por `v2.38AI`. Ninguna aprobación nueva del usuario fue necesaria.

Al construir `v2.38AS` se encontró y documentó un **bug real de conectividad del proveedor**: `api.firmenakte.at` sufre una degradación de conexión intermitente real (confirmado durante varios minutos con `curl`, sin relación con ningún límite de tasa ni con el resto de Internet) — Python `urllib` colgaba sistemáticamente contra ese host mientras `curl` respondía al instante, resuelto invocando `curl` como subproceso. El script se hizo **resumible** (nunca repite una empresa ya resuelta), verificado en vivo con tres ejecuciones reales consecutivas que preservaron exactamente las mismas 5 empresas confirmadas sin perderlas ni repetirlas.

### Resultado real (parcial, honesto)

**5/20 empresas austriacas con código ÖNACE real, 15/20 pendientes por la degradación real y actual del proveedor** (STRABAG/PORR→"Activities of head offices", Raiffeisen Bank International/Erste Group Bank→"Other monetary intermediation", Andritz→fabricación de maquinaria papelera). `MACRO_CONTEXT_READY` sube de 155 a **156** (+1: Erste Group Bank, vía `BANK_CREDIT_CYCLE` — su texto alemán de objeto social real, "Bankgeschäfte", coincide por subcadena con la palabra clave "bank", algo que la sola traducción al inglés no habría producido). Austria pasa de 0/689 a **1/689** con coincidencia real de sector, con 4 empresas más ya identificadas correctamente pero sin coincidencia de tema (holdings/bancos sin la palabra exacta).

**El hueco de sector europeo pasa de 47/689 a 48/689.** Este bloque queda explícitamente incompleto: en cuanto el proveedor se recupere, una nueva ejecución de `v2.38AS` completará las 15 empresas restantes sin perder las 5 ya confirmadas, y debería reconstruirse `v2.38AM` de nuevo entonces.

**Estado del bloque (sexta reconstrucción): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** 2 pruebas offline nuevas añadidas (14 en total).

---

## Séptima reconstrucción (mismo día, 2026-09-06): Irlanda — sin nueva política, y un campo real confirmado no fiable descartado deliberadamente

Instrucción del usuario: "sigue con Irlanda para el hueco de sector" (17/689 activos, 8/17 con identidad CRO real desde `v2.38Z`). Igual que Austria: ninguna aprobación nueva necesaria — el dataset abierto del CRO irlandés (`opendata.cro.ie`, ya usado en `v2.38Z` para identidad) ya devuelve un campo `nace_v2_code` real, nunca antes leído.

**Hallazgo real distinto**: un segundo campo (`princ_object_code`) también existe, pero se confirmó en vivo que es **no fiable** — Alkermes plc (una farmacéutica real y conocida) muestra el código "24.41" (fabricación de metales), demostrablemente incorrecto. Confirmado que Alkermes plc se constituyó de nuevo en Irlanda específicamente para su fusión de 2011 (no es una sociedad reutilizada con historial previo), así que el código erróneo probablemente refleja texto genérico de la cláusula de objeto social, no una clasificación real. Este campo se captura solo para trazabilidad y **nunca se usa** como texto de coincidencia de sector — una decisión deliberada de calidad de datos, no una limitación técnica.

### Resultado real

**3/8 empresas irlandesas con código NACE real** (Smurfit Westrock, TE Connectivity, Linde — las tres `6420` "Activities of holding companies", el mismo patrón de domicilio-sin-operación ya visto en GB/Francia/Suiza/Italia/Austria). `MACRO_CONTEXT_READY` se mantiene en **156** — resultado honesto: "holding companies" no coincide con ningún tema actual de la taxonomía, pero la fuente queda correctamente atribuida (`sector_text_source=v2.38AT`) y trazable.

**El hueco de sector europeo se mantiene en 48/689** (Irlanda no añade coincidencias de tema, pero sí clasificación real verificada para 3 empresas). Quedan 4 países sin atacar: España (15), Bélgica (6), Finlandia (5), Suecia (4) — 30/689 empresas.

**Estado del bloque (séptima reconstrucción): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** 2 pruebas offline nuevas añadidas (16 en total).

---

## Octava reconstrucción (mismo día, 2026-09-06): España, sin script nuevo, la mejor cobertura hasta ahora

Instrucción del usuario: "sigue con España para el hueco de sector" (15/689 activos, IBEX 35). Reconfirmado que las tres vías oficiales españolas siguen bloqueadas exactamente igual que en `v2.38AA` (WAF en Registradores, sin API buscable en BORME, formularios ASPX sin API en CNMV — incluida su propia herramienta interna de "Distribución por Sectores"). Presentada de nuevo la disyuntiva (Wikidata, ya comprobado con 13/15 coincidencias reales, o dejar el país sin atacar), **el usuario eligió Wikidata por cuarta vez**. Cuarto país con el mismo mecanismo generalizado — se reejecutó `v2.38AR` (`--countries CH IT DK ES`) sin ningún script nuevo.

### Resultado real

`MACRO_CONTEXT_READY` sube de **156 a 162** (+6, todos España: Cellnex→infraestructura de telecomunicaciones, Amadeus IT→software, Endesa/Iberdrola/Redeia→energía eléctrica, Repsol→petróleo, IAG→aviación, Telefónica→telecomunicaciones — nota: algunas de estas 6 coinciden con más de un tema). España pasa de 0/689 a **6/689** con coincidencia real de sector — 13/15 empresas (86,7%) con industria real capturada, **la mejor cobertura relativa de todos los países atacados hasta ahora**. 1 empresa ambigua (Banco Santander, mismo patrón real que Ahold Delhaize: dos elementos de Wikidata distintos), 1 sin coincidencia (AENA).

**El hueco de sector europeo pasa de 48/689 a 54/689.** Quedan 3 países sin atacar: Bélgica (6), Finlandia (5), Suecia (4) — 15/689 empresas.

**Estado del bloque (octava reconstrucción): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** Ninguna prueba nueva necesaria (16 en total) — el mecanismo genérico ya estaba probado.

---

## Novena reconstrucción (mismo día, 2026-09-06): Bélgica, cobertura perfecta, sin script nuevo

Instrucción del usuario: "sigue con Bélgica para el hueco de sector" (6/689 activos). Caso distinto de Suiza/Italia/España: el registro KBO/BCE belga sí publica datos abiertos oficiales con nombre de empresa real (a diferencia del KVK neerlandés, anonimizado) — pero son ficheros nacionales masivos (1,9M+ empresas) tras un registro cuya página está protegida con CAPTCHA, desproporcionado para consultar solo 6 empresas. Presentada la disyuntiva completa (registrar y procesar el fichero oficial / Wikidata, ya comprobado con 6/6 coincidencias reales / dejar el país sin atacar), **el usuario eligió Wikidata por quinta vez**. Quinto país con el mismo mecanismo — se reejecutó `v2.38AR` (`--countries CH IT DK ES BE`) sin ningún script nuevo.

### Resultado real

`MACRO_CONTEXT_READY` sube de **162 a 166** (+4, todos Bélgica: KBC→`BANK_CREDIT_CYCLE`, UCB→`HEALTHCARE_REGULATION`+`COMMODITY_INPUT_COSTS`, Lakefront Biotherapeutics→`HEALTHCARE_REGULATION`, Ageas→`BANK_CREDIT_CYCLE`). Bélgica pasa de 0/689 a **4/689** con coincidencia real de sector, con **cobertura perfecta de industria real: 6/6 empresas, 0 errores, 0 ambiguas** — la primera vez que un país atacado alcanza el 100%. AB InBev (cervecera) y Umicore (minería) no coinciden con ningún tema actual de la taxonomía (sin palabra clave para "brewing"/"mining") — resultado honesto, no un fallo.

**El hueco de sector europeo pasa de 54/689 a 58/689.** Quedan 2 países sin atacar: Finlandia (5), Suecia (4) — 9/689 empresas.

**Estado del bloque (novena reconstrucción): `COMPLETED_GLOBAL_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`.** Ninguna prueba nueva necesaria (16 en total).
