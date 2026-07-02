from __future__ import annotations

import ast
from pathlib import Path


APP = Path("app.py")

FUNCTIONS_TO_REMOVE = {
    "_sf16c1_active_score",
    "_sf16c1_active_reason",
    "_sf16c1_display_score",
    "_sf16c1_human_category",
    "_sf16c1_human_status",
    "_sf16c2_display_score",
    "_sf16c4_active_reason",
    "_sf16c4_active_source_label",
    "_sf16c4_is_combined_active",
    "_sf16c5_source_card_label",
    "_sf16c5_render_dashboard_combined_notice",
}


def function_ranges(source: str) -> list[tuple[int, int, str]]:
    tree = ast.parse(source)
    lines = source.splitlines()

    funcs: list[tuple[int, int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue

        if node.name not in FUNCTIONS_TO_REMOVE:
            continue

        start = node.lineno

        # Prefer native end_lineno when available.
        end = getattr(node, "end_lineno", None)
        if end is None:
            end = start
            for idx in range(start, len(lines)):
                line = lines[idx]
                if idx + 1 > start and (line.startswith("def ") or line.startswith("# >>> ") or line.startswith("# <<< ")):
                    end = idx
                    break
            else:
                end = len(lines)

        # Include contiguous blank lines after function to avoid leaving gaps.
        while end < len(lines) and lines[end].strip() == "":
            end += 1

        funcs.append((start, end, node.name))

    return sorted(funcs, key=lambda item: item[0], reverse=True)


def main() -> int:
    source = APP.read_text(encoding="utf-8")
    lines = source.splitlines()

    ranges = function_ranges(source)
    found = {name for _, _, name in ranges}
    missing = sorted(FUNCTIONS_TO_REMOVE - found)

    for start, end, name in ranges:
        del lines[start - 1:end]

    new_source = "\n".join(lines).rstrip() + "\n"

    marker = "# v1.6D3B remove superseded v1.6C legacy helpers packaged"
    if marker not in new_source:
        new_source = marker + "\n" + new_source

    APP.write_text(new_source, encoding="utf-8")

    print("Scout Finance ? v1.6D3B Remove Superseded v1.6C Legacy Helpers")
    print("=" * 92)
    print(f"OK   app.py updated: {APP}")
    print(f"OK   Functions removed: {len(ranges)}")
    for start, end, name in sorted(ranges, key=lambda item: item[0]):
        print(f"OK   Removed {name}() lines {start}-{end}")

    if missing:
        print("")
        print("WARN Missing expected functions:")
        for name in missing:
            print(f" - {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
