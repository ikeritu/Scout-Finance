#!/usr/bin/env python3
"""Resolve the 42 blocked JPX pilot symbols against the official J-Quants
equities master endpoint. Fail-closed: a symbol only resolves on an exact
CompanyNameEnglish match; anything else stays blocked. Never prints, logs,
or stores the API key. No price data is downloaded here.
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
MASTER_URL = "https://api.jquants.com/v2/equities/master"
MIN_SECONDS_BETWEEN_CALLS = 15.0  # free plan: 5 requests/minute (observed stricter in practice)
RATE_LIMIT_BACKOFF_SECONDS = 65.0
MAX_ATTEMPTS = 3


def normalize(name: str) -> str:
    return " ".join(name.strip().upper().split())


def fetch_master(key: str, code: str) -> dict:
    query = urllib.parse.urlencode({"code": code})
    request = urllib.request.Request(f"{MASTER_URL}?{query}", headers={"x-api-key": key})
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return {"rows": payload.get("data", [])}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                print(f"    rate-limited (429), waiting {RATE_LIMIT_BACKOFF_SECONDS:.0f}s before retry {attempt + 1}/{MAX_ATTEMPTS}", flush=True)
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            return {"error_type": "HTTPError", "http_status": exc.code, "body": body}
        except (urllib.error.URLError, TimeoutError) as exc:
            return {"error_type": type(exc).__name__, "http_status": None}
    return {"error_type": "HTTPError", "http_status": 429, "body": "rate limit retries exhausted"}


def resolve_row(key: str, row: dict) -> dict:
    ticker = row["ticker"].strip()
    expected_name = normalize(row["company_name"])
    result = fetch_master(key, ticker)

    if "error_type" in result:
        return {
            "pilot_id": row["pilot_id"],
            "ticker": ticker,
            "status": "unresolved",
            "reason": f"jquants_master_call_failed_{result['error_type']}",
            "provider_symbol": "",
            "http_status": result.get("http_status"),
            "error_body": (result.get("body") or "")[:200],
        }

    rows = result["rows"]
    if not rows:
        return {
            "pilot_id": row["pilot_id"],
            "ticker": ticker,
            "status": "unresolved",
            "reason": "code_not_found_in_jquants_master",
            "provider_symbol": "",
        }

    latest = max(rows, key=lambda r: r.get("Date", ""))
    actual_name = normalize(latest.get("CoNameEn", ""))
    if actual_name != expected_name:
        return {
            "pilot_id": row["pilot_id"],
            "ticker": ticker,
            "status": "unresolved",
            "reason": "name_mismatch_requires_manual_review",
            "provider_symbol": "",
            "jquants_company_name_english": latest.get("CoNameEn", ""),
        }

    return {
        "pilot_id": row["pilot_id"],
        "ticker": ticker,
        "status": "resolved_jquants_master_exact_match",
        "reason": "exact_company_name_english_match",
        "provider_symbol": latest.get("Code", ""),
        "jquants_market_name": latest.get("MktNm", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--only", default="", help="comma-separated pilot_id list to resolve (for retries)")
    args = parser.parse_args()

    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        print(f"BLOCKED: environment variable {API_KEY_ENV} is not configured")
        return 2

    with args.sample.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["exchange"] == "JPX"]
    if args.only:
        wanted = set(args.only.split(","))
        rows = [r for r in rows if r["pilot_id"] in wanted]
    if not rows:
        print("BLOCKED: no JPX rows found in sample")
        return 2

    results = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        results.append(resolve_row(key, row))
        print(f"[{i + 1}/{len(rows)}] {results[-1]['pilot_id']} -> {results[-1]['status']}", flush=True)

    resolved = [r for r in results if r["status"].startswith("resolved")]
    unresolved = [r for r in results if not r["status"].startswith("resolved")]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = ["pilot_id", "ticker", "status", "reason", "provider_symbol", "jquants_market_name", "jquants_company_name_english", "http_status", "error_body"]
    csv_path = args.output_dir / "jquants_symbol_resolution_v2_33g.csv"
    temporary_csv = csv_path.with_suffix(".csv.tmp")
    with temporary_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fields})
    temporary_csv.replace(csv_path)

    report = {
        "phase": "v2.33G-jquants-symbol-resolution",
        "input_rows": len(rows),
        "resolved": len(resolved),
        "unresolved": len(unresolved),
        "unresolved_reasons": {
            reason: sum(1 for r in unresolved if r["reason"] == reason)
            for reason in sorted({r["reason"] for r in unresolved})
        },
        "network_calls": len(rows),
        "credentials_used": True,
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }
    (args.output_dir / "jquants_symbol_resolution_report_v2_33g.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("PASS: v2.33G-jquants-symbols/exact-name-match-only/no-guessing/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
