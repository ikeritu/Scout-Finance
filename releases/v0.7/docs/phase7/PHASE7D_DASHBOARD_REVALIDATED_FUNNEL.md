# Scout Finance — Fase 7D: integración del funnel real revalidado en dashboard/app

## Objetivo

Integrar en `app.py` un bloque visual con:

```text
500 → 182 → 63 → 6
```

Incluye:

- políticas activas;
- métricas de Stage 1, Stage 2 y Stage 3;
- top candidates revalidadas;
- aviso profesional sobre `shares_dilution_3y` como limitación de yfinance.

## Aplicar

```powershell
.\.venv\Scripts\python.exe scripts/apply_phase7d_dashboard_revalidated_funnel.py
```

## Validar

```powershell
.\.venv\Scripts\python.exe scripts/check_phase7d_dashboard_revalidated_funnel.py
```

## Probar app

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7d_dashboard_revalidated_funnel.py
```
