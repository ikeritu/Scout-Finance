# Scout Finance — Phase 7B.4 Stage 1 Simulator Final Alignment

Generated at: `2026-06-08T10:57:41+00:00`

## Alignment result

- Compared: **500**.
- Matched: **500**.
- Mismatched: **0**.
- Match rate: **100.0%**.

## Scenario comparison

| Scenario | Passed | Watchlist | Rejected | Pass rate | Watchlist rate | Rejection rate |
|---|---:|---:|---:|---:|---:|---:|
| Actual/base final | 226 | 66 | 208 | 45.2% | 13.2% | 41.6% |
| Conservador | 144 | 84 | 272 | 28.8% | 16.8% | 54.4% |
| Equilibrado | 182 | 84 | 234 | 36.4% | 16.8% | 46.8% |
| Agresivo | 266 | 65 | 169 | 53.2% | 13.0% | 33.8% |

## Final price rule

- price < 1: rejected.
- 1 <= price < 3: strong watchlist.
- 3 <= price < 5: weak warning only.
- price >= 5: no price warning.

## Recommendation

The simulator is ready as the decision-support baseline for Stage 1 policy selection. Production filters were not changed.

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- release v0.6 modified: `False`
