#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_manual_review_pack_contract_v1.json"
SCHEMA = ROOT / "schemas/europe_manual_review_pack_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38T-europe-manual-review-pack"
    assert contract["input_phase"] == "v2.38Q"
    assert contract["previous_phase"] == "v2.38S"
    assert contract["eligible_route_status"] == "FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED"
    assert contract["expected_manual_review_assets"] == 17
    assert contract["known_placeholder_company_names"] == ["UKI0"]
    assert len(contract["required_human_actions"]) == 3
    assert contract["no_network"] is True
    assert contract["no_scraping"] is True
    assert contract["no_api_call"] is True
    assert contract["real_filings_downloaded"] is False
    assert contract["real_fundamentals_present"] is False
    assert contract["normalized_fundamentals_created"] is False
    assert contract["no_scoring"] is True
    assert contract["no_ranking"] is True
    assert contract["no_recommendations"] is True
    assert contract["no_phase9c"] is True
    assert contract["raw_cache_published"] is False
    assert schema["properties"]["phase"]["const"] == contract["phase"]
    assert schema["properties"]["route_from_38q"]["const"] == contract["eligible_route_status"]
    assert schema["properties"]["identity_verified"]["const"] == "false"
    assert schema["properties"]["identity_review_required"]["const"] == "true"
    assert schema["properties"]["registry_review_required"]["const"] == "true"
    assert schema["properties"]["provider_review_required"]["const"] == "true"
    assert schema["properties"]["no_network_fetch"]["const"] == "true"
    assert schema["properties"]["no_scraping"]["const"] == "true"
    assert schema["properties"]["no_api_call"]["const"] == "true"
    assert schema["properties"]["no_scoring"]["const"] == "true"
    assert schema["properties"]["no_ranking"]["const"] == "true"
    assert schema["properties"]["no_recommendation"]["const"] == "true"
    assert schema["properties"]["no_phase9c"]["const"] == "true"
    print("PASS: v2.38T/contract/schema/manual-review-pack-guardrails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
