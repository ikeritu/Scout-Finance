#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38c_us_eu_priority_coverage"


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_us_eu_priority_coverage_v2_38c.py")], cwd=ROOT, check=True, capture_output=True, text=True)
    with (OUT / "us_eu_provider_route_matrix_v2_38c.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert any(r["region"] == "US" and "SEC" in r["fundamental_route"] for r in rows)
    assert any(r["region"] == "EU" and r["market"] == "CBOE_EUROPE" and r["status"] == "SOURCE_REQUIRED" for r in rows)
    pilot = json.loads((OUT / "multi_region_coverage_pilot_v2_38c.json").read_text(encoding="utf-8"))
    assert pilot["status"] == "PILOT_DEFINED_NOT_EXECUTED"
    assert pilot["guardrails"]["network_calls"] == 0
    assert pilot["guardrails"]["scoring_calculated"] is False
    print("PASS: v2.38C/provider-routes/US-SEC/EU-home-exchange/pilot-defined-not-executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
