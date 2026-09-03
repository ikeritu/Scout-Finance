#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_price_history_acquisition_contract_v1.json"
SCHEMA = ROOT / "schemas/europe_price_history_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38O-europe-price-history-acquisition"
    assert contract["only_home_exchange_resolved"] is True
    assert contract["cboe_europe_source_forbidden"] is True
    assert contract["raw_cache_published"] is False
    assert contract["no_scoring"] is True
    assert contract["no_ranking"] is True
    assert contract["no_recommendations"] is True
    assert contract["no_phase9c"] is True
    assert contract["max_batch_limit"] == 100
    assert set(contract["supported_providers"]) == {"stooq", "twelvedata", "eodhd", "yahoo_chart"}
    assert schema["properties"]["provider"]["enum"] == ["stooq", "twelvedata", "eodhd", "yahoo_chart"]
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "v2_38o_europe_price_history_acquisition/europe_price_history_raw_v2_38o/" in gitignore
    print("PASS: v2.38O/contract/schema/gitignore/home-exchange-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
