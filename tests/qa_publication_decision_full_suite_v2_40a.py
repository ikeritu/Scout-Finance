#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "tests/qa_real_post_release_local_smoke_test_v2_39f.py",
    "scripts/build_publication_decision_v2_40a.py",
    "tests/qa_publication_decision_v2_40a.py",
]


def main() -> int:
    for step in STEPS:
        result = subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {step}")
            return result.returncode
    print("PASS: v2.40A/full-suite/publication-decision")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
