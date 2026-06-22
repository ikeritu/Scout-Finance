
"""
Scout Finance — Phase 7A.2 free market data enrichment.

Purpose:
- Read data/raw/universe_source_real.csv
- Enrich a limited number of symbols with free market data using yfinance
- Write data/raw/universe_source_real_market_enriched.csv
- Keep a local cache to avoid requesting the same symbols repeatedly

This module:
- does not call OpenAI;
- does not use paid APIs;
- does not modify app.py;
- does not modify releases/v0.6;
- does not execute Stage 1/2/3.

Important:
- yfinance is useful for local testing, but it is not a guaranteed official market-data API.
- Use small limits first: 50, 100, then 500.

Install dependency if needed:
    ./.venv/Scripts/python.exe -m pip install yfinance

Run:
    ./.venv/Scripts/python.exe -m src.enrich_market_data_yfinance --limit 100
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real_market_enriched.csv"

CACHE_DIR = PROJECT_ROOT / "data" / "cache"
CACHE_PATH = CACHE_DIR / "yfinance_market_data_cache.json"

SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"
SUMMARY_PATH = SCOUTING_OUTPUTS_DIR / "market_data_enrichment_summary.json"
FAILURES_PATH = SCOUTING_OUTPUTS_DIR / "market_data_enrichment_failures.csv"
SUCCESS_SAMPLE_PATH = SCOUTING_OUTPUTS_DIR / "market_data_enrichment_success_sample.csv"


REQUIRED_OUTPUT_COLUMNS = [
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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _today_key() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    try:
        number = float(value)
    except Exception:
        return None

    if math.isnan(number) or math.isinf(number):
        return None

    return number


def _safe_int(value: Any) -> int | None:
    number = _safe_float(value)

    if number is None:
        return None

    return int(number)


def _format_money(value: float | int | None) -> str:
    if value is None:
        return ""

    try:
        return str(float(value))
    except Exception:
        return ""


def _format_volume(value: float | int | None) -> str:
    if value is None:
        return ""

    try:
        return str(int(value))
    except Exception:
        return ""


def _load_cache() -> dict[str, Any]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if not CACHE_PATH.exists():
        return {}

    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def _get_cache_entry(cache: dict[str, Any], symbol: str, max_age_days: int) -> dict[str, Any] | None:
    entry = cache.get(symbol)

    if not entry:
        return None

    cached_date = entry.get("cached_date")

    if not cached_date:
        return None

    # Simple daily cache logic. If max_age_days <= 0, only accept today's cache.
    try:
        cached_day = datetime.fromisoformat(cached_date).date()
        today = datetime.now(timezone.utc).date()
        age_days = (today - cached_day).days
    except Exception:
        return None

    if age_days <= max_age_days:
        return entry

    return None


def _normalize_symbol_for_yfinance(symbol: str) -> str:
    """
    Try to convert common USA symbols to yfinance format.

    Examples:
    - BRK.B -> BRK-B
    - BRK/B -> BRK-B
    """

    text = str(symbol).strip().upper()
    text = text.replace("/", "-")
    text = text.replace(".", "-")
    return text


def _extract_fast_info_value(fast_info: Any, key: str) -> Any:
    try:
        if hasattr(fast_info, "get"):
            return fast_info.get(key)
    except Exception:
        pass

    try:
        return getattr(fast_info, key)
    except Exception:
        return None


def _fetch_yfinance_symbol(symbol: str) -> dict[str, Any]:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError(
            "Missing dependency: yfinance. Install it with "
            "./.venv/Scripts/python.exe -m pip install yfinance"
        ) from exc

    yf_symbol = _normalize_symbol_for_yfinance(symbol)
    ticker = yf.Ticker(yf_symbol)

    fast_info = {}
    info = {}

    try:
        fast_info = ticker.fast_info
    except Exception:
        fast_info = {}

    try:
        info = ticker.info or {}
    except Exception:
        info = {}

    price = (
        _safe_float(_extract_fast_info_value(fast_info, "last_price"))
        or _safe_float(info.get("currentPrice"))
        or _safe_float(info.get("regularMarketPrice"))
        or _safe_float(info.get("previousClose"))
    )

    market_cap = (
        _safe_float(_extract_fast_info_value(fast_info, "market_cap"))
        or _safe_float(info.get("marketCap"))
    )

    volume = (
        _safe_int(_extract_fast_info_value(fast_info, "last_volume"))
        or _safe_int(info.get("volume"))
        or _safe_int(info.get("regularMarketVolume"))
        or _safe_int(info.get("averageVolume"))
        or _safe_int(info.get("averageVolume10days"))
    )

    avg_volume_30d = (
        _safe_int(_extract_fast_info_value(fast_info, "thirty_day_average_volume"))
        or _safe_int(info.get("averageVolume"))
        or volume
    )

    avg_volume_90d = (
        _safe_int(_extract_fast_info_value(fast_info, "three_month_average_volume"))
        or _safe_int(info.get("averageVolume"))
        or avg_volume_30d
        or volume
    )

    sector = info.get("sector") or ""
    industry = info.get("industry") or ""

    quote_type = info.get("quoteType") or info.get("typeDisp") or ""

    has_core_market_data = price is not None and market_cap is not None and avg_volume_90d is not None

    return {
        "symbol": symbol,
        "yf_symbol": yf_symbol,
        "price": price,
        "market_cap": market_cap,
        "volume": volume,
        "avg_volume_30d": avg_volume_30d,
        "avg_volume_90d": avg_volume_90d,
        "sector": sector,
        "industry": industry,
        "quote_type": quote_type,
        "has_core_market_data": has_core_market_data,
        "cached_date": _today_key(),
        "fetched_at": _utc_now_iso(),
        "error": None,
    }


def enrich_market_data_yfinance(
    input_path: Path = DEFAULT_INPUT,
    output_path: Path = DEFAULT_OUTPUT,
    limit: int = 100,
    sleep_seconds: float = 0.25,
    cache_max_age_days: int = 2,
    include_cached: bool = True,
) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {input_path}. "
            "Run first: python -m src.download_free_us_universe"
        )

    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(input_path)

    if raw.empty:
        raise ValueError(f"Input CSV is empty: {input_path}")

    for column in REQUIRED_OUTPUT_COLUMNS:
        if column not in raw.columns:
            raw[column] = ""

    work = raw.copy()

    if limit and limit > 0:
        work = work.head(limit).copy()

    cache = _load_cache()
    failures: list[dict[str, Any]] = []
    enriched_rows = []

    fetched_count = 0
    cached_count = 0
    success_count = 0

    for _, row in work.iterrows():
        symbol = str(row.get("Symbol", "")).strip().upper()

        if not symbol:
            continue

        data = None

        if include_cached:
            data = _get_cache_entry(cache, symbol, cache_max_age_days)

            if data:
                cached_count += 1

        if data is None:
            try:
                data = _fetch_yfinance_symbol(symbol)
                fetched_count += 1
                cache[symbol] = data

                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)

            except Exception as exc:
                data = {
                    "symbol": symbol,
                    "yf_symbol": _normalize_symbol_for_yfinance(symbol),
                    "price": None,
                    "market_cap": None,
                    "volume": None,
                    "avg_volume_30d": None,
                    "avg_volume_90d": None,
                    "sector": "",
                    "industry": "",
                    "quote_type": "",
                    "has_core_market_data": False,
                    "cached_date": _today_key(),
                    "fetched_at": _utc_now_iso(),
                    "error": str(exc),
                }
                cache[symbol] = data

        output_row = row.to_dict()

        if data.get("price") is not None:
            output_row["Last Sale"] = _format_money(data.get("price"))

        if data.get("market_cap") is not None:
            output_row["Market Cap"] = _format_money(data.get("market_cap"))

        # Prefer 90d/average volume for Stage 1 compatibility.
        selected_volume = data.get("avg_volume_90d") or data.get("avg_volume_30d") or data.get("volume")

        if selected_volume is not None:
            output_row["Volume"] = _format_volume(selected_volume)

        if data.get("sector"):
            output_row["Sector"] = data.get("sector")

        if data.get("industry"):
            output_row["Industry"] = data.get("industry")

        output_row["Source"] = f"{output_row.get('Source', '')}|yfinance".strip("|")

        output_row["yf_symbol"] = data.get("yf_symbol")
        output_row["quote_type"] = data.get("quote_type")
        output_row["has_core_market_data"] = bool(data.get("has_core_market_data"))
        output_row["market_data_error"] = data.get("error")
        output_row["avg_volume_30d"] = data.get("avg_volume_30d")
        output_row["avg_volume_90d"] = data.get("avg_volume_90d")

        if data.get("has_core_market_data"):
            success_count += 1
        else:
            failures.append(
                {
                    "Symbol": symbol,
                    "Name": row.get("Name", ""),
                    "yf_symbol": data.get("yf_symbol"),
                    "error": data.get("error"),
                    "price": data.get("price"),
                    "market_cap": data.get("market_cap"),
                    "avg_volume_90d": data.get("avg_volume_90d"),
                    "quote_type": data.get("quote_type"),
                }
            )

        enriched_rows.append(output_row)

    _save_cache(cache)

    enriched_df = pd.DataFrame(enriched_rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    enriched_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    failures_df = pd.DataFrame(failures)
    failures_df.to_csv(FAILURES_PATH, index=False, encoding="utf-8-sig")

    success_sample = enriched_df[enriched_df.get("has_core_market_data", False) == True].head(50)
    success_sample.to_csv(SUCCESS_SAMPLE_PATH, index=False, encoding="utf-8-sig")

    summary = {
        "phase": "7A.2",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "input_path": str(input_path),
        "output_path": str(output_path),
        "input_rows": int(len(raw)),
        "processed_rows": int(len(work)),
        "success_with_core_market_data": int(success_count),
        "failed_or_incomplete_rows": int(len(failures)),
        "fetched_count": int(fetched_count),
        "cached_count": int(cached_count),
        "sleep_seconds": sleep_seconds,
        "cache_path": str(CACHE_PATH),
        "failures_path": str(FAILURES_PATH),
        "success_sample_path": str(SUCCESS_SAMPLE_PATH),
        "openai_called": False,
        "paid_api_called": False,
        "app_modified": False,
        "release_v0_6_modified": False,
        "notes": [
            "Uses yfinance for free local testing.",
            "yfinance is not an official guaranteed market-data API.",
            "Use small limits first and rely on cache.",
        ],
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7A.2 free market data enrichment")
    print("=" * 76)
    print(f"Status: {summary.get('status')}")
    print(f"Input rows: {summary.get('input_rows')}")
    print(f"Processed rows: {summary.get('processed_rows')}")
    print(f"Success with core market data: {summary.get('success_with_core_market_data')}")
    print(f"Failed/incomplete rows: {summary.get('failed_or_incomplete_rows')}")
    print(f"Fetched count: {summary.get('fetched_count')}")
    print(f"Cached count: {summary.get('cached_count')}")
    print(f"Output: {summary.get('output_path')}")
    print(f"Failures: {summary.get('failures_path')}")
    print(f"OpenAI called: {summary.get('openai_called')}")
    print(f"Paid API called: {summary.get('paid_api_called')}")
    print()
    print("Next command")
    print("-" * 76)
    print(
        ".\\.venv\\Scripts\\python.exe -m src.run_real_universe_pilot "
        "--input data/raw/universe_source_real_market_enriched.csv --limit 100 --source yfinance_market_data"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=0.25)
    parser.add_argument("--cache-max-age-days", type=int, default=2)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    summary = enrich_market_data_yfinance(
        input_path=Path(args.input),
        output_path=Path(args.output),
        limit=args.limit,
        sleep_seconds=args.sleep,
        cache_max_age_days=args.cache_max_age_days,
        include_cached=not args.no_cache,
    )

    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
