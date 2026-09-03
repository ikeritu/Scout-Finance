#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9k_us_scoring_contract_v2_38k.py",
    "qa_phase9k_us_scoring_builder_v2_38k.py",
    "qa_phase9k_us_scoring_quality_v2_38k.py",
    "qa_phase9j_us_candidate_matrix_full_suite_v2_38j.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38K US experimental scoring/full-suite/offline/no-secrets/no-recommendations/no-financial-advice/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
