#!/usr/bin/env python3
"""Fail-closed batch entrypoint. Network adapters remain separately authorized."""
from __future__ import annotations

import argparse
import csv
import json
import lzma
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "outputs/full_universe_source_acquisition/v2_38b_global_enrichment/global_acquisition_manifest_v2_38b.csv.xz"
TOKEN_ENV = {"JPX": "JQUANTS_API_KEY", "NASDAQ": "TWELVE_DATA_API_KEY", "NYSE": "TWELVE_DATA_API_KEY", "NYSE American": "TWELVE_DATA_API_KEY", "Cboe BZX": "TWELVE_DATA_API_KEY"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 500:
        print(json.dumps({"status": "BLOCKED", "reason": "batch_limit_must_be_1_to_500"}))
        return 2
    with lzma.open(MANIFEST, "rt", encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["exchange"] == args.market and r["batch_eligible"] == "true"]
    plan = {"market": args.market, "requested_limit": args.limit, "available": len(rows), "selected": min(args.limit, len(rows)), "asset_ids": [r["asset_id"] for r in rows[:args.limit]]}
    if not args.execute:
        print(json.dumps({"status": "DRY_RUN", **plan}, ensure_ascii=False))
        return 0
    credential = TOKEN_ENV.get(args.market)
    if credential and not os.environ.get(credential, "").strip():
        print(json.dumps({"status": "BLOCKED", "reason": "credential_missing", "environment_variable": credential, **plan}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "BLOCKED", "reason": "market_adapter_not_authorized_for_v2_38b_real_collection", **plan}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
