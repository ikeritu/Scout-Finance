"""
Scout Finance — Phase 5B funnel paths.

Centralized paths for the global funnel.
No OpenAI calls.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
UNIVERSE_DIR = DATA_DIR / "universe"
STAGES_DIR = DATA_DIR / "stages"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SCOUTING_OUTPUTS_DIR = OUTPUTS_DIR / "scouting"

GLOBAL_UNIVERSE_PATH = UNIVERSE_DIR / "global_universe.csv"
GLOBAL_UNIVERSE_VALIDATED_PATH = UNIVERSE_DIR / "global_universe_validated.csv"
UNIVERSE_VALIDATION_SUMMARY_PATH = SCOUTING_OUTPUTS_DIR / "universe_validation_summary.json"


def ensure_funnel_directories() -> None:
    """
    Create the folder structure required by Phase 5B.
    """

    for path in [
        DATA_DIR,
        UNIVERSE_DIR,
        STAGES_DIR,
        OUTPUTS_DIR,
        SCOUTING_OUTPUTS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
