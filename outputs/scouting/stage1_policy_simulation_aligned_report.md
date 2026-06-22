# Scout Finance — Phase 7B.3 Aligned Stage 1 Policy Simulator

Generated at: `2026-06-08T10:33:51+00:00`

## Alignment result

- Compared: **500**.
- Matched: **495**.
- Mismatched: **5**.
- Match rate: **99.0%**.

## Scenario comparison

| Scenario | Passed | Watchlist | Rejected | Pass rate | Watchlist rate | Rejection rate |
|---|---:|---:|---:|---:|---:|---:|
| Actual/base alineado | 231 | 61 | 208 | 46.2% | 12.2% | 41.6% |
| Conservador | 145 | 83 | 272 | 29.0% | 16.6% | 54.4% |
| Equilibrado | 185 | 81 | 234 | 37.0% | 16.2% | 46.8% |
| Agresivo | 268 | 63 | 169 | 53.6% | 12.6% | 33.8% |

## Rule correction

PRICE_WATCHLIST_RANGE is now treated as a weak warning. It does not create WATCHLIST by itself.
A company below the watch price can still pass if market cap and dollar volume are healthy.

## Recommendation

Use this aligned simulator as the decision-support tool for Stage 1 policy review. Do not modify production filters until a scenario is selected and validated.

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- release v0.6 modified: `False`
