
"""
Scout Finance — Phase 7A.5.3 UI text polish.

Purpose:
- Polish institutional dashboard labels in app.py.
- No data changes.
- No OpenAI/API/yfinance calls.
- No releases/v0.6 modification.

Run:
    ./.venv/Scripts/python.exe scripts/apply_phase7a5_3_ui_text_polish.py
"""

from __future__ import annotations

import ast
import py_compile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"
BACKUP_PATH = PROJECT_ROOT / "app_before_phase7a5_3_ui_text_polish.py"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def _validate_app() -> tuple[bool, str]:
    try:
        py_compile.compile(str(APP_PATH), doraise=True)
        ast.parse(APP_PATH.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _replace_all(content: str) -> tuple[str, int]:
    replacements = [
        ("Excluded rate", "Tasa excluida"),
        ("Market data success", "Éxito market data"),
        ("Stage 1 pass rate", "Tasa de paso Stage 1"),
        ("Stage 1 rejection rate", "Tasa de rechazo Stage 1"),
        ('"Count": value', '"Nº": value'),
        ("preferred, deuda, fondos,", "preferreds, deuda, fondos,"),
        ("ETNs y SPACs quedan fuera del universo inicial antes de Stage 1.", "ETNs y SPACs quedan fuera del universo inicial antes del filtrado financiero."),
    ]

    changed = 0

    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changed += 1
            ok(f"Replaced: {old} -> {new}")
        elif new in content:
            ok(f"Already polished: {new}")
        else:
            print(f"WARN Pattern not found: {old}")

    return content, changed


def main() -> int:
    print("Scout Finance — Phase 7A.5.3 UI text polish")
    print("=" * 64)

    if not APP_PATH.exists():
        fail(f"app.py not found: {APP_PATH}")
        return 1

    valid, error = _validate_app()
    if not valid:
        fail(f"app.py does not compile before patch: {error}")
        return 1

    ok("app.py compiles before patch")

    content = APP_PATH.read_text(encoding="utf-8", errors="replace")

    if "_render_institutional_universe_dashboard" not in content:
        fail("Phase 7A.5 dashboard function not found in app.py")
        return 1

    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_text(content, encoding="utf-8")
        ok(f"Backup created: {BACKUP_PATH}")
    else:
        ok(f"Backup already exists: {BACKUP_PATH}")

    content, changed = _replace_all(content)
    APP_PATH.write_text(content, encoding="utf-8")

    valid, error = _validate_app()
    if not valid:
        fail(f"app.py does not compile after patch: {error}")
        print(f"Restore manually if needed: Copy-Item '{BACKUP_PATH}' '{APP_PATH}' -Force")
        return 1

    ok("app.py compiles after patch")
    ok(f"UI polish replacements applied: {changed}")
    ok("No OpenAI/API/yfinance call performed")
    ok("releases/v0.6 not modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
