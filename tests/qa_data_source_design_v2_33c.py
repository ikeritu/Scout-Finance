#!/usr/bin/env python3
"""Static gate for the v2.33C source architecture."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/data_sources_v2_33c.json"


def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert data["phase"] == "v2.33C"
    assert data["status"] == "DESIGN_VALIDATED_NO_CREDENTIALS_NO_CALLS"
    assert data["eligible_assets_to_enrich"] == 23_888
    providers = {item["id"]: item for item in data["providers"]}
    assert set(providers) == {"sec_edgar", "openfigi", "eodhd", "twelve_data", "alpha_vantage"}
    assert providers["sec_edgar"]["decision"].startswith("APPROVED")
    assert providers["eodhd"]["decision"].startswith("CONDITIONAL")
    assert providers["alpha_vantage"]["decision"] == "REJECTED_AS_FULL_UNIVERSE_PRIMARY"
    assert all(item["official_urls"] and all(url.startswith("https://") for url in item["official_urls"]) for item in providers.values())
    pilot = data["pilot_before_purchase"]
    assert pilot["sample_size"] == 240
    assert pilot["max_false_identity_matches"] == 0
    assert pilot["required_match_rate"] >= 0.9
    governance = data["governance"]
    assert governance == {
        "provider_purchase_authorized": False,
        "credentials_present": False,
        "network_collection_executed": False,
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }
    text = REGISTRY.read_text(encoding="utf-8").casefold()
    assert "api_key=" not in text and "api_token=" not in text
    print("PASS: v2.33C/5-sources/hybrid-architecture/240-pilot/no-purchase/no-credentials/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
