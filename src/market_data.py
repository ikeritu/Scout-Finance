"""
Market data module.

This module downloads basic historical market data with yfinance and builds a
simple per-company market snapshot for the equity research MVP.

Current scope:
- Download price and volume history.
- Calculate basic technical/market metrics.
- Retrieve basic company metadata from yfinance.
- Build a one-row-per-ticker market snapshot.

Not included in this phase:
- Scoring.
- OpenAI analysis.
- Streamlit UI.
- Hard filters.
- Backtesting or validation.
- Exporting.
- Advanced cache.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf

from src.universe import validate_and_load_universe


PRICE_COLUMNS = ["Close", "Adj Close", "Volume"]


def _safe_float(value: Any) -> float | None:
    """
    Convert a value to float when possible.

    Returns None when the value is missing or cannot be converted.
    """

    if value is None or pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Any) -> bool | None:
    """
    Convert a value to bool while preserving missing values as None.
    """

    if value is None or pd.isna(value):
        return None

    return bool(value)


def _get_close_series(history_df: pd.DataFrame) -> pd.Series:
    """
    Return the preferred close price series from a history dataframe.

    Uses 'Close' when available. Falls back to 'Adj Close' if needed.
    """

    if "Close" in history_df.columns:
        return history_df["Close"].dropna()

    if "Adj Close" in history_df.columns:
        return history_df["Adj Close"].dropna()

    return pd.Series(dtype="float64")


def download_price_history(
    tickers: list[str],
    period: str = "1y",
) -> dict[str, pd.DataFrame]:
    """
    Download historical price and volume data for a list of tickers.

    Parameters
    ----------
    tickers:
        List of ticker symbols.
    period:
        yfinance period string. Default is "1y".

    Returns
    -------
    dict[str, pandas.DataFrame]
        Dictionary where each key is a ticker and each value is its historical
        dataframe. Failed or empty tickers are returned as empty dataframes.
    """

    clean_tickers = [str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()]

    if not clean_tickers:
        return {}

    histories: dict[str, pd.DataFrame] = {}

    try:
        raw_data = yf.download(
            tickers=clean_tickers,
            period=period,
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )
    except Exception as exc:
        print(f"Bulk yfinance download failed: {exc}")
        raw_data = pd.DataFrame()

    for ticker in clean_tickers:
        try:
            if raw_data.empty:
                history_df = yf.download(
                    tickers=ticker,
                    period=period,
                    interval="1d",
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                )
            elif isinstance(raw_data.columns, pd.MultiIndex):
                if ticker in raw_data.columns.get_level_values(0):
                    history_df = raw_data[ticker].copy()
                else:
                    history_df = pd.DataFrame()
            else:
                # yfinance returns a flat dataframe when only one ticker is downloaded.
                history_df = raw_data.copy()

            if history_df is None or history_df.empty:
                histories[ticker] = pd.DataFrame()
                continue

            available_columns = [column for column in PRICE_COLUMNS if column in history_df.columns]
            histories[ticker] = history_df[available_columns].dropna(how="all").copy()

        except Exception as exc:
            print(f"Error downloading history for {ticker}: {exc}")
            histories[ticker] = pd.DataFrame()

    return histories


def calculate_ticker_metrics(ticker: str, history_df: pd.DataFrame) -> dict[str, Any]:
    """
    Calculate basic market metrics for one ticker.

    Parameters
    ----------
    ticker:
        Ticker symbol.
    history_df:
        Historical price dataframe for that ticker.

    Returns
    -------
    dict
        Dictionary with price, volume, moving average and change metrics.
        Missing values are returned as None.
    """

    metrics: dict[str, Any] = {
        "ticker": ticker,
        "price": None,
        "previous_close": None,
        "volume": None,
        "avg_volume_50d": None,
        "relative_volume": None,
        "change_1d": None,
        "change_5d": None,
        "change_20d": None,
        "ma20": None,
        "ma50": None,
        "above_ma20": None,
        "above_ma50": None,
        "high_52w": None,
        "low_52w": None,
        "distance_to_52w_high": None,
        "distance_to_52w_low": None,
    }

    if history_df is None or history_df.empty:
        return metrics

    close = _get_close_series(history_df)
    volume = history_df["Volume"].dropna() if "Volume" in history_df.columns else pd.Series(dtype="float64")

    if close.empty:
        return metrics

    price = _safe_float(close.iloc[-1])
    previous_close = _safe_float(close.iloc[-2]) if len(close) >= 2 else None
    latest_volume = _safe_float(volume.iloc[-1]) if not volume.empty else None

    avg_volume_50d = _safe_float(volume.tail(50).mean()) if len(volume) > 0 else None
    relative_volume = (
        latest_volume / avg_volume_50d
        if latest_volume is not None and avg_volume_50d not in {None, 0}
        else None
    )

    ma20 = _safe_float(close.tail(20).mean()) if len(close) >= 20 else None
    ma50 = _safe_float(close.tail(50).mean()) if len(close) >= 50 else None

    high_52w = _safe_float(close.max()) if len(close) > 0 else None
    low_52w = _safe_float(close.min()) if len(close) > 0 else None

    def calculate_change(days: int) -> float | None:
        if price is None or len(close) <= days:
            return None

        past_price = _safe_float(close.iloc[-days - 1])
        if past_price in {None, 0}:
            return None

        return (price / past_price) - 1

    metrics.update(
        {
            "price": price,
            "previous_close": previous_close,
            "volume": latest_volume,
            "avg_volume_50d": avg_volume_50d,
            "relative_volume": relative_volume,
            "change_1d": calculate_change(1),
            "change_5d": calculate_change(5),
            "change_20d": calculate_change(20),
            "ma20": ma20,
            "ma50": ma50,
            "above_ma20": _safe_bool(price > ma20) if price is not None and ma20 is not None else None,
            "above_ma50": _safe_bool(price > ma50) if price is not None and ma50 is not None else None,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "distance_to_52w_high": (price / high_52w) - 1 if price is not None and high_52w not in {None, 0} else None,
            "distance_to_52w_low": (price / low_52w) - 1 if price is not None and low_52w not in {None, 0} else None,
        }
    )

    return metrics


def get_company_info(ticker: str) -> dict[str, Any]:
    """
    Retrieve basic company information from yfinance.

    Parameters
    ----------
    ticker:
        Ticker symbol.

    Returns
    -------
    dict
        Basic company metadata. Missing fields are returned as None.
    """

    default_info = {
        "company_name": None,
        "sector": None,
        "industry": None,
        "exchange": None,
        "currency": None,
        "market_cap": None,
    }

    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as exc:
        print(f"Error getting company info for {ticker}: {exc}")
        return default_info

    return {
        "company_name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "exchange": info.get("exchange"),
        "currency": info.get("currency"),
        "market_cap": info.get("marketCap"),
    }


def build_market_snapshot(universe_df: pd.DataFrame, period: str = "1y") -> pd.DataFrame:
    """
    Build a basic market snapshot for each ticker in the universe.

    Parameters
    ----------
    universe_df:
        Clean universe dataframe from src.universe.
    period:
        Historical download period. Default is "1y".

    Returns
    -------
    pandas.DataFrame
        One row per ticker combining universe metadata, yfinance company info
        and calculated market metrics.
    """

    tickers = universe_df["ticker"].dropna().astype(str).str.upper().tolist()
    histories = download_price_history(tickers=tickers, period=period)

    rows: list[dict[str, Any]] = []

    for _, company_row in universe_df.iterrows():
        ticker = str(company_row["ticker"]).strip().upper()
        history_df = histories.get(ticker, pd.DataFrame())

        metrics = calculate_ticker_metrics(ticker=ticker, history_df=history_df)
        company_info = get_company_info(ticker=ticker)

        row = {
            "ticker": ticker,
            "company_name": company_info.get("company_name") or company_row.get("company_name"),
            "sector": company_info.get("sector") or company_row.get("sector"),
            "industry": company_info.get("industry") or company_row.get("industry"),
            "exchange": company_info.get("exchange") or company_row.get("exchange"),
            "country": company_row.get("country"),
            "currency": company_info.get("currency") or company_row.get("currency"),
            "asset_type": company_row.get("asset_type"),
            "is_active": company_row.get("is_active"),
            "source": company_row.get("source"),
            "last_updated": company_row.get("last_updated"),
            "market_cap": company_info.get("market_cap"),
            "data_source": "yfinance",
        }

        row.update(metrics)
        rows.append(row)

    return pd.DataFrame(rows)


def summarize_market_snapshot(df: pd.DataFrame) -> dict[str, Any]:
    """
    Summarize a market snapshot dataframe.

    Parameters
    ----------
    df:
        Market snapshot dataframe.

    Returns
    -------
    dict
        Compact summary of the snapshot.
    """

    avg_relative_volume = None
    if "relative_volume" in df.columns and df["relative_volume"].notna().any():
        avg_relative_volume = float(df["relative_volume"].mean())

    return {
        "total_rows": int(len(df)),
        "tickers_with_price": int(df["price"].notna().sum()) if "price" in df.columns else 0,
        "tickers_with_market_cap": int(df["market_cap"].notna().sum()) if "market_cap" in df.columns else 0,
        "avg_relative_volume": avg_relative_volume,
        "first_5_tickers": df["ticker"].dropna().astype(str).head(5).tolist() if "ticker" in df.columns else [],
    }


if __name__ == "__main__":
    try:
        universe_df, universe_summary = validate_and_load_universe(mode="demo")
        print("Universe loaded:")
        print(universe_summary)

        snapshot_df = build_market_snapshot(universe_df=universe_df, period="1y")
        snapshot_summary = summarize_market_snapshot(snapshot_df)

        print("\nMarket snapshot summary:")
        for key, value in snapshot_summary.items():
            print(f"- {key}: {value}")

        preview_columns = [
            "ticker",
            "company_name",
            "price",
            "previous_close",
            "volume",
            "avg_volume_50d",
            "relative_volume",
            "change_1d",
            "change_5d",
            "change_20d",
            "market_cap",
        ]
        available_preview_columns = [column for column in preview_columns if column in snapshot_df.columns]

        print("\nSnapshot preview:")
        print(snapshot_df[available_preview_columns].head(10).to_string(index=False))

    except Exception as exc:
        print(f"Error building market snapshot: {exc}")
        raise
