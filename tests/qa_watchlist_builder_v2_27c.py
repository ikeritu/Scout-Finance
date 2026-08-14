#!/usr/bin/env python3
"""Self-contained QA for watchlist_builder_v2_27c.py."""
import importlib.util,tempfile
from pathlib import Path
def load(path):
 s=importlib.util.spec_from_file_location("wb",path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 root=Path(__file__).resolve().parents[1];m=load(root/"scripts/watchlist_builder_v2_27c.py")
 with tempfile.TemporaryDirectory() as d:
  d=Path(d);p=d/"w.json";x=d/"out.csv"
  data=m.new_watchlist("QA");row={"identity_key":"qa:one","name":"=Unsafe","ticker":"QA","exchange":"XQ","source_provider":"fixture"}
  m.add_item(data,row,"test,alpha","@note");m.atomic_write(p,data,backup=False)
  loaded=m.read_watchlist(p);assert len(loaded["items"])==1
  try:m.add_item(loaded,row)
  except ValueError:pass
  else:raise AssertionError("duplicate accepted")
  m.export_csv(loaded,x);text=x.read_text(encoding="utf-8-sig");assert "'=Unsafe" in text and "'@note" in text
  m.remove_item(loaded,"qa:one");assert not loaded["items"];m.validate_data(loaded)
 print("PASS: init/add/dedup/export-injection/remove/validate")
 return 0
if __name__=="__main__":raise SystemExit(main())
