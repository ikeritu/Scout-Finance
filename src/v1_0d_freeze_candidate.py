from __future__ import annotations
import csv, hashlib, json, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PHASE="v1.0D"
TITLE="Freeze v1.0.0-candidate"
VERSION="v1.0.0-candidate"
ZIP_NAME="Scout_Finance_v1.0.0_candidate_FREEZE.zip"
MANIFEST_NAME="MANIFEST_v1.0.0_candidate.json"
FREEZE_REPORT_NAME="FREEZE_REPORT_v1.0.0_candidate.md"

PROJECT_ROOT=Path(__file__).resolve().parents[1]
OUT=PROJECT_ROOT/"outputs"/"scouting"
REVIEW=OUT/"manual_review"
RELEASES=PROJECT_ROOT/"releases"

FLAGS={"openai_called":False,"api_called":False,"yfinance_called":False,"pipeline_recalculated":False,"app_modified":False,"filters_modified":False,"release_modified":False}

REQUIRED_FILES=[
"releases/Scout_Finance_v0.9.0_experimental_ai_FREEZE.zip",
"releases/MANIFEST_v0.9.0_experimental_ai.json",
"releases/FREEZE_REPORT_v0.9.0_experimental_ai.md",
"src/v1_0a_local_review_console.py",
"scripts/check_v1_0a_local_review_console.py",
"docs/v1/V1_0A_LOCAL_REVIEW_CONSOLE.md",
"outputs/scouting/v1_0a_local_review_console_summary.json",
"outputs/scouting/v1_0a_local_review_console_report.md",
"src/v1_0b_human_review_layer.py",
"scripts/check_v1_0b_human_review_layer.py",
"docs/v1/V1_0B_HUMAN_REVIEW_LAYER.md",
"outputs/scouting/v1_0b_human_review_layer_summary.json",
"outputs/scouting/v1_0b_human_review_layer_report.md",
"src/v1_0c_review_export_pack.py",
"scripts/check_v1_0c_review_export_pack.py",
"docs/v1/V1_0C_REVIEW_EXPORT_PACK.md",
"outputs/scouting/v1_0c_review_export_pack_summary.json",
"outputs/scouting/v1_0c_review_export_pack_report.md",
"outputs/scouting/manual_review/manual_review_state.json",
"outputs/scouting/manual_review/local_review_console.md",
"outputs/scouting/manual_review/local_review_console_index.csv",
"outputs/scouting/manual_review/manual_review_notes.md",
"outputs/scouting/manual_review/manual_review_summary.md",
"outputs/scouting/manual_review/reviewed_watchlist.csv",
"outputs/scouting/manual_review/reviewed_reject.csv",
"outputs/scouting/manual_review/needs_more_data.csv",
"outputs/scouting/manual_review/final_review_pack.md",
"outputs/scouting/manual_review/final_review_pack.json",
"outputs/scouting/manual_review/final_review_pack.csv",
]

OPTIONAL_INCLUDE_PATTERNS=[
"src/phase9*.py","src/data_hub.py","src/red_flags.py",
"scripts/check_phase9*.py",
"schemas/*.json",
"docs/phase9/*.md","docs/v1/*.md",
"outputs/scouting/phase9*.json","outputs/scouting/phase9*.md","outputs/scouting/phase9*.csv",
"outputs/scouting/research_memos_v2/*","outputs/scouting/red_flags/*","outputs/scouting/research_memos_v2_red_flags/*","outputs/scouting/ai_profiles_dry_run/*",
"outputs/scouting/manual_review/*",
"outputs/scouting/v1_0*.json","outputs/scouting/v1_0*.md","outputs/scouting/v1_0*.csv",
]

def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")

def sha256_file(path:Path):
    if not path.exists() or not path.is_file(): return None
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def read_json(path:Path, default:Any):
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default

def write_json(path:Path,data:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")

def record(rel:str)->Dict[str,Any]:
    p=PROJECT_ROOT/rel
    return {"path":rel,"exists":p.exists(),"is_file":p.is_file(),"size_bytes":p.stat().st_size if p.exists() and p.is_file() else None,"sha256":sha256_file(p)}

def check_summary(rel:str)->Dict[str,Any]:
    p=PROJECT_ROOT/rel
    data=read_json(p,{})
    return {
        "path":rel,
        "exists":p.exists(),
        "phase":data.get("phase"),
        "status":data.get("status"),
        "controls":{k:data.get(k) for k in FLAGS},
    }

def controls_false(summary:Dict[str,Any])->bool:
    return all(summary.get("controls",{}).get(k) is False for k in FLAGS)

def collect_files()->List[Path]:
    paths=[]
    seen=set()
    for rel in REQUIRED_FILES:
        p=PROJECT_ROOT/rel
        if p.exists() and p.is_file() and rel not in seen:
            paths.append(p); seen.add(rel)
    for pattern in OPTIONAL_INCLUDE_PATTERNS:
        for p in PROJECT_ROOT.glob(pattern):
            if p.is_file():
                rel=str(p.relative_to(PROJECT_ROOT))
                if rel not in seen and not rel.endswith(ZIP_NAME):
                    paths.append(p); seen.add(rel)
    return sorted(paths,key=lambda p:str(p.relative_to(PROJECT_ROOT)))

def write_zip(zip_path:Path, paths:List[Path])->str:
    zip_path.parent.mkdir(parents=True,exist_ok=True)
    if zip_path.exists(): zip_path.unlink()
    with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p,p.relative_to(PROJECT_ROOT))
    return sha256_file(zip_path) or ""

def write_csv(path:Path, rows:List[Dict[str,Any]]):
    fields=["path","exists","is_file","size_bytes","sha256"]
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:r.get(k) for k in fields})

def write_report(path:Path, manifest:Dict[str,Any]):
    checks=manifest["checks"]
    lines=[
        "# Scout Finance — v1.0.0-candidate Freeze Report","",
        "Status: **OK**","",
        "## Summary","",
        f"- Version: `{manifest['version']}`",
        f"- Created at: `{manifest['created_at']}`",
        f"- ZIP: `{manifest['zip']['path']}`",
        f"- ZIP SHA256: `{manifest['zip']['sha256']}`",
        f"- Files included: {manifest['zip']['file_count']}",
        "",
        "## Checks","",
    ]
    for k,v in checks.items():
        lines.append(f"- {k}: `{v}`")
    lines += ["","## Safety",""]
    for k,v in manifest["controls"].items():
        lines.append(f"- {k}: `{v}`")
    lines += [
        "",
        "## Included workflow",
        "",
        "- v0.9 experimental AI freeze",
        "- v1.0A Local Review Console",
        "- v1.0B Human Review Layer",
        "- v1.0C Review Export Pack",
        "",
        "## Manual review state",
        "",
        f"- Watchlist: {manifest['manual_review_counts'].get('reviewed_watchlist')}",
        f"- Rejected: {manifest['manual_review_counts'].get('reviewed_reject')}",
        f"- Needs more data: {manifest['manual_review_counts'].get('needs_more_data')}",
        f"- Pending review: {manifest['manual_review_counts'].get('pending_review')}",
        "",
        "## Non-goals",
        "",
        "- No real AI execution.",
        "- No external API calls.",
        "- No yfinance calls.",
        "- No pipeline recalculation.",
        "- No investment advice.",
        "",
    ]
    path.write_text("\n".join(lines),encoding="utf-8")

def manual_counts():
    state=read_json(REVIEW/"manual_review_state.json",{})
    counts={"reviewed_watchlist":0,"reviewed_reject":0,"needs_more_data":0,"pending_review":0}
    for rec in state.get("records",{}).values():
        s=rec.get("manual_status")
        if s in counts: counts[s]+=1
    return counts

def main():
    OUT.mkdir(parents=True,exist_ok=True); RELEASES.mkdir(parents=True,exist_ok=True)
    required=[record(rel) for rel in REQUIRED_FILES]
    v1_summaries=[
        check_summary("outputs/scouting/v1_0a_local_review_console_summary.json"),
        check_summary("outputs/scouting/v1_0b_human_review_layer_summary.json"),
        check_summary("outputs/scouting/v1_0c_review_export_pack_summary.json"),
    ]
    all_required=all(r["exists"] for r in required)
    all_v1_ok=all(s["exists"] and s["status"]=="OK" for s in v1_summaries)
    all_controls=all(controls_false(s) for s in v1_summaries)
    counts=manual_counts()
    files=collect_files()

    manifest_path=RELEASES/MANIFEST_NAME
    report_path=RELEASES/FREEZE_REPORT_NAME
    zip_path=RELEASES/ZIP_NAME
    summary_path=OUT/"v1_0d_freeze_candidate_summary.json"
    audit_path=OUT/"v1_0d_freeze_candidate_audit.json"
    report_out_path=OUT/"v1_0d_freeze_candidate_report.md"
    index_path=OUT/"v1_0d_freeze_candidate_file_index.csv"

    manifest={
        "phase":PHASE,"title":TITLE,"version":VERSION,"status":"OK","created_at":now(),
        "checks":{
            "all_required_files_exist":all_required,
            "all_v1_summaries_ok":all_v1_ok,
            "all_v1_controls_false":all_controls,
            "v09_freeze_detected":(PROJECT_ROOT/"releases/Scout_Finance_v0.9.0_experimental_ai_FREEZE.zip").exists(),
            "final_review_pack_detected":(REVIEW/"final_review_pack.md").exists(),
            "manual_review_state_detected":(REVIEW/"manual_review_state.json").exists(),
        },
        "required_files":required,
        "v1_summaries":v1_summaries,
        "manual_review_counts":counts,
        "controls":FLAGS,
        "zip":{"path":str(zip_path.relative_to(PROJECT_ROOT)),"sha256":None,"file_count":None},
        "next":"v1.0E — User Manual / Operating Guide"
    }
    write_json(manifest_path,manifest)
    write_report(report_path,manifest)
    write_json(audit_path,manifest)
    write_report(report_out_path,manifest)

    files=collect_files()+[manifest_path,report_path,audit_path,report_out_path]
    seen=set(); clean=[]
    for p in files:
        rel=str(p.relative_to(PROJECT_ROOT))
        if p.exists() and p.is_file() and rel not in seen and rel != f"releases/{ZIP_NAME}":
            clean.append(p); seen.add(rel)
    zip_sha=write_zip(zip_path,clean)
    manifest["zip"]={"path":str(zip_path.relative_to(PROJECT_ROOT)),"sha256":zip_sha,"file_count":len(clean)}
    write_json(manifest_path,manifest); write_report(report_path,manifest)
    write_json(audit_path,manifest); write_report(report_out_path,manifest)
    summary={"phase":PHASE,"title":TITLE,"version":VERSION,"status":"OK","created_at":manifest["created_at"],**manifest["checks"],"watchlist_count":counts["reviewed_watchlist"],"reject_count":counts["reviewed_reject"],"needs_more_data_count":counts["needs_more_data"],"pending_review_count":counts["pending_review"],"zip_path":manifest["zip"]["path"],"zip_sha256":zip_sha,"zip_file_count":len(clean),**FLAGS}
    write_json(summary_path,summary)
    write_csv(index_path,[record(str(p.relative_to(PROJECT_ROOT))) for p in clean])
    print("Scout Finance — v1.0D Freeze v1.0.0-candidate")
    print("="*92)
    print("Status: OK")
    print(f"All required files exist: {all_required}")
    print(f"All v1 summaries OK: {all_v1_ok}")
    print(f"All v1 controls false: {all_controls}")
    print(f"ZIP: {manifest['zip']['path']}")
    print(f"ZIP SHA256: {zip_sha}")
    print(f"Files included: {len(clean)}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print("v1.0.0-candidate freeze complete.")

if __name__=="__main__":
    main()
