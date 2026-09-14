#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "tests/qa_limitations_backlog_product_risk_register_full_suite_v2_38cg.py",
    "tests/qa_release_candidate_audit_v2_38ch.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38CH/full-suite/release-candidate-audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
