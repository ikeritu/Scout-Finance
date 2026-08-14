#!/usr/bin/env python3
import hashlib,json,tempfile
from pathlib import Path
from src.ui_v2_28.adapters import build_app_state,load_scoring,load_universe
from src.ui_v2_28.navigation import SCREENS,get_screen
from src.ui_v2_28.paths import safe_repo_path
from src.ui_v2_28.state import ConsumerState

def main():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);out=root/"outputs/full_universe_source_acquisition";out.mkdir(parents=True)
  dataset=out/"universe.csv";dataset.write_text("id,name\n1,One\n")
  dsha=hashlib.sha256(dataset.read_bytes()).hexdigest()
  (out/"current_operational_universe_pointer.json").write_text(json.dumps({"current_dataset":"outputs\\full_universe_source_acquisition\\universe.csv","current_dataset_rows":1,"current_dataset_sha256":dsha}))
  (out/"current_operational_scoring_pointer.json").write_text(json.dumps({"schema_version":"1.0","status":"NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED","active_scoring_available":False,"production_scoring_authorized":False,"scoring_promoted":False,"active_scoring_artifact":None,"active_scoring_sha256":None,"consumer_contract":{"allow_ranking":False}}))
  m=out/"v2_26f_scheduled_maintenance_plan";m.mkdir()
  (m/"maintenance_plan_report.json").write_text(json.dumps({"operating_state":{"refresh_promotion_status":"HOLD_NO_ELIGIBLE_CANDIDATE","open_provider_gap":{"providers_complete":13,"providers_expected":14,"missing_rows":2013}}}))
  s=build_app_state(root)
  assert s.universe.available and s.universe.rows==1
  assert s.scoring.consumer_state==ConsumerState.SCORING_UNAVAILABLE and not s.scoring.allow_ranking
  assert s.maintenance.providers_complete==13 and s.maintenance.missing_rows==2013
  assert len(SCREENS)==8 and get_screen("scores").id=="scores"
  try:safe_repo_path(root,"../escape")
  except ValueError:pass
  else:raise AssertionError("path traversal accepted")
  dataset.write_text("tampered")
  assert not load_universe(root).available
 print("PASS: pointer/hash/path/state/navigation/maintenance/fail-closed")
 return 0
if __name__=="__main__":raise SystemExit(main())
