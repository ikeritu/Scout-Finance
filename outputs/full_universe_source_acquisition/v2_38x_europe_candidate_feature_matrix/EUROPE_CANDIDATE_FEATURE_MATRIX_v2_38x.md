# v2.38X — matriz de candidatos de Europa (real, no simulada)

> **Reconstruida dos veces el 2026-09-05.** Primera reconstrucción: tras v2.38Y (Companies House + iXBRL a las 40 identidades GB corregidas) se añadió Kingfisher como segundo candidato junto a la fila heredada "Softcat" (mal atribuida al activo `U37446`, que la corrección de v2.38V identificó como SSE PLC). Segunda reconstrucción, esta misma tarde, tras comprobar Companies House + iXBRL específicamente para SSE PLC: **confirmado que SSE PLC solo tiene PDF depositado en Companies House (sin iXBRL disponible)** — no existe ninguna vía para obtener cifras reales de SSE por este pipeline. En consecuencia, `U37446` queda **excluido explícitamente** de la matriz (nunca en silencio: la exclusión se registra en `europe_fundamental_feature_rejections_v2_38x.csv` con motivo `asset_reidentified_as_sse_plc_by_v2_38v_correction_but_records_are_softcat_plc_real_data_sse_confirmed_pdf_only_no_ixbrl_available`). La matriz queda con **1 único candidato, correctamente identificado: Kingfisher plc**. Ver `outputs/full_universe_source_acquisition/v2_38v_europe_gb_identity_resolution/CORRECTION_XETRA_SOURCE_IDENTITY_v2_38v.md` para el detalle completo de esta cadena de hallazgos.

Fecha original: 2026-09-05. Alcance: análogo de Europa a v2.38G (features fundamentales) + v2.38J (matriz de candidatos) de EE. UU., construido sobre los datos reales de v2.38W y v2.38Y. Dos scripts, ambos ejecutados contra datos reales, sin red.

## Parte 1 — Features fundamentales (`build_europe_fundamental_features_v2_38x.py`)

**Diferencia deliberada con v2.38G (EE. UU.)**: no se calcula ninguna métrica de crecimiento interanual. Los extractores de v2.38W/Y solo capturan el periodo más reciente por concepto (decisión ya documentada en esos bloques) — no existe un segundo año con el que comparar todavía. Todas las features de este bloque son ratios de un único periodo:

`net_margin`, `operating_margin`, `pretax_margin`, `return_on_assets`, `return_on_equity`, `liabilities_to_assets`, `equity_to_assets`, `cash_to_assets`, `current_ratio`.

**Exclusión explícita de identidad conocida**: `KNOWN_IDENTITY_MISMATCH_EXCLUSIONS` en el script excluye `U37446` (Softcat/SSE, ver aviso arriba) antes de calcular ninguna feature — nunca se llega a producir una fila con ratios reales bajo una identidad que sabemos incorrecta.

**Resultado real (1 empresa, tras excluir el caso de identidad conocida):**

| Ratio | Kingfisher (v2.38Y) |
|---|---:|
| net_margin | 1,89% |
| operating_margin | 3,62% |
| return_on_equity | 3,98% |
| liabilities_to_assets | 45,97% |
| current_ratio | 1,21 |

**9/9 ratios calculados → `FEATURES_READY`.** 1 activo excluido por identidad conocida (registrado, no silenciado). Ningún ratio se aproxima ni se calcula con un componente ausente.

## Parte 2 — Matriz de candidatos (`build_europe_candidate_feature_matrix_v2_38x.py`)

Une las features fundamentales (parte 1) con las features de precio de v2.38P — que hoy tienen **0 filas reales** (v2.38O/P nunca llegaron a recolectar historial de precios real para Europa). El resultado refleja esto con honestidad, no lo oculta ni lo simula.

**Resultado real:**

| Estado | Cantidad |
|---|---:|
| `CANDIDATE_MATRIX_READY` (fundamentales + precio) | 0 |
| `CANDIDATE_MATRIX_PARTIAL_PRICE` (solo fundamentales) | **1** (Kingfisher) |
| `CANDIDATE_MATRIX_PARTIAL_FUNDAMENTALS` (solo precio) | 0 |
| `CANDIDATE_MATRIX_INSUFFICIENT_EVIDENCE` | 0 |
| Total de candidatos | **1** |

Kingfisher queda como único candidato, con estado `CANDIDATE_MATRIX_PARTIAL_PRICE` — sus campos de precio quedan explícitamente vacíos con un resumen textual que dice literalmente "v2.38P/O no han recolectado historial de precios real todavía", en vez de dejar un hueco sin explicar.

## Por qué el resultado sigue siendo pequeño, y por qué eso es correcto

De los 40 activos GB ahora correctamente identificados (v2.38V corrección) y los 29/40 con perfil confirmado en Companies House (v2.38Y):
- Solo 2/29 tienen (o tuvieron) un paquete iXBRL real disponible en Companies House: Softcat (mal atribuido a un activo que en realidad es SSE PLC, ahora excluido) y Kingfisher (correctamente atribuido).
- SSE PLC específicamente comprobada y confirmada sin iXBRL — solo PDF, igual que Rio Tinto y Rentokil.
- 0/689 activos europeos con historial de precios real (v2.38O/P).
- Los otros 617 (piloto de proveedor) siguen bloqueados por política de pago; los 17 de Irlanda por identidad sin confirmar.

Este bloque no amplía ninguna de estas cifras — solo une lo que ya existe, excluyendo explícitamente lo que ya se sabe que está mal atribuido. Un resultado de "1 candidato parcial" es la representación honesta y correcta del estado real del proyecto en Europa hoy, no un error del script.

## Pruebas offline

`tests/qa_europe_candidate_feature_matrix_v2_38x.py` — 8 casos, sin red, sin datos reales:

1. Todos los ratios se calculan correctamente cuando los 9 conceptos están presentes.
2. Un concepto ausente produce `FEATURES_PARTIAL` con el motivo de rechazo correcto (`missing_numerator` / `missing_or_zero_denominator`).
3. Sin ningún dato real → `INSUFFICIENT_FEATURE_EVIDENCE`.
4. Varios ficheros de registros de entrada se combinan correctamente por empresa, y un fichero ausente se salta sin error.
5. **Nuevo**: un activo con identidad mal atribuida conocida (`U37446`) se excluye explícitamente de la matriz, y la exclusión queda registrada en el fichero de rechazos, nunca es un descarte silencioso.
6. La matriz clasifica correctamente `READY` / `PARTIAL_PRICE` / `PARTIAL_FUNDAMENTALS`.
7. Con 0 filas de precio de entrada (el estado real actual), la matriz nunca inventa un valor de precio — los campos quedan vacíos con un resumen textual honesto.
8. Una fila con identidad inválida se rechaza explícitamente, nunca se descarta en silencio.

```
.venv/Scripts/python.exe tests/qa_europe_candidate_feature_matrix_v2_38x.py
PASS: v2.38X-europe-candidate-feature-matrix/ratio-computation/classification/no-invented-price-signal/no-silent-drops
```

## Seguridad y alcance

- Sin red, sin credenciales en este bloque — solo lee ficheros ya generados por v2.38W y v2.38Y (reales, gitignored) y v2.38P (real, vacío).
- Solo se publican ratios (porcentajes/proporciones), nunca cifras absolutas de ingresos/beneficio/activos — consistente con la política de todo el proyecto de no publicar magnitudes con licencia del proveedor.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.
- `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: `COMPLETED_EUROPE_CANDIDATE_FEATURE_MATRIX_NOT_SCORING`.** 1 candidato preparado, real y correctamente identificado (Kingfisher, parcial, sin precio); listo para una fase de scoring futura solo cuando exista suficiente evidencia. La advertencia de identidad heredada de la reconstrucción anterior queda resuelta: ya no hay ninguna fila con identidad conocida-incorrecta en la matriz publicada.
