from __future__ import annotations
import csv,json
from pathlib import Path
PHASE='v1.0C'
def root(): return Path(__file__).resolve().parents[1]
def read_json(p): return json.loads(p.read_text(encoding='utf-8'))
def ok(m): print('OK   '+m)
def fail(m): print('FAIL '+m); raise SystemExit(1)
def require(c,m): ok(m) if c else fail(m)
def require_file(p): require(p.exists(),f'File exists: {p}')
def csv_rows(p):
    with p.open('r',encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def main():
    r=root(); out=r/'outputs'/'scouting'; review=out/'manual_review'
    print('Scout Finance — v1.0C Review Export Pack checker')
    print('='*92)
    required=[r/'src'/'v1_0c_review_export_pack.py',r/'scripts'/'check_v1_0c_review_export_pack.py',review/'manual_review_state.json',review/'final_review_pack.md',review/'final_review_pack.json',review/'final_review_pack.csv',out/'v1_0c_review_export_pack_summary.json',out/'v1_0c_review_export_pack_report.md']
    for p in required: require_file(p)
    summary=read_json(out/'v1_0c_review_export_pack_summary.json')
    pack=read_json(review/'final_review_pack.json')
    rows=csv_rows(review/'final_review_pack.csv')
    require(summary.get('phase')==PHASE,'Summary phase OK')
    require(summary.get('status')=='OK','Summary status OK')
    require(pack.get('phase')==PHASE,'Pack phase OK')
    require(len(rows)==summary.get('records_total'),'CSV rows match summary')
    require(len(pack.get('records',[]))==summary.get('records_total'),'JSON records match summary')
    counts=pack.get('counts',{})
    require(counts.get('reviewed_watchlist')==summary.get('watchlist_count'),'Watchlist count OK')
    require(counts.get('reviewed_reject')==summary.get('reject_count'),'Reject count OK')
    require(counts.get('needs_more_data')==summary.get('needs_more_data_count'),'Needs more data count OK')
    require(counts.get('pending_review')==summary.get('pending_review_count'),'Pending count OK')
    for k in ['openai_called','api_called','yfinance_called','pipeline_recalculated','app_modified','filters_modified','release_modified']:
        require(summary.get(k) is False,f'Summary control OK: {k}=False')
        require(pack.get(k) is False,f'Pack control OK: {k}=False')
    md=(review/'final_review_pack.md').read_text(encoding='utf-8').lower()
    for text in ['final review pack','executive summary','watchlist','needs more data','rejected','consolidated table','not financial advice']:
        require(text in md,f'Markdown contains: {text}')
    print(); print('Result'); print('-'*92); print('OK   v1.0C Review Export Pack is valid')
if __name__=='__main__': main()
