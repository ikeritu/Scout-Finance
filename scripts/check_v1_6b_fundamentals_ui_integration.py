from __future__ import annotations
import json
import py_compile
from pathlib import Path

def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)

def main():
    root=Path(__file__).resolve().parents[1]
    app=root/"app.py"
    out=root/"outputs"/"fundamentals"
    print("Scout Finance — v1.6B Fundamentals UI Integration checker")
    print("="*92)

    req(app.exists(), f"File exists: {app}")
    text=app.read_text(encoding="utf-8")

    for marker in [
        "v1.6B fundamentals UI integration packaged",
        "v1.6B FUNDAMENTALS UI INTEGRATION HELPERS",
        "_sf16b_load_fundamentals_df",
        "_sf16b_get_fundamentals_for_ticker",
        "_sf16b_fundamentals_status_for_ticker",
        "_sf16b_render_fundamentals_block",
        "_sf16b_render_fundamentals_block(row)",
        "Fundamentales",
        "Revenue",
        "Crecimiento YoY",
        "Gross margin",
        "Operating margin",
        "Free cash flow",
        "manual_fundamentals.csv",
    ]:
        req(marker in text, f"app.py contains marker: {marker}")

    helper_pos=text.find("def _sf16b_render_fundamentals_block")
    ranking_pos=text.find("def _build_clean_ranking_table")
    company_pos=text.find("def _render_company_detail")
    ranking_call_pos=text.find("_sf16b_fundamentals_status_for_ticker", ranking_pos)
    company_call_pos=text.find("_sf16b_render_fundamentals_block(row)", company_pos)
    main_call_pos=text.rfind("main()")

    req(helper_pos != -1, "v1.6B helper exists")
    req(ranking_pos != -1, "Ranking table builder exists")
    req(company_pos != -1, "Company detail function exists")
    req(helper_pos < ranking_pos, "v1.6B helper defined before ranking builder")
    req(helper_pos < company_pos, "v1.6B helper defined before company detail")
    req(ranking_call_pos != -1, "Ranking adds fundamentals status")
    req(company_call_pos != -1, "Company detail renders fundamentals block")
    req(company_call_pos < main_call_pos, "Company fundamentals call before main invocation")

    req((root/"outputs"/"fundamentals"/"manual_fundamentals_valid_rows.csv").exists(), "Validated fundamentals rows exist")
    req((root/"data"/"real"/"manual_fundamentals.csv").exists(), "Manual fundamentals CSV exists")

    summary_path=out/"fundamentals_input_summary.json"
    req(summary_path.exists(), "Fundamentals summary exists")
    s=json.loads(summary_path.read_text(encoding="utf-8"))
    req(s.get("phase")=="v1.6A", "Summary phase OK")
    req(s.get("status")=="OK", "Fundamentals input status OK")
    req(s.get("valid_tickers", 0) >= 1, "At least one valid fundamentals ticker")
    req(s.get("openai_called") is False, "OpenAI control false")
    req(s.get("broker_called") is False, "Broker control false")
    req(s.get("yfinance_called") is False, "yfinance control false")
    req(s.get("fundamentals_api_called") is False, "Fundamentals API control false")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")

    print()
    print("Result")
    print("-"*92)
    print("OK   v1.6B Fundamentals UI Integration is valid")

if __name__=="__main__":
    main()
