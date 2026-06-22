# Scout Finance — Fase 7B.8.1: exact guarded Stage 1 implementation

## Objetivo

Aplicar la política equilibrada en el lugar real del código:

```text
DEFAULT_STAGE1_CONFIG
+
bloque # Price
```

## Aplicar

```powershell
.\.venv\Scripts\python.exe scripts/apply_phase7b8_1_exact_stage1_policy.py
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7b8_1_exact_implementation.py
```

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7b8_1_exact_stage1_policy.py
```
