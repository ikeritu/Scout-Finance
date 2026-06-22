# Scout Finance — Phase 7C.2 v2 Stage 2 yfinance policy dry-run

Generated at: `2026-06-09T08:27:07+00:00`

## Purpose

Dry-run a Stage 2 policy aligned with yfinance limitations without calling internal `filter_stage2.py` functions.

The only simulated policy change is:

```text
MISSING_SHARES_DILUTION -> MISSING_SHARES_DILUTION_PROVIDER_LIMITATION
```

Missing 3Y dilution from yfinance is tracked as a provider limitation but does not block a clean pass by itself.

## Current Stage 2

| Bucket | Count |
|---|---:|
| Passed | 0 |
| Watchlist | 144 |
| Rejected | 38 |

## Simulated yfinance-aligned Stage 2

| Bucket | Count |
|---|---:|
| Passed | 63 |
| Watchlist | 81 |
| Rejected | 38 |

## Main simulated reasons

- MISSING_SHARES_DILUTION_PROVIDER_LIMITATION: 182
- MISSING_FCF_MARGIN: 33
- DATA_COMPLETENESS_WATCHLIST_RANGE: 24
- OPERATING_MARGIN_WATCHLIST_RANGE: 23
- DEBT_WATCHLIST_RANGE: 23
- MISSING_NET_DEBT_TO_EBITDA: 20
- FCF_MARGIN_TOO_NEGATIVE: 19
- OPERATING_MARGIN_TOO_NEGATIVE_BUT_RECOVERABLE: 19
- OPERATING_MARGIN_TOO_NEGATIVE: 19
- DEBT_TOO_HIGH: 15
- FCF_MARGIN_TOO_NEGATIVE_BUT_RECOVERABLE: 13
- FCF_MARGIN_WATCHLIST_RANGE: 10
- MISSING_REVENUE_SPECIAL_CASE: 9
- LOW_DATA_COMPLETENESS: 2
- MISSING_REVENUE: 1

## Transitions

- WATCHLIST->WATCHLIST: 81
- WATCHLIST->PASSED: 63
- REJECTED->REJECTED: 38

## Decision

- Recommended decision: **APPROVE_FOR_GUARDED_IMPLEMENTATION**
- Recommended next phase: **7C.3 — Guarded Stage 2 yfinance policy implementation**

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filter_stage2.py modified: `False`
- release modified: `False`
