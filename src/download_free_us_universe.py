
"""
Scout Finance — Phase 7A.1 free USA universe downloader.

Downloads free Nasdaq Trader symbol directories and creates:
    data/raw/universe_source_real.csv

Run:
    ./.venv/Scripts/python.exe -m src.download_free_us_universe
"""

from __future__ import annotations

import argparse
import io
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_PATH = RAW_DIR / "universe_source_real.csv"
SUMMARY_PATH = PROJECT_ROOT / "outputs" / "scouting" / "free_us_universe_download_summary.json"

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _download_text(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ScoutFinance/0.6 educational personal project"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _read_pipe_file(text: str) -> pd.DataFrame:
    lines = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.lower().startswith("file creation time"):
            continue
        lines.append(clean)

    if not lines:
        return pd.DataFrame()

    return pd.read_csv(io.StringIO("\n".join(lines)), sep="|")


def _normalize_nasdaq_listed(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    result = pd.DataFrame()
    result["Symbol"] = df.get("Symbol", pd.Series(dtype="object")).astype("string").str.strip()
    result["Name"] = df.get("Security Name", pd.Series(dtype="object")).astype("string").str.strip()
    result["Exchange"] = "NASDAQ"
    result["Country"] = "USA"
    result["Sector"] = ""
    result["Industry"] = ""
    result["Market Cap"] = ""
    result["Last Sale"] = ""
    result["Volume"] = ""
    result["ETF"] = df.get("ETF", pd.Series(["N"] * len(df))).astype("string").str.strip()
    result["Test Issue"] = df.get("Test Issue", pd.Series(["N"] * len(df))).astype("string").str.strip()
    result["Source"] = "nasdaqlisted"
    return result


def _normalize_other_listed(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    exchange_map = {"A": "AMEX", "N": "NYSE", "P": "ARCA", "Z": "BATS", "V": "IEXG"}

    result = pd.DataFrame()
    result["Symbol"] = df.get("ACT Symbol", pd.Series(dtype="object")).astype("string").str.strip()
    result["Name"] = df.get("Security Name", pd.Series(dtype="object")).astype("string").str.strip()

    exchange_series = df.get("Exchange", pd.Series(["UNKNOWN"] * len(df))).astype("string").str.strip()
    result["Exchange"] = exchange_series.map(exchange_map).fillna(exchange_series)

    result["Country"] = "USA"
    result["Sector"] = ""
    result["Industry"] = ""
    result["Market Cap"] = ""
    result["Last Sale"] = ""
    result["Volume"] = ""
    result["ETF"] = df.get("ETF", pd.Series(["N"] * len(df))).astype("string").str.strip()
    result["Test Issue"] = df.get("Test Issue", pd.Series(["N"] * len(df))).astype("string").str.strip()
    result["Source"] = "otherlisted"
    return result


def _filter_universe(df: pd.DataFrame, include_etfs: bool = False, include_test_issues: bool = False) -> pd.DataFrame:
    if df.empty:
        return df

    result = df.copy()
    result = result[result["Symbol"].notna()]
    result = result[result["Symbol"].astype(str).str.len() > 0]
    result = result[~result["Symbol"].astype(str).str.contains("File Creation Time", case=False, na=False)]

    if not include_etfs and "ETF" in result.columns:
        result = result[result["ETF"].fillna("N").astype(str).str.upper() != "Y"]

    if not include_test_issues and "Test Issue" in result.columns:
        result = result[result["Test Issue"].fillna("N").astype(str).str.upper() != "Y"]

    result = result[~result["Symbol"].astype(str).str.contains(r"[$\^/]", regex=True, na=False)]
    result = result.drop_duplicates(subset=["Symbol"], keep="first")
    return result.reset_index(drop=True)


def download_free_us_universe(
    output_path: Path = OUTPUT_PATH,
    include_etfs: bool = False,
    include_test_issues: bool = False,
    timeout: int = 30,
) -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    nasdaq_text = _download_text(NASDAQ_LISTED_URL, timeout=timeout)
    other_text = _download_text(OTHER_LISTED_URL, timeout=timeout)

    nasdaq_raw = _read_pipe_file(nasdaq_text)
    other_raw = _read_pipe_file(other_text)

    combined = pd.concat(
        [_normalize_nasdaq_listed(nasdaq_raw), _normalize_other_listed(other_raw)],
        ignore_index=True,
    )
    filtered = _filter_universe(
        combined,
        include_etfs=include_etfs,
        include_test_issues=include_test_issues,
    )

    output_columns = [
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
    ]

    for column in output_columns:
        if column not in filtered.columns:
            filtered[column] = ""

    final_df = filtered[output_columns].copy()
    final_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    summary = {
        "phase": "7A.1",
        "created_at": _utc_now_iso(),
        "status": "OK",
        "sources": {
            "nasdaqlisted": NASDAQ_LISTED_URL,
            "otherlisted": OTHER_LISTED_URL,
        },
        "raw_rows": {
            "nasdaqlisted": int(len(nasdaq_raw)),
            "otherlisted": int(len(other_raw)),
        },
        "output_rows": int(len(final_df)),
        "output_path": str(output_path),
        "include_etfs": include_etfs,
        "include_test_issues": include_test_issues,
        "exchange_distribution": final_df["Exchange"].value_counts(dropna=False).to_dict() if not final_df.empty else {},
        "source_distribution": final_df["Source"].value_counts(dropna=False).to_dict() if not final_df.empty else {},
        "openai_called": False,
        "paid_api_called": False,
        "app_modified": False,
        "release_v0_6_modified": False,
        "notes": [
            "Market Cap, Last Sale, Volume, Sector and Industry are intentionally blank in this free base universe.",
            "Use Phase 7A pilot to test normalization and Stage 1 behavior.",
            "Stage 1 will reject rows missing market data until a market-data enrichment step is added.",
        ],
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7A.1 free USA universe downloader")
    print("=" * 72)
    print(f"Status: {summary.get('status')}")
    print(f"Output rows: {summary.get('output_rows')}")
    print(f"Output path: {summary.get('output_path')}")
    print(f"OpenAI called: {summary.get('openai_called')}")
    print(f"Paid API called: {summary.get('paid_api_called')}")
    print(f"app.py modified: {summary.get('app_modified')}")
    print(f"release v0.6 modified: {summary.get('release_v0_6_modified')}")
    print()
    print("Next command")
    print("-" * 72)
    print(".\\.venv\\Scripts\\python.exe -m src.run_real_universe_pilot --input data/raw/universe_source_real.csv --limit 500 --source nasdaqtrader_free")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    parser.add_argument("--include-etfs", action="store_true")
    parser.add_argument("--include-test-issues", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    summary = download_free_us_universe(
        output_path=Path(args.output),
        include_etfs=args.include_etfs,
        include_test_issues=args.include_test_issues,
        timeout=args.timeout,
    )
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
