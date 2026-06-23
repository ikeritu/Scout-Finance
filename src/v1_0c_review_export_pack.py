from __future__ import annotations
import csv, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PHASE='v1.0C'
TITLE='Review Export Pack'
VERSION='v1.0.0-candidate-review-export-c'
PROJECT_ROOT=Path(__file__).resolve().parents[1]
OUT=PROJECT_ROOT/'outputs'/'scouting'
REVIEW=OUT/'manual_review'
STATE=REVIEW/'manual_review_state.json'
PACK_MD=REVIEW/'final_review_pack.md'
PACK_JSON=REVIEW/'final_review_pack.json'
PACK_CSV=REVIEW/'final_review_pack.csv'
SUMMARY=OUT/'v1_0c_review_export_pack_summary.json'
REPORT=OUT/'v1_0c_review_export_pack_report.md'
FLAGS={'openai_called':False,'api_called':False,'yfinance_called':False,'pipeline_recalculated':False,'app_modified':False,'filters_modified':False,'release_modified':False}
ORDER={'reviewed_watchlist':0,'needs_more_data':1,'reviewed_reject':2,'pending_review':3}

def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')

def read_json(path:Path, default:Any):
    if not path.exists(): return default
    return json.loads(path.read_text(encoding='utf-8'))

def write_json(path:Path, data:Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

def load_state()->Dict[str,Any]:
    state=read_json(STATE,{})
    if not isinstance(state,dict) or not isinstance(state.get('records'),dict):
        raise SystemExit('Missing or invalid manual review state. Run v1.0B first.')
    return state

def rows_from_state(state:Dict[str,Any])->List[Dict[str,Any]]:
    rows=[]
    for rec in state['records'].values():
        rows.append({
            'ticker':rec.get('ticker'),
            'company_name':rec.get('company_name'),
            'auto_verdict':rec.get('auto_verdict'),
            'manual_status':rec.get('manual_status'),
            'manual_notes':rec.get('manual_notes'),
            'reviewed_at':rec.get('reviewed_at'),
            'reviewer':rec.get('reviewer'),
            'red_flag_count':rec.get('red_flag_count'),
            'max_severity':rec.get('max_severity'),
            'has_high_or_critical':rec.get('has_high_or_critical'),
            'manual_review_required':rec.get('manual_review_required'),
            'not_financial_advice':rec.get('not_financial_advice'),
        })
    return sorted(rows, key=lambda r:(ORDER.get(str(r.get('manual_status')),99), str(r.get('ticker',''))))

def count_status(rows:List[Dict[str,Any]])->Dict[str,int]:
    counts={'reviewed_watchlist':0,'reviewed_reject':0,'needs_more_data':0,'pending_review':0}
    for row in rows:
        status=row.get('manual_status')
        if status in counts: counts[status]+=1
    return counts

def write_csv(path:Path, rows:List[Dict[str,Any]]):
    fields=['ticker','company_name','auto_verdict','manual_status','manual_notes','reviewed_at','reviewer','red_flag_count','max_severity','has_high_or_critical','manual_review_required','not_financial_advice']
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for r in rows: w.writerow({k:r.get(k) for k in fields})

def add_section(lines:List[str], title:str, rows:List[Dict[str,Any]]):
    lines += [f'## {title}','']
    if not rows:
        lines += ['_No records._','']; return
    lines += ['| Ticker | Company | Auto verdict | Red flags | Max severity | Manual note |','|---|---|---:|---:|---:|---|']
    for r in rows:
        note=str(r.get('manual_notes') or '').replace('\n',' ')
        lines.append(f"| {r.get('ticker')} | {r.get('company_name')} | {r.get('auto_verdict')} | {r.get('red_flag_count')} | {r.get('max_severity')} | {note} |")
    lines.append('')

def write_markdown(rows:List[Dict[str,Any]], counts:Dict[str,int], generated_at:str):
    watch=[r for r in rows if r.get('manual_status')=='reviewed_watchlist']
    need=[r for r in rows if r.get('manual_status')=='needs_more_data']
    reject=[r for r in rows if r.get('manual_status')=='reviewed_reject']
    pending=[r for r in rows if r.get('manual_status')=='pending_review']
    lines=['# Scout Finance — Final Review Pack','',f'Generated at: `{generated_at}`','','## Executive summary','',f'- Total reviewed records: {len(rows)}',f'- Watchlist: {counts["reviewed_watchlist"]}',f'- Rejected: {counts["reviewed_reject"]}',f'- Needs more data: {counts["needs_more_data"]}',f'- Pending review: {counts["pending_review"]}','','## Safety and scope','','- This is not financial advice.','- Manual review is required.','- Automatic verdicts are inputs, not final decisions.','- No OpenAI calls were made.','- No API calls were made.','- No yfinance calls were made.','- No pipeline recalculation was performed.','']
    add_section(lines,'Watchlist',watch)
    add_section(lines,'Needs more data',need)
    add_section(lines,'Rejected',reject)
    add_section(lines,'Pending review',pending)
    lines += ['## Consolidated table','','| Ticker | Status | Auto verdict | Red flags | Max severity | Reviewed at |','|---|---|---:|---:|---:|---|']
    for r in rows:
        lines.append(f"| {r.get('ticker')} | {r.get('manual_status')} | {r.get('auto_verdict')} | {r.get('red_flag_count')} | {r.get('max_severity')} | {r.get('reviewed_at')} |")
    lines += ['','## Source files','','- `outputs/scouting/manual_review/manual_review_state.json`','- `outputs/scouting/manual_review/manual_review_summary.md`','']
    PACK_MD.write_text('\n'.join(lines), encoding='utf-8')

def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    state=load_state()
    rows=rows_from_state(state)
    counts=count_status(rows)
    generated_at=now()
    write_csv(PACK_CSV, rows)
    write_markdown(rows, counts, generated_at)
    pack={'phase':PHASE,'title':TITLE,'version':VERSION,'generated_at':generated_at,'source_state':str(STATE.relative_to(PROJECT_ROOT)),'counts':counts,'records':rows,**FLAGS}
    write_json(PACK_JSON, pack)
    summary={'phase':PHASE,'title':TITLE,'version':VERSION,'status':'OK','created_at':generated_at,'records_total':len(rows),'watchlist_count':counts['reviewed_watchlist'],'reject_count':counts['reviewed_reject'],'needs_more_data_count':counts['needs_more_data'],'pending_review_count':counts['pending_review'],'outputs':{'final_review_pack_md':str(PACK_MD.relative_to(PROJECT_ROOT)),'final_review_pack_json':str(PACK_JSON.relative_to(PROJECT_ROOT)),'final_review_pack_csv':str(PACK_CSV.relative_to(PROJECT_ROOT))},**FLAGS,'next':'v1.0D — Freeze v1.0.0-candidate'}
    write_json(SUMMARY, summary)
    report=['# v1.0C — Review Export Pack','','Status: **OK**','',f'- Total records: {len(rows)}',f'- Watchlist: {counts["reviewed_watchlist"]}',f'- Rejected: {counts["reviewed_reject"]}',f'- Needs more data: {counts["needs_more_data"]}',f'- Pending review: {counts["pending_review"]}','','## Outputs','']
    for v in summary['outputs'].values(): report.append(f'- `{v}`')
    report += ['','## Safety','','- OpenAI called: False','- API called: False','- yfinance called: False','- Pipeline recalculated: False','- Not financial advice.','']
    REPORT.write_text('\n'.join(report), encoding='utf-8')
    print('Scout Finance — v1.0C Review Export Pack')
    print('='*92)
    print('Status: OK')
    print(f'Records total: {len(rows)}')
    print(f'Watchlist: {counts["reviewed_watchlist"]}')
    print(f'Rejected: {counts["reviewed_reject"]}')
    print(f'Needs more data: {counts["needs_more_data"]}')
    print(f'Pending review: {counts["pending_review"]}')
    print('OpenAI called: False')
    print('API called: False')
    print('yfinance called: False')
    print('Pipeline recalculated: False')
    print('Final review pack generated.')

if __name__=='__main__': main()
