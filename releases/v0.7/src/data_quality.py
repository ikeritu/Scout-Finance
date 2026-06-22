"""
Data quality module.

This module evaluates whether each market snapshot row contains enough
basic data to be used later by filters, scoring and OpenAI analysis.

Current scope:
- Basic completeness checks.
- Simple data quality score.
- Human-readable quality label.
- Basic issue/error extraction.

Not included in this phase:
- Scoring.
- OpenAI analysis.
- Streamlit UI.
- Database writes.
- Advanced anomaly detection.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


CRITICAL_FIELDS = [
    "ticker",
    "price",
    "previous_close",
    "volume",
    "avg_volume_50d",
    "market_cap",
]

IMPORTANT_FIELDS = [
    "relative_volume",
    "change_1d",
    "change_5d",
    "change_20d",
    "ma20",
    "ma50",
    "high_52w",
    "low_52w",
]

CONTEXT_FIELDS = [
    "company_name",
    "sector",
    "industry",
    "exchange",
    "currency",
]


def _is_missing(value: Any) -> bool:
    """
    Return True if a value should be considered missing.

    Handles None, NaN, pandas NA and empty strings.
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


def calculate_data_quality_score(row: pd.Series | dict[str, Any]) -> int:
    """
    Calculate a simple data quality score from 0 to 100.

    The score is intentionally simple at this stage:
    - Critical fields have the highest weight.
    - Important market fields have medium weight.
    - Context fields have lower weight.
    - Basic sanity penalties are applied for invalid numeric values.

    Parameters
    ----------
    row:
        Market snapshot row.

    Returns
    -------
    int
        Score between 0 and 100.
    """

    score = 100

    for field in CRITICAL_FIELDS:
        if _is_missing(row.get(field)):
            score -= 10

    for field in IMPORTANT_FIELDS:
        if _is_missing(row.get(field)):
            score -= 4

    for field in CONTEXT_FIELDS:
        if _is_missing(row.get(field)):
            score -= 2

    price = _safe_float(row.get("price"))
    previous_close = _safe_float(row.get("previous_close"))
    volume = _safe_float(row.get("volume"))
    avg_volume_50d = _safe_float(row.get("avg_volume_50d"))
    market_cap = _safe_float(row.get("market_cap"))

    if price is not None and price <= 0:
        score -= 15

    if previous_close is not None and previous_close <= 0:
        score -= 10

    if volume is not None and volume < 0:
        score -= 10

    if avg_volume_50d is not None and avg_volume_50d < 0:
        score -= 10

    if market_cap is not None and market_cap <= 0:
        score -= 10

    return max(0, min(100, int(score)))


def get_data_quality_label(score: int) -> str:
    """
    Convert a numeric data quality score into a readable label.

    Parameters
    ----------
    score:
        Data quality score from 0 to 100.

    Returns
    -------
    str
        Quality label.
    """

    if score >= 85:
        return "high"

    if score >= 60:
        return "medium"

    return "low"


def detect_data_quality_issues(row: pd.Series | dict[str, Any]) -> list[str]:
    """
    Detect basic data quality issues in one market snapshot row.

    Parameters
    ----------
    row:
        Market snapshot row.

    Returns
    -------
    list[str]
        List of detected issue messages.
    """

    issues: list[str] = []

    for field in CRITICAL_FIELDS:
        if _is_missing(row.get(field)):
            issues.append(f"missing_critical_field:{field}")

    for field in IMPORTANT_FIELDS:
        if _is_missing(row.get(field)):
            issues.append(f"missing_important_field:{field}")

    price = _safe_float(row.get("price"))
    previous_close = _safe_float(row.get("previous_close"))
    volume = _safe_float(row.get("volume"))
    avg_volume_50d = _safe_float(row.get("avg_volume_50d"))
    market_cap = _safe_float(row.get("market_cap"))

    if price is not None and price <= 0:
        issues.append("invalid_price")

    if previous_close is not None and previous_close <= 0:
        issues.append("invalid_previous_close")

    if volume is not None and volume < 0:
        issues.append("invalid_volume")

    if avg_volume_50d is not None and avg_volume_50d < 0:
        issues.append("invalid_avg_volume_50d")

    if market_cap is not None and market_cap <= 0:
        issues.append("invalid_market_cap")

    return issues


def apply_data_quality(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add data quality columns to a market snapshot dataframe.

    Added columns:
    - data_quality_score
    - data_quality_label
    - data_quality_issues

    Parameters
    ----------
    df:
        Market snapshot dataframe.

    Returns
    -------
    pandas.DataFrame
        Dataframe with data quality columns.
    """

    df_quality = df.copy()

    scores = df_quality.apply(calculate_data_quality_score, axis=1)
    df_quality["data_quality_score"] = scores
    df_quality["data_quality_label"] = scores.apply(get_data_quality_label)
    df_quality["data_quality_issues"] = df_quality.apply(
        lambda row: ";".join(detect_data_quality_issues(row)),
        axis=1,
    )

    return df_quality


def summarize_data_quality(df: pd.DataFrame) -> dict[str, Any]:
    """
    Summarize data quality results.

    Parameters
    ----------
    df:
        Market snapshot dataframe after apply_data_quality().

    Returns
    -------
    dict
        Summary dictionary.
    """

    if df.empty:
        return {
            "total_rows": 0,
            "high_quality_rows": 0,
            "medium_quality_rows": 0,
            "low_quality_rows": 0,
            "avg_data_quality_score": None,
            "rows_with_issues": 0,
        }

    label_counts = df["data_quality_label"].value_counts().to_dict()

    return {
        "total_rows": int(len(df)),
        "high_quality_rows": int(label_counts.get("high", 0)),
        "medium_quality_rows": int(label_counts.get("medium", 0)),
        "low_quality_rows": int(label_counts.get("low", 0)),
        "avg_data_quality_score": float(df["data_quality_score"].mean()),
        "rows_with_issues": int((df["data_quality_issues"] != "").sum()),
    }


def build_data_error_rows(
    df: pd.DataFrame,
    run_id: str | None = None,
    source: str = "market_data",
) -> list[dict[str, Any]]:
    """
    Build simple data error rows from data quality issues.

    This function does not write to SQLite. It only prepares dictionaries
    that can later be inserted by database.py if needed.

    Parameters
    ----------
    df:
        Market snapshot dataframe after apply_data_quality().
    run_id:
        Optional run identifier.
    source:
        Source label for the error.

    Returns
    -------
    list[dict]
        List of error dictionaries.
    """

    errors: list[dict[str, Any]] = []

    if "data_quality_issues" not in df.columns:
        return errors

    for _, row in df.iterrows():
        ticker = row.get("ticker")
        issues_text = row.get("data_quality_issues", "")

        if _is_missing(issues_text):
            continue

        issues = [issue for issue in str(issues_text).split(";") if issue]

        for issue in issues:
            severity = "high" if "critical" in issue or "invalid" in issue else "medium"

            errors.append(
                {
                    "run_id": run_id,
                    "ticker": ticker,
                    "source": source,
                    "error_type": issue,
                    "error_message": f"Data quality issue detected: {issue}",
                    "severity": severity,
                }
            )

    return errors


if __name__ == "__main__":
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

    print("\nFirst 10 quality rows:")
    columns_to_show = [
        "ticker",
        "price",
        "volume",
        "market_cap",
        "data_quality_score",
        "data_quality_label",
        "data_quality_issues",
    ]
    available_columns = [column for column in columns_to_show if column in quality_df.columns]
    print(quality_df[available_columns].head(10).to_string(index=False))
