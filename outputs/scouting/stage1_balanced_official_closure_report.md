# Scout Finance — Phase 7B.9 Stage 1 Balanced Official Closure

Generated at: `2026-06-08T18:43:18+00:00`

## Official status

- Active Stage 1 policy: **balanced**.
- Status: **OK**.
- Ready for v0.7 checkpoint: **True**.
- Recommended next phase: **7C — Revalidate Stage 2 / Stage 3 / candidates with Stage 1 Balanced active**.

## Confirmed counts

| Bucket | Expected | Actual |
|---|---:|---:|
| Passed | 182 | 182 |
| Watchlist | 84 | 84 |
| Rejected | 234 | 234 |

## Active Balanced policy

```text
market_cap rejected below 150M
market_cap watchlist below 500M
price rejected below 1.5
price strong watchlist from 1.5 to below 3
price weak warning from 3 to below 5
dollar volume rejected below 1M
dollar volume watchlist below 5M
```

## Rollback

```powershell
.\.venv\Scripts\python.exe scripts/rollback_phase7b8_1_exact_stage1_policy.py
```

Backup:

```text
C:\Users\ikeri\proyectos\Scout Finance\src\filter_stage1_before_phase7b8_1_exact.py
```

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- release modified: `False`
- filter_stage1.py modified: `True`
