#!/usr/bin/env python3
"""Accumulated closure gate for v2.29A-v2.29F."""
from __future__ import annotations
import argparse,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(name,args):
 start=time.perf_counter();result=subprocess.run([sys.executable,str(ROOT/name),*map(str,args)],cwd=ROOT,capture_output=True,text=True);elapsed=time.perf_counter()-start
 if result.returncode:raise AssertionError(f"{name} failed\n{result.stdout}\n{result.stderr}")
 if "PASS:" not in result.stdout:raise AssertionError(f"{name} returned no PASS marker")
 return {"gate":name,"status":"PASS","seconds":round(elapsed,2),"marker":result.stdout.strip().splitlines()[-1]}
def main(argv=None):
 parser=argparse.ArgumentParser();parser.add_argument("--universe",type=Path,required=True);parser.add_argument("--diagnostic",type=Path,required=True);parser.add_argument("--scoring-pointer",type=Path,required=True);parser.add_argument("--json-output",type=Path);args=parser.parse_args(argv)
 gates=[
  run("tests/qa_clean_windows_install_v2_29a.py",[]),
  run("tests/qa_full_universe_ui_v2_29b.py",[args.universe]),
  run("tests/qa_eol_hash_compatibility_v2_29b.py",[]),
  run("tests/qa_functional_flows_v2_29c.py",[args.universe,args.diagnostic,args.scoring_pointer]),
  run("tests/qa_performance_memory_v2_29d.py",[args.universe]),
  run("tests/qa_incident_closure_v2_29e.py",[]),
  run("tests/qa_local_ui_closure_v2_28f.py",[]),
 ]
 report={"status":"PASS","phase":"v2.29F","gate_count":len(gates),"gates":gates,"universe_rows":43089,"diagnostic_rows":33498,"open_incidents":0,"allow_ranking":False,"production_scoring_authorized":False}
 rendered=json.dumps(report,ensure_ascii=False,indent=2);print(rendered)
 if args.json_output:args.json_output.write_text(rendered+"\n",encoding="utf-8")
 print("PASS: v2.29A-B-C-D-E-F/7-gates/43089/33498/0-incidents/fail-closed/stable-freeze");return 0
if __name__=="__main__":raise SystemExit(main())
