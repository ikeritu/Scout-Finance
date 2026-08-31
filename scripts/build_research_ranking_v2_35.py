#!/usr/bin/env python3
"""Build the authorized phase-6 experimental ranking from local-only data."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scoring_engine.core import (  # noqa: E402
    build_raw_factors, canonical_json, latest_fundamentals, load_jsonl,
    load_prices, percentile_scores, score_assets, sha256,
)

CONTRACT = ROOT / "config/scoring_factor_contract_v1.json"
UNIVERSE = ROOT / "outputs/full_universe_source_acquisition/v2_34a_fundamental_universe_audit/fundamental_universe_manifest_v2_34a.csv"
NORMALIZED = ROOT / "outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/fundamental_records_v2_34f.jsonl"
DERIVED = ROOT / "outputs/full_universe_source_acquisition/v2_34g_derived_metrics/derived_records_v2_34g.jsonl"
PRICE_DIRS = [
    ROOT / "outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/jquants_prices_collection_v2_33g",
    ROOT / "outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot/twse_opendata_prices_collection_v2_33i",
]
OUTPUT_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_35_phase6_scoring_local"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of-date", default="2026-08-31")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    required = [CONTRACT, UNIVERSE, NORMALIZED, DERIVED, *PRICE_DIRS]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        print(canonical_json({"status": "BLOCKED_INPUT_DATA", "missing": missing}), end="")
        return 2

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    universe = list(csv.DictReader(UNIVERSE.open(encoding="utf-8", newline="")))
    if len(universe) != 50 or any(r["identity_status"] != "identity_verified" for r in universe):
        raise SystemExit("Expected exactly 50 identity_verified assets")
    records = load_jsonl(NORMALIZED) + load_jsonl(DERIVED)
    fundamentals, source_flags = latest_fundamentals(records, args.as_of_date)
    prices, pilots = load_prices(PRICE_DIRS, args.as_of_date)
    raw = build_raw_factors(fundamentals, prices)
    normalized = percentile_scores(raw, contract)
    results = score_assets(raw, normalized, contract)
    known = {r["asset_id"]: r for r in universe}
    for row in results:
        meta = known[row["asset_id"]]
        row.update({"company_name": meta["company_name"], "market": meta["exchange"], "ticker": meta["ticker"], "quality_flags": source_flags.get(row["asset_id"], [])})
    ranked = sorted((r for r in results if r.get("rank")), key=lambda r: r["rank"])
    shortlist = ranked[: contract["shortlist_size"]]
    status_counts = Counter(r["eligibility_status"] for r in results)
    report = {
        "phase": "v2.35-phase6-scoring", "status": "CALCULATED_NOT_PHASE7_VALIDATED",
        "as_of_date": args.as_of_date, "input_assets": len(universe), "assets_with_fundamentals": len(fundamentals),
        "assets_with_prices": len(prices), "eligibility_status_counts": dict(sorted(status_counts.items())),
        "ranked_assets": len(ranked), "shortlist_size": len(shortlist),
        "shortlist": [{"rank": r["rank"], "asset_id": r["asset_id"], "ticker": r["ticker"], "market": r["market"], "total_score": r["total_score"], "confidence": r["confidence"]} for r in shortlist],
        "input_hashes": {"contract": sha256(CONTRACT), "universe": sha256(UNIVERSE), "normalized": sha256(NORMALIZED), "derived": sha256(DERIVED)},
        "limitations": ["Experimental research ranking, not investment advice.", "No phase-7 backtest has been run.", "TWSE has one fundamental period; growth is not applicable.", "Debt, capex, FCF and buybacks are unavailable."],
        "phase7_authorized": False,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "scoring_results_v2_35.json").write_text(canonical_json(results), encoding="utf-8")
    (args.output_dir / "research_ranking_v2_35.json").write_text(canonical_json(ranked), encoding="utf-8")
    (args.output_dir / "scoring_aggregate_report_v2_35.json").write_text(canonical_json(report), encoding="utf-8")
    print(canonical_json(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
