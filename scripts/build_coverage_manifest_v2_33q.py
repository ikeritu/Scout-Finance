#!/usr/bin/env python3
"""Build the per-asset coverage manifest (Bloque F3) from the real, locally
downloaded collections of every approved adapter, via the canonical schema
(scripts/price_adapters/). No network calls, no credentials. Reads only
data already fetched by each pilot's own fail-closed downloader.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from price_adapters import jquants_adapter, twse_adapter  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_33q_multisource_architecture"

ADAPTERS = {
    "jquants": {
        "module": jquants_adapter,
        "raw_dir": ROOT / "outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/jquants_prices_collection_v2_33g",
    },
    "twse_opendata": {
        "module": twse_adapter,
        "raw_dir": ROOT / "outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot/twse_opendata_prices_collection_v2_33i",
    },
}


def build_manifest() -> dict:
    per_asset = defaultdict(list)
    provider_status = {}

    for name, cfg in ADAPTERS.items():
        raw_dir = cfg["raw_dir"]
        if not raw_dir.exists():
            provider_status[name] = "SKIPPED_NO_LOCAL_DATA"
            continue
        records = cfg["module"].normalize_collection(raw_dir)
        for r in records:
            per_asset[r.asset_id].append(r)
        provider_status[name] = "LOADED"

    manifest_rows = []
    for asset_id, records in sorted(per_asset.items()):
        ok_records = [r for r in records if r.quality_status == "ok"]
        dates = sorted(r.date for r in ok_records)
        provider = records[0].provider
        manifest_rows.append({
            "asset_id": asset_id,
            "provider": provider,
            "provider_symbol": records[0].provider_symbol,
            "sessions_available": len(ok_records),
            "no_trade_calendar_rows": len(records) - len(ok_records),
            "date_range_start": dates[0] if dates else None,
            "date_range_end": dates[-1] if dates else None,
            "is_adjusted": records[0].is_adjusted,
            "adjustment_source": records[0].adjustment_source,
            "license_status": records[0].license_status,
            "confidence": "validated_real_collection",
            "block_reason": None,
            "last_updated": records[0].retrieved_at,
            "next_update_allowed": "no_incremental_policy_defined_yet_v2_33q",
        })

    return {
        "phase": "v2.33Q-coverage-manifest",
        "provider_status": provider_status,
        "assets_covered": len(manifest_rows),
        "manifest": manifest_rows,
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest()
    print(json.dumps({k: v for k, v in manifest.items() if k != "manifest"}, ensure_ascii=False, indent=2))
    print(f"... {len(manifest['manifest'])} asset rows (see --write output for full manifest)")

    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / "coverage_manifest_v2_33q.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
