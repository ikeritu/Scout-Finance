# Scout Finance v2.34F — normalización a `FundamentalRecord` (Bloque F, fase 5)

Fecha: 2026-08-31. Alcance: **normalizar los datos reales ya adquiridos en el Bloque E hacia el esquema canónico del Bloque C**. Sin red, sin credenciales. Los normalizadores son independientes por fuente (ningún parámetro específico de un proveedor se filtra al esquema canónico), y preservan siempre el valor original (`raw_value`, `raw_metric`, `raw_currency`) junto al normalizado.

## Normalizadores construidos

| Módulo | Fuente | Entrada | Salida |
|---|---|---|---|
| `scripts/fundamental_adapters/jquants_normalizer.py` | J-Quants `/v2/fins/summary` | JSON crudo del Bloque D/E | `FundamentalRecord` por divulgación × métrica × ámbito de consolidación |
| `scripts/fundamental_adapters/twse_normalizer.py` | MOPS opendata | JSON crudo del Bloque D/E | `FundamentalRecord` por empresa × métrica |

Orquestador: `scripts/build_fundamental_dataset_v2_34f.py` — corre ambos normalizadores sobre las colecciones reales, escribe el conjunto completo de registros normalizados en local (`fundamental_records_v2_34f.jsonl`, **fuera de git**, añadido a `.gitignore` antes de crearse: sigue conteniendo valores reales con licencia del proveedor) y un manifiesto de cobertura agregado (`fundamental_coverage_manifest_v2_34f.json`, **sí committeado**: solo recuentos y nombres de métricas, ningún valor).

## Decisiones de diseño no triviales

1. **Exclusión explícita de `EarnForecastRevision`/`DividendForecastRevision`** (hallazgo del Bloque E): el normalizador J-Quants descarta estas divulgaciones por completo (`normalize_disclosure` retorna `[]`) antes de generar ningún registro. Son guidance del proveedor, no un estado financiero — incluirlas habría exigido `value_status="estimated"`, prohibido por la regla 3.1.
2. **Separación consolidado/no consolidado como registros distintos, no columnas paralelas**: J-Quants reporta simultáneamente cifras consolidadas y no consolidadas (columnas `NC*`) para la misma métrica. En vez de inventar un id de métrica nuevo, se emiten dos registros con el mismo `metric` y `consolidation_scope` distinto — así lo previó el esquema del Bloque C.
3. **Blanco del proveedor ≠ cero**: un campo vacío (`""`) del proveedor se convierte siempre en `value=None` + `missing_reason="not_reported_by_company"`, nunca en `0.0`. Verificado con datos reales: 4.451 de 10.227 registros JPX quedan así (43.5%), reflejando que muchos campos (p. ej. `CFO`/`BPS`) solo se reportan en ciertos tipos de periodo, no en todos.
4. **`currency` se anula cuando el valor es nulo o cuando la unidad no es monetaria** (acciones, ratios): un valor ausente no puede llevar una etiqueta de moneda, y un recuento de acciones o un ratio no tiene moneda propia. Esta regla se detectó inconsistente entre los dos normalizadores durante las pruebas de este mismo bloque (el normalizador J-Quants inicialmente dejaba `currency="JPY"` en un campo monetario ausente) y se corrigió antes del cierre — ver evidencia en las pruebas.
5. **Escala TWSE confirmada, no asumida**: `t187ap06_L_ci`/`t187ap07_L_ci` están en miles de NTD (confirmado en v2.34D cruzando contra `t187ap17_L`, que expresa ingresos en millones). `value = raw_value × 1000`; `raw_value` conserva la cifra original del proveedor.
6. **`period_end` derivado por calendario, no asumido sobre el contenido**: MOPS no da fechas de periodo explícitas, solo año ROC + trimestre. El fin de trimestre calendario (`Q2` → `30 de junio`) es aritmética de calendario, no una suposición sobre lo que la empresa reportó — se documenta como tal.
7. **Limitación marcada explícitamente, no resuelta por conveniencia**: no está confirmado si las cifras de MOPS son del trimestre discreto o acumuladas desde el inicio del ejercicio (práctica común en Taiwán). Cada registro TWSE lleva el `quality_flag` `period_cumulative_vs_discrete_unconfirmed` en vez de asumir una de las dos.

## Resultado real (evidencia, `fundamental_coverage_manifest_v2_34f.json`)

- **50/50 activos cubiertos** (42 JPX + 8 TWSE).
- **10.315 registros `FundamentalRecord`** generados en total (10.227 JPX + 88 TWSE).
- **0 registros inválidos contra el esquema** (`schema.validate_record()` sobre los 10.315, no una muestra).
- JPX: 5.776 registros con valor real (56.5%), 4.451 con `missing_reason="not_reported_by_company"` (43.5%) — la asimetría de fuentes ya prevista en v2.34B (campos que solo aplican a según qué tipo de periodo o empresa).
- TWSE: 88/88 registros con valor real (100%) — consistente con que MOPS reporta el estado financiero completo, no un resumen.

## Pruebas offline

`tests/qa_fundamental_normalizers_v2_34f.py` — 7 casos, sin red, sin datos reales (fixtures sintéticas), cada registro producido validado contra el `schema.validate_record()` real:

1. Un valor reportado y un campo en blanco en la misma divulgación se distinguen correctamente (`value`/`missing_reason` mutuamente excluyentes; moneda anulada en el campo ausente).
2. Una divulgación `EarnForecastRevision` se descarta por completo.
3. El indicador de restatement (`ChgByASRev`) se detecta correctamente y el split consolidado/no-consolidado genera dos registros independientes.
4. Un valor no parseable (`"not_a_number"`) se marca `incomplete_response`/`normalization_error`, nunca se descarta silenciosamente ni se convierte en 0.
5. Reproducibilidad determinista de principio a fin sobre un fichero crudo de fixture.
6. TWSE: conversión de escala (miles → unidades) y derivación de `period_end` por calendario, ambas correctas contra un valor real conocido (71.289.957 miles → 71.289.957.000 TWD).
7. TWSE: un campo en blanco recibe `missing_reason`, nunca cero.

```
.venv/Scripts/python.exe -m py_compile scripts/fundamental_adapters/jquants_normalizer.py scripts/fundamental_adapters/twse_normalizer.py scripts/build_fundamental_dataset_v2_34f.py tests/qa_fundamental_normalizers_v2_34f.py
.venv/Scripts/python.exe tests/qa_fundamental_normalizers_v2_34f.py
PASS: v2.34F-fundamental-normalizers/schema-valid/no-synthetic-values/forecast-revision-exclusion/scale-conversion
.venv/Scripts/python.exe scripts/build_fundamental_dataset_v2_34f.py
{"status": "COMPLETED", "assets_covered": 50, "total_records": 10315, "total_invalid_schema_records": 0}
```

Verificado además: dos ejecuciones consecutivas de `build_fundamental_dataset_v2_34f.py` producen un manifiesto de cobertura byte-idéntico.

## Seguridad y alcance

- Ningún valor real de fundamentales se ha comiteado: el JSONL normalizado está en `.gitignore` (añadido antes de crearse). Solo el manifiesto agregado (recuentos, nombres de métrica, sin cifras) se publica.
- Sin red, sin credenciales en este bloque.
- `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: `COMPLETED`.** Los 10.315 registros normalizados y validados contra el esquema quedan listos para el Bloque G (métricas derivadas) y el Bloque H (validación económica/contable y score de calidad).
