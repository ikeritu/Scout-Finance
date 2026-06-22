"""
Universe module.

This module loads, validates and cleans the company universe used by the
equity research MVP.

Current scope:
- Read universe CSV files.
- Validate required columns.
- Clean tickers and basic metadata.
- Return valid tickers and summary information.

Not included in this phase:
- Market data download.
- yfinance integration.
- Scoring.
- OpenAI analysis.
- Streamlit UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEMO_UNIVERSE_PATH = PROJECT_ROOT / "data" / "demo" / "demo_universe.csv"
REAL_UNIVERSE_PATH = PROJECT_ROOT / "data" / "real" / "universe.csv"


REQUIRED_COLUMNS = [
    "ticker",
    "company_name",
    "exchange",
    "country",
    "currency",
    "sector",
    "industry",
    "asset_type",
    "is_active",
    "source",
    "last_updated",
]


TEXT_COLUMNS = [
    "ticker",
    "company_name",
    "exchange",
    "country",
    "currency",
    "sector",
    "industry",
    "asset_type",
    "source",
    "last_updated",
]


def load_universe(mode: str = "demo") -> pd.DataFrame:
    """
    Load the universe CSV for the selected mode.

    Parameters
    ----------
    mode:
        Either "demo" or "real".

    Returns
    -------
    pandas.DataFrame
        Raw universe dataframe loaded from CSV.

    Raises
    ------
    ValueError
        If mode is not "demo" or "real".
    FileNotFoundError
        If the expected universe CSV does not exist.
    """

    if mode not in {"demo", "real"}:
        raise ValueError("Invalid mode. Expected 'demo' or 'real'.")

    csv_path = DEMO_UNIVERSE_PATH if mode == "demo" else REAL_UNIVERSE_PATH

    if not csv_path.exists():
        raise FileNotFoundError(f"Universe file not found: {csv_path}")

    return pd.read_csv(csv_path)


def validate_universe_columns(df: pd.DataFrame) -> None:
    """
    Validate that the dataframe contains all required universe columns.

    Parameters
    ----------
    df:
        Universe dataframe.

    Raises
    ------
    ValueError
        If one or more required columns are missing.
    """

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    if missing_columns:
        raise ValueError(
            "Universe CSV is missing required columns: "
            + ", ".join(missing_columns)
        )


def _to_bool(value: Any) -> bool:
    """
    Convert common boolean representations to bool.

    Accepted true values:
    - True
    - 1
    - "true"
    - "1"
    - "yes"
    - "y"

    Any other value is treated as False.
    """

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    if isinstance(value, (int, float)):
        return value == 1

    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}

    return False


def clean_universe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and filter the universe dataframe.

    Cleaning rules:
    - Remove rows with empty ticker.
    - Convert ticker to uppercase.
    - Strip leading/trailing spaces from text columns.
    - Remove duplicated tickers.
    - Keep only USA companies.
    - Keep only USD currency.
    - Keep only common stocks.
    - Keep only active companies.
    - Reset dataframe index.

    Parameters
    ----------
    df:
        Raw universe dataframe.

    Returns
    -------
    pandas.DataFrame
        Cleaned universe dataframe.
    """

    df_clean = df.copy()

    for column in TEXT_COLUMNS:
        if column in df_clean.columns:
            df_clean[column] = df_clean[column].astype("string").str.strip()

    df_clean = df_clean.dropna(subset=["ticker"])
    df_clean = df_clean[df_clean["ticker"].astype(str).str.strip() != ""]

    df_clean["ticker"] = df_clean["ticker"].astype(str).str.strip().str.upper()
    df_clean["country"] = df_clean["country"].astype(str).str.strip().str.upper()
    df_clean["currency"] = df_clean["currency"].astype(str).str.strip().str.upper()
    df_clean["asset_type"] = (
        df_clean["asset_type"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace(
            {
                "equity": "common_stock",
                "stock": "common_stock",
                "common stock": "common_stock",
                "common_stock": "common_stock",
                "commonstock": "common_stock",
            }
        )
    )
    df_clean["is_active"] = df_clean["is_active"].apply(_to_bool)

    df_clean = df_clean.drop_duplicates(subset=["ticker"], keep="first")

    df_clean = df_clean[
        (df_clean["country"] == "USA")
        & (df_clean["currency"] == "USD")
        & (df_clean["asset_type"] == "common_stock")
        & (df_clean["is_active"] == True)  # noqa: E712
    ]

    return df_clean.reset_index(drop=True)


def get_valid_tickers(df: pd.DataFrame) -> list[str]:
    """
    Return a list of clean valid tickers.

    Parameters
    ----------
    df:
        Cleaned universe dataframe.

    Returns
    -------
    list[str]
        List of tickers.
    """

    return df["ticker"].dropna().astype(str).str.upper().tolist()


def summarize_universe(df: pd.DataFrame) -> dict[str, Any]:
    """
    Create a compact summary of the cleaned universe.

    Parameters
    ----------
    df:
        Cleaned universe dataframe.

    Returns
    -------
    dict
        Summary with company count, unique tickers, sector count,
        exchange count and first five tickers.
    """

    return {
        "total_companies": int(len(df)),
        "unique_tickers": int(df["ticker"].nunique()),
        "sectors_count": int(df["sector"].nunique()),
        "exchanges_count": int(df["exchange"].nunique()),
        "first_5_tickers": get_valid_tickers(df)[:5],
    }


def validate_and_load_universe(mode: str = "demo") -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Load, validate, clean and summarize the universe.

    Parameters
    ----------
    mode:
        Either "demo" or "real".

    Returns
    -------
    tuple[pandas.DataFrame, dict]
        Cleaned dataframe and summary dictionary.
    """

    df = load_universe(mode=mode)
    validate_universe_columns(df)
    df_clean = clean_universe(df)
    summary = summarize_universe(df_clean)

    return df_clean, summary


if __name__ == "__main__":
    try:
        universe_df, universe_summary = validate_and_load_universe(mode="demo")
        valid_tickers = get_valid_tickers(universe_df)

        print("Universe summary:")
        for key, value in universe_summary.items():
            print(f"- {key}: {value}")

        print("\nFirst 10 valid tickers:")
        print(valid_tickers[:10])

    except Exception as exc:
        print(f"Error loading universe: {exc}")
        raise
