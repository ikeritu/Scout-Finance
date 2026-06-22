# Scout Finance — Fase 7C.3: implementación protegida Stage 2 yfinance policy

## Objetivo

Aplicar de forma protegida la política aprobada en 7C.2:

```text
MISSING_SHARES_DILUTION
→ MISSING_SHARES_DILUTION_PROVIDER_LIMITATION
```

La ausencia de `shares_dilution_3y` por limitación de yfinance se registra como warning, pero no bloquea PASSED por sí sola.

## Aplicar

```powershell
.\.venv\Scripts\python.exe scripts/apply_phase7c3_stage2_yfinance_policy.py
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7c3_stage2_yfinance_policy.py
```

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7c3_stage2_yfinance_policy.py
```

## Resultado esperado

```text
PASSED: 63
WATCHLIST: 81
REJECTED: 38
```
