#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/macro_geopolitical_context_contract_v1.json"
SCHEMA = ROOT / "schemas/macro_geopolitical_context_record_v1.schema.json"

REQUIRED_THEMES = {
    "INTEREST_RATES", "INFLATION", "USD_STRENGTH", "AI_SEMICONDUCTORS",
    "DEFENSE_SECURITY", "ENERGY_TRANSITION", "OIL_GAS_SUPPLY",
    "CHINA_US_TENSIONS", "SUPPLY_CHAIN_RESILIENCE", "CYBERSECURITY",
    "HEALTHCARE_REGULATION", "BANK_CREDIT_CYCLE", "SMALL_CAP_LIQUIDITY",
    "INDUSTRIAL_RESHORING", "EUROPE_REGULATORY_DRAG", "CLIMATE_POLICY",
    "COMMODITY_INPUT_COSTS",
}


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38M-macro-geopolitical-context"
    assert REQUIRED_THEMES.issubset(set(contract["taxonomy_themes"]))
    assert set(contract["allowed_statuses"]) == {
        "MACRO_CONTEXT_READY",
        "MACRO_CONTEXT_PARTIAL",
        "MACRO_CONTEXT_REVIEW_REQUIRED",
        "MACRO_CONTEXT_BLOCKED",
    }
    assert set(contract["allowed_note_types"]) == {
        "MACRO_OPPORTUNITY",
        "MACRO_RISK",
        "GEOPOLITICAL_EXPOSURE",
        "EVIDENCE_LIMITATION",
        "NEXT_RESEARCH_STEP",
        "LANGUAGE_GUARDRAIL",
    }
    assert contract["no_network"] is True
    assert contract["no_live_news"] is True
    assert contract["no_llm_runtime_classification"] is True
    assert contract["guardrails"]["network_calls"] == 0
    assert contract["guardrails"]["recommendations_generated"] is False
    assert contract["guardrails"]["financial_advice"] is False
    assert contract["guardrails"]["phase9c_authorized"] is False
    assert schema["properties"]["recommendation_generated"]["const"] is False
    assert schema["properties"]["financial_advice"]["const"] is False
    assert schema["properties"]["broker_actions_allowed"]["const"] is False
    assert schema["properties"]["phase9c_authorized"]["const"] is False
    print("PASS: v2.38M/contract/schema/static-macro-geo/no-live-news")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
