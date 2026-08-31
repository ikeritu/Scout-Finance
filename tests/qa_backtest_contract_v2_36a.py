#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads((ROOT / "config/backtest_contract_v1.json").read_text(encoding="utf-8"))
gate = json.loads((ROOT / "config/backtest_promotion_gate_v1.json").read_text(encoding="utf-8"))

assert contract["frozen_before_performance"] is True
assert contract["information_policy"]["publication_date_required"] is True
assert contract["information_policy"]["retrieved_at_fallback_forbidden"] is True
assert contract["information_policy"]["execution_lag_sessions"] >= 1
assert contract["cost_scenarios_bps_one_way"]["base"] > 0
assert contract["benchmark"]["primary"] == "eligible_universe_equal_weight"
assert contract["excluded_assets"] == ["P020", "P178"]
assert contract["phase8_authorized"] is False and gate["phase8_authorized"] is False
assert gate["threshold_changes_after_results_forbidden"] is True
print("PASS: v2.36A contract/frozen-before-performance/PIT/costs/benchmark/no-phase8")
