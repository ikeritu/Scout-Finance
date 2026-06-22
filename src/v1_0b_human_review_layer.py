from __future__ import annotations
import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path

PHASE="v1.0B"
VERSION="v1.0.0-candidate-human-review-b"
PROJECT_ROOT=Path(__file__).resolve().parents[1]
OUT=PROJECT_ROOT/"outputs"/"scouting"
REVIEW=OUT/"manual_review"
STATE=REVIEW/"manual_review_state.json"
ALLOWED={"pending_review","reviewed_watchlist","reviewed_reject","needs_more_data"}
FLAGS={"openai_called":False,"api_called":False,"yfinance_called":False,"pipeline_recalculated":False,"app_modified":False,"filters_modified":False,"release_modified":False}

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")

def read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def load_state():
    state=read_json(STATE,{})
    if not isinstance(state,dict) or not isinstance(state.get("records"),dict):
        raise SystemExit("Missing or invalid outputs/scouting/manual_review/manual_review_state.json. Run v1.0A first.")
    return state

def save_state(state):
    state["updated_at"]=now()
    write_json(STATE,state)

def update(state,ticker,status,note,reviewer):
    ticker=ticker.strip().upper()
    records=state["records"]
    if ticker not in records:
        raise SystemExit("Ticker not found: "+ticker+". Available: "+", ".join(sorted(records)))
    if status and status not in ALLOWED:
        raise SystemExit("Invalid status: "+status)
    rec=records[ticker]
    if status:
        rec["manual_status"]=status
    if note is not None:
        rec["manual_notes"]=note
    rec["reviewed_at"]=now()
    rec["reviewer"]=reviewer
    rec["manual_review_required"]=True
    rec["not_financial_advice"]=True
    records[ticker]=rec
    return rec

def rows_for(state,status):
    rows=[]
    for rec in state["records"].values():
        if rec.get("manual_status")==status:
            rows.append({
                "ticker":rec.get("ticker"),
                "company_name":rec.get("company_name"),
                "auto_verdict":rec.get("auto_verdict"),
                "manual_status":rec.get("manual_status"),
                "manual_notes":rec.get("manual_notes"),
                "reviewed_at":rec.get("reviewed_at"),
                "reviewer":rec.get("reviewer"),
                "red_flag_count":rec.get("red_flag_count"),
                "max_severity":rec.get("max_severity"),
                "has_high_or_critical":rec.get("has_high_or_critical"),
                "manual_review_required":rec.get("manual_review_required"),
                "not_financial_advice":rec.get("not_financial_advice"),
            })
    return sorted(rows,key=lambda x:str(x.get("ticker","")))

def write_csv(path,rows):
    fields=["ticker","company_name","auto_verdict","manual_status","manual_notes","reviewed_at","reviewer","red_flag_count","max_severity","has_high_or_critical","manual_review_required","not_financial_advice"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k:r.get(k) for k in fields})

def export_all(state):
    watch=rows_for(state,"reviewed_watchlist")
    rej=rows_for(state,"reviewed_reject")
    need=rows_for(state,"needs_more_data")
    pending=rows_for(state,"pending_review")
    write_csv(REVIEW/"reviewed_watchlist.csv",watch)
    write_csv(REVIEW/"reviewed_reject.csv",rej)
    write_csv(REVIEW/"needs_more_data.csv",need)
    lines=["# Scout Finance — Manual Review Summary","","Status: **OK**","","## Safety","","- Not financial advice.","- Manual review required.","- OpenAI called: `False`","- API called: `False`","- yfinance called: `False`","- Pipeline recalculated: `False`","","## Counts","",f"- Watchlist: {len(watch)}",f"- Rejected: {len(rej)}",f"- Needs more data: {len(need)}",f"- Pending review: {len(pending)}",""]
    for title,rows in [("Reviewed watchlist",watch),("Reviewed reject",rej),("Needs more data",need),("Pending review",pending)]:
        lines += [f"## {title}",""]
        if not rows:
            lines += ["_No records._",""]
            continue
        lines += ["| Ticker | Company | Auto verdict | Red flags | Max severity | Notes |","|---|---|---:|---:|---:|---|"]
        for r in rows:
            note=str(r.get("manual_notes") or "").replace("\n"," ")
            lines.append(f"| {r.get('ticker')} | {r.get('company_name')} | {r.get('auto_verdict')} | {r.get('red_flag_count')} | {r.get('max_severity')} | {note} |")
        lines.append("")
    (REVIEW/"manual_review_summary.md").write_text("\n".join(lines),encoding="utf-8")
    summary={"phase":PHASE,"title":"Human Review Layer","version":VERSION,"status":"OK","created_at":now(),"source_state":str(STATE.relative_to(PROJECT_ROOT)),"records_total":len(state["records"]),"manual_status_allowed_values":sorted(ALLOWED),"watchlist_count":len(watch),"reject_count":len(rej),"needs_more_data_count":len(need),"pending_review_count":len(pending),"outputs":{"reviewed_watchlist_csv":"outputs/scouting/manual_review/reviewed_watchlist.csv","reviewed_reject_csv":"outputs/scouting/manual_review/reviewed_reject.csv","needs_more_data_csv":"outputs/scouting/manual_review/needs_more_data.csv","manual_review_summary_md":"outputs/scouting/manual_review/manual_review_summary.md"},**FLAGS,"next":"v1.0C — Watchlist and reject export refinement"}
    write_json(OUT/"v1_0b_human_review_layer_summary.json",summary)
    report=["# v1.0B — Human Review Layer","","Status: **OK**","",f"- Total records: {summary['records_total']}",f"- Watchlist: {summary['watchlist_count']}",f"- Rejected: {summary['reject_count']}",f"- Needs more data: {summary['needs_more_data_count']}",f"- Pending review: {summary['pending_review_count']}","","## Safety","","- OpenAI called: False","- API called: False","- yfinance called: False","- Pipeline recalculated: False","- Not financial advice.","","## Outputs",""]
    for v in summary["outputs"].values():
        report.append(f"- `{v}`")
    (OUT/"v1_0b_human_review_layer_report.md").write_text("\n".join(report),encoding="utf-8")
    return summary

def show(state):
    print("Ticker | Auto verdict | Red flags | Max severity | Manual status | Notes")
    print("-"*92)
    for rec in sorted(state["records"].values(),key=lambda r:str(r.get("ticker",""))):
        note=str(rec.get("manual_notes") or "")
        if len(note)>60: note=note[:60]+"..."
        print(f"{rec.get('ticker')} | {rec.get('auto_verdict')} | {rec.get('red_flag_count')} | {rec.get('max_severity')} | {rec.get('manual_status')} | {note}")

def main():
    parser=argparse.ArgumentParser(description="Scout Finance v1.0B Human Review Layer")
    parser.add_argument("--list",action="store_true")
    parser.add_argument("--ticker")
    parser.add_argument("--status",choices=sorted(ALLOWED))
    parser.add_argument("--note")
    parser.add_argument("--reviewer",default="local_user")
    parser.add_argument("--export",action="store_true")
    args=parser.parse_args()
    state=load_state()
    if args.ticker:
        rec=update(state,args.ticker,args.status,args.note,args.reviewer)
        save_state(state)
        print(f"Updated {rec.get('ticker')}: {rec.get('manual_status')}")
    summary=export_all(state)
    if args.list or not args.ticker:
        show(state)
    print()
    print("Scout Finance — v1.0B Human Review Layer")
    print("="*92)
    print("Status: OK")
    print(f"Records total: {summary['records_total']}")
    print(f"Watchlist: {summary['watchlist_count']}")
    print(f"Rejected: {summary['reject_count']}")
    print(f"Needs more data: {summary['needs_more_data_count']}")
    print(f"Pending review: {summary['pending_review_count']}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")

if __name__=="__main__":
    main()
