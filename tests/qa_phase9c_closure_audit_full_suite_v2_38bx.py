#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "tests/qa_phase9c_closure_audit_contract_v2_38bx.py",
    "tests/qa_phase9c_closure_audit_builder_v2_38bx.py",
    "tests/qa_phase9c_closure_audit_quality_v2_38bx.py",
    "tests/qa_global_research_ranking_v2_38bv.py",
    "tests/qa_ui_global_ranking_v2_38bv.py",
]


def main() -> int:
    for test in TESTS:
        result = subprocess.run([sys.executable, str(ROOT / test)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {test}")
            return result.returncode
    print("PASS: v2.38BX Phase 9C closure audit/full-suite/read-only/no-network/no-methodology-change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
