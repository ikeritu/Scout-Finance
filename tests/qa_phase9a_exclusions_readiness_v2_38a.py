#!/usr/bin/env python3
from __future__ import annotations

import csv
import lzma
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "outputs/full_universe_source_acquisition/v2_38a_global_universe_audit/global_universe_audited_v2_38a.csv.xz"


def main() -> int:
    with lzma.open(DATA, "rt", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    eligibility = Counter(r["eligibility_status"] for r in rows)
    assert eligibility == {"ELIGIBLE": 21165, "EXCLUDED": 10432, "REVIEW": 9710, "BLOCKED": 1782}
    assert all(r["enrichment_readiness"] == "NOT_ELIGIBLE" for r in rows if r["eligibility_status"] == "EXCLUDED")
    assert all(r["enrichment_readiness"] == "REVIEW_REQUIRED" for r in rows if r["eligibility_status"] == "REVIEW")
    assert all(r["enrichment_readiness"] == "METADATA_REPAIR_REQUIRED" for r in rows if r["eligibility_status"] == "BLOCKED")
    assert all(r["blocker_reason"] for r in rows if r["eligibility_status"] != "ELIGIBLE" or r["enrichment_readiness"] != "READY_FOR_SOURCE_PLANNING")
    assert sum(r["exchange"] == "XETR" and r["eligibility_status"] == "BLOCKED" for r in rows) == 1424
    assert sum(r["exchange"] == "SGX" and r["eligibility_status"] == "BLOCKED" for r in rows) == 358
    print("PASS: v2.38A/exclusions/10432/review/9710/blocked/1782/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
