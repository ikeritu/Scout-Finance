#!/usr/bin/env python3
import hashlib,json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.verify_local_ui_install_v2_29a import verify
def main():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);out=root/"outputs/full_universe_source_acquisition";out.mkdir(parents=True)
  for rel in ("app_v2_28.py","requirements-ui-v2_28.txt","run_local_ui_v2_28.bat"):(root/rel).write_text("fixture",encoding="utf-8")
  dataset=out/"universe.csv";dataset.write_text("id\n1\n",encoding="utf-8");sha=hashlib.sha256(dataset.read_bytes().replace(b"\n",b"\r\n")).hexdigest()
  (out/"current_operational_universe_pointer.json").write_text(json.dumps({"current_dataset":"outputs\\full_universe_source_acquisition\\universe.csv","current_dataset_rows":43089,"current_dataset_sha256":sha}))
  (out/"current_operational_scoring_pointer.json").write_text(json.dumps({"production_scoring_authorized":False,"consumer_contract":{"allow_ranking":False}}))
  report=verify(root,check_dependencies=False);assert report["status"]=="PASS" and report["checks"]["universe_sha256_matches"]
  dataset.write_text("tampered",encoding="utf-8");bad=verify(root,check_dependencies=False);assert bad["status"]=="FAIL" and "operational universe SHA-256 mismatch" in bad["errors"]
  escaped=json.loads((out/"current_operational_universe_pointer.json").read_text());escaped["current_dataset"]="..\\..\\..\\escape.csv";(out/"current_operational_universe_pointer.json").write_text(json.dumps(escaped))
  unsafe=verify(root,check_dependencies=False);assert unsafe["status"]=="FAIL" and any("escapes" in error for error in unsafe["errors"])
 print("PASS: clean-install/requirements/python/pointers/hash/path-safety/fail-closed/tamper-detection");return 0
if __name__=="__main__":raise SystemExit(main())
