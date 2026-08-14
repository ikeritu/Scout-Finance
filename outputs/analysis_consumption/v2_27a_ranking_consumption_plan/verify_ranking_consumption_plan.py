#!/usr/bin/env python3
"""Validate v2.27A ranking-consumption safety invariants."""
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",type=Path,default=Path("outputs/analysis_consumption/v2_27a_ranking_consumption_plan/ranking_consumption_plan.json"))
    args=ap.parse_args()
    r=json.loads(args.report.read_text(encoding="utf-8"))
    errors=[]
    p=r["current_inputs"]["scoring_pointer"]
    d=r["current_inputs"]["diagnostic_artifact"]
    if p["allow_ranking"] is not False: errors.append("current pointer unexpectedly allows ranking")
    if r["decision"]["production_ranking_authorized"]: errors.append("production ranking unexpectedly authorized")
    if r["decision"]["diagnostic_ranking_authorized"]: errors.append("diagnostic ranking unexpectedly authorized")
    if d["rows"]+d["uncovered_rows"]!=r["current_inputs"]["operational_universe"]["rows"]: errors.append("coverage arithmetic mismatch")
    states={x["state"] for x in r["consumer_states"]}
    required={"CATALOG_AVAILABLE","DIAGNOSTIC_LOCKED","PRODUCTION_RANKING","SCORING_UNAVAILABLE"}
    if states!=required: errors.append("consumer state set mismatch")
    if r["current_inputs"]["diagnostic_formula"]["attractiveness_score"]!=0: errors.append("diagnostic attractiveness weight changed")
    if errors:
        print("\n".join(errors)); return 1
    print("PASS: catalog fallback, ranking gates and diagnostic disclosures are valid")
    return 0
if __name__=="__main__": raise SystemExit(main())
