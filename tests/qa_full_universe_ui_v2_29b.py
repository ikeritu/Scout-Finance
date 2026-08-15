#!/usr/bin/env python3
"""Exercise catalog UI services against the full operational universe."""
from __future__ import annotations
import argparse,json,statistics,sys,time,tracemalloc
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ui_v2_28.catalog import DISPLAY_FIELDS,assert_metadata_only,distinct_values,load_catalog,query_catalog

def timed(callable_):
 start=time.perf_counter();value=callable_();return value,time.perf_counter()-start

def main(argv=None):
 parser=argparse.ArgumentParser();parser.add_argument("dataset",type=Path);parser.add_argument("--expected-rows",type=int,default=43089);parser.add_argument("--json-output",type=Path);args=parser.parse_args(argv)
 tracemalloc.start();rows,load_seconds=timed(lambda:load_catalog(args.dataset));current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
 identities=[row["identity_key"] for row in rows];counts=Counter(identities);duplicates=sum(count-1 for count in counts.values() if count>1)
 unknown={field:sum(row[field]=="Unknown" for row in rows) for field in DISPLAY_FIELDS}
 search_samples=[row for row in rows if row["ticker"]!="Unknown"][:20];search_times=[]
 for row in search_samples:
  result,elapsed=timed(lambda row=row:query_catalog(rows,row["ticker"],page=1,page_size=50));search_times.append(elapsed)
  if not result.total:raise AssertionError(f'search missed {row["ticker"]}')
 filter_fields=("country","exchange","currency","asset_type","provider");filter_times=[];filter_counts={}
 for field in filter_fields:
  values=distinct_values(rows,field);selected=next((value for value in values if value!="Unknown"),"Unknown")
  result,elapsed=timed(lambda field=field,selected=selected:query_catalog(rows,filters={field:[selected]},page=1,page_size=100));filter_times.append(elapsed);filter_counts[field]=result.total
 page,_page_seconds=timed(lambda:query_catalog(rows,page=999999,page_size=250))
 assert_metadata_only(rows)
 report={
  "status":"PASS","rows":len(rows),"expected_rows":args.expected_rows,"columns":list(DISPLAY_FIELDS),
  "unique_identities":len(counts),"duplicate_identity_rows":duplicates,"unknown_counts":unknown,
  "load_seconds":round(load_seconds,4),"peak_memory_mb":round(peak/1024/1024,2),
  "search_mean_ms":round(1000*statistics.mean(search_times),2),"search_max_ms":round(1000*max(search_times),2),
  "filter_mean_ms":round(1000*statistics.mean(filter_times),2),"filter_max_ms":round(1000*max(filter_times),2),"filter_result_counts":filter_counts,
  "last_page":page.page,"last_page_rows":len(page.rows),"pagination_ms":round(1000*_page_seconds,2),
 }
 errors=[]
 if len(rows)!=args.expected_rows:errors.append("row count mismatch")
 if duplicates:errors.append(f"{duplicates} duplicate stable identities")
 if load_seconds>15:errors.append("catalog load exceeds 15 seconds")
 if peak/1024/1024>512:errors.append("peak memory exceeds 512 MB")
 if max(search_times,default=0)>2:errors.append("search exceeds 2 seconds")
 if max(filter_times,default=0)>2:errors.append("filter exceeds 2 seconds")
 if errors:report["status"]="FAIL";report["errors"]=errors
 rendered=json.dumps(report,ensure_ascii=False,indent=2);print(rendered)
 if args.json_output:args.json_output.write_text(rendered+"\n",encoding="utf-8")
 if report["status"]=="PASS":print("PASS: 43089/load/memory/search/filters/pagination/identity/metadata-only")
 return 0 if report["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
