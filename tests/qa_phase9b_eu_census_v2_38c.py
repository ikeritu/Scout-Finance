#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38c_us_eu_priority_coverage"


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_us_eu_priority_coverage_v2_38c.py")], cwd=ROOT, check=True, capture_output=True, text=True)
    with (OUT / "eu_universe_census_v2_38c.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 22578
    assert sum(r["eligibility_status"] == "ELIGIBLE" for r in rows) == 10483
    counts = Counter(r["home_exchange_status"] for r in rows)
    assert counts["EU_HOME_EXCHANGE_AMBIGUOUS"] + counts["EU_ISIN_MISSING"] == 10483
    assert counts["NOT_ELIGIBLE"] == 12095
    assert sum(r["exchange"] == "CBOE_EUROPE" for r in rows) == 21154
    assert sum(r["exchange"] == "XETR" for r in rows) == 1424
    print("PASS: v2.38C/EU-census/Cboe-secondary/home-exchange-required/no-naive-primary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
