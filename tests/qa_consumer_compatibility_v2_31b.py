#!/usr/bin/env python3
"""Full consumer compatibility regression for v2.31B."""
from __future__ import annotations
import json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 from src.ui_v2_28.adapters import build_app_state
 from src.ui_v2_28.catalog import asset_by_identity,load_catalog,query_catalog
 from src.ui_v2_28.reports import package_report,universe_markdown
 from src.ui_v2_28.watchlists import add,atomic_write,create,export_csv_bytes,read
 pointer=json.loads((ROOT/"outputs/full_universe_source_acquisition/current_operational_universe_pointer.json").read_text(encoding="utf-8"))
 promoted=ROOT/str(pointer["current_dataset"]).replace("\\","/")
 baseline=ROOT/str(pointer["rollback_dataset"]).replace("\\","/")
 old_rows=load_catalog(baseline);new_rows=load_catalog(promoted)
 old_ids={r["identity_key"] for r in old_rows};new_ids={r["identity_key"] for r in new_rows}
 assert len(old_rows)==len(new_rows)==len(old_ids)==len(new_ids)==43089 and old_ids==new_ids
 search=query_catalog(new_rows,search="20MICRONS");assert search.total==1
 nse=query_catalog(new_rows,filters={"provider":["nse_india"],"country":["India"],"exchange":["NSE"]},page_size=250)
 assert nse.total==2013 and len(nse.rows)==250 and nse.pages==9
 asset=asset_by_identity(new_rows,search.rows[0]["identity_key"]);assert asset["ticker"]=="20MICRONS" and asset["provider"]=="nse_india"
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);path,data=create(root,"Regression");add(data,asset,"nse,regression","identity preserved");atomic_write(path,data)
  restored=read(path);assert restored["items"][0]["identity_key"] in new_ids
  exported=export_csv_bytes(restored);assert b"20MICRONS" in exported and b"score" not in exported.lower()
 state=build_app_state(ROOT);assert state.universe.available and state.maintenance.missing_rows==0 and not state.scoring.allow_ranking
 md=universe_markdown(state.universe,state.scoring);payload,manifest=package_report(md,"universe","md",[{"dataset_sha256":state.universe.dataset_sha256}])
 contract=json.loads(manifest);assert pointer["current_dataset_sha256"] in payload.decode() and contract["investment_recommendation"] is False and contract["broker_action"] is False
 print("PASS: v2.31B/13-consumers/43089-identities/no-breaking-change/no-migration/scoring-fail-closed")
 return 0
if __name__=="__main__":raise SystemExit(main())
