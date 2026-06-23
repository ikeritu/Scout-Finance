from __future__ import annotations
import json, zipfile
from pathlib import Path
PHASE="v1.0D"
VERSION="v1.0.0-candidate"
ZIP_NAME="Scout_Finance_v1.0.0_candidate_FREEZE.zip"
MANIFEST_NAME="MANIFEST_v1.0.0_candidate.json"
FREEZE_REPORT_NAME="FREEZE_REPORT_v1.0.0_candidate.md"

def root(): return Path(__file__).resolve().parents[1]
def read_json(p): return json.loads(p.read_text(encoding="utf-8"))
def ok(m): print("OK   "+m)
def fail(m):
    print("FAIL "+m); raise SystemExit(1)
def require(c,m): ok(m) if c else fail(m)
def require_file(p): require(p.exists(),f"File exists: {p}")

def main():
    r=root(); out=r/"outputs"/"scouting"; rel=r/"releases"
    print("Scout Finance — v1.0D Freeze Candidate checker")
    print("="*92)
    required=[
        r/"src"/"v1_0d_freeze_candidate.py",
        r/"scripts"/"check_v1_0d_freeze_candidate.py",
        out/"v1_0d_freeze_candidate_summary.json",
        out/"v1_0d_freeze_candidate_audit.json",
        out/"v1_0d_freeze_candidate_report.md",
        out/"v1_0d_freeze_candidate_file_index.csv",
        rel/MANIFEST_NAME,
        rel/FREEZE_REPORT_NAME,
        rel/ZIP_NAME,
        rel/"Scout_Finance_v0.9.0_experimental_ai_FREEZE.zip",
    ]
    for p in required: require_file(p)
    summary=read_json(out/"v1_0d_freeze_candidate_summary.json")
    manifest=read_json(rel/MANIFEST_NAME)
    require(summary.get("phase")==PHASE,"Summary phase OK")
    require(summary.get("version")==VERSION,"Summary version OK")
    require(summary.get("status")=="OK","Summary status OK")
    require(manifest.get("phase")==PHASE,"Manifest phase OK")
    require(manifest.get("version")==VERSION,"Manifest version OK")
    require(manifest.get("status")=="OK","Manifest status OK")
    for k in ["all_required_files_exist","all_v1_summaries_ok","all_v1_controls_false","v09_freeze_detected","final_review_pack_detected","manual_review_state_detected"]:
        require(summary.get(k) is True,f"Check OK: {k}")
    for k in ["openai_called","api_called","yfinance_called","pipeline_recalculated","app_modified","filters_modified","release_modified"]:
        require(summary.get(k) is False,f"Summary control OK: {k}=False")
        require(manifest.get("controls",{}).get(k) is False,f"Manifest control OK: {k}=False")
    require(summary.get("zip_sha256"),"ZIP SHA present")
    require(summary.get("zip_file_count",0)>0,"ZIP file count > 0")
    require(manifest.get("zip",{}).get("sha256")==summary.get("zip_sha256"),"ZIP SHA matches")
    with zipfile.ZipFile(rel/ZIP_NAME,"r") as z:
        names=set(z.namelist())
    for expected in [
        "outputs/scouting/manual_review/final_review_pack.md",
        "outputs/scouting/manual_review/final_review_pack.json",
        "outputs/scouting/manual_review/final_review_pack.csv",
        "outputs/scouting/manual_review/manual_review_state.json",
        f"releases/{MANIFEST_NAME}",
        f"releases/{FREEZE_REPORT_NAME}",
    ]:
        require(expected in names,f"ZIP contains: {expected}")
    report=(rel/FREEZE_REPORT_NAME).read_text(encoding="utf-8")
    for text in ["v1.0.0-candidate","Manual review state","No real AI execution","No investment advice"]:
        require(text in report,f"Freeze report contains: {text}")
    print()
    print("Result")
    print("-"*92)
    print("OK   v1.0D Freeze Candidate is valid")

if __name__=="__main__":
    main()
