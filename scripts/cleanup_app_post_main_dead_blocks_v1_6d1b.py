from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

START_MARKERS = [
    "# >>> PHASE 7D REVALIDATED FUNNEL DASHBOARD HELPERS",
    "# PHASE 7D.1 DASHBOARD HOTFIX SUPERSEDED BY v1.2A",
    "# >>> v1.4E2 MARKET DATA PROVIDER FALLBACK HELPERS",
    "# >>> v1.5C REAL UNIVERSE SCALE TEST PANEL",
]

END_MARKERS = [
    "# <<< PHASE 7D REVALIDATED FUNNEL DASHBOARD HELPERS",
    "# <<< v1.4E2 MARKET DATA PROVIDER FALLBACK HELPERS",
    "# <<< v1.5C REAL UNIVERSE SCALE TEST PANEL",
]


def remove_block(lines: list[str], start_marker: str, end_marker: str | None) -> tuple[list[str], bool]:
    start_idx = None
    for i, line in enumerate(lines):
        if start_marker in line:
            start_idx = i
            break

    if start_idx is None:
        return lines, False

    if end_marker is None:
        end_idx = start_idx
        while end_idx < len(lines):
            # Stop before the next explicit version block.
            if end_idx > start_idx and lines[end_idx].startswith("# >>> "):
                break
            end_idx += 1
        return lines[:start_idx] + lines[end_idx:], True

    end_idx = None
    for i in range(start_idx, len(lines)):
        if end_marker in lines[i]:
            end_idx = i + 1
            break

    if end_idx is None:
        raise RuntimeError(f"End marker not found for block: {start_marker}")

    return lines[:start_idx] + lines[end_idx:], True


def main() -> int:
    text = APP.read_text(encoding="utf-8")
    lines = text.splitlines()

    removed = []

    block_pairs = [
        (
            "# >>> PHASE 7D REVALIDATED FUNNEL DASHBOARD HELPERS",
            "# <<< PHASE 7D REVALIDATED FUNNEL DASHBOARD HELPERS",
        ),
        (
            "# PHASE 7D.1 DASHBOARD HOTFIX SUPERSEDED BY v1.2A",
            None,
        ),
        (
            "# >>> v1.4E2 MARKET DATA PROVIDER FALLBACK HELPERS",
            "# <<< v1.4E2 MARKET DATA PROVIDER FALLBACK HELPERS",
        ),
        (
            "# >>> v1.5C REAL UNIVERSE SCALE TEST PANEL",
            "# <<< v1.5C REAL UNIVERSE SCALE TEST PANEL",
        ),
    ]

    for start, end in block_pairs:
        lines, did_remove = remove_block(lines, start, end)
        if did_remove:
            removed.append(start)

    new_text = "\n".join(lines).rstrip() + "\n"

    # Add phase marker once.
    marker = "# v1.6D1B post-main dead blocks cleanup packaged"
    if marker not in new_text:
        new_text = marker + "\n" + new_text

    APP.write_text(new_text, encoding="utf-8")

    print("Scout Finance — v1.6D1B Remove Post-Main Dead Blocks")
    print("=" * 92)
    print(f"OK   app.py updated: {APP}")
    print(f"OK   Blocks removed: {len(removed)}")
    for item in removed:
        print(f"OK   Removed: {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
