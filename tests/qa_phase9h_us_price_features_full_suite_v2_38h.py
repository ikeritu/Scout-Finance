#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9h_us_price_features_contract_v2_38h.py",
    "qa_phase9h_us_price_features_builder_v2_38h.py",
    "qa_phase9h_us_price_features_quality_v2_38h.py",
    "qa_phase9g_us_sec_full_suite_v2_38g.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38H US price features/full-suite/offline/no-secrets/no-scoring/no-ranking/no-recommendations/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
