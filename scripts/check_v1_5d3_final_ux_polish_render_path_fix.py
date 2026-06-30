from __future__ import annotations
import py_compile
from pathlib import Path

def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)

def main():
    root=Path(__file__).resolve().parents[1]
    app=root/"app.py"
    print("Scout Finance — v1.5D3 Final UX Polish Render Path Fix checker")
    print("="*92)
    req(app.exists(),f"File exists: {app}")
    text=app.read_text(encoding="utf-8")
    markers=[
        "v1.5D3 final UX polish render path fix packaged",
        "v1.5D3 FINAL UX POLISH RENDER PATH FIX HELPERS",
        "_sf15d3_human_category",
        "_sf15d3_human_provider",
        "_sf15d3_humanize_ranking_df",
        "_sf15d3_render_company_explainability",
        "_sf15d3_render_company_explainability(row)",
        "Alta prioridad local",
        "Score local v0",
        "Manual",
        "Lectura del ranking",
        "Sube por",
        "Vigilar",
        "Revisión",
    ]
    for m in markers:
        req(m in text,f"app.py contains marker: {m}")
    req('col2.metric("Categoría", _sf15d3_human_category(row.get("category_final")))' in text, "Category metric uses v1.5D3 humanizer")
    req("clean_df = _sf15d3_humanize_ranking_df(clean_df)" in text, "Clean ranking table is humanized before return")
    detail_pos=text.find("def _render_company_detail")
    call_pos=text.find("_sf15d3_render_company_explainability(row)", detail_pos)
    state_pos=text.find("Estado IA legacy resumido", detail_pos)
    req(detail_pos != -1, "Company detail function exists")
    req(call_pos != -1, "Explainability block call exists in company detail")
    req(state_pos == -1 or call_pos < state_pos, "Explainability block appears before legacy IA section")
    py_compile.compile(str(app),doraise=True)
    ok("app.py compiles")
    print()
    print("Result")
    print("-"*92)
    print("OK   v1.5D3 Final UX Polish Render Path Fix is valid")

if __name__=="__main__":
    main()
