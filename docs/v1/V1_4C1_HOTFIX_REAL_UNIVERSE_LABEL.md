# v1.4C1 Hotfix — Real Universe Label

## Objetivo

Corregir el fallo del checker v1.4C1: el app.py seguía etiquetando internamente `active_real_universe_top_candidates.csv` como `revalidated_funnel`.

## Cambios

- `active_real_universe_top_candidates.csv` y `real_universe_candidates.csv` ahora se marcan como `real_universe_input`.
- Dashboard muestra `Universo real input`.
- Avisos mencionan `INPUT_ONLY` y no scoring financiero real.
- Se mantiene el fallback antiguo solo para el funnel revalidado real.

## Validación

```powershell
.\.venv\Scripts\python.exe scripts/check_v1_4c1_hotfix_real_universe_label.py
```
