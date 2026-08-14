#!/usr/bin/env python3
import argparse,json
from pathlib import Path
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--report",type=Path,default=Path("outputs/analysis_consumption/v2_27b_export_pack_design/export_pack_design.json"));a=ap.parse_args();r=json.loads(a.report.read_text());e=[]
 if r["source_contract"]["allow_ranking"] is not False:e.append("ranking unexpectedly allowed")
 if r["decisions"]["production_ranking_exports_authorized"]:e.append("production export unexpectedly authorized")
 if r["decisions"]["score_columns_outside_production"]:e.append("score leakage allowed")
 if {p["id"] for p in r["package_catalog"]}!={f"P0{i}" for i in range(1,9)}:e.append("package catalog mismatch")
 if not {"manifest.json","README.md","data_dictionary.csv"}.issubset({x["path"] for x in r["standard_bundle_layout"]}):e.append("bundle baseline missing")
 if not any(x["risk"]=="CSV formula injection" for x in r["safety_controls"]):e.append("CSV injection control missing")
 if e:print("\n".join(e));return 1
 print("PASS: export provenance, security and scoring gates are valid");return 0
if __name__=="__main__":raise SystemExit(main())
