# Scout Finance — Fase 7B.8: guarded implementation patch

## Objetivo

Aplicar política equilibrada en `src/filter_stage1.py` con backup y validación contra dry-run 7B.6.

## Aplicar

```powershell
.\.venv\Scripts\python.exe scripts/apply_phase7b8_guarded_stage1_policy.py
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7b8_guarded_implementation.py
```

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7b8_stage1_policy.py
```
