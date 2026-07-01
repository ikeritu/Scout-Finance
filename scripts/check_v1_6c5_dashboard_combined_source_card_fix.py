from __future__ import annotations
import csv, json, py_compile
from pathlib import Path

def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)

def main():
    root=Path(__file__).resolve().parents[1]
    app=root/"app.py"
    src=root/"src/combined_scoring_v1.py"
    summary=root/"outputs/scoring/combined_score_v1_summary.json"
    active=root/"outputs/scouting/active_real_universe_top_candidates.csv"

    print("Scout Finance — v1.6C5 Dashboard Combined Source Card Fix checker")
    print("="*92)

    req(app.exists(), f"File exists: {app}")
    req(src.exists(), f"File exists: {src}")

    text=app.read_text(encoding="utf-8")
    src_text=src.read_text(encoding="utf-8")

    for marker in [
        "v1.6C5 dashboard combined source card fix packaged",
        "v1.6C5 DASHBOARD COMBINED SOURCE CARD FIX HELPERS",
        "_sf16c5_active_combined_summary",
        "_sf16c5_is_combined_active",
        "_sf16c5_source_card_label",
        "_sf16c5_render_dashboard_combined_notice",
        "Score combinado v1",
        "Ranking activo: COMBINED_SCORE_V1",
    ]:
        req(marker in text, f"app.py contains marker: {marker}")

    req("_sf16c5_source_card_label" in text, "Source card uses combined source label helper")
    req("_sf16c5_render_dashboard_combined_notice()" in text, "Dashboard renders combined notice")
    req("v1.6C5 dashboard combined source card compatible" in src_text, "combined_scoring_v1.py contains v1.6C5 marker")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(src), doraise=True)
    ok("combined_scoring_v1.py compiles")

    if summary.exists() and active.exists():
        s=json.loads(summary.read_text(encoding="utf-8"))
        req(s.get("phase")=="v1.6C", "Summary phase OK")
        req(s.get("status")=="OK", "Summary status OK")
        with active.open("r", encoding="utf-8-sig", newline="") as f:
            rows=list(csv.DictReader(f))
        req(bool(rows), "Active ranking has rows")
        row=rows[0]
        req(row.get("stage3_status")=="COMBINED_SCORE_V1", "Active ranking status combined")
        req(row.get("combined_score_v1") == row.get("score"), "Active score is combined")
    else:
        ok("Combined outputs not regenerated yet; run --score")

    print()
    print("Result")
    print("-"*92)
    print("OK   v1.6C5 Dashboard Combined Source Card Fix is valid")

if __name__=="__main__":
    main()
