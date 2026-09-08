"""Read-only, fail-closed access to the full 43,089-company global coverage
matrix (v2.38AL), plus a rebuild trigger for the "Actualizar" button.

Deliberately kept entirely separate from repository.py's fixed, contract-
guarded 50-asset canonical product dataset -- this is a second, independent
lens onto local research state (identity/fundamentals/growth/price status
per company, never a score or a ranking), not a replacement or an input to
the ranking pipeline.

rebuild_global_matrix() re-runs only the four pure, offline, network-free
builders that already exist (v2.38AL, v2.38AM, v2.38BO, v2.38BT) -- all
four read whatever real source data has already been collected by the
many separate, deliberately manual CLI phases of this project and
reassemble it. None of them ever fetches anything new from any external
source itself; that stays a distinct, deliberate, per-source decision
outside this button's scope. v2.38BT does not actually depend on v2.38AL/
AM/BO's own output (it reads the raw growth-feature files directly), but
runs last in this same sequence purely for one simple "Actualizar" button
UX -- if an earlier step fails, this one is conservatively skipped too,
even though it could technically still run on its own.

load_global_matrix() also joins in v2.38BO's scoring-eligibility tier per
company (a classification, never a score) when that file exists -- if it
doesn't yet, every row's eligibility fields are simply blank, same
fail-open-to-blank convention used everywhere else in this module.

v2.38BT's "unicornio" flag (a real, pre-existing multi-signal growth
combination, never a weighted score) is joined in the same way -- when a
company has no growth-feature row anywhere, its unicorn fields are simply
blank, never a computed "false".
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
ELIGIBILITY_REL = "outputs/full_universe_source_acquisition/v2_38bo_global_scoring_eligibility/global_scoring_eligibility_v2_38bo.csv"
UNICORN_REL = "outputs/full_universe_source_acquisition/v2_38bt_global_unicorn_flag/global_unicorn_flag_v2_38bt.csv"
COVERAGE_SCRIPT_REL = "scripts/build_global_coverage_matrix_v2_38al.py"
MACRO_SCRIPT_REL = "scripts/build_global_macro_geopolitical_context_v2_38am.py"
ELIGIBILITY_SCRIPT_REL = "scripts/build_global_scoring_eligibility_v2_38bo.py"
UNICORN_SCRIPT_REL = "scripts/build_global_unicorn_flag_v2_38bt.py"
REBUILD_TIMEOUT_SECONDS = 600
ELIGIBILITY_FIELDS_DEFAULT = {"eligibility_tier": "", "eligibility_reason": "", "is_financial_institution_heuristic": ""}
UNICORN_FIELDS_DEFAULT = {"unicorn_status": "", "unicorn_reason": ""}


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


def _load_eligibility_index(root: Path) -> dict[str, dict]:
    path = _rooted(root, ELIGIBILITY_REL)
    if not path.is_file():
        return {}
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return {row["asset_id"]: row for row in csv.DictReader(handle)}
    except Exception:  # noqa: BLE001
        return {}


def _load_unicorn_index(root: Path) -> dict[str, dict]:
    path = _rooted(root, UNICORN_REL)
    if not path.is_file():
        return {}
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return {row["asset_id"]: row for row in csv.DictReader(handle)}
    except Exception:  # noqa: BLE001
        return {}


def load_global_matrix(root: Path) -> GlobalMatrixData:
    path = _rooted(root, MATRIX_REL)
    if not path.is_file():
        return GlobalMatrixData(False, (), "", "La matriz de cobertura todavía no se ha construido nunca en este equipo -- pulsa Actualizar.")
    try:
        with lzma.open(path, "rt", encoding="utf-8", newline="") as handle:
            rows = tuple(csv.DictReader(handle))
    except Exception as exc:  # noqa: BLE001
        return GlobalMatrixData(False, (), "", f"No se pudo leer la matriz existente: {exc}")
    eligibility_index = _load_eligibility_index(root)
    unicorn_index = _load_unicorn_index(root)
    merged_rows = tuple({
        **row,
        "eligibility_tier": eligibility_index.get(row["asset_id"], ELIGIBILITY_FIELDS_DEFAULT).get("eligibility_tier", ""),
        "eligibility_reason": eligibility_index.get(row["asset_id"], ELIGIBILITY_FIELDS_DEFAULT).get("eligibility_reason", ""),
        "is_financial_institution_heuristic": eligibility_index.get(row["asset_id"], ELIGIBILITY_FIELDS_DEFAULT).get("is_financial_institution_heuristic", ""),
        "unicorn_status": unicorn_index.get(row["asset_id"], UNICORN_FIELDS_DEFAULT).get("unicorn_status", ""),
        "unicorn_reason": unicorn_index.get(row["asset_id"], UNICORN_FIELDS_DEFAULT).get("unicorn_reason", ""),
    } for row in rows)
    generated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    return GlobalMatrixData(True, merged_rows, generated_at)


def rebuild_global_matrix(root: Path, run: Callable = subprocess.run) -> RebuildResult:
    """Re-run the coverage matrix builder, then the macro context builder,
    then the scoring-eligibility builder, then the unicorn-flag builder,
    each on top of the one before it. Uses the same Python interpreter
    this app is already running under (sys.executable), so it works
    identically whether the app was launched from a venv or a system
    install. `run` is injectable purely for offline testing -- production
    callers never pass it."""
    steps: list[RebuildStep] = []
    ok = True
    for label, script_rel in (
        ("Matriz de cobertura (v2.38AL)", COVERAGE_SCRIPT_REL),
        ("Contexto geopolítico (v2.38AM)", MACRO_SCRIPT_REL),
        ("Elegibilidad para scoring (v2.38BO)", ELIGIBILITY_SCRIPT_REL),
        ("Icono unicornio (v2.38BT)", UNICORN_SCRIPT_REL),
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
                break  # never run a later step on top of one that failed -- each depends on the one(s) before it
        except Exception as exc:  # noqa: BLE001
            steps.append(RebuildStep(label, False, time.monotonic() - start, str(exc)))
            ok = False
            break
    return RebuildResult(ok, tuple(steps))
