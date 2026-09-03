#!/usr/bin/env python3
"""Run controlled v2.38O Europe price-history acquisition batches."""
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
CONTRACT = ROOT / "config/europe_price_history_acquisition_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38o_europe_price_history_acquisition"
PLAN = OUT / "europe_price_history_acquisition_plan_v2_38o.csv"
LEDGER = OUT / "europe_price_history_batch_ledger_v2_38o.csv"
LEDGER_FIELDS = [
    "batch_id",
    "run_utc",
    "provider",
    "requested",
    "selected",
    "collected",
    "skipped_existing",
    "failed",
    "status",
    "phase9c_authorized",
    "scoring_calculated",
    "ranking_calculated",
    "recommendations_generated",
]
PRICE_FIELDS = ["date", "open", "high", "low", "close", "adjusted_close", "volume", "provider", "provider_symbol", "home_exchange", "home_mic", "home_currency"]


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
    print(json.dumps({
        "status": "BLOCKED",
        "reason": reason,
        "scoring_calculated": False,
        "ranking_calculated": False,
        "recommendations_generated": False,
        "phase9c_authorized": False,
    }, sort_keys=True))
    return 2


def parse_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def normalize_twelvedata(payload: dict[str, Any], row: dict[str, str], provider: str) -> list[dict[str, Any]]:
    values = payload.get("values", [])
    if not isinstance(values, list):
        raise ValueError("missing_values")
    rows = []
    for item in values:
        if not isinstance(item, dict):
            continue
        dt = str(item.get("datetime", item.get("date", "")))[:10]
        close = parse_float(item.get("close"))
        if not dt or close is None or close <= 0:
            continue
        rows.append({
            "date": dt,
            "open": parse_float(item.get("open")) or close,
            "high": parse_float(item.get("high")) or close,
            "low": parse_float(item.get("low")) or close,
            "close": close,
            "adjusted_close": parse_float(item.get("adjusted_close")) or close,
            "volume": parse_float(item.get("volume")) or "",
            "provider": provider,
            "provider_symbol": row["provider_symbol"],
            "home_exchange": row["home_exchange"],
            "home_mic": row["home_mic"],
            "home_currency": row["home_currency"],
        })
    rows.sort(key=lambda r: r["date"])
    return rows


def fetch_mock(row: dict[str, str], mock_dir: Path, provider: str) -> list[dict[str, Any]]:
    path = mock_dir / f"{row['provider_symbol']}.json"
    if not path.exists():
        raise RuntimeError("mock_payload_missing")
    return normalize_twelvedata(json.loads(path.read_text(encoding="utf-8")), row, provider)


def fetch_twelvedata(row: dict[str, str], api_key: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({
        "symbol": row["provider_symbol"],
        "interval": "1day",
        "start_date": from_date,
        "end_date": to_date,
        "outputsize": 5000,
        "apikey": api_key,
    })
    request = urllib.request.Request(
        f"https://api.twelvedata.com/time_series?{params}",
        headers={"User-Agent": "ScoutFinance/2.38O"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("status") == "error":
        raise RuntimeError(str(payload.get("message", "provider_error")))
    return normalize_twelvedata(payload, row, "twelvedata")


def fetch_stooq(row: dict[str, str]) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"s": row["provider_symbol"], "i": "d"})
    request = urllib.request.Request(
        f"https://stooq.com/q/d/l/?{params}",
        headers={"User-Agent": "ScoutFinance/2.38O"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8", errors="replace")
    parsed = []
    for item in csv.DictReader(text.splitlines()):
        close = parse_float(item.get("Close"))
        if not item.get("Date") or close is None or close <= 0:
            continue
        parsed.append({
            "date": item["Date"],
            "open": parse_float(item.get("Open")) or close,
            "high": parse_float(item.get("High")) or close,
            "low": parse_float(item.get("Low")) or close,
            "close": close,
            "adjusted_close": close,
            "volume": parse_float(item.get("Volume")) or "",
            "provider": "stooq",
            "provider_symbol": row["provider_symbol"],
            "home_exchange": row["home_exchange"],
            "home_mic": row["home_mic"],
            "home_currency": row["home_currency"],
        })
    parsed.sort(key=lambda r: r["date"])
    return parsed


def fetch_eodhd(row: dict[str, str], api_key: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"api_token": api_key, "fmt": "json", "from": from_date, "to": to_date})
    request = urllib.request.Request(
        f"https://eodhistoricaldata.com/api/eod/{urllib.parse.quote(row['provider_symbol'])}?{params}",
        headers={"User-Agent": "ScoutFinance/2.38O"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError("provider_error")
    return normalize_twelvedata({"values": payload}, row, "eodhd")


def select_rows(plan_path: Path, limit: int, provider: str, force: bool, raw_cache: Path) -> list[dict[str, str]]:
    selected = []
    for row in read_csv(plan_path):
        if row.get("collection_status") not in {"READY_FOR_COLLECTION", "COLLECTED", "SKIPPED_EXISTING_CACHE"}:
            continue
        if row.get("provider") != provider:
            continue
        if row.get("home_exchange") == "CBOE_EUROPE" or row.get("home_mic", "").startswith("CBOE"):
            continue
        if not row.get("provider_symbol"):
            continue
        if (raw_cache / f"{row['asset_id']}.csv").exists() and not force:
            continue
        selected.append(row)
        if len(selected) >= limit:
            break
    return selected


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=int(contract["default_batch_limit"]))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--provider", default=os.environ.get("SCOUT_FINANCE_EU_PRICE_PROVIDER", "stooq").lower())
    parser.add_argument("--from-date", default=contract["default_from_date"])
    parser.add_argument("--to-date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--raw-cache", type=Path, default=ROOT / contract["raw_cache"])
    parser.add_argument("--plan-path", type=Path, default=PLAN)
    parser.add_argument("--mock-provider-dir", type=Path)
    args = parser.parse_args()
    supported = set(contract["supported_providers"])
    if args.provider not in supported:
        return blocked("provider_not_supported")
    if args.limit < 1 or args.limit > int(contract["max_batch_limit"]):
        return blocked("batch_limit_must_be_1_to_100")
    selected = select_rows(args.plan_path, args.limit, args.provider, args.force, args.raw_cache)
    if not args.execute:
        print(json.dumps({
            "status": "DRY_RUN",
            "provider": args.provider,
            "requested_limit": args.limit,
            "selected": len(selected),
            "asset_ids": [row["asset_id"] for row in selected],
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
            "phase9c_authorized": False,
        }, sort_keys=True))
        return 0
    token_env = contract["providers_requiring_credentials"].get(args.provider, "")
    token = os.environ.get(token_env, "") if token_env else ""
    if token_env and not token:
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
            if args.mock_provider_dir:
                prices = fetch_mock(row, args.mock_provider_dir, args.provider)
            elif args.provider == "twelvedata":
                prices = fetch_twelvedata(row, token, args.from_date, args.to_date)
            elif args.provider == "stooq":
                prices = fetch_stooq(row)
            elif args.provider == "eodhd":
                prices = fetch_eodhd(row, token, args.from_date, args.to_date)
            else:
                raise RuntimeError("provider_not_supported")
            if len(prices) < int(contract["expected_min_rows"]):
                raise RuntimeError("insufficient_price_history")
            write_csv(target, prices, PRICE_FIELDS)
            collected += 1
            time.sleep(0.15)
        except Exception as exc:  # noqa: BLE001 - record per-asset failure and continue.
            failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "reason": type(exc).__name__})
    status = "COMPLETED" if not failures else "COMPLETED_WITH_ERRORS"
    append_ledger({
        "batch_id": datetime.now(timezone.utc).strftime("v2_38o_%Y%m%dT%H%M%SZ"),
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
