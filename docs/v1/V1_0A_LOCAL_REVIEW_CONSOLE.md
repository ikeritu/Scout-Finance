# v1.0A — Local Review Console

## Objective

Create a simple local review console from v0.9 outputs.

No dashboard, no Streamlit, no external calls. This is a Markdown/JSON/CSV review layer.

## Inputs

- `outputs/scouting/phase9e_memo_v2_red_flags_export.json`

## Outputs

- `outputs/scouting/manual_review/manual_review_state.json`
- `outputs/scouting/manual_review/local_review_console.md`
- `outputs/scouting/manual_review/manual_review_notes.md`
- `outputs/scouting/manual_review/local_review_console_index.csv`
- `outputs/scouting/v1_0a_local_review_console_summary.json`
- `outputs/scouting/v1_0a_local_review_console_report.md`

## Manual statuses

- `pending_review`
- `reviewed_watchlist`
- `reviewed_reject`
- `needs_more_data`

## Safety

- No OpenAI calls.
- No API calls.
- No yfinance calls.
- No pipeline recalculation.
