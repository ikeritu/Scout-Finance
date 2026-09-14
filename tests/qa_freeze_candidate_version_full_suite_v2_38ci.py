#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "tests/qa_release_candidate_audit_full_suite_v2_38ch.py",
    "scripts/build_freeze_candidate_version_v2_38ci.py",
    "tests/qa_freeze_candidate_version_v2_38ci.py",
]


def main() -> int:
    for step in STEPS:
        result = subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {step}")
            return result.returncode
    print("PASS: v2.38CI/full-suite/freeze-candidate-version")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
