#!/usr/bin/env python3
"""Fail-closed downloader for TWSE's own official STOCK_DAY endpoint
(www.twse.com.tw), used to check whether it gives deeper history than the
EODHD-sourced TWSE data collected in v2.33D1. Public, official, no account
and no API key. Confirmed working range: 2010-01-04 to today (TWSE itself
rejects earlier dates with an explicit error message). One HTTP call per
stock per calendar month; self-throttled to be polite to a public
government site with no documented rate limit. Resumable: skips any
pilot_id whose output file already exists. No scoring, no ranking.
"""
from __future__ import annotations

import argparse
import csv
import json
import ssl
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import certifi

BASE_URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
MIN_SECONDS_BETWEEN_CALLS = 0.8
EARLIEST_CONFIRMED_DATE = date(2010, 1, 4)
FIELD_NAMES = ["Date", "TradeVolumeShares", "TradeValue", "Open", "High", "Low", "Close", "Change", "Transactions", "Note"]


def month_starts(start: date, end: date):
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        yield date(year, month, 1)
        month += 1
        if month > 12:
            month = 1
            year += 1


def roc_to_iso(roc_date: str) -> str:
    year, month, day = (int(p) for p in roc_date.strip().split("/"))
    return f"{year + 1911:04d}-{month:02d}-{day:02d}"


def parse_number(value: str) -> float | None:
    value = value.strip().replace(",", "")
    if not value or value == "--":
        return None
    return float(value)


def fetch_month(stock_no: str, month_start: date) -> dict:
    query = f"response=json&date={month_start:%Y%m01}&stockNo={stock_no}"
    request = urllib.request.Request(f"{BASE_URL}?{query}", headers={"User-Agent": "ScoutFinance/2.33I local-personal-pilot"})
    with urllib.request.urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--execute", action="store_true", help="perform the real, multi-call historical collection")
    parser.add_argument("--from-date", default=EARLIEST_CONFIRMED_DATE.isoformat())
    args = parser.parse_args()

    if not args.execute:
        print("BLOCKED: pass --execute only after explicit pilot authorization")
        return 2

    with args.sample.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["exchange"] == "TWSE"]
    if not rows:
        print("BLOCKED: no TWSE rows found in sample")
        return 2

    start = date.fromisoformat(args.from_date)
    today = date.today()
    months = list(month_starts(start, today))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    collected = 0
    skipped = 0
    failures: list[dict[str, object]] = []
    first_call = True

    for row in rows:
        output = args.output_dir / f"{row['pilot_id']}.json"
        if output.exists():
            skipped += 1
            continue

        stock_no = row["ticker"].split(".")[0]
        prices: list[dict] = []
        month_failures = 0
        for month_start in months:
            if not first_call:
                time.sleep(MIN_SECONDS_BETWEEN_CALLS)
            first_call = False
            try:
                payload = fetch_month(stock_no, month_start)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                month_failures += 1
                failures.append({"pilot_id": row["pilot_id"], "month": month_start.isoformat(), "error_type": type(exc).__name__})
                continue

            if payload.get("stat") != "OK":
                continue  # e.g. a month entirely before listing date, or a genuinely empty month
            for record in payload.get("data", []):
                prices.append({
                    "Date": roc_to_iso(record[0]),
                    "Open": parse_number(record[3]),
                    "High": parse_number(record[4]),
                    "Low": parse_number(record[5]),
                    "Close": parse_number(record[6]),
                    "Volume_shares": parse_number(record[1]),
                    "TradeValue": parse_number(record[2]),
                    "Change": record[7].strip(),
                    "Transactions": parse_number(record[8]),
                    "Note": record[9].strip(),
                })

        if not prices:
            failures.append({"pilot_id": row["pilot_id"], "month": None, "error_type": "NoDataCollected"})
            continue

        temporary = output.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps({"pilot": row, "prices": prices, "month_call_failures": month_failures}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output)
        collected += 1

    report = {
        "status": "COMPLETED" if not failures else "COMPLETED_WITH_ERRORS",
        "input_assets": len(rows),
        "collected": collected,
        "skipped_existing": skipped,
        "failed": len(failures),
        "failures": failures,
        "from_date": start.isoformat(),
        "to_date": today.isoformat(),
        "months_per_asset_requested": len(months),
    }
    (args.output_dir / "download_report_v2_33i.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
