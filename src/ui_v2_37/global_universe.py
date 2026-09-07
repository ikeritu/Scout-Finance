"""Read-only, fail-closed access to the full 43,089-company global coverage
matrix (v2.38AL), plus a rebuild trigger for the "Actualizar" button.

Deliberately kept entirely separate from repository.py's fixed, contract-
guarded 50-asset canonical product dataset -- this is a second, independent
lens onto local research state (identity/fundamentals/growth/price status
per company, never a score or a ranking), not a replacement or an input to
the ranking pipeline.

rebuild_global_matrix() re-runs only the two pure, offline, network-free
builders that already exist (v2.38AL, v2.38AM) -- both read whatever real
source data has already been collected by the many separate, deliberately
manual CLI phases of this project and reassemble it. It never fetches
anything new from any external source itself; that stays a distinct,
deliberate, per-source decision outside this button's scope.
"""
from __future__ import annotations

import csv
import lzma
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

MATRIX_REL = "outputs/full_universe_source_acquisition/v2_38al_global_coverage_matrix/global_coverage_matrix_v2_38al.csv.xz"
COVERAGE_SCRIPT_REL = "scripts/build_global_coverage_matrix_v2_38al.py"
MACRO_SCRIPT_REL = "scripts/build_global_macro_geopolitical_context_v2_38am.py"
REBUILD_TIMEOUT_SECONDS = 600


@dataclass(frozen=True)
class GlobalMatrixData:
    available: bool
    rows: tuple[dict, ...]
    generated_at: str
    error: str = ""


@dataclass(frozen=True)
class RebuildStep:
    label: str
    ok: bool
    seconds: float
    detail: str = ""


@dataclass(frozen=True)
class RebuildResult:
    ok: bool
    steps: tuple[RebuildStep, ...]


def _rooted(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes repository root") from exc
    return candidate


def load_global_matrix(root: Path) -> GlobalMatrixData:
    path = _rooted(root, MATRIX_REL)
    if not path.is_file():
        return GlobalMatrixData(False, (), "", "La matriz de cobertura todavía no se ha construido nunca en este equipo -- pulsa Actualizar.")
    try:
        with lzma.open(path, "rt", encoding="utf-8", newline="") as handle:
            rows = tuple(csv.DictReader(handle))
    except Exception as exc:  # noqa: BLE001
        return GlobalMatrixData(False, (), "", f"No se pudo leer la matriz existente: {exc}")
    generated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    return GlobalMatrixData(True, rows, generated_at)


def rebuild_global_matrix(root: Path, run: Callable = subprocess.run) -> RebuildResult:
    """Re-run the coverage matrix builder, then the macro context builder
    on top of it. Uses the same Python interpreter this app is already
    running under (sys.executable), so it works identically whether the
    app was launched from a venv or a system install. `run` is injectable
    purely for offline testing -- production callers never pass it."""
    steps: list[RebuildStep] = []
    ok = True
    for label, script_rel in (
        ("Matriz de cobertura (v2.38AL)", COVERAGE_SCRIPT_REL),
        ("Contexto geopolítico (v2.38AM)", MACRO_SCRIPT_REL),
    ):
        script_path = _rooted(root, script_rel)
        start = time.monotonic()
        try:
            result = run([sys.executable, str(script_path)], cwd=str(root), capture_output=True, text=True, timeout=REBUILD_TIMEOUT_SECONDS)
            elapsed = time.monotonic() - start
            step_ok = result.returncode == 0
            detail = (result.stdout or result.stderr or "").strip()
            steps.append(RebuildStep(label, step_ok, elapsed, detail[-800:]))
            ok = ok and step_ok
            if not step_ok:
                break  # never build macro context on top of a coverage matrix that failed to regenerate
        except Exception as exc:  # noqa: BLE001
            steps.append(RebuildStep(label, False, time.monotonic() - start, str(exc)))
            ok = False
            break
    return RebuildResult(ok, tuple(steps))
