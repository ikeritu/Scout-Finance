
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real.csv"
SUMMARY = PROJECT_ROOT / "outputs" / "scouting" / "free_us_universe_download_summary.json"

REQUIRED_COLUMNS = [
    "Symbol", "Name", "Exchange", "Country", "Sector",
    "Industry", "Market Cap", "Last Sale", "Volume", "Source",
]


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7A.1 free USA universe checker")
    print("=" * 72)

    if not OUTPUT.exists():
        fail(f"Missing output CSV: {OUTPUT}")
        print("Run first: .\\.venv\\Scripts\\python.exe -m src.download_free_us_universe")
        return 1
    ok(f"Output CSV exists: {OUTPUT}")

    if not SUMMARY.exists():
        fail(f"Missing summary JSON: {SUMMARY}")
        return 1
    ok(f"Summary JSON exists: {SUMMARY}")

    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read summary: {exc}")
        return 1

    if summary.get("phase") != "7A.1":
        fail(f"Summary phase is not 7A.1: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7A.1")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    for flag, label in [
        ("openai_called", "OpenAI was not called"),
        ("paid_api_called", "Paid API was not called"),
        ("app_modified", "app.py was not modified"),
        ("release_v0_6_modified", "release v0.6 was not modified"),
    ]:
        if summary.get(flag) is False:
            ok(label)
        else:
            fail(f"Summary flag invalid: {flag}")
            return 1

    try:
        df = pd.read_csv(OUTPUT)
    except Exception as exc:
        fail(f"Cannot read output CSV: {exc}")
        return 1

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        fail("Output CSV missing columns:")
        for column in missing_columns:
            print(f"   - {column}")
        return 1
    ok("Required columns present")

    if df.empty:
        fail("Output CSV is empty")
        return 1
    ok(f"Output CSV has rows: {len(df)}")

    duplicate_symbols = int(df["Symbol"].duplicated(keep=False).sum())
    if duplicate_symbols == 0:
        ok("No duplicated symbols")
    else:
        warn(f"Duplicated symbols found: {duplicate_symbols}")

    print()
    print("Summary")
    print("-" * 72)
    print(f"Rows: {len(df)}")
    print(f"Summary output_rows: {summary.get('output_rows')}")
    print(f"Exchanges: {df['Exchange'].value_counts(dropna=False).to_dict()}")
    print(f"Sources: {df['Source'].value_counts(dropna=False).to_dict()}")

    print()
    print("Result")
    print("-" * 72)
    ok("Phase 7A.1 free USA universe is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
