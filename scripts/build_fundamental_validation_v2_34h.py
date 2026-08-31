#!/usr/bin/env python3
"""Block H: validate the real block-F/G FundamentalRecord dataset (schema,
accounting equations, temporal consistency, economic sanity) and compute a
per-asset data-QUALITY score (never an investment score). No network, no
credentials.

Writes two files:
  - validation_detail_v2_34h.json: full detail including real values (e.g.
    sanity-flag magnitudes) -- kept out of git, same licensing reasoning as
    every other real-value file in phase 5.
  - fundamental_validation_report_v2_34h.json: aggregate only (counts,
    thresholds, per-asset scores and promotion tier -- no raw magnitudes) --
    this one is committed.

Promotion thresholds are defined in this file BEFORE the report is built,
per the phase-5 requirement that thresholds precede the decision they
gate, not follow it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fundamental_adapters import schema, validators  # noqa: E402

NORMALIZED_PATH = ROOT / "outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/fundamental_records_v2_34f.jsonl"
DERIVED_PATH = ROOT / "outputs/full_universe_source_acquisition/v2_34g_derived_metrics/derived_records_v2_34g.jsonl"
DETAIL_OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_34h_validation/validation_detail_v2_34h.json"
REPORT_OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_34h_validation/fundamental_validation_report_v2_34h.json"

# Defined BEFORE any score is computed, per the phase-5 requirement.
# These gate DATA quality/promotability for phase 6 eligibility -- they
# say nothing about whether any asset is a good investment.
PROMOTION_THRESHOLDS = {
    "PROMOTABLE": 0.75,      # composite_quality_score >= this
    "PARTIAL": 0.50,         # composite_quality_score >= this, < PROMOTABLE
    # below PARTIAL: NOT_PROMOTABLE
}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def promotion_tier(score: float) -> str:
    if score >= PROMOTION_THRESHOLDS["PROMOTABLE"]:
        return "PROMOTABLE"
    if score >= PROMOTION_THRESHOLDS["PARTIAL"]:
        return "PARTIAL"
    return "NOT_PROMOTABLE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detail-output", type=Path, default=DETAIL_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=REPORT_OUTPUT)
    args = parser.parse_args()

    if not NORMALIZED_PATH.exists() or not DERIVED_PATH.exists():
        print(json.dumps({"status": "BLOCKED", "reason": "run_block_f_and_block_g_first"}))
        return 2

    normalized = load_jsonl(NORMALIZED_PATH)
    derived = load_jsonl(DERIVED_PATH)
    all_records = normalized + derived

    schema_invalid = [(r["asset_id"], r["metric"], schema.validate_record(r)) for r in all_records]
    schema_invalid = [x for x in schema_invalid if x[2]]

    equation_results = validators.check_accounting_equations(normalized)
    temporal_problems = validators.check_temporal_consistency(normalized)
    sanity_flags = validators.check_economic_sanity(all_records)

    assets = sorted({(r["asset_id"], r["provider"]) for r in normalized})
    quality_scores = [validators.compute_quality_scores(asset_id, provider, normalized, equation_results, sanity_flags) for asset_id, provider in assets]
    for q in quality_scores:
        q["promotion_tier"] = promotion_tier(q["composite_quality_score"])

    detail = {
        "schema_version": "1.0.0", "block": "v2.34H",
        "schema_invalid_records": [{"asset_id": a, "metric": m, "problems": p} for a, m, p in schema_invalid],
        "accounting_equation_results": equation_results,
        "temporal_problems": temporal_problems,
        "economic_sanity_flags": sanity_flags,
        "quality_scores": quality_scores,
    }
    args.detail_output.parent.mkdir(parents=True, exist_ok=True)
    detail_tmp = args.detail_output.with_suffix(".json.tmp")
    detail_tmp.write_text(json.dumps(detail, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    detail_tmp.replace(args.detail_output)

    from collections import Counter
    equation_status_counts = Counter((e["equation"], e["status"]) for e in equation_results)
    sanity_flag_type_counts = Counter(f["issue"] for f in sanity_flags)
    promotion_tier_counts = Counter(q["promotion_tier"] for q in quality_scores)

    report = {
        "schema_version": "1.0.0", "block": "v2.34H",
        "promotion_thresholds": PROMOTION_THRESHOLDS,
        "total_records_validated": len(all_records),
        "schema_invalid_records_count": len(schema_invalid),
        "accounting_equation_status_counts": {f"{eq}/{status}": count for (eq, status), count in sorted(equation_status_counts.items())},
        "temporal_problems_count": len(temporal_problems),
        "economic_sanity_flag_type_counts": dict(sorted(sanity_flag_type_counts.items())),
        "economic_sanity_flags_total": len(sanity_flags),
        "assets_by_promotion_tier": dict(sorted(promotion_tier_counts.items())),
        "per_asset_quality_scores": [
            {"asset_id": q["asset_id"], "provider": q["provider"], "composite_quality_score": round(q["composite_quality_score"], 4),
             "dimensions": {k: (round(v, 4) if v is not None else None) for k, v in q["dimensions"].items()},
             "promotion_tier": q["promotion_tier"]}
            for q in quality_scores
        ],
    }
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    report_payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    report_tmp = args.report_output.with_suffix(".json.tmp")
    report_tmp.write_text(report_payload, encoding="utf-8")
    report_tmp.replace(args.report_output)

    print(json.dumps({
        "status": "COMPLETED" if not schema_invalid else "COMPLETED_WITH_SCHEMA_ERRORS",
        "total_records_validated": len(all_records),
        "schema_invalid_records_count": len(schema_invalid),
        "assets_by_promotion_tier": dict(sorted(promotion_tier_counts.items())),
    }, ensure_ascii=False))
    return 0 if not schema_invalid else 1


if __name__ == "__main__":
    raise SystemExit(main())
