#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "qa_phase9b_contract_manifest_v2_38b.py",
    "qa_phase9b_market_plan_v2_38b.py",
    "qa_phase9b_orchestrator_v2_38b.py",
    "qa_phase9a_full_suite_v2_38a.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / "tests" / test)], cwd=ROOT)
        if result.returncode:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38B full suite/offline/global-manifest/fail-closed/no-secrets/no-scoring/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
