# Scout Finance v2.34C — esquema canónico de fundamentales (Bloque C, fase 5)

Fecha: 2026-08-31. Alcance: **solo diseño, código y pruebas offline** — ninguna llamada de red, ninguna credencial usada. Este bloque construye el contrato de datos que los bloques D-J deberán respetar; no descarga ni normaliza ningún dato real todavía.

## C.1-C.4 — Esquema formal

Contrato en `schemas/fundamental_record_v1.schema.json` (JSON Schema draft 2020-12, `additionalProperties: false`). Un `FundamentalRecord` es **una fila por observación** (activo, periodo fiscal, métrica) — no una tabla ancha por empresa-periodo — siguiendo el mismo patrón long-format ya usado para `PriceRecord` en la fase 4 (v2.33Q).

Grupos de campos, tal como exige el encargo:

- **Identidad/procedencia**: `asset_id`, `pilot_id`, `ticker`, `provider_symbol`, `company_name`, `exchange`, `country`, `provider`, `source_url_or_endpoint` (solo la ruta del endpoint, nunca una URL completa con credencial), `retrieved_at`, `normalizer_version`.
- **Periodo fiscal**: `statement_type`, `period_type` (`annual` | `quarterly` | `semiannual` | `ttm` | `instant` — nunca mezclados dentro de un mismo registro), `fiscal_year`, `fiscal_quarter`, `period_start`, `period_end`, `filing_date`, `publication_date`, `restatement_status`, `consolidation_scope`, `accounting_standard`.
- **Valor/unidad**: `metric` (id canónico), `raw_metric` (nombre literal del proveedor), `value`, `raw_value`, `currency`, `raw_currency`, `unit`, `scale`, `sign_convention`, `value_status`.
- **Estado/calidad**: `source_status`, `normalization_status`, `validation_status`, `missing_reason`, `quality_flags`, `transformation_notes`.

Espejo en código: `scripts/fundamental_adapters/schema.py`, un `dataclass` congelado que refleja el JSON Schema campo a campo, más `validate_record(record: dict) -> list[str]` como la única función de validación real (usa `jsonschema.Draft202012Validator` contra el fichero JSON — el JSON es la fuente de verdad, el dataclass es solo el envoltorio cómodo en Python).

## C.5 — Catálogo de métricas mínimas

`config/fundamental_metrics_v1.json`: 29 métricas canónicas cubriendo cuenta de resultados, balance, flujo de caja y rentabilidad/márgenes. Cada métrica declara `statement`, `kind` (`reported` | `calculated`) y `reported_by` — la lista de fuentes aprobadas (`jquants_fins_summary`, `twse_mops_opendata`) que de verdad la reportan, según lo confirmado empíricamente en v2.34B, no lo asumido.

Consecuencia directa de la asimetría de fuentes documentada en v2.34B: varias métricas quedan con `reported_by: []` en **ambas** fuentes aprobadas —

| Métrica | Motivo |
|---|---|
| `current_debt`, `noncurrent_debt` | Ninguna fuente gratuita aprobada desglosa deuda financiera corriente/no corriente (el desglose de JPX vive tras `/fins/details`, de pago, descartado) |
| `gross_debt`, `net_debt` (calculadas) | Dependen de `current_debt`/`noncurrent_debt` — bloqueadas mientras estos no existan |
| `capex` | No es un campo distinto en `/fins/summary` (solo `CFI` agregado) ni en los ficheros MOPS evaluados |
| `free_cash_flow` (calculada) | Depende de `capex` — bloqueada por la misma razón |
| `buybacks` | No confirmado en ninguna fuente |

Estas métricas no se eliminan del catálogo: se declaran explícitamente vacías para que el Bloque G las marque `calculation_impossible_missing_components` en vez de aproximarlas o inventarlas.

## C.6 — Documentación, ejemplos y pruebas

- Documentación de campos, reglas de moneda/escala/signo y ejemplos válidos/rechazados: [`docs/fundamentals/FUNDAMENTAL_DATA_CONTRACT_v2_34c.md`](../../../docs/fundamentals/FUNDAMENTAL_DATA_CONTRACT_v2_34c.md).
- Pruebas automáticas del esquema: `tests/qa_fundamental_schema_v2_34c.py` — 9 casos, sin red: 1 registro válido con valor, 1 registro válido con `value=None` + `missing_reason` correcto, y 7 casos deliberadamente rechazados (valor nulo sin motivo, código de motivo inventado, valor y motivo presentes a la vez, `value_status="estimated"` prohibido, métrica canónica desconocida, valor de enum fuera de catálogo). Resultado: **9/9 PASS**.

```
.venv/Scripts/python.exe -m py_compile scripts/fundamental_adapters/schema.py tests/qa_fundamental_schema_v2_34c.py
.venv/Scripts/python.exe tests/qa_fundamental_schema_v2_34c.py
PASS: v2.34C-fundamental-schema/valid-and-rejected-examples/closed-catalogs/no-estimated-values
```

## Decisiones deliberadas de diseño

1. **`value_status="estimated"` queda en el enum del JSON Schema pero prohibido en código** (`validate_record` lo rechaza explícitamente citando la regla 3.1 del encargo, "no valores sintéticos"). Se mantiene en el enum a propósito: si algún día se colara un valor así, el código tiene algo tipado contra lo que fallar, con un mensaje explicativo, en vez de que el propio enum lo prohibiera y produjera un error de validación de esquema genérico y menos claro.
2. **Nunca ambos `value` y `missing_reason` a la vez, nunca ninguno de los dos**: exactamente uno debe estar presente. Esto es lo que impide el patrón que la regla 3.1 prohíbe explícitamente — convertir silenciosamente una ausencia en cero o en un hueco sin explicar.
3. **Sin conversión de moneda automática**: `currency`/`raw_currency` se guardan tal cual llegan del proveedor (JPY o TWD); no hay ningún paso de FX en este bloque ni está previsto en el Bloque F.
4. **`company_id` (LEI/ISIN cruzado)** se deja como `null` reservado para una fase futura — no se fabrica ningún identificador que no esté ya confirmado.

## Seguridad y alcance

- Cero llamadas de red, cero credenciales usadas.
- Ningún fichero de datos reales creado; solo esquema, catálogos, código y pruebas con datos ficticios.
- `production_scoring_authorized: false`, `allow_ranking: false`.

**Estado del bloque: `COMPLETED`.** El contrato queda cerrado y probado; los bloques D (adaptadores de adquisición) y F (normalizadores) deben ajustarse a este esquema exactamente, sin extenderlo de manera ad hoc.
