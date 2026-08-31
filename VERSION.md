<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## Estado real actual del pipeline de datos / Current Data Pipeline Real State

**Fase 4 — cerrada** con la decisión `COMPLETED_SCOPED_OPERATIONAL_UNIVERSE` (v2.33R, 2026-08-31). Detalle completo, matriz por mercado y justificación en `outputs/full_universe_source_acquisition/v2_33r_phase4_final_gate/PHASE4_FINAL_GATE_v2_33r.md`.

- App/MVP: `v1.1C — MVP Final Freeze` (sin cambios).
- Interfaz local estable: `v2.32F — local UI final freeze` (sin cambios).
- Pipeline de datos vigente: `v2.33R — Fase 4 Final Gate`, sobre la base de `v2.33D1`–`v2.33Q`.
- **Cobertura real hoy: 50/21.165 candidatos elegibles (0,24 %)** — JPX (42 activos, J-Quants) + TWSE (8 activos, fuente oficial). Techo teórico si se resuelven las acciones pendientes: **44,45 %**. Excluido de forma permanente en el estado actual: **55,55 %** (Cboe Europe, ASX, BVC).
- Fuentes descartadas como mundiales: EODHD (`COMPLETED_NO_PROMOTION`, v2.33D1), Twelve Data (v2.33E, solo EE. UU./forex/cripto).
- JPX (v2.33G/N): `PASS_FOR_NEXT_CONTROLLED_PILOT`, licencia confirmada compatible con uso privado; ampliación a 3.701 candidatos bloqueada, pendiente de autorización (>500 activos).
- TWSE (v2.33I/O): `PASS_FOR_NEXT_CONTROLLED_PILOT`, sustituye a EODHD para los 8 activos; sin ajuste por splits/dividendos (fuente de ajuste oficial identificada, algoritmo no implementado); ampliación a 696 candidatos bloqueada, pendiente de autorización.
- Cboe Europe (v2.33H): `PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`, bloqueado indefinidamente (usuario descarta pago).
- ASX (v2.33J): `NO_FREE_SOURCE_FOUND`, confirmado de primera mano.
- BVC (v2.33K): cerrado por decisión del usuario, bajo impacto (1 símbolo).
- SGX/Xetra (v2.33P): identidad reparada (SGX 100 %, Xetra 88,2 %) vía OpenFIGI; sin fuente de precios evaluada todavía.
- Arquitectura multifuente (v2.33Q): esquema canónico `PriceRecord` + adaptadores J-Quants/TWSE, verificados contra 50 activos reales.
- EE. UU. (v2.33M): `BLOCKED_USER_ACTION_REQUIRED` — Twelve Data es la única candidata, requiere que el usuario cree la cuenta.
- Progreso global: **4/8 fases cerradas** (fase 4 recién cerrada).
- Siguiente fase recomendada: **fase 5 NO autorizada por este cierre.** Requiere decisión explícita nueva del usuario tras leer `PHASE4_FINAL_GATE_v2_33r.md`. Puntos abiertos independientes entre sí: (1) crear cuenta Twelve Data, (2) autorizar ampliación JPX, (3) autorizar ampliación TWSE, (4) decidir si se construye el algoritmo de ajuste TWSE, (5) decidir si se investiga fuente de precios para SGX/Xetra.

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
