# v1.5C1 — Scale Test Output Restore Hotfix

## Objetivo

Corregir v1.5C para que el scale test no deje activos los outputs sintéticos de 20/50/100 tickers en la app.

## Problema detectado

v1.5C restauraba:

- `data/real/real_universe.csv`
- `data/real/manual_market_data.csv`

pero dejaba activo:

- `outputs/scouting/active_real_universe_top_candidates.csv`

por lo que la app seguía mostrando 20 filas tras la prueba.

## Solución

v1.5C1 hace backup/restauración de inputs y outputs activos:

- data real
- active candidates
- local score outputs
- ranking explainability outputs
- market data fallback outputs

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.real_universe_scale_test --run
.\.venv\Scripts\python.exe scripts/check_v1_5c1_scale_test_output_restore_hotfix.py
```
