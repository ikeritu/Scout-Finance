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

**v2.38AF — generalización a 7 países de golpe**: el método GLEIF aplicado en una sola ejecución a Suiza, Italia, Dinamarca, Austria, Bélgica, Finlandia y Suecia (107 activos) — **102/107 confirmados**, con 6 países al 100% (Suiza 29/29 con dos autoridades de registro reales distintas, Italia 22/22, Dinamarca 21/21, Austria 20/20, Bélgica 6/6, Suecia 4/4). **Finlandia (0/5) es una laguna real y confirmada de GLEIF** (comprobado en vivo que ni siquiera el ISIN real de Nokia tiene registro), no un fallo del método. Con esto, el registro de identidad queda confirmado para **10 de los 13 países** del universo europeo. Ninguna fase de este rango calcula scoring adicional, ranking, recomendaciones ni autoriza fase 9C.

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
- Extensión global: **9A cerrada; 9B en curso (v2.38C–AF cerradas, con una corrección real de identidad post-X: 40/40 activos GB identificados correctamente vía fuente Xetra, v2.38Y ampliando Companies House/iXBRL a esa escala real -- 29/40 perfiles confirmados, y SSE PLC comprobada específicamente y confirmada sin iXBRL disponible -- v2.38X reconstruido finalmente con 1 único candidato real y correctamente identificado: Kingfisher plc -- v2.38Z aplicando el mismo método a Irlanda: 17/17 identidades resueltas -- v2.38AA aplicándolo a España: 15/15 identidades resueltas -- v2.38AB generalizando a las 689 empresas europeas del alcance: 689/689 identidades reales confirmadas -- v2.38AC investigando el registro alemán: sin vía gratuita, actualizada y accesible sin scraping -- v2.38AD confirmando registro parcial en Francia: 18/53 perfiles reales, 12/53 ambiguos por duplicados genuinos del registro -- v2.38AE en Países Bajos, descubriendo GLEIF como localizador universal por ISIN: 36/44 perfiles y números KVK confirmados -- y v2.38AF generalizando GLEIF a 7 países de golpe: 102/107 confirmados, 6 países al 100%, registro de identidad ya cerrado para 10/13 países del universo europeo); 9C no autorizada**. Este rango (v2.38K–AF + corrección + reconstrucciones) vive en el branch `phase9b-global-enrichment-v2-38b` (subido a GitHub, **no fusionado a `main`**). Estado: `outputs/full_universe_source_acquisition/v2_38b_global_enrichment/PHASE9B_EXECUTION_STATUS_v2_38b.md`. El ranking de la app sigue limitado a 50 activos, es experimental y no está validado históricamente.

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
