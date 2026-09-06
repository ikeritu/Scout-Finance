<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## Estado actual del pipeline de datos / Current Data Pipeline State

**Fases v2.38K–X — scoring experimental US y fundamentales reales de Europa** (branch `phase9b-global-enrichment-v2-38b`, aún no fusionado a `main`). Sobre la matriz de candidatos US de v2.38J: scoring experimental (v2.38K), shortlist explicada (v2.38L) y contexto macro/geopolítico estático (v2.38M). Fundación de Europa: casa de cotización (v2.38N), precios sin ejecutar (v2.38O/P), enrutamiento de fundamentales (v2.38Q/R/S: 617/55/17), revisión manual de Irlanda (v2.38T) y gate de disposición (v2.38U). **v2.38V/W/X**: primer piloto real de identidad, Companies House e iXBRL para 3-4 empresas GB, incluida Softcat con 14/14 conceptos IFRS extraídos y verificados contablemente.

**⚠️ Corrección real encontrada el mismo día**: 2 de esas 4 identidades (`SCT`→"Softcat", `BMT`→"Braime") estaban mal atribuidas — el resolutor original confundía el mnemonic interno de Xetra con un ticker real de LSE, y coincidió por casualidad con el ticker real de otra empresa no relacionada. Corregido resolviendo directamente contra el fichero fuente oficial de Xetra ya local (sin red, sin colisión posible vía ISIN): **40/40 activos GB ahora identificados correctamente** (Diageo, BAE Systems, British American Tobacco, Rio Tinto, SSE, BP, Barclays, Vodafone, Tesco, GSK, Shell, Unilever y 28 más) — un salto enorme frente al 4/40 anterior. Ningún commit se reescribe; la corrección queda documentada con transparencia total, con avisos añadidos en V/W/X.

**v2.38Y — Companies House + iXBRL ampliados a las 40 empresas**: perfiles de Companies House confirmados **29/40** (fail-closed; los 11 restantes son nombres Xetra abreviados o empresas no constituidas en UK, nunca forzados por adivinanza). Dos bugs reales de limpieza de nombres encontrados y corregidos en el proceso (un sufijo de denominación con espacio sin cubrir; el nombre legal real de BP registrado como "BP P.L.C." con puntos, que rompía el emparejamiento del sufijo). De las 29, **Kingfisher plc** tiene un paquete iXBRL real (13/14 conceptos IFRS extraídos, verificados con las cuatro identidades contables exactas) — segunda empresa real confirmada tras Softcat.

**SSE PLC comprobada específicamente**: ya estaba entre las 40 comprobadas en v2.38Y — perfil de Companies House confirmado (nº SC117119, activa), pero su filing de cuentas más reciente es **solo PDF, sin iXBRL disponible** (igual que Rio Tinto/Rentokil). Confirma con evidencia real que la fila "Softcat" mal atribuida a ese activo nunca podrá convertirse en datos reales de SSE. **Matriz v2.38X reconstruida de nuevo**: esa fila queda excluida explícitamente (registrada, no silenciada) — la matriz final queda con **1 único candidato, real y correctamente identificado: Kingfisher plc** (9/9 ratios, `CANDIDATE_MATRIX_PARTIAL_PRICE`).

**v2.38Z — Irlanda**: mismo método Xetra/ISIN aplicado a los 17 activos de Euronext Dublin — **17/17 identidades resueltas** (Ryanair, Medtronic, Accenture, ICON, Linde, Aon, Johnson Controls y 10 más). La CRO irlandesa no tiene API REST documentado públicamente, pero sí un Open Data Portal oficial (CC BY 4.0, sin credencial) — **8/17 perfiles de registro confirmados**, y una comprobación en vivo confirmó que el 100% de las cuentas depositadas en Irlanda son PDF: **ninguna empresa irlandesa tiene fundamentales reales extraíbles por esta vía**, un límite más definitivo que en GB.

**v2.38AA — España**: mismo método aplicado a los 15 activos de Bolsa de Madrid — **15/15 identidades resueltas** (Iberdrola, Inditex, Telefónica, Santander, BBVA, Repsol, CaixaBank y 8 más). Tres vías oficiales de registro/financials investigadas con evidencia real: el Open Data del Colegio de Registradores está bloqueado por un WAF (confirmado, no se intenta ningún rodeo); el API real de BORME solo publica boletines cronológicos, no un buscador de empresas; el visualizador XBRL de la CNMV (la vía más prometedora, mandato ESEF desde 2020) es solo un formulario web sin API documentado, automatizarlo sería scraping. **Ninguna vía oficial española es accesible sin scraping** — a diferencia de GB e Irlanda.

**v2.38AB — generalización a las 689 empresas europeas**: la matriz completa de v2.38N reveló que el mismo problema de identidad afecta a las 689 empresas del alcance europeo, no solo a las 72 ya tratadas — las otras 617 nunca habían sido identificadas porque estaban enrutadas solo al piloto de pago EODHD. Aplicado el mismo método sin filtro de país: **689/689 resueltas, 0 ambiguas** (Alemania 413, Francia 53, Países Bajos 44, Suiza 29, Italia 22, Dinamarca 21, Austria 20, Bélgica 6, Finlandia 5, Suecia 4, además de las 72 ya conocidas) — verificado sin ninguna discrepancia contra los resultados ya publicados.

**v2.38AC — Alemania (413 activos, ya identificados)**: investigación real de registro/financials, sin script nuevo de identidad. Ni el Handelsregister ni el Bundesanzeiger tienen API oficial; la alternativa cívica más prometedora (OffeneRegister.de, CC BY 4.0) fue comprobada en vivo y resultó técnicamente inviable hoy: su API devuelve `502 Bad Gateway` de forma consistente y sus datos masivos son de 2019. **Ninguna vía alemana es accesible, gratuita y actualizada hoy**.

**v2.38AD — Francia (53 activos)**: descubierta y corregida una limpieza de nombres compartida con otros países (marcadores de tipo de acción de Xetra, "INH."/"O.N."/"NOM."/"NAM.", antes sin eliminar). `recherche-entreprises.api.gouv.fr` (gobierno francés, sin cuenta) permitió confirmar **18/53 perfiles reales**; **12/53 quedan honestamente ambiguos porque el registro francés tiene varias empresas activas con el nombre exacto idéntico** (Hermès, LVMH, Renault, Michelin y 8 más), comprobado en vivo, nunca forzado por adivinanza. El endpoint de cuentas anuales de Francia está restringido a administraciones públicas — fundamentales confirmados sin acceso.

**v2.38AE — Países Bajos (44 activos) y un descubrimiento reutilizable**: ninguna vía holandesa de búsqueda por nombre es gratuita y accesible (API oficial de pago, alternativa gratuita bloqueada por Cloudflare, dataset abierto anonimizado). En su lugar, **GLEIF** (registro internacional de identificadores LEI, gratis, sin cuenta, CC0) resuelve un ISIN directamente al número de registro nacional — para Países Bajos, el número KVK real, comprobado en vivo (ASML → KVK 17085815, Heineken → KVK 33011433) — **eliminando la ambigüedad de nombre que afectó a Francia y GB/Irlanda**, potencialmente reutilizable para cualquier país. **36/44 perfiles y números KVK confirmados.** El dataset gratuito de cuentas anuales estructuradas (XBRL real) existe pero solo cubre empresas pequeñas/medianas — comprobado en una muestra de 8 (límite real de 1 petición/minuto): **0/8 tienen cuentas ahí**, mismo patrón que GB/Irlanda para grandes cotizadas.

**v2.38AF — generalización a 7 países de golpe**: el método GLEIF aplicado en una sola ejecución a Suiza, Italia, Dinamarca, Austria, Bélgica, Finlandia y Suecia (107 activos) — **102/107 confirmados**, con 6 países al 100% (Suiza 29/29 con dos autoridades de registro reales distintas, Italia 22/22, Dinamarca 21/21, Austria 20/20, Bélgica 6/6, Suecia 4/4). **Finlandia (0/5) es una laguna real y confirmada de GLEIF** (comprobado en vivo que ni siquiera el ISIN real de Nokia tiene registro), no un fallo del método. Con esto, el registro de identidad queda confirmado para **10 de los 13 países** del universo europeo.

**v2.38AG — Suiza: fundamentales, hallazgo estructural**: a diferencia de todos los países anteriores, **la ley suiza no exige en general depositar cuentas anuales en ningún registro público** — solo bancos, financieras y cotizadas divulgan cuentas, vía SIX Exchange Regulation en PDF, sin dataset estructurado. Suiza tampoco tiene mandato ESEF al no ser miembro de la UE. Zefix (registro central suizo) tiene API gratuita real pero exige credencial por correo, e igualmente no publica cifras financieras. **Conclusión: sin vía oficial para fundamentales suizos, por causa legal estructural, no por falta de herramienta técnica.**

**v2.38AH — Italia: fundamentales, dato gratuito sin API**: Italia tiene uno de los mandatos iXBRL más antiguos de Europa, y **el bilancio XBRL es genuinamente gratuito de descargar** desde `registroimprese.it` — pero **solo mediante navegación web interactiva, sin ningún API documentado**. Automatizarlo sería scraping. El API real de InfoCamere existe pero exige identidad digital italiana y pago por consulta. **Conclusión: dato correcto y gratuito, pero sin vía de acceso automatizado sin scraping** — un hallazgo distinto a Alemania o Suiza, más parecido al caso de la CNMV española.

**v2.38AI — Austria: fundamentales reales multi-año, excepción comercial aprobada**: sin API oficial gratuito del Firmenbuch. Con aprobación explícita del usuario, se usó **firmenakte.at** (agregador comercial, no oficial, nivel gratuito real de 100 llamadas/mes) — consultado directamente por el número de Firmenbuch que GLEIF ya dio en v2.38AF, sin ninguna ambigüedad de nombre. Un bug real (bloqueo Cloudflare por el `User-Agent` por defecto de Python) se encontró y corrigió en vivo. **Resultado: 20/20 empresas, 902 registros, 564 valores reales, hasta 5 años por empresa** — el resultado más rico en fundamentales de todo el proyecto. La identidad contable cuadra exactamente para algunas empresas pero no para bancos/aseguradoras (esquemas de balance distintos); **advertencia clave: son cifras de la entidad individual, no del grupo consolidado** (confirmado con OMV: 289M€ de ingresos pero 1.623M€ de beneficio neto).

**v2.38X reconstruido por tercera vez — 21 candidatos con Austria**: generalizado el cálculo de ratios para soportar el vocabulario alemán de Austria junto al IFRS de GB/Irlanda, mediante un sistema de alias canónicos. Caso especial verificado: el balance austriaco reparte "pasivo" en dos partidas (`verbindlichkeiten` + `rueckstellungen`) que ahora se suman, confirmado exacto contra PORR AG. **21 candidatos totales** — 1 completo (Kingfisher), 17 parciales, y **2 bancos sin ningún ratio calculable** (esquema regulado sin partida de ingresos industrial). **Confirmado con ratios reales**: OMV, VERBUND, SBO y STRABAG muestran márgenes netos superiores al 100% — coherente para la entidad individual (holding), nunca comparable al grupo consolidado.

**v2.38AJ — precios de Europa, hallazgo negativo confirmado**: cinco vías reales investigadas (Stooq, ahora protegido por un reto real de proof-of-work en JavaScript; Alpha Vantage, 25 peticiones/día, impracticable; LSE oficial, solo 15 min de retraso gratis; EODData, histórico profundo de pago; Twelve Data/Cboe Europe reconfirmados). **Se confirma que no existe hoy ninguna vía gratuita y accionable para precios reales del universo europeo** — refuerza la conclusión ya alcanzada en v2.33H. Tener identidad real para 689/689 activos no resuelve este problema independiente. Ninguna fase de este rango calcula scoring adicional, ranking, recomendaciones ni autoriza fase 9C.

**Fase v2.38J — matriz US de candidatos** (`COMPLETED_US_CANDIDATE_FEATURE_MATRIX_NOT_SCORING`). La capa une SEC fundamentals y price features US locales en una matriz preparada para scoring explicable futuro. No genera recomendaciones, no predice rentabilidad y no constituye asesoramiento financiero.

**Fase v2.38D — fundación SEC para EEUU** (`COMPLETED_US_SEC_FOUNDATION_DRY_RUN`). Añade contrato, esquema, overlay y runner para resolver CIK/submissions/companyfacts sobre 9.200 filas US / 5.011 elegibles. El acceso SEC real queda bloqueado por defecto y exige `--execute` más `SCOUT_FINANCE_SEC_USER_AGENT`; no hay scoring, ranking ni recomendaciones.

**Fase 9B-US/EU — cobertura prioritaria** (`COMPLETED_PARTIAL_COVERAGE`, v2.38C). Scout Finance queda alineado con el roadmap maestro: el objetivo es rastrear las 43.089 empresas, no optimizar solo Japón. La nueva capa offline censó 5.011 elegibles de EEUU y 10.483 elegibles europeas; EEUU queda encaminado hacia SEC/CIK/XBRL y precios ajustados con proveedor por validar, y Europa queda bloqueada principalmente por la resolución de Cboe Europe a home exchange. No se calculan scoring, ranking ni recomendaciones.

**Fase 9B — piloto controlado validado, enriquecimiento global aún incompleto** (`CONTROLLED_PILOT_VALIDATED_NOT_GLOBAL_PROMOTION`, v2.38B). El manifiesto conserva 43.089 filas: 763 listas para lote controlado (67 JPX verificadas + 696 TWSE), 3.634 JPX requieren resolución exacta y 5.011 estadounidenses requieren cuenta/licencia/piloto. El piloto nuevo valida 25 JPX y 25 TWSE (16.200 registros de precios); no se ha calculado scoring global.

**Fase 9A (auditoría global) — cerrada** (`COMPLETED_GLOBAL_CENSUS_READY_FOR_SOURCE_PLANNING`, v2.38A). El censo canónico conserva 43.089 filas y separa 21.165 elegibles, 10.432 excluidas, 9.710 revisables y 1.782 bloqueadas.

**Fase 8 (producto local) — cerrada** (`COMPLETED_LOCAL_PRODUCT`, v2.37). La entrada canónica sigue siendo `app_v2_37.py` y limitada a 50 activos; conserva de forma visible la decisión de fase 7 **`INSUFFICIENT_EVIDENCE`** y no autoriza broker, trading ni despliegue público.

- Interfaz vigente: `v2.37 — producto local de investigación`; la interfaz estable anterior `v2.32F` permanece intacta.
- Pipeline de precios vigente: `v2.33R — Fase 4 Final Gate` (sin cambios).
- Pipeline de fundamentales vigente: `v2.34J — Fase 5 Final Gate`.
- Pipeline de scoring vigente: `v2.35C — Fase 6 Final Gate`.
- Validación histórica: `v2.36 — Fase 7 Final Gate` (`INSUFFICIENT_EVIDENCE`; no demuestra ni refuta capacidad predictiva).
- **Scoring real:** 50/50 activos con entradas; 41 JPX en ranking principal (`HIGH`), 7 TWSE en comparabilidad parcial (`LOW`) y 2 en revisión (`P020`, `P178`). Shortlist experimental top 10, determinista y explicable.
- **Fundamentales: 50/50 activos** (42 JPX + 8 TWSE, los mismos de la fase 4) — **13.917 registros `FundamentalRecord` reales, 0 inválidos contra el esquema, 50/50 `PROMOTABLE`** (umbral ≥0,75, definido antes de calcular ningún score).
- **Limitación estructural declarada:** deuda desglosada, capex, flujo de caja libre y recompras no están disponibles en ninguna de las dos fuentes aprobadas (J-Quants `/fins/summary`, MOPS opendata) — bloqueadas con motivo, nunca aproximadas.
- **Cobertura de precios (heredada de fase 4, sin cambios): 50/21.165 candidatos elegibles (0,24 %)** — JPX (42 activos, vía J-Quants) + TWSE (8 activos, fuente oficial de Taiwán). Techo teórico si se resuelven las acciones pendientes: **44,45 %**. Excluido de forma permanente en el estado actual: **55,55 %** (Cboe Europe, ASX, BVC).
- **Mercados incluidos/condicionados:** JPX y TWSE (`PASS_FOR_NEXT_CONTROLLED_PILOT`, ampliación bloqueada por umbral de 500 activos, pendiente de autorización); EE. UU. — NASDAQ/NYSE/NYSE American/Cboe BZX (`BLOCKED_USER_ACTION_REQUIRED`, Twelve Data como única candidata, requiere que el usuario cree una cuenta).
- **Mercados excluidos:** Cboe Europe (`PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`, bloqueado indefinidamente), ASX (`NO_FREE_SOURCE_FOUND`), BVC (cerrado por decisión del usuario).
- **SGX y Xetra:** identidad reparada (SGX 100 %, Xetra 88,2 %) vía OpenFIGI; sin fuente de precios evaluada todavía.
- **Fuentes descartadas como mundiales:** EODHD (`COMPLETED_NO_PROMOTION`), Twelve Data en su versión global (solo cubre EE. UU./forex/cripto de forma gratuita).
- Historial completo, cierre por cierre (v2.33D1 a v2.38X), en `CHANGELOG.md`.
- Extensión global: **9A cerrada; 9B en curso (v2.38C–AJ cerradas, con una corrección real de identidad post-X: 40/40 activos GB identificados correctamente vía fuente Xetra, v2.38Y ampliando Companies House/iXBRL a esa escala real -- 29/40 perfiles confirmados, y SSE PLC comprobada específicamente y confirmada sin iXBRL disponible -- v2.38X reconstruido finalmente con 1 único candidato real y correctamente identificado: Kingfisher plc -- v2.38Z aplicando el mismo método a Irlanda: 17/17 identidades resueltas -- v2.38AA aplicándolo a España: 15/15 identidades resueltas -- v2.38AB generalizando a las 689 empresas europeas del alcance: 689/689 identidades reales confirmadas -- v2.38AC investigando el registro alemán: sin vía gratuita, actualizada y accesible sin scraping -- v2.38AD confirmando registro parcial en Francia: 18/53 perfiles reales, 12/53 ambiguos por duplicados genuinos del registro -- v2.38AE en Países Bajos, descubriendo GLEIF como localizador universal por ISIN: 36/44 perfiles y números KVK confirmados -- v2.38AF generalizando GLEIF a 7 países de golpe: 102/107 confirmados, 6 países al 100%, registro de identidad ya cerrado para 10/13 países del universo europeo -- v2.38AG en Suiza, hallazgo estructural: sin vía oficial de fundamentales porque la ley suiza no exige depósito público de cuentas, no por falta de herramienta técnica -- v2.38AH en Italia, dato gratuito pero solo accesible vía interfaz web, sin API: automatizarlo sería scraping -- v2.38AI en Austria, fundamentales reales multi-año vía una excepción comercial aprobada por el usuario: 20/20 empresas, hasta 5 años cada una -- v2.38X reconstruido por tercera vez con esas 20 empresas: 21 candidatos, generalización de ratios a vocabulario alemán, advertencia de entidad individual confirmada con márgenes reales >100% -- v2.38AJ confirmando, con evidencia real de 5 fuentes nuevas, que sigue sin existir ninguna vía gratuita para precios reales de Europa -- v2.38AK calculando, por primera vez para Europa, features de crecimiento interanual real (no solo ratios de un periodo): reutilizando la metodología ya validada en EE. UU. (v2.38G), aplicada a las 20 empresas austriacas (únicas con evidencia multi-año real hoy): 9/20 con las 4 features de crecimiento completas, 11/20 parciales, 0 insuficientes -- v2.38AL construyendo la matriz de cobertura global: una fila para cada una de las 43.089 empresas del censo, con identidad→fundamentales→crecimiento como una escalera de profundidad y el precio en columna separada (para no enterrar la señal real bajo el hueco estructural de precios europeos); resultado real: 41.845 sin ningún dato todavía, 690 solo identidad, 511 con crecimiento real (parcial o completo, casi todo EE. UU. más las 9 austriacas listas), verificación cruzada exacta 1.244 identidades resueltas = 555 EE. UU. + 689 Europa -- v2.38AM generalizando el módulo geopolítico estático (v2.38M) de las 50 empresas de la shortlist antigua a las 1.244 con identidad real, con 4 temas nuevos por país (UE, Eurozona, Brexit, franco suizo) verificados correctamente excluyentes entre sí; resultado real: 108/1.244 con coincidencia real de sector, las 108 todas de EE. UU., 0 de Europa -- hallazgo honesto de que los nombres legales europeos no contienen palabras clave en inglés -- y v2.38AN/AO atacando ese hueco: bug real corregido en Companies House (v2.38Y consultaba el endpoint equivocado, nunca devolvía SIC), 29/29 GB con código SIC real verificado; 18/18 Francia con código NAF/NACE real verificado vía la misma API ya validada en v2.38AD; v2.38AM reconstruido sube a 115/1.244 (+7, todos en Europa) -- hallazgo honesto de que 23/47 de las nuevas empresas clasificadas son en realidad su holding/sede social registrada, no la operación real, mismo patrón ya visto en Austria -- v2.38AP investigando Alemania (413 activos, el país más grande): hallazgo negativo estructural distinto de GB/Francia -- el código WZ alemán no se publica por empresa a través de ningún canal gubernamental (confirmado con Destatis), a diferencia de Companies House/SIRENE donde el dato SÍ vive en el registro público; sin script nuevo -- y v2.38AQ atacando Países Bajos vía Wikidata (excepción de política elegida explícitamente por el usuario tras confirmar que el KVK real exige pago): 32/44 empresas con industria real, hallazgo real de Ahold Delhaize con dos elementos de Wikidata compartiendo el mismo ISIN (pre/post fusión 2016) dejado correctamente ambiguo; v2.38AM reconstruido por tercera vez sube a 129/1.244 (+14, todos NL) -- el hueco de sector europeo pasa de 7/689 a 21/689 -- y v2.38AR generalizando ese mismo mecanismo a Suiza tras probar en vivo un cliente SOAP real contra el registro oficial suizo UID (confirmado con 5 llamadas reales que NOGACode nunca aparece en el nivel público, mismo patrón que Alemania): 15/29 empresas suizas con industria real vía Wikidata (elegido de nuevo por el usuario); v2.38AM reconstruido por cuarta vez sube a 135/1.244 (+6, todos CH) -- el hueco de sector europeo pasa de 21/689 a 27/689 -- y con Italia (re-ejecución de v2.38AR, sin script nuevo, tras confirmar que el portal de datos abiertos oficial de InfoCamere está detrás de reCAPTCHA y su alternativa es de pago): 16/22 empresas italianas con industria real vía Wikidata (elegido por tercera vez); v2.38AM reconstruido por quinta vez sube a 147/1.244 (+12, todos IT) -- el hueco de sector europeo pasa de 27/689 a 39/689, con 7 países aún sin atacar (88 empresas)); 9C no autorizada**. Este rango (v2.38K–AR + corrección + reconstrucciones) vive en el branch `phase9b-global-enrichment-v2-38b` (subido a GitHub, **no fusionado a `main`**). Estado: `outputs/full_universe_source_acquisition/v2_38b_global_enrichment/PHASE9B_EXECUTION_STATUS_v2_38b.md`. El ranking de la app sigue limitado a 50 activos, es experimental y no está validado históricamente.

<!-- SCOUT_FINANCE_V2_33D1_STATE_END -->

<!-- SCOUT_FINANCE_V2_14I_STATE_START -->
## Estado actual del proyecto / Current Project State

Estado documental añadido en **v2.14I — Documentation and Canonical Dataset Path**.

- Línea app/MVP: `v1.1C — MVP Final Freeze`
- Línea pipeline de datos: `v2.14H — Audit Triage / Stability Gate`
- Último cierre de proveedor validado: `v2.14G — Deutsche Boerse Xetra Closure Report`
- Commit de cierre Xetra: `5a4e3f0`
- Commit de triage auditoría: `7f1cb64`
- Dataset expandido canónico vigente: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Filas actuales: `38,287`
- Fuente hacia 50k: `76.6%`
- Filas pendientes hacia 50k: `11,713`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

Nota: la documentación distingue explícitamente entre la app Streamlit congelada en v1.1C y el pipeline de expansión de universo en v2.x.


<!-- SCOUT_FINANCE_V2_14I_STATE_END -->

# Scout Finance — Private Research MVP

## Qué es

Scout Finance es una herramienta privada para priorizar empresas investigables mediante:

- pipeline cuantitativo;
- análisis asistido por IA;
- outputs estructurados;
- comparativa visual;
- revisión manual documentada.

No es una app de trading, no se conecta a brokers y no da recomendaciones de compra/venta.

## Estado actual

Base congelada: `v1.1C — MVP Final Freeze` (ver `docs/v1/V1_1C_MVP_FINAL_FREEZE.md` y `CHANGELOG.md`).

Sobre esa base, la interfaz Streamlit (`app.py`) está simplificada para pruebas rápidas:

- sin pantalla de login;
- sin FAQ;
- 4 pestañas esenciales en vez de 7 (ver más abajo).

El código de login, FAQ y las pestañas avanzadas (Candidatos Stage 3, Histórico/técnico, Ajustes) sigue en `app.py` pero no se llama desde `main()` — se puede reactivar fácilmente si se necesita.

## Flujo recomendado (interfaz Streamlit)

1. Abrir la pestaña Dashboard y ejecutar el pipeline cuantitativo.
2. Revisar Ranking.
3. Abrir Análisis empresa y consultar/generar outputs Fase 2.
4. Comparar empresas.

Para la revisión manual documentada (watchlist / reject / needs_more_data) se usa un flujo aparte por línea de comandos — ver `docs/QUICKSTART.md`.

## Ejecutar app

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Outputs Fase 2

Los análisis estructurados se guardan en:

```text
outputs/analyses
```

Archivos esperados:

```text
TICKER_FECHA.md
TICKER_FECHA.json
TICKER_FECHA_scorecard.png
TICKER_FECHA_scenarios.png
TICKER_FECHA_executive_card.html
```

## Pestañas activas

### 🏠 Dashboard

Vista ejecutiva del estado general, controles de ejecución del pipeline y resumen del último run.

### 🔎 Ranking

Tabla priorizada de empresas.

### 📄 Análisis empresa

Ficha individual, análisis legacy y outputs Fase 2.

### 🧮 Comparar empresas

Comparativa visual basada en JSON ya generados.

## Revisión manual (CLI)

Workflow de decisión humana documentada (watchlist / reject / needs_more_data) y export del pack final de revisión. Detalle completo en `docs/QUICKSTART.md` y `docs/USER_GUIDE.md`.

## Aviso

Scout Finance es una herramienta de investigación. No ofrece asesoramiento financiero.
# Scout-Finance
