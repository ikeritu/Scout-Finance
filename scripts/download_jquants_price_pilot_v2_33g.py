#!/usr/bin/env python3
"""Fail-closed J-Quants EOD downloader for the explicitly authorized v2.33G
JPX pilot. Resumable, atomic per-symbol writes, no credential/URL leakage in
errors or reports. Confirmed free-plan window: 2024-06-08 to 2026-06-08.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_KEY_ENV = "SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN"
BARS_URL = "https://api.jquants.com/v2/equities/bars/daily"
MIN_SECONDS_BETWEEN_CALLS = 15.0  # free plan: 5 requests/minute (observed stricter in practice)
RATE_LIMIT_BACKOFF_SECONDS = 65.0
MAX_ATTEMPTS = 3
REQUIRED_FIELDS = {"Date", "Code", "O", "H", "L", "C", "Vo"}


def fetch_bars(key: str, code: str, from_date: str, to_date: str) -> list[dict]:
    query = urllib.parse.urlencode({"code": code, "from": from_date, "to": to_date})
    request = urllib.request.Request(f"{BARS_URL}?{query}", headers={"x-api-key": key})
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                print(f"    rate-limited (429), waiting {RATE_LIMIT_BACKOFF_SECONDS:.0f}s before retry {attempt + 1}/{MAX_ATTEMPTS}", flush=True)
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            raise
    else:
        raise urllib.error.HTTPError(BARS_URL, 429, "rate limit retries exhausted", hdrs=None, fp=None)

    rows = payload.get("data", [])
    if rows and not REQUIRED_FIELDS.issubset(rows[0]):
        raise ValueError("Provider response does not match the expected bars schema")
    if "pagination_key" in payload and payload["pagination_key"]:
        raise ValueError("Unexpected pagination_key: response spans more than one page")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("resolved_symbols_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--execute", action="store_true", help="perform authorized network collection")
    parser.add_argument("--from-date", default="2024-06-08")
    parser.add_argument("--to-date", default="2026-06-08")
    args = parser.parse_args()

    key = os.environ.get(API_KEY_ENV, "").strip()
    if not args.execute:
        print("BLOCKED: pass --execute only after explicit pilot authorization")
        return 2
    if not key:
        print(f"BLOCKED: environment variable {API_KEY_ENV} is not configured")
        return 2

    with args.resolved_symbols_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    resolved = [r for r in rows if r.get("status", "").startswith("resolved") and r.get("provider_symbol")]
    if not resolved:
        print(json.dumps({"status": "BLOCKED", "reason": "no_resolved_symbols"}))
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    collected = 0
    skipped = 0
    failures: list[dict[str, object]] = []

    for i, row in enumerate(resolved):
        output = args.output_dir / f"{row['pilot_id']}.json"
        if output.exists():
            skipped += 1
            continue

        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)

        try:
            bars = fetch_bars(key, row["provider_symbol"], args.from_date, args.to_date)
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            UnicodeDecodeError,
        ) as exc:
            failures.append({
                "pilot_id": row["pilot_id"],
                "provider_symbol": row["provider_symbol"],
                "error_type": type(exc).__name__,
                "http_status": getattr(exc, "code", None),
            })
            continue

        temporary = output.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps({"pilot": row, "prices": bars}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output)
        collected += 1

    report = {
        "status": "COMPLETED" if not failures else "COMPLETED_WITH_ERRORS",
        "input_assets": len(resolved),
        "collected": collected,
        "skipped_existing": skipped,
        "failed": len(failures),
        "failures": failures,
        "from_date": args.from_date,
        "to_date": args.to_date,
    }
    (args.output_dir / "download_report_v2_33g.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
