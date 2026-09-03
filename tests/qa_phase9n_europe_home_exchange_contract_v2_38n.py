#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_home_exchange_resolution_contract_v1.json"
SCHEMA = ROOT / "schemas/europe_home_exchange_resolution_record_v1.schema.json"

STATUSES = {
    "HOME_EXCHANGE_RESOLVED",
    "CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED",
    "MULTILISTING_REVIEW_REQUIRED",
    "ADR_GDR_REVIEW_REQUIRED",
    "COUNTRY_EXCHANGE_MISMATCH_REVIEW",
    "PROVIDER_ROUTE_BLOCKED",
    "INSUFFICIENT_IDENTITY_EVIDENCE",
    "OUT_OF_SCOPE_NON_EUROPE",
}


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38N-europe-home-exchange-resolution"
    assert contract["input_universe_rows_expected"] == 43089
    assert contract["cboe_europe_is_secondary_by_default"] is True
    assert contract["home_exchange_required_for_europe_enrichment"] is True
    assert contract["no_network"] is True
    assert contract["no_scoring"] is True
    assert contract["no_ranking"] is True
    assert contract["no_recommendations"] is True
    assert contract["no_phase9c"] is True
    assert set(contract["closed_statuses"]) == STATUSES
    props = schema["properties"]
    assert props["phase"]["const"] == "v2.38N-europe-home-exchange-resolution"
    assert set(props["resolution_status"]["enum"]) == STATUSES
    assert props["scoring_calculated"]["const"] is False
    assert props["ranking_calculated"]["const"] is False
    assert props["recommendations_generated"]["const"] is False
    assert props["phase9c_authorized"]["const"] is False
    print("PASS: v2.38N/contract/schema/home-exchange-guardrails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
