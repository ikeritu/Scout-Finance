r"""
Scout Finance — Phase 4H.1 stability checker

Run from project root:

    ./.venv/Scripts/python.exe check_phase4g_stability.py

This script does not call OpenAI and does not modify files.
"""

from __future__ import annotations

import ast
import py_compile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
APP_PATH = PROJECT_ROOT / "app.py"
ANALYSES_DIR = PROJECT_ROOT / "outputs" / "analyses"

REQUIRED_FUNCTIONS = [
    "_render_dashboard_tab",
    "_render_ranking_tab",
    "_render_company_analysis_tab",
    "_render_phase3b_json_comparison",
    "_render_history_technical_tab",
    "_render_settings_tab",
]

REQUIRED_TEXT_MARKERS = [
    "Scout Finance",
    "Dashboard",
    "Ranking",
    "Análisis empresa",
    "Comparar empresas",
    "Histórico / técnico",
    "Ajustes",
    "Dashboard ejecutivo",
    "Comparativa visual",
    "Histórico de análisis por empresa",
    "Ajustes / panel técnico",
    "Fase 2",
    "outputs/analyses",
]


def print_ok(label: str) -> None:
    print(f"OK   {label}")


def print_warn(label: str) -> None:
    print(f"WARN {label}")


def print_fail(label: str) -> None:
    print(f"FAIL {label}")


def main() -> int:
    print("Scout Finance — Phase 4H.1 stability checker")
    print("=" * 48)

    if not APP_PATH.exists():
        print_fail("app.py no existe en la raíz del proyecto.")
        return 1

    print_ok("app.py encontrado")

    try:
        py_compile.compile(str(APP_PATH), doraise=True)
        print_ok("app.py compila correctamente")
    except Exception as exc:
        print_fail(f"app.py no compila: {exc}")
        return 1

    try:
        content = APP_PATH.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content)
        functions = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        }
        print_ok("AST de app.py leído correctamente")
    except Exception as exc:
        print_fail(f"No se pudo analizar app.py: {exc}")
        return 1

    missing_functions = [
        function_name
        for function_name in REQUIRED_FUNCTIONS
        if function_name not in functions
    ]

    if missing_functions:
        print_fail("Faltan funciones esperadas:")
        for function_name in missing_functions:
            print(f"   - {function_name}")
        return 1

    print_ok("Funciones principales presentes")

    missing_markers = [
        marker
        for marker in REQUIRED_TEXT_MARKERS
        if marker not in content
    ]

    if missing_markers:
        print_warn("Faltan algunos textos/markers esperados:")
        for marker in missing_markers:
            print(f"   - {marker}")
    else:
        print_ok("Markers principales de UI presentes")

    if ANALYSES_DIR.exists():
        print_ok("outputs/analyses existe")
    else:
        print_warn("outputs/analyses no existe todavía")

    json_count = len(list(ANALYSES_DIR.glob("*.json"))) if ANALYSES_DIR.exists() else 0
    md_count = len(list(ANALYSES_DIR.glob("*.md"))) if ANALYSES_DIR.exists() else 0
    html_count = len(list(ANALYSES_DIR.glob("*executive_card.html"))) if ANALYSES_DIR.exists() else 0
    png_count = len(list(ANALYSES_DIR.glob("*.png"))) if ANALYSES_DIR.exists() else 0

    print()
    print("Outputs detectados")
    print("-" * 48)
    print(f"JSON:     {json_count}")
    print(f"Markdown: {md_count}")
    print(f"HTML:     {html_count}")
    print(f"PNG:      {png_count}")

    if json_count == 0:
        print_warn("No hay JSON Fase 2. Comparativa e histórico estarán vacíos.")
    else:
        print_ok("Hay JSON Fase 2 para comparativa/histórico")

    print()
    print("Resultado")
    print("-" * 48)
    print_ok("Revisión de estabilidad completada")
    print("No se ha llamado a OpenAI ni se han modificado archivos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
