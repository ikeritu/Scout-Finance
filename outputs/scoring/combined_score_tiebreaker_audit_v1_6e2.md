# Scout Finance ? v1.6E2 Tie-breaker Audit

## Purpose

This audit checks whether tied combined scores can be separated by existing score components.
It does not change the production ranking formula.

## Candidate tie-breaker order

1. combined_score_v1
2. fundamentals_score_component
3. market_data_score_component
4. metadata_score_component
5. ticker alphabetical fallback

## Ranking using candidate tie-breaker

1. **MSFT** ? combined 91.06, fundamentals 100.00, market 79.32, metadata 91.48
2. **ASML** ? combined 91.06, fundamentals 100.00, market 79.32, metadata 91.48
3. **AAPL** ? combined 89.30, fundamentals 97.00, market 78.70, metadata 90.52

## Interpretation

If tied companies have identical fundamentals, market data and metadata components,
weights alone cannot solve the tie. The model needs either more granular components
or a deterministic tie-breaker.