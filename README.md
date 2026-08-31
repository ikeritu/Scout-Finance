<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## Estado actual del pipeline de datos / Current Data Pipeline State

Estado añadido en el cierre de **v2.33D1 — EODHD Price Pilot Hardening & Real Collection Validation** (2026-08-30).

- Interfaz estable (app/UI, sin cambios en este cierre): `v2.32F — local UI final freeze`.
- Pipeline de datos vigente: `v2.33D1 — EODHD Price Pilot Hardening & Real Collection Validation`.
- Piloto real de precios EODHD: **77/77 históricos válidos**, 1 índice excluido (`P014`), 162/240 símbolos aún bloqueados por ambigüedad.
- Profundidad histórica real observada: mediana 250 sesiones/activo, ningún activo alcanza 2021 (plan gratuito de EODHD limitado a ~1 año, confirmado por el propio proveedor).
- **Decisión del gate: `COMPLETED_NO_PROMOTION`.** EODHD (plan gratuito) no se promociona a producción. Scoring, rankings, recomendaciones, fundamentales, incorporación masiva de precios, contratación de planes y fase 5 siguen **bloqueados**.
- Detalle: `outputs/full_universe_source_acquisition/v2_33d_price_pilot/PRICE_PILOT_STATUS_v2_33d.md`.
- Twelve Data (plan gratuito) descartado como alternativa mundial (v2.33E: solo cubre EE. UU./forex/cripto). Fuentes oficiales por bolsa evaluadas en v2.33F.
- **v2.33G — J-Quants (JPX/Japón):** piloto real ejecutado tras v2.33F. 42/42 símbolos japoneses resueltos y descargados, cobertura del 99.18% frente al 90% exigido. **Decisión: `PASS_FOR_NEXT_CONTROLLED_PILOT`, acotado exclusivamente a Japón** — no resuelve Cboe Europe (119 bloqueados), ASX ni TWSE. Detalle: `outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/PRICE_PILOT_STATUS_v2_33g.md`.
- **v2.33H — mapeo de identificadores Cboe Europe (OpenFIGI):** 89/119 empresas identificadas de forma inequívoca, pero sin bolsa primaria determinable de forma fiable para la mayoría (el código de "mercado compuesto" de OpenFIGI no corresponde al país real, verificado explícitamente). **Decisión: `PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE`** — no habilita ninguna descarga nueva. Cboe Europe queda bloqueado de forma indefinida (usuario descarta opciones de pago). Detalle: `outputs/full_universe_source_acquisition/v2_33h_cboe_europe_identifier_mapping/CBOE_EUROPE_IDENTIFIER_MAPPING_v2_33h.md`.
- **v2.33I — TWSE con datos oficiales de Taiwán:** piloto real sobre los 8 activos TWSE ya resueltos. 8/8 descargados, 29.472 observaciones, mediana 4.076 sesiones/activo (>16× la profundidad de EODHD), ventana real 2010-01-04 → hoy. **Decisión: `PASS_FOR_NEXT_CONTROLLED_PILOT`**, acotado a estos 8 activos. Detalle: `outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot/PRICE_PILOT_STATUS_v2_33i.md`.
- Progreso global: **3/8 fases cerradas, fase 4 en curso** (adquisición de fuente de datos completa).

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

