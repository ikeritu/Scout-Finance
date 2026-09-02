#!/usr/bin/env python3
"""Run controlled v2.38I US price history acquisition batches."""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_price_history_acquisition_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38i_us_price_history_acquisition"
PLAN = OUT / "us_price_history_acquisition_plan_v2_38i.csv"
LEDGER = OUT / "us_price_history_batch_ledger_v2_38i.csv"
LEDGER_FIELDS = [
    "batch_id", "run_utc", "provider", "requested", "selected", "collected",
    "skipped_existing", "failed", "status", "phase9c_authorized",
    "scoring_calculated", "ranking_calculated", "recommendations_generated",
]
PRICE_FIELDS = ["date", "close", "adjusted_close", "volume", "provider", "provider_symbol"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def append_ledger(row: dict[str, Any]) -> None:
    existing = read_csv(LEDGER)
    existing.append({field: str(row.get(field, "")) for field in LEDGER_FIELDS})
    write_csv(LEDGER, existing, LEDGER_FIELDS)


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "phase9c_authorized": False}, sort_keys=True))
    return 2


def validate_limit(limit: int) -> bool:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    return 1 <= limit <= int(contract["batch_limit_max"])


def select_rows(plan_path: Path, limit: int, force: bool, raw_cache: Path) -> list[dict[str, str]]:
    rows = read_csv(plan_path)
    selected = []
    for row in rows:
        if row.get("acquisition_status") not in {"PENDING_COLLECTION", "LOCAL_PRICE_READY"}:
            continue
        local = raw_cache / f"{row['asset_id']}.csv"
        if local.exists() and not force:
            continue
        if not row.get("provider_symbol"):
            continue
        selected.append(row)
        if len(selected) >= limit:
            break
    return selected


def parse_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def normalize_twelvedata(payload: dict[str, Any], provider_symbol: str) -> list[dict[str, Any]]:
    values = payload.get("values", [])
    if not isinstance(values, list):
        raise ValueError("missing_values")
    rows = []
    for item in values:
        if not isinstance(item, dict):
            continue
        dt = str(item.get("datetime", ""))[:10]
        close = parse_float(item.get("close"))
        if not dt or close is None or close <= 0:
            continue
        adjusted = parse_float(item.get("adjusted_close"))
        volume = parse_float(item.get("volume"))
        rows.append({
            "date": dt,
            "close": close,
            "adjusted_close": adjusted,
            "volume": volume,
            "provider": "twelvedata",
            "provider_symbol": provider_symbol,
        })
    rows.sort(key=lambda r: r["date"])
    return rows


def fetch_twelvedata(symbol: str, api_key: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": "1day",
        "start_date": from_date,
        "end_date": to_date,
        "outputsize": 5000,
        "apikey": api_key,
    })
    url = f"https://api.twelvedata.com/time_series?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "ScoutFinance/2.38I"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("status") == "error":
        raise RuntimeError(str(payload.get("message", "provider_error")))
    return normalize_twelvedata(payload, symbol)


def fetch_mock(symbol: str, mock_dir: Path) -> list[dict[str, Any]]:
    path = mock_dir / f"{symbol}.json"
    if not path.exists():
        raise RuntimeError("mock_payload_missing")
    return normalize_twelvedata(json.loads(path.read_text(encoding="utf-8")), symbol)


def write_price_history(path: Path, rows: list[dict[str, Any]]) -> None:
    serializable = []
    for row in rows:
        serializable.append({field: "" if row.get(field) is None else row.get(field) for field in PRICE_FIELDS})
    write_csv(path, serializable, PRICE_FIELDS)


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--provider", default=os.environ.get("SCOUT_FINANCE_US_PRICE_PROVIDER", "twelvedata").lower())
    parser.add_argument("--from-date", default=contract["default_from_date"])
    parser.add_argument("--to-date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--raw-cache", type=Path, default=ROOT / contract["raw_cache"])
    parser.add_argument("--plan-path", type=Path, default=PLAN)
    parser.add_argument("--mock-provider-dir", type=Path)
    args = parser.parse_args()
    if not validate_limit(args.limit):
        return blocked("batch_limit_must_be_1_to_250")
    if args.provider not in contract["allowed_providers"]:
        return blocked("provider_not_supported")
    selected = select_rows(args.plan_path, args.limit, args.force, args.raw_cache)
    if not args.execute:
        print(json.dumps({
            "status": "DRY_RUN",
            "provider": args.provider,
            "requested_limit": args.limit,
            "selected": len(selected),
            "asset_ids": [row["asset_id"] for row in selected],
            "recommendations_generated": False,
            "phase9c_authorized": False,
        }, sort_keys=True))
        return 0
    token_env = contract["provider_env"][args.provider]
    token = os.environ.get(token_env, "")
    if not token:
        return blocked("credential_missing")
    args.raw_cache.mkdir(parents=True, exist_ok=True)
    collected = 0
    skipped = 0
    failures: list[dict[str, str]] = []
    for row in selected:
        target = args.raw_cache / f"{row['asset_id']}.csv"
        if target.exists() and not args.force:
            skipped += 1
            continue
        try:
            if args.provider == "twelvedata":
                prices = fetch_mock(row["provider_symbol"], args.mock_provider_dir) if args.mock_provider_dir else fetch_twelvedata(row["provider_symbol"], token, args.from_date, args.to_date)
            else:
                raise RuntimeError("provider_not_supported")
            if not prices:
                raise RuntimeError("empty_price_history")
            write_price_history(target, prices)
            collected += 1
            time.sleep(0.15)
        except Exception as exc:  # noqa: BLE001 - per-asset failure must be recorded, not fatal.
            failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "reason": type(exc).__name__})
    status = "COMPLETED" if not failures else "COMPLETED_WITH_ERRORS"
    append_ledger({
        "batch_id": datetime.now(timezone.utc).strftime("v2_38i_%Y%m%dT%H%M%SZ"),
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "provider": args.provider,
        "requested": args.limit,
        "selected": len(selected),
        "collected": collected,
        "skipped_existing": skipped,
        "failed": len(failures),
        "status": status,
        "phase9c_authorized": "false",
        "scoring_calculated": "false",
        "ranking_calculated": "false",
        "recommendations_generated": "false",
    })
    print(json.dumps({
        "status": status,
        "provider": args.provider,
        "selected": len(selected),
        "collected": collected,
        "skipped_existing": skipped,
        "failed": len(failures),
        "failures": failures,
        "scoring_calculated": False,
        "ranking_calculated": False,
        "recommendations_generated": False,
        "phase9c_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
