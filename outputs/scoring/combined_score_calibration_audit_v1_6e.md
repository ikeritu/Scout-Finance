# Scout Finance ? v1.6E Combined Scoring Calibration Audit

## Scope

- This audit does not change the production scoring formula.
- It compares alternative weight scenarios using the current score components.
- Current production weights remain 20% metadata, 35% market data, 45% fundamentals.

## Current ranking

1. **MSFT** ? 91.06 (metadata 91.48, market 79.32, fundamentals 100.00)
2. **ASML** ? 91.06 (metadata 91.48, market 79.32, fundamentals 100.00)
3. **AAPL** ? 89.30 (metadata 90.52, market 78.70, fundamentals 97.00)

## Weight sensitivity

### current_20_35_45

1. **MSFT** ? 91.06
2. **ASML** ? 91.06
3. **AAPL** ? 89.30

### balanced_25_35_40

1. **MSFT** ? 90.63
2. **ASML** ? 90.63
3. **AAPL** ? 88.97

### market_heavier_20_45_35

1. **MSFT** ? 88.99
2. **ASML** ? 88.99
3. **AAPL** ? 87.47

### fundamentals_heavier_15_30_55

1. **MSFT** ? 92.52
2. **ASML** ? 92.52
3. **AAPL** ? 90.54

### metadata_lighter_10_40_50

1. **MSFT** ? 90.88
2. **ASML** ? 90.88
3. **AAPL** ? 89.03

## Current top gap

- Top: **MSFT** ? 91.06
- Second: **ASML** ? 91.06
- Gap: **0.00 points**

Interpretation: the current formula produces an almost tied top ranking.
This suggests calibration should focus on discriminating fundamentals quality, market data, or metadata more precisely.