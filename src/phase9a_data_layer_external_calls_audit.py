from __future__ import annotations
import csv, hashlib, json, re, ast
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
PHASE='9A'; TITLE='DataLayer and External Calls Audit'; DEFAULT_TOP_N=3; MAX_TOP_N=3
EXCLUDE={'.git','.venv','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','node_modules','releases'}
PATTERNS={
 'yfinance':[r'\byfinance\b',r'\byf\.'], 'openai':[r'\bopenai\b',r'OpenAI',r'ENABLE_OPENAI'],
 'requests':[r'\brequests\.',r'\brequests\b'], 'urllib':[r'\burllib\b'], 'httpx':[r'\bhttpx\b'],
 'pandas_read_csv':[r'\bread_csv\s*\('], 'sqlite':[r'\bsqlite3\b',r'\.db\b',r'connect\s*\('],
 'dotenv_env':[r'os\.getenv\s*\(',r'load_dotenv',r'ENABLE_',r'ALLOW_',r'AI_RESEARCH'],
 'api_key':[r'API_KEY',r'api_key',r'SECRET',r'TOKEN']}
HINTS={
 'data':['data','download','fetch','universe','yfinance','enrich','clean'], 'scoring':['score','scoring','rank','ranking'],
 'filters':['filter_stage','stage1','stage2','stage3'], 'research_memo':['research_memo','memo','fundamentals','valuation','risk_analysis','moat','growth','institutional','earnings'],
 'ai':['openai','ai_','llm','prompt','gate'], 'exports':['export','report','markdown','csv','json'], 'dashboard':['dashboard','streamlit','app'], 'checks':['check_','validate','audit']}
CONTROL={'openai_called':False,'api_called':False,'yfinance_called':False,'pipeline_recalculated':False,'app_modified':False,'filters_modified':False,'release_modified':False}
def root(): return Path(__file__).resolve().parents[1]
def now(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
def skip(p,r):
    try: rel=p.relative_to(r)
    except ValueError: return True
    return any(part in EXCLUDE for part in rel.parts)
def txt(p):
    for enc in ('utf-8','latin-1'):
        try: return p.read_text(encoding=enc)
        except Exception: pass
    return ''
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def cats(p):
    s=(p.name+' '+str(p)).lower(); out=[k for k,v in HINTS.items() if any(h in s for h in v)]
    return out or ['unclassified']
def imports_of(text):
    out=[]
    try: tree=ast.parse(text)
    except SyntaxError: return out
    for n in ast.walk(tree):
        if isinstance(n, ast.Import): out += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module: out.append(n.module)
    return sorted(set(out))
def scan(r):
    mods=[]; finds=[]; direct=[]
    files=[]
    for d in ('src','scripts'):
        b=r/d
        if b.exists(): files += [p for p in b.rglob('*.py') if p.is_file() and not skip(p,r)]
    for n in ('.env','.env.example','pyproject.toml','requirements.txt','requirements-dev.txt'):
        p=r/n
        if p.exists(): files.append(p)
    for p in sorted(files, key=lambda x: str(x).lower()):
        t=txt(p); rel=str(p.relative_to(r)); imps=imports_of(t) if p.suffix=='.py' else []
        mods.append({'relative_path':rel,'size_bytes':p.stat().st_size,'sha256':sha(t),'categories':cats(p),'imports':imps})
        for kind, pats in PATTERNS.items():
            for i,line in enumerate(t.splitlines(),1):
                for pat in pats:
                    if re.search(pat,line,re.I):
                        row={'relative_path':rel,'kind':kind,'line_number':i,'pattern':pat,'line':line.strip()[:500]}
                        finds.append(row)
                        if kind in ('pandas_read_csv','sqlite'): direct.append(row)
                        break
    return mods, finds, direct
def expected(r):
    arr=['src/research_memo.py','src/fundamentals.py','src/valuation.py','src/risk_analysis.py','src/moat_analysis.py','src/growth_analysis.py','src/institutional_view.py','src/earnings_quality.py','src/earnings_analysis.py','src/red_flags.py','src/data_hub.py','src/data_cache.py','src/openai_client.py','src/openai_equity_research_v2.py','src/phase8g_optional_ai_interpretation_gate.py','src/phase8i_optional_ai_execution_sandbox.py','scripts/check_phase8g_optional_ai_interpretation_gate.py','scripts/check_phase8i_optional_ai_execution_sandbox.py','outputs/scouting','releases/Scout_Finance_v0.8.0_candidate_FREEZE.zip','releases/RELEASE_LOCK_v0.8.json']
    rows=[]
    for item in arr:
        p=r/item; rows.append({'relative_path':item,'exists':p.exists(),'is_file':p.is_file(),'is_dir':p.is_dir(),'size_bytes':p.stat().st_size if p.exists() and p.is_file() else None})
    return rows
def outputs(r):
    out=r/'outputs'/'scouting'; rows=[]
    if not out.exists(): return rows
    for p in out.rglob('*'):
        if p.is_file() and any(x in p.name.lower() for x in ['phase8','phase9','memo','research','gate','prompt','audit','scouting','top_']):
            rows.append({'relative_path':str(p.relative_to(r)),'size_bytes':p.stat().st_size,'last_write_time':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')})
    return sorted(rows,key=lambda x:x['relative_path'])
def write_json(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
def write_csv(p,rows,fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(row.get(k),ensure_ascii=False) if isinstance(row.get(k),(list,dict)) else row.get(k) for k in fields})
def main():
    r=root(); out=r/'outputs'/'scouting'; out.mkdir(parents=True,exist_ok=True)
    mods, finds, direct = scan(r); exp=expected(r); outs=outputs(r); ex={x['relative_path']:x['exists'] for x in exp}
    by={}; cats_count={}
    for f in finds: by[f['kind']]=by.get(f['kind'],0)+1
    for m in mods:
        for c in m['categories']: cats_count[c]=cats_count.get(c,0)+1
    summary={'phase':PHASE,'title':TITLE,'status':'OK','created_at':now(),'default_top_n':DEFAULT_TOP_N,'max_top_n':MAX_TOP_N,**CONTROL,'module_count':len(mods),'external_findings_count':len(finds),'external_findings_by_kind':by,'module_categories':cats_count,'data_hub_detected':bool(ex.get('src/data_hub.py') or ex.get('src/data_cache.py')),'red_flags_module_detected':bool(ex.get('src/red_flags.py')),'openai_client_detected':bool(ex.get('src/openai_client.py')),'research_memo_detected':bool(ex.get('src/research_memo.py')),'phase8_gate_detected':bool(ex.get('src/phase8g_optional_ai_interpretation_gate.py')),'v08_freeze_detected':bool(ex.get('releases/Scout_Finance_v0.8.0_candidate_FREEZE.zip')),'next':'Phase 9B — Minimal DataHub/cache only if justified'}
    recs=[]
    recs.append({'priority':'Alta','area':'DataLayer','recommendation':'Crear DataHub/cache mínimo solo si esta auditoría confirma accesos dispersos.','rationale':'No copiar arquitectura FinceptTerminal.'})
    if not summary['red_flags_module_detected']: recs.append({'priority':'Alta','area':'Red Flags','recommendation':'Valorar src/red_flags.py reutilizando reglas Stage 1/2/3.','rationale':'No se detecta módulo explícito.'})
    if summary['openai_client_detected']: recs.append({'priority':'Alta','area':'OpenAI','recommendation':'Reutilizar openai_client.py; no crear cliente duplicado.','rationale':'Cliente existente detectado.'})
    recs.append({'priority':'Descartar','area':'Scope','recommendation':'No terminal, brokers, streaming ni agentes masivos.','rationale':'Sobredimensiona Scout Finance.'})
    audit={'phase':PHASE,'title':TITLE,'status':'OK','created_at':summary['created_at'],'summary':summary,'expected_paths':exp,'modules':mods,'external_findings':finds,'direct_reads':direct,'outputs':outs,'recommendations':recs}
    write_json(out/'phase9a_data_layer_external_calls_audit_summary.json',summary)
    write_json(out/'phase9a_data_layer_external_calls_audit.json',audit)
    write_csv(out/'phase9a_module_responsibility_matrix.csv',mods,['relative_path','size_bytes','sha256','categories','imports'])
    write_csv(out/'phase9a_external_calls_and_data_access.csv',finds,['relative_path','kind','line_number','pattern','line'])
    write_csv(out/'phase9a_expected_paths_audit.csv',exp,['relative_path','exists','is_file','is_dir','size_bytes'])
    write_csv(out/'phase9a_outputs_inventory.csv',outs,['relative_path','size_bytes','last_write_time'])
    report=['# Phase 9A — DataLayer and External Calls Audit','','Status: **OK**','',f'- Modules scanned: {len(mods)}',f'- External/data-access findings: {len(finds)}',f'- DataHub detected: {summary["data_hub_detected"]}',f'- Red flags module detected: {summary["red_flags_module_detected"]}',f'- OpenAI client detected: {summary["openai_client_detected"]}',f'- Research memo detected: {summary["research_memo_detected"]}',f'- Phase 8 AI gate detected: {summary["phase8_gate_detected"]}',f'- v0.8 freeze detected: {summary["v08_freeze_detected"]}','','## Safety controls','','- OpenAI called: False','- API called: False','- yfinance called: False','- Pipeline recalculated: False','- app.py modified: False','- filters modified: False','- release modified: False','','## Findings by kind']
    for k,v in sorted(by.items()): report.append(f'- {k}: {v}')
    report += ['','## Recommendations','','| Priority | Area | Recommendation | Rationale |','|---|---|---|---|']
    for rec in recs: report.append(f"| {rec['priority']} | {rec['area']} | {rec['recommendation']} | {rec['rationale']} |")
    report += ['','## Next','','Phase 9B only if this audit proves a minimal DataHub/cache is justified.']
    (out/'phase9a_data_layer_external_calls_audit_report.md').write_text('\n'.join(report),encoding='utf-8')
    print('Scout Finance — Phase 9A DataLayer and External Calls Audit')
    print('='*92); print('\nAudit\n'+'-'*92); print('Status: OK')
    print(f"Modules scanned: {len(mods)}"); print(f"External/data-access findings: {len(finds)}")
    print(f"DataHub detected: {summary['data_hub_detected']}"); print(f"Red flags module detected: {summary['red_flags_module_detected']}")
    print(f"OpenAI client detected: {summary['openai_client_detected']}"); print(f"Research memo detected: {summary['research_memo_detected']}")
    print(f"Phase 8 AI gate detected: {summary['phase8_gate_detected']}"); print(f"v0.8 freeze detected: {summary['v08_freeze_detected']}")
    print('OpenAI called: False\nAPI called: False\nyfinance called: False\nPipeline recalculated: False')
    print('\nFinal\n'+'-'*92); print('Phase 9A DataLayer and External Calls Audit is complete.')
if __name__=='__main__': main()
