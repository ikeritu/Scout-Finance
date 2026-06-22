# Scout Finance — Phase 7D v2 dashboard revalidated funnel integration

Generated at: `2026-06-09T09:46:11+00:00`

## Result

- Status: **OK**
- app.py modified: **True**
- Backup: `C:\Users\ikeri\proyectos\Scout Finance\app_before_phase7d_dashboard_revalidated_funnel.py`

## Dashboard content integrated

- Funnel: `500 → 182 → 63 → 6`
- Stage 1 policy: `Balanced official policy`
- Stage 2 policy: `yfinance-aligned provider-limitation policy`
- Stage 3 policy: `Existing Stage 3 opportunity scoring policy`
- Top candidates rows available: `20`

## Applied changes

- PHASE7D_HELPERS_APPENDED
- PHASE7D_RENDER_CALL_INSERTED

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7d_dashboard_revalidated_funnel.py
```

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- filters modified: `False`
- release modified: `False`
