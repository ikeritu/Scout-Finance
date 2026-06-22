# Scout Finance — Fase 7B.4: simulador Stage 1 alineado al 100%

## Objetivo

Ajustar la lógica de precio del simulador para reproducir Stage 1 real.

## Regla final

```text
price < 1        -> REJECTED
1 <= price < 3   -> WATCHLIST
3 <= price < 5   -> WEAK_WARNING_ONLY
price >= 5       -> NO_PRICE_WARNING
```

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.simulate_stage1_policy_final
.\.venv\Scripts\python.exe scripts/check_phase7b4_final_simulator.py
```
