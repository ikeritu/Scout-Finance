"""Pointer-safe UI foundation for Scout Finance v2.28."""
from .state import ConsumerState, AppState, UniverseState, ScoringState
from .adapters import build_app_state
from .navigation import SCREENS, get_screen
__all__=["ConsumerState","AppState","UniverseState","ScoringState","build_app_state","SCREENS","get_screen"]
