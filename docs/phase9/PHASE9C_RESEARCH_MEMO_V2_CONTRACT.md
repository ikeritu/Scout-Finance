# Phase 9C — Research Memo v2 Contract Hardening

## Objective

Harden the Equity Research Memo contract before adding red flags or AI profiles.

This phase does not run OpenAI and does not recalculate the pipeline.

## Adds

- `schemas/equity_research_memo_schema_v0_2.json`
- `src/phase9c_research_memo_v2_contract.py`
- `scripts/check_phase9c_research_memo_v2_contract.py`

## Contract additions

- `manual_review_required = true`
- `not_financial_advice = true`
- `normalized_verdict`:
  - `WATCHLIST`
  - `REJECT`
  - `NEEDS_MORE_DATA`

Legacy compatibility:

- `watchlist` → `WATCHLIST`
- `avoid` → `REJECT`
- `data_insufficient` → `NEEDS_MORE_DATA`

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

- `outputs/scouting/phase9c_research_memo_v2_contract_summary.json`
- `outputs/scouting/phase9c_research_memo_v2_contract_report.md`
- `outputs/scouting/phase9c_research_memo_v2_contract_audit.json`
- `outputs/scouting/phase9c_research_memo_v2_contract_export.json`
- `outputs/scouting/phase9c_research_memo_v2_contract_index.csv`
- `outputs/scouting/research_memos_v2/*.json`
- `outputs/scouting/research_memos_v2/*.md`

## Next

Phase 9D — Red Flags Detector.
