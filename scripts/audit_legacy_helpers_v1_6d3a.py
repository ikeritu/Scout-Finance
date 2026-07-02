from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
OUT = ROOT / "outputs" / "audit" / "legacy_helper_usage_v1_6d3.md"
OUT.parent.mkdir(parents=True, exist_ok=True)


LEGACY_PREFIXES = [
    "_sf16c1_",
    "_sf16c2_",
    "_sf16c4_",
    "_sf16c5_",
    "_sf16c6_",
    "_sf15a_",
    "_sf15b_",
    "_sf15d_",
    "_sf15d2_",
]


def get_defs(tree: ast.AST) -> dict[str, int]:
    out: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            out[node.name] = node.lineno
    return out


def get_call_lines(tree: ast.AST) -> dict[str, list[int]]:
    calls: dict[str, list[int]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr

        if name:
            calls.setdefault(name, []).append(node.lineno)

    return calls


def main() -> int:
    text = APP.read_text(encoding="utf-8")
    tree = ast.parse(text)

    defs = get_defs(tree)
    calls = get_call_lines(tree)

    legacy = []
    for name, line in sorted(defs.items(), key=lambda x: x[1]):
        if any(name.startswith(prefix) for prefix in LEGACY_PREFIXES):
            call_lines = [x for x in calls.get(name, []) if x != line]
            legacy.append(
                {
                    "name": name,
                    "line": line,
                    "calls": call_lines,
                }
            )

    removable_candidates = [
        item for item in legacy
        if not item["calls"]
    ]

    report = []
    report.append("# Scout Finance ? v1.6D3A Legacy Helper Usage Audit")
    report.append("")
    report.append(f"- File: `{APP}`")
    report.append(f"- Legacy helpers found: {len(legacy)}")
    report.append(f"- No-call candidates: {len(removable_candidates)}")
    report.append("")
    report.append("## No-call candidates")
    report.append("")
    if removable_candidates:
        for item in removable_candidates:
            report.append(f"- Line {item['line']}: `{item['name']}()`")
    else:
        report.append("- None")
    report.append("")
    report.append("## Legacy helpers with calls")
    report.append("")
    any_called = False
    for item in legacy:
        if item["calls"]:
            any_called = True
            report.append(f"- Line {item['line']}: `{item['name']}()` called at {item['calls']}")
    if not any_called:
        report.append("- None")
    report.append("")
    report.append("## Full legacy inventory")
    report.append("")
    for item in legacy:
        report.append(f"- Line {item['line']}: `{item['name']}()` ? calls: {item['calls'] or 'none'}")

    OUT.write_text("\n".join(report), encoding="utf-8")

    print("Scout Finance ? v1.6D3A Legacy Helper Usage Audit")
    print("=" * 92)
    print(f"OK   app.py: {APP}")
    print(f"OK   Legacy helpers found: {len(legacy)}")
    print(f"OK   No-call candidates: {len(removable_candidates)}")
    print(f"OK   Report written: {OUT}")
    print("")
    print("No-call candidates:")
    for item in removable_candidates:
        print(f" - line {item['line']}: {item['name']}()")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
