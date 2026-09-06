# v2.38X — matriz de candidatos de Europa (real, no simulada)

> **Reconstruida por tercera vez el 2026-09-06**, ahora incorporando las 20 empresas austriacas reales de v2.38AI. Las reconstrucciones anteriores del mismo día (Softcat+Kingfisher, y después solo Kingfisher tras confirmar que SSE PLC no tiene iXBRL disponible) siguen documentadas más abajo y en `outputs/full_universe_source_acquisition/v2_38v_europe_gb_identity_resolution/CORRECTION_XETRA_SOURCE_IDENTITY_v2_38v.md`.

## Generalización real necesaria: dos vocabularios de conceptos distintos

Los registros de Austria (v2.38AI) usan nombres de concepto en alemán (`umsatzerloese`, `eigenkapital`, `bilanzSumme`...), no la taxonomía IFRS (`ifrs-full:Revenue`, `ifrs-full:Equity`...) usada por GB/Irlanda. `build_europe_fundamental_features_v2_38x.py` se generalizó con un sistema de **alias canónicos** (`CONCEPT_ALIASES`): cada ratio ahora se calcula sobre un concepto canónico (`revenue`, `net_profit`, `total_assets`...) resuelto desde cualquiera de los dos vocabularios, no sobre el nombre crudo — añadir un tercer vocabulario en el futuro solo exige añadir sus nombres aquí, sin tocar la lógica de ratios.

**Caso especial real: "liabilities"**. El balance austriaco reparte lo que IFRS llama "Liabilities" en dos partidas separadas — `verbindlichkeiten` (deudas/pasivo exigible) y `rueckstellungen` (provisiones) — que junto con `eigenkapital` (patrimonio) suman el activo total (`bilanzSumme`), **verificado de forma exacta contra la cuenta real de PORR AG** en v2.38AI. El script ahora suma ambas partidas cuando no hay un concepto IFRS directo, en vez de usar solo `verbindlichkeiten` (lo que infravaloraría el pasivo real).

**Filtrado real necesario: solo el periodo más reciente**. A diferencia de GB/Irlanda (que solo tenían un periodo por concepto), Austria aporta **hasta 5 ejercicios fiscales por empresa**. El script ahora filtra explícitamente al periodo más reciente antes de calcular cualquier ratio — mezclar años habría producido ratios sin sentido (ej. combinar el `jahresueberschuss` de un año con el `umsatzerloese` de otro).

## Resultado real

**21 candidatos totales** (Kingfisher + 20 empresas austriacas; SSE/Softcat sigue excluido explícitamente, ver aviso de identidad heredada). Desglose de calidad de features:

| Estado | Cantidad |
|---|---:|
| `FEATURES_READY` (9/9 ratios) | 1 (Kingfisher) |
| `FEATURES_PARTIAL` | 17 (empresas austriacas — `current_ratio` siempre falta, sin equivalente austriaco de pasivo corriente capturado) |
| `INSUFFICIENT_FEATURE_EVIDENCE` | 3 (Raiffeisen Bank International, BAWAG Group, Fabasoft) |

**Hallazgo real: dos bancos austriacos (Raiffeisen Bank International, BAWAG Group) no tienen ningún ratio calculable.** Los bancos usan un esquema de cuenta de resultados regulado (BWG) que no incluye una partida "Umsatzerlöse" (ingresos) en el sentido industrial — el concepto simplemente no existe en su GuV real, por lo que se queda honestamente ausente, nunca aproximado.

## Matriz de candidatos final

Unida a las features de precio de v2.38P (**0 filas reales**, sin cambios): **21 candidatos, todos `CANDIDATE_MATRIX_PARTIAL_PRICE`** (sus campos de precio quedan vacíos con el mismo resumen textual honesto de siempre).

## ⚠️ Advertencia crítica, confirmada con ratios reales: entidad individual, no grupo consolidado

La advertencia de v2.38AI se traslada aquí con evidencia concreta: varias empresas austriacas muestran **márgenes netos superiores al 100%** — un resultado que sería absurdo para una empresa operativa normal, pero económicamente coherente para la **entidad jurídica individual (holding)** depositada en el Firmenbuch, cuyo resultado del ejercicio está dominado por ingresos de participaciones/dividendos de filiales, no por ventas operativas:

| Empresa | `net_margin` real | Interpretación |
|---|---:|---|
| OMV Aktiengesellschaft | 560,7% | Holding — beneficio neto (dividendos de filiales) muy superior a ingresos operativos individuales |
| VERBUND AG | 558,7% | Igual patrón |
| SBO AG | 480,6% | Igual patrón |
| STRABAG SE | 458,8% | Igual patrón |

**Estas cifras son reales y correctas para la entidad individual, pero nunca deben interpretarse como el margen neto del "grupo" que conocen los inversores.** Cualquier uso futuro de esta matriz para scoring debe tratar estos ratios con esta advertencia explícita, no como comparables directos a los de una empresa industrial consolidada.

## Pruebas offline

`tests/qa_europe_candidate_feature_matrix_v2_38x.py` — **9 casos**, sin red, sin datos reales: los 8 ya existentes más 1 nuevo (`test_austrian_vocabulary_ratios_and_liabilities_component_sum`) que reproduce exactamente el caso real de PORR AG — vocabulario alemán, suma de `verbindlichkeiten`+`rueckstellungen`, y filtrado al periodo más reciente (una ratio absurda de un año antiguo sintético nunca debe filtrarse al resultado).

```
.venv/Scripts/python.exe tests/qa_europe_candidate_feature_matrix_v2_38x.py
PASS: v2.38X-europe-candidate-feature-matrix/ratio-computation/classification/no-invented-price-signal/no-silent-drops
```

## Seguridad y alcance

- Sin red en este bloque — solo lee ficheros ya generados por v2.38W, v2.38Y, v2.38AI (reales) y v2.38P (real, vacío).
- Solo se publican ratios, nunca cifras absolutas de ingresos/beneficio/activos.
- Sin scoring, sin ranking, sin recomendaciones, sin fase 9C.

**Estado del bloque: `COMPLETED_EUROPE_CANDIDATE_FEATURE_MATRIX_NOT_SCORING`.** 21 candidatos preparados (todos parciales por falta de precio); el mayor salto de cobertura de fundamentales reales de toda la matriz hasta hoy, con las advertencias de entidad-individual-vs-grupo y esquema-bancario-distinto documentadas con total transparencia.
