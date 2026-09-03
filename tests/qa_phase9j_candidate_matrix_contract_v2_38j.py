#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_candidate_feature_matrix_contract_v1.json"
SCHEMA = ROOT / "schemas/us_candidate_feature_matrix_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38J-us-candidate-feature-matrix"
    assert set(contract["allowed_candidate_statuses"]) == {
        "CANDIDATE_MATRIX_READY",
        "CANDIDATE_MATRIX_PARTIAL_PRICE",
        "CANDIDATE_MATRIX_PARTIAL_FUNDAMENTALS",
        "CANDIDATE_MATRIX_INSUFFICIENT_EVIDENCE",
        "CANDIDATE_MATRIX_BLOCKED",
    }
    assert contract["guardrails"] == {
        "network_calls": 0,
        "phase9c_authorized": False,
        "ranking_calculated": False,
        "recommendations_generated": False,
        "scoring_calculated": False,
    }
    assert schema["properties"]["scoring_calculated"]["const"] is False
    assert schema["properties"]["ranking_calculated"]["const"] is False
    assert schema["properties"]["recommendation_generated"]["const"] is False
    print("PASS: v2.38J/contract/schema/closed-statuses/no-scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
