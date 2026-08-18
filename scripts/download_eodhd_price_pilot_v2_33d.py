#!/usr/bin/env python3
"""Fail-closed EODHD EOD downloader for an explicitly authorized v2.33D pilot."""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_ENV = "SCOUT_FINANCE_EODHD_API_TOKEN"
REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Adjusted_close", "Volume"}


def parse_prices(payload: str) -> list[dict[str, str]]:
    rows = list(csv.DictReader(io.StringIO(payload)))
    if not rows or not REQUIRED_COLUMNS.issubset(rows[0]):
        raise ValueError("Provider response does not match the expected EOD CSV schema")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--execute", action="store_true", help="perform authorized network collection")
    parser.add_argument("--from-date", default="2021-01-01")
    args = parser.parse_args()
    token = os.environ.get(TOKEN_ENV, "").strip()
    if not args.execute:
        print("BLOCKED: pass --execute only after explicit pilot authorization")
        return 2
    if not token:
        print(f"BLOCKED: environment variable {TOKEN_ENV} is not configured")
        return 2

    sample = list(csv.DictReader(args.sample.open(encoding="utf-8", newline="")))
    unresolved = [row["pilot_id"] for row in sample if row.get("provider_symbol_status") != "resolved" or not row.get("provider_symbol")]
    if unresolved:
        print(json.dumps({"status": "BLOCKED", "reason": "provider_symbols_unresolved", "rows": len(unresolved)}))
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    collected = 0
    for row in sample:
        symbol = urllib.parse.quote(row["provider_symbol"], safe=".-")
        query = urllib.parse.urlencode({"api_token": token, "fmt": "csv", "from": args.from_date, "period": "d"})
        request = urllib.request.Request(
            f"https://eodhd.com/api/eod/{symbol}?{query}",
            headers={"User-Agent": "ScoutFinance/2.33D local-personal-pilot"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
        rows = parse_prices(payload)
        output = args.output_dir / f"{row['pilot_id']}.json"
        output.write_text(json.dumps({"pilot": row, "prices": rows}, ensure_ascii=False) + "\n", encoding="utf-8")
        collected += 1
        time.sleep(0.12)
    print(json.dumps({"status": "COLLECTED", "assets": collected}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
