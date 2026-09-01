<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## v2.38A — auditoría canónica del universo global (2026-09-01)

Cierra la fase 9A como **`COMPLETED_GLOBAL_CENSUS_READY_FOR_SOURCE_PLANNING`**. Resuelve por hash el censo canónico v2.33B2 y conserva 43.089/43.089 filas: 21.165 elegibles, 10.432 excluidas, 9.710 revisables y 1.782 bloqueadas. Añade contrato, esquema, artefacto detallado comprimido, desgloses, matriz de rutas/licencias para 15 mercados, manifiesto y QA offline determinista. No usa red ni credenciales, no descarga datos y no calcula scoring, ranking o recomendaciones. La fase 9B permanece sin autorizar.

## v2.37 — producto local de investigación (2026-09-01)

Cierra la fase 8 como **`COMPLETED_LOCAL_PRODUCT`** tras superar la suite offline y el recorrido funcional con datos reales locales en Windows 11. Añade una interfaz Streamlit nueva y aislada (`app_v2_37.py`) sobre el universo canónico de 50 activos. Separa 41 JPX en ranking experimental, 7 TWSE con comparabilidad parcial y P020/P178 en revisión requerida. Incorpora universo filtrable, fichas, comparador, watchlists privadas con escritura atómica, informes trazables y estados explícitos de disponibilidad. No usa red ni datos demo y mantiene visible `INSUFFICIENT_EVIDENCE`; el cierre de producto no valida capacidad predictiva.

## v2.36 — gate de evidencia y cierre de la fase 7 (2026-08-31)

Cierra la validación histórica como **`INSUFFICIENT_EVIDENCE`** sin observar rendimiento después de fallar el gate predefinido. JPX aporta 368–486 sesiones: insuficientes para formar factores de 12 meses y obtener dos ventanas OOS. TWSE tiene mayor profundidad, pero precios sin ajustar y fundamentales sin fecha de publicación verificable. Añade contrato congelado, primitives point-in-time, costes, benchmark, métricas deterministas y QA anti-look-ahead. La fase 8 no está autorizada.

## v2.35C — gate final y cierre de la fase 6 (2026-08-31)

Cierra scoring y selección con **`COMPLETED_SCOPED`**: 50/50 activos con precios y fundamentales, 41 JPX comparables en el ranking principal, 7 TWSE separados como `PARTIAL_COMPARABILITY` y 2 revisiones (`P020`, margen real 316,5%; `P178`, banco incompatible con el contrato industrial). Contrato congelado de 14 factores, pesos al 100%, periodos anuales preferidos, ausencias sin imputación, explicaciones deterministas y doble ejecución real byte-idéntica. Shortlist experimental top 10; no constituye recomendación. Fase 7 preparada pero no autorizada. Detalle en `outputs/full_universe_source_acquisition/v2_35c_phase6_final_gate/PHASE6_FINAL_GATE_v2_35c.md`.

## v2.35B — explicabilidad y QA real local (2026-08-31)

Añade explicaciones deterministas, conciliación de contribuciones, control de lenguaje, estados excluyentes y gate local de doble ejecución sobre los 50 activos. Resultado real: PASS, 41 ranked, 7 partial, 2 review, sin fase 7.

## v2.35A — contrato y motor de scoring (2026-08-31)

Congela antes de aceptar resultados un contrato de 14 factores en cinco pilares. El primer cálculo detecta y corrige dos defectos: los activos `LOW` dejan de competir con `HIGH`, y las financieras requieren contrato separado. Una revisión posterior impide mezclar periodos trimestrales y anuales. Ningún peso se optimiza según rentabilidad.

## v2.34J — gate final y cierre de la fase 5, Bloque J (2026-08-31)

Cierra la fase 5 (adquisición, normalización y validación de fundamentales reales) con la decisión **`COMPLETED_PROMOTABLE`**. Alcance: los mismos 50 activos ya validados en la fase 4 (42 JPX + 8 TWSE) — la fase 5 no amplía el universo de mercados ni de activos. **13.917 registros `FundamentalRecord` reales, 0 inválidos contra el esquema; 50/50 activos alcanzan el umbral `PROMOTABLE` (≥0,75) de calidad de datos**, definido antes de calcular ningún score. Deuda desglosada, capex, flujo de caja libre y recompras quedan estructuralmente bloqueados en ambas fuentes aprobadas (J-Quants `/fins/summary`, MOPS opendata), documentados con motivo, nunca aproximados. Una anomalía económica real (`P020`, margen neto 316,5%) queda marcada, no corregida. **Fase 6: no iniciada, no autorizada** — requiere decisión explícita nueva del usuario. Progreso global: 5/8 fases cerradas. Detalle en `outputs/full_universe_source_acquisition/v2_34j_phase5_final_gate/PHASE5_FINAL_GATE_v2_34j.md`.

## v2.34I — integración de QA offline y verificación cruzada, Bloque I (2026-08-31)

Un único punto de entrada (`tests/qa_fundamentals_phase5_full_suite_v2_34i.py`) ejecuta los 6 módulos offline construidos en los Bloques C-H (44 casos individuales), sin duplicar su lógica. Verifica la lista de checklist completa: compilación de todos los ficheros de fase 5, `pytest -q` completo del proyecto (mismos 3 fallos preexistentes, sin regresiones nuevas), `git diff --check` limpio, escaneo de secretos sin coincidencias, ningún fichero grande versionado, los 5 ficheros/directorios con valores reales correctamente ignorados. Detalle en `outputs/full_universe_source_acquisition/v2_34i_offline_qa_integration/OFFLINE_QA_INTEGRATION_v2_34i.md`.

## v2.34H — validación y score de calidad de datos, Bloque H (2026-08-31)

Valida los 13.917 registros reales (normalizados + derivados): ecuaciones contables con tolerancia del 2% (nunca igualdad exacta) — 16/16 pasadas donde comprobables (TWSE), `not_applicable` para JPX sin comprobación circular; 0 problemas temporales; 1 bandera de sanidad económica real investigada y marcada (`P020`, margen neto 316,5%). Score de calidad de datos en 7 dimensiones (identidad/procedencia/completitud/continuidad/coherencia/comparabilidad/frescura, nunca un score de inversión), con `coherence=null` (no 0) cuando ninguna ecuación es comprobable. Umbrales de promoción definidos antes de calcular ningún score: **50/50 activos `PROMOTABLE`**. Detalle en `outputs/full_universe_source_acquisition/v2_34h_validation/FUNDAMENTAL_VALIDATION_v2_34h.md`.

## v2.34G — métricas derivadas, Bloque G (2026-08-31)

Calcula márgenes, ROA, ratio corriente y crecimiento interanual (3.602 registros derivados, 0 inválidos) solo donde los componentes son reales — `gross_margin`/`current_ratio` correctamente exclusivos de TWSE, `revenue_growth_yoy`/`net_income_growth_yoy` exclusivos de JPX. División por cero y denominador negativo manejados sin excepción; 7 casos reales de crecimiento con base negativa marcados, nunca presentados como un porcentaje ordinario. `gross_debt`/`net_debt`/`free_cash_flow` bloqueados de forma explícita (648 registros cada uno), nunca omitidos en silencio. Corrige un hallazgo real: el Bloque F no tenía regla de prioridad restated-vs-original para múltiples disclosures del mismo periodo; añadida y probada aquí. Detalle en `outputs/full_universe_source_acquisition/v2_34g_derived_metrics/DERIVED_METRICS_v2_34g.md`.

## v2.34F — normalización a FundamentalRecord, Bloque F (2026-08-31)

Dos normalizadores independientes (J-Quants, TWSE MOPS) convierten la adquisición real del Bloque E en 10.315 registros `FundamentalRecord`, 0 inválidos. Excluye por completo las divulgaciones `EarnForecastRevision`/`DividendForecastRevision` de J-Quants (guidance, no estados financieros). Un campo en blanco del proveedor nunca se convierte en cero (43,5% de JPX queda `not_reported_by_company`, por diseño). Escala de TWSE (miles→unidades TWD) confirmada, no asumida; ambigüedad trimestre discreto vs acumulado marcada explícitamente, no resuelta por conveniencia. Detalle en `outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/FUNDAMENTAL_NORMALIZATION_v2_34f.md`.

## v2.34E — adquisición controlada real, 50/50 activos, Bloque E (2026-08-31)

Piloto pequeño primero (5 JPX + 3 TWSE), con puerta de calidad, luego escalado a los 50 activos completos: **42/42 JPX y 8/8 TWSE, 0 fallos**, con evidencia real (389 divulgaciones JPX, ~2 años de historia). Descubre que las divulgaciones `EarnForecastRevision`/`DividendForecastRevision` de J-Quants no llevan cifras reales — hallazgo aplicado directamente en el Bloque F. Detalle en `outputs/full_universe_source_acquisition/v2_34e_controlled_acquisition/CONTROLLED_ACQUISITION_v2_34e.md`.

## v2.34D — adaptadores de adquisición de fundamentales, Bloque D (2026-08-31)

Dos adaptadores fail-closed e independientes (J-Quants `/fins/summary`, TWSE MOPS opendata) — bloqueados por defecto, reanudables, escritura atómica, taxonomía de errores cerrada. MOPS no tiene consulta por empresa: se descargan los 4 ficheros del mercado completo una vez y se extrae por código de empresa. Datos crudos fuera de git desde antes de crearse. 9/9 pruebas offline sin red ni credenciales reales. Detalle en `outputs/full_universe_source_acquisition/v2_34d_fundamentals_acquisition/FUNDAMENTALS_ACQUISITION_ARCHITECTURE_v2_34d.md`.

## v2.34C — esquema canónico FundamentalRecord, Bloque C (2026-08-31)

Contrato `FundamentalRecord` (JSON Schema draft 2020-12 + dataclass Python), formato long, con catálogo cerrado de 29 métricas iniciales y 10 motivos de ausencia. `value_status="estimated"` prohibido en código (regla 3.1), aunque se conserva en el enum para poder fallar explícitamente. 9/9 pruebas offline con ejemplos válidos y rechazados. Detalle en `outputs/full_universe_source_acquisition/v2_34c_fundamental_record_schema/FUNDAMENTAL_RECORD_SCHEMA_v2_34c.md`.

## v2.34B — evaluación de fuentes de fundamentales, Bloque B (2026-08-31)

Evalúa J-Quants `/fins/summary` (JPX) y MOPS opendata (TWSE): ambas `APPROVED_SCOPED`. J-Quants da historia real (~2 años) pero sin desglose de deuda (exclusivo del plan Premium de pago, descartado). MOPS da estado financiero detallado pero solo del periodo más reciente por empresa, sin histórico ni flujo de caja confirmado. Ninguna cuenta nueva creada. Detalle en `outputs/full_universe_source_acquisition/v2_34b_fundamental_source_evaluation/FUNDAMENTAL_SOURCE_EVALUATION_v2_34b.md`.

## v2.34A — auditoría inicial y universo canónico de fundamentales, Bloque A (2026-08-31)

Inicio de la fase 5. Manifiesto de 50 activos (42 JPX + 8 TWSE, los mismos ya validados en la fase 4), todos `identity_verified`, reutilizando evidencia ya confirmada sin re-derivarla. El trabajo previo de fundamentales basado en yfinance queda explícitamente descartado, no reutilizado. Detalle en `outputs/full_universe_source_acquisition/v2_34a_fundamental_universe_audit/FUNDAMENTAL_UNIVERSE_AUDIT_v2_34a.md`.

## v2.33R — gate final y cierre de la fase 4, Bloque H (2026-08-31)

Cierra la fase 4 (precios históricos y arquitectura multifuente) con la decisión **`COMPLETED_SCOPED_OPERATIONAL_UNIVERSE`**. Matriz final por mercado (JPX, TWSE, NASDAQ, NYSE, NYSE American, Cboe BZX, Cboe Europe, ASX, BVC, Xetra, SGX) con fuente, estado, profundidad, retraso, ajustado, licencia, cobertura y decisión, todas trazables a un cierre publicado — cero mercados "pendientes" sin motivo. **Cobertura real calculada: 50/21.165 candidatos elegibles (0,24 %)**, techo teórico del 44,45 % si se resuelven las acciones pendientes, 55,55 % excluido de forma permanente en el estado actual. Sesgo geográfico (concentración EE. UU./Japón/Taiwán, exclusión de Europa y Australia) declarado explícitamente, no oculto. Cinco puntos quedan pendientes de intervención del usuario, listados de forma independiente entre sí. **Fase 5: no iniciada, no autorizada** — requiere decisión explícita nueva tras leer el informe. Progreso global: 4/8 fases cerradas. Detalle en `outputs/full_universe_source_acquisition/v2_33r_phase4_final_gate/PHASE4_FINAL_GATE_v2_33r.md`.

## v2.33Q — arquitectura multifuente mínima, Bloque F (2026-08-31)

Esquema canónico `PriceRecord` (20 campos) en `scripts/price_adapters/schema.py`, con distinción explícita entre sin-operación / no-aplica / no-disponible-por-licencia. Adaptadores de normalización para J-Quants y TWSE (sin tocar red ni credenciales, reutilizan los descargadores ya probados de v2.33G/v2.33I) — verificados contra datos reales: 20.294 registros J-Quants, 29.484 registros TWSE, 0 problemas de forma. Manifiesto de cobertura reproducible para 50 activos reales. QA offline sin red. No autoriza scoring, ranking ni fase 5. Detalle en `outputs/full_universe_source_acquisition/v2_33q_multisource_architecture/MULTISOURCE_ARCHITECTURE_v2_33q.md`.

## v2.33P — reparación de metadatos SGX y Xetra, Bloque E (2026-08-31)

Repara identidad (no precios) sobre los 1.782 candidatos retenidos por corrupción de esquema. **SGX (358 filas):** columnas ticker/nombre intercambiadas, confirmado al 100%; ticker real recuperado en 358/358, nombre de empresa marcado como genuinamente ausente (no inventado). **Xetra (1.424 filas):** `company_name` contenía códigos de clasificación de segmento de Deutsche Börse, no nombres reales; reparado vía OpenFIGI por ISIN (fail-closed, sin cuenta) — **1.256/1.424 (88,2%)** reparados con coincidencia exacta, 168 bloqueados (163 por discrepancia real entre fuentes, 5 sin registro). El censo canónico no se modifica; toda reparación vive en archivos delta separados. No se investiga fuente de precios en este bloque. Detalle en `outputs/full_universe_source_acquisition/v2_33p_sgx_xetra_metadata_repair/SGX_XETRA_METADATA_REPAIR_v2_33p.md`.

## v2.33O — cierre operativo TWSE, Bloque D (2026-08-31)

Decide sustituir EODHD por la fuente oficial TWSE (v2.33I) para los 8 activos ya validados: gana en profundidad (16×) y licencia, pierde el ajuste por splits/dividendos que sí tenía EODHD (documentado sin ocultar). Identifica el endpoint oficial `TWT49U` (ex-derecho/ex-dividendo) como vía real para construir ajuste en el futuro — confirmado en vivo, algoritmo no implementado en este cierre; series marcadas explícitamente `unadjusted`. Ampliación a los 696 candidatos elegibles bloqueada: supera el umbral de 500 activos, estimada en ~31 horas de ejecución, pendiente de autorización explícita. Detalle en `outputs/full_universe_source_acquisition/v2_33o_twse_operational_closure/TWSE_OPERATIONAL_CLOSURE_v2_33o.md`.

## v2.33N — licencia J-Quants y alcance JPX, Bloque C (2026-08-31)

Confirma mediante documentación oficial que la licencia de J-Quants es compatible con el uso privado de Scout Finance (cita textual de "Purpose of use and use of data"), con el límite explícito de no compartir datos brutos ni proveer análisis a terceros de forma recurrente. Evalúa qué indicadores son válidos con la ventana real de 2 años: retorno a 1 año, medias móviles, momentum y volatilidad sí; estabilidad multi-ciclo y CAGR a 3-5 años no. Ampliación a los 3.701 candidatos elegibles bloqueada: supera el umbral de 500 activos, estimada en ~31 horas de ejecución, pendiente de autorización explícita. Detalle en `outputs/full_universe_source_acquisition/v2_33n_jpx_license_and_scope/JPX_LICENSE_AND_SCOPE_v2_33n.md`.

## v2.33M — evaluación de fuentes EE. UU., Bloque B (2026-08-31)

Evalúa fuentes gratuitas para el bloque EE. UU. (NASDAQ+NYSE+NYSE American+Cboe BZX, 5.011 candidatos, 23,67 % del universo). Twelve Data (plan Basic) es la única candidata viable identificada, pero requiere que el usuario cree una cuenta (no hecho, corresponde solo al usuario). Stooq descartada explícitamente por carecer de términos de uso documentados ("API no documentada" según la comunidad) — incumple las reglas del proyecto. **Decisión: `BLOCKED_USER_ACTION_REQUIRED`.** No autoriza ninguna descarga, cuenta, scoring, ranking ni fase 5. Detalle en `outputs/full_universe_source_acquisition/v2_33m_us_source_evaluation/US_SOURCE_EVALUATION_v2_33m.md`.

## v2.33L — auditoría, inventario y alcance del universo operativo (2026-08-31)

Inicio del cierre completo de la fase 4 (precios históricos y arquitectura multifuente), Bloque A. Auditoría confirma repo limpio y alineado con `origin/main`. **Hallazgo clave:** medido contra el censo canónico completo (21.165 candidatos elegibles, no la muestra de 240), Cboe Europe representa el **49,53 %** del universo elegible — ya bloqueado indefinidamente desde v2.33H. Distribución completa: JPX 17,49 %, NASDAQ 14,25 %, NYSE 8,32 %, ASX 6,01 %, TWSE 3,29 %, NYSE American 1,10 %, BVC 0,01 %, Cboe BZX 0,00 %. Además, 1.782 candidatos (Xetra 1.424, SGX 358) quedan retenidos fuera de este total por corrupción de esquema, pendientes de reparación. **Decisión de alcance: MVP multifuente de alcance limitado, no cobertura mundial** — techo teórico de cobertura si JPX/TWSE se amplían y EE. UU. se resuelve: ~44,45 % de los 21.165 candidatos. Sesgo geográfico documentado explícitamente (concentración en EE. UU./Japón/Taiwán). Añade `scripts/build_market_universe_inventory_v2_33l.py` y `tests/qa_market_universe_inventory_v2_33l.py`. No autoriza scoring, ranking, fundamentales ni fase 5. Detalle en `outputs/full_universe_source_acquisition/v2_33l_operational_universe_scope/OPERATIONAL_UNIVERSE_SCOPE_v2_33l.md`.

## Post-cierre v2.33K (2026-08-31) — BVC cerrado por decisión del usuario

El usuario decide no seguir investigando BVC (ni siquiera comprobar manualmente la herramienta de bvc.com.co). BVC (1 símbolo, Banco de Bogotá) queda cerrado sin fuente de precios, sin previsión de retomarlo.

## v2.33K — evaluación de fuentes BVC, Colombia (2026-08-31)

Revisión del único símbolo bloqueado de BVC (P015, Banco de Bogotá, 1/240 del piloto original). La página oficial de la Superintendencia Financiera de Colombia confirma directamente nuestro identificador interno (`COB01PAAO006`) pero solo ofrece 3 cifras resumen por periodo (precio/máximo/mínimo), no una serie diaria — insuficiente para reconstruir un histórico OHLCV. BVC (bvc.com.co) probablemente ofrece una herramienta mejor según fuentes secundarias independientes, pero no fue accesible de forma automatizada en un navegador real (se queda cargando indefinidamente sin llamadas de datos observables); no se intentó ningún método para forzar el acceso. **Decisión: inconcluso, de bajo impacto (1 símbolo)** — no se recomienda seguir invirtiendo tiempo salvo que el usuario quiera probarlo manualmente. Detalle en `outputs/full_universe_source_acquisition/v2_33k_bvc_source_evaluation/BVC_SOURCE_EVALUATION_v2_33k.md`.

## v2.33J — reconfirmación de fuentes ASX (2026-08-31)

Tras el éxito con TWSE en v2.33I, se comprobó si ASX (Australia) tiene un equivalente gratuito oficial. Resultado: **no lo tiene**, confirmado con evidencia de primera mano (no solo búsquedas): la propia página oficial de ASX declara que el acceso a datos de precios exige licencia directa o suscripción de pago a un distribuidor, sin nivel gratuito; y el único endpoint no oficial conocido usado por herramientas de terceros está confirmado muerto (HTTP 404 en una única petición sin autenticar, sin intento de sortear ninguna protección). **Decisión: `NO_FREE_SOURCE_FOUND`.** Reconfirma, con más rigor, la conclusión ya alcanzada en v2.33F. No autoriza ninguna descarga, scoring, ranking ni fase 5. Detalle en `outputs/full_universe_source_acquisition/v2_33j_asx_source_reconfirmation/ASX_SOURCE_RECONFIRMATION_v2_33j.md`.

## v2.33I — piloto real de precios TWSE con datos oficiales de Taiwán (2026-08-31)

Piloto real (no solo documental) sobre la fuente identificada en v2.33F: el endpoint oficial `STOCK_DAY` de TWSE (`www.twse.com.tw`), gratuito y sin cuenta, para los 8 activos TWSE ya resueltos en v2.33D. Resultado: **8/8 activos descargados, 0 fallos**, **29.472 observaciones válidas**, mediana de **4.076 sesiones/activo** (más de 16 veces la profundidad de EODHD para los mismos activos), ventana real 2010-01-04 → 2026-08-31 confirmada por el propio proveedor. Incidencia técnica resuelta: fallo de verificación SSL por un certificado con "Subject Key Identifier" incompleto en el lado de TWSE, corregido usando el almacén de certificados de `certifi` (sin desactivar la verificación). Limitación documentada: sin ajuste por splits/dividendos, a diferencia de EODHD/J-Quants. **Decisión: `PASS_FOR_NEXT_CONTROLLED_PILOT`, acotado a estos 8 activos.** No autoriza sustitución automática en producción, scoring, ranking, fundamentales, planes de pago, brokers ni fase 5. Añade `scripts/download_twse_opendata_price_pilot_v2_33i.py`, `scripts/build_twse_opendata_collection_report_v2_33i.py`, `tests/qa_twse_opendata_price_pilot_v2_33i.py`, `tests/qa_twse_opendata_downloader_v2_33i.py`. Detalle en `outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot/PRICE_PILOT_STATUS_v2_33i.md`.

## Post-cierre v2.33H (2026-08-31) — sin opciones de pago para Cboe Europe

El usuario descarta explícitamente cualquier opción de pago para desambiguar las 76 empresas de Cboe Europe con mercado múltiple. Cboe Europe (119 símbolos) queda bloqueado de forma indefinida: agotadas las vías gratuitas conocidas (OpenFIGI para identidad, fuentes oficiales de v2.33F para precio) y sin vía de pago autorizada.

## v2.33H — mapeo de identificadores Cboe Europe vía OpenFIGI (2026-08-31)

Siguiendo con Cboe Europe tras v2.33F: mapeo de identificadores de los 119 símbolos bloqueados usando la búsqueda pública de OpenFIGI (sin cuenta, sin clave, sin gasto). Fail-closed: solo se acepta una empresa como identificada ante coincidencia exacta de nombre normalizado contra un único `shareClassFIGI`. Resultado: **89/119 (74.8%) empresas identificadas**, 30 sin identificar (29 sin coincidencia, 1 ambiguo — BlackRock Inc, correctamente bloqueado). Hallazgo central: incluso entre las empresas identificadas, el código de "mercado compuesto" de OpenFIGI **no es un indicador fiable de bolsa primaria** — el mismo código aparece en empresas de países completamente distintos (verificado explícitamente, no asumido). Por tanto, esta identificación **no habilita ninguna descarga de precios nueva**: determinar la bolsa real de cotización de estas empresas exigiría datos adicionales no disponibles gratuitamente. **Decisión: `PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`.** No autoriza scoring, ranking, fundamentales, planes de pago, brokers ni fase 5. Añade `scripts/resolve_cboe_europe_identifiers_v2_33h.py` y `tests/qa_cboe_europe_identifier_mapping_v2_33h.py`. Detalle en `outputs/full_universe_source_acquisition/v2_33h_cboe_europe_identifier_mapping/CBOE_EUROPE_IDENTIFIER_MAPPING_v2_33h.md`.

## v2.33G — piloto real de precios J-Quants / JPX (2026-08-31)

Piloto real (no solo documental) sobre la candidata más prometedora de v2.33F: J-Quants, API oficial de JPX, para los 42 símbolos japoneses bloqueados. El usuario creó una cuenta gratuita explícitamente para este piloto. Resultado: **42/42 símbolos resueltos por coincidencia exacta de nombre (0 emparejamientos dudosos)**, **42/42 activos descargados (0 fallos)**, **20.228 observaciones válidas**, ventana confirmada por el propio proveedor 2024-06-08 → 2026-06-08, **cobertura del 99.18%** frente al umbral del 90% de v2.33C. Incidente operativo documentado: el límite de tasa real (HTTP 429) fue más estricto que el documentado; se corrigió con mayor espaciado y reintento automático, sin pérdida de datos en la ejecución final. **Decisión: `PASS_FOR_NEXT_CONTROLLED_PILOT`, acotado exclusivamente a JPX/Japón** — no es una promoción a producción ni resuelve Cboe Europe/ASX/TWSE/BVC. No autoriza scoring, ranking, fundamentales, planes de pago, brokers ni fase 5. Añade `scripts/resolve_jquants_price_pilot_v2_33g.py`, `scripts/download_jquants_price_pilot_v2_33g.py`, `scripts/build_jquants_collection_report_v2_33g.py`, `tests/qa_jquants_price_pilot_collection_v2_33g.py`, `tests/qa_jquants_price_pilot_downloader_v2_33g.py`. Detalle en `outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/PRICE_PILOT_STATUS_v2_33g.md`.

## v2.33F — evaluación documental de fuentes oficiales por bolsa (2026-08-31)

Investigación pública (sin cuentas, sin claves, sin descargas, sin gasto) de fuentes oficiales de precios por bolsa como alternativa a EODHD/Twelve Data. Hallazgo clave: "Cboe Europe" (119 símbolos bloqueados) no es una bolsa de origen sino una plataforma de cruce paneuropea con emisores de docenas de países; no existe una fuente única para resolverla. Candidatas concretas encontradas: **J-Quants** (JPX/Japón, oficial, gratis, 2 años de histórico, retraso de 12 semanas) y el **portal de datos abiertos del gobierno de Taiwán** (oficial, gratis, actualizado a diario, podría mejorar la profundidad de los 8 activos TWSE ya resueltos). Sin alternativa gratuita encontrada para Xetra, ASX ni BVC. Detalle en `outputs/full_universe_source_acquisition/v2_33f_official_exchange_sources_evaluation/OFFICIAL_EXCHANGE_SOURCES_EVALUATION_v2_33f.md`.

## v2.33E — evaluación documental de Twelve Data (2026-08-31)

Investigación pública (sin cuenta, sin clave, sin descargas, sin gasto) de Twelve Data como alternativa gratuita a EODHD para precios mundiales. Hallazgo: el plan gratuito de Twelve Data solo cubre EE. UU., forex y cripto; ASX, TWSE, Cboe Europe y JPX requieren Pro+/Venture+ (planes de pago). 0/162 símbolos actualmente bloqueados serían accesibles en el plan gratuito. Decisión: **descartado como alternativa mundial gratuita**. Detalle en `outputs/full_universe_source_acquisition/v2_33e_twelve_data_evaluation/TWELVE_DATA_EVALUATION_v2_33e.md`.

## Post-cierre v2.33D1 (2026-08-30) — sin plan de pago

El usuario descarta explícitamente contratar cualquier plan de pago de EODHD. EODHD queda cerrado en `COMPLETED_NO_PROMOTION` de forma definitiva en su plan gratuito; no se reevaluará con un plan superior salvo que el usuario lo reabra explícitamente. El siguiente paso pendiente, no ejecutado, es explorar una fuente alternativa gratuita para precios mundiales o continuar resolviendo los 162 símbolos ambiguos restantes.

## v2.33D1 — EODHD Price Pilot Hardening & Real Collection Validation

Cierre honesto del piloto real de precios EODHD. No autoriza scoring, rankings, recomendaciones, fundamentales, incorporación masiva de precios, contratación de planes, brokers ni el inicio de la fase 5.

### Añadido

- `scripts/build_price_pilot_collection_report_v2_33d.py`: valida los 77 JSON descargados y construye un informe agregado reproducible (sin precios fila a fila).
- `tests/qa_price_pilot_collection_v2_33d.py`: QA local de los 77 históricos reales; imprime `SKIP` sin fallar CI cuando la carpeta de datos licenciados no está presente.
- `tests/qa_price_pilot_downloader_v2_33d.py`: QA del descargador reanudable, íntegramente offline (mocks, sin red, sin credenciales reales) — bloqueos, reanudación, continuidad tras errores, escritura atómica, ausencia de URL/token en informes.
- `outputs/full_universe_source_acquisition/v2_33d_price_pilot/price_pilot_collection_report_v2_33d1.json` y `PRICE_PILOT_COLLECTION_REPORT_v2_33d1.md`: informe agregado publicable.

### Corregido

- `scripts/download_eodhd_price_pilot_v2_33d.py`: acepta `resolved` y `resolved_deterministic`, es reanudable, omite archivos existentes, continúa tras errores HTTP/esquema, no registra URL ni token en errores, escribe cada JSON de forma atómica (temporal + reemplazo), genera `download_report_v2_33d.json`.
- `scripts/resolve_price_symbols_v2_33d.py`: `P014` (`ZSP.AX`, STANDARD & POORS INDICES AUSTRALIA) se excluye como índice no empresarial en vez de resolverse; `MOG.B` se resuelve correctamente como `MOG-B.US`.
- `.gitignore`: ignora explícitamente `outputs/full_universe_source_acquisition/v2_33d_price_pilot/eodhd_prices_collection_77_v2_33d/` (JSON brutos licenciados) y `.env.*`.

### Resultado

- 77/240 símbolos resueltos, 1 excluido, 162 bloqueados por ambigüedad real.
- Descarga real: 77/77 activos, 0 fallos, 0 omitidos.
- 18.714 observaciones numéricas válidas (18.791 filas en bruto, incluyendo una fila de aviso del proveedor por activo).
- Profundidad histórica real: mediana 250 sesiones por activo, ningún activo alcanza 2021; los 77/77 archivos incluyen el aviso literal del proveedor "Data is limited by one year as you have free subscription".
- **Decisión del gate: `COMPLETED_NO_PROMOTION`.** EODHD (plan gratuito) no supera el umbral de cobertura histórica (~17.5% vs 90% requerido por v2.33C) ni el de emparejamiento sobre la muestra completa (32% vs 90%). Detalle en `outputs/full_universe_source_acquisition/v2_33d_price_pilot/PRICE_PILOT_STATUS_v2_33d.md`.
- Progreso global: 3/8 fases cerradas, fase 4 en curso.

<!-- SCOUT_FINANCE_V2_33D1_STATE_END -->

<!-- SCOUT_FINANCE_V2_14I_STATE_START -->
## Entrada documental v2.14I

### v2.14I — Documentation and Canonical Dataset Path

- Documenta la separación entre app/MVP `v1.1C` y pipeline de datos `v2.14H`.
- Fija la ruta canónica vigente del expanded universe: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`.
- Documenta estado actual: `38,287` filas, `76.6%` hacia 50k, `11,713` filas pendientes.
- Mantiene full source gate y full 59k dry-run bloqueados.
- Fase documental: no modifica datos, no rebuild, no scoring, no OpenAI, no broker.


<!-- SCOUT_FINANCE_V2_14I_STATE_END -->

# CHANGELOG

## Sin tag — Simplificación de la interfaz para pruebas

### Cambiado

- `app.py`: login y FAQ deshabilitados (no se llaman desde `main()`, código sin borrar).
- `app.py`: pestañas reducidas de 7 a 4 (Dashboard, Ranking, Análisis empresa, Comparar empresas). Candidatos Stage 3, Histórico/técnico y Ajustes quedan ocultas.
- `app.py`: panel de costes OpenAI en la sidebar movido a un expander colapsado.
- Nuevo `.streamlit/config.toml` con tema visual básico.
- README.md / VERSION.md actualizados: la documentación seguía en v0.4 pero el código y los freezes (`docs/v1/`) ya estaban en v1.1C.

## v1.0 → v1.1C — Freezes intermedios (ver `docs/v1/`)

Entre v0.4 y este punto se añadió, en commits y freezes separados no reflejados antes en este changelog:

- capa de revisión manual documentada (watchlist / reject / needs_more_data) y export pack final;
- freeze candidate v1.0.0 y freeze de documentación (`docs/USER_GUIDE.md`, `docs/SAFETY_LIMITS.md`, `docs/QUICKSTART.md`);
- parche de usabilidad v1.1B;
- freeze final v1.1C MVP.

Detalle completo en `docs/v1/*.md` y `releases/`.

## v0.4 — Versión estable Fase 4H

### Añadido

- Documentación principal actualizada.
- FAQ actualizado dentro de Streamlit.
- `VERSION.md`.
- `CHECKLIST_USO.md`.
- `FAQ_SCOUT_FINANCE.md`.
- Consolidación de versión estable.

### Consolidado

- Dashboard ejecutivo.
- Ranking resumido.
- Análisis empresa con outputs Fase 2.
- Comparativa visual por JSON.
- Avisos por baja confianza/datos insuficientes.
- Histórico por empresa.
- Riesgo interpretado correctamente.
- Gráfico de riesgo separado.
- Ajustes / panel técnico.
- Checker de estabilidad.

### No incluido

- Recomendaciones Buy/Hold/Sell.
- Broker integration.
- Portfolio construction.
- Automatización de inversión.
