#!/usr/bin/env python3
"""Repeatable performance and memory gate for the stable local UI services."""
from __future__ import annotations
import argparse,gc,json,statistics,sys,time,tracemalloc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ui_v2_28.catalog import distinct_values,load_catalog,query_catalog
from src.ui_v2_28.reports import package_report,watchlist_markdown
from src.ui_v2_28.state import ConsumerState,ScoringState
from src.ui_v2_28.watchlists import export_csv_bytes,new_watchlist,add

def measure(callable_,iterations=1):
 times=[];value=None
 for _ in range(iterations):
  start=time.perf_counter();value=callable_();times.append(time.perf_counter()-start)
 return value,times
def stats(times):return {"mean_ms":round(statistics.mean(times)*1000,2),"p95_ms":round(sorted(times)[max(0,int(len(times)*.95)-1)]*1000,2),"max_ms":round(max(times)*1000,2)}
def main(argv=None):
 parser=argparse.ArgumentParser();parser.add_argument("dataset",type=Path);parser.add_argument("--json-output",type=Path);args=parser.parse_args(argv)
 gc.collect();tracemalloc.start();rows,loads=measure(lambda:load_catalog(args.dataset),3);current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();assert len(rows)==43089
 tickers=[row["ticker"] for row in rows[::max(1,len(rows)//60)] if row["ticker"]!="Unknown"][:60];measure(lambda:query_catalog(rows,tickers[0]),1)
 search_times=[]
 for ticker in tickers:
  _,elapsed=measure(lambda ticker=ticker:query_catalog(rows,ticker,page_size=50));search_times+=elapsed
 fields=("country","exchange","currency","asset_type","provider");facets={field:next(value for value in distinct_values(rows,field) if value!="Unknown") for field in fields};filter_times=[]
 for _ in range(12):
  for field,value in facets.items():_,elapsed=measure(lambda field=field,value=value:query_catalog(rows,filters={field:[value]},page_size=100));filter_times+=elapsed
 _,pagination_times=measure(lambda:query_catalog(rows,page=173,page_size=250),40)
 watch=new_watchlist("Performance")
 for row in rows[:1000]:add(watch,row,"perf","benchmark")
 _,export_times=measure(lambda:export_csv_bytes(watch),20);scoring=ScoringState(ConsumerState.SCORING_UNAVAILABLE,"LOCKED",False);markdown=watchlist_markdown(watch,scoring);_,report_times=measure(lambda:package_report(markdown,"watchlist","html",[]),20)
 memory_mb=peak/1024/1024;report={"status":"PASS","rows":len(rows),"load":stats(loads),"peak_memory_mb":round(memory_mb,2),"memory_kb_per_1000_rows":round(memory_mb*1024/len(rows)*1000,2),"search_60":stats(search_times),"filter_60":stats(filter_times),"pagination_40":stats(pagination_times),"watchlist_export_1000_items_20":stats(export_times),"html_report_1000_items_20":stats(report_times)}
 errors=[]
 gates=((max(loads),15,"load >15s"),(memory_mb,512,"memory >512MB"),(max(search_times),.5,"search >500ms"),(max(filter_times),.5,"filter >500ms"),(max(pagination_times),.5,"pagination >500ms"),(max(export_times),1,"export >1s"),(max(report_times),1,"report >1s"))
 for value,limit,message in gates:
  if value>limit:errors.append(message)
 if errors:report["status"]="FAIL";report["errors"]=errors
 rendered=json.dumps(report,ensure_ascii=False,indent=2);print(rendered)
 if args.json_output:args.json_output.write_text(rendered+"\n",encoding="utf-8")
 if report["status"]=="PASS":print("PASS: repeated-load/memory/search/filter/pagination/export/report/performance-gates")
 return 0 if report["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
