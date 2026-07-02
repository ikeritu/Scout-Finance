from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
OUT_DIR = ROOT / "outputs" / "audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_PATH = OUT_DIR / "app_dead_code_audit_v1_6d1.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def line_of(text: str, needle: str) -> int | None:
    for idx, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return idx
    return None


def get_defs(tree: ast.AST) -> dict[str, int]:
    defs: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defs[node.name] = node.lineno
    return defs


def get_called_names(tree: ast.AST) -> set[str]:
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called.add(func.id)
            elif isinstance(func, ast.Attribute):
                called.add(func.attr)
    return called


def get_top_level_calls(tree: ast.Module) -> list[tuple[int, str]]:
    calls: list[tuple[int, str]] = []

    for node in tree.body:
        # Ignore imports, constants, def/class.
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
            continue

        # Detect if __name__ == "__main__": blocks separately.
        if isinstance(node, ast.If):
            test = ast.unparse(node.test) if hasattr(ast, "unparse") else ""
            if "__name__" in test and "__main__" in test:
                continue

        # Anything else at module level is potentially risky.
        try:
            rendered = ast.unparse(node)
        except Exception:
            rendered = type(node).__name__

        first_line = rendered.splitlines()[0] if rendered else type(node).__name__
        calls.append((getattr(node, "lineno", -1), first_line[:160]))

    return calls


def find_markers(text: str) -> list[tuple[int, str]]:
    markers: list[tuple[int, str]] = []
    patterns = [
        "HELPERS",
        "hotfix",
        "HOTFIX",
        "superseded",
        "SUPERSEDED",
        "packaged",
        "v1.",
        "v0.",
    ]

    for idx, line in enumerate(text.splitlines(), start=1):
        if any(p in line for p in patterns):
            if ">>> " in line or "<<< " in line or "packaged" in line or "superseded" in line.lower() or "hotfix" in line.lower():
                markers.append((idx, line.strip()))

    return markers


def main() -> int:
    if not APP_PATH.exists():
        raise SystemExit(f"Missing app.py: {APP_PATH}")

    text = read_text(APP_PATH)
    tree = ast.parse(text)
    assert isinstance(tree, ast.Module)

    defs = get_defs(tree)
    called = get_called_names(tree)
    top_level = get_top_level_calls(tree)
    markers = find_markers(text)

    unused_candidates = []
    for name, lineno in sorted(defs.items(), key=lambda x: x[1]):
        # main is called by if __name__ block indirectly.
        if name == "main":
            continue
        # Streamlit callbacks / render helpers may be selected dynamically;
        # this is only a candidate list.
        if name not in called:
            unused_candidates.append((lineno, name))

    main_line = defs.get("main")
    post_main_defs = []
    if main_line:
        for name, lineno in sorted(defs.items(), key=lambda x: x[1]):
            if lineno > main_line and name != "main":
                post_main_defs.append((lineno, name))

    report = []
    report.append("# Scout Finance — v1.6D1A App.py Dead-Code Audit")
    report.append("")
    report.append("## Scope")
    report.append("")
    report.append(f"- File: `{APP_PATH}`")
    report.append(f"- Total lines: {len(text.splitlines())}")
    report.append(f"- Functions found: {len(defs)}")
    report.append("")
    report.append("## Important note")
    report.append("")
    report.append("This is a static audit. `unused_candidates` are not automatically safe to delete.")
    report.append("Streamlit callbacks, dynamic dispatch, and helper references can produce false positives.")
    report.append("")
    report.append("## main()")
    report.append("")
    report.append(f"- `main()` line: {main_line}")
    report.append("")
    report.append("## Top-level executable statements outside function definitions")
    report.append("")
    if top_level:
        for lineno, snippet in top_level:
            report.append(f"- Line {lineno}: `{snippet}`")
    else:
        report.append("- None detected.")
    report.append("")
    report.append("## Functions defined after main()")
    report.append("")
    if post_main_defs:
        for lineno, name in post_main_defs:
            report.append(f"- Line {lineno}: `{name}()`")
    else:
        report.append("- None detected.")
    report.append("")
    report.append("## Unused function candidates")
    report.append("")
    if unused_candidates:
        for lineno, name in unused_candidates:
            report.append(f"- Line {lineno}: `{name}()`")
    else:
        report.append("- None detected.")
    report.append("")
    report.append("## Phase / hotfix / superseded markers")
    report.append("")
    if markers:
        for lineno, marker in markers:
            report.append(f"- Line {lineno}: `{marker}`")
    else:
        report.append("- None detected.")
    report.append("")

    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")

    print("Scout Finance — v1.6D1A App.py Dead-Code Audit")
    print("=" * 92)
    print(f"OK   app.py exists: {APP_PATH}")
    print(f"OK   Functions found: {len(defs)}")
    print(f"OK   Top-level executable statements: {len(top_level)}")
    print(f"OK   Functions defined after main(): {len(post_main_defs)}")
    print(f"OK   Unused function candidates: {len(unused_candidates)}")
    print(f"OK   Markers found: {len(markers)}")
    print(f"OK   Report written: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
