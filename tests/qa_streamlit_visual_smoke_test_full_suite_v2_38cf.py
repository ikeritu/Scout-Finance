#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "tests/qa_windows_reproducible_packaging_full_suite_v2_38ce.py",
    "tests/qa_streamlit_visual_smoke_test_v2_38cf.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38CF/full-suite/streamlit-visual-smoke-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
