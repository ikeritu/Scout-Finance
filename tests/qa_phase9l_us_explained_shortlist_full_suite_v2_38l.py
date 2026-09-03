#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9l_us_shortlist_contract_v2_38l.py",
    "qa_phase9l_us_shortlist_builder_v2_38l.py",
    "qa_phase9l_us_shortlist_quality_v2_38l.py",
    "qa_phase9k_us_experimental_scoring_full_suite_v2_38k.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38L US explained shortlist/full-suite/offline/no-secrets/no-final-recommendations/no-financial-advice/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
