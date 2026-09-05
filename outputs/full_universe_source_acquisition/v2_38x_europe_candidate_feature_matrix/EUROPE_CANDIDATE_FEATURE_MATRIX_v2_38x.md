# v2.38X — matriz de candidatos de Europa (real, no simulada)

> **Reconstruida el 2026-09-05** tras la ampliación real de v2.38Y (Companies House + iXBRL a las 40 identidades GB corregidas). Esta versión sustituye a la original de este mismo día, que solo tenía a Softcat como candidato — ahora incluye **Softcat y Kingfisher**, las dos únicas empresas con un paquete iXBRL real confirmado hasta hoy (v2.38W y v2.38Y respectivamente). Los scripts (`build_europe_fundamental_features_v2_38x.py`, `build_europe_candidate_feature_matrix_v2_38x.py`) no cambiaron de lógica: la parte 1 ahora lee y combina los ficheros de registros iXBRL de **ambos** bloques (v2.38W + v2.38Y) en vez de solo v2.38W.
>
> **⚠️ Advertencia de identidad heredada, aún sin corregir en los datos**: la fila de "SOFTCAT PLC" (`asset_id U37446`) contiene cifras financieras reales y correctas, pero corresponden **literalmente a Softcat plc**, mientras que la identidad correcta de ese activo del censo es **SSE PLC** (ver `outputs/full_universe_source_acquisition/v2_38v_europe_gb_identity_resolution/CORRECTION_XETRA_SOURCE_IDENTITY_v2_38v.md`). v2.38W nunca se ha vuelto a ejecutar contra la identidad corregida (SSE PLC), así que esta fila sigue siendo, en la práctica, "los fundamentales reales de Softcat, bajo el asset_id de SSE" — útil como prueba de que el extractor funciona, no como dato atribuible a SSE PLC. Corregirlo exigiría repetir Companies House + iXBRL para SSE PLC específicamente, no incluido en el alcance de "reconstruir la matriz" de hoy.

Fecha original: 2026-09-05. Alcance: análogo de Europa a v2.38G (features fundamentales) + v2.38J (matriz de candidatos) de EE. UU., construido sobre los datos reales de v2.38W y v2.38Y. Dos scripts, ambos ejecutados contra datos reales, sin red.

## Parte 1 — Features fundamentales (`build_europe_fundamental_features_v2_38x.py`)

**Diferencia deliberada con v2.38G (EE. UU.)**: no se calcula ninguna métrica de crecimiento interanual. Los extractores de v2.38W/Y solo capturan el periodo más reciente por concepto (decisión ya documentada en esos bloques) — no existe un segundo año con el que comparar todavía. Todas las features de este bloque son ratios de un único periodo:

`net_margin`, `operating_margin`, `pretax_margin`, `return_on_assets`, `return_on_equity`, `liabilities_to_assets`, `equity_to_assets`, `cash_to_assets`, `current_ratio`.

**Resultado real (2 empresas, tras combinar los registros de v2.38W + v2.38Y):**

| Ratio | Softcat (v2.38W)* | Kingfisher (v2.38Y) |
|---|---:|---:|
| net_margin | 9,12% | 1,89% |
| operating_margin | 11,86% | 3,62% |
| return_on_equity | 39,26% | 3,98% |
| liabilities_to_assets | 71,58% | 45,97% |
| current_ratio | 1,39 | 1,21 |

\* Fila etiquetada "Softcat" por herencia de v2.38W — ver advertencia de identidad arriba.

**9/9 ratios calculados para AMBAS empresas → `FEATURES_READY` × 2.** Ningún ratio se aproxima ni se calcula con un componente ausente: la lógica de rechazo (`missing_numerator` / `missing_or_zero_denominator`) sigue probada explícitamente con fixtures sintéticos, y ahora también una prueba dedicada a la fusión de varios ficheros de entrada (`test_multiple_records_inputs_are_merged_across_companies`), incluyendo el caso de un fichero de entrada que aún no existe (una fuente futura sin datos reales todavía) — se salta honestamente, nunca es un error.

## Parte 2 — Matriz de candidatos (`build_europe_candidate_feature_matrix_v2_38x.py`)

Une las features fundamentales (parte 1) con las features de precio de v2.38P — que hoy tienen **0 filas reales** (v2.38O/P nunca llegaron a recolectar historial de precios real para Europa). El resultado refleja esto con honestidad, no lo oculta ni lo simula.

**Resultado real:**

| Estado | Cantidad |
|---|---:|
| `CANDIDATE_MATRIX_READY` (fundamentales + precio) | 0 |
| `CANDIDATE_MATRIX_PARTIAL_PRICE` (solo fundamentales) | **2** (Softcat*, Kingfisher) |
| `CANDIDATE_MATRIX_PARTIAL_FUNDAMENTALS` (solo precio) | 0 |
| `CANDIDATE_MATRIX_INSUFFICIENT_EVIDENCE` | 0 |
| Total de candidatos | **2** |

Ambas quedan como candidatos con estado `CANDIDATE_MATRIX_PARTIAL_PRICE` — nunca se rellenan sus campos de precio (`return_3m`, `return_12m`, etc.) con nada; quedan explícitamente vacíos, con un resumen textual que dice literalmente "v2.38P/O no han recolectado historial de precios real todavía", en vez de dejar un hueco sin explicar.

## Por qué el resultado sigue siendo pequeño, y por qué eso es correcto

De los 40 activos GB ahora correctamente identificados (v2.38V corrección) y los 29/40 con perfil confirmado en Companies House (v2.38Y):
- Solo 2/29 tienen un paquete iXBRL real disponible en Companies House (Softcat y Kingfisher) — el resto son PDF-only, no forzado a OCR.
- 0/689 activos europeos con historial de precios real (v2.38O/P).
- Los otros 617 (piloto de proveedor) siguen bloqueados por política de pago; los 17 de Irlanda por identidad sin confirmar.

Este bloque no amplía ninguna de estas cifras — solo une lo que ya existe. Un resultado de "2 candidatos parciales" es la representación honesta y correcta del estado real del proyecto en Europa hoy, no un error del script.

## Pruebas offline

`tests/qa_europe_candidate_feature_matrix_v2_38x.py` — 7 casos, sin red, sin datos reales:

1. Todos los ratios se calculan correctamente cuando los 9 conceptos están presentes.
2. Un concepto ausente produce `FEATURES_PARTIAL` con el motivo de rechazo correcto (`missing_numerator` / `missing_or_zero_denominator`).
3. Sin ningún dato real → `INSUFFICIENT_FEATURE_EVIDENCE`.
4. **Nuevo**: varios ficheros de registros de entrada se combinan correctamente por empresa, y un fichero ausente se salta sin error.
5. La matriz clasifica correctamente `READY` / `PARTIAL_PRICE` / `PARTIAL_FUNDAMENTALS`.
6. Con 0 filas de precio de entrada (el estado real actual), la matriz nunca inventa un valor de precio — los campos quedan vacíos con un resumen textual honesto.
7. Una fila con identidad inválida se rechaza explícitamente, nunca se descarta en silencio.

```
.venv/Scripts/python.exe tests/qa_europe_candidate_feature_matrix_v2_38x.py
PASS: v2.38X-europe-candidate-feature-matrix/ratio-computation/classification/no-invented-price-signal/no-silent-drops
```

## Seguridad y alcance

- Sin red, sin credenciales en este bloque — solo lee ficheros ya generados por v2.38W y v2.38Y (reales, gitignored) y v2.38P (real, vacío).
- Solo se publican ratios (porcentajes/proporciones), nunca cifras absolutas de ingresos/beneficio/activos — consistente con la política de todo el proyecto de no publicar magnitudes con licencia del proveedor.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.
- `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: `COMPLETED_EUROPE_CANDIDATE_FEATURE_MATRIX_NOT_SCORING`.** 2 candidatos preparados (ambos parciales, sin precio); listo para una fase de scoring futura solo cuando exista suficiente evidencia — hoy, con 2 empresas (una de ellas con una advertencia de identidad heredada sin resolver), cualquier scoring real seguiría siendo estadísticamente vacío de sentido.
