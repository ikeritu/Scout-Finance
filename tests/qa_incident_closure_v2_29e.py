#!/usr/bin/env python3
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ui_v2_28.catalog import query_catalog
from src.ui_v2_28.watchlists import atomic_write,create,list_watchlists,scan_watchlists,update_metadata
def main():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);path,data=create(root,"Valid","ok");corrupt=path.parent/"corrupt.json";corrupt.write_text("{broken",encoding="utf-8")
  valid,errors=scan_watchlists(root);assert len(valid)==1 and len(errors)==1 and errors[0][0].name=="corrupt.json" and len(list_watchlists(root))==1
  before=json.loads(path.read_text(encoding="utf-8"))
  try:update_metadata(path,data,"","")
  except ValueError:pass
  else:raise AssertionError("empty watchlist name accepted")
  assert json.loads(path.read_text(encoding="utf-8"))==before
  raw=[{"identity_key":"id:1","name":"One","ticker":"ONE","exchange":"X","isin":"Unknown","country":"ES","currency":"EUR","asset_type":"Equity","provider":"p"}]
  assert query_catalog(raw,"one").total==1 and query_catalog(raw,filters={"country":["ES"]}).total==1
  powershell=(Path(__file__).resolve().parents[1]/"setup_local_ui_v2_29a.ps1").read_text(encoding="utf-8");assert "$PythonExe @PythonArgs -m venv .venv" in powershell and "$PythonCommand[0]" not in powershell
 print("PASS: corrupt-watchlist-isolation/valid-list-continuity/required-name/query-equivalence/PowerShell-invocation");return 0
if __name__=="__main__":raise SystemExit(main())
