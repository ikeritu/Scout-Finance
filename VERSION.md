<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## Estado real actual del pipeline de datos / Current Data Pipeline Real State

Estado tras el cierre de **v2.33D1 — EODHD Price Pilot Hardening & Real Collection Validation**.

- App/MVP: `v1.1C — MVP Final Freeze` (sin cambios).
- Interfaz local estable: `v2.32F — local UI final freeze` (sin cambios).
- Pipeline de datos vigente: `v2.33D1 — EODHD Price Pilot Hardening & Real Collection Validation`.
- Decisión del piloto real de precios EODHD: **`COMPLETED_NO_PROMOTION`** — no se promociona a producción (ver `outputs/full_universe_source_acquisition/v2_33d_price_pilot/PRICE_PILOT_STATUS_v2_33d.md`).
- Progreso global: `3/8 fases cerradas, fase 4 en curso`.
- Siguiente fase recomendada: **ninguna fase nueva autorizada por este cierre**. El usuario ha descartado explícitamente contratar un plan de pago de EODHD (2026-08-30); EODHD queda cerrado de forma definitiva en su plan gratuito. El siguiente paso, si el usuario lo decide, es evaluar una fuente alternativa gratuita para precios mundiales o resolver los 162 símbolos aún ambiguos.

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
