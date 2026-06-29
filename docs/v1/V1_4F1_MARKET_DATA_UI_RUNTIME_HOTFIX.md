# v1.4F1 — Market Data UI Runtime Hotfix

## Objetivo

Corregir el error de runtime de v1.4F:

`NameError: name '_sf14f_is_market_data_row' is not defined`

## Causa

Los helpers de v1.4F quedaron definidos demasiado tarde en `app.py`, después de la llamada a `main()`.

## Cambios

- Define los helpers antes de `_render_company_detail`.
- Mantiene la integración UI de market data.
- No cambia datos, scoring, proveedores ni outputs.

## Validación

```powershell
.\.venv\Scripts\python.exe scripts/check_v1_4f1_market_data_ui_runtime_hotfix.py
```
