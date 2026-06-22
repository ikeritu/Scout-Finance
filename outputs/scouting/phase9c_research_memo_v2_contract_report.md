# Phase 9C — Research Memo v2 Contract Hardening

Status: **OK**

## Summary

- Source file: `outputs\scouting\phase8f_research_memo_export_report_layer_export.json`
- Memos loaded: 3
- Memos exported v2: 3
- Verdicts: `{'NEEDS_MORE_DATA': 3}`
- Manual review required: `True`
- Not financial advice: `True`

## Safety controls

- OpenAI called: False
- API called: False
- yfinance called: False
- Pipeline recalculated: False
- app.py modified: False
- filters modified: False
- release modified: False

## Contract

- `manual_review_required = true`
- `not_financial_advice = true`
- `normalized_verdict` allowed values:
  - `WATCHLIST`
  - `REJECT`
  - `NEEDS_MORE_DATA`
- Keep compatibility with legacy verdicts such as `watchlist`, `avoid`, `data_insufficient`.

## Next

Proceed to Phase 9D — Red Flags Detector after this contract is validated.
