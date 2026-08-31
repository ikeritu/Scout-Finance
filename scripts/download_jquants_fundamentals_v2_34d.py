#!/usr/bin/env python3
"""Fail-closed acquisition adapter: J-Quants /v2/fins/summary -> raw JSON,
one file per asset, for the 42 JPX assets validated in phase 4. Reuses the
same account/token and rate-limit lesson as the v2.33G price pilot (the
documented 5/min limit is stricter in practice; backoff-and-retry on 429).

This script only fetches and stores the provider's raw response. It does
NOT normalize into the canonical FundamentalRecord schema (block F's job)
and does not compute anything. Raw output stays outside git (see
.gitignore) because it is the provider's licensed content, not our own
derived work.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from fundamental_adapters.errors import classify_http_error  # noqa: E402

API_KEY_ENV = "SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN"
FINS_SUMMARY_URL = "https://api.jquants.com/v2/fins/summary"
DEFAULT_REQUEST_DELAY = 15.0  # free plan: 5 requests/minute (observed stricter in practice, see v2.33G)
RATE_LIMIT_BACKOFF_SECONDS = 65.0
DEFAULT_MAX_RETRIES = 3
MANIFEST_PATH = Path("outputs/full_universe_source_acquisition/v2_34a_fundamental_universe_audit/fundamental_universe_manifest_v2_34a.csv")


def load_jpx_assets(manifest_path: Path) -> list[dict]:
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["exchange"] == "JPX"]
    if manifest_path == MANIFEST_PATH and len(rows) != 42:
        raise SystemExit(f"expected 42 JPX assets in the canonical block-A manifest, found {len(rows)}")
    return rows


def fetch_fins_summary(key: str, code: str, max_retries: int) -> list[dict]:
    query = urllib.parse.urlencode({"code": code})
    request = urllib.request.Request(f"{FINS_SUMMARY_URL}?{query}", headers={"x-api-key": key})
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < max_retries:
                print(f"    rate-limited (429), waiting {RATE_LIMIT_BACKOFF_SECONDS:.0f}s before retry {attempt + 1}/{max_retries}", flush=True)
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            raise
    else:
        raise urllib.error.HTTPError(FINS_SUMMARY_URL, 429, "rate limit retries exhausted", hdrs=None, fp=None)

    if "data" not in payload:
        raise ValueError("Provider response missing top-level 'data' key")
    return payload["data"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/full_universe_source_acquisition/v2_34d_fundamentals_acquisition/jquants_fundamentals_raw_v2_34d"))
    parser.add_argument("--execute", action="store_true", help="perform the real, authorized network collection")
    parser.add_argument("--resume", action="store_true", help="skip assets whose output file already exists (default behavior; flag kept explicit per the phase-5 acquisition contract)")
    parser.add_argument("--limit", type=int, default=None, help="only process the first N assets (pilot runs)")
    parser.add_argument("--asset-id", action="append", default=None, help="only process this pilot_id (repeatable)")
    parser.add_argument("--request-delay", type=float, default=DEFAULT_REQUEST_DELAY)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    args = parser.parse_args()

    if not args.execute:
        print("BLOCKED: pass --execute only after explicit authorization to run this pilot/collection")
        return 2

    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        print(f"BLOCKED: environment variable {API_KEY_ENV} is not configured")
        return 2

    assets = load_jpx_assets(args.manifest)
    if args.asset_id:
        wanted = set(args.asset_id)
        assets = [a for a in assets if a["pilot_id"] in wanted]
    if args.limit is not None:
        assets = assets[: args.limit]
    if not assets:
        print(json.dumps({"status": "BLOCKED", "reason": "no_assets_selected"}))
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    collected = 0
    skipped = 0
    failures: list[dict[str, object]] = []

    for i, asset in enumerate(assets):
        output = args.output_dir / f"{asset['pilot_id']}.json"
        if output.exists():
            skipped += 1
            continue

        if i > 0:
            time.sleep(args.request_delay)

        code = asset["provider_symbol_jquants"]
        try:
            disclosures = fetch_fins_summary(key, code, args.max_retries)
        except urllib.error.HTTPError as exc:
            failures.append({"pilot_id": asset["pilot_id"], "provider_symbol": code, "error_type": classify_http_error(exc), "http_status": exc.code})
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            failures.append({"pilot_id": asset["pilot_id"], "provider_symbol": code, "error_type": "TIMEOUT", "http_status": None})
            continue
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            failures.append({"pilot_id": asset["pilot_id"], "provider_symbol": code, "error_type": "SCHEMA_MISMATCH", "http_status": None})
            continue

        if not disclosures:
            failures.append({"pilot_id": asset["pilot_id"], "provider_symbol": code, "error_type": "EMPTY_RESPONSE", "http_status": None})
            continue

        mismatched = [d for d in disclosures if d.get("Code") not in (code, code.rstrip("0"))]
        if mismatched:
            failures.append({"pilot_id": asset["pilot_id"], "provider_symbol": code, "error_type": "IDENTITY_MISMATCH", "http_status": None})
            continue

        temporary = output.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps({"asset": asset, "provider": "jquants_fins_summary", "disclosures": disclosures}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output)
        collected += 1

    report = {
        "status": "COMPLETED" if not failures else "COMPLETED_WITH_ERRORS",
        "input_assets": len(assets),
        "collected": collected,
        "skipped_existing": skipped,
        "failed": len(failures),
        "failures": failures,
    }
    (args.output_dir / "download_report_v2_34d.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
