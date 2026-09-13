#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/phase9c_closure_audit_contract_v2_38bx.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38BX-phase9c-closure-audit"
    assert contract["input_phase_scoring"] == "v2.38BV"
    assert contract["input_phase_ui"] == "v2.38BW"
    assert contract["expected_main_ranking_count"] == 318
    assert contract["expected_partial_comparability_count"] == 373
    assert contract["expected_review_required_count"] == 124
    assert contract["expected_blocked_count"] == 270
    assert contract["expected_not_yet_scored_count"] == 26
    assert contract["expected_total_count"] == 1111
    for key in ("scoring_recomputed", "methodology_changed", "weights_changed", "network_allowed", "broker_actions_allowed", "financial_advice_allowed", "recommendations_allowed", "ui_recompute_allowed"):
        assert contract[key] is False
    assert contract["final_status"] == "COMPLETED_PHASE9C_CLOSURE_AUDIT_EXPERIMENTAL_RANKING_VERIFIED"
    print("PASS: v2.38BX/contract/phase9c-closure-guardrails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
