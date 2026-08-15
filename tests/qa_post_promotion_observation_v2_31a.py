#!/usr/bin/env python3
"""Post-promotion observation gate for v2.31A."""
from __future__ import annotations
import hashlib,json,time,tracemalloc
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()
def main():
 from src.ui_v2_28.adapters import build_app_state
 from src.ui_v2_28.catalog import load_catalog,query_catalog
 pointer=json.loads((ROOT/"outputs/full_universe_source_acquisition/current_operational_universe_pointer.json").read_text(encoding="utf-8"))
 dataset=ROOT/str(pointer["current_dataset"]).replace("\\","/")
 assert sha256(dataset)==pointer["current_dataset_sha256"]
 tracemalloc.start();start=time.perf_counter();rows=load_catalog(dataset);elapsed=time.perf_counter()-start;peak=tracemalloc.get_traced_memory()[1]/1048576
 assert len(rows)==43089 and len({r["identity_key"] for r in rows})==43089
 assert sum(r["provider"]=="Unknown" for r in rows)==0
 assert len(query_catalog(rows,filters={"provider":["nse_india"]},page_size=250).rows)==250
 assert query_catalog(rows,filters={"provider":["nse_india"]},page_size=250).total==2013
 start=time.perf_counter();result=query_catalog(rows,search="20MICRONS");search_ms=(time.perf_counter()-start)*1000
 state=build_app_state(ROOT)
 assert state.maintenance.providers_complete==14 and state.maintenance.missing_rows==0
 assert not state.scoring.allow_ranking
 assert elapsed<=3.0 and peak<=128 and search_ms<=250
 print(f"PASS: v2.31A/43089/14-of-14/0-missing/load={elapsed:.3f}s/peak={peak:.2f}MB/search={search_ms:.2f}ms/fail-closed")
 return 0
if __name__=="__main__":raise SystemExit(main())
