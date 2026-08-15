#!/usr/bin/env python3
"""Verify a clean local UI installation without starting Streamlit."""
from __future__ import annotations
import argparse,hashlib,importlib,json,platform,sys
from pathlib import Path

REQUIRED_FILES=(
 "app_v2_28.py","requirements-ui-v2_28.txt","run_local_ui_v2_28.bat",
 "outputs/full_universe_source_acquisition/current_operational_universe_pointer.json",
 "outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json",
)

def digest(path):
 h=hashlib.sha256()
 with path.open("rb") as handle:
  for chunk in iter(lambda:handle.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def digest_matches_csv(path,expected):
 if digest(path)==expected:return True
 raw=path.read_bytes()
 if path.suffix.lower()!=".csv" or b"\r" in raw:return False
 return hashlib.sha256(raw.replace(b"\n",b"\r\n")).hexdigest()==expected

def safe_path(root,value):
 candidate=(root/str(value or "").replace("\\","/").lstrip("/")).resolve()
 try:candidate.relative_to(root.resolve())
 except ValueError:raise ValueError("pointer path escapes project root")
 return candidate

def verify(root,skip_dataset_hash=False,check_dependencies=True):
 checks={};errors=[]
 checks["python_supported"]=sys.version_info>=(3,10)
 if not checks["python_supported"]:errors.append("Python 3.10 or newer is required")
 for rel in REQUIRED_FILES:
  ok=(root/rel).is_file();checks[f"file:{rel}"]=ok
  if not ok:errors.append(f"missing {rel}")
 if check_dependencies:
  for module in ("streamlit","pandas"):
   try:importlib.import_module(module);checks[f"dependency:{module}"]=True
   except ImportError:checks[f"dependency:{module}"]=False;errors.append(f"missing dependency {module}")
 universe_pointer=root/REQUIRED_FILES[3];scoring_pointer=root/REQUIRED_FILES[4]
 if universe_pointer.is_file():
  try:
   pointer=json.loads(universe_pointer.read_text(encoding="utf-8"));dataset=safe_path(root,pointer["current_dataset"])
   checks["universe_rows_43089"]=int(pointer.get("current_dataset_rows",0))==43089
   checks["universe_dataset_exists"]=dataset.is_file()
   if not checks["universe_rows_43089"]:errors.append("unexpected universe row count")
   if not checks["universe_dataset_exists"]:errors.append("operational universe dataset missing")
   if dataset.is_file() and not skip_dataset_hash:
    checks["universe_sha256_matches"]=digest_matches_csv(dataset,pointer.get("current_dataset_sha256"))
    if not checks["universe_sha256_matches"]:errors.append("operational universe SHA-256 mismatch")
  except (OSError,KeyError,ValueError,json.JSONDecodeError) as exc:errors.append(f"universe pointer invalid: {exc}")
 if scoring_pointer.is_file():
  try:
   pointer=json.loads(scoring_pointer.read_text(encoding="utf-8"));contract=pointer.get("consumer_contract") or {}
   checks["scoring_fail_closed"]=pointer.get("production_scoring_authorized") is False and contract.get("allow_ranking") is False
   if not checks["scoring_fail_closed"]:errors.append("scoring pointer is not in expected fail-closed state")
  except (OSError,json.JSONDecodeError) as exc:errors.append(f"scoring pointer invalid: {exc}")
 return {"status":"PASS" if not errors else "FAIL","platform":platform.platform(),"python":platform.python_version(),"checks":checks,"errors":errors}

def main(argv=None):
 parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument("--skip-dataset-hash",action="store_true");parser.add_argument("--skip-dependencies",action="store_true");args=parser.parse_args(argv)
 report=verify(args.root.resolve(),args.skip_dataset_hash,not args.skip_dependencies);print(json.dumps(report,ensure_ascii=False,indent=2))
 if report["status"]=="PASS":print("PASS: python/files/dependencies/universe-pointer/dataset/scoring-fail-closed")
 return 0 if report["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
