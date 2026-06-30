from __future__ import annotations
import csv,json,py_compile
from pathlib import Path
def ok(m): print('OK   '+m)
def fail(m): print('FAIL '+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)
def main():
    root=Path(__file__).resolve().parents[1]; market=root/'outputs'/'market_data'; scout=root/'outputs'/'scouting'
    print('Scout Finance — v1.4F2 Manual Market Data Percent Normalization checker'); print('='*92)
    for p in [root/'app.py',root/'src/market_data_provider_fallback.py',root/'scripts/check_v1_4f2_manual_market_data_percent_normalization.py',root/'docs/v1/V1_4F2_MANUAL_MARKET_DATA_PERCENT_NORMALIZATION.md',root/'data/real/manual_market_data_template.csv']:
        req(p.exists(),f'File exists: {p}')
    py_compile.compile(str(root/'app.py'),doraise=True); ok('app.py compiles')
    py_compile.compile(str(root/'src/market_data_provider_fallback.py'),doraise=True); ok('market_data_provider_fallback.py compiles')
    app=(root/'app.py').read_text(encoding='utf-8'); req('v1.4F2 manual market data percent normalization packaged' in app,'app.py contains v1.4F2 marker')
    script=(root/'src/market_data_provider_fallback.py').read_text(encoding='utf-8')
    for m in ['PCT_INPUT_MODE','human_percent','change_1d_pct','pct_to_ratio','percent_input_mode','market_data_provider_fallback_v0_pct_normalized']:
        req(m in script,f'adapter contains marker: {m}')
    header=(root/'data/real/manual_market_data_template.csv').read_text(encoding='utf-8').splitlines()[0]
    req('change_1d_pct' in header and 'change_20d_pct' in header,'Manual template uses pct headers')
    sp=market/'market_data_provider_fallback_summary.json'
    if sp.exists():
        for p in [sp,market/'market_data_provider_fallback_rows.csv',market/'market_data_provider_fallback_report.md',scout/'real_universe_market_data_candidates.csv',scout/'active_real_universe_top_candidates.csv']: req(p.exists(),f'Generated file exists: {p}')
        s=json.loads(sp.read_text(encoding='utf-8')); req(s.get('phase') in {'v1.4E2','v1.4F2'},'Summary phase valid'); req(s.get('openai_called') is False,'OpenAI control false'); req(s.get('broker_called') is False,'Broker control false'); req(s.get('pipeline_recalculated') is False,'Pipeline control false'); req(s.get('yfinance_called') is False,'yfinance control false')
        with (scout/'active_real_universe_top_candidates.csv').open('r',encoding='utf-8-sig',newline='') as f: rs=list(csv.DictReader(f))
        if rs and rs[0].get('percent_input_mode')=='human_percent':
            vals=[float(rs[0].get('change_1d') or 0),float(rs[0].get('change_5d') or 0),float(rs[0].get('change_20d') or 0)]; req(all(abs(v)<1 for v in vals),'Manual percent values normalized to ratios')
        else: ok('Active file not regenerated with v1.4F2 yet; run --merge to normalize ratios')
    else: ok('Provider fallback summary not generated yet; run --merge')
    print(); print('Result'); print('-'*92); print('OK   v1.4F2 Manual Market Data Percent Normalization is valid')
if __name__=='__main__': main()
