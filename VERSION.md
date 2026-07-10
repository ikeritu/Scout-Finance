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
