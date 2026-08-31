# v2.33Q — arquitectura multifuente mínima (Bloque F, fase 4)

Estado: construida y verificada contra datos reales (50 activos, JPX + TWSE).

## Resultado

- Esquema canónico `PriceRecord` (20 campos) en `scripts/price_adapters/schema.py`, distingue explícitamente sin-operación / no-aplica / no-disponible-por-licencia.
- Adaptadores de normalización para J-Quants y TWSE, sin tocar red ni credenciales — reutilizan los descargadores ya probados de v2.33G/v2.33I.
- Manifiesto de cobertura reproducible (`coverage_manifest_v2_33q.json`) generado desde datos reales locales.
- QA offline sin red (`tests/qa_price_adapters_schema_v2_33q.py`).

## Archivos

- `scripts/price_adapters/schema.py`, `jquants_adapter.py`, `twse_adapter.py`.
- `scripts/build_coverage_manifest_v2_33q.py`.
- `tests/qa_price_adapters_schema_v2_33q.py`.
- `coverage_manifest_v2_33q.json`: manifiesto agregado (sin precios fila a fila).
- `MULTISOURCE_ARCHITECTURE_v2_33q.md`: detalle completo F1–F5.
