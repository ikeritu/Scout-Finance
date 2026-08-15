#!/usr/bin/env python3
"""Scenario-level acceptance test for every stable local UI workflow."""
from __future__ import annotations
import argparse,json,shutil,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ui_v2_28.catalog import asset_by_identity,load_catalog,query_catalog
from src.ui_v2_28.navigation import SCREENS,get_screen
from src.ui_v2_28.reports import diagnostic_markdown,package_report,universe_markdown,watchlist_markdown
from src.ui_v2_28.scoring import diagnostic_contract,load_diagnostic
from src.ui_v2_28.state import ConsumerState,ScoringState,UniverseState
from src.ui_v2_28.watchlists import add,atomic_write,create,export_csv_bytes,list_watchlists,read,remove,update_item,update_metadata

def main(argv=None):
 parser=argparse.ArgumentParser();parser.add_argument("universe",type=Path);parser.add_argument("diagnostic",type=Path);parser.add_argument("scoring_pointer",type=Path);args=parser.parse_args(argv)
 rows=load_catalog(args.universe);assert len(rows)==43089
 scenarios=[]
 assert len(SCREENS)==8 and all(get_screen(screen.id)==screen for screen in SCREENS);scenarios.append("navigation")
 result=query_catalog(rows,rows[100]["ticker"],page_size=25);assert result.total>=1;asset=asset_by_identity(rows,result.rows[0]["identity_key"]);assert asset["ticker"]==result.rows[0]["ticker"];scenarios+=['catalog_search','asset_detail']
 filtered=query_catalog(rows,filters={"provider":[rows[100]["provider"]]},page=2,page_size=50);assert filtered.total>=len(filtered.rows);scenarios+=['catalog_filter','pagination']
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);out=root/"outputs/full_universe_source_acquisition";out.mkdir(parents=True);pointer=json.loads(args.scoring_pointer.read_text(encoding="utf-8"));diagnostic_name=Path(pointer["diagnostic_artifact"]["path"].replace("\\","/")).name;shutil.copy2(args.diagnostic,out/diagnostic_name);(out/"current_operational_scoring_pointer.json").write_text(json.dumps(pointer),encoding="utf-8")
  path,watch=create(root,"Acceptance","Functional scenario");add(watch,rows[0],"core,qa","initial note");add(watch,rows[1],"qa","second");atomic_write(path,watch)
  try:add(watch,rows[0])
  except ValueError:pass
  else:raise AssertionError("watchlist duplicate accepted")
  update_item(watch,rows[0]["identity_key"],"updated","reviewed");update_metadata(path,watch,"Acceptance updated","End-to-end");persisted=read(path);assert len(persisted["items"])==2 and len(list_watchlists(root))==1 and b"identity_key" in export_csv_bytes(persisted);scenarios+=['watchlist_create','watchlist_add','watchlist_dedupe','watchlist_edit','watchlist_export']
  contract=diagnostic_contract(root);assert contract["available"] and contract["rows"]==33498
  try:load_diagnostic(root,False)
  except PermissionError:pass
  else:raise AssertionError("diagnostic opened without acknowledgement")
  summary=load_diagnostic(root,True);assert summary["rows"]==33498 and summary["allow_ranking"] is False;scenarios+=['score_fail_closed','diagnostic_ack','diagnostic_integrity']
  scoring=ScoringState(ConsumerState.SCORING_UNAVAILABLE,"LOCKED",False);universe=UniverseState(True,43089,args.universe,"verified")
  reports=(("universe",universe_markdown(universe,scoring)),("watchlist",watchlist_markdown(persisted,scoring)),("diagnostic",diagnostic_markdown(summary)))
  for kind,markdown in reports:
   for fmt in ("md","html"):
    payload,manifest=package_report(markdown,kind,fmt,[{"scenario":"v2.29C"}]);meta=json.loads(manifest);assert payload and meta["investment_recommendation"] is False and meta["broker_action"] is False
  scenarios+=['report_universe','report_watchlist','report_diagnostic','manifest_download']
  remove(persisted,rows[1]["identity_key"]);atomic_write(path,persisted);assert len(read(path)["items"])==1;scenarios.append('watchlist_remove')
 app=(Path(__file__).resolve().parents[1]/"app_v2_28.py").read_text(encoding="utf-8");assert "Vista avanzada · solo lectura" in app and "Ayuda y límites" in app and "SCORING UNAVAILABLE" in app;scenarios+=['maintenance_read_only','help_limits']
 report={"status":"PASS","scenario_count":len(scenarios),"scenarios":scenarios,"universe_rows":len(rows),"diagnostic_rows":33498,"allow_ranking":False}
 print(json.dumps(report,ensure_ascii=False,indent=2));print(f"PASS: {len(scenarios)} functional scenarios/catalog/watchlists/diagnostic/reports/maintenance/help/fail-closed");return 0
if __name__=="__main__":raise SystemExit(main())
