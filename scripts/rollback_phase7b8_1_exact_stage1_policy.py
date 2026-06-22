from __future__ import annotations

import py_compile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILTER_PATH = ROOT / "src" / "filter_stage1.py"
BACKUP_PATH = ROOT / "src" / "filter_stage1_before_phase7b8_1_exact.py"

def main() -> int:
    print("Scout Finance — Phase 7B.8.1 rollback")
    print("=" * 70)
    if not BACKUP_PATH.exists():
        print(f"FAIL Missing backup: {BACKUP_PATH}")
        return 1
    shutil.copy2(BACKUP_PATH, FILTER_PATH)
    py_compile.compile(str(FILTER_PATH), doraise=True)
    print(f"OK   Restored: {FILTER_PATH}")
    print("OK   filter_stage1.py compiles after rollback")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
