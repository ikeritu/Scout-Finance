#!/usr/bin/env python3
"""Block G: run the derived-metrics calculator over the real block-F
normalized dataset. Writes the full set of derived FundamentalRecord rows
locally as JSONL (kept out of git, same reasoning as blocks D/F: real
computed values are still derived from licensed provider data) and an
aggregate, git-safe coverage manifest (counts and quality-flag totals only,
no values). No network, no credentials.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fundamental_adapters import derived_metrics, schema  # noqa: E402

NORMALIZED_DATASET_PATH = ROOT / "outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/fundamental_records_v2_34f.jsonl"
DERIVED_DATASET_PATH = ROOT / "outputs/full_universe_source_acquisition/v2_34g_derived_metrics/derived_records_v2_34g.jsonl"
MANIFEST_PATH = ROOT / "outputs/full_universe_source_acquisition/v2_34g_derived_metrics/derived_metrics_coverage_manifest_v2_34g.json"


def load_normalized_records(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def build_coverage_manifest(derived: list[dict]) -> dict:
    by_metric = defaultdict(lambda: {"ok": 0, "missing_by_reason": Counter(), "flagged": 0, "invalid_schema": 0})
    for record in derived:
        problems = schema.validate_record(record)
        entry = by_metric[record["metric"]]
        if problems:
            entry["invalid_schema"] += 1
            continue
        if record["value"] is not None:
            entry["ok"] += 1
        else:
            entry["missing_by_reason"][record["missing_reason"]] += 1
        if record["quality_flags"]:
            entry["flagged"] += 1

    per_metric = []
    for metric in sorted(by_metric):
        e = by_metric[metric]
        per_metric.append({
            "metric": metric,
            "ok_records": e["ok"],
            "missing_by_reason": dict(sorted(e["missing_by_reason"].items())),
            "flagged_records": e["flagged"],
            "invalid_schema_records": e["invalid_schema"],
        })

    return {
        "schema_version": "1.0.0",
        "block": "v2.34G",
        "total_derived_records": len(derived),
        "total_invalid_schema_records": sum(e["invalid_schema"] for e in by_metric.values()),
        "per_metric": per_metric,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized-input", type=Path, default=NORMALIZED_DATASET_PATH)
    parser.add_argument("--dataset-output", type=Path, default=DERIVED_DATASET_PATH)
    parser.add_argument("--manifest-output", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()

    if not args.normalized_input.exists():
        print(json.dumps({"status": "BLOCKED", "reason": "normalized_dataset_not_found_run_block_f_first"}))
        return 2

    normalized = load_normalized_records(args.normalized_input)
    derived = derived_metrics.compute_derived_records(normalized)
    manifest = build_coverage_manifest(derived)

    args.dataset_output.parent.mkdir(parents=True, exist_ok=True)
    dataset_tmp = args.dataset_output.with_suffix(".jsonl.tmp")
    with dataset_tmp.open("w", encoding="utf-8") as handle:
        for record in derived:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    dataset_tmp.replace(args.dataset_output)

    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    manifest_tmp = args.manifest_output.with_suffix(".json.tmp")
    manifest_tmp.write_text(manifest_payload, encoding="utf-8")
    manifest_tmp.replace(args.manifest_output)

    print(json.dumps({
        "status": "COMPLETED" if manifest["total_invalid_schema_records"] == 0 else "COMPLETED_WITH_SCHEMA_ERRORS",
        "total_derived_records": manifest["total_derived_records"],
        "total_invalid_schema_records": manifest["total_invalid_schema_records"],
    }, ensure_ascii=False))
    return 0 if manifest["total_invalid_schema_records"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
