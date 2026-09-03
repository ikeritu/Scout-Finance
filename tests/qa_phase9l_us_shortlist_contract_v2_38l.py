#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_explained_shortlist_contract_v1.json"
SCHEMA = ROOT / "schemas/us_explained_shortlist_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38L-us-explained-shortlist"
    assert contract["default_limit"] == 50
    assert contract["max_limit"] == 100
    assert set(contract["allowed_shortlist_buckets"]) == {
        "SHORTLIST_HIGH_PRIORITY",
        "SHORTLIST_MEDIUM_PRIORITY",
        "SHORTLIST_WATCHLIST",
        "REVIEW_REQUIRED",
        "BLOCKED",
    }
    assert "buy" in contract["forbidden_language"]
    assert contract["guardrails"]["network_calls"] == 0
    assert contract["guardrails"]["recommendation_generated"] is False
    assert contract["guardrails"]["recommendations_generated"] is False
    assert contract["guardrails"]["financial_advice"] is False
    assert contract["guardrails"]["phase9c_authorized"] is False
    assert schema["properties"]["recommendation_generated"]["const"] is False
    assert schema["properties"]["financial_advice"]["const"] is False
    assert schema["properties"]["broker_actions_allowed"]["const"] is False
    assert schema["properties"]["phase9c_authorized"]["const"] is False
    print("PASS: v2.38L/contract/schema/explained-shortlist/no-final-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
