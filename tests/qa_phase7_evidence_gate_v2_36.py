#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runner = ROOT / "scripts/audit_phase7_evidence_v2_36.py"
report_path = ROOT / "outputs/full_universe_source_acquisition/v2_36_phase7_validation/phase7_aggregate_report_v2_36.json"

first = subprocess.run([sys.executable, str(runner)], cwd=ROOT, capture_output=True, check=True).stdout
saved = report_path.read_bytes()
assert b"\r\n" not in saved
second = subprocess.run([sys.executable, str(runner)], cwd=ROOT, capture_output=True, check=True).stdout
assert first == second and saved == report_path.read_bytes()
report = json.loads(saved)
assert report["decision"] == "INSUFFICIENT_EVIDENCE"
assert report["performance_observed"] is False
assert report["markets"]["JPX"]["classification"] == "INSUFFICIENT_HISTORY"
assert report["markets"]["JPX"]["sessions_median"] < report["markets"]["JPX"]["required_sessions"]
assert report["markets"]["TWSE"]["classification"] == "BLOCKED_BY_TEMPORAL_METADATA"
assert report["markets"]["TWSE"]["adjusted_prices"] is False
assert report["phase8_authorized"] is False
gate_text = (ROOT / "outputs/full_universe_source_acquisition/v2_36_phase7_final_gate/PHASE7_FINAL_GATE_v2_36.md").read_text(encoding="utf-8")
assert "INSUFFICIENT_EVIDENCE" in gate_text
assert "phase8_authorized: false" in gate_text
assert "FASE 8 NO AUTORIZADA" in gate_text
print("PASS: v2.36 evidence/JPX-insufficient/TWSE-temporal-block/no-performance/no-phase8")
