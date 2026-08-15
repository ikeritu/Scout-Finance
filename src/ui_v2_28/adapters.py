"""Read-only, pointer-safe data adapters."""
from __future__ import annotations
import json
from pathlib import Path
from .paths import safe_repo_path,sha256,sha256_matches
from .state import AppState,ConsumerState,MaintenanceState,ScoringState,UniverseState
UNIVERSE_POINTER="outputs/full_universe_source_acquisition/current_operational_universe_pointer.json"
SCORING_POINTER="outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json"
MAINTENANCE_REPORT="outputs/full_universe_source_acquisition/v2_31d_live_provider_probe/probe_report.json"
def read_json(path):return json.loads(path.read_text(encoding="utf-8"))
def load_universe(root:Path,pointer_rel=UNIVERSE_POINTER,verify_hash=True):
 errors=[];pointer=safe_repo_path(root,pointer_rel)
 try:
  p=read_json(pointer);dataset=safe_repo_path(root,p["current_dataset"])
  if not dataset.is_file():raise ValueError("operational universe dataset missing")
  expected=p.get("current_dataset_sha256")
  if verify_hash and expected and not sha256_matches(dataset,expected,True):raise ValueError("operational universe SHA-256 mismatch")
  rows=int(p.get("current_dataset_rows",0))
  if rows<=0:raise ValueError("operational universe row count invalid")
  return UniverseState(True,rows,dataset,expected,sha256(pointer),"ACTIVE_REFERENCE",())
 except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:
  errors.append(str(exc));return UniverseState(False,status="UNAVAILABLE_FAIL_CLOSED",errors=tuple(errors))
def scoring_checks(p):
 c=p.get("consumer_contract") or {}
 return {"schema_version_supported":p.get("schema_version")=="1.0","status_is_active":p.get("status") not in (None,"NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED"),"active_scoring_available_true":p.get("active_scoring_available") is True,"production_scoring_authorized_true":p.get("production_scoring_authorized") is True,"scoring_promoted_true":p.get("scoring_promoted") is True,"active_scoring_artifact_non_null":bool(p.get("active_scoring_artifact")),"active_scoring_sha256_present":bool(p.get("active_scoring_sha256")),"allow_ranking_true":c.get("allow_ranking") is True}
def load_scoring(root:Path,pointer_rel=SCORING_POINTER):
 pointer=safe_repo_path(root,pointer_rel)
 try:
  p=read_json(pointer);checks=scoring_checks(p);diagnostic=p.get("diagnostic_artifact") or {}
  if not all(checks.values()):
   failed=tuple(k for k,v in checks.items() if not v);return ScoringState(ConsumerState.SCORING_UNAVAILABLE,p.get("status","SCORING_UNAVAILABLE"),False,diagnostic_rows=int(diagnostic.get("rows",0)),errors=failed)
  artifact=safe_repo_path(root,p["active_scoring_artifact"])
  if not artifact.is_file():raise ValueError("active scoring artifact missing")
  if not sha256_matches(artifact,p["active_scoring_sha256"],True):raise ValueError("active scoring SHA-256 mismatch")
  return ScoringState(ConsumerState.PRODUCTION_RANKING,p["status"],True,artifact,p.get("active_formula_version"),int(diagnostic.get("rows",0)),())
 except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:return ScoringState(ConsumerState.SCORING_UNAVAILABLE,"SCORING_UNAVAILABLE_FAIL_CLOSED",False,errors=(str(exc),))
def load_maintenance(root:Path,report_rel=MAINTENANCE_REPORT):
 try:
  r=read_json(safe_repo_path(root,report_rel));op=r.get("operating_state") or {};gap=op.get("open_provider_gap") or {}
  return MaintenanceState(op.get("refresh_promotion_status","UNKNOWN"),int(gap.get("providers_complete",0)),int(gap.get("providers_expected",0)),int(gap.get("missing_rows",0)))
 except (OSError,TypeError,ValueError,json.JSONDecodeError):return MaintenanceState()
def build_app_state(root:Path,verify_universe_hash=True):
 root=root.resolve();return AppState(root,load_universe(root,verify_hash=verify_universe_hash),load_scoring(root),load_maintenance(root))
