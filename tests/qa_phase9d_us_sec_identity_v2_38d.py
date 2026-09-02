#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation"
ALLOWED = {
    "US_SEC_CIK_RESOLVED", "US_SEC_TICKER_AMBIGUOUS", "US_SEC_EXCHANGE_MISMATCH",
    "US_SEC_CIK_MISSING", "US_SEC_ENTITY_NAME_REVIEW", "US_SEC_SOURCE_UNAVAILABLE",
    "US_SEC_NOT_ELIGIBLE", "US_SEC_MANUAL_REVIEW",
}


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_us_sec_foundation_v2_38d.py")], cwd=ROOT, check=True, capture_output=True, text=True)
    with (OUT / "us_sec_identity_overlay_v2_38d.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 9200 == len({r["asset_id"] for r in rows})
    assert {r["identity_status"] for r in rows} <= ALLOWED
    assert all(len(r["evidence_hash"]) == 64 for r in rows)
    assert all((not r["cik"]) or re.fullmatch(r"[0-9]{10}", r["cik"]) for r in rows)
    counts = Counter(r["identity_status"] for r in rows)
    assert counts["US_SEC_SOURCE_UNAVAILABLE"] == 5011
    assert counts["US_SEC_NOT_ELIGIBLE"] == 4189
    assert counts["US_SEC_CIK_RESOLVED"] == 0
    print("PASS: v2.38D/US-SEC-identity/schema/closed-statuses/fail-closed/no-invented-cik")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
