<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## Estado real actual del pipeline de datos / Current Data Pipeline Real State

Estado tras el cierre de **v2.33D1 — EODHD Price Pilot Hardening & Real Collection Validation**.

- App/MVP: `v1.1C — MVP Final Freeze` (sin cambios).
- Interfaz local estable: `v2.32F — local UI final freeze` (sin cambios).
- Pipeline de datos vigente: `v2.33G — J-Quants (JPX/Japón) Real Price Pilot`, sobre la base de `v2.33D1`/`v2.33E`/`v2.33F`.
- Decisión del piloto real de precios EODHD: **`COMPLETED_NO_PROMOTION`** — no se promociona a producción (ver `outputs/full_universe_source_acquisition/v2_33d_price_pilot/PRICE_PILOT_STATUS_v2_33d.md`).
- Twelve Data (plan gratuito): descartado como fuente mundial (v2.33E) — solo cubre EE. UU./forex/cripto.
- Decisión del piloto real de precios J-Quants (JPX/Japón): **`PASS_FOR_NEXT_CONTROLLED_PILOT`, acotado exclusivamente a Japón** — 42/42 símbolos resueltos y descargados, 99.18% de cobertura histórica frente al 90% exigido (ver `outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/PRICE_PILOT_STATUS_v2_33g.md`). No resuelve Cboe Europe (119 bloqueados), ASX ni TWSE.
- Mapeo de identificadores Cboe Europe (v2.33H, OpenFIGI): **89/119 empresas identificadas**, pero **`PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`** — el código de mercado compuesto de OpenFIGI no indica de forma fiable la bolsa real (verificado), así que no habilita ninguna descarga nueva. Usuario descarta opciones de pago (2026-08-31): Cboe Europe (119 símbolos) queda bloqueado de forma indefinida. Ver `outputs/full_universe_source_acquisition/v2_33h_cboe_europe_identifier_mapping/CBOE_EUROPE_IDENTIFIER_MAPPING_v2_33h.md`.
- Piloto real TWSE con datos oficiales de Taiwán (v2.33I): **`PASS_FOR_NEXT_CONTROLLED_PILOT`**, acotado a los 8 activos TWSE ya resueltos — 8/8 descargados, mediana 4.076 sesiones/activo (>16× EODHD), ventana real 2010-01-04 → hoy, sin ajuste por splits/dividendos. Ver `outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot/PRICE_PILOT_STATUS_v2_33i.md`.
- ASX (v2.33J): **`NO_FREE_SOURCE_FOUND`**, confirmado con evidencia de primera mano (política oficial exige licencia/pago; único endpoint no oficial conocido confirmado muerto). Ver `outputs/full_universe_source_acquisition/v2_33j_asx_source_reconfirmation/ASX_SOURCE_RECONFIRMATION_v2_33j.md`.
- BVC / Colombia (v2.33K, 1 símbolo): **inconcluso, bajo impacto**. Fuente oficial (SFC) confirmada pero insuficiente (solo resumen); herramienta de BVC probablemente mejor, no verificable de forma automatizada. Ver `outputs/full_universe_source_acquisition/v2_33k_bvc_source_evaluation/BVC_SOURCE_EVALUATION_v2_33k.md`.
- Progreso global: `3/8 fases cerradas, fase 4 en curso`.
- Siguiente fase recomendada: **ninguna fase nueva autorizada por este cierre**. El usuario ha descartado explícitamente contratar un plan de pago de EODHD (2026-08-30) y opciones de pago para Cboe Europe (2026-08-31). Con esto se completa la revisión de los cuatro mercados originalmente bloqueados/limitados del piloto v2.33D. El siguiente paso, si el usuario lo decide, es confirmar por escrito el alcance de licencia de J-Quants antes de darle más uso, o decidir si sustituir la fuente TWSE de EODHD por la oficial de v2.33I.

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
