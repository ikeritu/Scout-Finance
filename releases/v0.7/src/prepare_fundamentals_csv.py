
"""
Scout Finance — Phase 6C fundamentals CSV enrichment.

Reads data/raw/fundamentals_source.csv, normalizes fundamental columns,
merges them into data/stages/stage1_passed.csv, and writes
data/stages/stage1_passed_enriched.csv.

No external APIs. No OpenAI. Does not modify app.py.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.funnel_paths import SCOUTING_OUTPUTS_DIR, STAGES_DIR, ensure_funnel_directories


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FUNDAMENTALS_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "fundamentals_source.csv"
STAGE1_PASSED_PATH = STAGES_DIR / "stage1_passed.csv"
STAGE1_PASSED_ENRICHED_PATH = STAGES_DIR / "stage1_passed_enriched.csv"
SUMMARY_PATH = SCOUTING_OUTPUTS_DIR / "fundamentals_enrichment_summary.json"


FUNDAMENTAL_OUTPUT_COLUMNS = [
    "ticker",
    "revenue_ttm",
    "revenue_growth_1y",
    "revenue_growth_3y",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "ebitda",
    "free_cash_flow",
    "fcf_margin",
    "total_debt",
    "cash",
    "net_debt",
    "net_debt_to_ebitda",
    "debt_to_equity",
    "current_ratio",
    "interest_coverage",
    "shares_dilution_3y",
    "financial_data_date",
    "data_completeness_score",
    "special_case",
]


COLUMN_ALIASES = {
    "ticker": ["ticker", "symbol", "Symbol", "Ticker", "SYMBOL"],
    "revenue_ttm": ["revenue_ttm", "Revenue TTM", "Revenue", "Total Revenue", "revenue"],
    "revenue_growth_1y": ["revenue_growth_1y", "Revenue Growth 1Y", "revenueGrowth1Y"],
    "revenue_growth_3y": ["revenue_growth_3y", "Revenue Growth 3Y", "revenueGrowth3Y"],
    "gross_margin": ["gross_margin", "Gross Margin", "grossMargin"],
    "operating_margin": ["operating_margin", "Operating Margin", "operatingMargin"],
    "net_margin": ["net_margin", "Net Margin", "netMargin"],
    "ebitda": ["ebitda", "EBITDA", "Ebitda"],
    "free_cash_flow": ["free_cash_flow", "Free Cash Flow", "FCF", "freeCashFlow"],
    "fcf_margin": ["fcf_margin", "FCF Margin", "freeCashFlowMargin"],
    "total_debt": ["total_debt", "Total Debt", "totalDebt"],
    "cash": ["cash", "Cash", "cashAndCashEquivalents"],
    "net_debt": ["net_debt", "Net Debt", "netDebt"],
    "net_debt_to_ebitda": ["net_debt_to_ebitda", "Net Debt / EBITDA", "netDebtToEbitda"],
    "debt_to_equity": ["debt_to_equity", "Debt to Equity", "debtToEquity"],
    "current_ratio": ["current_ratio", "Current Ratio", "currentRatio"],
    "interest_coverage": ["interest_coverage", "Interest Coverage", "interestCoverage"],
    "shares_dilution_3y": ["shares_dilution_3y", "Shares Dilution 3Y", "sharesDilution3Y"],
    "financial_data_date": ["financial_data_date", "Financial Data Date", "date", "fiscalDateEnding"],
    "data_completeness_score": ["data_completeness_score", "Data Completeness Score", "dataCompletenessScore"],
    "special_case": ["special_case", "Special Case", "specialCase"],
}


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    normalized_columns = {str(col).strip().lower(): col for col in df.columns}
    for alias in aliases:
        key = alias.strip().lower()
        if key in normalized_columns:
            return normalized_columns[key]
    return None


def _get_series(df: pd.DataFrame, target: str, default: Any = None) -> pd.Series:
    column = _find_column(df, COLUMN_ALIASES.get(target, [target]))
    if column is None:
        return pd.Series([default] * len(df))
    return df[column]


def _parse_number(value: Any) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    text = text.replace("$", "").replace(",", "").replace("%", "").strip()
    is_negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")

    multiplier = 1.0
    if text[-1:].upper() == "T":
        multiplier = 1_000_000_000_000
        text = text[:-1]
    elif text[-1:].upper() == "B":
        multiplier = 1_000_000_000
        text = text[:-1]
    elif text[-1:].upper() == "M":
        multiplier = 1_000_000
        text = text[:-1]
    elif text[-1:].upper() == "K":
        multiplier = 1_000
        text = text[:-1]

    text = re.sub(r"[^0-9.\-]", "", text)
    if not text:
        return None

    try:
        number = float(text) * multiplier
        return -number if is_negative else number
    except Exception:
        return None


def _parse_percent_or_ratio(value: Any) -> float | None:
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip()
        if not text:
            return None
        has_percent = "%" in text
        number = _parse_number(text)
        if number is None:
            return None
        if has_percent:
            return number / 100.0

    if abs(number) > 1.5:
        return number / 100.0
    return number


def _parse_bool(value: Any) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "si", "sí", "special", "especial"}


def _calculate_completeness(row: pd.Series, columns: list[str]) -> float:
    if not columns:
        return 0.0
    present = sum(1 for column in columns if column in row.index and pd.notna(row.get(column)))
    return round((present / len(columns)) * 100, 2)


def normalize_fundamentals_csv(
    input_path: Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
    data_source: str = "fundamentals_csv",
) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Fundamentals input CSV not found: {input_path}. "
            "Place a file in data/raw/fundamentals_source.csv first."
        )

    raw = pd.read_csv(input_path)
    if raw.empty:
        raise ValueError("Fundamentals input CSV is empty.")

    result = pd.DataFrame()
    result["ticker"] = _get_series(raw, "ticker").astype("string").str.strip().str.upper()

    money_columns = ["revenue_ttm", "ebitda", "free_cash_flow", "total_debt", "cash", "net_debt"]
    ratio_columns = [
        "revenue_growth_1y",
        "revenue_growth_3y",
        "gross_margin",
        "operating_margin",
        "net_margin",
        "fcf_margin",
        "net_debt_to_ebitda",
        "debt_to_equity",
        "current_ratio",
        "interest_coverage",
        "shares_dilution_3y",
    ]

    for column in money_columns:
        result[column] = _get_series(raw, column).apply(_parse_number)

    for column in ratio_columns:
        result[column] = _get_series(raw, column).apply(_parse_percent_or_ratio)

    result["financial_data_date"] = _get_series(raw, "financial_data_date", _utc_today())
    result["financial_data_date"] = result["financial_data_date"].fillna(_utc_today()).astype("string")
    result["special_case"] = _get_series(raw, "special_case", False).apply(_parse_bool)

    mask_net_debt = result["net_debt"].isna() & result["total_debt"].notna() & result["cash"].notna()
    result.loc[mask_net_debt, "net_debt"] = result.loc[mask_net_debt, "total_debt"] - result.loc[mask_net_debt, "cash"]

    mask_fcf_margin = (
        result["fcf_margin"].isna()
        & result["free_cash_flow"].notna()
        & result["revenue_ttm"].notna()
        & (result["revenue_ttm"] != 0)
    )
    result.loc[mask_fcf_margin, "fcf_margin"] = (
        result.loc[mask_fcf_margin, "free_cash_flow"] / result.loc[mask_fcf_margin, "revenue_ttm"]
    )

    mask_nd_ebitda = (
        result["net_debt_to_ebitda"].isna()
        & result["net_debt"].notna()
        & result["ebitda"].notna()
        & (result["ebitda"] != 0)
    )
    result.loc[mask_nd_ebitda, "net_debt_to_ebitda"] = (
        result.loc[mask_nd_ebitda, "net_debt"] / result.loc[mask_nd_ebitda, "ebitda"]
    )

    completeness_columns = [
        "revenue_ttm",
        "operating_margin",
        "fcf_margin",
        "net_debt_to_ebitda",
        "shares_dilution_3y",
        "financial_data_date",
        "special_case",
    ]
    existing_score = _get_series(raw, "data_completeness_score")
    calculated_scores = result.apply(lambda row: _calculate_completeness(row, completeness_columns), axis=1)
    result["data_completeness_score"] = existing_score.apply(_parse_number).fillna(calculated_scores)

    result["fundamentals_data_source"] = data_source
    result["fundamentals_last_updated"] = _utc_today()

    result = result[result["ticker"].notna()]
    result = result[result["ticker"].astype(str).str.len() > 0]
    result = result.drop_duplicates(subset=["ticker"], keep="first")

    for column in FUNDAMENTAL_OUTPUT_COLUMNS:
        if column not in result.columns:
            result[column] = pd.NA

    return result[FUNDAMENTAL_OUTPUT_COLUMNS + ["fundamentals_data_source", "fundamentals_last_updated"]]


def enrich_stage1_passed_with_fundamentals(
    fundamentals_input_path: Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
    stage1_passed_path: Path = STAGE1_PASSED_PATH,
    output_path: Path = STAGE1_PASSED_ENRICHED_PATH,
    data_source: str = "fundamentals_csv",
    overwrite_stage1_passed: bool = False,
) -> dict[str, Any]:
    ensure_funnel_directories()

    if not stage1_passed_path.exists():
        raise FileNotFoundError(f"Stage 1 passed file not found: {stage1_passed_path}. Run Stage 1 first.")

    stage1_df = pd.read_csv(stage1_passed_path)
    fundamentals_df = normalize_fundamentals_csv(input_path=fundamentals_input_path, data_source=data_source)

    enriched = stage1_df.merge(fundamentals_df, on="ticker", how="left", suffixes=("", "_fundamental"))

    matched = int(enriched["revenue_ttm"].notna().sum()) if "revenue_ttm" in enriched.columns else 0
    input_companies = int(len(stage1_df))
    fundamentals_rows = int(len(fundamentals_df))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(output_path, index=False, encoding="utf-8-sig")

    overwritten = False
    if overwrite_stage1_passed:
        enriched.to_csv(stage1_passed_path, index=False, encoding="utf-8-sig")
        overwritten = True

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "phase": "6C",
        "input_stage1_companies": input_companies,
        "fundamentals_rows": fundamentals_rows,
        "matched_companies_with_revenue": matched,
        "match_rate_percent": round((matched / input_companies) * 100, 2) if input_companies else 0,
        "output_path": str(output_path),
        "stage1_passed_overwritten": overwritten,
        "openai_called": False,
        "api_called": False,
        "app_modified": False,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_FUNDAMENTALS_INPUT_PATH))
    parser.add_argument("--source", default="fundamentals_csv")
    parser.add_argument("--overwrite-stage1-passed", action="store_true")
    args = parser.parse_args()

    summary = enrich_stage1_passed_with_fundamentals(
        fundamentals_input_path=Path(args.input),
        data_source=args.source,
        overwrite_stage1_passed=args.overwrite_stage1_passed,
    )

    print("Scout Finance — Phase 6C fundamentals CSV enrichment")
    print("=" * 64)
    print(f"Stage 1 companies: {summary.get('input_stage1_companies')}")
    print(f"Fundamentals rows: {summary.get('fundamentals_rows')}")
    print(f"Matched companies with revenue: {summary.get('matched_companies_with_revenue')}")
    print(f"Match rate: {summary.get('match_rate_percent')}%")
    print(f"Output: {summary.get('output_path')}")
    print(f"Stage1 passed overwritten: {summary.get('stage1_passed_overwritten')}")
    print("No API call. No OpenAI call. app.py not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
