#!/usr/bin/env python3
"""Validate the v2.26F maintenance-plan invariants."""
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",type=Path,default=Path("outputs/full_universe_source_acquisition/v2_26f_scheduled_maintenance_plan/maintenance_plan_report.json"))
    args=ap.parse_args()
    r=json.loads(args.report.read_text(encoding="utf-8"))
    errors=[]
    cadences={x["cadence"] for x in r["schedule"]}
    required={"weekly","monthly","quarterly","annual","event-driven"}
    if not required.issubset(cadences): errors.append("missing required cadence")
    if r["closure"]["completed"]!=r["closure"]["total"]: errors.append("v2.26 closure incomplete")
    if r["closure"]["refresh_promotion_authorized"]: errors.append("promotion unexpectedly authorized")
    if r["operating_state"]["scoring_status"]!="NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED": errors.append("scoring not fail-closed")
    if not any(x["severity"]=="P1" for x in r["alert_thresholds"]): errors.append("no P1 threshold")
    if errors:
        print("\n".join(errors)); return 1
    print("PASS: maintenance cadences, fail-closed controls and v2.26 closure are valid")
    return 0
if __name__=="__main__": raise SystemExit(main())
