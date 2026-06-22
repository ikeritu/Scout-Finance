# Scout Finance — Fase 7D.2: hotfix Count/Nº en Universo institucional

## Problema

En el dashboard de Universo institucional aparece:

```text
KeyError: 'Count'
```

La tabla usa `Nº`, pero el código ordenaba por `Count`.

## Aplicar

```powershell
.\.venv\Scripts\python.exe scripts/apply_phase7d2_institutional_count_hotfix.py
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7d2_institutional_count_hotfix.py
```

## Probar app

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7d2_institutional_count_hotfix.py
```
