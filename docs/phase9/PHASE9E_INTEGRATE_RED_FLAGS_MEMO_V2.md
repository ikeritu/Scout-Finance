# Phase 9E — Integrate Red Flags into Research Memo v2

## Objective

Merge Phase 9C Research Memo v2 outputs with Phase 9D deterministic red flags.

This phase does not use AI and does not recalculate the pipeline.

## Adds

- `src/phase9e_integrate_red_flags_memo_v2.py`
- `scripts/check_phase9e_integrate_red_flags_memo_v2.py`

## Policy

- Red flags are integrated into each memo.
- If high/critical red flags exist, final verdict remains `NEEDS_MORE_DATA`.
- `manual_review_required` remains true.
- `not_financial_advice` remains true.
- No buy/sell language.
- No real AI.

## Safety

- No OpenAI calls.
- No API calls.
- No yfinance calls.
- No pipeline recalculation.
- No app changes.
- No filter changes.
- No release changes.
- v0.8 remains untouched.

## Outputs

- `outputs/scouting/phase9e_memo_v2_red_flags_summary.json`
- `outputs/scouting/phase9e_memo_v2_red_flags_report.md`
- `outputs/scouting/phase9e_memo_v2_red_flags_audit.json`
- `outputs/scouting/phase9e_memo_v2_red_flags_export.json`
- `outputs/scouting/phase9e_memo_v2_red_flags_index.csv`
- `outputs/scouting/research_memos_v2_red_flags/*.json`
- `outputs/scouting/research_memos_v2_red_flags/*.md`

## Next

Phase 9F — AI profiles dry-run, optional.
