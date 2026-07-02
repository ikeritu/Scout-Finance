# Scout Finance ? v1.6E4 Fundamentals Granularity Audit

## Purpose

This audit calculates a non-production granular fundamentals score.
It is intended to diagnose ties caused by capped fundamentals components.

## Ranking by granular fundamentals

1. **MSFT** ? granular fundamentals 99.60
   - Revenue scale: 100.00, Growth: 98.00, Gross: 100.00, Operating: 100.00, Net: 100.00, FCF: 100.00, Balance sheet: 100.00
2. **ASML** ? granular fundamentals 80.41
   - Revenue scale: 80.00, Growth: 84.00, Gross: 78.46, Operating: 77.50, Net: 77.14, FCF: 70.00, Balance sheet: 100.00
3. **AAPL** ? granular fundamentals 77.74
   - Revenue scale: 100.00, Growth: 58.40, Gross: 69.23, Operating: 75.00, Net: 74.29, FCF: 100.00, Balance sheet: 70.00

## Interpretation

If companies tied at fundamentals_score_component = 100 separate here,
the production component is too coarse or capped too early.