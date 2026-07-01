# v1.6A — Fundamentals Input Bridge

## Objetivo

Añadir entrada local/manual de fundamentales para preparar el scoring combinado v1.

## Input principal

`data/real/manual_fundamentals.csv`

## Plantilla

`data/real/manual_fundamentals_template.csv`

## Campos

- ticker
- period
- period_end
- revenue
- revenue_growth_yoy
- gross_margin
- operating_margin
- net_margin
- free_cash_flow
- total_cash
- total_debt
- shares_diluted
- currency
- source_note

## Outputs

- `outputs/fundamentals/fundamentals_input_summary.json`
- `outputs/fundamentals/fundamentals_input_report.md`
- `outputs/fundamentals/manual_fundamentals_valid_rows.csv`
- `outputs/fundamentals/manual_fundamentals_issues.csv`

## Comandos

```powershell
.\.venv\Scripts\python.exe -m src.fundamentals_input --init-template
Copy-Item .\data\real\manual_fundamentals_template.csv .\data\real\manual_fundamentals.csv -Force
.\.venv\Scripts\python.exe -m src.fundamentals_input --validate
.\.venv\Scripts\python.exe scripts/check_v1_6a_fundamentals_input_bridge.py
```

## No toca

- scoring actual
- market data
- ranking
- OpenAI
- broker
- yfinance
- APIs externas
