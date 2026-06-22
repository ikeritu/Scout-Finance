# v1.0B — Human Review Layer

## Objective

Make manual review operational without editing JSON by hand.

## Commands

List records:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --list
```

Update a ticker:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --ticker ADBE --status reviewed_watchlist --note "Strong candidate, review valuation."
```

Export current buckets:

```powershell
.\.venv\Scripts\python.exe -m src.v1_0b_human_review_layer --export
```

## Outputs

- `outputs/scouting/manual_review/reviewed_watchlist.csv`
- `outputs/scouting/manual_review/reviewed_reject.csv`
- `outputs/scouting/manual_review/needs_more_data.csv`
- `outputs/scouting/manual_review/manual_review_summary.md`
- `outputs/scouting/v1_0b_human_review_layer_summary.json`
- `outputs/scouting/v1_0b_human_review_layer_report.md`

## Safety

No OpenAI, API, yfinance or pipeline recalculation. Not financial advice.
