#!/usr/bin/env python3
"""Controlled SEC enrichment runner for v2.38E."""
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
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38e_us_sec_enrichment_expansion"
OVERLAY = ROOT / "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation/us_sec_identity_overlay_v2_38d.csv"
MAX_LIMIT = 250
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def emit(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return code


def fetch_json(url: str, user_agent: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate", "Host": "data.sec.gov"})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            body = gzip.decompress(body)
        return json.loads(body.decode("utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def load_candidates(asset_id: str | None) -> list[dict[str, str]]:
    with OVERLAY.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    candidates = [r for r in rows if r["identity_status"] == "US_SEC_CIK_RESOLVED" and r["cik"]]
    if asset_id:
        candidates = [r for r in candidates if r["asset_id"] == asset_id]
    return sorted(candidates, key=lambda r: (r["asset_id"], r["ticker"]))


def has_cache(cache_dir: Path, cik: str) -> bool:
    return (cache_dir / "submissions" / f"CIK{cik}.json").exists() and (cache_dir / "companyfacts" / f"CIK{cik}.json").exists()


def select_batch(rows: list[dict[str, str]], cache_dir: Path, limit: int) -> list[dict[str, str]]:
    pending = [r for r in rows if not has_cache(cache_dir, r["cik"])]
    return pending[:limit]


def fetch_one(kind: str, cik: str, user_agent: str, cache_dir: Path) -> tuple[bool, int, str]:
    url = SUBMISSIONS_URL.format(cik=cik) if kind == "submissions" else COMPANYFACTS_URL.format(cik=cik)
    path = cache_dir / kind / f"CIK{cik}.json"
    if path.exists():
        return True, 0, "cached"
    payload = fetch_json(url, user_agent)
    write_json(path, payload)
    return True, 1, "downloaded"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--asset-id")
    parser.add_argument("--cache-dir", type=Path, default=OUT / "sec_raw_cache_v2_38e")
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.limit <= MAX_LIMIT:
        return emit({"status": "BLOCKED", "reason": "batch_limit_must_be_1_to_250"}, 2)
    rows = load_candidates(args.asset_id)
    selected = select_batch(rows, args.cache_dir, args.limit)
    skipped_existing = len(rows) - len([r for r in rows if not has_cache(args.cache_dir, r["cik"])])
    if not args.execute:
        return emit({
            "status": "DRY_RUN",
            "eligible_with_cik": len(rows),
            "skipped_existing": skipped_existing,
            "selected": len(selected),
            "asset_ids": [r["asset_id"] for r in selected],
            "network_calls": 0,
            "phase9c_authorized": False,
        })
    user_agent = os.environ.get("SCOUT_FINANCE_SEC_USER_AGENT", "").strip()
    if not user_agent:
        return emit({"status": "BLOCKED", "reason": "sec_user_agent_missing"}, 2)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    failures: list[dict] = []
    collected = 0
    network_calls = 0
    submissions_available = 0
    companyfacts_available = 0
    for row in selected:
        cik = row["cik"]
        row_ok = True
        for kind in ("submissions", "companyfacts"):
            try:
                ok, calls, _ = fetch_one(kind, cik, user_agent, args.cache_dir)
                network_calls += calls
                if kind == "submissions":
                    submissions_available += int(ok)
                else:
                    companyfacts_available += int(ok)
                if calls and args.sleep_seconds > 0:
                    time.sleep(args.sleep_seconds)
            except urllib.error.HTTPError as exc:
                reason = "sec_rate_limited" if exc.code == 429 else f"sec_{kind}_error"
                failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "cik": cik, "source": kind, "reason": reason, "http_status": exc.code})
                row_ok = False
                if exc.code in {403, 429}:
                    return emit(_payload(selected, collected, skipped_existing, failures, network_calls, submissions_available, companyfacts_available), 1)
            except Exception as exc:  # noqa: BLE001
                failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "cik": cik, "source": kind, "reason": f"sec_{kind}_error", "detail": exc.__class__.__name__})
                row_ok = False
        collected += int(row_ok)
    return emit(_payload(selected, collected, skipped_existing, failures, network_calls, submissions_available, companyfacts_available), 0 if not failures else 1)


def _payload(selected: list[dict[str, str]], collected: int, skipped_existing: int, failures: list[dict], network_calls: int, submissions_available: int, companyfacts_available: int) -> dict:
    return {
        "status": "COMPLETED_WITH_ERRORS" if failures else "COMPLETED",
        "selected": len(selected),
        "collected": collected,
        "skipped_existing": skipped_existing,
        "failed": len(failures),
        "failures": failures,
        "network_calls": network_calls,
        "submissions_available": submissions_available,
        "companyfacts_available": companyfacts_available,
        "scoring_calculated": False,
        "ranking_calculated": False,
        "recommendations_generated": False,
        "phase9c_authorized": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
