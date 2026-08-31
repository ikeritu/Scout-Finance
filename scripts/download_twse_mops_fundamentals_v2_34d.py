#!/usr/bin/env python3
"""Fail-closed acquisition adapter: TWSE MOPS open-data CSVs -> raw snapshot
+ per-asset extraction, for the 8 TWSE assets validated in phase 4.

Unlike J-Quants, MOPS open-data has no per-company query: each of the four
confirmed files (t187ap03_L company info, t187ap06_L_ci consolidated income
statement, t187ap07_L_ci consolidated balance sheet, t187ap17_L profitability
ratios) is a single CSV snapshot covering every listed company's most
recently disclosed period at once (confirmed in v2.34B: 1,048 rows, one
year/quarter pair -- e.g. "115"/"2" -- across the whole file). So this
adapter downloads the four whole-market files once (raw, outside git, see
.gitignore) and then extracts only our 8 companies' rows into per-asset
JSON files. --asset-id/--limit filter which companies get extracted, not
what gets downloaded -- there is no cheaper unit to fetch.

--from-date/--to-date are not applicable here (MOPS open-data has no
historical query) and are intentionally not offered, per v2.34B: the only
history obtainable this way is whatever this project accumulates forward
in time, one quarterly snapshot at a time.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from fundamental_adapters.errors import classify_http_error  # noqa: E402

BASE_URL = "https://mopsfin.twse.com.tw/opendata"
FILES = {
    "company_info": "t187ap03_L",
    "income_statement": "t187ap06_L_ci",
    "balance_sheet": "t187ap07_L_ci",
    "profitability_ratios": "t187ap17_L",
}
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
DEFAULT_REQUEST_DELAY = 1.0  # no documented rate limit; self-throttled to be polite (same posture as v2.33I)
DEFAULT_MAX_RETRIES = 3
COMPANY_CODE_FIELD = "公司代號"  # 公司代號
MANIFEST_PATH = Path("outputs/full_universe_source_acquisition/v2_34a_fundamental_universe_audit/fundamental_universe_manifest_v2_34a.csv")


def load_twse_assets(manifest_path: Path) -> list[dict]:
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["exchange"] == "TWSE"]
    if manifest_path == MANIFEST_PATH and len(rows) != 8:
        raise SystemExit(f"expected 8 TWSE assets in the canonical block-A manifest, found {len(rows)}")
    return rows


def fetch_csv_rows(file_code: str, max_retries: int) -> list[dict]:
    url = f"{BASE_URL}/{file_code}.csv"
    request = urllib.request.Request(url, headers={"User-Agent": "ScoutFinance/2.34D local-personal-pilot"})
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=60, context=SSL_CONTEXT) as response:
                raw = response.read()
            text = raw.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            if not rows:
                raise ValueError("empty CSV body")
            if COMPANY_CODE_FIELD not in (reader.fieldnames or []):
                raise ValueError(f"missing expected column {COMPANY_CODE_FIELD!r}")
            return rows
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 429 and attempt < max_retries:
                time.sleep(30.0)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(5.0)
                continue
            raise
    raise last_exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/full_universe_source_acquisition/v2_34d_fundamentals_acquisition/twse_mops_raw_v2_34d"))
    parser.add_argument("--execute", action="store_true", help="perform the real, authorized network collection")
    parser.add_argument("--resume", action="store_true", help="skip a snapshot file whose raw CSV was already downloaded today's session (default behavior; flag kept explicit per the phase-5 acquisition contract)")
    parser.add_argument("--limit", type=int, default=None, help="only extract the first N of the 8 TWSE assets")
    parser.add_argument("--asset-id", action="append", default=None, help="only extract this pilot_id (repeatable)")
    parser.add_argument("--request-delay", type=float, default=DEFAULT_REQUEST_DELAY)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    args = parser.parse_args()

    if not args.execute:
        print("BLOCKED: pass --execute only after explicit authorization to run this pilot/collection")
        return 2

    assets = load_twse_assets(args.manifest)
    if args.asset_id:
        wanted = set(args.asset_id)
        assets = [a for a in assets if a["pilot_id"] in wanted]
    if args.limit is not None:
        assets = assets[: args.limit]
    if not assets:
        print(json.dumps({"status": "BLOCKED", "reason": "no_assets_selected"}))
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output_dir / "raw_snapshots"
    raw_dir.mkdir(parents=True, exist_ok=True)

    snapshots: dict[str, list[dict]] = {}
    download_failures: list[dict[str, object]] = []
    first_call = True
    for name, file_code in FILES.items():
        raw_path = raw_dir / f"{file_code}.csv.json"
        if raw_path.exists():
            snapshots[name] = json.loads(raw_path.read_text(encoding="utf-8"))["rows"]
            continue
        if not first_call:
            time.sleep(args.request_delay)
        first_call = False
        try:
            rows = fetch_csv_rows(file_code, args.max_retries)
        except urllib.error.HTTPError as exc:
            download_failures.append({"file": file_code, "error_type": classify_http_error(exc), "http_status": exc.code})
            continue
        except (urllib.error.URLError, TimeoutError):
            download_failures.append({"file": file_code, "error_type": "TIMEOUT", "http_status": None})
            continue
        except ValueError:
            download_failures.append({"file": file_code, "error_type": "SCHEMA_MISMATCH", "http_status": None})
            continue

        temporary = raw_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps({"file_code": file_code, "rows": rows}, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(raw_path)
        snapshots[name] = rows

    if download_failures:
        report = {
            "status": "BLOCKED_DOWNLOAD_FAILED",
            "download_failures": download_failures,
            "extracted": 0,
        }
        (args.output_dir / "download_report_v2_34d.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=False))
        return 1

    extracted = 0
    skipped = 0
    failures: list[dict[str, object]] = []
    for asset in assets:
        output = args.output_dir / f"{asset['pilot_id']}.json"
        if output.exists():
            skipped += 1
            continue

        code = asset["provider_symbol_twse"].split(".")[0]
        per_source_rows = {name: [r for r in rows if r.get(COMPANY_CODE_FIELD) == code] for name, rows in snapshots.items()}

        if not any(per_source_rows.values()):
            failures.append({"pilot_id": asset["pilot_id"], "provider_symbol": code, "error_type": "EMPTY_RESPONSE", "http_status": None})
            continue

        temporary = output.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps({"asset": asset, "provider": "twse_mops_opendata", "snapshot_files": per_source_rows}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output)
        extracted += 1

    report = {
        "status": "COMPLETED" if not failures else "COMPLETED_WITH_ERRORS",
        "input_assets": len(assets),
        "extracted": extracted,
        "skipped_existing": skipped,
        "failed": len(failures),
        "failures": failures,
        "snapshot_row_counts": {name: len(rows) for name, rows in snapshots.items()},
    }
    (args.output_dir / "download_report_v2_34d.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
