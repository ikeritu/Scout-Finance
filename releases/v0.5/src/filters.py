"""
Filters module.

This module applies basic hard filters to the market snapshot before any
scoring or OpenAI analysis.

Current scope:
- Filter by minimum price.
- Filter by minimum market capitalization.
- Filter by minimum average volume.
- Filter by minimum data quality score.
- Explain why each company passes or is excluded.

Not included in this phase:
- Scoring.
- Ranking.
- OpenAI analysis.
- Streamlit UI.
- Database writes.
- Recommendations.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from config import (
    MIN_AVG_VOLUME_50D,
    MIN_DATA_QUALITY_SCORE,
    MIN_MARKET_CAP,
    MIN_PRICE,
)


FILTER_COLUMNS = [
    "passes_basic_filters",
    "filter_reasons",
    "excluded_by_price",
    "excluded_by_market_cap",
    "excluded_by_avg_volume_50d",
    "excluded_by_data_quality",
]


def _is_missing(value: Any) -> bool:
    """
    Return True if a value should be considered missing.
    """

    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except TypeError:
        pass

    if isinstance(value, str) and value.strip() == "":
        return True

    return False


def _safe_float(value: Any) -> float | None:
    """
    Convert a value to float when possible.

    Returns None if the value is missing or cannot be converted.
    """

    if _is_missing(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def evaluate_basic_filters(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate basic hard filters for one company.

    Parameters
    ----------
    row:
        One row from a market snapshot dataframe.

    Returns
    -------
    dict
        Filter result with pass/fail flags and readable reasons.
    """

    price = _safe_float(row.get("price"))
    market_cap = _safe_float(row.get("market_cap"))
    avg_volume_50d = _safe_float(row.get("avg_volume_50d"))
    data_quality_score = _safe_float(row.get("data_quality_score"))

    excluded_by_price = price is None or price < MIN_PRICE
    excluded_by_market_cap = market_cap is None or market_cap < MIN_MARKET_CAP
    excluded_by_avg_volume_50d = (
        avg_volume_50d is None or avg_volume_50d < MIN_AVG_VOLUME_50D
    )
    excluded_by_data_quality = (
        data_quality_score is None or data_quality_score < MIN_DATA_QUALITY_SCORE
    )

    reasons: list[str] = []

    if excluded_by_price:
        reasons.append(f"price_below_min_or_missing:{MIN_PRICE}")

    if excluded_by_market_cap:
        reasons.append(f"market_cap_below_min_or_missing:{MIN_MARKET_CAP}")

    if excluded_by_avg_volume_50d:
        reasons.append(f"avg_volume_50d_below_min_or_missing:{MIN_AVG_VOLUME_50D}")

    if excluded_by_data_quality:
        reasons.append(f"data_quality_below_min_or_missing:{MIN_DATA_QUALITY_SCORE}")

    passes_basic_filters = not any(
        [
            excluded_by_price,
            excluded_by_market_cap,
            excluded_by_avg_volume_50d,
            excluded_by_data_quality,
        ]
    )

    return {
        "passes_basic_filters": passes_basic_filters,
        "filter_reasons": ";".join(reasons),
        "excluded_by_price": excluded_by_price,
        "excluded_by_market_cap": excluded_by_market_cap,
        "excluded_by_avg_volume_50d": excluded_by_avg_volume_50d,
        "excluded_by_data_quality": excluded_by_data_quality,
    }


def apply_basic_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply basic hard filters to a market snapshot dataframe.

    This function does not remove rows. It only adds filter columns so the
    caller can inspect both accepted and excluded companies.

    Parameters
    ----------
    df:
        Market snapshot dataframe, ideally after apply_data_quality().

    Returns
    -------
    pandas.DataFrame
        Dataframe with filter result columns.
    """

    df_filtered = df.copy()

    filter_results = df_filtered.apply(evaluate_basic_filters, axis=1)
    filter_results_df = pd.DataFrame(filter_results.tolist(), index=df_filtered.index)

    for column in FILTER_COLUMNS:
        df_filtered[column] = filter_results_df[column]

    return df_filtered


def get_passed_companies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return only companies that passed the basic filters.

    Parameters
    ----------
    df:
        Dataframe after apply_basic_filters().

    Returns
    -------
    pandas.DataFrame
        Filtered dataframe with only passed companies.
    """

    if "passes_basic_filters" not in df.columns:
        raise ValueError("Missing column: passes_basic_filters. Run apply_basic_filters() first.")

    return df[df["passes_basic_filters"] == True].reset_index(drop=True)  # noqa: E712


def get_excluded_companies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return only companies excluded by the basic filters.

    Parameters
    ----------
    df:
        Dataframe after apply_basic_filters().

    Returns
    -------
    pandas.DataFrame
        Filtered dataframe with only excluded companies.
    """

    if "passes_basic_filters" not in df.columns:
        raise ValueError("Missing column: passes_basic_filters. Run apply_basic_filters() first.")

    return df[df["passes_basic_filters"] == False].reset_index(drop=True)  # noqa: E712


def summarize_filters(df: pd.DataFrame) -> dict[str, Any]:
    """
    Summarize filter results.

    Parameters
    ----------
    df:
        Dataframe after apply_basic_filters().

    Returns
    -------
    dict
        Summary of passed and excluded companies.
    """

    if df.empty:
        return {
            "total_rows": 0,
            "passed_companies": 0,
            "excluded_companies": 0,
            "excluded_by_price": 0,
            "excluded_by_market_cap": 0,
            "excluded_by_avg_volume_50d": 0,
            "excluded_by_data_quality": 0,
            "first_5_passed_tickers": [],
        }

    if "passes_basic_filters" not in df.columns:
        raise ValueError("Missing column: passes_basic_filters. Run apply_basic_filters() first.")

    passed_df = get_passed_companies(df)

    return {
        "total_rows": int(len(df)),
        "passed_companies": int(df["passes_basic_filters"].sum()),
        "excluded_companies": int((~df["passes_basic_filters"]).sum()),
        "excluded_by_price": int(df["excluded_by_price"].sum()),
        "excluded_by_market_cap": int(df["excluded_by_market_cap"].sum()),
        "excluded_by_avg_volume_50d": int(df["excluded_by_avg_volume_50d"].sum()),
        "excluded_by_data_quality": int(df["excluded_by_data_quality"].sum()),
        "first_5_passed_tickers": passed_df["ticker"].head(5).tolist()
        if "ticker" in passed_df.columns
        else [],
    }


def print_filter_thresholds() -> None:
    """
    Print the current filter thresholds from config.py.
    """

    print("Current filter thresholds:")
    print(f"- MIN_PRICE: {MIN_PRICE}")
    print(f"- MIN_MARKET_CAP: {MIN_MARKET_CAP}")
    print(f"- MIN_AVG_VOLUME_50D: {MIN_AVG_VOLUME_50D}")
    print(f"- MIN_DATA_QUALITY_SCORE: {MIN_DATA_QUALITY_SCORE}")


if __name__ == "__main__":
    from src.data_quality import apply_data_quality, summarize_data_quality
    from src.market_data import build_market_snapshot, summarize_market_snapshot
    from src.universe import validate_and_load_universe

    universe_df, universe_summary = validate_and_load_universe(mode="demo")

    print("Universe loaded:")
    print(universe_summary)

    snapshot_df = build_market_snapshot(universe_df, period="1y")
    snapshot_summary = summarize_market_snapshot(snapshot_df)

    print("\nMarket snapshot summary:")
    for key, value in snapshot_summary.items():
        print(f"- {key}: {value}")

    quality_df = apply_data_quality(snapshot_df)
    quality_summary = summarize_data_quality(quality_df)

    print("\nData quality summary:")
    for key, value in quality_summary.items():
        print(f"- {key}: {value}")

    filtered_df = apply_basic_filters(quality_df)
    filter_summary = summarize_filters(filtered_df)

    print()
    print_filter_thresholds()

    print("\nFilter summary:")
    for key, value in filter_summary.items():
        print(f"- {key}: {value}")

    print("\nFirst 10 filtered rows:")
    columns_to_show = [
        "ticker",
        "price",
        "market_cap",
        "avg_volume_50d",
        "data_quality_score",
        "passes_basic_filters",
        "filter_reasons",
    ]
    available_columns = [column for column in columns_to_show if column in filtered_df.columns]
    print(filtered_df[available_columns].head(10).to_string(index=False))
