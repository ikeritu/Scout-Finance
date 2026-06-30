from __future__ import annotations
import argparse, csv, json, shutil, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"real"; OUTS=ROOT/"outputs"/"scouting"; OUTSC=ROOT/"outputs"/"scoring"; OUTM=ROOT/"outputs"/"market_data"; OUT=ROOT/"outputs"/"scale_tests"
REAL=DATA/"real_universe.csv"; MANUAL=DATA/"manual_market_data.csv"; BAK=OUT/"backups"
SUMMARY=OUT/"scale_test_summary.json"; REPORT=OUT/"scale_test_report.md"
SIZES=[20,50,100]

# v1.5C1: restore both input CSVs and active generated outputs after the scale test.
FILES_TO_RESTORE=[
    REAL,
    MANUAL,
    OUTS/"active_real_universe_top_candidates.csv",
    OUTS/"real_universe_market_data_candidates.csv",
    OUTS/"local_score_v0_candidates.csv",
    OUTS/"ranking_explainability_candidates.csv",
    OUTM/"market_data_provider_fallback_rows.csv",
    OUTM/"market_data_provider_fallback_summary.json",
    OUTM/"market_data_provider_fallback_report.md",
    OUTSC/"local_score_v0_breakdown.csv",
    OUTSC/"local_score_v0_summary.json",
    OUTSC/"local_score_v0_report.md",
    OUTSC/"ranking_explainability_factors.csv",
    OUTSC/"ranking_explainability_summary.json",
    OUTSC/"ranking_explainability_report.md",
]

SEEDS=[
("AAPL","Apple Inc.","NASDAQ","US","Technology","Consumer Electronics",195,3000000000000,50000000,55000000,0.5,1.2,3.5,"USD"),
("MSFT","Microsoft Corporation","NASDAQ","US","Technology","Software",430,3200000000000,25000000,28000000,0.3,0.9,2.8,"USD"),
("ASML","ASML Holding N.V.","NASDAQ","NL","Technology","Semiconductor Equipment",750,300000000000,1200000,1500000,-0.2,1.5,4.1,"EUR"),
("NVDA","NVIDIA Corporation","NASDAQ","US","Technology","Semiconductors",120,2900000000000,30000000,35000000,0.8,2.0,5.5,"USD"),
("GOOGL","Alphabet Inc.","NASDAQ","US","Communication Services","Internet Content",175,2100000000000,22000000,24000000,0.1,0.7,2.1,"USD"),
("AMZN","Amazon.com Inc.","NASDAQ","US","Consumer Cyclical","Internet Retail",185,1900000000000,35000000,36000000,0.4,1.0,3.0,"USD"),
("META","Meta Platforms Inc.","NASDAQ","US","Communication Services","Internet Content",500,1250000000000,14000000,16000000,0.2,1.1,4.0,"USD"),
("TSLA","Tesla Inc.","NASDAQ","US","Consumer Cyclical","Auto Manufacturers",250,800000000000,90000000,85000000,-1.5,-3.0,8.0,"USD"),
("BRK-B","Berkshire Hathaway Inc.","NYSE","US","Financial Services","Insurance",410,880000000000,4000000,4500000,0.1,0.5,1.2,"USD"),
("LLY","Eli Lilly and Company","NYSE","US","Healthcare","Drug Manufacturers",900,850000000000,3000000,3200000,0.6,1.8,6.0,"USD"),
("V","Visa Inc.","NYSE","US","Financial Services","Credit Services",280,560000000000,6000000,6500000,0.2,0.9,2.5,"USD"),
("JPM","JPMorgan Chase & Co.","NYSE","US","Financial Services","Banks",200,580000000000,9000000,9500000,0.1,0.6,2.0,"USD"),
("UNH","UnitedHealth Group Inc.","NYSE","US","Healthcare","Healthcare Plans",520,480000000000,3500000,3700000,-0.1,0.4,1.5,"USD"),
("XOM","Exxon Mobil Corporation","NYSE","US","Energy","Oil & Gas",115,460000000000,17000000,18000000,0.2,0.8,1.9,"USD"),
("MA","Mastercard Incorporated","NYSE","US","Financial Services","Credit Services",450,420000000000,2500000,2800000,0.2,0.9,2.6,"USD"),
("AVGO","Broadcom Inc.","NASDAQ","US","Technology","Semiconductors",1700,780000000000,2500000,3000000,1.1,3.0,7.5,"USD"),
("HD","The Home Depot Inc.","NYSE","US","Consumer Cyclical","Home Improvement",350,350000000000,4000000,4500000,0.1,0.7,1.8,"USD"),
("COST","Costco Wholesale Corporation","NASDAQ","US","Consumer Defensive","Discount Stores",850,380000000000,1800000,2000000,0.2,0.8,2.4,"USD"),
("ADBE","Adobe Inc.","NASDAQ","US","Technology","Software",530,235000000000,3000000,3300000,0.4,1.1,3.2,"USD"),
("AMD","Advanced Micro Devices Inc.","NASDAQ","US","Technology","Semiconductors",160,260000000000,50000000,52000000,-0.4,1.6,5.8,"USD"),
]

def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
def rows(p:Path):
    if not p.exists(): return []
    with p.open("r",encoding="utf-8-sig",newline="") as f: return [dict(r) for r in csv.DictReader(f)]
def wcsv(p:Path, rs:list[dict[str,Any]], fields:list[str]):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rs)
def kb(p:Path): return round(p.stat().st_size/1024,2) if p.exists() else 0

def safe_backup_name(path:Path)->str:
    try:
        rel=path.relative_to(ROOT)
    except Exception:
        rel=path.name
    return str(rel).replace("\\","__").replace("/","__")

def backup():
    BAK.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for p in FILES_TO_RESTORE:
        target=BAK/safe_backup_name(p)
        if p.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,target)
            manifest.append({"path":str(p.relative_to(ROOT)),"backup":target.name,"existed":True})
        else:
            manifest.append({"path":str(p.relative_to(ROOT)),"backup":target.name,"existed":False})
    (BAK/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")

def restore():
    manifest_path=BAK/"manifest.json"
    if not manifest_path.exists():
        return
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest:
        p=ROOT/item["path"]
        b=BAK/item["backup"]
        if item.get("existed") and b.exists():
            p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(b,p)
        elif not item.get("existed") and p.exists():
            # The scale test created a file that did not exist before; remove it.
            p.unlink()

def make(size:int):
    u=[]; m=[]
    for i in range(size):
        s=SEEDS[i%len(SEEDS)]; extra="" if i<len(SEEDS) else f"T{i+1}"
        ticker=s[0] if not extra else f"{s[0]}{extra}"
        u.append({"ticker":ticker,"name":s[1] if not extra else f"{s[1]} Scale {i+1}","exchange":s[2],"country":s[3],"sector":s[4],"industry":s[5]})
        m.append({"ticker":ticker,"price":round(s[6]*(1+(i%7)*0.01),2),"market_cap":int(s[7]*(1+(i%5)*0.02)),"volume":int(s[8]*(1+(i%9)*0.03)),"average_volume":int(s[9]*(1+(i%6)*0.02)),"change_1d_pct":s[10],"change_5d_pct":s[11],"change_20d_pct":s[12],"currency":s[13],"as_of":"2026-06-29","source_note":"scale test synthetic"})
    return u,m

def run_one(size:int):
    u,m=make(size)
    wcsv(REAL,u,["ticker","name","exchange","country","sector","industry"])
    wcsv(MANUAL,m,["ticker","price","market_cap","volume","average_volume","change_1d_pct","change_5d_pct","change_20d_pct","currency","as_of","source_note"])
    errs=[]; t=time.perf_counter()
    try:
        from src.market_data_provider_fallback import merge
        t0=time.perf_counter(); fs=merge(); ft=round(time.perf_counter()-t0,4)
    except Exception as e:
        fs={}; ft=0; errs.append(f"fallback:{e}")
    try:
        from src.local_scoring_v0 import run_score
        t0=time.perf_counter(); ss=run_score(); st=round(time.perf_counter()-t0,4)
    except Exception as e:
        ss={}; st=0; errs.append(f"score:{e}")
    try:
        from src.ranking_explainability import run_explain
        t0=time.perf_counter(); es=run_explain(); et=round(time.perf_counter()-t0,4)
    except Exception as e:
        es={}; et=0; errs.append(f"explain:{e}")
    total=round(time.perf_counter()-t,4)
    active=OUTS/"active_real_universe_top_candidates.csv"
    nrows=len(rows(active))
    d=OUT/f"size_{size}"; d.mkdir(parents=True,exist_ok=True)
    for p in [active, OUTS/"local_score_v0_candidates.csv", OUTS/"ranking_explainability_candidates.csv", OUTSC/"local_score_v0_breakdown.csv", OUTSC/"ranking_explainability_factors.csv"]:
        if p.exists(): shutil.copy2(p,d/p.name)
    return {"size":size,"status":"OK" if not errs and nrows==size else "ERROR","active_rows":nrows,"fallback_status":fs.get("status",""),"score_status":ss.get("status",""),"explain_status":es.get("status",""),"fallback_seconds":ft,"score_seconds":st,"explain_seconds":et,"total_seconds":total,"active_kb":kb(active),"errors":errs}

def run_scale_test():
    OUT.mkdir(parents=True,exist_ok=True)
    before_active_rows=len(rows(OUTS/"active_real_universe_top_candidates.csv"))
    backup(); start=time.perf_counter(); runs=[]; restore_ok=False; after_active_rows=None
    try:
        for size in SIZES: runs.append(run_one(size))
    finally:
        restore()
        after_active_rows=len(rows(OUTS/"active_real_universe_top_candidates.csv"))
        restore_ok=(after_active_rows==before_active_rows)
    total=round(time.perf_counter()-start,4)
    summary={"phase":"v1.5C1","title":"Real Universe Scale Test Output Restore Hotfix","status":"OK" if all(r["status"]=="OK" for r in runs) and restore_ok else "ERROR","created_at":now(),"sizes":SIZES,"max_size_tested":max(SIZES),"total_seconds":total,"before_active_rows":before_active_rows,"after_active_rows":after_active_rows,"restore_ok":restore_ok,"runs":runs,"openai_called":False,"broker_called":False,"pipeline_recalculated":False,"yfinance_called":False}
    SUMMARY.write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    lines=["# Scout Finance — v1.5C1 Real Universe Scale Test Output Restore Hotfix Report","","Status: **"+summary["status"]+"**",f"Restore OK: `{restore_ok}`",f"Active rows before/after: `{before_active_rows}` / `{after_active_rows}`","","| Size | Status | Active rows | Fallback s | Score s | Explain s | Total s | Active KB | Errors |","|---:|---|---:|---:|---:|---:|---:|---:|---|"]
    for r in runs: lines.append(f"| {r['size']} | {r['status']} | {r['active_rows']} | {r['fallback_seconds']} | {r['score_seconds']} | {r['explain_seconds']} | {r['total_seconds']} | {r['active_kb']} | {'; '.join(r['errors']) or '-'} |")
    lines += ["","Controls: OpenAI=False, Broker=False, Pipeline=False, yfinance=False."]
    REPORT.write_text("\n".join(lines),encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser(); p.add_argument("--run",action="store_true"); a=p.parse_args()
    if not a.run: p.print_help(); return
    s=run_scale_test()
    print("Scout Finance — v1.5C1 Real Universe Scale Test Output Restore Hotfix"); print("="*92)
    print(f"Status: {s['status']}"); print(f"Sizes: {s['sizes']}"); print(f"Max size tested: {s['max_size_tested']}"); print(f"Total seconds: {s['total_seconds']}"); print(f"Restore OK: {s['restore_ok']}"); print(f"Active rows before/after: {s['before_active_rows']} / {s['after_active_rows']}")
    print("OpenAI called: False\nBroker called: False\nPipeline recalculated: False\nyfinance called: False\nReport: outputs/scale_tests/scale_test_report.md")
if __name__=="__main__": main()
