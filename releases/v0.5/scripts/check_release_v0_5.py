"""
Scout Finance — Phase 5J release v0.5 checker.

Run from project root:

    ./.venv/Scripts/python.exe scripts/check_release_v0_5.py

This checker does not call OpenAI and does not modify app.py.
"""

from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = PROJECT_ROOT / "releases" / "v0.5"
MANIFEST_PATH = RELEASE_DIR / "RELEASE_MANIFEST_v0_5.json"


REQUIRED_RELEASE_FILES = [
    "app.py",
    "app_v0_5_stable.py",
    "README.md",
    "CHANGELOG.md",
    "VERSION.md",
    "requirements.txt",
    "VERSION_RELEASE_v0_5.md",
    "RELEASE_MANIFEST_v0_5.json",
]


REQUIRED_RELEASE_DIRS = [
    "src",
    "scripts",
]


REQUIRED_APP_MARKERS = [
    "🧭 Candidatos Stage 3",
    "🧭 Embudo global de scouting",
    "_render_stage3_candidates_tab",
    "_render_global_funnel_summary_dashboard",
]


REQUIRED_SRC_FILES = [
    "src/run_global_funnel_demo.py",
    "src/filter_stage1.py",
    "src/filter_stage2.py",
    "src/filter_stage3.py",
    "src/scouting_candidates.py",
]


REQUIRED_SCRIPT_FILES = [
    "scripts/check_phase5f_candidates.py",
    "scripts/check_phase5g1_app.py",
    "scripts/check_phase5h_app.py",
    "scripts/check_phase5i_global_funnel_runner.py",
]


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 5J release v0.5 checker")
    print("=" * 62)

    if not RELEASE_DIR.exists():
        fail(f"Release directory missing: {RELEASE_DIR}")
        return 1

    ok(f"Release directory exists: {RELEASE_DIR}")

    for relative_path in REQUIRED_RELEASE_FILES:
        path = RELEASE_DIR / relative_path
        if not path.exists():
            fail(f"Missing release file: {relative_path}")
            return 1
        ok(f"Release file exists: {relative_path}")

    for relative_path in REQUIRED_RELEASE_DIRS:
        path = RELEASE_DIR / relative_path
        if not path.exists() or not path.is_dir():
            fail(f"Missing release directory: {relative_path}")
            return 1
        ok(f"Release directory exists: {relative_path}")

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read manifest: {exc}")
        return 1

    if manifest.get("release") != "v0.5":
        fail("Manifest release is not v0.5")
        return 1

    ok("Manifest release is v0.5")

    if manifest.get("openai_called") is False:
        ok("Manifest confirms OpenAI was not called")
    else:
        fail("Manifest indicates OpenAI was called")
        return 1

    app_path = RELEASE_DIR / "app.py"

    try:
        py_compile.compile(str(app_path), doraise=True)
        ok("Release app.py compiles")
    except Exception as exc:
        fail(f"Release app.py does not compile: {exc}")
        return 1

    content = app_path.read_text(encoding="utf-8", errors="replace")
    ast.parse(content)

    missing_markers = [marker for marker in REQUIRED_APP_MARKERS if marker not in content]
    if missing_markers:
        fail("Missing app markers in release:")
        for marker in missing_markers:
            print(f"   - {marker}")
        return 1

    ok("Release app contains Phase 5G/5H markers")

    for relative_path in REQUIRED_SRC_FILES:
        path = RELEASE_DIR / relative_path
        if not path.exists():
            fail(f"Missing required src file in release: {relative_path}")
            return 1
        ok(f"Required src file exists: {relative_path}")

    for relative_path in REQUIRED_SCRIPT_FILES:
        path = RELEASE_DIR / relative_path
        if not path.exists():
            warn(f"Recommended checker missing in release: {relative_path}")
        else:
            ok(f"Checker exists: {relative_path}")

    print()
    print("Result")
    print("-" * 62)
    ok("Release v0.5 is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
