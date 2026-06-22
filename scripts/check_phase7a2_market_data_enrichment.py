
"""
Scout Finance — Phase 7A.2 free market data enrichment checker.

Run:
    ./.venv/Scripts/python.exe scripts/check_phase7a2_market_data_enrichment.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real_market_enriched.csv"
SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "market_data_enrichment_summary.json"
FAILURES = PROJECT_ROOT / "outputs" / "scouting" / "market_data_enrichment_failures.csv"

REQUIRED_COLUMNS = [
    "Symbol",
    "Name",
    "Exchange",
    "Country",
    "Sector",
    "Industry",
    "Market Cap",
    "Last Sale",
    "Volume",
    "Source",
    "has_core_market_data",
]


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7A.2 market data enrichment checker")
    print("=" * 76)

    for path in [OUTPUT, SUMMARY, FAILURES]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read summary: {exc}")
        return 1

    if summary.get("phase") != "7A.2":
        fail(f"Summary phase is not 7A.2: {summary.get('phase')}")
        return 1

    ok("Summary phase is 7A.2")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1

    ok("Summary status OK")

    if summary.get("openai_called") is False:
        ok("OpenAI was not called")
    else:
        fail("Summary indicates OpenAI was called")
        return 1

    if summary.get("paid_api_called") is False:
        ok("Paid API was not called")
    else:
        fail("Summary indicates paid API was called")
        return 1

    if summary.get("app_modified") is False:
        ok("app.py was not modified")
    else:
        fail("Summary indicates app.py was modified")
        return 1

    df = pd.read_csv(OUTPUT)

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    if missing:
        fail("Enriched CSV missing columns:")
        for column in missing:
            print(f"   - {column}")
        return 1

    ok("Required columns present")

    if df.empty:
        fail("Enriched CSV is empty")
        return 1

    ok(f"Enriched CSV has rows: {len(df)}")

    success_count = int(df["has_core_market_data"].astype(str).str.lower().isin(["true", "1"]).sum())

    if success_count == 0:
        warn("No rows have complete core market data. Check yfinance availability or ticker compatibility.")
    else:
        ok(f"Rows with complete core market data: {success_count}")

    print()
    print("Summary")
    print("-" * 76)
    print(f"Processed rows: {summary.get('processed_rows')}")
    print(f"Success with core market data: {summary.get('success_with_core_market_data')}")
    print(f"Failed/incomplete rows: {summary.get('failed_or_incomplete_rows')}")
    print(f"Fetched count: {summary.get('fetched_count')}")
    print(f"Cached count: {summary.get('cached_count')}")

    print()
    print("Result")
    print("-" * 76)
    ok("Phase 7A.2 market data enrichment outputs are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
