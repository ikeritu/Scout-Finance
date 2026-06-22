"""
Utility module.

This module contains small reusable helpers for the MVP.

Current scope:
- Formatting numbers, money and percentages.
- Safe conversions.
- Simple date/time helpers.
- Small console/table helpers.
- Basic path helpers.

Not included in this phase:
- Business logic.
- Market data downloads.
- Scoring logic.
- Database writes.
- Streamlit UI.
- OpenAI calls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def utc_now_iso() -> str:
    """
    Return the current UTC datetime in ISO format.
    """

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today_utc_str(separator: str = "-") -> str:
    """
    Return the current UTC date.

    Parameters
    ----------
    separator:
        Date separator. Use "-" for YYYY-MM-DD or "" for YYYYMMDD.

    Returns
    -------
    str
        Current UTC date.
    """

    if separator == "":
        return datetime.now(timezone.utc).strftime("%Y%m%d")

    return datetime.now(timezone.utc).strftime(f"%Y{separator}%m{separator}%d")


def ensure_dir(path: str | Path) -> Path:
    """
    Create a directory if it does not exist and return it as Path.
    """

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def is_missing(value: Any) -> bool:
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


def safe_float(value: Any, default: float | None = None) -> float | None:
    """
    Convert a value to float when possible.

    Parameters
    ----------
    value:
        Value to convert.
    default:
        Returned when conversion is not possible.

    Returns
    -------
    float | None
        Converted float or default.
    """

    if is_missing(value):
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int | None = None) -> int | None:
    """
    Convert a value to int when possible.
    """

    if is_missing(value):
        return default

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """
    Convert common boolean representations to bool.
    """

    if isinstance(value, bool):
        return value

    if is_missing(value):
        return default

    if isinstance(value, (int, float)):
        return value == 1

    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "si", "sí"}

    return default


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """
    Restrict a numeric value to a fixed interval.
    """

    return max(minimum, min(maximum, value))


def format_number(value: Any, decimals: int = 2) -> str:
    """
    Format a number using thousands separators.

    Returns "-" for missing values.
    """

    number = safe_float(value)

    if number is None:
        return "-"

    return f"{number:,.{decimals}f}"


def format_integer(value: Any) -> str:
    """
    Format a number as integer with thousands separators.

    Returns "-" for missing values.
    """

    number = safe_int(value)

    if number is None:
        return "-"

    return f"{number:,}"


def format_percent(value: Any, decimals: int = 2, input_is_ratio: bool = True) -> str:
    """
    Format a value as percentage.

    Parameters
    ----------
    value:
        Numeric value.
    decimals:
        Number of decimals.
    input_is_ratio:
        If True, 0.05 becomes 5.00%.
        If False, 5 becomes 5.00%.
    """

    number = safe_float(value)

    if number is None:
        return "-"

    if input_is_ratio:
        number *= 100

    return f"{number:.{decimals}f}%"


def format_usd(value: Any, decimals: int = 2, compact: bool = False) -> str:
    """
    Format a numeric value as USD.

    Parameters
    ----------
    value:
        Numeric value.
    decimals:
        Number of decimals.
    compact:
        If True, use K/M/B/T suffixes.
    """

    number = safe_float(value)

    if number is None:
        return "-"

    if not compact:
        return f"${number:,.{decimals}f}"

    abs_number = abs(number)

    if abs_number >= 1_000_000_000_000:
        return f"${number / 1_000_000_000_000:.{decimals}f}T"

    if abs_number >= 1_000_000_000:
        return f"${number / 1_000_000_000:.{decimals}f}B"

    if abs_number >= 1_000_000:
        return f"${number / 1_000_000:.{decimals}f}M"

    if abs_number >= 1_000:
        return f"${number / 1_000:.{decimals}f}K"

    return f"${number:.{decimals}f}"


def normalize_ticker(ticker: Any) -> str:
    """
    Normalize a ticker to uppercase without surrounding spaces.
    """

    if is_missing(ticker):
        return ""

    return str(ticker).strip().upper()


def normalize_text(value: Any) -> str:
    """
    Normalize text by converting to string and stripping spaces.
    """

    if is_missing(value):
        return ""

    return str(value).strip()


def dataframe_preview(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    rows: int = 10,
) -> str:
    """
    Return a printable preview of a DataFrame.

    Parameters
    ----------
    df:
        DataFrame to preview.
    columns:
        Optional list of preferred columns.
    rows:
        Number of rows.

    Returns
    -------
    str
        Console-friendly table.
    """

    if df.empty:
        return "Empty DataFrame"

    preview_df = df.copy()

    if columns:
        available_columns = [column for column in columns if column in preview_df.columns]
        if available_columns:
            preview_df = preview_df[available_columns]

    return preview_df.head(rows).to_string(index=False)


def print_dict(title: str, data: dict[str, Any]) -> None:
    """
    Print a dictionary as a simple bullet list.
    """

    print(title)

    if not data:
        print("- empty")
        return

    for key, value in data.items():
        print(f"- {key}: {value}")


def print_section(title: str) -> None:
    """
    Print a readable console section title.
    """

    print()
    print("=" * len(title))
    print(title)
    print("=" * len(title))


def select_existing_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
    """
    Return only columns that exist in a DataFrame.
    """

    return [column for column in columns if column in df.columns]


def sort_dataframe_if_possible(
    df: pd.DataFrame,
    by: list[str],
    ascending: bool | list[bool] = False,
) -> pd.DataFrame:
    """
    Sort a DataFrame only if all requested columns exist.

    If any column is missing, the original DataFrame is returned.
    """

    if df.empty:
        return df

    if not all(column in df.columns for column in by):
        return df

    return df.sort_values(by=by, ascending=ascending).reset_index(drop=True)


def summarize_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """
    Return a compact generic DataFrame summary.
    """

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
    }


def make_safe_filename(value: str) -> str:
    """
    Convert a text string into a simple safe filename fragment.
    """

    unsafe_chars = '<>:"/\\|?*'
    safe = str(value).strip()

    for char in unsafe_chars:
        safe = safe.replace(char, "_")

    safe = safe.replace(" ", "_")

    while "__" in safe:
        safe = safe.replace("__", "_")

    return safe.strip("_")


if __name__ == "__main__":
    print_section("Utils demo")

    sample_values = {
        "utc_now_iso": utc_now_iso(),
        "today_utc": today_utc_str(),
        "today_utc_compact": today_utc_str(separator=""),
        "format_usd": format_usd(1_234_567_890, compact=True),
        "format_percent": format_percent(0.1234),
        "format_number": format_number(1234567.8912),
        "format_integer": format_integer(1234567.8912),
        "normalize_ticker": normalize_ticker(" aapl "),
        "safe_bool_true": safe_bool("true"),
        "safe_bool_false": safe_bool("0"),
        "safe_filename": make_safe_filename("run report/demo: test.xlsx"),
    }

    print_dict("Sample utility outputs:", sample_values)

    demo_df = pd.DataFrame(
        [
            {"ticker": "AAPL", "score_priority": 81.73, "market_cap": 4_565_564_915_712},
            {"ticker": "MSFT", "score_priority": 72.11, "market_cap": 3_065_492_275_200},
        ]
    )

    print_section("DataFrame preview")
    print(dataframe_preview(demo_df, columns=["ticker", "score_priority", "market_cap"]))
