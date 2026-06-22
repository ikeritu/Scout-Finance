# Scout Finance — Phase 7B.1 Stage 1 Policy Simulation

Generated at: `2026-06-08T09:20:30+00:00`

## Executive summary

This report simulates alternative Stage 1 policies without modifying production filters.

## Scenario comparison

| Scenario | Passed | Watchlist | Rejected | Pass rate | Watchlist rate | Rejection rate |
|---|---:|---:|---:|---:|---:|---:|
| Actual/base | 213 | 79 | 208 | 42.6% | 15.8% | 41.6% |
| Conservador | 136 | 92 | 272 | 27.2% | 18.4% | 54.4% |
| Equilibrado | 173 | 93 | 234 | 34.6% | 18.6% | 46.8% |
| Agresivo | 259 | 72 | 169 | 51.8% | 14.4% | 33.8% |

## Recommendation

Recommended next step: use the balanced scenario as the first candidate policy for review, but do not apply it automatically. It raises market-cap and liquidity discipline while preserving small-cap discovery potential. Conservative may be more suitable for institutional-only portfolios; aggressive is useful for early-stage scouting but increases noise.

## Scenario rationale

### Actual/base

Approximation of current Stage 1 thresholds.

- Minimum market cap: `100000000`; watch below `300000000`.
- Minimum price: `1.0`; watch below `5.0`.
- Minimum dollar volume: `500000`; watch below `2000000`.

### Conservador

Higher quality/liquidity bar; fewer but cleaner candidates.

- Minimum market cap: `300000000`; watch below `1000000000`.
- Minimum price: `2.0`; watch below `8.0`.
- Minimum dollar volume: `2000000`; watch below `10000000`.

### Equilibrado

Professional middle ground; keeps small-cap optionality while improving quality.

- Minimum market cap: `150000000`; watch below `500000000`.
- Minimum price: `1.5`; watch below `5.0`.
- Minimum dollar volume: `1000000`; watch below `5000000`.

### Agresivo

More permissive; captures earlier/smaller opportunities with more noise.

- Minimum market cap: `50000000`; watch below `150000000`.
- Minimum price: `0.75`; watch below `2.0`.
- Minimum dollar volume: `250000`; watch below `1000000`.

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- release v0.6 modified: `False`
