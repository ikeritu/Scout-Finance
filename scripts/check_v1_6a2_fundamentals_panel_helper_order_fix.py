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
    print("Scout Finance — v1.6A2 Fundamentals Panel Helper Order Fix checker")
    print("="*92)

    req(app.exists(), f"File exists: {app}")
    text=app.read_text(encoding="utf-8")

    for marker in [
        "v1.6A2 fundamentals panel helper order fix packaged",
        "v1.6A fundamentals input bridge packaged",
        "v1.6A FUNDAMENTALS INPUT BRIDGE PANEL",
        "def _sf16a_render_fundamentals_panel",
        "def _render_dashboard_tab",
        "_sf16a_render_fundamentals_panel()",
        "Fundamentals input",
        "manual_fundamentals.csv",
    ]:
        req(marker in text, f"app.py contains marker: {marker}")

    helper_pos=text.find("def _sf16a_render_fundamentals_panel")
    dashboard_pos=text.find("def _render_dashboard_tab")
    call_pos=text.find("_sf16a_render_fundamentals_panel()", dashboard_pos)
    main_call_pos=text.rfind("main()")
    run_pos=text.find("_render_run_controls(mode)", dashboard_pos)

    req(helper_pos != -1, "Helper definition exists")
    req(dashboard_pos != -1, "Dashboard function exists")
    req(call_pos != -1, "Dashboard call exists")
    req(helper_pos < dashboard_pos, "Helper is defined before dashboard function")
    req(dashboard_pos < call_pos, "Call is inside/after dashboard function")
    req(call_pos < run_pos, "Panel appears before execution controls")
    req(call_pos < main_call_pos, "Call appears before main invocation")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(root/"src"/"fundamentals_input.py"), doraise=True)
    ok("fundamentals_input.py compiles")

    summary_path=out/"fundamentals_input_summary.json"
    if summary_path.exists():
        s=json.loads(summary_path.read_text(encoding="utf-8"))
        req(s.get("phase")=="v1.6A", "Summary phase OK")
        req(s.get("status") in {"OK","ERROR"}, "Summary status valid")
        req(s.get("openai_called") is False, "OpenAI control false")
        req(s.get("broker_called") is False, "Broker control false")
        req(s.get("yfinance_called") is False, "yfinance control false")
        req(s.get("fundamentals_api_called") is False, "Fundamentals API control false")
    else:
        ok("Fundamentals summary not generated yet; run --validate")

    print()
    print("Result")
    print("-"*92)
    print("OK   v1.6A2 Fundamentals Panel Helper Order Fix is valid")

if __name__=="__main__":
    main()
