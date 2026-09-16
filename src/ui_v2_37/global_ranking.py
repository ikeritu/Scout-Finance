"""Read-only, fail-closed access to the real v2.38BV global research
ranking -- the first real score this project has ever computed, over the
eligible universe v2.38BO defines.

Deliberately its own module, separate from global_universe.py (which
explicitly documents itself as "never a score or a ranking") and from
repository.py's fixed, contract-guarded 50-asset canonical product --
this is a third, independent lens: a real experimental research
prioritization over the 43,089-company census's eligible subset, never a
replacement for either of the other two, never investment advice.

No rebuild trigger here (unlike global_universe.py's "Actualizar"
button) -- v2.38BV is a heavier, multi-input computation (Phase 9C blocks
1 and 2) that is deliberately run from the CLI, not re-triggered from
inside the app.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

RESULTS_REL = "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json"
BUILD_COMMAND = "python scripts/build_global_research_ranking_v2_38bv.py"
LIMITATIONS_DOC_REL = "docs/FINAL_COVERAGE_LIMITATIONS_v2_41d.md"


@dataclass(frozen=True)
class GlobalRankingData:
    available: bool
    rows: tuple[dict, ...]
    generated_at: str
    error: str = ""


def _rooted(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes repository root") from exc
    return candidate


def load_global_ranking(root: Path) -> GlobalRankingData:
    path = _rooted(root, RESULTS_REL)
    if not path.is_file():
        return GlobalRankingData(
            False,
            (),
            "",
            "No se encuentra el ranking global experimental. "
            f"Archivo esperado: {RESULTS_REL}. "
            "Lo genera la fase v2.38BV; si ya tienes los datos locales, regenera con: "
            f"{BUILD_COMMAND}. No requiere credenciales ni descarga externa desde esta pantalla.",
        )
    try:
        rows = tuple(json.loads(path.read_text(encoding="utf-8")))
    except Exception as exc:  # noqa: BLE001
        return GlobalRankingData(
            False,
            (),
            "",
            "El ranking global experimental existe, pero no se pudo leer como JSON valido. "
            f"Archivo afectado: {RESULTS_REL}. "
            f"Detalle tecnico: {exc}. "
            f"Regeneralo con {BUILD_COMMAND} si el repositorio contiene los inputs locales esperados.",
        )
    if not isinstance(rows, tuple) or any(not isinstance(row, dict) for row in rows):
        return GlobalRankingData(
            False,
            (),
            "",
            "El ranking global experimental no tiene la estructura esperada de lista de filas. "
            f"Archivo afectado: {RESULTS_REL}. "
            f"Regeneralo con {BUILD_COMMAND}; la app no inventa filas ni recalcula scores.",
        )
    generated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    return GlobalRankingData(True, rows, generated_at)
