from __future__ import annotations

import ast

from conftest import project_path


def test_app_py_compiles() -> None:
    app_path = project_path("app.py")
    source = app_path.read_text(encoding="utf-8")
    compile(source, str(app_path), "exec")


def test_app_has_current_combined_source_refactor() -> None:
    source = project_path("app.py").read_text(encoding="utf-8")

    assert "v1.6C8 data source detection refactor packaged" in source
    assert '"active_source": "combined_score_v1"' in source
    assert '"label": "Score combinado v1"' in source
    assert 'c1.metric("Fuente", status["label"])' in source
    assert 'if status["active_source"] == "combined_score_v1"' in source


def test_no_functions_defined_after_main() -> None:
    app_path = project_path("app.py")
    source = app_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    ]

    main_nodes = [node for node in functions if node.name == "main"]
    assert main_nodes, "main() not found"

    main_line = main_nodes[0].lineno

    post_main = [
        (node.lineno, node.name)
        for node in functions
        if node.lineno > main_line and node.name != "main"
    ]

    assert post_main == [], f"Functions defined after main(): {post_main}"
