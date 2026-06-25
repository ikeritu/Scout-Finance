from __future__ import annotations
import csv, hashlib, json, subprocess, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
PHASE='v1.1C'; TITLE='MVP Final Freeze'; VERSION='v1.1C-mvp-final-freeze'
ZIP_NAME='Scout_Finance_v1.1C_MVP_FINAL_FREEZE.zip'
MANIFEST_NAME='MANIFEST_v1.1C_mvp_final_freeze.json'; REPORT_NAME='FREEZE_REPORT_v1.1C_mvp_final_freeze.md'
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs'/'scouting'; REL=ROOT/'releases'
FLAGS={'openai_called':False,'api_called':False,'yfinance_called':False,'pipeline_recalculated':False,'app_modified':False,'filters_modified':False,'release_modified':False}
REQ=['releases/Scout_Finance_v1.0.0_candidate_FREEZE.zip','releases/Scout_Finance_v1.0.0_candidate_DOCUMENTATION_FREEZE.zip','releases/MANIFEST_v1.0.0_candidate.json','releases/FREEZE_REPORT_v1.0.0_candidate.md','releases/MANIFEST_v1.0.0_candidate_documentation.json','releases/FREEZE_REPORT_v1.0.0_candidate_documentation.md','docs/USER_GUIDE.md','docs/QUICKSTART.md','docs/SAFETY_LIMITS.md','docs/v1/V1_0E_USER_MANUAL.md','docs/v1/V1_0F_FINAL_DOCUMENTATION_FREEZE.md','docs/v1/V1_1B_USABILITY_PATCH.md','scripts/check_v1_0d_freeze_candidate.py','scripts/check_v1_0e_user_manual.py','scripts/check_v1_0f_final_documentation_freeze.py','scripts/check_v1_1b_usability_patch.py','outputs/scouting/v1_0d_freeze_candidate_summary.json','outputs/scouting/v1_0e_user_manual_summary.json','outputs/scouting/v1_0f_final_documentation_freeze_summary.json','outputs/scouting/v1_1b_usability_patch_summary.json','outputs/scouting/manual_review/final_review_pack.md','outputs/scouting/manual_review/final_review_pack.json','outputs/scouting/manual_review/final_review_pack.csv','outputs/scouting/manual_review/manual_review_state.json']
PAT=['docs/*.md','docs/v1/*.md','scripts/check_v1_*.py','src/v1_0d_freeze_candidate.py','src/v1_0f_final_documentation_freeze.py','outputs/scouting/v1_0d_freeze_candidate_*','outputs/scouting/v1_0e_user_manual_*','outputs/scouting/v1_0f_final_documentation_freeze_*','outputs/scouting/v1_1b_usability_patch_*','outputs/scouting/manual_review/final_review_pack.*','outputs/scouting/manual_review/manual_review_state.json','outputs/scouting/manual_review/manual_review_summary.md','outputs/scouting/manual_review/reviewed_watchlist.csv','outputs/scouting/manual_review/reviewed_reject.csv','outputs/scouting/manual_review/needs_more_data.csv','releases/MANIFEST_v1.0.0_candidate*.json','releases/FREEZE_REPORT_v1.0.0_candidate*.md']
def now(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
def sha(p:Path):
    if not p.exists() or not p.is_file(): return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()
def read_json(p:Path,default:Any):
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default
def write_json(p:Path,d:Any): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
def rec(rel:str):
    p=ROOT/rel
    return {'path':rel,'exists':p.exists(),'is_file':p.is_file(),'size_bytes':p.stat().st_size if p.exists() and p.is_file() else None,'sha256':sha(p)}
def git(cmd):
    try: return subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=False).stdout.strip()
    except Exception as e: return f'ERROR: {e}'
def git_clean(status:str):
    lines=[x.strip() for x in status.splitlines() if x.strip()]
    return len(lines)==1 and lines[0].startswith('## ')
def summary_ok(name): return read_json(OUT/name,{}).get('status')=='OK'
def controls_false(name):
    d=read_json(OUT/name,{})
    return all(d.get(k) is False for k in FLAGS)
def collect():
    paths=[]; seen=set()
    for rel in REQ:
        p=ROOT/rel
        if p.exists() and p.is_file(): paths.append(p); seen.add(rel)
    for pat in PAT:
        for p in ROOT.glob(pat):
            rel=str(p.relative_to(ROOT))
            if p.is_file() and rel not in seen: paths.append(p); seen.add(rel)
    return sorted(paths,key=lambda p:str(p.relative_to(ROOT)))
def make_zip(zpath, files):
    zpath.parent.mkdir(parents=True,exist_ok=True)
    if zpath.exists(): zpath.unlink()
    with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for f in files: z.write(f,f.relative_to(ROOT))
    return sha(zpath) or ''
def write_csv(p,rows):
    fields=['path','exists','is_file','size_bytes','sha256']; p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); [w.writerow({k:r.get(k) for k in fields}) for r in rows]
def report(p,m):
    lines=['# Scout Finance — v1.1C MVP Final Freeze Report','','Status: **OK**','','## Summary','',f"- Version: `{m['version']}`",f"- Git HEAD: `{m['git']['head']}`",f"- Git clean: `{m['git']['clean']}`",f"- ZIP: `{m['zip']['path']}`",f"- ZIP SHA256: `{m['zip']['sha256']}`",f"- Files included: {m['zip']['file_count']}",'','## Checks','']
    for k,v in m['checks'].items(): lines.append(f'- {k}: `{v}`')
    lines += ['','## Safety','']
    for k,v in m['controls'].items(): lines.append(f'- {k}: `{v}`')
    lines += ['','## Scope','','MVP final freeze only. No scoring changes, no filter changes, no pipeline recalculation, no OpenAI execution, no external API calls and no yfinance calls.','','## Next','','Use the MVP locally with real cases before starting any v2 work.','']
    p.write_text('\n'.join(lines),encoding='utf-8')
def main():
    OUT.mkdir(parents=True,exist_ok=True); REL.mkdir(parents=True,exist_ok=True)
    status=git(['git','status','-sb']); head=git(['git','log','--oneline','-1']); required=[rec(r) for r in REQ]
    checks={'all_required_files_exist':all(r['exists'] for r in required),'v1_0d_summary_ok':summary_ok('v1_0d_freeze_candidate_summary.json'),'v1_0e_summary_ok':summary_ok('v1_0e_user_manual_summary.json'),'v1_0f_summary_ok':summary_ok('v1_0f_final_documentation_freeze_summary.json'),'v1_1b_summary_ok':summary_ok('v1_1b_usability_patch_summary.json'),'all_controls_false':all(controls_false(n) for n in ['v1_0d_freeze_candidate_summary.json','v1_0e_user_manual_summary.json','v1_0f_final_documentation_freeze_summary.json','v1_1b_usability_patch_summary.json']),'candidate_freeze_detected':(REL/'Scout_Finance_v1.0.0_candidate_FREEZE.zip').exists(),'documentation_freeze_detected':(REL/'Scout_Finance_v1.0.0_candidate_DOCUMENTATION_FREEZE.zip').exists(),'final_review_pack_detected':(OUT/'manual_review'/'final_review_pack.md').exists(),'git_clean':git_clean(status)}
    man=REL/MANIFEST_NAME; rep=REL/REPORT_NAME; zpath=REL/ZIP_NAME; audit=OUT/'v1_1c_mvp_final_freeze_audit.json'; outrep=OUT/'v1_1c_mvp_final_freeze_report.md'; summary=OUT/'v1_1c_mvp_final_freeze_summary.json'; idx=OUT/'v1_1c_mvp_final_freeze_file_index.csv'
    m={'phase':PHASE,'title':TITLE,'version':VERSION,'status':'OK','created_at':now(),'checks':checks,'required_files':required,'controls':FLAGS,'git':{'status':status,'head':head,'clean':checks['git_clean']},'zip':{'path':str(zpath.relative_to(ROOT)),'sha256':None,'file_count':None},'next':'Use real local cases before v2 work'}
    write_json(man,m); report(rep,m); write_json(audit,m); report(outrep,m)
    files=collect()+[man,rep,audit,outrep]
    clean=[]; seen=set()
    for f in files:
        rel=str(f.relative_to(ROOT))
        if f.exists() and f.is_file() and rel not in seen and rel != f'releases/{ZIP_NAME}': clean.append(f); seen.add(rel)
    zsha=make_zip(zpath,clean)
    m['zip']={'path':str(zpath.relative_to(ROOT)),'sha256':zsha,'file_count':len(clean)}
    write_json(man,m); report(rep,m); write_json(audit,m); report(outrep,m)
    write_json(summary,{'phase':PHASE,'title':TITLE,'version':VERSION,'status':'OK','created_at':m['created_at'],**checks,'git_head':head,'git_status':status,'zip_path':m['zip']['path'],'zip_sha256':zsha,'zip_file_count':len(clean),**FLAGS})
    write_csv(idx,[rec(str(f.relative_to(ROOT))) for f in clean])
    print('Scout Finance — v1.1C MVP Final Freeze'); print('='*92); print('Status: OK')
    for k in ['all_required_files_exist','v1_0d_summary_ok','v1_0e_summary_ok','v1_0f_summary_ok','v1_1b_summary_ok','all_controls_false','git_clean']: print(f'{k}: {checks[k]}')
    print(f'Git HEAD: {head}'); print(f'ZIP: {m["zip"]["path"]}'); print(f'ZIP SHA256: {zsha}'); print(f'Files included: {len(clean)}')
    print('OpenAI called: False'); print('API called: False'); print('yfinance called: False'); print('Pipeline recalculated: False'); print('v1.1C MVP final freeze complete.')
if __name__=='__main__': main()
