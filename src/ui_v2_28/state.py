"""Typed UI state. No Streamlit dependency."""
from dataclasses import dataclass,field
from enum import Enum
from pathlib import Path
from typing import Optional,Tuple

class ConsumerState(str,Enum):
 CATALOG_AVAILABLE="CATALOG_AVAILABLE"
 DIAGNOSTIC_LOCKED="DIAGNOSTIC_LOCKED"
 PRODUCTION_RANKING="PRODUCTION_RANKING"
 SCORING_UNAVAILABLE="SCORING_UNAVAILABLE"

@dataclass(frozen=True)
class UniverseState:
 available:bool;rows:int=0;dataset:Optional[Path]=None;dataset_sha256:Optional[str]=None;pointer_sha256:Optional[str]=None;status:str="UNAVAILABLE";errors:Tuple[str,...]=()

@dataclass(frozen=True)
class ScoringState:
 consumer_state:ConsumerState;status:str;allow_ranking:bool=False;active_artifact:Optional[Path]=None;formula_version:Optional[str]=None;diagnostic_rows:int=0;errors:Tuple[str,...]=()

@dataclass(frozen=True)
class MaintenanceState:
 refresh_status:str="UNKNOWN";providers_complete:int=0;providers_expected:int=0;missing_rows:int=0

@dataclass(frozen=True)
class AppState:
 root:Path;universe:UniverseState;scoring:ScoringState;maintenance:MaintenanceState=field(default_factory=MaintenanceState)
 @property
 def catalog_available(self):return self.universe.available
