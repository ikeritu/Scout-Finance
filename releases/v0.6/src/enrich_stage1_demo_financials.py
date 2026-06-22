"""
Enrich Stage 1 PASSED demo companies with basic financial fields.

Purpose:
- This is only for local Phase 5D testing.
- It adds sample financial data for AAPL and MSFT if present.
- It does not call OpenAI.
- It does not modify app.py.

Run from project root:

    ./.venv/Scripts/python.exe -m src.enrich_stage1_demo_financials
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.funnel_paths import STAGES_DIR


STAGE1_PASSED_PATH = STAGES_DIR / "stage1_passed.csv"


DEMO_FINANCIALS = {
    "AAPL": {
        "revenue_ttm": 390_000_000_000,
        "revenue_growth_1y": 0.03,
        "revenue_growth_3y": 0.06,
        "gross_margin": 0.46,
        "operating_margin": 0.30,
        "net_margin": 0.25,
        "ebitda": 125_000_000_000,
        "free_cash_flow": 100_000_000_000,
        "fcf_margin": 0.26,
        "total_debt": 110_000_000_000,
        "cash": 65_000_000_000,
        "net_debt": 45_000_000_000,
        "net_debt_to_ebitda": 0.36,
        "debt_to_equity": 1.5,
        "current_ratio": 1.0,
        "interest_coverage": 35.0,
        "shares_dilution_3y": -0.08,
        "financial_data_date": "2026-03-31",
        "data_completeness_score": 95,
        "special_case": False,
    },
    "MSFT": {
        "revenue_ttm": 245_000_000_000,
        "revenue_growth_1y": 0.14,
        "revenue_growth_3y": 0.15,
        "gross_margin": 0.69,
        "operating_margin": 0.44,
        "net_margin": 0.36,
        "ebitda": 130_000_000_000,
        "free_cash_flow": 75_000_000_000,
        "fcf_margin": 0.31,
        "total_debt": 80_000_000_000,
        "cash": 85_000_000_000,
        "net_debt": -5_000_000_000,
        "net_debt_to_ebitda": -0.04,
        "debt_to_equity": 0.4,
        "current_ratio": 1.2,
        "interest_coverage": 40.0,
        "shares_dilution_3y": -0.03,
        "financial_data_date": "2026-03-31",
        "data_completeness_score": 96,
        "special_case": False,
    },
}


def main() -> int:
    if not STAGE1_PASSED_PATH.exists():
        raise FileNotFoundError(
            f"Stage 1 passed file not found: {STAGE1_PASSED_PATH}. "
            "Run: python -m src.run_stage1_filter"
        )

    df = pd.read_csv(STAGE1_PASSED_PATH)

    for column in next(iter(DEMO_FINANCIALS.values())).keys():
        if column not in df.columns:
            df[column] = pd.NA

    for idx, row in df.iterrows():
        ticker = str(row.get("ticker", "")).upper().strip()

        if ticker not in DEMO_FINANCIALS:
            continue

        for column, value in DEMO_FINANCIALS[ticker].items():
            df.at[idx, column] = value

    df.to_csv(STAGE1_PASSED_PATH, index=False, encoding="utf-8-sig")

    print(f"Stage 1 passed enriched with demo financials: {STAGE1_PASSED_PATH}")
    print(f"Rows: {len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
