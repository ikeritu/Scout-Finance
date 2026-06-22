# Scout Finance — Phase 7B.6 Balanced Policy Protected Dry-Run

Generated at: `2026-06-08T11:20:30+00:00`

## Executive summary

- Input companies: **500**.
- Balanced passed: **182** (36.4%).
- Balanced watchlist: **84** (16.8%).
- Balanced rejected: **234** (46.8%).

## Current/base vs balanced

| Transition | Count |
|---|---:|
| REJECTED → REJECTED | 208 |
| PASSED → PASSED | 182 |
| PASSED → WATCHLIST | 44 |
| WATCHLIST → WATCHLIST | 40 |
| WATCHLIST → REJECTED | 26 |

## Safety interpretation

- Passed retained as passed: **182**.
- Passed moved to watchlist: **44**.
- Passed moved to rejected: **0**.

The dry-run does not change production outputs. It only writes separated dry-run files under `outputs/scouting/stage1_balanced_dry_run`.

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py modified: `False`
- filters modified: `False`
- production Stage 1 overwritten: `False`
- release modified: `False`
