from __future__ import annotations
import json, zipfile
from pathlib import Path
PHASE="v1.0F"; VERSION="v1.0.0-candidate-docs-freeze"
ZIP="Scout_Finance_v1.0.0_candidate_DOCUMENTATION_FREEZE.zip"
MAN="MANIFEST_v1.0.0_candidate_documentation.json"
REP="FREEZE_REPORT_v1.0.0_candidate_documentation.md"
def root(): return Path(__file__).resolve().parents[1]
def read_json(p): return json.loads(p.read_text(encoding="utf-8"))
def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)
def reqf(p): req(p.exists(),f"File exists: {p}")
def main():
    r=root(); out=r/"outputs"/"scouting"; rel=r/"releases"
    print("Scout Finance — v1.0F Final Documentation Freeze checker")
    print("="*92)
    files=[r/"src"/"v1_0f_final_documentation_freeze.py",r/"scripts"/"check_v1_0f_final_documentation_freeze.py",out/"v1_0f_final_documentation_freeze_summary.json",out/"v1_0f_final_documentation_freeze_audit.json",out/"v1_0f_final_documentation_freeze_report.md",out/"v1_0f_final_documentation_freeze_file_index.csv",rel/MAN,rel/REP,rel/ZIP,r/"docs"/"USER_GUIDE.md",r/"docs"/"QUICKSTART.md",r/"docs"/"SAFETY_LIMITS.md",rel/"Scout_Finance_v1.0.0_candidate_FREEZE.zip"]
    for f in files: reqf(f)
    s=read_json(out/"v1_0f_final_documentation_freeze_summary.json"); m=read_json(rel/MAN)
    req(s.get("phase")==PHASE,"Summary phase OK"); req(s.get("version")==VERSION,"Summary version OK"); req(s.get("status")=="OK","Summary status OK")
    req(m.get("phase")==PHASE,"Manifest phase OK"); req(m.get("version")==VERSION,"Manifest version OK"); req(m.get("status")=="OK","Manifest status OK")
    for k in ["all_required_files_exist","v1d_freeze_summary_ok","v1e_user_manual_summary_ok","documentation_content_ok","candidate_freeze_detected","final_review_pack_detected","controls_false"]:
        req(s.get(k) is True,f"Check OK: {k}")
    for k in ["openai_called","api_called","yfinance_called","pipeline_recalculated","app_modified","filters_modified","release_modified"]:
        req(s.get(k) is False,f"Summary control OK: {k}=False"); req(m.get("controls",{}).get(k) is False,f"Manifest control OK: {k}=False")
    req(s.get("zip_sha256"),"ZIP SHA present"); req(s.get("zip_file_count",0)>0,"ZIP file count > 0"); req(m.get("zip",{}).get("sha256")==s.get("zip_sha256"),"ZIP SHA matches")
    with zipfile.ZipFile(rel/ZIP,"r") as z: names=set(z.namelist())
    for expected in ["docs/USER_GUIDE.md","docs/QUICKSTART.md","docs/SAFETY_LIMITS.md","outputs/scouting/manual_review/final_review_pack.md",f"releases/{MAN}",f"releases/{REP}"]:
        req(expected in names,f"ZIP contains: {expected}")
    report=(rel/REP).read_text(encoding="utf-8")
    for text in ["Documentation Freeze Report","Documentation files","Documentation freeze only","No code functionality changes"]:
        req(text in report,f"Freeze report contains: {text}")
    print(); print("Result"); print("-"*92); print("OK   v1.0F Final Documentation Freeze is valid")
if __name__=="__main__": main()
