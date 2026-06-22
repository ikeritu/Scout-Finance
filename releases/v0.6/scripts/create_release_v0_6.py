
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = PROJECT_ROOT / "releases" / "v0.6"
MANIFEST_PATH = RELEASE_DIR / "RELEASE_MANIFEST_v0_6.json"

FILES_TO_COPY = [
    "app.py", "config.py", "README.md", "CHANGELOG.md", "VERSION.md",
    "requirements.txt", ".env.example", ".gitignore",
]

DIRECTORIES_TO_COPY = ["src", "scripts", "templates", "docs"]

REQUIRED_PHASE6_FILES = [
    "src/prepare_real_universe_csv.py",
    "src/fundamental_coverage_report.py",
    "src/prepare_fundamentals_csv.py",
    "src/run_stage2_filter_enriched.py",
    "src/run_global_funnel_demo.py",
    "scripts/check_phase6a_real_universe.py",
    "scripts/check_phase6b_fundamental_coverage.py",
    "scripts/check_phase6c_fundamentals_enrichment.py",
    "scripts/check_phase6d_stage2_enriched.py",
    "scripts/check_phase6e_clean_global_runner.py",
    "scripts/check_phase6f_dashboard.py",
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
        return {"path": relative_path, "status": "missing", "size_bytes": None, "sha256": None}
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {"path": relative_path, "status": "copied", "size_bytes": dst.stat().st_size, "sha256": _sha256(dst)}


def _copy_directory(relative_path: str) -> dict:
    src = PROJECT_ROOT / relative_path
    dst = RELEASE_DIR / relative_path
    if not src.exists() or not src.is_dir():
        return {"path": relative_path, "status": "missing", "files": 0}
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache", ".ruff_cache"))
    return {"path": relative_path, "status": "copied", "files": sum(1 for p in dst.rglob("*") if p.is_file())}


def _write_version_snapshot() -> None:
    (RELEASE_DIR / "VERSION_RELEASE_v0_6.md").write_text(
        "# Scout Finance — Release v0.6\n\n"
        f"Fecha de creación: {_utc_now_iso()}\n\n"
        "## Hito\n\n"
        "Versión estable con universo CSV, fundamentales CSV, runner limpio y Dashboard enriquecido.\n\n"
        "Incluye:\n\n"
        "- Normalizador de universo real/sample por CSV.\n"
        "- Informe de cobertura de datos fundamentales.\n"
        "- Enriquecimiento fundamental por CSV.\n"
        "- Stage 2 desde `stage1_passed_enriched.csv` sin sobrescribir Stage 1.\n"
        "- Runner global limpio Fase 6E.\n"
        "- Dashboard con cobertura de fundamentales Fase 6F.\n"
        "- Pestaña Candidatos Stage 3.\n"
        "- Resumen visual del embudo global.\n\n"
        "No es asesoramiento financiero. No se conecta a brokers.\n",
        encoding="utf-8",
    )


def create_release_v0_6() -> dict:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    copied_files = [_copy_file(path) for path in FILES_TO_COPY]
    copied_dirs = [_copy_directory(path) for path in DIRECTORIES_TO_COPY]

    app_src = PROJECT_ROOT / "app.py"
    stable_root = PROJECT_ROOT / "app_v0_6_stable.py"
    stable_release = RELEASE_DIR / "app_v0_6_stable.py"
    stable_app_status = "missing"

    if app_src.exists():
        shutil.copy2(app_src, stable_root)
        shutil.copy2(app_src, stable_release)
        stable_app_status = "copied"

    _write_version_snapshot()

    required_phase6_status = []
    for relative_path in REQUIRED_PHASE6_FILES:
        release_path = RELEASE_DIR / relative_path
        required_phase6_status.append({
            "path": relative_path,
            "exists_in_release": release_path.exists(),
            "sha256": _sha256(release_path),
        })

    manifest = {
        "release": "v0.6",
        "phase": "6G",
        "created_at": _utc_now_iso(),
        "release_dir": str(RELEASE_DIR),
        "openai_called": False,
        "api_called": False,
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
        "required_phase6_files": required_phase6_status,
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def print_release_summary(manifest: dict) -> None:
    print("Scout Finance — Phase 6G create stable release v0.6")
    print("=" * 64)
    print(f"Release: {manifest.get('release')}")
    print(f"Release dir: {manifest.get('release_dir')}")
    print(f"OpenAI called: {manifest.get('openai_called')}")
    print(f"API called: {manifest.get('api_called')}")
    print(f"Funnel executed: {manifest.get('funnel_executed')}")
    print(f"Outputs modified: {manifest.get('outputs_modified')}")
    print("\nRequired Phase 6 files")
    print("-" * 64)
    for item in manifest.get("required_phase6_files", []):
        status = "OK" if item.get("exists_in_release") else "MISSING"
        print(f"{status:8} {item.get('path')}")
    print(f"\nManifest: {MANIFEST_PATH}")


def main() -> int:
    manifest = create_release_v0_6()
    print_release_summary(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
