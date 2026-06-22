# Scout Finance — Phase 7B.8 Guarded Stage 1 Implementation

Generated at: `2026-06-08T13:40:58+00:00`

## Result

- Status: **MISMATCH**.
- Stage 1 run OK: **True**.
- Matches dry-run: **False**.

## Counts

| Bucket | Expected dry-run | Actual after patch |
|---|---:|---:|
| Passed | 182 | 226 |
| Watchlist | 84 | 66 |
| Rejected | 234 | 208 |

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7b8_stage1_policy.py
```
