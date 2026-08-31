#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tests = [
    "tests/qa_backtest_contract_v2_36a.py",
    "tests/qa_no_lookahead_v2_36.py",
    "tests/qa_backtest_engine_v2_36c.py",
    "tests/qa_phase7_evidence_gate_v2_36.py",
    "tests/qa_scoring_engine_v2_35.py",
    "tests/qa_phase6_final_gate_v2_35c.py",
]
for test in tests:
    completed = subprocess.run([sys.executable, test], cwd=ROOT)
    if completed.returncode:
        raise SystemExit(f"FAIL: {test}")
for path in [ROOT / "config/backtest_contract_v1.json", ROOT / "config/backtest_promotion_gate_v1.json"]:
    text = path.read_text(encoding="utf-8").lower()
    assert "api_token" not in text and "password" not in text and "secret" not in text
report = (ROOT / "outputs/full_universe_source_acquisition/v2_36_phase7_validation/phase7_aggregate_report_v2_36.json").read_text(encoding="utf-8")
assert '"phase8_authorized": false' in report
print("PASS: v2.36 phase-7 full suite/offline/no-secrets/insufficient-evidence/no-phase8")
