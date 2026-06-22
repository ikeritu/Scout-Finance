"""
Scout Finance — Phase 5J create stable release v0.5.

Run from project root:

    ./.venv/Scripts/python.exe scripts/create_release_v0_5.py

Purpose:
- Freeze the current stable app/project state into releases/v0.5
- Create app_v0_5_stable.py
- Copy key source, script, documentation and config files
- Create release manifest

This script does not call OpenAI.
It does not run the funnel.
It does not modify outputs.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = PROJECT_ROOT / "releases" / "v0.5"
MANIFEST_PATH = RELEASE_DIR / "RELEASE_MANIFEST_v0_5.json"


FILES_TO_COPY = [
    "app.py",
    "config.py",
    "README.md",
    "CHANGELOG.md",
    "VERSION.md",
    "requirements.txt",
    ".env.example",
    ".gitignore",
]

DIRECTORIES_TO_COPY = [
    "src",
    "scripts",
    "templates",
    "docs",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None

    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def _copy_file(relative_path: str) -> dict:
    src = PROJECT_ROOT / relative_path
    dst = RELEASE_DIR / relative_path

    if not src.exists():
        return {
            "path": relative_path,
            "status": "missing",
            "size_bytes": None,
            "sha256": None,
        }

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    return {
        "path": relative_path,
        "status": "copied",
        "size_bytes": dst.stat().st_size,
        "sha256": _sha256(dst),
    }


def _copy_directory(relative_path: str) -> dict:
    src = PROJECT_ROOT / relative_path
    dst = RELEASE_DIR / relative_path

    if not src.exists() or not src.is_dir():
        return {
            "path": relative_path,
            "status": "missing",
            "files": 0,
        }

    if dst.exists():
        shutil.rmtree(dst)

    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        ),
    )

    file_count = sum(1 for p in dst.rglob("*") if p.is_file())

    return {
        "path": relative_path,
        "status": "copied",
        "files": file_count,
    }


def _write_version_snapshot() -> None:
    version_snapshot = RELEASE_DIR / "VERSION_RELEASE_v0_5.md"

    version_snapshot.write_text(
        "# Scout Finance — Release v0.5\n\n"
        f"Fecha de creación: {_utc_now_iso()}\n\n"
        "## Hito\n\n"
        "Versión estable con embudo global demo integrado en la app.\n\n"
        "Incluye:\n\n"
        "- Stage 0: validación de universo global.\n"
        "- Stage 1: filtro de universo invertible.\n"
        "- Stage 2: sanity check financiero.\n"
        "- Stage 3: opportunity scoring.\n"
        "- Pestaña Candidatos Stage 3.\n"
        "- Resumen visual del embudo en Dashboard.\n"
        "- Runner único demo del embudo.\n"
        "- Checkers de estabilidad.\n\n"
        "No es asesoramiento financiero. No se conecta a brokers.\n",
        encoding="utf-8",
    )


def create_release_v0_5() -> dict:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    copied_files = []
    copied_dirs = []

    for relative_path in FILES_TO_COPY:
        copied_files.append(_copy_file(relative_path))

    for relative_path in DIRECTORIES_TO_COPY:
        copied_dirs.append(_copy_directory(relative_path))

    # Stable app snapshot in root and release.
    app_src = PROJECT_ROOT / "app.py"
    stable_root = PROJECT_ROOT / "app_v0_5_stable.py"
    stable_release = RELEASE_DIR / "app_v0_5_stable.py"

    stable_app_status = "missing"

    if app_src.exists():
        shutil.copy2(app_src, stable_root)
        shutil.copy2(app_src, stable_release)
        stable_app_status = "copied"

    _write_version_snapshot()

    manifest = {
        "release": "v0.5",
        "phase": "5J",
        "created_at": _utc_now_iso(),
        "release_dir": str(RELEASE_DIR),
        "openai_called": False,
        "funnel_executed": False,
        "outputs_modified": False,
        "stable_app_snapshot": {
            "root_path": str(stable_root),
            "release_path": str(stable_release),
            "status": stable_app_status,
            "sha256": _sha256(stable_release),
        },
        "copied_files": copied_files,
        "copied_directories": copied_dirs,
        "notes": [
            "Release v0.5 freezes the current stable state before moving to real global universe data.",
            "This release should include Phase 5B-5I functionality.",
            "The script does not call OpenAI and does not run the funnel.",
        ],
    }

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return manifest


def print_release_summary(manifest: dict) -> None:
    print("Scout Finance — Phase 5J create stable release v0.5")
    print("=" * 64)
    print(f"Release: {manifest.get('release')}")
    print(f"Release dir: {manifest.get('release_dir')}")
    print(f"OpenAI called: {manifest.get('openai_called')}")
    print(f"Funnel executed: {manifest.get('funnel_executed')}")
    print(f"Outputs modified: {manifest.get('outputs_modified')}")
    print()

    print("Stable app snapshot")
    print("-" * 64)
    snapshot = manifest.get("stable_app_snapshot", {})
    print(f"Status: {snapshot.get('status')}")
    print(f"Root: {snapshot.get('root_path')}")
    print(f"Release: {snapshot.get('release_path')}")
    print()

    print("Copied files")
    print("-" * 64)
    for item in manifest.get("copied_files", []):
        print(f"{item.get('status'):8} {item.get('path')}")

    print()
    print("Copied directories")
    print("-" * 64)
    for item in manifest.get("copied_directories", []):
        print(f"{item.get('status'):8} {item.get('path')} ({item.get('files')} files)")

    print()
    print(f"Manifest: {MANIFEST_PATH}")


def main() -> int:
    manifest = create_release_v0_5()
    print_release_summary(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
