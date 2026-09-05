<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
## Estado actual del pipeline de datos / Current Data Pipeline State

**Fases v2.38K–X — scoring experimental US y fundamentales reales de Europa** (branch `phase9b-global-enrichment-v2-38b`, aún no fusionado a `main`). Sobre la matriz de candidatos US de v2.38J: scoring experimental (v2.38K), shortlist explicada (v2.38L) y contexto macro/geopolítico estático (v2.38M). Fundación de Europa: casa de cotización (v2.38N), precios sin ejecutar (v2.38O/P), enrutamiento de fundamentales (v2.38Q/R/S: 617/55/17), revisión manual de Irlanda (v2.38T) y gate de disposición (v2.38U). **v2.38V/W/X**: primer piloto real de identidad, Companies House e iXBRL para 3-4 empresas GB, incluida Softcat con 14/14 conceptos IFRS extraídos y verificados contablemente.

**⚠️ Corrección real encontrada el mismo día**: 2 de esas 4 identidades (`SCT`→"Softcat", `BMT`→"Braime") estaban mal atribuidas — el resolutor original confundía el mnemonic interno de Xetra con un ticker real de LSE, y coincidió por casualidad con el ticker real de otra empresa no relacionada. Corregido resolviendo directamente contra el fichero fuente oficial de Xetra ya local (sin red, sin colisión posible vía ISIN): **40/40 activos GB ahora identificados correctamente** (Diageo, BAE Systems, British American Tobacco, Rio Tinto, SSE, BP, Barclays, Vodafone, Tesco, GSK, Shell, Unilever y 28 más) — un salto enorme frente al 4/40 anterior. Ningún commit se reescribe; la corrección queda documentada con transparencia total, con avisos añadidos en V/W/X.

**v2.38Y — Companies House + iXBRL ampliados a las 40 empresas**: perfiles de Companies House confirmados **29/40** (fail-closed; los 11 restantes son nombres Xetra abreviados o empresas no constituidas en UK, nunca forzados por adivinanza). Dos bugs reales de limpieza de nombres encontrados y corregidos en el proceso (un sufijo de denominación con espacio sin cubrir; el nombre legal real de BP registrado como "BP P.L.C." con puntos, que rompía el emparejamiento del sufijo). De las 29, **Kingfisher plc** tiene un paquete iXBRL real (13/14 conceptos IFRS extraídos, verificados con las cuatro identidades contables exactas) — segunda empresa real confirmada tras Softcat. Ninguna fase de este rango calcula scoring adicional, ranking, recomendaciones ni autoriza fase 9C.

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
- Extensión global: **9A cerrada; 9B en curso (v2.38C–Y cerradas, con una corrección real de identidad post-X: 40/40 activos GB identificados correctamente vía fuente Xetra, y v2.38Y ampliando Companies House/iXBRL a esa escala real: 29/40 perfiles confirmados, 2 empresas con iXBRL real -- Softcat y Kingfisher); 9C no autorizada**. Este rango (v2.38K–Y + corrección) vive en el branch `phase9b-global-enrichment-v2-38b` (subido a GitHub, **no fusionado a `main`**). Estado: `outputs/full_universe_source_acquisition/v2_38b_global_enrichment/PHASE9B_EXECUTION_STATUS_v2_38b.md`. El ranking de la app sigue limitado a 50 activos, es experimental y no está validado históricamente.

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
