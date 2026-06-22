
"""
Scout Finance — Phase 6F dashboard fundamental coverage checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase6f_dashboard.py
"""

from __future__ import annotations

import ast
import py_compile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 6F dashboard checker")
    print("=" * 56)

    if not APP_PATH.exists():
        fail("app.py no existe.")
        return 1

    try:
        py_compile.compile(str(APP_PATH), doraise=True)
        ok("app.py compila correctamente")
    except Exception as exc:
        fail(f"app.py no compila: {exc}")
        return 1

    content = APP_PATH.read_text(encoding="utf-8", errors="replace")
    ast.parse(content)

    required_markers = [
        "_render_fundamental_enrichment_dashboard",
        "_sf6f_build_fundamental_enrichment_summary",
        "🧬 Cobertura de fundamentales",
        "Fundamentals matched",
        "clean_enriched_flow",
        "stage1_passed_enriched.csv",
        "stage1_passed.csv` no fue sobrescrito",
    ]

    missing = [marker for marker in required_markers if marker not in content]

    if missing:
        fail("Faltan markers de Fase 6F:")
        for marker in missing:
            print(f"   - {marker}")
        return 1

    ok("Markers de Fase 6F presentes")
    ok("Dashboard preparado para cobertura fundamental")
    ok("Fase 6F app validada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
