from __future__ import annotations
import argparse, csv, json, math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"real"
OUTM=ROOT/"outputs"/"market_data"
OUTS=ROOT/"outputs"/"scouting"
UNIV=DATA/"real_universe.csv"
TEMPLATE=DATA/"manual_market_data_template.csv"
MANUAL=DATA/"manual_market_data.csv"
YFCACHE=OUTM/"real_market_data_rows.csv"
OUT_ROWS=OUTM/"market_data_provider_fallback_rows.csv"
OUT_SUM=OUTM/"market_data_provider_fallback_summary.json"
OUT_REP=OUTM/"market_data_provider_fallback_report.md"
OUT_CAND=OUTS/"real_universe_market_data_candidates.csv"
OUT_ACTIVE=OUTS/"active_real_universe_top_candidates.csv"
METHOD="market_data_provider_fallback_v0"
REQ=["ticker","price","market_cap","volume","average_volume","change_1d","change_5d","change_20d","currency","as_of"]

def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
def n(v): return str(v or "").strip()
def u(v): return n(v).upper().replace("$","")
def fl(v):
    try:
        if n(v)=="": return None
        x=float(v)
        return None if math.isnan(x) else x
    except Exception: return None
def rows(p:Path):
    if not p.exists(): return []
    with p.open("r",encoding="utf-8-sig",newline="") as f: return [dict(r) for r in csv.DictReader(f)]
def wcsv(p:Path, rs:list[dict[str,Any]]):
    p.parent.mkdir(parents=True,exist_ok=True)
    if not rs: p.write_text("",encoding="utf-8"); return
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0].keys())); w.writeheader(); w.writerows(rs)
def wjson(p:Path,d:Any):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")
def init_template():
    DATA.mkdir(parents=True,exist_ok=True)
    if not TEMPLATE.exists():
        TEMPLATE.write_text("ticker,price,market_cap,volume,average_volume,change_1d,change_5d,change_20d,currency,as_of,source_note\nAAPL,195,3000000000000,50000000,55000000,0.5,1.2,3.5,USD,2026-06-29,manual test data\nMSFT,430,3200000000000,25000000,28000000,0.3,0.9,2.8,USD,2026-06-29,manual test data\nASML,750,300000000000,1200000,1500000,-0.2,1.5,4.1,EUR,2026-06-29,manual test data\n",encoding="utf-8")
    return TEMPLATE
def idx(rs):
    d={}
    for r in rs:
        t=u(r.get("ticker"))
        if t and t not in d: d[t]=r
    return d
def score(r,i):
    s=70
    s += 8 if fl(r.get("regular_market_price")) else -10
    mc=fl(r.get("market_cap")); s += 7 if mc and mc>1e9 else (3 if mc else -4)
    vol=fl(r.get("volume")); s += 5 if vol and vol>100000 else (2 if vol else -3)
    c20=fl(r.get("change_20d")); s += 3 if c20 is not None and -25<=c20<=40 else (-4 if c20 is not None else 0)
    s += max(0,5-i*0.1)
    return round(max(0,min(100,s)),2)
def validate_manual(rs):
    issues=[]
    if not rs: return [{"level":"ERROR","message":"manual_market_data.csv missing or empty"}]
    miss=[c for c in REQ if c not in rs[0]]
    if miss: return [{"level":"ERROR","message":f"Missing columns: {miss}"}]
    seen=set()
    for i,r in enumerate(rs,2):
        t=u(r.get("ticker"))
        if not t: issues.append({"level":"ERROR","row":i,"message":"Empty ticker"}); continue
        if t in seen: issues.append({"level":"WARNING","row":i,"ticker":t,"message":"Duplicate ticker"})
        seen.add(t)
        for c in ["price","market_cap","volume","average_volume","change_1d","change_5d","change_20d"]:
            if n(r.get(c)) and fl(r.get(c)) is None: issues.append({"level":"ERROR","row":i,"ticker":t,"message":f"Non numeric {c}"})
    return issues
def merge():
    OUTM.mkdir(parents=True,exist_ok=True); OUTS.mkdir(parents=True,exist_ok=True)
    universe=rows(UNIV); manual=rows(MANUAL); yf=rows(YFCACHE)
    issues=validate_manual(manual); blocking=[x for x in issues if x["level"]=="ERROR"]
    mb, yb = idx(manual), idx(yf)
    merged=[]; man=yc=fb=0; seen=set()
    for i,b in enumerate(universe,1):
        t=u(b.get("ticker"))
        if not t or t in seen: continue
        seen.add(t); provider="METADATA_SCORE_FALLBACK"; md={}
        if t in mb and not blocking:
            m=mb[t]; provider="MARKET_DATA_SCORE_MANUAL"; man+=1
            price=fl(m.get("price")); vol=fl(m.get("volume")); avg=fl(m.get("average_volume"))
            md={"regular_market_price":price or "","price_at_signal":price or "","market_cap":int(fl(m.get("market_cap")) or 0) if fl(m.get("market_cap")) is not None else "","volume":int(vol or 0) if vol is not None else "","average_volume":int(avg or 0) if avg is not None else "","relative_volume":round(vol/avg,2) if vol and avg else "","change_1d":fl(m.get("change_1d")) if fl(m.get("change_1d")) is not None else "","change_5d":fl(m.get("change_5d")) if fl(m.get("change_5d")) is not None else "","change_20d":fl(m.get("change_20d")) if fl(m.get("change_20d")) is not None else "","currency":n(m.get("currency")),"market_data_timestamp":n(m.get("as_of")),"market_data_status":"OK_MANUAL","market_data_provider":"manual_market_data.csv","error":""}
        elif t in yb and n(yb[t].get("regular_market_price")):
            y=yb[t]; provider="MARKET_DATA_SCORE_YFINANCE"; yc+=1
            md={k:y.get(k,"") for k in ["regular_market_price","price_at_signal","market_cap","volume","average_volume","relative_volume","change_1d","change_5d","change_20d","currency","market_data_timestamp","market_data_status","error"]}
            md["market_data_provider"]="yfinance_cache"
        else:
            fb+=1; md={"regular_market_price":"","price_at_signal":"","market_cap":"","volume":"","average_volume":"","relative_volume":"","change_1d":"","change_5d":"","change_20d":"","currency":"","market_data_timestamp":"","market_data_status":"NO_MARKET_DATA","market_data_provider":"metadata_fallback","error":"No usable market data"}
        row={"ticker":t,"name":n(b.get("name")) or t,"company_name":n(b.get("name")) or t,"exchange":u(b.get("exchange")),"country":u(b.get("country")),"sector":n(b.get("sector")),"industry":n(b.get("industry")),**md,"stage3_status":provider,"stage3_category":"market_data_provider_fallback","final_stage3_score":0,"risk_score":"","data_quality_score":100 if provider.startswith("MARKET_DATA") else 50,"data_quality_label":provider,"business_quality_score":"","financial_health_score":"","growth_score":"","valuation_score":"","moat_proxy_score":"","momentum_score":"","liquidity_score":"","score_method":METHOD,"source":"data/real/real_universe.csv + provider fallback","note":"Manual market data priority, yfinance cache second, metadata fallback last."}
        row["final_stage3_score"]=score(row,i); merged.append(row)
    merged.sort(key=lambda x:x["final_stage3_score"],reverse=True)
    summ={"phase":"v1.4E2","title":"Market Data Provider Fallback","status":"OK" if merged and not blocking else ("ERROR" if blocking else "EMPTY"),"created_at":now(),"rows_universe":len(universe),"rows_manual":len(manual),"rows_merged":len(merged),"manual_used":man,"yfinance_cache_used":yc,"fallback_used":fb,"top_tickers":", ".join(r["ticker"] for r in merged[:10]),"score_method":METHOD,"issues":issues,"openai_called":False,"broker_called":False,"pipeline_recalculated":False,"yfinance_called":False}
    wcsv(OUT_ROWS,merged); wcsv(OUT_CAND,merged); wcsv(OUT_ACTIVE,merged); wjson(OUT_SUM,summ)
    OUT_REP.write_text("# Scout Finance — v1.4E2 Market Data Provider Fallback Report\n\n"+json.dumps(summ,indent=2,ensure_ascii=False),encoding="utf-8")
    return summ
def main():
    p=argparse.ArgumentParser(); p.add_argument("--init-template",action="store_true"); p.add_argument("--merge",action="store_true"); a=p.parse_args()
    if a.init_template: print(f"Template ready: {init_template()}")
    if a.merge:
        s=merge(); print("Scout Finance — v1.4E2 Market Data Provider Fallback"); print("="*92)
        for k in ["status","rows_universe","rows_manual","rows_merged","manual_used","yfinance_cache_used","fallback_used","top_tickers","score_method"]:
            print(f"{k.replace('_',' ').title()}: {s[k]}")
        print("OpenAI called: False\nBroker called: False\nPipeline recalculated: False\nyfinance called: False\nReport: outputs/market_data/market_data_provider_fallback_report.md")
    if not a.init_template and not a.merge: p.print_help()
if __name__=="__main__": main()
