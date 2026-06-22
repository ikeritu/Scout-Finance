
from __future__ import annotations

import py_compile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILTER_PATH = ROOT / "src" / "filter_stage2.py"
BACKUP_PATH = ROOT / "src" / "filter_stage2_before_phase7c3_yfinance_policy.py"


def main() -> int:
    print("Scout Finance — Phase 7C.3 rollback")
    print("=" * 72)

    if not BACKUP_PATH.exists():
        print(f"FAIL Missing backup: {BACKUP_PATH}")
        return 1

    shutil.copy2(BACKUP_PATH, FILTER_PATH)
    py_compile.compile(str(FILTER_PATH), doraise=True)

    print(f"OK   Restored: {FILTER_PATH}")
    print("OK   filter_stage2.py compiles after rollback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
