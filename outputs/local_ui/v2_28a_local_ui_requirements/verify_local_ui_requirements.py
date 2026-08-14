#!/usr/bin/env python3
import argparse,json
from pathlib import Path
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--report",type=Path,default=Path("outputs/local_ui/v2_28a_local_ui_requirements/local_ui_requirements.json"));a=ap.parse_args();r=json.loads(a.report.read_text());e=[]
 if r["architecture_decision"]["framework"]!="Streamlit":e.append("framework mismatch")
 if r["current_truth"]["allow_ranking"] is not False:e.append("ranking unexpectedly allowed")
 if len(r["screens"])!=8:e.append("screen map incomplete")
 if len(r["functional_requirements"])<30:e.append("functional requirements incomplete")
 if len(r["nonfunctional_requirements"])<15:e.append("nonfunctional requirements incomplete")
 if not any(x["severity"]=="CRITICAL" for x in r["legacy_gap_audit"]):e.append("critical legacy gap missing")
 if len(r["roadmap"])!=6:e.append("v2.28 roadmap incomplete")
 if r["pointer_or_dataset_modified"]:e.append("requirements phase modified state")
 if e:print("\n".join(e));return 1
 print("PASS: framework, screens, requirements, legacy gaps and roadmap are complete");return 0
if __name__=="__main__":raise SystemExit(main())
