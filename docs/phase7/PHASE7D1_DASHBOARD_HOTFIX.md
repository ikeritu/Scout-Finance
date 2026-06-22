# Scout Finance — Fase 7D.1: dashboard hotfix

## Problema corregido

La llamada al dashboard 7D se ejecutaba antes de definir el helper:

```text
name '_render_phase7d_revalidated_funnel_dashboard' is not defined
```

## Aplicar

```powershell
.\.venv\Scripts\python.exe scripts/apply_phase7d1_dashboard_hotfix.py
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7d1_dashboard_hotfix.py
```

## Probar app

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7d1_dashboard_hotfix.py
```
