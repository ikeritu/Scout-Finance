# v2.38X — matriz de candidatos de Europa (real, no simulada)

> **⚠️ CORRECCIÓN POSTERIOR (2026-09-05, mismo día)**: el único candidato de esta matriz ("Softcat PLC") hereda una identidad mal atribuida de v2.38V/W — el activo real del censo es **SSE PLC**, no Softcat. Ver `outputs/full_universe_source_acquisition/v2_38v_europe_gb_identity_resolution/CORRECTION_XETRA_SOURCE_IDENTITY_v2_38v.md`. Esta matriz queda pendiente de reconstrucción una vez se decida si se amplía Companies House/iXBRL a las 40 identidades ahora confirmadas.

Fecha: 2026-09-05. Alcance: análogo de Europa a v2.38G (features fundamentales) + v2.38J (matriz de candidatos) de EE. UU., construido sobre los datos reales de v2.38W. Dos scripts, ambos ejecutados contra datos reales, sin red.

## Parte 1 — Features fundamentales (`build_europe_fundamental_features_v2_38x.py`)

**Diferencia deliberada con v2.38G (EE. UU.)**: no se calcula ninguna métrica de crecimiento interanual. El extractor de v2.38W solo captura el periodo más reciente por concepto (decisión ya documentada en ese bloque) — no existe un segundo año con el que comparar todavía. Todas las features de este bloque son ratios de un único periodo:

`net_margin`, `operating_margin`, `pretax_margin`, `return_on_assets`, `return_on_equity`, `liabilities_to_assets`, `equity_to_assets`, `cash_to_assets`, `current_ratio`.

**Resultado real (Softcat, único input con fundamentales reales tras v2.38W):**

| Ratio | Valor |
|---|---:|
| net_margin | 9,12% |
| operating_margin | 11,86% |
| return_on_equity | 39,26% |
| liabilities_to_assets | 71,58% |
| current_ratio | 1,39 |

**9/9 ratios calculados → `FEATURES_READY`.** Ningún ratio se aproxima ni se calcula con un componente ausente: la lógica de rechazo (`missing_numerator` / `missing_or_zero_denominator`) queda probada explícitamente con fixtures sintéticos.

## Parte 2 — Matriz de candidatos (`build_europe_candidate_feature_matrix_v2_38x.py`)

Une las features fundamentales (parte 1) con las features de precio de v2.38P — que hoy tienen **0 filas reales** (v2.38O/P nunca llegaron a recolectar historial de precios real para Europa). El resultado refleja esto con honestidad, no lo oculta ni lo simula.

**Resultado real:**

| Estado | Cantidad |
|---|---:|
| `CANDIDATE_MATRIX_READY` (fundamentales + precio) | 0 |
| `CANDIDATE_MATRIX_PARTIAL_PRICE` (solo fundamentales) | **1** (Softcat) |
| `CANDIDATE_MATRIX_PARTIAL_FUNDAMENTALS` (solo precio) | 0 |
| `CANDIDATE_MATRIX_INSUFFICIENT_EVIDENCE` | 0 |
| Total de candidatos | **1** |

Softcat queda como único candidato, con estado `CANDIDATE_MATRIX_PARTIAL_PRICE` — nunca se rellenan sus campos de precio (`return_3m`, `return_12m`, etc.) con nada; quedan explícitamente vacíos, con un resumen textual que dice literalmente "v2.38P/O no han recolectado historial de precios real todavía", en vez de dejar un hueco sin explicar.

## Por qué el resultado es tan pequeño, y por qué eso es correcto

De los 689 activos europeos con casa de cotización resuelta (v2.38N):
- 617 (piloto de proveedor) bloqueados por política — EODHD Fundamentals exige pago.
- 55 (filings oficiales GB/ES) — de los 40 GB, solo 4 identidades reales resueltas (v2.38V), de las cuales solo 3 tienen perfil confirmado en Companies House, y de esas solo 1 (Softcat) tiene un documento iXBRL real parseable.
- 17 (revisión manual Irlanda) bloqueados por identidad sin confirmar.
- 0/689 con historial de precios real.

Este bloque no amplía ninguna de estas cifras — solo une lo que ya existe. Un resultado de "1 candidato parcial" es la representación honesta y correcta del estado real del proyecto en Europa hoy, no un error del script.

## Pruebas offline

`tests/qa_europe_candidate_feature_matrix_v2_38x.py` — 6 casos, sin red, sin datos reales:

1. Todos los ratios se calculan correctamente cuando los 9 conceptos están presentes.
2. Un concepto ausente produce `FEATURES_PARTIAL` con el motivo de rechazo correcto (`missing_numerator` / `missing_or_zero_denominator`).
3. Sin ningún dato real → `INSUFFICIENT_FEATURE_EVIDENCE`.
4. La matriz clasifica correctamente `READY` / `PARTIAL_PRICE` / `PARTIAL_FUNDAMENTALS`.
5. Con 0 filas de precio de entrada (el estado real actual), la matriz nunca inventa un valor de precio — los campos quedan vacíos con un resumen textual honesto.
6. Una fila con identidad inválida se rechaza explícitamente, nunca se descarta en silencio.

```
.venv/Scripts/python.exe tests/qa_europe_candidate_feature_matrix_v2_38x.py
PASS: v2.38X-europe-candidate-feature-matrix/ratio-computation/classification/no-invented-price-signal/no-silent-drops
```

## Seguridad y alcance

- Sin red, sin credenciales en este bloque — solo lee ficheros ya generados por v2.38W (real, gitignored) y v2.38P (real, vacío).
- Solo se publican ratios (porcentajes/proporciones), nunca cifras absolutas de ingresos/beneficio/activos — consistente con la política de todo el proyecto de no publicar magnitudes con licencia del proveedor.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.
- `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: `COMPLETED_EUROPE_CANDIDATE_FEATURE_MATRIX_NOT_SCORING`.** 1 candidato preparado (parcial, sin precio); listo para v2.38Y una vez exista suficiente evidencia — hoy, solo con Softcat, cualquier scoring real sería estadísticamente vacío de sentido.
