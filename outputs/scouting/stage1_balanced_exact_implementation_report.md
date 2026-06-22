# Scout Finance — Phase 7B.8.1 Exact Stage 1 Implementation

Generated at: `2026-06-08T14:41:20+00:00`

## Result

- Status: **OK**.
- Stage 1 run OK: **True**.
- Matches dry-run: **True**.

## Counts

| Bucket | Expected dry-run | Actual after exact patch |
|---|---:|---:|
| Passed | 182 | 182 |
| Watchlist | 84 | 84 |
| Rejected | 234 | 234 |

## Applied changes

- ALREADY_APPLIED

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7b8_1_exact_stage1_policy.py
```

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- release modified: `False`
- filter_stage1.py modified: `True`
