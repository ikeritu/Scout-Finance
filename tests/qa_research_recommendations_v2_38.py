#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_v2_37.recommendations import candidate_explanation, select_interesting_companies


def asset(asset_id, score, status="ELIGIBLE_PARTIAL", confidence="HIGH"):
    return {
        "asset_id": asset_id, "total_score": score, "eligibility_status": status, "confidence": confidence,
        "pillar_scores": {"quality": 80, "growth": 55, "risk": 40},
        "strength_factors": ["operating_margin"], "weakness_factors": ["volatility_12m"],
    }


def main() -> int:
    rows = [
        asset("A", 72), asset("B", 60), asset("C", 59.99),
        asset("P020", 99, "REVIEW_REQUIRED", "NOT_RANKABLE"),
        asset("TW", 90, "PARTIAL_COMPARABILITY", "LOW"),
    ]
    selected = select_interesting_companies(rows)
    assert [row["asset_id"] for row in selected] == ["A", "B"]
    assert select_interesting_companies([asset("C", 59.99)]) == []
    explanation = candidate_explanation(selected[0])
    assert explanation["summary"].startswith("Score experimental 72.00")
    assert explanation["reasons"][0] == "pillar:quality:80.00"
    assert explanation["cautions"][0] == "pillar:risk:40.00"
    aggregate = candidate_explanation({**selected[0], "pillar_scores": {}, "strength_factors": [], "weakness_factors": []})
    assert aggregate["reasons"] == ["criterion:high_confidence", "criterion:score_above:60"]
    assert aggregate["cautions"] == ["limitation:aggregate_detail_unavailable"]
    print("PASS: v2.38 variable-selection/traceable-reasons/exclusions/no-buy-language")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
