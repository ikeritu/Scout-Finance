#!/usr/bin/env python3
import hashlib,importlib.util,json,tempfile
from pathlib import Path
def load(path):
 s=importlib.util.spec_from_file_location("se",path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 root=Path(__file__).resolve().parents[1];m=load(root/"scripts/score_explorer_v2_27d.py")
 with tempfile.TemporaryDirectory() as d:
  d=Path(d);scores=d/"scores.csv";pointer=d/"pointer.json";locked=d/"locked.html";diag=d/"diag.html"
  scores.write_text("dry_run_v2_25b_score,score_bucket,data_quality_score,scope_confidence_score,provider_quality_score,attractiveness_score,source_provider,country,formula_version,production_scoring_authorized,promotion_status,dry_run_rank\n80,A,90,80,70,,P1,ES,vtest,False,NOT_PROMOTED,1\n60,B,70,60,50,,P2,FR,vtest,False,NOT_PROMOTED,2\n")
  sha=hashlib.sha256(scores.read_bytes()).hexdigest()
  p={"status":"NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED","active_scoring_available":False,"production_scoring_authorized":False,"scoring_promoted":False,"consumer_contract":{"allow_ranking":False},"diagnostic_artifact":{"path":"scores.csv","sha256":sha,"rows":2,"role":"DATA_READINESS_ONLY","production_eligible":False}}
  pointer.write_text(json.dumps(p))
  assert m.main(["--pointer",str(pointer),"--output",str(locked)])==0
  assert "FAIL-CLOSED" in locked.read_text() and "dry_run_rank" not in locked.read_text()
  assert m.main(["--pointer",str(pointer),"--output",str(diag),"--mode","diagnostic","--scores",str(scores)])==1
  assert m.main(["--pointer",str(pointer),"--output",str(diag),"--mode","diagnostic","--scores",str(scores),"--acknowledge-data-readiness-only"])==0
  text=diag.read_text();assert "DIAGNOSTIC" in text and "not an investment ranking" in text and "dry_run_rank" not in text
 print("PASS: locked-default/ack-required/hash+rows/diagnostic-no-ranking")
 return 0
if __name__=="__main__":raise SystemExit(main())
