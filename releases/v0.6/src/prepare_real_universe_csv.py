"""
Scout Finance — Phase 6A prepare real universe CSV.

Purpose:
- Read a flexible real-world CSV from data/raw/universe_source.csv
- Normalize it into data/universe/global_universe.csv
- Do not call external APIs
- Do not call OpenAI
- Do not modify app.py

Run from project root:

    ./.venv/Scripts/python.exe -m src.prepare_real_universe_csv

Optional:

    ./.venv/Scripts/python.exe -m src.prepare_real_universe_csv --input data/raw/my_file.csv --source nasdaq_csv
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.funnel_paths import GLOBAL_UNIVERSE_PATH, ensure_funnel_directories


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "universe_source.csv"


OUTPUT_COLUMNS = [
    "ticker",
    "name",
    "exchange",
    "country",
    "region",
    "currency",
    "sector",
    "industry",
    "asset_type",
    "is_active",
    "market_cap",
    "price",
    "avg_volume_30d",
    "avg_volume_90d",
    "data_source",
    "last_updated",
]


COLUMN_ALIASES = {
    "ticker": ["ticker", "symbol", "Symbol", "Ticker", "SYMBOL"],
    "name": ["name", "Name", "company", "company_name", "Company Name", "Security Name"],
    "exchange": ["exchange", "Exchange", "Exchange Name", "market", "Market"],
    "country": ["country", "Country"],
    "sector": ["sector", "Sector"],
    "industry": ["industry", "Industry"],
    "market_cap": ["market_cap", "Market Cap", "marketCap", "MarketCap", "Mkt Cap"],
    "price": ["price", "Price", "Last Sale", "lastSale", "Last Price"],
    "volume": ["volume", "Volume", "avg_volume", "Avg Volume", "Average Volume"],
    "avg_volume_30d": ["avg_volume_30d", "Average Volume 30D", "avgVolume30d"],
    "avg_volume_90d": ["avg_volume_90d", "Average Volume 90D", "avgVolume90d"],
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
    aliases = COLUMN_ALIASES.get(target, [target])
    column = _find_column(df, aliases)

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
        return float(text) * multiplier
    except Exception:
        return None


def _normalize_exchange(value: Any) -> str:
    if pd.isna(value):
        return "UNKNOWN"

    text = str(value).strip().upper()

    mapping = {
        "NASDAQGS": "NASDAQ",
        "NASDAQGM": "NASDAQ",
        "NASDAQCM": "NASDAQ",
        "NAS": "NASDAQ",
        "NYSE ARCA": "ARCA",
        "NYSEAMERICAN": "AMEX",
        "NYSE AMERICAN": "AMEX",
    }

    return mapping.get(text, text or "UNKNOWN")


def _infer_region(country: str) -> str:
    country_upper = str(country).upper().strip()

    if country_upper in {"USA", "US", "UNITED STATES", "UNITED STATES OF AMERICA"}:
        return "North America"

    if country_upper in {"CANADA", "CA"}:
        return "North America"

    return "Unknown"


def normalize_real_universe_csv(
    input_path: Path = DEFAULT_INPUT_PATH,
    output_path: Path = GLOBAL_UNIVERSE_PATH,
    data_source: str = "manual_csv",
    default_country: str = "USA",
    default_currency: str = "USD",
) -> pd.DataFrame:
    ensure_funnel_directories()
    input_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {input_path}. "
            "Place a real universe CSV in data/raw/universe_source.csv first."
        )

    raw = pd.read_csv(input_path)

    if raw.empty:
        raise ValueError("Input CSV is empty.")

    result = pd.DataFrame()

    result["ticker"] = _get_series(raw, "ticker").astype("string").str.strip().str.upper()
    result["name"] = _get_series(raw, "name").astype("string").str.strip()
    result["name"] = result["name"].fillna(result["ticker"])

    result["exchange"] = _get_series(raw, "exchange", "UNKNOWN").apply(_normalize_exchange)

    result["country"] = _get_series(raw, "country", default_country).fillna(default_country)
    result["country"] = result["country"].astype("string").str.strip()
    result["region"] = result["country"].apply(_infer_region)

    result["currency"] = default_currency

    result["sector"] = _get_series(raw, "sector", "Unknown").fillna("Unknown").astype("string").str.strip()
    result["industry"] = _get_series(raw, "industry", "Unknown").fillna("Unknown").astype("string").str.strip()

    result["asset_type"] = "common_stock"
    result["is_active"] = True

    result["market_cap"] = _get_series(raw, "market_cap").apply(_parse_number)
    result["price"] = _get_series(raw, "price").apply(_parse_number)

    volume = _get_series(raw, "volume").apply(_parse_number)
    avg_volume_30d = _get_series(raw, "avg_volume_30d").apply(_parse_number)
    avg_volume_90d = _get_series(raw, "avg_volume_90d").apply(_parse_number)

    result["avg_volume_30d"] = avg_volume_30d.fillna(volume)
    result["avg_volume_90d"] = avg_volume_90d.fillna(volume)

    result["data_source"] = data_source
    result["last_updated"] = _utc_today()

    result = result[OUTPUT_COLUMNS]

    result = result[result["ticker"].notna()]
    result = result[result["ticker"].astype(str).str.len() > 0]
    result = result.drop_duplicates(subset=["ticker"], keep="first")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, encoding="utf-8-sig")

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH))
    parser.add_argument("--output", default=str(GLOBAL_UNIVERSE_PATH))
    parser.add_argument("--source", default="manual_csv")
    parser.add_argument("--country", default="USA")
    parser.add_argument("--currency", default="USD")
    args = parser.parse_args()

    df = normalize_real_universe_csv(
        input_path=Path(args.input),
        output_path=Path(args.output),
        data_source=args.source,
        default_country=args.country,
        default_currency=args.currency,
    )

    print("Scout Finance — Phase 6A prepare real universe CSV")
    print("=" * 58)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Rows written: {len(df)}")
    print("No OpenAI call. app.py not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
