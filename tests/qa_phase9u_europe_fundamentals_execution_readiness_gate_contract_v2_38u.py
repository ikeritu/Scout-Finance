#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_fundamentals_execution_readiness_gate_contract_v1.json"
SCHEMA = ROOT / "schemas/europe_fundamentals_execution_readiness_gate_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38U-europe-fundamentals-execution-readiness-gate"
    assert contract["input_phase"] == ["v2.38R", "v2.38S", "v2.38T"]
    assert contract["previous_phase"] == "v2.38T"
    assert set(contract["routes"]) == {"provider_pilot", "official_filings_review", "manual_review"}
    assert contract["routes"]["provider_pilot"]["credential_env_var"] == "EODHD_API_KEY"
    assert contract["routes"]["official_filings_review"]["credential_env_var"] == ""
    assert contract["routes"]["manual_review"]["execution_method"] == "human_manual_review"
    assert contract["routes"]["manual_review"]["automation_script_glob"] == ""
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
    assert schema["properties"]["route"]["enum"] == ["provider_pilot", "official_filings_review", "manual_review"]
    assert schema["properties"]["readiness_status"]["enum"] == ["READY", "NOT_READY"]
    assert schema["properties"]["real_fundamentals_downloaded"]["const"] == "false"
    assert schema["properties"]["network_used_in_this_gate"]["const"] == "false"
    assert schema["properties"]["phase9c_authorized"]["const"] == "false"
    print("PASS: v2.38U/contract/schema/execution-readiness-gate-guardrails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
