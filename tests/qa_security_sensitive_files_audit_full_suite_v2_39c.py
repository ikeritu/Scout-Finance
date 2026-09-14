#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "tests/qa_public_documentation_cleanup_v2_39b.py",
    "scripts/build_security_sensitive_files_audit_v2_39c.py",
    "tests/qa_security_sensitive_files_audit_v2_39c.py",
]


def main() -> int:
    for step in STEPS:
        result = subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {step}")
            return result.returncode
    print("PASS: v2.39C/full-suite/security-sensitive-files-audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
