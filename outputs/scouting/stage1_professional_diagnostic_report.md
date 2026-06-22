# Scout Finance — Phase 7B Stage 1 Professional Diagnostic

Generated at: `2026-06-08T09:13:13+00:00`

## Executive summary

- Stage 1 input: **500** companies.
- Passed: **226** (45.2%).
- Watchlist: **66** (13.2%).
- Rejected: **208** (41.6%).

## Numeric profile

### Passed

- **market_cap**: median `1829743296.0`, p25 `813871264.0`, p75 `5885543808.0`.
- **price**: median `29.27`, p25 `11.5625`, p75 `79.905`.
- **dollar_volume_90d**: median `26991102.525`, p25 `8924241.6275`, p75 `82533267.7125`.

### Watchlist

- **market_cap**: median `231209232.0`, p25 `154352508.0`, p75 `423648560.0`.
- **price**: median `5.92`, p25 `2.7425`, p75 `11.0675`.
- **dollar_volume_90d**: median `1788522.585`, p25 `1130723.46`, p75 `3803093.1625`.

### Rejected

- **market_cap**: median `34091560.0`, p25 `10346569.5`, p75 `83182928.0`.
- **price**: median `2.18`, p25 `1.1088`, p75 `5.6625`.
- **dollar_volume_90d**: median `276074.009`, p25 `97550.1582`, p75 `1081231.0073`.

## Top rejection reasons

| Reason code | Count |
|---|---:|
| MARKET_CAP_BELOW_MINIMUM | 171 |
| LOW_DOLLAR_VOLUME | 132 |
| PRICE_WATCHLIST_RANGE | 98 |
| DOLLAR_VOLUME_WATCHLIST_RANGE | 71 |
| MARKET_CAP_WATCHLIST_RANGE | 68 |
| PRICE_BELOW_MINIMUM | 39 |
| MISSING_MARKET_CAP | 2 |

## Professional interpretation

- Stage 1 pass rate is within a reasonable diagnostic range for a first investability layer.
- Watchlist rate looks usable as an intermediate review bucket.
- Rejection rate appears compatible with a broad first-pass filter.
- Stage 1 remains a market/liquidity filter; Stage 2 still needs real fundamentals before professional opportunity ranking.
- No threshold changes are applied in this phase; this is a diagnostic report only.

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- release v0.6 modified: `False`
