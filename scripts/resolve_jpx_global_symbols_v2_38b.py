#!/usr/bin/env python3
"""Fail-closed, resumable JPX symbol resolution for the global v2.38B universe."""
from __future__ import annotations

import argparse
import csv
import json
import lzma
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs/full_universe_source_acquisition/v2_38b_global_enrichment"
SOURCE = ROOT / "outputs/full_universe_source_acquisition/v2_38a_global_universe_audit/global_universe_audited_v2_38a.csv.xz"
KNOWN = ROOT / "outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/jquants_symbol_resolution_v2_33g.csv"
OVERLAY = BASE / "jpx_symbol_resolution_overlay_25_v2_38b.csv"
RUNTIME = BASE / "jpx_global_resolution_runtime_v2_38b"
TOKEN_ENV = "SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN"
MASTER_URL = "https://api.jquants.com/v2/equities/master"
FIELDS = ["asset_id", "ticker", "exchange", "provider_symbol", "resolution_status", "evidence_source"]
MIN_SECONDS_BETWEEN_CALLS = 15.0


def normalize(value: str) -> str:
    return " ".join(value.strip().upper().split())


def read_csv(path: Path) -> list[dict[str, str]]:
    context = lzma.open(path, "rt", encoding="utf-8", newline="") if path.suffix == ".xz" else path.open("r", encoding="utf-8", newline="")
    with context as handle:
        return list(csv.DictReader(handle))


def write_overlay(path: Path, rows: list[dict[str, str]]) -> None:
    rows = sorted(rows, key=lambda row: row["asset_id"])
    if len(rows) != len({row["asset_id"] for row in rows}) or len(rows) != len({row["ticker"] for row in rows}):
        raise ValueError("overlay contains duplicate asset_id or ticker")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    temporary.replace(path)


def fetch_master(token: str, ticker: str) -> list[dict]:
    request = urllib.request.Request(
        f"{MASTER_URL}?{urllib.parse.urlencode({'code': ticker})}",
        headers={"x-api-key": token},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8")).get("data", [])


def exact_resolution(row: dict[str, str], provider_rows: list[dict]) -> tuple[dict[str, str] | None, str]:
    if not provider_rows:
        return None, "code_not_found"
    latest = max(provider_rows, key=lambda item: item.get("Date", ""))
    if normalize(latest.get("CoNameEn", "")) != normalize(row["company_name"]):
        return None, "company_name_mismatch"
    symbol = latest.get("Code", "").strip()
    if not symbol:
        return None, "provider_symbol_empty"
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "exchange": "JPX",
        "provider_symbol": symbol, "resolution_status": "EXACT_COMPANY_NAME_MATCH",
        "evidence_source": "J-Quants equities master",
    }, "resolved"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--known", type=Path, default=KNOWN)
    parser.add_argument("--overlay", type=Path, default=OVERLAY)
    parser.add_argument("--runtime", type=Path, default=RUNTIME)
    parser.add_argument("--min-seconds", type=float, default=MIN_SECONDS_BETWEEN_CALLS)
    args = parser.parse_args()
    if not 1 <= args.limit <= 500:
        print(json.dumps({"status": "BLOCKED", "reason": "batch_limit_must_be_1_to_500"}))
        return 2
    source = [row for row in read_csv(args.source) if row["exchange"] == "JPX" and row["eligibility_status"] == "ELIGIBLE" and row["identity_status"] == "COMPLETE"]
    known_rows = read_csv(args.known)
    known_tickers = {row["ticker"] for row in known_rows if row.get("status", "").startswith("resolved") and row.get("provider_symbol")}
    overlay = read_csv(args.overlay) if args.overlay.exists() else []
    if any(row.get("resolution_status") != "EXACT_COMPANY_NAME_MATCH" for row in overlay):
        print(json.dumps({"status": "BLOCKED", "reason": "overlay_contains_non_exact_resolution"}))
        return 2
    completed_ids = {row["asset_id"] for row in overlay}
    completed_tickers = known_tickers | {row["ticker"] for row in overlay}
    pending = [row for row in source if row["asset_id"] not in completed_ids and row["ticker"] not in completed_tickers]
    selected = pending[:args.limit]
    plan = {"requested_limit": args.limit, "eligible_jpx": len(source), "already_resolved": len(known_tickers) + len(overlay), "remaining": len(pending), "selected": len(selected), "asset_ids": [row["asset_id"] for row in selected]}
    if not args.execute:
        print(json.dumps({"status": "DRY_RUN", **plan}, ensure_ascii=False))
        return 0
    token = os.environ.get(TOKEN_ENV, "").strip()
    if not token:
        print(json.dumps({"status": "BLOCKED", "reason": "credential_missing", "environment_variable": TOKEN_ENV, **plan}, ensure_ascii=False))
        return 2
    if not selected:
        print(json.dumps({"status": "COMPLETED", "resolved": 0, "failed": 0, **plan}, ensure_ascii=False))
        return 0
    args.runtime.mkdir(parents=True, exist_ok=True)
    failures: list[dict[str, object]] = []
    resolved = 0
    for index, row in enumerate(selected):
        if index:
            time.sleep(max(0.0, args.min_seconds))
        try:
            resolution, reason = exact_resolution(row, fetch_master(token, row["ticker"]))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            resolution, reason = None, type(exc).__name__
        if resolution:
            overlay.append(resolution)
            write_overlay(args.overlay, overlay)
            resolved += 1
        else:
            failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "reason": reason})
        print(f"[{index + 1}/{len(selected)}] {row['asset_id']} -> {reason}", flush=True)
    report = {"status": "COMPLETED" if not failures else "COMPLETED_WITH_ERRORS", **plan, "resolved": resolved, "failed": len(failures), "failures": failures, "network_calls": len(selected), "phase9c_authorized": False}
    report_path = args.runtime / "latest_resolution_report_v2_38b.json"
    temporary = report_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(report_path)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
