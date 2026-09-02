#!/usr/bin/env python3
"""Fail-closed SEC pilot runner for v2.38D."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation"
SELECTION = OUT / "us_sec_pilot_selection_v2_38d.csv"
MAX_LIMIT = 50


def emit(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False))
    return code


def read_selection(limit: int, asset_id: str | None) -> list[dict[str, str]]:
    if not SELECTION.exists():
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "scripts/build_us_sec_foundation_v2_38d.py")], cwd=ROOT, check=True)
    with SELECTION.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if asset_id:
        rows = [r for r in rows if r["asset_id"] == asset_id]
    return rows[:limit]


def fetch_json(url: str, user_agent: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate", "Host": "data.sec.gov"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--asset-id")
    parser.add_argument("--cache-dir", type=Path, default=OUT / "sec_raw_cache_v2_38d")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.limit <= MAX_LIMIT:
        return emit({"status": "BLOCKED", "reason": "pilot_limit_must_be_1_to_50"}, 2)
    rows = read_selection(args.limit, args.asset_id)
    if not args.execute:
        return emit({"status": "DRY_RUN", "selected": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_calls": 0, "phase9c_authorized": False})
    user_agent = os.environ.get("SCOUT_FINANCE_SEC_USER_AGENT", "").strip()
    if not user_agent:
        return emit({"status": "BLOCKED", "reason": "sec_user_agent_missing"}, 2)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    network_calls = 0
    try:
        company_tickers_url = "https://www.sec.gov/files/company_tickers_exchange.json"
        payload = fetch_json(company_tickers_url, user_agent)
        network_calls += 1
        (args.cache_dir / "company_tickers_exchange.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    except urllib.error.HTTPError as exc:
        reason = "sec_rate_limited" if exc.code == 429 else "sec_network_error"
        failures.append({"source": "company_tickers_exchange", "reason": reason, "http_status": exc.code})
    except Exception as exc:  # noqa: BLE001 - closed taxonomy is emitted below.
        failures.append({"source": "company_tickers_exchange", "reason": "sec_network_error", "detail": exc.__class__.__name__})
    status = "COMPLETED_WITH_ERRORS" if failures else "COMPLETED"
    return emit({
        "status": status,
        "selected": len(rows),
        "network_calls": network_calls,
        "cache_dir": str(args.cache_dir),
        "company_tickers_cached": not failures,
        "submissions_available": 0,
        "companyfacts_available": 0,
        "failures": failures,
        "scoring_calculated": False,
        "ranking_calculated": False,
        "recommendations_generated": False,
        "phase9c_authorized": False,
    }, 0 if not failures else 1)


if __name__ == "__main__":
    raise SystemExit(main())
