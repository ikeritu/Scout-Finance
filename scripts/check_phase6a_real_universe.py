"""
Scout Finance — Phase 6A real universe CSV checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase6a_real_universe.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_INPUT = PROJECT_ROOT / "data" / "raw" / "universe_source.csv"
GLOBAL_UNIVERSE = PROJECT_ROOT / "data" / "universe" / "global_universe.csv"

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


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 6A real universe checker")
    print("=" * 56)

    if RAW_INPUT.exists():
        ok(f"Raw input exists: {RAW_INPUT}")
    else:
        warn(f"Raw input missing: {RAW_INPUT}")

    if not GLOBAL_UNIVERSE.exists():
        fail(f"Global universe missing: {GLOBAL_UNIVERSE}")
        return 1

    ok(f"Global universe exists: {GLOBAL_UNIVERSE}")

    try:
        df = pd.read_csv(GLOBAL_UNIVERSE)
    except Exception as exc:
        fail(f"Cannot read global universe: {exc}")
        return 1

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    if missing:
        fail("Missing required columns:")
        for column in missing:
            print(f"   - {column}")
        return 1

    ok("Required columns present")
    print(f"Rows: {len(df)}")

    if df.empty:
        warn("Global universe is empty.")
        return 0

    duplicated = int(df["ticker"].duplicated(keep=False).sum())
    missing_market_cap = int(df["market_cap"].isna().sum())
    missing_price = int(df["price"].isna().sum())
    missing_volume = int(df["avg_volume_90d"].isna().sum())

    print()
    print("Quality")
    print("-" * 56)
    print(f"Duplicated ticker rows: {duplicated}")
    print(f"Missing market_cap: {missing_market_cap}")
    print(f"Missing price: {missing_price}")
    print(f"Missing avg_volume_90d: {missing_volume}")

    if duplicated == 0:
        ok("No duplicated ticker rows")
    else:
        warn("Duplicated ticker rows detected")

    ok("Phase 6A real universe CSV is ready for Phase 5B validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
