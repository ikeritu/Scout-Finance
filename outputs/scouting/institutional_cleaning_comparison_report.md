# Scout Finance — Phase 7A.4 Institutional Cleaning Comparison

Generated at: `2026-06-07T13:30:29+00:00`

## Executive summary

Institutional universe cleaning improved the quality and efficiency of the pipeline.
The system now separates out-of-scope instruments before Stage 1, instead of treating them as financial rejections.

## Before vs after

| Metric | Pre-cleaning | Post-cleaning |
|---|---:|---:|
| Processed rows | 50 | 100 |
| Market-data success | 34 | 100 |
| Market-data success rate | 68.0% | 100.0% |
| Stage 1 passed | 15 | 48 |
| Stage 1 watchlist | 4 | 10 |
| Stage 1 rejected | 31 | 42 |
| Stage 1 pass rate | 30.0% | 48.0% |
| Stage 1 rejection rate | 62.0% | 42.0% |

## Improvement deltas

- Market-data success rate delta: **32.0 percentage points**.
- Stage 1 pass rate delta: **18.0 percentage points**.
- Stage 1 rejection rate delta: **-20.0 percentage points**.

## Universe cleaning impact

- Initial universe rows: **7053**.
- Clean in-scope rows: **5617**.
- Excluded out-of-scope rows: **1436**.
- Excluded rate: **20.36%**.

### Excluded distribution

| Instrument type | Count |
|---|---:|
| WARRANT | 468 |
| UNIT | 286 |
| SPAC_OR_BLANK_CHECK | 208 |
| BOND_OR_NOTE | 159 |
| PREFERRED | 140 |
| RIGHT | 126 |
| CLOSED_END_FUND | 33 |
| ETN | 15 |
| ETF | 1 |

## Professional interpretation

The cleaning layer is not a financial rejection layer. It is an institutional universe-definition layer.
This makes Stage 1 cleaner, more defensible and easier to audit.

## Controls

- OpenAI called: `False`
- Paid API called: `False`
- yfinance called during this report: `False`
- app.py modified: `False`
- release v0.6 modified: `False`
