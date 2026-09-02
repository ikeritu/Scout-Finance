#!/usr/bin/env python3
"""Fail-closed SEC pilot runner for v2.38D."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation"
SELECTION = OUT / "us_sec_pilot_selection_v2_38d.csv"
MAX_LIMIT = 50
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


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
    host = "www.sec.gov" if "www.sec.gov" in url else "data.sec.gov"
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate", "Host": host})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            body = gzip.decompress(body)
        return json.loads(body.decode("utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def load_company_tickers(cache_dir: Path, user_agent: str) -> tuple[dict, int]:
    cache = cache_dir / "company_tickers_exchange.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8")), 0
    payload = fetch_json(SEC_TICKERS_URL, user_agent)
    write_json(cache, payload)
    return payload, 1


def rows_by_ticker(payload: dict) -> dict[str, list[dict]]:
    fields = payload.get("fields", [])
    data = payload.get("data", [])
    by_ticker: dict[str, list[dict]] = {}
    if not isinstance(fields, list) or not isinstance(data, list):
        return by_ticker
    for item in data:
        record = dict(zip(fields, item))
        ticker = str(record.get("ticker", "")).upper()
        if ticker:
            by_ticker.setdefault(ticker, []).append(record)
    return by_ticker


def resolve_cik(row: dict[str, str], sec_by_ticker: dict[str, list[dict]]) -> tuple[str, str]:
    matches = sec_by_ticker.get(row["ticker"].upper(), [])
    if not matches:
        return "", "cik_not_found"
    if len(matches) > 1:
        return "", "ticker_ambiguous"
    cik = str(matches[0].get("cik", "")).zfill(10)
    if not cik.isdigit() or len(cik) != 10:
        return "", "cik_malformed"
    return cik, "cik_resolved"


def fetch_optional_json(url: str, user_agent: str, output: Path) -> tuple[bool, str, int]:
    if output.exists():
        return True, "cached", 0
    payload = fetch_json(url, user_agent)
    write_json(output, payload)
    return True, "downloaded", 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--asset-id")
    parser.add_argument("--cache-dir", type=Path, default=OUT / "sec_raw_cache_v2_38d")
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
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
        payload, calls = load_company_tickers(args.cache_dir, user_agent)
        network_calls += calls
        sec_by_ticker = rows_by_ticker(payload)
    except urllib.error.HTTPError as exc:
        reason = "sec_rate_limited" if exc.code == 429 else "sec_network_error"
        return emit({"status": "BLOCKED", "reason": reason, "http_status": exc.code, "phase9c_authorized": False}, 2)
    except Exception as exc:  # noqa: BLE001 - closed taxonomy is emitted below.
        return emit({"status": "BLOCKED", "reason": "sec_network_error", "detail": exc.__class__.__name__, "phase9c_authorized": False}, 2)
    resolved = 0
    submissions_available = 0
    companyfacts_available = 0
    for row in rows:
        cik, resolution = resolve_cik(row, sec_by_ticker)
        if not cik:
            failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "reason": resolution})
            continue
        resolved += 1
        try:
            ok, _, calls = fetch_optional_json(SEC_SUBMISSIONS_URL.format(cik=cik), user_agent, args.cache_dir / "submissions" / f"CIK{cik}.json")
            network_calls += calls
            submissions_available += int(ok)
            if calls and args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)
        except urllib.error.HTTPError as exc:
            reason = "sec_rate_limited" if exc.code == 429 else "sec_submissions_error"
            failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "cik": cik, "source": "submissions", "reason": reason, "http_status": exc.code})
            if exc.code in {403, 429}:
                break
        except Exception as exc:  # noqa: BLE001
            failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "cik": cik, "source": "submissions", "reason": "sec_submissions_error", "detail": exc.__class__.__name__})
        try:
            ok, _, calls = fetch_optional_json(SEC_COMPANYFACTS_URL.format(cik=cik), user_agent, args.cache_dir / "companyfacts" / f"CIK{cik}.json")
            network_calls += calls
            companyfacts_available += int(ok)
            if calls and args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)
        except urllib.error.HTTPError as exc:
            reason = "sec_rate_limited" if exc.code == 429 else "sec_companyfacts_error"
            failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "cik": cik, "source": "companyfacts", "reason": reason, "http_status": exc.code})
            if exc.code in {403, 429}:
                break
        except Exception as exc:  # noqa: BLE001
            failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "cik": cik, "source": "companyfacts", "reason": "sec_companyfacts_error", "detail": exc.__class__.__name__})
    status = "COMPLETED_WITH_ERRORS" if failures else "COMPLETED"
    return emit({
        "status": status,
        "selected": len(rows),
        "network_calls": network_calls,
        "cache_dir": str(args.cache_dir),
        "company_tickers_cached": True,
        "cik_resolved": resolved,
        "submissions_available": submissions_available,
        "companyfacts_available": companyfacts_available,
        "failures": failures,
        "scoring_calculated": False,
        "ranking_calculated": False,
        "recommendations_generated": False,
        "phase9c_authorized": False,
    }, 0 if not failures else 1)


if __name__ == "__main__":
    raise SystemExit(main())
