# Scout Finance — Phase 7B.5 Stage 1 Candidate Policy Decision

Generated at: `2026-06-08T11:07:09+00:00`

## Decision

Recommended candidate policy: **Equilibrado**.

Select the balanced policy as the Stage 1 candidate for a guarded dry-run. Do not apply it to production yet.

## Scenario comparison

| Scenario | Passed | Watchlist | Rejected | Pass rate | Watchlist rate | Rejection rate | Score | Recommendation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Equilibrado | 182 | 84 | 234 | 36.4% | 16.8% | 46.8% | 96.44 | CANDIDATE |
| Actual/base final | 226 | 66 | 208 | 45.2% | 13.2% | 41.6% | 81.8 | BASELINE |
| Conservador | 144 | 84 | 272 | 28.8% | 16.8% | 54.4% | 81.7 | ALTERNATIVE_STRICT |
| Agresivo | 266 | 65 | 169 | 53.2% | 13.0% | 33.8% | 65.34 | NOT_RECOMMENDED |

## Why balanced is the candidate

- It reduces pass-through noise versus current/base.
- It keeps enough companies for discovery.
- It is not as restrictive as conservative.
- It is more professionally defensible than aggressive.

## Important control

This phase does **not** modify production filters. It only selects a candidate policy for a guarded dry-run.

## Next step

Run Phase 7B.6: guarded dry-run of the balanced Stage 1 policy against the 500-company batch.

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- release modified: `False`
