
"""
Scout Finance — Phase 7A.5.3 UI text polish checker.

Run:
    ./.venv/Scripts/python.exe scripts/check_phase7a5_3_ui_text_polish.py
"""

from __future__ import annotations

import ast
import py_compile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"


REQUIRED_TEXTS = [
    "Tasa excluida",
    "Éxito market data",
    "Tasa de paso Stage 1",
    "Tasa de rechazo Stage 1",
    "Nº",
    "antes del filtrado financiero",
]


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7A.5.3 UI text polish checker")
    print("=" * 66)

    if not APP_PATH.exists():
        fail(f"app.py not found: {APP_PATH}")
        return 1

    try:
        py_compile.compile(str(APP_PATH), doraise=True)
        ast.parse(APP_PATH.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        fail(f"app.py does not compile/parse: {exc}")
        return 1

    ok("app.py compiles and parses")

    content = APP_PATH.read_text(encoding="utf-8", errors="replace")

    missing = [text for text in REQUIRED_TEXTS if text not in content]
    if missing:
        fail("Missing polished UI texts:")
        for text in missing:
            print(f"   - {text}")
        return 1

    ok("Required polished UI texts present")

    print()
    print("Result")
    print("-" * 66)
    ok("Phase 7A.5.3 UI text polish is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
