"""
Scout Finance — Phase 5B global universe loader.

Purpose:
- Load data/universe/global_universe.csv
- Validate minimum required columns
- Normalize basic fields
- Detect duplicates
- Calculate dollar_volume_90d
- Save data/universe/global_universe_validated.csv
- Save outputs/scouting/universe_validation_summary.json

This module does not call OpenAI.
It does not filter companies yet.
It only validates and prepares the universe.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.funnel_paths import (
    GLOBAL_UNIVERSE_PATH,
    GLOBAL_UNIVERSE_VALIDATED_PATH,
    UNIVERSE_VALIDATION_SUMMARY_PATH,
    ensure_funnel_directories,
)


REQUIRED_COLUMNS = [
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

OPTIONAL_COLUMNS = [
    "isin",
    "figi",
    "cusip",
    "ipo_date",
    "shares_outstanding",
    "free_float",
    "primary_listing",
    "adr_flag",
    "otc_flag",
    "etf_flag",
    "fund_flag",
    "preferred_flag",
    "warrant_flag",
    "spac_flag",
    "duplicate_group",
]

BOOLEAN_COLUMNS = [
    "is_active",
    "primary_listing",
    "adr_flag",
    "otc_flag",
    "etf_flag",
    "fund_flag",
    "preferred_flag",
    "warrant_flag",
    "spac_flag",
]

NUMERIC_COLUMNS = [
    "market_cap",
    "price",
    "avg_volume_30d",
    "avg_volume_90d",
    "shares_outstanding",
    "free_float",
]


def _utc_now_iso() -> str:
    """
    Return current UTC timestamp as ISO string.
    """

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_bool(value: Any) -> bool | None:
    """
    Convert common boolean-like values to bool.

    Returns None if the value cannot be interpreted.
    """

    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()

    if text in {"true", "1", "yes", "y", "si", "sí", "active", "activo"}:
        return True

    if text in {"false", "0", "no", "n", "inactive", "inactivo"}:
        return False

    return None


def _normalize_text_series(series: pd.Series) -> pd.Series:
    """
    Normalize text columns without destroying missing values.
    """

    return (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    )


def load_global_universe(path: Path = GLOBAL_UNIVERSE_PATH) -> pd.DataFrame:
    """
    Load global universe CSV.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Global universe file not found: {path}. "
            "Create data/universe/global_universe.csv first."
        )

    return pd.read_csv(path)


def validate_required_columns(df: pd.DataFrame) -> list[str]:
    """
    Return missing required columns.
    """

    return [column for column in REQUIRED_COLUMNS if column not in df.columns]


def normalize_global_universe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize basic fields and add optional missing columns.
    """

    normalized = df.copy()

    for column in OPTIONAL_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = pd.NA

    text_columns = [
        "ticker",
        "name",
        "exchange",
        "country",
        "region",
        "currency",
        "sector",
        "industry",
        "asset_type",
        "data_source",
        "last_updated",
        "isin",
        "figi",
        "cusip",
        "ipo_date",
        "duplicate_group",
    ]

    for column in text_columns:
        if column in normalized.columns:
            normalized[column] = _normalize_text_series(normalized[column])

    if "ticker" in normalized.columns:
        normalized["ticker"] = normalized["ticker"].astype("string").str.upper().str.strip()

    if "currency" in normalized.columns:
        normalized["currency"] = normalized["currency"].astype("string").str.upper().str.strip()

    if "asset_type" in normalized.columns:
        normalized["asset_type"] = normalized["asset_type"].astype("string").str.lower().str.strip()

    for column in NUMERIC_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    for column in BOOLEAN_COLUMNS:
        if column in normalized.columns:
            normalized[column] = normalized[column].apply(_safe_bool)

    normalized["dollar_volume_90d"] = (
        pd.to_numeric(normalized["price"], errors="coerce")
        * pd.to_numeric(normalized["avg_volume_90d"], errors="coerce")
    )

    normalized["universe_validation_status"] = "VALIDATED_STAGE0"
    normalized["universe_validation_date"] = _utc_now_iso()

    return normalized


def build_validation_summary(df: pd.DataFrame, missing_required_columns: list[str]) -> dict[str, Any]:
    """
    Build universe validation summary.
    """

    ticker_duplicates = 0

    if "ticker" in df.columns:
        ticker_duplicates = int(df["ticker"].duplicated(keep=False).sum())

    summary = {
        "phase": "5B",
        "created_at": _utc_now_iso(),
        "input_companies": int(len(df)),
        "missing_required_columns": missing_required_columns,
        "has_required_columns": len(missing_required_columns) == 0,
        "duplicated_ticker_rows": ticker_duplicates,
        "missing_values": {},
        "counts": {},
    }

    for column in REQUIRED_COLUMNS:
        if column in df.columns:
            summary["missing_values"][column] = int(df[column].isna().sum())

    if "market_cap" in df.columns:
        summary["counts"]["missing_market_cap"] = int(df["market_cap"].isna().sum())
        summary["counts"]["market_cap_positive"] = int((pd.to_numeric(df["market_cap"], errors="coerce") > 0).sum())

    if "price" in df.columns:
        summary["counts"]["missing_price"] = int(df["price"].isna().sum())
        summary["counts"]["price_positive"] = int((pd.to_numeric(df["price"], errors="coerce") > 0).sum())

    if "avg_volume_90d" in df.columns:
        summary["counts"]["missing_avg_volume_90d"] = int(df["avg_volume_90d"].isna().sum())
        summary["counts"]["avg_volume_90d_positive"] = int(
            (pd.to_numeric(df["avg_volume_90d"], errors="coerce") > 0).sum()
        )

    if "asset_type" in df.columns:
        summary["asset_type_distribution"] = (
            df["asset_type"].fillna("MISSING").astype(str).value_counts().head(20).to_dict()
        )

    if "country" in df.columns:
        summary["country_distribution_top20"] = (
            df["country"].fillna("MISSING").astype(str).value_counts().head(20).to_dict()
        )

    if "sector" in df.columns:
        summary["sector_distribution_top20"] = (
            df["sector"].fillna("MISSING").astype(str).value_counts().head(20).to_dict()
        )

    return summary


def save_validation_outputs(
    validated_df: pd.DataFrame,
    summary: dict[str, Any],
    validated_path: Path = GLOBAL_UNIVERSE_VALIDATED_PATH,
    summary_path: Path = UNIVERSE_VALIDATION_SUMMARY_PATH,
) -> None:
    """
    Save validated CSV and summary JSON.
    """

    ensure_funnel_directories()

    validated_df.to_csv(validated_path, index=False, encoding="utf-8-sig")

    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def validate_and_prepare_global_universe(
    input_path: Path = GLOBAL_UNIVERSE_PATH,
    validated_path: Path = GLOBAL_UNIVERSE_VALIDATED_PATH,
    summary_path: Path = UNIVERSE_VALIDATION_SUMMARY_PATH,
) -> dict[str, Any]:
    """
    Main Phase 5B function.
    """

    ensure_funnel_directories()

    raw_df = load_global_universe(input_path)
    missing_required_columns = validate_required_columns(raw_df)

    if missing_required_columns:
        summary = build_validation_summary(raw_df, missing_required_columns)
        summary["status"] = "FAILED_MISSING_REQUIRED_COLUMNS"
        summary["error"] = (
            "Missing required columns: "
            + ", ".join(missing_required_columns)
        )
        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return summary

    validated_df = normalize_global_universe(raw_df)
    summary = build_validation_summary(validated_df, missing_required_columns)
    summary["status"] = "OK"

    save_validation_outputs(
        validated_df=validated_df,
        summary=summary,
        validated_path=validated_path,
        summary_path=summary_path,
    )

    return summary


def print_summary(summary: dict[str, Any]) -> None:
    """
    Print summary in terminal-friendly format.
    """

    print("Scout Finance — Phase 5B global universe loader")
    print("=" * 52)
    print(f"Status: {summary.get('status')}")
    print(f"Input companies: {summary.get('input_companies')}")
    print(f"Has required columns: {summary.get('has_required_columns')}")
    print(f"Duplicated ticker rows: {summary.get('duplicated_ticker_rows')}")

    if summary.get("missing_required_columns"):
        print()
        print("Missing required columns:")
        for column in summary["missing_required_columns"]:
            print(f"- {column}")

    print()
    print("Output files:")
    print(f"- {GLOBAL_UNIVERSE_VALIDATED_PATH}")
    print(f"- {UNIVERSE_VALIDATION_SUMMARY_PATH}")
