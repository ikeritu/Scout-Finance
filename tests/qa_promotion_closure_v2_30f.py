#!/usr/bin/env python3
"""QA gate for v2.30F operational promotion and compressed catalog compatibility."""
from __future__ import annotations
import csv,hashlib,json,lzma
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def main():
 from src.ui_v2_28.adapters import build_app_state
 from src.ui_v2_28.catalog import load_catalog
 p=json.loads((ROOT/"outputs/full_universe_source_acquisition/current_operational_universe_pointer.json").read_text(encoding="utf-8"))
 dataset=ROOT/str(p["current_dataset"]).replace("\\","/")
 assert dataset.suffix==".xz" and dataset.is_file()
 assert sha256(dataset)==p["current_dataset_sha256"]=="4cbde1e534ccf145542e6d0bd0c1f5aec7dba4d43037aea5f115e1ea9b46d6bf"
 with lzma.open(dataset,"rt",encoding="utf-8-sig",newline="") as f:
  raw=list(csv.DictReader(f))
 assert len(raw)==43089 and len(raw[0])==33
 assert sum(not row["source_provider"] for row in raw)==0
 assert sum(row["source_provider"]=="nse_india" for row in raw)==2013
 catalog=load_catalog(dataset)
 assert len(catalog)==43089 and len({row["identity_key"] for row in catalog})==43089
 state=build_app_state(ROOT)
 assert state.universe.available and state.universe.rows==43089
 assert state.maintenance.providers_complete==14 and state.maintenance.providers_expected==14 and state.maintenance.missing_rows==0
 assert not state.scoring.allow_ranking
 scoring=json.loads((ROOT/"outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json").read_text(encoding="utf-8"))
 assert scoring["production_scoring_authorized"] is False and scoring["scoring_promoted"] is False
 print("PASS: v2.30F/promoted/43089/14-of-14/2013-nse/0-missing/xz-compatible/scoring-fail-closed")
 return 0
if __name__=="__main__":raise SystemExit(main())
