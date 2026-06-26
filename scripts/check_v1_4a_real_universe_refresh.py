from __future__ import annotations
import py_compile
from pathlib import Path

def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)

def main():
    root=Path(__file__).resolve().parents[1]
    app=root/"app.py"
    print("Scout Finance — v1.4A Real Universe Refresh checker")
    print("="*92)
    req(app.exists(), f"File exists: {app}")
    text=app.read_text(encoding="utf-8")
    markers=[
        "v1.4A data source transparency packaged",
        "v1.4A DATA SOURCE TRANSPARENCY HELPERS",
        "_sf14a_file_info",
        "_sf14a_build_data_source_audit",
        "_sf14a_detect_active_source",
        "_sf14a_render_data_source_panel",
        "Fuente de datos activa",
        "Auditar archivos que alimentan la interfaz",
        "Cómo conseguir empresas distintas",
        "phase7c4_pipeline_revalidation_top_candidates.csv",
        "top_100_candidates.csv",
        "outputs/analyses",
        "data/demo",
        "data/real",
        "_sf14a_render_data_source_panel(mode=mode, top_n=top_n)",
    ]
    for marker in markers:
        req(marker in text, f"app.py contains marker: {marker}")
    for forbidden in ["openai.ChatCompletion.create", "yf.download(", "yfinance.download(", "requests.get("]:
        req(forbidden not in text, f"No forbidden external call marker: {forbidden}")
    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")
    print()
    print("Result")
    print("-"*92)
    print("OK   v1.4A Real Universe Refresh is valid")

if __name__=="__main__":
    main()
