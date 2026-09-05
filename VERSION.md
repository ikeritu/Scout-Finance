<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## Estado real actual del pipeline de datos / Current Data Pipeline Real State

**Fases v2.38K–U — scoring experimental US y fundación de fundamentales de Europa** (branch `phase9b-global-enrichment-v2-38b`, subido a GitHub, **no fusionado a `main`**, que sigue en `v2.38A`). US: scoring experimental determinista sobre la matriz de v2.38J (v2.38K, `COMPLETED_US_EXPERIMENTAL_SCORING_NOT_RECOMMENDATIONS`, 350/555 puntuados, rango 7,5–87,33), shortlist explicada de 50 empresas (v2.38L, `COMPLETED_US_EXPLAINED_SHORTLIST_NOT_RECOMMENDATIONS`, 20 alta prioridad, 30 media), contexto macro/geopolítico estático (v2.38M, `COMPLETED_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS`, 12 completos/38 parciales de 50). Europa: resolución de casa de cotización (v2.38N, `COMPLETED_EUROPE_HOME_EXCHANGE_RESOLUTION_NOT_ENRICHMENT`, 689/22.578 resueltas, 21.066 Cboe Europe bloqueadas como venue secundario), plan de adquisición de precios sin ejecutar (v2.38O, `READY_FOR_COLLECTION`, 0/689 recolectados), gate de price features fail-closed por falta de historial local (v2.38P, `PRICE_FEATURES_BLOCKED_NO_LOCAL_EUROPE_PRICE_HISTORY`), enrutamiento de fundamentales (v2.38Q, `COMPLETED_EUROPE_FUNDAMENTALS_ROUTE_FOUNDATION_NOT_COLLECTION`: 617 piloto de proveedor / 55 filings oficiales / 17 revisión manual), piloto de proveedor listo sin ejecutar (v2.38R, `COMPLETED_EUROPE_FUNDAMENTALS_PROVIDER_PILOT_READY_NOT_EXECUTED`, 13 lotes), revisión de filings oficiales (v2.38S, `COMPLETED_EUROPE_OFFICIAL_FILINGS_REVIEW_READY_NOT_EXECUTED`, 55 activos, jurisdicciones ES/GB), el paquete de revisión manual de los 17 activos de Euronext Dublin (v2.38T, `COMPLETED_EUROPE_MANUAL_REVIEW_PACK_READY_NOT_EXECUTED`) — **hallazgo real**: los 17 comparten el mismo `company_name` heredado (`"UKI0"`, marcador de posición del feed original de Deutsche Börse Xetra usado desde v2.38C/N, no un nombre verificado); 51 acciones de checklist generadas (3 por activo), ninguna identidad ni ruta inventada — y el gate de disposición para ejecución (v2.38U, `EUROPE_FUNDAMENTALS_EXECUTION_NOT_READY_PENDING_PREREQUISITES`): **0 de 3 rutas listas hoy** — piloto de proveedor bloqueado por script de ejecución inexistente y `EODHD_API_KEY` ausente (comprobación estrictamente booleana, ningún valor de credencial se lee ni se expone); filings oficiales y revisión manual bloqueadas por 0/55 y 0/17 identificadores/identidades resueltos.

**v2.38V — primer piloto real de recolección de fundamentales de Europa** (`COMPLETED_EUROPE_GB_IDENTITY_RESOLUTION_PARTIAL`): investigación previa confirma que EODHD Fundamentals exige un plan de pago (mín. €59,99/mes, plan gratuito limitado a 2 consultas de fundamentales/día) — choca con la postura ya establecida del usuario de no usar fuentes de pago; no se construye ningún runner para esa ruta. En su lugar, resolución real de identidad para los 40 activos GB vía OpenFIGI `/v3/mapping` (gratis, sin cuenta, mismo patrón de v2.33C/H/P): **4/40 resueltos** (Rio Tinto, Rentokil Initial, Softcat, Braime), fail-closed. Dos hallazgos reales aplicados tras sondeos en vivo: `exchCode="LN"` es el parámetro correcto (no `micCode`, que devolvió una empresa francesa no relacionada en un sondeo); varios tickers llevan un sufijo numérico espurio heredado del mismo feed roto de Xetra, corregible solo como reintento explícitamente etiquetado (nunca sustituido en silencio). Localizador de perfil en UK Companies House (API oficial gratuita, confirmada contra la documentación oficial) construido y probado offline (9 casos de prueba entre ambos scripts), bloqueado por defecto. El usuario creó su propia cuenta gratuita en Companies House y guardó `SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY` (nunca vista por este proyecto); ejecutado con esa credencial el 2026-09-05: **3/4 perfiles reales confirmados** — RIO TINTO PLC (nº 00719885, activa, 1962-03-30), SOFTCAT PLC (nº 02174990, activa, 1987-10-07), RENTOKIL INITIAL PLC (nº 05393279, activa, 2005-03-15); Braime queda sin resolver (`no_exact_normalized_name_match`, desajuste honesto entre la descripción de clase de acción de OpenFIGI y la razón social registrada, fail-closed correcto). Escaneo de secretos sobre los ficheros de salida reales: sin coincidencias.

**v2.38W — primeros fundamentales reales de Europa (iXBRL)**: descarga real del documento de cuentas más reciente para las 3 empresas de v2.38V. Rio Tinto y Rentokil solo tienen PDF en Companies House (bloqueadas, `accounts_format_not_parseable_pdf_only`, sin OCR); Softcat tiene un paquete ESEF/iXBRL real (identificado por LEI `213800N42YZLR9GLVC42`, taxonomía de extensión propia). Extractor específico de 14 conceptos IFRS estándar (`ifrs-full:*`), no un motor XBRL genérico. **Hallazgo y corrección real durante la construcción**: un primer diseño elegía un único "contexto ganador" global por fecha entre todos los conceptos de tipo stock, pero el patrimonio tiene un desglose por componente (`xbrldi:explicitMember` sobre `ifrs-full:ComponentsOfEquityAxis`) con contextos que comparten la misma fecha del contexto total — el ganador global podía terminar siendo un componente parcial, dejando `Assets`/`Liabilities` marcados "no etiquetados" pese a estar presentes. Corregido exigiendo el contexto sin `<xbrli:scenario>`; prueba de regresión dedicada con fixture sintético añadida antes de aceptar ningún resultado real. **Resultado real, 14/14 conceptos extraídos para Softcat (ejercicio a 2025-07-31)**: Revenue £1.458.411.000, beneficio operativo £172.900.000, beneficio antes de impuestos £178.202.000, beneficio neto £133.008.000, activos £1.191.927.000 (corriente £1.121.714.000 + no corriente £70.213.000), pasivos £853.145.000 (corriente £808.950.000 + no corriente £44.195.000), patrimonio £338.782.000, efectivo £182.282.000. **Cuatro ecuaciones contables verifican de forma exacta** contra estos valores reales (activo=pasivo+patrimonio; activo corriente+no corriente=activo total; pasivo corriente+no corriente=pasivo total; activos netos=patrimonio) — la evidencia más fuerte de que la extracción es correcta, no solo de que no lanzó ningún error. 7 pruebas offline entre ambos scripts (fetch + normalizador), una detectó y motivó la corrección de un bug real adicional (`relative_to(ROOT)` fallaba con una caché cruda fuera del repo). Valores reales y documento crudo fuera de git; solo el informe de cobertura agregado se publica. Ninguna fase de este rango calcula scoring/ranking adicional, genera recomendaciones ni autoriza fase 9C.

**Fase v2.38J — matriz US de candidatos** (`COMPLETED_US_CANDIDATE_FEATURE_MATRIX_NOT_SCORING`). Combina identidad SEC, features fundamentales v2.38G y price features v2.38H/38I en una matriz US trazable para scoring futuro. No usa red, no publica raw cache y no calcula scoring, ranking ni recomendaciones.

**Fase v2.38D — fundación SEC para EEUU** (`COMPLETED_US_SEC_FOUNDATION_DRY_RUN`). Se crea la ruta técnica para identidad CIK, submissions y companyfacts de la SEC sobre las 9.200 filas US / 5.011 elegibles. Sin ejecución real SEC ni cache local, los 5.011 elegibles quedan fail-closed como `US_SEC_SOURCE_UNAVAILABLE`; el runner real exige `--execute` y `SCOUT_FINANCE_SEC_USER_AGENT`. Sin scoring, ranking, recomendaciones ni fase 9C.

**Fase 9B-US/EU — cobertura prioritaria añadida** (`COMPLETED_PARTIAL_COVERAGE`, v2.38C). El proyecto queda reorientado al roadmap maestro: rastreo global de 43.089 empresas, con prioridad práctica en EEUU y Europa. Censo US/EU offline: 5.011 elegibles estadounidenses y 10.483 elegibles europeas. EEUU queda encaminado a SEC CIK/XBRL + proveedor de precios ajustados; Europa queda bloqueada principalmente por Cboe Europe como venue secundario hasta resolver home exchange. Sin scoring, ranking, recomendaciones ni fase 9C.

**Fase 9B — piloto controlado validado, sin promoción global** (`CONTROLLED_PILOT_VALIDATED_NOT_GLOBAL_PROMOTION`, v2.38B). El universo canónico contiene 43.089 filas; 763 tienen símbolo y ruta listos para lote controlado, 3.634 JPX requieren catálogo y 5.011 estadounidenses requieren acción externa. El piloto nuevo valida 25 JPX y 25 TWSE (16.200 registros); no existe scoring ni recomendación global.

**Fase 9A — cerrada como censo global auditable** (`COMPLETED_GLOBAL_CENSUS_READY_FOR_SOURCE_PLANNING`, v2.38A).

**Fase 8 — cerrada como producto local** (`COMPLETED_LOCAL_PRODUCT`, v2.37). La entrada canónica `app_v2_37.py` conserva la decisión de fase 7 `INSUFFICIENT_EVIDENCE` y permanece limitada a 50 activos locales, sin broker ni trading.

- App/MVP: `v1.1C — MVP Final Freeze` (sin cambios).
- Interfaz vigente: `v2.37 — producto local de investigación`; `v2.32F` permanece como interfaz estable anterior.
- Pipeline de precios vigente: `v2.33R — Fase 4 Final Gate` (sin cambios), sobre la base de `v2.33D1`–`v2.33Q`.
- Pipeline de fundamentales vigente: `v2.34J — Fase 5 Final Gate`, sobre la base de `v2.34A`–`v2.34I`.
- Pipeline de scoring vigente: `v2.35C — Fase 6 Final Gate`, sobre la base de `v2.35A`–`v2.35B`.
- Gate de evidencia histórica: `v2.36 — Fase 7 Final Gate`; capacidad predictiva no demostrada.
- **Ranking experimental:** 41 activos JPX comparables, top 10 publicable, doble ejecución byte-idéntica; 7 TWSE no entran en el ranking principal y `P020`/`P178` requieren revisión.
- **Fundamentales: 50/50 activos** (42 JPX + 8 TWSE, mismo universo de la fase 4). Fuentes: J-Quants `/v2/fins/summary` (v2.34B/D, `APPROVED_SCOPED`, ~2 años de historia, sin desglose de deuda) y TWSE MOPS opendata (v2.34B/D, `APPROVED_SCOPED`, estado financiero detallado pero un único periodo por empresa, sin histórico). **13.917 registros `FundamentalRecord` reales (v2.34F normalización + v2.34G derivadas), 0 inválidos contra el esquema (v2.34H), 50/50 activos `PROMOTABLE`** (umbral ≥0,75, definido antes de calcular ningún score).
- Limitación estructural declarada: deuda desglosada, capex, flujo de caja libre y recompras no disponibles en ninguna fuente aprobada (v2.34G) — bloqueadas con motivo, nunca aproximadas.
- **Cobertura de precios (heredada de fase 4, sin cambios): 50/21.165 candidatos elegibles (0,24 %)**. Techo teórico si se resuelven las acciones pendientes: **44,45 %**. Excluido de forma permanente en el estado actual: **55,55 %** (Cboe Europe, ASX, BVC).
- Fuentes descartadas como mundiales: EODHD (`COMPLETED_NO_PROMOTION`, v2.33D1), Twelve Data (v2.33E, solo EE. UU./forex/cripto).
- JPX (v2.33G/N): `PASS_FOR_NEXT_CONTROLLED_PILOT`, licencia confirmada compatible con uso privado; ampliación a 3.701 candidatos bloqueada, pendiente de autorización (>500 activos).
- TWSE (v2.33I/O): `PASS_FOR_NEXT_CONTROLLED_PILOT`, sustituye a EODHD para los 8 activos; sin ajuste por splits/dividendos (fuente de ajuste oficial identificada, algoritmo no implementado); ampliación a 696 candidatos bloqueada, pendiente de autorización.
- Cboe Europe (v2.33H): `PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`, bloqueado indefinidamente (usuario descarta pago).
- ASX (v2.33J): `NO_FREE_SOURCE_FOUND`, confirmado de primera mano.
- BVC (v2.33K): cerrado por decisión del usuario, bajo impacto (1 símbolo).
- SGX/Xetra (v2.33P): identidad reparada (SGX 100 %, Xetra 88,2 %) vía OpenFIGI; sin fuente de precios evaluada todavía.
- Arquitectura multifuente de precios (v2.33Q): esquema canónico `PriceRecord` + adaptadores J-Quants/TWSE, verificados contra 50 activos reales.
- EE. UU. (v2.33M): `BLOCKED_USER_ACTION_REQUIRED` — Twelve Data es la única candidata, requiere que el usuario cree la cuenta.
- Progreso histórico: **8/8 fases originales cerradas**; extensión global **9A cerrada / 9B en curso (v2.38C–W cerradas: scoring experimental US + shortlist + contexto macro, y primeros fundamentales reales de Europa -- 1 empresa (Softcat) con 14/14 conceptos IFRS extraídos y contablemente verificados, 2 bloqueadas por formato de documento) / 9C no autorizada**. Rango v2.38K–W no fusionado a `main`.
- Cierre: suite completa offline y checklist funcional con datos locales reales en Windows 11 superados el 2026-09-01.

<!-- SCOUT_FINANCE_V2_33D1_STATE_END -->

<!-- SCOUT_FINANCE_V2_14I_STATE_START -->
## Estado real actual / Current Real State

Estado real del repositorio tras auditoría y cierre Xetra.

- App/MVP: `v1.1C — MVP Final Freeze`
- Pipeline de datos: `v2.14H — Audit Triage / Stability Gate`
- Dataset canónico vigente: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Siguiente fase recomendada: `v2.14J — Post-Closure Integrity Test` o `v2.15A — Next Provider Route`, según prioridad operativa.


<!-- SCOUT_FINANCE_V2_14I_STATE_END -->

# Scout Finance — VERSION

## Versión actual

`v1.1C — MVP Final Freeze`

Detalle del freeze en `docs/v1/V1_1C_MVP_FINAL_FREEZE.md` y `releases/FREEZE_REPORT_v1.1C_mvp_final_freeze.md`.

## Cambios sobre el freeze (sin tag formal todavía)

Simplificación de la interfaz Streamlit (`app.py`) para pruebas locales rápidas:

- login y FAQ deshabilitados (código intacto, sin llamar desde `main()`);
- pestañas reducidas de 7 a 4: Dashboard, Ranking, Análisis empresa, Comparar empresas;
- pestañas Candidatos Stage 3, Histórico/técnico y Ajustes ocultas (no eliminadas);
- tema visual básico vía `.streamlit/config.toml`.

## Estado

Estable para uso local en modo demo/privado.

## Incluye

- Dashboard ejecutivo.
- Ranking.
- Ficha empresa con outputs Fase 2.
- Comparativa visual.
- Capa de revisión manual documentada (CLI) — `docs/QUICKSTART.md`.
- Freeze candidate v1.0 y freeze final v1.1C.

## Principio del proyecto

Scout Finance prioriza empresas para investigar. No recomienda comprar, vender ni mantener.
