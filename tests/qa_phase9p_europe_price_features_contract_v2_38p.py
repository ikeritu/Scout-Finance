#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_price_features_contract_v1.json"
SCHEMA = ROOT / "schemas/europe_price_feature_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38P-europe-price-features"
    assert contract["raw_cache_published"] is False
    assert contract["no_network"] is True
    assert contract["no_scoring"] is True
    assert contract["no_ranking"] is True
    assert contract["no_recommendations"] is True
    assert contract["no_phase9c"] is True
    assert contract["cboe_europe_source_forbidden"] is True
    assert contract["min_rows_ready"] == 252
    assert contract["min_rows_partial"] == 120
    assert schema["properties"]["phase"]["const"] == "v2.38P-europe-price-features"
    assert schema["properties"]["scoring_calculated"]["const"] == "false"
    assert schema["properties"]["ranking_calculated"]["const"] == "false"
    assert schema["properties"]["recommendations_generated"]["const"] == "false"
    assert schema["properties"]["phase9c_authorized"]["const"] == "false"
    assert "EUROPE_PRICE_FEATURES_READY" in schema["properties"]["price_quality_status"]["enum"]
    print("PASS: v2.38P/contract/schema/price-features/closed-statuses/no-scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
