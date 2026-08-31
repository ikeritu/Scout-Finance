# Scout Finance v2.34A — auditoría inicial y manifiesto canónico (Bloque A, fase 5)

Fecha: 2026-08-31. Punto de partida: cierre de fase 4, commit `2d22e61c33466587856655540e2370d09d12fa8e`, decisión `COMPLETED_SCOPED_OPERATIONAL_UNIVERSE`.

## A.1 — Estado del repositorio

- Rama `main`, alineada con `origin/main` (0 commits de diferencia en ambas direcciones).
- `HEAD` coincide exactamente con el commit de referencia del prompt.
- Árbol de trabajo limpio salvo los 6 archivos locales protegidos (intactos, sin versionar).
- Estructura confirmada: `config/`, `docs/`, `outputs/`, `schemas/`, `scripts/`, `src/`, `tests/` — todas existen.
- **Hallazgo relevante:** existe trabajo previo de "fundamentales" en el repositorio (`src/enrich_fundamentals_yfinance.py`, `data/raw/fundamentals_source_yfinance.csv`, `docs/phase7/PHASE7C1_YFINANCE_FUNDAMENTALS_ENRICHMENT.md`), pero pertenece a la línea histórica del MVP antiguo (fases 6–7, anteriores al rigor v2.33), usa `yfinance` (un envoltorio no oficial de Yahoo Finance) y **no se reutiliza** en este cierre: no es una fuente oficial ni documentada, y mezclarla con el pipeline v2.33/v2.34 introduciría precisamente el tipo de fuente no autorizada que este proyecto evita. Se deja intacta, sin tocar, como parte del histórico útil del MVP congelado.
- No existía manifiesto de cobertura de fundamentales previo (`config/data_sources_v2_33c.json` es un registro de fuentes de **precios/identidad** de v2.33C, anterior al descubrimiento de J-Quants/TWSE; no se modifica, es histórico).

## A.2 — Población canónica: manifiesto de los 50 activos

Construido de forma reproducible (`scripts/prepare_fundamental_universe_v2_34a.py`) a partir de los artefactos reales ya validados de fase 4 — no se ha inventado ningún identificador:

- **42 activos JPX**, con `provider_symbol_jquants` (código oficial J-Quants confirmado en v2.33G) y `company_name` (nombre verificado por coincidencia exacta contra el maestro oficial de J-Quants).
- **8 activos TWSE**, con `provider_symbol_twse` (ticker `.TW` confirmado en v2.33D y validado con descarga real oficial en v2.33I) y `company_name`.
- **ISIN y LEI: vacíos para los 50** — el censo canónico de fase 4 no los contiene para JPX/TWSE, y no se han inventado ni buscado en fuentes externas en este bloque. Se registra la ausencia de forma honesta.
- Profundidad de precios ya validada, incorporada al manifiesto para contexto (no se vuelve a descargar): mediana JPX ~486 sesiones, mediana TWSE ~4.076 sesiones.

## A.3 — Control de identidad

Los 50 activos se clasifican `identity_verified`:

- **JPX (42):** resueltos en v2.33G mediante coincidencia **exacta** de `CompanyNameEnglish` contra el endpoint oficial `/v2/equities/master` de J-Quants — no por similitud textual. Cero coincidencias falsas confirmadas (el resolver bloqueaba cualquier caso ambiguo).
- **TWSE (8):** ticker `.TW` resuelto de forma determinista en v2.33D (regla de sufijo oficial, no adivinada) y confirmado de forma independiente al descargar 16 años de histórico real bajo ese mismo código oficial en v2.33I.

**0 activos en `identity_partial`, `identity_conflict` o `identity_blocked`.** Los 50 entran en el pipeline de adquisición de fundamentales (A.4).

## A.4 — Resultado de la auditoría

| | Valor |
|---|---:|
| Activos esperados | 50 |
| Activos encontrados | 50 |
| JPX | 42 |
| TWSE | 8 |
| Identificadores disponibles por activo | ticker interno, símbolo de proveedor, nombre verificado |
| Conflictos de identidad | 0 |
| Activos bloqueados | 0 |
| Archivos de entrada | `jquants_symbol_resolution_v2_33g.csv`, `price_pilot_symbols_v2_33d.csv`, `coverage_manifest_v2_33q.json` |
| Estado de Git | limpio, alineado con `origin/main`, 6 archivos protegidos intactos |
| **Decisión de continuidad** | **Continuar** — los 50 activos son válidos para el Bloque B en adelante |

Este bloque **no ha modificado** ningún archivo canónico de fase 4 (censo, manifiestos, informes de precios) — solo los ha leído.

## Seguridad y alcance

- Sin credenciales usadas, sin cuentas creadas, sin gasto.
- Sin descargas de red.
- `production_scoring_authorized: false`, `allow_ranking: false`.
