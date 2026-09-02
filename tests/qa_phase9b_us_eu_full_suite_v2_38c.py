#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9b_us_census_v2_38c.py",
    "qa_phase9b_eu_census_v2_38c.py",
    "qa_phase9b_provider_routes_v2_38c.py",
    "qa_phase9b_full_suite_v2_38b.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38C US/EU priority coverage/full-suite/offline/no-scoring/no-ranking/no-recommendations/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
