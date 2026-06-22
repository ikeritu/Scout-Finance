
from __future__ import annotations

import py_compile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
BACKUP_PATH = ROOT / "app_before_phase7d_dashboard_revalidated_funnel.py"


def main() -> int:
    print("Scout Finance — Phase 7D dashboard rollback")
    print("=" * 72)

    if not BACKUP_PATH.exists():
        print(f"FAIL Missing backup: {BACKUP_PATH}")
        return 1

    shutil.copy2(BACKUP_PATH, APP_PATH)
    py_compile.compile(str(APP_PATH), doraise=True)

    print(f"OK   Restored: {APP_PATH}")
    print("OK   app.py compiles after rollback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
