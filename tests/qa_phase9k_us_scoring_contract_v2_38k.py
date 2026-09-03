#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_experimental_scoring_contract_v1.json"
SCHEMA = ROOT / "schemas/us_experimental_score_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38K-us-experimental-scoring"
    assert round(sum(contract["pillar_weights"].values()), 6) == 1.0
    assert contract["pillar_weights"] == {
        "fundamentals_quality": 0.3,
        "growth_momentum": 0.2,
        "profitability_cashflow": 0.2,
        "price_momentum_trend": 0.2,
        "risk_liquidity": 0.1,
    }
    assert contract["guardrails"]["scoring_calculated"] is True
    assert contract["guardrails"]["ranking_calculated"] is True
    assert contract["guardrails"]["recommendations_generated"] is False
    assert contract["guardrails"]["phase9c_authorized"] is False
    assert contract["guardrails"]["broker_actions_allowed"] is False
    assert schema["properties"]["scoring_calculated"]["const"] is True
    assert schema["properties"]["ranking_calculated"]["const"] is True
    assert schema["properties"]["recommendation_generated"]["const"] is False
    print("PASS: v2.38K/contract/schema/experimental-scoring/no-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
