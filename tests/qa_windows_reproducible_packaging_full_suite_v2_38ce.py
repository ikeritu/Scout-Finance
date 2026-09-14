#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "tests/qa_required_outputs_diagnostics_full_suite_v2_38cd.py",
    "tests/qa_windows_reproducible_packaging_v2_38ce.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38CE/full-suite/windows-reproducible-packaging")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
