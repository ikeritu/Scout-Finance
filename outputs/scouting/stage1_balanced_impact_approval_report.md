# Scout Finance — Phase 7B.7 Balanced Stage 1 Impact Approval

Generated at: `2026-06-08T13:19:01+00:00`

## Executive decision

- Decision: **APPROVE_FOR_GUARDED_APPLICATION**.
- Apply to production now: **False**.
- Recommended next step: **Phase 7B.8 guarded implementation patch**.

## Impact summary

- Input companies: **500**.
- Balanced passed: **182** (36.4%).
- Balanced watchlist: **84** (16.8%).
- Balanced rejected: **234** (46.8%).

## Transition summary

| Transition | Count |
|---|---:|
| REJECTED->REJECTED | 208 |
| PASSED->PASSED | 182 |
| PASSED->WATCHLIST | 44 |
| WATCHLIST->WATCHLIST | 40 |
| WATCHLIST->REJECTED | 26 |

## Safety findings

- Passed retained as passed: **182**.
- Passed moved to watchlist: **44**.
- Passed moved to rejected: **0**.
- Watchlist moved to rejected: **26**.

## Professional interpretation

- Balanced policy reduces pass-through noise while keeping a substantial discovery pool.
- No current PASSED company is moved directly to REJECTED.
- PASSED to WATCHLIST transitions are review downgrades, not hard exclusions.
- WATCHLIST to REJECTED transitions are primarily the intended cleanup area.
- Production filters should only be changed in a guarded implementation phase with backup and rollback.

## Main reasons affected

| Reason code | Count |
|---|---:|
| MARKET_CAP_BELOW_MINIMUM | 199 |
| LOW_DOLLAR_VOLUME | 164 |
| DOLLAR_VOLUME_WATCHLIST_RANGE | 100 |
| MARKET_CAP_WATCHLIST_RANGE | 85 |
| PRICE_BELOW_MINIMUM | 80 |
| PRICE_WEAK_WATCHLIST_RANGE | 58 |
| PRICE_STRONG_WATCHLIST_RANGE | 57 |
| MISSING_MARKET_CAP | 2 |

## Approval guardrails

- Do not overwrite production Stage 1 files without a backup.
- Apply only through a guarded patch phase.
- After applying, rerun the 500-company validation.
- Compare new production outputs against the 7B.6 dry-run.
- Keep actual/base outputs available for rollback.

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- production Stage 1 overwritten: `False`
- release modified: `False`
