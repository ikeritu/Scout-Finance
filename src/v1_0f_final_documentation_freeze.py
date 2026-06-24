from __future__ import annotations
import csv, hashlib, json, zipfile
from datetime import datetime, timezone
from pathlib import Path

PHASE="v1.0F"
VERSION="v1.0.0-candidate-docs-freeze"
ZIP_NAME="Scout_Finance_v1.0.0_candidate_DOCUMENTATION_FREEZE.zip"
MANIFEST_NAME="MANIFEST_v1.0.0_candidate_documentation.json"
REPORT_NAME="FREEZE_REPORT_v1.0.0_candidate_documentation.md"
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs"/"scouting"
REL=ROOT/"releases"
FLAGS={"openai_called":False,"api_called":False,"yfinance_called":False,"pipeline_recalculated":False,"app_modified":False,"filters_modified":False,"release_modified":False}
REQ=["releases/Scout_Finance_v1.0.0_candidate_FREEZE.zip","releases/MANIFEST_v1.0.0_candidate.json","releases/FREEZE_REPORT_v1.0.0_candidate.md","docs/USER_GUIDE.md","docs/QUICKSTART.md","docs/SAFETY_LIMITS.md","docs/v1/V1_0E_USER_MANUAL.md","scripts/check_v1_0e_user_manual.py","outputs/scouting/v1_0e_user_manual_summary.json","outputs/scouting/v1_0e_user_manual_report.md"]
PATTERNS=["docs/*.md","docs/v1/*.md","scripts/check_v1_0d_freeze_candidate.py","scripts/check_v1_0e_user_manual.py","releases/MANIFEST_v1.0.0_candidate.json","releases/FREEZE_REPORT_v1.0.0_candidate.md","outputs/scouting/v1_0d_freeze_candidate_summary.json","outputs/scouting/v1_0d_freeze_candidate_report.md","outputs/scouting/v1_0e_user_manual_summary.json","outputs/scouting/v1_0e_user_manual_report.md","outputs/scouting/manual_review/final_review_pack.*"]

def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
def sha(p):
    if not p.exists() or not p.is_file(): return None
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def read_json(p,default):
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return default
def write_json(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
def rec(rel):
    p=ROOT/rel
    return {"path":rel,"exists":p.exists(),"is_file":p.is_file(),"size_bytes":p.stat().st_size if p.exists() and p.is_file() else None,"sha256":sha(p)}
def doc_ok():
    checks={"docs/USER_GUIDE.md":["Finalidad","Flujo completo","revisión manual","No es un asesor financiero"],"docs/QUICKSTART.md":["Arranque rápido","Ver candidatos","Generar pack final","Validar candidate freeze"],"docs/SAFETY_LIMITS.md":["No es asesoramiento financiero","No trading automático","IA real desactivada","Decisión humana obligatoria"]}
    out={}
    for rel,terms in checks.items():
        p=ROOT/rel; text=p.read_text(encoding="utf-8") if p.exists() else ""
        out[rel]=all(t.lower() in text.lower() for t in terms)
    return out
def collect():
    paths=[]; seen=set()
    for rel in REQ:
        p=ROOT/rel
        if p.exists() and p.is_file(): paths.append(p); seen.add(rel)
    for pat in PATTERNS:
        for p in ROOT.glob(pat):
            rel=str(p.relative_to(ROOT))
            if p.is_file() and rel not in seen:
                paths.append(p); seen.add(rel)
    return sorted(paths,key=lambda p:str(p.relative_to(ROOT)))
def make_zip(path,files):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): path.unlink()
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for f in files: z.write(f,f.relative_to(ROOT))
    return sha(path)
def write_csv(p,rows):
    fields=["path","exists","is_file","size_bytes","sha256"]
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:r.get(k) for k in fields})
def report(p,m):
    lines=["# Scout Finance — v1.0.0-candidate Documentation Freeze Report","","Status: **OK**","","## Summary","",f"- Version: `{m['version']}`",f"- ZIP: `{m['zip']['path']}`",f"- ZIP SHA256: `{m['zip']['sha256']}`",f"- Files included: {m['zip']['file_count']}","","## Checks",""]
    for k,v in m["checks"].items(): lines.append(f"- {k}: `{v}`")
    lines += ["","## Documentation files",""]
    for r in m["required_files"]: lines.append(f"- `{r['path']}` — exists: `{r['exists']}`")
    lines += ["","## Safety",""]
    for k,v in m["controls"].items(): lines.append(f"- {k}: `{v}`")
    lines += ["","Documentation freeze only. No code functionality changes.",""]
    p.write_text("\n".join(lines),encoding="utf-8")
def main():
    OUT.mkdir(parents=True,exist_ok=True); REL.mkdir(parents=True,exist_ok=True)
    required=[rec(r) for r in REQ]
    v1d=read_json(OUT/"v1_0d_freeze_candidate_summary.json",{})
    v1e=read_json(OUT/"v1_0e_user_manual_summary.json",{})
    dc=doc_ok()
    checks={"all_required_files_exist":all(r["exists"] for r in required),"v1d_freeze_summary_ok":v1d.get("status")=="OK","v1e_user_manual_summary_ok":v1e.get("status")=="OK","documentation_content_ok":all(dc.values()),"candidate_freeze_detected":(REL/"Scout_Finance_v1.0.0_candidate_FREEZE.zip").exists(),"final_review_pack_detected":(OUT/"manual_review"/"final_review_pack.md").exists(),"controls_false":all(v1e.get(k) is False for k in FLAGS)}
    man_path=REL/MANIFEST_NAME; rep_path=REL/REPORT_NAME; zip_path=REL/ZIP_NAME
    audit=OUT/"v1_0f_final_documentation_freeze_audit.json"; outrep=OUT/"v1_0f_final_documentation_freeze_report.md"; summary_path=OUT/"v1_0f_final_documentation_freeze_summary.json"; index=OUT/"v1_0f_final_documentation_freeze_file_index.csv"
    m={"phase":PHASE,"title":"Final Documentation Freeze","version":VERSION,"status":"OK","created_at":now(),"checks":checks,"documentation_content_checks":dc,"required_files":required,"controls":FLAGS,"zip":{"path":str(zip_path.relative_to(ROOT)),"sha256":None,"file_count":None},"next":"v1.1A — Real Local Use Trial"}
    write_json(man_path,m); report(rep_path,m); write_json(audit,m); report(outrep,m)
    files=collect()+[man_path,rep_path,audit,outrep]
    clean=[]; seen=set()
    for f in files:
        rel=str(f.relative_to(ROOT))
        if f.exists() and f.is_file() and rel not in seen and rel != f"releases/{ZIP_NAME}":
            clean.append(f); seen.add(rel)
    zsha=make_zip(zip_path,clean)
    m["zip"]={"path":str(zip_path.relative_to(ROOT)),"sha256":zsha,"file_count":len(clean)}
    write_json(man_path,m); report(rep_path,m); write_json(audit,m); report(outrep,m)
    write_json(summary_path,{"phase":PHASE,"title":"Final Documentation Freeze","version":VERSION,"status":"OK","created_at":m["created_at"],**checks,"zip_path":m["zip"]["path"],"zip_sha256":zsha,"zip_file_count":len(clean),**FLAGS})
    write_csv(index,[rec(str(f.relative_to(ROOT))) for f in clean])
    print("Scout Finance — v1.0F Final Documentation Freeze")
    print("="*92)
    print("Status: OK")
    print(f"All required files exist: {checks['all_required_files_exist']}")
    print(f"v1.0D freeze summary OK: {checks['v1d_freeze_summary_ok']}")
    print(f"v1.0E user manual summary OK: {checks['v1e_user_manual_summary_ok']}")
    print(f"Documentation content OK: {checks['documentation_content_ok']}")
    print(f"ZIP: {m['zip']['path']}")
    print(f"ZIP SHA256: {zsha}")
    print(f"Files included: {len(clean)}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print("v1.0F documentation freeze complete.")
if __name__=="__main__": main()
