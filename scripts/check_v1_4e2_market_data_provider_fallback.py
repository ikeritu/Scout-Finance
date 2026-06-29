from __future__ import annotations
import json, py_compile
from pathlib import Path
def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)
def main():
    root=Path(__file__).resolve().parents[1]; market=root/"outputs"/"market_data"; scout=root/"outputs"/"scouting"
    print("Scout Finance — v1.4E2 Market Data Provider Fallback checker"); print("="*92)
    for p in [root/"app.py",root/"src/market_data_provider_fallback.py",root/"scripts/check_v1_4e2_market_data_provider_fallback.py",root/"docs/v1/V1_4E2_MARKET_DATA_PROVIDER_FALLBACK.md",root/"data/real/manual_market_data_template.csv"]:
        req(p.exists(),f"File exists: {p}")
    py_compile.compile(str(root/"app.py"),doraise=True); ok("app.py compiles")
    py_compile.compile(str(root/"src/market_data_provider_fallback.py"),doraise=True); ok("market_data_provider_fallback.py compiles")
    text=(root/"app.py").read_text(encoding="utf-8")
    for m in ["v1.4E2 market data provider fallback packaged","v1.4E2 MARKET DATA PROVIDER FALLBACK HELPERS","_sf14e2_render_provider_fallback_panel","Market data provider fallback"]:
        req(m in text,f"app.py contains marker: {m}")
    req((root/"data/real/manual_market_data_template.csv").read_text(encoding="utf-8").splitlines()[0].startswith("ticker,price,market_cap,volume,average_volume"),"Manual template header OK")
    sp=market/"market_data_provider_fallback_summary.json"
    if sp.exists():
        for p in [sp,market/"market_data_provider_fallback_rows.csv",market/"market_data_provider_fallback_report.md",scout/"real_universe_market_data_candidates.csv",scout/"active_real_universe_top_candidates.csv"]:
            req(p.exists(),f"Generated file exists: {p}")
        s=json.loads(sp.read_text(encoding="utf-8"))
        req(s.get("phase")=="v1.4E2","Summary phase OK")
        req(s.get("status") in {"OK","ERROR","EMPTY"},"Summary status valid")
        req(s.get("score_method")=="market_data_provider_fallback_v0","Score method OK")
        req(s.get("openai_called") is False,"OpenAI control false")
        req(s.get("broker_called") is False,"Broker control false")
        req(s.get("pipeline_recalculated") is False,"Pipeline control false")
        req(s.get("yfinance_called") is False,"yfinance control false")
        active=(scout/"active_real_universe_top_candidates.csv").read_text(encoding="utf-8")
        req(any(x in active for x in ["MARKET_DATA_SCORE_MANUAL","MARKET_DATA_SCORE_YFINANCE","METADATA_SCORE_FALLBACK"]),"Active candidates contain provider fallback state")
    else: ok("Provider fallback summary not generated yet; run --merge")
    print(); print("Result"); print("-"*92); print("OK   v1.4E2 Market Data Provider Fallback is valid")
if __name__=="__main__": main()
