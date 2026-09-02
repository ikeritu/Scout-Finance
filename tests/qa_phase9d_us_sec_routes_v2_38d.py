#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation"


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_us_sec_foundation_v2_38d.py")], cwd=ROOT, check=True, capture_output=True, text=True)
    with (OUT / "us_sec_provider_route_matrix_v2_38d.csv").open(encoding="utf-8", newline="") as f:
        routes = list(csv.DictReader(f))
    assert {r["route"] for r in routes} == {"identity", "filings", "fundamentals", "prices"}
    assert any(r["route"] == "identity" and "SEC company_tickers" in r["source"] for r in routes)
    assert any(r["route"] == "fundamentals" and "companyfacts" in r["source"] for r in routes)
    assert any(r["route"] == "prices" and r["status"] == "USER_ACTION_REQUIRED" for r in routes)
    summary = json.loads((OUT / "us_sec_coverage_summary_v2_38d.json").read_text(encoding="utf-8"))
    assert summary["us_rows"] == 9200 and summary["us_eligible_rows"] == 5011
    assert summary["guardrails"]["scoring_calculated"] is False
    assert summary["guardrails"]["ranking_calculated"] is False
    assert summary["guardrails"]["recommendations_generated"] is False
    print("PASS: v2.38D/US-SEC-routes/sec-companyfacts/submissions/adjusted-price-pending/no-scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
