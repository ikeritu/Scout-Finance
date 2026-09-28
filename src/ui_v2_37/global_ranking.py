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

v2.46E: 44 of the 1,111 scored companies are dual listings of the same
SEC registrant (same CIK, e.g. a US original + its Cboe Europe secondary
row) -- v2.38BV scores and ranks each listing independently, so a company
with two listings can occupy two ranking slots. `scripts/build_global_
research_ranking_v2_38bv.py --dedupe-by-cik-from` writes a second,
deduplicated ranking (one row per SEC registrant, `DUPLICATE_LISTING` for
the rest) to its own v2.46E output directory -- the original v2.38BV
files are never touched, since the v2.38BX..v2.44A audits already cite
their exact numbers. This loader prefers the deduplicated ranking when it
exists locally and falls back to v2.38BV, fail-closed, when it does not
-- never silently recomputing, never blocking the screen over a decision
the user has not been asked yet to make permanent.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

RESULTS_REL = "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json"
DEDUPED_RESULTS_REL = "outputs/full_universe_source_acquisition/v2_46e_global_research_ranking_deduplicated/global_research_ranking_results_v2_46e.json"
BUILD_COMMAND = "python scripts/build_global_research_ranking_v2_38bv.py"
DEDUPE_BUILD_COMMAND = "python scripts/build_global_research_ranking_v2_38bv.py --dedupe-by-cik-from"
LIMITATIONS_DOC_REL = "docs/FINAL_COVERAGE_LIMITATIONS_v2_41d.md"


@dataclass(frozen=True)
class GlobalRankingData:
    available: bool
    rows: tuple[dict, ...]
    generated_at: str
    error: str = ""
    deduplicated: bool = False


def _rooted(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes repository root") from exc
    return candidate


def _read_rows(path: Path, results_rel: str, build_command: str) -> GlobalRankingData | tuple[dict, ...]:
    """Returns the parsed rows, or a GlobalRankingData already carrying the error."""
    try:
        rows = tuple(json.loads(path.read_text(encoding="utf-8")))
    except Exception as exc:  # noqa: BLE001
        return GlobalRankingData(
            False,
            (),
            "",
            "El ranking global experimental existe, pero no se pudo leer como JSON valido. "
            f"Archivo afectado: {results_rel}. "
            f"Detalle tecnico: {exc}. "
            f"Regeneralo con {build_command} si el repositorio contiene los inputs locales esperados.",
        )
    if not isinstance(rows, tuple) or any(not isinstance(row, dict) for row in rows):
        return GlobalRankingData(
            False,
            (),
            "",
            "El ranking global experimental no tiene la estructura esperada de lista de filas. "
            f"Archivo afectado: {results_rel}. "
            f"Regeneralo con {build_command}; la app no inventa filas ni recalcula scores.",
        )
    return rows


def load_global_ranking(root: Path) -> GlobalRankingData:
    deduped_path = _rooted(root, DEDUPED_RESULTS_REL)
    if deduped_path.is_file():
        result = _read_rows(deduped_path, DEDUPED_RESULTS_REL, DEDUPE_BUILD_COMMAND)
        if isinstance(result, tuple):
            generated_at = datetime.fromtimestamp(deduped_path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
            return GlobalRankingData(True, result, generated_at, deduplicated=True)
        return result

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
    result = _read_rows(path, RESULTS_REL, BUILD_COMMAND)
    if not isinstance(result, tuple):
        return result
    generated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    return GlobalRankingData(True, result, generated_at, deduplicated=False)
