# Scout Finance — Phase 7D.2 institutional Count/Nº hotfix

Generated at: `2026-06-09T10:13:39+00:00`

## Result

- Status: **OK**
- app.py modified: **True**
- Backup: `C:\Users\ikeri\proyectos\Scout Finance\app_before_phase7d2_institutional_count_hotfix.py`

## Problem fixed

The institutional universe dashboard displayed a table using the Spanish count column:

```text
Nº
```

but attempted to sort by:

```text
Count
```

This caused:

```text
KeyError: 'Count'
```

## Applied changes

- REPLACED_SORT_COUNT_WITH_N_IN_INSTITUTIONAL_DASHBOARD_1
- PHASE7D2_MARKER_ADDED

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7d2_institutional_count_hotfix.py
```

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- filters modified: `False`
- release modified: `False`
