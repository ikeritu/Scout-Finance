# Scout Finance — Phase 7B.2 Stage 1 Simulator Alignment

Generated at: `2026-06-08T09:36:20+00:00`

## Executive summary

- Companies compared: **500**.
- Matched: **487**.
- Mismatched: **13**.
- Match rate: **97.4%**.

## Real vs simulated counts

### Real Stage 1

- PASSED: **226**
- REJECTED: **208**
- WATCHLIST: **66**

### Simulated current_base

- PASSED: **213**
- REJECTED: **208**
- WATCHLIST: **79**

## Mismatch summary

| Real decision | Simulated decision | Count |
|---|---|---:|
| PASSED | WATCHLIST | 13 |

## Likely causes

- The simulator approximates Stage 1 but may not replicate every internal condition from src/filter_stage1.py.
- Most important differences should be inspected in stage1_simulator_alignment_mismatches.csv.
- If mismatches are mostly PASSED vs WATCHLIST, hard rejection thresholds may already match while watchlist-band logic differs.

## Recommendation

Do not apply Stage 1 threshold changes until current_base simulation matches real Stage 1 or until documented differences are intentionally accepted.

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- release v0.6 modified: `False`
