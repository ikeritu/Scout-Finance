from __future__ import annotations
import json, py_compile
from pathlib import Path

def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)

def main():
    root=Path(__file__).resolve().parents[1]
    out=root/"outputs"/"fundamentals"
    print("Scout Finance — v1.6A Fundamentals Input Bridge checker")
    print("="*92)
    for p in [
        root/"app.py",
        root/"src/fundamentals_input.py",
        root/"scripts/check_v1_6a_fundamentals_input_bridge.py",
        root/"docs/v1/V1_6A_FUNDAMENTALS_INPUT_BRIDGE.md",
        root/"data/real/manual_fundamentals_template.csv",
    ]:
        req(p.exists(),f"File exists: {p}")
    py_compile.compile(str(root/"app.py"),doraise=True); ok("app.py compiles")
    py_compile.compile(str(root/"src/fundamentals_input.py"),doraise=True); ok("fundamentals_input.py compiles")

    app_text=(root/"app.py").read_text(encoding="utf-8")
    for marker in [
        "v1.6A fundamentals input bridge packaged",
        "v1.6A FUNDAMENTALS INPUT BRIDGE PANEL",
        "_sf16a_render_fundamentals_panel",
        "Fundamentals input",
        "manual_fundamentals.csv",
    ]:
        req(marker in app_text,f"app.py contains marker: {marker}")

    script_text=(root/"src/fundamentals_input.py").read_text(encoding="utf-8")
    for marker in [
        "manual_fundamentals.csv",
        "manual_fundamentals_template.csv",
        "FUNDAMENTALS_INPUT_VALID",
        "manual_fundamentals_input_v0",
        "fundamentals_api_called",
    ]:
        req(marker in script_text,f"fundamentals_input.py contains marker: {marker}")

    header=(root/"data/real/manual_fundamentals_template.csv").read_text(encoding="utf-8").splitlines()[0]
    for col in ["ticker","revenue","revenue_growth_yoy","gross_margin","operating_margin","free_cash_flow","total_cash","total_debt"]:
        req(col in header,f"Template header contains: {col}")

    summary_path=out/"fundamentals_input_summary.json"
    if summary_path.exists():
        for p in [
            summary_path,
            out/"fundamentals_input_report.md",
            out/"manual_fundamentals_valid_rows.csv",
            out/"manual_fundamentals_issues.csv",
        ]:
            req(p.exists(),f"Generated file exists: {p}")
        s=json.loads(summary_path.read_text(encoding="utf-8"))
        req(s.get("phase")=="v1.6A","Summary phase OK")
        req(s.get("status") in {"OK","ERROR"},"Summary status valid")
        req(s.get("openai_called") is False,"OpenAI control false")
        req(s.get("broker_called") is False,"Broker control false")
        req(s.get("pipeline_recalculated") is False,"Pipeline control false")
        req(s.get("yfinance_called") is False,"yfinance control false")
        req(s.get("fundamentals_api_called") is False,"Fundamentals API control false")
    else:
        ok("Fundamentals summary not generated yet; run --validate")
    print()
    print("Result")
    print("-"*92)
    print("OK   v1.6A Fundamentals Input Bridge is valid")

if __name__=="__main__":
    main()
