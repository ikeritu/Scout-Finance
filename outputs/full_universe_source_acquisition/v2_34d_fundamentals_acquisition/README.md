# v2.34D — arquitectura de adquisición de fundamentales (Bloque D, fase 5)

Estado: **`COMPLETED`** — dos adaptadores independientes construidos y probados offline (9/9), sin ninguna descarga real todavía.

## Resultado

- `scripts/download_jquants_fundamentals_v2_34d.py` (J-Quants `/v2/fins/summary`, una llamada por activo, reutiliza el backoff de 429 de v2.33G) y `scripts/download_twse_mops_fundamentals_v2_34d.py` (MOPS opendata, descarga los 4 CSV completos una vez y extrae por código de empresa, sin consulta histórica disponible).
- Contrato de flags común: bloqueado por defecto, `--execute` obligatorio, reanudable, `--limit`/`--asset-id`/`--output-dir`/`--request-delay`/`--max-retries`; `--from-date`/`--to-date` solo donde aplica (no en TWSE).
- Taxonomía de errores cerrada compartida (`scripts/fundamental_adapters/errors.py`).
- Datos crudos fuera de git (añadido a `.gitignore` antes de crear las carpetas).

Detalle completo en `FUNDAMENTALS_ACQUISITION_ARCHITECTURE_v2_34d.md`.
