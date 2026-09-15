#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "tests/qa_security_sensitive_files_audit_v2_39c.py",
    "scripts/build_clean_windows_install_validation_v2_39d.py",
    "tests/qa_clean_windows_install_validation_v2_39d.py",
]


def main() -> int:
    for step in STEPS:
        result = subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT)
        if result.returncode != 0:
            print(f"FAIL: {step}")
            return result.returncode
    print("PASS: v2.39D/full-suite/clean-windows-install-validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
