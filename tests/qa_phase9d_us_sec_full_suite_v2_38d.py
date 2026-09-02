#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9d_us_sec_identity_v2_38d.py",
    "qa_phase9d_us_sec_routes_v2_38d.py",
    "qa_phase9d_us_sec_pilot_v2_38d.py",
    "qa_phase9b_us_eu_full_suite_v2_38c.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38D US SEC foundation/full-suite/offline/no-secrets/no-scoring/no-ranking/no-recommendations/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
