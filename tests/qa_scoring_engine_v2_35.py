#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from scoring_engine.core import build_raw_factors, canonical_json, latest_fundamentals, percentile_scores, price_factors, score_assets


def contract() -> dict:
    return json.loads((ROOT / "config/scoring_factor_contract_v1.json").read_text(encoding="utf-8"))


def synthetic_raw() -> dict:
    rows = [(f"2025-{(i//28)%12+1:02d}-{i%28+1:02d}", 100.0 + i * 0.2) for i in range(253)]
    fundamentals = {
        "A": {"operating_margin": .20, "net_margin": .10, "roa": .08, "roe_reported": .12, "revenue_growth_yoy": .10, "net_income_growth_yoy": .08, "eps_basic": 5, "book_value_per_share": 50},
        "B": {"operating_margin": .10, "net_margin": .05, "roa": .04, "roe_reported": .06, "revenue_growth_yoy": .02, "net_income_growth_yoy": .01, "eps_basic": 2, "book_value_per_share": 30},
    }
    return build_raw_factors(fundamentals, {"A": rows, "B": [(d, v * 1.1) for d, v in rows]})


def main() -> int:
    c = contract()
    assert abs(sum(f["weight"] for f in c["factors"]) - 1.0) < 1e-12
    raw = synthetic_raw()
    normalized = percentile_scores(raw, c)
    first = score_assets(raw, normalized, c)
    second = score_assets(raw, percentile_scores(raw, c), c)
    assert canonical_json(first) == canonical_json(second), "not deterministic"
    by_id = {r["asset_id"]: r for r in first}
    assert by_id["A"]["total_score"] > by_id["B"]["total_score"], "monotonic favorable fundamentals failed"
    assert all(math.isfinite(r["total_score"]) for r in first if r["total_score"] is not None)
    assert price_factors([(str(i), 100.0) for i in range(253)])["max_drawdown_12m"] == 0.0
    extreme = {"X": {"operating_margin": .2, "net_margin": 3.165, "roa": .1, "return_3m": .1, "return_6m": .2, "return_12m": .3, "distance_sma200": .1, "volatility_12m": .2, "max_drawdown_12m": .2}}
    ex = score_assets(extreme, percentile_scores(extreme, c), c)[0]
    assert ex["eligibility_status"] == "REVIEW_REQUIRED" and ex["total_score"] is None
    missing = {"Y": {"operating_margin": .2}}
    blocked = score_assets(missing, percentile_scores(missing, c), c)[0]
    assert blocked["eligibility_status"] == "BLOCKED" and blocked["confidence"] == "NOT_RANKABLE"
    low = {"L": {"operating_margin": .2, "net_margin": .1, "roa": .1, "return_3m": .1, "return_6m": .1, "return_12m": .1, "distance_sma200": .1, "volatility_12m": .2, "max_drawdown_12m": .2}}
    low_result = score_assets(low, percentile_scores(low, c), c)[0]
    assert low_result["confidence"] == "LOW" and low_result["eligibility_status"] == "PARTIAL_COMPARABILITY" and "rank" not in low_result
    bank = score_assets(raw, normalized, c, {"A": "financial_institution_requires_separate_factor_contract"})
    assert next(r for r in bank if r["asset_id"] == "A")["eligibility_status"] == "REVIEW_REQUIRED"
    tied = {"A": {"operating_margin": .1}, "B": {"operating_margin": .1}}
    tied_scores = percentile_scores(tied, c)
    assert tied_scores["A"]["operating_margin"] == tied_scores["B"]["operating_margin"] == 50.0
    pending = {"asset_id": "A", "metric": "net_margin", "value": .1, "validation_status": "pending", "publication_date": "2026-01-01", "period_end": "2025-12-31", "quality_flags": []}
    selected, _ = latest_fundamentals([pending], "2026-08-31")
    assert selected["A"]["net_margin"] == .1
    print("PASS: v2.35 scoring contract/determinism/monotonicity/missingness/outlier/ties")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
