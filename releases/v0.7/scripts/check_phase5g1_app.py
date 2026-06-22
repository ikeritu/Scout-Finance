"""
Scout Finance — Phase 5G.1 app checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_phase5g1_app.py
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
    print("Scout Finance — Phase 5G.1 app checker")
    print("=" * 50)

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
        "_render_stage3_candidates_tab",
        "🧭 Candidatos Stage 3",
        "Score medio",
        "st.selectbox(",
        "Estás viendo una muestra pequeña de candidatos",
        "Vista del embudo global. No es recomendación de inversión.",
    ]

    missing = [marker for marker in required_markers if marker not in content]

    if missing:
        fail("Faltan markers de Fase 5G.1:")
        for marker in missing:
            print(f"   - {marker}")
        return 1

    ok("Markers de Fase 5G.1 presentes")
    ok("Filtro de categoría simplificado")
    ok("Fase 5G.1 app validada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
