<!-- SCOUT_FINANCE_V2_33D1_STATE_START -->
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
