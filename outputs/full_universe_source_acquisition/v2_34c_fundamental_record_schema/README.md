# v2.34C — esquema canónico de fundamentales (Bloque C, fase 5)

Estado: **`COMPLETED`** — contrato de datos diseñado, implementado y probado offline (9/9 pruebas).

## Resultado

- Esquema JSON (`schemas/fundamental_record_v1.schema.json`) + dataclass Python (`scripts/fundamental_adapters/schema.py`) para `FundamentalRecord`, formato long (una fila por observación).
- Catálogo cerrado de 29 métricas (`config/fundamental_metrics_v1.json`), cada una etiquetada `reported`/`calculated` y con las fuentes que realmente la reportan según v2.34B. Varias métricas de deuda/capex/FCF quedan `reported_by: []` en ambas fuentes — bloqueadas para el Bloque G, no aproximadas.
- Catálogo cerrado de 10 motivos de ausencia (`config/fundamental_missing_reasons_v1.json`).
- `value_status="estimated"` prohibido en código (regla 3.1: no valores sintéticos), aunque queda en el enum del esquema para poder fallar explícitamente si apareciera.

Detalle completo en `FUNDAMENTAL_RECORD_SCHEMA_v2_34c.md`. Documentación de contrato y ejemplos válidos/rechazados en `docs/fundamentals/FUNDAMENTAL_DATA_CONTRACT_v2_34c.md`.
