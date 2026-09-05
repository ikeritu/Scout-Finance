#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9t_europe_manual_review_pack_contract_v2_38t.py",
    "qa_phase9t_europe_manual_review_pack_builder_v2_38t.py",
    "qa_phase9t_europe_manual_review_pack_quality_v2_38t.py",
    "qa_phase9s_europe_official_filings_review_full_suite_v2_38s.py",
]


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_europe_fundamentals_routes_v2_38q.py")], cwd=ROOT, check=True)
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38T Europe manual-review-pack/full-suite/offline/no-network/no-scraping/no-api/identity-not-invented/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
