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
        return GlobalRankingData(False, (), "", "El ranking global todavía no se ha calculado nunca en este equipo -- ejecuta scripts/build_global_research_ranking_v2_38bv.py.")
    try:
        rows = tuple(json.loads(path.read_text(encoding="utf-8")))
    except Exception as exc:  # noqa: BLE001
        return GlobalRankingData(False, (), "", f"No se pudo leer el ranking existente: {exc}")
    generated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    return GlobalRankingData(True, rows, generated_at)
