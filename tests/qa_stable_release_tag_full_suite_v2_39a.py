#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "tests/qa_final_operational_publication_full_suite_v2_38cj.py",
    "scripts/build_stable_release_tag_v2_39a.py",
    "tests/qa_stable_release_tag_v2_39a.py",
]


def main() -> int:
    for step in STEPS:
        result = subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {step}")
            return result.returncode
    print("PASS: v2.39A/full-suite/stable-release-tag")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
