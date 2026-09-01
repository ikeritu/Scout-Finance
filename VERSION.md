<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## Estado real actual del pipeline de datos / Current Data Pipeline Real State

**Fase 9B — infraestructura offline completada y adquisición real bloqueada** (`BLOCKED_EXTERNAL_ACTIONS_AFTER_INFRASTRUCTURE_READY`, v2.38B). El universo canónico contiene 43.089 filas; 738 tienen símbolo y ruta listos para lote controlado, 3.659 JPX requieren catálogo y 5.011 estadounidenses requieren acción externa. No existe scoring ni recomendación global.

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
- Progreso histórico: **8/8 fases originales cerradas**; extensión global **9A cerrada / 9B infraestructura lista pero adquisición bloqueada / 9C no autorizada**.
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
