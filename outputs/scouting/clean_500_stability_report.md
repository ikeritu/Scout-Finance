# Scout Finance — Phase 7A.6 Clean 500 Stability Report

Generated at: `2026-06-08T08:39:46+00:00`

## Core metrics

| Metric | Value |
|---|---:|
| Limit | 500 |
| Market-data processed rows | 500 |
| Market-data success | 498 |
| Market-data success rate | 99.6% |
| Market-data failed/incomplete | 2 |
| Stage 1 input | 500 |
| Stage 1 passed | 226 |
| Stage 1 watchlist | 66 |
| Stage 1 rejected | 208 |
| Stage 1 pass rate | 45.2% |
| Stage 1 watchlist rate | 13.2% |
| Stage 1 rejection rate | 41.6% |

## Stage 1 rejection distribution

| Reason code | Count |
|---|---:|
| MARKET_CAP_BELOW_MINIMUM | 171 |
| LOW_DOLLAR_VOLUME | 132 |
| PRICE_WATCHLIST_RANGE | 98 |
| DOLLAR_VOLUME_WATCHLIST_RANGE | 71 |
| MARKET_CAP_WATCHLIST_RANGE | 68 |
| PRICE_BELOW_MINIMUM | 39 |
| MISSING_MARKET_CAP | 2 |

## Controls

- OpenAI called: `False`
- Paid API called: `False`
- yfinance called: `True`
- app.py modified: `False`
- release v0.6 modified: `False`

## Interpretation

This phase is a scale/stability test. It does not yet evaluate fundamentals.
Companies that pass Stage 1 are investable-universe candidates, not final investment recommendations.
