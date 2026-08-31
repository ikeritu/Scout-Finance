#!/usr/bin/env python3
"""Block F: run both normalizers over the real block-D/E raw collections and
produce (1) the full set of normalized FundamentalRecord rows, written
locally as JSONL (kept out of git -- see .gitignore -- because it still
carries real provider-reported values), and (2) an aggregate, git-safe
coverage manifest: per-asset, per-metric counts only, no values. No network,
no credentials.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fundamental_adapters import jquants_normalizer, schema, twse_normalizer  # noqa: E402

JQUANTS_RAW_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_34d_fundamentals_acquisition/jquants_fundamentals_raw_v2_34d"
TWSE_RAW_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_34d_fundamentals_acquisition/twse_mops_raw_v2_34d"
DATASET_PATH = ROOT / "outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/fundamental_records_v2_34f.jsonl"
MANIFEST_PATH = ROOT / "outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/fundamental_coverage_manifest_v2_34f.json"


def build_records() -> list[dict]:
    records = jquants_normalizer.normalize_collection(JQUANTS_RAW_DIR)
    records += twse_normalizer.normalize_collection(TWSE_RAW_DIR)
    return records


def build_coverage_manifest(records: list[dict]) -> dict:
    per_asset = defaultdict(lambda: {"provider": None, "exchange": None, "total_records": 0, "ok": 0, "missing_by_reason": defaultdict(int), "invalid_schema": 0, "metrics_ok": set()})
    for record in records:
        problems = schema.validate_record(record)
        entry = per_asset[record["asset_id"]]
        entry["provider"] = record["provider"]
        entry["exchange"] = record["exchange"]
        entry["total_records"] += 1
        if problems:
            entry["invalid_schema"] += 1
            continue
        if record["value"] is not None:
            entry["ok"] += 1
            entry["metrics_ok"].add(record["metric"])
        else:
            entry["missing_by_reason"][record["missing_reason"]] += 1

    manifest = []
    for asset_id in sorted(per_asset):
        e = per_asset[asset_id]
        manifest.append({
            "asset_id": asset_id,
            "provider": e["provider"],
            "exchange": e["exchange"],
            "total_records": e["total_records"],
            "ok_records": e["ok"],
            "distinct_metrics_with_value": sorted(e["metrics_ok"]),
            "missing_by_reason": dict(sorted(e["missing_by_reason"].items())),
            "invalid_schema_records": e["invalid_schema"],
        })

    total_invalid = sum(e["invalid_schema"] for e in per_asset.values())
    return {
        "schema_version": "1.0.0",
        "block": "v2.34F",
        "assets_covered": len(per_asset),
        "total_records": len(records),
        "total_invalid_schema_records": total_invalid,
        "per_asset": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-output", type=Path, default=DATASET_PATH)
    parser.add_argument("--manifest-output", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()

    records = build_records()
    manifest = build_coverage_manifest(records)

    args.dataset_output.parent.mkdir(parents=True, exist_ok=True)
    dataset_tmp = args.dataset_output.with_suffix(".jsonl.tmp")
    with dataset_tmp.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    dataset_tmp.replace(args.dataset_output)

    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    manifest_tmp = args.manifest_output.with_suffix(".json.tmp")
    manifest_tmp.write_text(manifest_payload, encoding="utf-8")
    manifest_tmp.replace(args.manifest_output)

    print(json.dumps({
        "status": "COMPLETED" if manifest["total_invalid_schema_records"] == 0 else "COMPLETED_WITH_SCHEMA_ERRORS",
        "assets_covered": manifest["assets_covered"],
        "total_records": manifest["total_records"],
        "total_invalid_schema_records": manifest["total_invalid_schema_records"],
    }, ensure_ascii=False))
    return 0 if manifest["total_invalid_schema_records"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
