from __future__ import annotations
import csv, json
from pathlib import Path

PHASE="v1.0B"

def root():
    return Path(__file__).resolve().parents[1]

def read_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def ok(m): print("OK   "+m)

def fail(m):
    print("FAIL "+m)
    raise SystemExit(1)

def require(c,m):
    ok(m) if c else fail(m)

def require_file(p):
    require(p.exists(),f"File exists: {p}")

def csv_rows(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def main():
    r=root(); out=r/"outputs"/"scouting"; review=out/"manual_review"
    print("Scout Finance — v1.0B Human Review Layer checker")
    print("="*92)
    required=[r/"src"/"v1_0b_human_review_layer.py",r/"scripts"/"check_v1_0b_human_review_layer.py",review/"manual_review_state.json",review/"reviewed_watchlist.csv",review/"reviewed_reject.csv",review/"needs_more_data.csv",review/"manual_review_summary.md",out/"v1_0b_human_review_layer_summary.json",out/"v1_0b_human_review_layer_report.md"]
    for p in required: require_file(p)
    state=read_json(review/"manual_review_state.json")
    summary=read_json(out/"v1_0b_human_review_layer_summary.json")
    require(summary.get("phase")==PHASE,"Summary phase OK")
    require(summary.get("status")=="OK","Summary status OK")
    require(summary.get("records_total",0)>0,"Records total > 0")
    require(isinstance(state.get("records"),dict),"State records dict")
    require(len(state["records"])==summary.get("records_total"),"Summary records match state")
    allowed={"pending_review","reviewed_watchlist","reviewed_reject","needs_more_data"}
    require(set(summary.get("manual_status_allowed_values",[]))==allowed,"Allowed statuses OK")
    counts={k:0 for k in allowed}
    for t,rec in state["records"].items():
        require(rec.get("manual_status") in allowed,f"{t}: manual status allowed")
        require(rec.get("manual_review_required") is True,f"{t}: manual review required")
        require(rec.get("not_financial_advice") is True,f"{t}: not financial advice")
        counts[rec.get("manual_status")]+=1
    require(counts["reviewed_watchlist"]==summary.get("watchlist_count"),"Watchlist count OK")
    require(counts["reviewed_reject"]==summary.get("reject_count"),"Reject count OK")
    require(counts["needs_more_data"]==summary.get("needs_more_data_count"),"Needs more data count OK")
    require(counts["pending_review"]==summary.get("pending_review_count"),"Pending count OK")
    require(len(csv_rows(review/"reviewed_watchlist.csv"))==summary.get("watchlist_count"),"Watchlist CSV count OK")
    require(len(csv_rows(review/"reviewed_reject.csv"))==summary.get("reject_count"),"Reject CSV count OK")
    require(len(csv_rows(review/"needs_more_data.csv"))==summary.get("needs_more_data_count"),"Needs more data CSV count OK")
    for k in ["openai_called","api_called","yfinance_called","pipeline_recalculated","app_modified","filters_modified","release_modified"]:
        require(summary.get(k) is False,f"Control OK: {k}=False")
    md=(review/"manual_review_summary.md").read_text(encoding="utf-8")
    for txt in ["Manual Review Summary","Not financial advice","Reviewed watchlist","Reviewed reject","Needs more data","Pending review"]:
        require(txt in md,f"Manual review summary contains: {txt}")
    print()
    print("Result")
    print("-"*92)
    print("OK   v1.0B Human Review Layer is valid")

if __name__=="__main__":
    main()
