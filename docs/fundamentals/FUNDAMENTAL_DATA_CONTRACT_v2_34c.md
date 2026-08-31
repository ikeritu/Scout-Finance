# Scout Finance — contrato de datos `FundamentalRecord` v1 (v2.34C, Bloque C fase 5)

Este documento describe el contrato formal para cualquier observación de fundamentales en Scout Finance a partir de la fase 5. La fuente de verdad es `schemas/fundamental_record_v1.schema.json` (JSON Schema draft 2020-12); este documento es su explicación legible por humanos, no un sustituto. El código valida contra el JSON, no contra este texto.

## Forma del registro

Un `FundamentalRecord` es **una fila por observación**: (activo, tipo de estado financiero, periodo fiscal, métrica). Una empresa con 10 métricas para un trimestre produce 10 registros, no uno ancho con 10 columnas. Esto permite mezclar fuentes con cobertura de métricas distinta (J-Quants y MOPS reportan conjuntos de campos que se solapan solo parcialmente, ver v2.34B) sin forzar un esquema ancho que tendría que inventar columnas vacías.

## Grupos de campos

### Identidad y procedencia
`asset_id`, `pilot_id`, `ticker`, `provider_symbol`, `company_name`, `exchange` (`JPX`|`TWSE`), `country` (`JP`|`TW`), `provider` (`jquants_fins_summary`|`twse_mops_opendata`), `source_url_or_endpoint` (solo la ruta, p. ej. `/v2/fins/summary` — nunca una URL completa que pudiera llevar una clave como parámetro), `retrieved_at`, `normalizer_version`.

### Periodo fiscal
`statement_type` ∈ {`income_statement`, `balance_sheet`, `cash_flow`, `derived_reported_by_provider`}. `period_type` ∈ {`annual`, `quarterly`, `semiannual`, `ttm`, `instant`} — un registro nunca mezcla dos tipos de periodo. `fiscal_year`, `fiscal_quarter`, `period_start`, `period_end`, `filing_date`, `publication_date`, `restatement_status` (`original`|`restated`|`unknown`), `consolidation_scope` (`consolidated`|`non_consolidated`|`unknown`), `accounting_standard` (`JGAAP`|`IFRS`|`USGAAP`|`ROC_GAAP`|`unknown`).

### Valor y unidad
`metric` (id canónico del catálogo, p. ej. `revenue`, `net_debt`), `raw_metric` (el nombre literal que usa el proveedor, p. ej. `Sales`, `營業收入`), `value` (ya normalizado a la unidad estándar del proyecto para esa métrica), `raw_value` (el valor original del proveedor, sin tocar), `currency`/`raw_currency` (`JPY`|`TWD`|`null` — **nunca se convierte de moneda en la ingesta**), `unit` ∈ {`currency`, `shares`, `currency_per_share`, `percent`, `ratio`, `days`, `count`}, `scale` ∈ {`units`, `thousands`, `millions`, `unknown`}, `sign_convention` ∈ {`natural`, `expense_positive`, `expense_negative`}, `value_status` ∈ {`ok`, `estimated`, `provider_reported_only`, `calculated`}.

### Estado y calidad
`source_status` (qué pasó al pedir el dato: `received`, `http_error`, `auth_error`, `rate_limited`, `timeout`, `empty_response`, `identity_mismatch`, `schema_mismatch`, `provider_error`, `license_block`), `normalization_status` (`normalized`|`normalization_error`|`not_attempted`), `validation_status` (`pending`|`passed`|`flagged`|`rejected`), `missing_reason` (código del catálogo cerrado, obligatorio si `value` es `null`), `quality_flags` (lista libre de banderas, p. ej. `["fiscal_quarter_estimated_from_period_end"]`), `transformation_notes`.

## Reglas de moneda, escala y signo

- **Moneda**: se preserva tal cual el proveedor la entrega (`JPY` para J-Quants, `TWD` para MOPS). No existe ningún paso de conversión de divisas en la fase 5; si en el futuro se necesitara, sería una capa derivada documentada aparte, nunca silenciosa durante la ingesta.
- **Escala**: cada proveedor expresa las cifras en una escala distinta (unidades, miles, millones); `scale` registra la escala **original** del proveedor y `value` ya viene normalizado a unidades enteras del proyecto — así un `1500` en `raw_value` con `scale="thousands"` se normaliza a `value=1500000`.
- **Signo**: `sign_convention` documenta si los gastos llegan en positivo (`expense_positive`, forma natural de la mayoría de cuentas de resultados) o si el proveedor ya los reporta en negativo (`expense_negative`). Esto evita que un normalizador aplique un signo incorrecto asumiendo la convención equivocada.

## La regla de oro: `value` y `missing_reason` son mutuamente excluyentes y colectivamente exhaustivos

- Si `value` no es `null`: `missing_reason` **debe** ser `null`.
- Si `value` es `null`: `missing_reason` **debe** ser uno de los 10 códigos cerrados de `config/fundamental_missing_reasons_v1.json` (`not_reported_by_company`, `not_applicable`, `not_available_from_provider`, `incomplete_response`, `identity_error`, `provider_error`, `normalization_error`, `rejected_by_qa`, `calculation_impossible_missing_components`, `coverage_unknown`).

Esta es la regla que impide el patrón que la regla 3.1 del encargo prohíbe explícitamente: convertir silenciosamente una ausencia de dato en un cero, o dejarla como un hueco sin explicar por qué falta.

## `value_status="estimated"` está prohibido en la práctica

El enum del JSON Schema conserva `estimated` como valor válido de forma, pero `scripts/fundamental_adapters/schema.py::validate_record()` lo rechaza explícitamente citando la regla 3.1 ("no valores sintéticos"). Se mantiene en el enum a propósito — es una decisión de diseño, no un descuido — para que, si algún registro llegara alguna vez con ese estado, el código tenga algo tipado contra lo que fallar con un mensaje claro ("forbidden ... rule 3.1"), en lugar de que el propio esquema lo bloqueara con un error de validación genérico y menos explicable. Ningún adaptador de los bloques D/F debe producir jamás este valor.

## Ejemplo válido — valor presente

```json
{
  "schema_version": "1.0.0",
  "record_id": "sha256:...",
  "asset_id": "P143", "pilot_id": "P143", "ticker": "1301",
  "provider_symbol": "13010", "company_name": "KYOKUYO CO.,LTD.",
  "exchange": "JPX", "country": "JP",
  "provider": "jquants_fins_summary", "source_url_or_endpoint": "/v2/fins/summary",
  "retrieved_at": "2026-08-31T00:00:00+00:00", "normalizer_version": "1.0.0",
  "statement_type": "income_statement", "period_type": "quarterly",
  "fiscal_year": "2026", "fiscal_quarter": 1,
  "period_start": "2026-01-01", "period_end": "2026-03-31",
  "restatement_status": "original", "consolidation_scope": "consolidated",
  "accounting_standard": "JGAAP",
  "metric": "revenue", "raw_metric": "Sales",
  "value": 1000000.0, "raw_value": 1000000.0,
  "currency": "JPY", "raw_currency": "JPY",
  "unit": "currency", "scale": "units", "sign_convention": "natural",
  "value_status": "ok",
  "source_status": "received", "normalization_status": "normalized",
  "validation_status": "passed", "missing_reason": null, "quality_flags": []
}
```

## Ejemplo válido — ausencia declarada

Igual que arriba pero para una métrica que J-Quants no reporta (p. ej. `current_debt`):

```json
{
  "...": "... mismos campos de identidad/periodo ...",
  "metric": "current_debt", "raw_metric": "n/a",
  "value": null, "raw_value": null,
  "currency": null, "raw_currency": null,
  "value_status": "ok",
  "missing_reason": "not_available_from_provider",
  "quality_flags": []
}
```

## Ejemplos rechazados (probados en `tests/qa_fundamental_schema_v2_34c.py`)

| Caso | Por qué se rechaza |
|---|---|
| `value: null`, `missing_reason: null` | Ausencia sin explicar — exactamente lo que la regla 3.1 prohíbe |
| `missing_reason: "made_up_reason"` | No está en el catálogo cerrado de 10 códigos |
| `value: 1000000.0`, `missing_reason: "not_reported_by_company"` | Valor y motivo de ausencia a la vez — deben ser mutuamente excluyentes |
| `value_status: "estimated"` | Prohibido explícitamente por regla de negocio, aunque el enum del esquema lo permitiría por forma |
| `metric: "totally_made_up_metric"` | No existe en `config/fundamental_metrics_v1.json` |
| `exchange: "NASDAQ"` | Fuera del enum cerrado (`JPX`\|`TWSE`) — la fase 5 no cubre otros mercados |

Ejecutar las pruebas:

```
.venv/Scripts/python.exe tests/qa_fundamental_schema_v2_34c.py
```
