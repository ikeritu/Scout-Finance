
"""
Scout Finance — Phase 7A.5.1 dashboard hotfix.

Purpose:
- Recover app.py if Phase 7A.5 left an unterminated string.
- Restore from app_before_phase7a5.py when app.py does not compile.
- Apply the institutional universe dashboard with safe Python strings.
- Validate app.py.

Run from project root:

    ./.venv/Scripts/python.exe scripts/hotfix_phase7a5_dashboard.py
"""

from __future__ import annotations

import ast
import py_compile
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"
BACKUP_PATH = PROJECT_ROOT / "app_before_phase7a5.py"
HOTFIX_BACKUP_PATH = PROJECT_ROOT / "app_before_phase7a5_1_hotfix.py"


PHASE7A5_FUNCTIONS = r