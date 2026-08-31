# v2.34F — normalización a `FundamentalRecord` (Bloque F, fase 5)

Estado: **`COMPLETED`** — 50/50 activos normalizados, 10.315 registros, 0 inválidos contra el esquema, 7/7 pruebas offline.

## Resultado

- Dos normalizadores independientes (`scripts/fundamental_adapters/{jquants,twse}_normalizer.py`), ninguno filtra lógica específica de proveedor al esquema canónico.
- Hallazgo del Bloque E aplicado: las divulgaciones `EarnForecastRevision`/`DividendForecastRevision` de J-Quants se excluyen por completo (son guidance, no estados financieros).
- Cobertura real: JPX 56.5% de valores reportados (resto `not_reported_by_company`, nunca cero); TWSE 100%.
- Dataset normalizado (con valores reales) fuera de git; solo el manifiesto agregado de cobertura (`fundamental_coverage_manifest_v2_34f.json`, sin valores) se publica.

Detalle completo en `FUNDAMENTAL_NORMALIZATION_v2_34f.md`.
