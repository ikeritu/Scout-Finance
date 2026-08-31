#!/usr/bin/env python3
"""Audit phase-7 temporal evidence without calculating performance."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from backtesting.core import canonical_json, evidence_decision, sha256  # noqa: E402

CONTRACT = ROOT / "config/backtest_contract_v1.json"
GATE = ROOT / "config/backtest_promotion_gate_v1.json"
JPX_REPORT = ROOT / "outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/jquants_collection_report_v2_33g.json"
TWSE_REPORT = ROOT / "outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot/twse_opendata_collection_report_v2_33i.json"
NORMALIZED = ROOT / "outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/fundamental_records_v2_34f.jsonl"
OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_36_phase7_validation/phase7_aggregate_report_v2_36.json"


def local_temporal_audit() -> dict:
    result = {"available": NORMALIZED.exists(), "jpx_missing_publication_rows": None, "twse_missing_publication_rows": None}
    if not NORMALIZED.exists():
        return result
    counts = {"JPX": [0, 0], "TWSE": [0, 0]}
    for line in NORMALIZED.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        market = "TWSE" if row.get("provider") == "twse_mops_opendata" else "JPX"
        counts[market][0] += 1
        if not (row.get("publication_date") or row.get("filing_date")):
            counts[market][1] += 1
    result.update({"jpx_rows": counts["JPX"][0], "jpx_missing_publication_rows": counts["JPX"][1], "twse_rows": counts["TWSE"][0], "twse_missing_publication_rows": counts["TWSE"][1]})
    return result


def build_report() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    jpx = json.loads(JPX_REPORT.read_text(encoding="utf-8"))
    twse = json.loads(TWSE_REPORT.read_text(encoding="utf-8"))
    local = local_temporal_audit()
    jpx_sessions = jpx["sessions_per_asset"]
    minimum = contract["minimum_evidence"]["price_sessions_per_asset"]
    audit = {
        "point_in_time_metadata_complete": False,
        "lookahead_violations": 0,
        "data_leakage_violations": 0,
        "oos_windows": 0,
        "oos_rebalances": 0,
        "integrity_blocked": False,
    }
    decision = evidence_decision(audit, gate)
    return {
        "phase": "v2.36-phase7-validation",
        "status": "EVIDENCE_AUDITED_NO_PERFORMANCE_RUN",
        "decision": decision,
        "performance_observed": False,
        "contract_hash": sha256(CONTRACT),
        "gate_hash": sha256(GATE),
        "markets": {
            "JPX": {
                "classification": "INSUFFICIENT_HISTORY",
                "assets": jpx["valid_assets"],
                "price_start": jpx["date_coverage"]["global_min_valid_date_observed"],
                "price_end": jpx["date_coverage"]["global_max_valid_date_observed"],
                "sessions_min": jpx_sessions["min"],
                "sessions_median": jpx_sessions["median"],
                "required_sessions": minimum,
                "reason": "Two years of prices leave roughly one evaluable year after 12-month factor formation; no defensible two-window OOS validation."
            },
            "TWSE": {
                "classification": "BLOCKED_BY_TEMPORAL_METADATA",
                "assets": twse["valid_assets"],
                "price_start": twse["date_coverage"]["global_min_valid_date_observed"],
                "price_end": twse["date_coverage"]["global_max_valid_date_observed"],
                "adjusted_prices": False,
                "reason": "Normalized fundamentals have no verified publication date and price history is unadjusted; historical signals would require invented availability or unsafe returns."
            }
        },
        "local_temporal_audit": local,
        "limitations": [
            "The 50-asset pilot was selected before phase 7 and is not a survivorship-free historical universe.",
            "JPX price depth is insufficient for the pre-frozen OOS gate.",
            "TWSE fundamental publication dates are absent and its prices are unadjusted.",
            "No return, Sharpe, drawdown or benchmark statistic was calculated after insufficiency was established.",
            "Infrastructure QA is not evidence of predictive power."
        ],
        "phase8_authorized": False
    }


def main() -> int:
    report = build_report()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(OUTPUT.suffix + ".tmp")
    temporary.write_text(canonical_json(report), encoding="utf-8", newline="\n")
    temporary.replace(OUTPUT)
    print(canonical_json(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
