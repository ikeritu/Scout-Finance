<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## Estado actual del pipeline de datos / Current Data Pipeline State

**Fase 7 (validación histórica) — cerrada** con la decisión **`INSUFFICIENT_EVIDENCE`** (v2.36, 2026-08-31). El gate temporal falló antes de observar rendimientos: JPX no tiene profundidad OOS suficiente y TWSE carece de fechas fundamentales point-in-time y precios ajustados. Detalle en `outputs/full_universe_source_acquisition/v2_36_phase7_final_gate/PHASE7_FINAL_GATE_v2_36.md`.

- Interfaz estable (app/UI, sin cambios): `v2.32F — local UI final freeze`.
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
- Historial completo, cierre por cierre (v2.33D1 a v2.35C), en `CHANGELOG.md`.
- Progreso global: **7/8 fases cerradas**. **Fase 8 no autorizada**; el ranking debe seguir presentándose como experimental y no validado históricamente.

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
