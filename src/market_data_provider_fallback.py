from __future__ import annotations
import argparse,csv,json,math
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'real'; OUTM=ROOT/'outputs'/'market_data'; OUTS=ROOT/'outputs'/'scouting'
UNIV=DATA/'real_universe.csv'; TEMPLATE=DATA/'manual_market_data_template.csv'; MANUAL=DATA/'manual_market_data.csv'; YFCACHE=OUTM/'real_market_data_rows.csv'
OUT_ROWS=OUTM/'market_data_provider_fallback_rows.csv'; OUT_SUM=OUTM/'market_data_provider_fallback_summary.json'; OUT_REP=OUTM/'market_data_provider_fallback_report.md'; OUT_CAND=OUTS/'real_universe_market_data_candidates.csv'; OUT_ACTIVE=OUTS/'active_real_universe_top_candidates.csv'
METHOD='market_data_provider_fallback_v0_pct_normalized'; PCT_INPUT_MODE='human_percent'
REQ_BASE=['ticker','price','market_cap','volume','average_volume','currency','as_of']; PCT_NEW=['change_1d_pct','change_5d_pct','change_20d_pct']; PCT_OLD=['change_1d','change_5d','change_20d']
def now(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
def n(v:Any)->str: return str(v or '').strip()
def u(v:Any)->str: return n(v).upper().replace('$','')
def fl(v:Any):
    try:
        if n(v)=='': return None
        x=float(v); return None if math.isnan(x) else x
    except Exception: return None
def pct_to_ratio(v:Any):
    x=fl(v); return '' if x is None else round(x/100.0,6)
def rows(p:Path):
    if not p.exists(): return []
    with p.open('r',encoding='utf-8-sig',newline='') as f: return [dict(r) for r in csv.DictReader(f)]
def wcsv(p:Path,rs:list[dict[str,Any]]):
    p.parent.mkdir(parents=True,exist_ok=True)
    if not rs: p.write_text('',encoding='utf-8'); return
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0].keys())); w.writeheader(); w.writerows(rs)
def wjson(p:Path,d:Any): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
def init_template():
    DATA.mkdir(parents=True,exist_ok=True)
    TEMPLATE.write_text('ticker,price,market_cap,volume,average_volume,change_1d_pct,change_5d_pct,change_20d_pct,currency,as_of,source_note\nAAPL,195.00,3000000000000,50000000,55000000,0.5,1.2,3.5,USD,2026-06-29,manual test data; pct fields use human percent units\nMSFT,430.00,3200000000000,25000000,28000000,0.3,0.9,2.8,USD,2026-06-29,manual test data; pct fields use human percent units\nASML,750.00,300000000000,1200000,1500000,-0.2,1.5,4.1,EUR,2026-06-29,manual test data; pct fields use human percent units\n',encoding='utf-8')
    return TEMPLATE
def idx(rs):
    d={}
    for r in rs:
        t=u(r.get('ticker'))
        if t and t not in d: d[t]=r
    return d
def getpct(r,new,old): return r.get(new) if new in r else r.get(old)
def validate_manual(rs):
    issues=[]
    if not rs: return [{'level':'ERROR','message':'manual_market_data.csv missing or empty'}]
    cols=set(rs[0].keys()); miss=[c for c in REQ_BASE if c not in cols]
    if miss: issues.append({'level':'ERROR','message':f'Missing base columns: {miss}'})
    has_new=all(c in cols for c in PCT_NEW); has_old=all(c in cols for c in PCT_OLD)
    if not has_new and not has_old: issues.append({'level':'ERROR','message':'Missing percent columns. Use change_1d_pct/change_5d_pct/change_20d_pct.'})
    if any(i['level']=='ERROR' for i in issues): return issues
    seen=set()
    for i,r in enumerate(rs,2):
        t=u(r.get('ticker'))
        if not t: issues.append({'level':'ERROR','row':i,'message':'Empty ticker'}); continue
        if t in seen: issues.append({'level':'WARNING','row':i,'ticker':t,'message':'Duplicate ticker'})
        seen.add(t)
        for c in ['price','market_cap','volume','average_volume']:
            if n(r.get(c)) and fl(r.get(c)) is None: issues.append({'level':'ERROR','row':i,'ticker':t,'message':f'Non numeric {c}'})
        for new,old in zip(PCT_NEW,PCT_OLD):
            val=getpct(r,new,old); parsed=fl(val)
            if n(val) and parsed is None: issues.append({'level':'ERROR','row':i,'ticker':t,'message':f'Non numeric {new}'})
            elif parsed is not None and abs(parsed)>100: issues.append({'level':'WARNING','row':i,'ticker':t,'message':f'Suspicious percentage {new}={parsed}. Manual values are human percent units.'})
        if has_old and not has_new: issues.append({'level':'WARNING','row':i,'ticker':t,'message':'Legacy change columns detected; interpreted as human percentages.'})
    return issues
def score(r,i):
    s=70; s+=8 if fl(r.get('regular_market_price')) else -10
    mc=fl(r.get('market_cap')); s+=7 if mc and mc>1e9 else (3 if mc else -4)
    vol=fl(r.get('volume')); s+=5 if vol and vol>100000 else (2 if vol else -3)
    c20=fl(r.get('change_20d'))
    if c20 is not None: s+=3 if -25 <= c20*100 <= 40 else -4
    s+=max(0,5-i*0.1); return round(max(0,min(100,s)),2)
def merge():
    OUTM.mkdir(parents=True,exist_ok=True); OUTS.mkdir(parents=True,exist_ok=True)
    universe=rows(UNIV); manual=rows(MANUAL); yf=rows(YFCACHE)
    issues=validate_manual(manual); blocking=[x for x in issues if x['level']=='ERROR']; mb=idx(manual); yb=idx(yf)
    merged=[]; man=yc=fb=0; seen=set()
    for i,b in enumerate(universe,1):
        t=u(b.get('ticker'))
        if not t or t in seen: continue
        seen.add(t); provider='METADATA_SCORE_FALLBACK'; md={}
        if t in mb and not blocking:
            m=mb[t]; provider='MARKET_DATA_SCORE_MANUAL'; man+=1
            price=fl(m.get('price')); vol=fl(m.get('volume')); avg=fl(m.get('average_volume')); mcap=fl(m.get('market_cap'))
            c1=pct_to_ratio(getpct(m,'change_1d_pct','change_1d')); c5=pct_to_ratio(getpct(m,'change_5d_pct','change_5d')); c20=pct_to_ratio(getpct(m,'change_20d_pct','change_20d'))
            md={'regular_market_price':price or '','price_at_signal':price or '','market_cap':int(mcap or 0) if mcap is not None else '','volume':int(vol or 0) if vol is not None else '','average_volume':int(avg or 0) if avg is not None else '','relative_volume':round(vol/avg,2) if vol and avg else '','change_1d':c1,'change_5d':c5,'change_20d':c20,'change_1d_pct_input':getpct(m,'change_1d_pct','change_1d'),'change_5d_pct_input':getpct(m,'change_5d_pct','change_5d'),'change_20d_pct_input':getpct(m,'change_20d_pct','change_20d'),'currency':n(m.get('currency')),'market_data_timestamp':n(m.get('as_of')),'market_data_status':'OK_MANUAL','market_data_provider':'manual_market_data.csv','percent_input_mode':PCT_INPUT_MODE,'error':''}
        elif t in yb and n(yb[t].get('regular_market_price')):
            y=yb[t]; provider='MARKET_DATA_SCORE_YFINANCE'; yc+=1
            md={k:y.get(k,'') for k in ['regular_market_price','price_at_signal','market_cap','volume','average_volume','relative_volume','change_1d','change_5d','change_20d','currency','market_data_timestamp','market_data_status','error']}; md['market_data_provider']='yfinance_cache'; md['percent_input_mode']='provider_ratio'
        else:
            fb+=1; md={'regular_market_price':'','price_at_signal':'','market_cap':'','volume':'','average_volume':'','relative_volume':'','change_1d':'','change_5d':'','change_20d':'','currency':'','market_data_timestamp':'','market_data_status':'NO_MARKET_DATA','market_data_provider':'metadata_fallback','percent_input_mode':'','error':'No usable market data'}
        row={'ticker':t,'name':n(b.get('name')) or t,'company_name':n(b.get('name')) or t,'exchange':u(b.get('exchange')),'country':u(b.get('country')),'sector':n(b.get('sector')),'industry':n(b.get('industry')),**md,'stage3_status':provider,'stage3_category':'market_data_provider_fallback','final_stage3_score':0,'risk_score':'','data_quality_score':100 if provider.startswith('MARKET_DATA') else 50,'data_quality_label':provider,'business_quality_score':'','financial_health_score':'','growth_score':'','valuation_score':'','moat_proxy_score':'','momentum_score':'','liquidity_score':'','score_method':METHOD,'source':'data/real/real_universe.csv + provider fallback','note':'Manual market data priority. Percent inputs normalized from human percent units to app ratios.'}
        row['final_stage3_score']=score(row,i); merged.append(row)
    merged.sort(key=lambda x:x['final_stage3_score'], reverse=True)
    summ={'phase':'v1.4F2','title':'Manual Market Data Percent Normalization','status':'OK' if merged and not blocking else ('ERROR' if blocking else 'EMPTY'),'created_at':now(),'rows_universe':len(universe),'rows_manual':len(manual),'rows_merged':len(merged),'manual_used':man,'yfinance_cache_used':yc,'fallback_used':fb,'top_tickers':', '.join(r['ticker'] for r in merged[:10]),'score_method':METHOD,'percent_input_mode':PCT_INPUT_MODE,'issues':issues,'openai_called':False,'broker_called':False,'pipeline_recalculated':False,'yfinance_called':False}
    wcsv(OUT_ROWS,merged); wcsv(OUT_CAND,merged); wcsv(OUT_ACTIVE,merged); wjson(OUT_SUM,summ); OUT_REP.write_text('# Scout Finance — v1.4F2 Manual Market Data Percent Normalization Report\n\n'+json.dumps(summ,indent=2,ensure_ascii=False),encoding='utf-8'); return summ
def main():
    p=argparse.ArgumentParser(); p.add_argument('--init-template',action='store_true'); p.add_argument('--merge',action='store_true'); a=p.parse_args()
    if a.init_template: print(f'Template ready: {init_template()}')
    if a.merge:
        s=merge(); print('Scout Finance — v1.4F2 Manual Market Data Percent Normalization'); print('='*92)
        for label,key in [('Status','status'),('Rows universe','rows_universe'),('Rows manual','rows_manual'),('Rows merged','rows_merged'),('Manual used','manual_used'),('yfinance cache used','yfinance_cache_used'),('Metadata fallback used','fallback_used'),('Top tickers','top_tickers'),('Score method','score_method'),('Percent input mode','percent_input_mode')]: print(f'{label}: {s[key]}')
        print('OpenAI called: False\nBroker called: False\nPipeline recalculated: False\nyfinance called: False\nReport: outputs/market_data/market_data_provider_fallback_report.md')
    if not a.init_template and not a.merge: p.print_help()
if __name__=='__main__': main()
