from __future__ import annotations
import csv, json
from pathlib import Path
PHASE='9A'
def root(): return Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def ok(m): print(f'OK   {m}')
def fail(m): print(f'FAIL {m}'); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)
def reqf(p): req(p.exists(),f'File exists: {p}')
def main():
    r=root(); out=r/'outputs'/'scouting'
    print('Scout Finance — Phase 9A DataLayer and External Calls Audit checker'); print('='*92)
    files=[out/'phase9a_data_layer_external_calls_audit_summary.json',out/'phase9a_data_layer_external_calls_audit_report.md',out/'phase9a_data_layer_external_calls_audit.json',out/'phase9a_module_responsibility_matrix.csv',out/'phase9a_external_calls_and_data_access.csv',out/'phase9a_expected_paths_audit.csv',out/'phase9a_outputs_inventory.csv',r/'src'/'phase9a_data_layer_external_calls_audit.py']
    for f in files: reqf(f)
    s=read(out/'phase9a_data_layer_external_calls_audit_summary.json'); a=read(out/'phase9a_data_layer_external_calls_audit.json')
    req(s.get('phase')==PHASE,'Summary phase is 9A'); req(s.get('status')=='OK','Summary status OK'); req(s.get('default_top_n')==3,'Default TOP N OK'); req(s.get('max_top_n')==3,'MAX TOP N OK')
    for k in ['openai_called','api_called','yfinance_called','pipeline_recalculated','app_modified','filters_modified','release_modified']: req(s.get(k) is False,f'Control OK: {k}=False')
    req(s.get('module_count',0)>0,'Modules scanned > 0'); req('external_findings_by_kind' in s,'Findings by kind present'); req('module_categories' in s,'Module categories present')
    req(s.get('v08_freeze_detected') is True,'v0.8 freeze detected'); req(s.get('research_memo_detected') is True,'Research memo detected'); req(s.get('phase8_gate_detected') is True,'Phase 8 gate detected')
    req(a.get('phase')==PHASE,'Audit phase OK')
    for k in ['expected_paths','modules','external_findings','direct_reads','outputs','recommendations']: req(k in a and isinstance(a[k],list),f'Audit {k} is list')
    with (out/'phase9a_module_responsibility_matrix.csv').open(encoding='utf-8',newline='') as fh: mods=list(csv.DictReader(fh))
    req(len(mods)==s.get('module_count'),'Module matrix row count matches summary')
    with (out/'phase9a_external_calls_and_data_access.csv').open(encoding='utf-8',newline='') as fh: finds=list(csv.DictReader(fh))
    req(len(finds)==s.get('external_findings_count'),'External findings row count matches summary')
    exp={x['relative_path']:x for x in a['expected_paths']}
    for p in ['src/research_memo.py','src/openai_client.py','src/phase8g_optional_ai_interpretation_gate.py','outputs/scouting','releases/Scout_Finance_v0.8.0_candidate_FREEZE.zip']: req(p in exp,f'Expected path audited: {p}')
    rep=(out/'phase9a_data_layer_external_calls_audit_report.md').read_text(encoding='utf-8')
    for t in ['Phase 9A','DataLayer','External Calls','OpenAI called: False','yfinance called: False','Pipeline recalculated: False','Phase 9B']: req(t in rep,f'Report contains: {t}')
    print('\nResult\n'+'-'*92); print('OK   Phase 9A DataLayer and External Calls Audit is valid')
if __name__=='__main__': main()
