#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "tests/qa_global_research_ranking_v2_38bv.py",
    "tests/qa_ui_global_ranking_v2_38bv.py",
    "tests/qa_phase9c_closure_audit_full_suite_v2_38bx.py",
    "tests/qa_phase9c_ranking_ux_hardening_full_suite_v2_38by.py",
    "tests/qa_product_readiness_gate_full_suite_v2_38bz.py",
    "tests/qa_release_candidate_local_full_suite_v2_38ca.py",
    "tests/qa_local_startup_validation_v2_38cb.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38CB/full-suite/local-startup-validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
