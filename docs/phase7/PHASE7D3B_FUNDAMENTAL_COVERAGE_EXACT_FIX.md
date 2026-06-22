# Scout Finance — Fase 7D.3b: corrección exacta cobertura fundamental

## Problema

El bloque real está en `app.py` alrededor de:

```python
summary = _sf6f_build_fundamental_enrichment_summary()
```

Ese summary seguía devolviendo los valores antiguos 4 / 4 / 100% / 6E.

## Aplicar

```powershell
.\.venv\Scripts\python.exe scripts/apply_phase7d3b_fundamental_coverage_exact_fix.py
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7d3b_fundamental_coverage_exact_fix.py
```

## Probar app

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7d3b_fundamental_coverage_exact_fix.py
```
