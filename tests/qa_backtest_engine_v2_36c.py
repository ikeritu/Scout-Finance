#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from backtesting.core import BacktestIntegrityError, canonical_json, evidence_decision, metrics, midrank_percentiles, portfolio_return, spearman

a = midrank_percentiles({"B": 2, "A": 1, "C": 2})
b = midrank_percentiles({"C": 2, "B": 2, "A": 1})
assert a == b == {"A": 0.0, "B": 75.0, "C": 75.0}
net = portfolio_return({"A": 0.5, "B": 0.5}, {"A": 0.10, "B": 0.0}, 1.0, 25)
assert abs(net - 0.0475) < 1e-12
try:
    portfolio_return({"A": 1.0}, {"A": 0.1}, 1.0, -1)
    raise AssertionError("negative cost accepted")
except BacktestIntegrityError:
    pass
m = metrics([0.01, -0.02, 0.03], [0.0, 0.0, 0.0])
assert m["observations"] == 3 and m["maximum_drawdown"] < 0
assert spearman([(1, 1), (2, 2), (3, 3)]) == 1.0
gate = json.loads((ROOT / "config/backtest_promotion_gate_v1.json").read_text(encoding="utf-8"))
audit = {"point_in_time_metadata_complete": False, "oos_windows": 0, "oos_rebalances": 0}
assert evidence_decision(audit, gate) == "INSUFFICIENT_EVIDENCE"
payload = {"x": 1.0, "status": "deterministic"}
assert canonical_json(payload) == canonical_json(payload)
try:
    canonical_json({"bad": math.nan})
    raise AssertionError("NaN accepted")
except ValueError:
    pass
print("PASS: v2.36 engine/determinism/ties/costs/metrics/insufficient-evidence/no-NaN")
