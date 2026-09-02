#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38c_us_eu_priority_coverage"


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_us_eu_priority_coverage_v2_38c.py")], cwd=ROOT, check=True, capture_output=True, text=True)
    with (OUT / "us_universe_census_v2_38c.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 9200
    assert sum(r["eligibility_status"] == "ELIGIBLE" for r in rows) == 5011
    assert {r["normalized_exchange_group"] for r in rows} >= {"NASDAQ", "NYSE", "NYSE American", "Cboe BZX"}
    counts = Counter(r["readiness_status"] for r in rows)
    assert counts["US_TICKER_EXCHANGE_READY"] == 5010
    assert counts["US_SOURCE_REQUIRED"] == 1
    assert counts["NOT_ELIGIBLE"] == 4189
    summary = json.loads((OUT / "us_coverage_summary_v2_38c.json").read_text(encoding="utf-8"))
    assert summary["guardrails"]["recommendations_generated"] is False
    print("PASS: v2.38C/US-census/5011/sec-route/no-scoring/no-ranking/no-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
