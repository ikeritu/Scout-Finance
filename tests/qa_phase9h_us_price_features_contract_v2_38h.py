#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_price_features_contract_v1.json"
SCHEMA = ROOT / "schemas/us_price_feature_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38H-us-price-features"
    assert set(contract["allowed_price_feature_quality_status"]) == set(schema["properties"]["price_feature_quality_status"]["enum"])
    forbidden = set(contract["forbidden_actions"])
    assert {"network", "raw_price_cache_in_git", "scoring", "ranking", "recommendations", "predictions", "phase9c", "broker", "trading"} <= forbidden
    assert schema["additionalProperties"] is False
    for feature in contract["allowed_features"]:
        assert feature in schema["properties"], feature
    print("PASS: v2.38H/contract/schema/price-features/closed-statuses/no-scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
