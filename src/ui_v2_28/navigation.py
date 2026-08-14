"""Static navigation contract."""
from dataclasses import dataclass
from typing import Tuple
from .state import ConsumerState

@dataclass(frozen=True)
class Screen:
 id:str;label:str;icon:str;allowed_states:Tuple[ConsumerState,...];advanced:bool=False

SCREENS=(
 Screen("status","Inicio / Estado","🏠",tuple(ConsumerState)),
 Screen("universe","Universo","🌐",(ConsumerState.CATALOG_AVAILABLE,ConsumerState.SCORING_UNAVAILABLE,ConsumerState.DIAGNOSTIC_LOCKED,ConsumerState.PRODUCTION_RANKING)),
 Screen("watchlists","Watchlists","⭐",(ConsumerState.CATALOG_AVAILABLE,ConsumerState.SCORING_UNAVAILABLE,ConsumerState.DIAGNOSTIC_LOCKED,ConsumerState.PRODUCTION_RANKING)),
 Screen("scores","Score Explorer","📊",tuple(ConsumerState)),
 Screen("reports","Informes y exports","📄",tuple(ConsumerState)),
 Screen("asset","Detalle de activo","🔎",tuple(ConsumerState)),
 Screen("maintenance","Mantenimiento","🛠️",tuple(ConsumerState),True),
 Screen("help","Ayuda y límites","❓",tuple(ConsumerState)),
)
def get_screen(screen_id):
 for s in SCREENS:
  if s.id==screen_id:return s
 raise KeyError(f"unknown screen: {screen_id}")
