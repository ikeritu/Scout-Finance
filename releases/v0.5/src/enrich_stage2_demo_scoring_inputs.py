"""
Enrich Stage 2 PASSED demo companies with valuation/momentum fields.

Purpose:
- This is only for local Phase 5E testing.
- It adds sample valuation/momentum data for AAPL and MSFT if present.
- It does not call OpenAI.
- It does not modify app.py.

Run from project root:

    ./.venv/Scripts/python.exe -m src.enrich_stage2_demo_scoring_inputs
"""

from __future__ import annotations

import pandas as pd

from src.funnel_paths import STAGES_DIR


STAGE2_PASSED_PATH = STAGES_DIR / "stage2_passed.csv"


DEMO_SCORING_INPUTS = {
    "AAPL": {
        "pe_ratio": 30.0,
        "forward_pe": 28.0,
        "ev_ebitda": 22.0,
        "price_sales": 7.5,
        "fcf_yield": 0.035,
        "price_change_6m": 0.08,
        "price_change_12m": 0.12,
        "relative_strength_6m": 0.04,
        "drawdown_from_52w_high": -0.08,
    },
    "MSFT": {
        "pe_ratio": 34.0,
        "forward_pe": 31.0,
        "ev_ebitda": 24.0,
        "price_sales": 11.0,
        "fcf_yield": 0.028,
        "price_change_6m": 0.16,
        "price_change_12m": 0.24,
        "relative_strength_6m": 0.11,
        "drawdown_from_52w_high": -0.05,
    },
}


def main() -> int:
    if not STAGE2_PASSED_PATH.exists():
        raise FileNotFoundError(
            f"Stage 2 passed file not found: {STAGE2_PASSED_PATH}. "
            "Run: python -m src.run_stage2_filter"
        )

    df = pd.read_csv(STAGE2_PASSED_PATH)

    for column in next(iter(DEMO_SCORING_INPUTS.values())).keys():
        if column not in df.columns:
            df[column] = pd.NA

    for idx, row in df.iterrows():
        ticker = str(row.get("ticker", "")).upper().strip()

        if ticker not in DEMO_SCORING_INPUTS:
            continue

        for column, value in DEMO_SCORING_INPUTS[ticker].items():
            df.at[idx, column] = value

    df.to_csv(STAGE2_PASSED_PATH, index=False, encoding="utf-8-sig")

    print(f"Stage 2 passed enriched with demo scoring inputs: {STAGE2_PASSED_PATH}")
    print(f"Rows: {len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
