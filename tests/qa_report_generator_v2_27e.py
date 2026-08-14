#!/usr/bin/env python3
import hashlib,importlib.util,json,tempfile
from pathlib import Path
def loadm(path):
 s=importlib.util.spec_from_file_location("rg",path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 root=Path(__file__).resolve().parents[1];m=loadm(root/"scripts/report_generator_v2_27e.py")
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);sp=d/"sp.json";up=d/"up.json";wl=d/"wl.json";scores=d/"scores.csv"
  scores.write_text("score_bucket,data_quality_score,scope_confidence_score,provider_quality_score,attractiveness_score,production_scoring_authorized,promotion_status,dry_run_rank\nA,90,80,70,,False,NOT_PROMOTED,1\n")
  sha=hashlib.sha256(scores.read_bytes()).hexdigest()
  sp.write_text(json.dumps({"status":"NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED","active_scoring_available":False,"production_scoring_authorized":False,"scoring_promoted":False,"consumer_contract":{"allow_ranking":False},"diagnostic_artifact":{"sha256":sha,"rows":1,"role":"DATA_READINESS_ONLY","production_eligible":False}}))
  up.write_text(json.dumps({"current_dataset_rows":43089,"current_dataset":"universe.csv","current_dataset_sha256":"a"*64,"quality_floor_target":42000,"quality_ceiling_target":45000,"remaining_capacity":1911}))
  wl.write_text(json.dumps({"name":"QA","consumer_state":"CATALOG_AVAILABLE","scoring_used":False,"items":[{"identity_key":"one","ticker":"QA","exchange":"XQ","name":"Asset","tags":["test"],"note":"note"}]}))
  u=d/"u.md";w=d/"w.html";g=d/"g.md"
  assert m.main(["--type","universe","--scoring-pointer",str(sp),"--universe-pointer",str(up),"--output",str(u)])==0
  assert "43,089" in u.read_text() and "FAIL-CLOSED" in u.read_text()
  assert m.main(["--type","watchlist","--scoring-pointer",str(sp),"--watchlist",str(wl),"--format","html","--output",str(w)])==0
  assert "Asset" in w.read_text() and "recommendation" in w.read_text().lower()
  assert m.main(["--type","diagnostic","--scoring-pointer",str(sp),"--scores",str(scores),"--output",str(g)])==1
  assert m.main(["--type","diagnostic","--scoring-pointer",str(sp),"--scores",str(scores),"--acknowledge-data-readiness-only","--output",str(g)])==0
  assert "dry_run_rank" in g.read_text() and "no assets are ordered" in g.read_text()
  for x in (u,w,g):assert x.with_suffix(x.suffix+".manifest.json").exists()
 print("PASS: universe/watchlist/diagnostic-ack/html/manifests/fail-closed")
 return 0
if __name__=="__main__":raise SystemExit(main())
