#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "tests/qa_user_guide_dummy_friendly_full_suite_v2_38cc.py",
    "tests/qa_required_outputs_diagnostics_v2_38cd.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38CD/full-suite/required-outputs-diagnostics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
