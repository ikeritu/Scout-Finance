# PHASE 8F — Research Memo Export/Report Layer

## Objective

Create a readable export/report layer for the deterministic TOP 3 equity research memos persisted in Phase 8E.

## Scope

- Read persisted memos from `outputs/scouting/phase8e_persisted_equity_research_memos.json`.
- Fall back to the SQLite table `equity_research_memos` if the JSON output is unavailable.
- Export one Markdown report per memo.
- Export JSON, CSV index, summary, audit and phase report files.

## Hard constraints

- No OpenAI calls.
- No external APIs.
- No yfinance calls.
- No pipeline recalculation.
- Do not modify `app.py`.
- Do not modify `src/filters.py`.
- Do not modify `releases/v0.7`.
- Keep `estimated_cost = 0.0`.
- Keep `model_used = null`.
- Do not invent data; missing data remains marked as `data_insufficient`.
- Keep objective data and AI interpretation separated.

## Outputs

- `outputs/scouting/phase8f_research_memo_export_report_layer_summary.json`
- `outputs/scouting/phase8f_research_memo_export_report_layer_report.md`
- `outputs/scouting/phase8f_research_memo_export_report_layer_export.json`
- `outputs/scouting/phase8f_research_memo_export_report_layer_index.csv`
- `outputs/scouting/phase8f_research_memo_export_report_layer_audit.json`
- `outputs/scouting/research_memos/equity_research_memo_XX_TICKER.md`

## Next phase

8G — Optional AI interpretation gate and cost guardrails.
