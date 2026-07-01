from __future__ import annotations
import json, py_compile
from pathlib import Path

def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)

def main():
    root=Path(__file__).resolve().parents[1]
    app=root/"app.py"
    src=root/"src/combined_scoring_v1.py"
    print("Scout Finance — v1.6C1 Combined Score UI Priority Fix checker")
    print("="*92)
    req(app.exists(), f"File exists: {app}")
    req(src.exists(), f"File exists: {src}")
    text=app.read_text(encoding="utf-8")
    for m in [
        "v1.6C1 combined score UI priority fix packaged",
        "v1.6C1 COMBINED SCORE UI PRIORITY FIX HELPERS",
        "_sf16c1_active_score",
        "_sf16c1_human_category",
        "_sf16c1_human_status",
        "_sf16c1_humanize_ranking_df",
        "clean_df = _sf16c1_humanize_ranking_df(clean_df)",
        "Score combinado v1",
        "Alta prioridad combinada",
    ]:
        req(m in text, f"app.py contains marker: {m}")
    helper_pos=text.find("def _sf16c1_active_score")
    ranking_pos=text.find("def _build_clean_ranking_table")
    company_pos=text.find("def _render_company_detail")
    req(helper_pos < ranking_pos, "v1.6C1 helper before ranking builder")
    req(helper_pos < company_pos, "v1.6C1 helper before company detail")
    req("_sf16c1_active_score(row)" in text, "Company score uses combined-priority helper")
    req("_sf16c1_human_category(row)" in text, "Company category uses combined-priority helper")
    req("_sf16c1_human_status(row)" in text, "Company status uses combined-priority helper")
    src_text=src.read_text(encoding="utf-8")
    req("v1.6C1 preserves combined score as active score" in src_text, "Scoring script contains v1.6C1 marker")
    req('out["score"] = combined' in src_text, "Scoring script writes active score as combined")
    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(src), doraise=True)
    ok("combined_scoring_v1.py compiles")
    print()
    print("Result")
    print("-"*92)
    print("OK   v1.6C1 Combined Score UI Priority Fix is valid")

if __name__=="__main__":
    main()
