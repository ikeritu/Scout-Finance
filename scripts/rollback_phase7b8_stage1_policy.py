
from __future__ import annotations

import py_compile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "src" / "filter_stage1.py"
BACKUP = ROOT / "src" / "filter_stage1_before_phase7b8_balanced.py"


def main():
    print("Scout Finance — Phase 7B.8 rollback")
    print("=" * 60)

    if not BACKUP.exists():
        print(f"FAIL Missing backup: {BACKUP}")
        return 1

    shutil.copy2(BACKUP, FILTER)
    py_compile.compile(str(FILTER), doraise=True)

    print(f"OK   Restored: {FILTER}")
    print("OK   filter_stage1.py compiles after rollback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
