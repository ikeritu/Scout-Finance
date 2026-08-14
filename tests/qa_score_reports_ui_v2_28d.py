#!/usr/bin/env python3
import csv,hashlib,json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ui_v2_28.reports import diagnostic_markdown,package_report,universe_markdown,watchlist_markdown
from src.ui_v2_28.scoring import diagnostic_contract,distribution_rows,load_diagnostic
from src.ui_v2_28.state import ScoringState,UniverseState,ConsumerState
def main():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);out=root/"outputs/full_universe_source_acquisition";out.mkdir(parents=True);scores=out/"diag.csv"
  fields=["score_bucket","source_provider","country","data_quality_score","scope_confidence_score","provider_quality_score","attractiveness_score","production_scoring_authorized","dry_run_rank"]
  with scores.open("w",encoding="utf-8",newline="") as handle:
   writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows([{"score_bucket":"A","source_provider":"p1","country":"ES","data_quality_score":"80","scope_confidence_score":"70","provider_quality_score":"60","attractiveness_score":"0","production_scoring_authorized":"False","dry_run_rank":"1"},{"score_bucket":"B","source_provider":"p2","country":"Unknown","data_quality_score":"60","scope_confidence_score":"50","provider_quality_score":"40","attractiveness_score":"0","production_scoring_authorized":"False","dry_run_rank":"2"}])
  sha=hashlib.sha256(scores.read_bytes()).hexdigest();pointer=out/"current_operational_scoring_pointer.json";pointer.write_text(json.dumps({"status":"NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED","diagnostic_artifact":{"path":"outputs/full_universe_source_acquisition/diag.csv","sha256":sha,"rows":2,"role":"DATA_READINESS_ONLY","production_eligible":False},"consumer_contract":{"allow_ranking":False}}))
  assert diagnostic_contract(root)["available"]
  try:load_diagnostic(root,False)
  except PermissionError:pass
  else:raise AssertionError("diagnostic opened without acknowledgement")
  summary=load_diagnostic(root,True);assert summary["rows"]==2 and summary["allow_ranking"] is False and summary["component_means"]["data_quality_score"]==70
  assert distribution_rows(summary["buckets"],2)[0]["percent"]==50
  universe=UniverseState(True,43089,Path("universe.csv"),"abc");scoring=ScoringState(ConsumerState.SCORING_UNAVAILABLE,"LOCKED",False)
  watchlist={"name":"Core","watchlist_id":"id","updated_at_utc":"now","items":[],"scoring_used":False}
  texts=(universe_markdown(universe,scoring),watchlist_markdown(watchlist,scoring),diagnostic_markdown(summary))
  assert all("recommendation" not in text.lower() or "no " in text.lower() for text in texts)
  payload,manifest=package_report(texts[0],"universe","html",[{"sha256":"abc"}]);meta=json.loads(manifest);assert payload.startswith(b"<!doctype html>") and meta["investment_recommendation"] is False and meta["broker_action"] is False
 print("PASS: diagnostic-ack/hash/rows/no-ranking/components/reports/manifest/fail-closed");return 0
if __name__=="__main__":raise SystemExit(main())
