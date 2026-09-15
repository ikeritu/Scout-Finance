#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "tests/qa_final_reproducible_package_release_assets_v2_39e.py",
    "scripts/build_real_post_release_local_smoke_test_v2_39f.py",
    "tests/qa_real_post_release_local_smoke_test_v2_39f.py",
]


def main() -> int:
    for step in STEPS:
        result = subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {step}")
            return result.returncode
    print("PASS: v2.39F/full-suite/real-post-release-local-smoke-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
