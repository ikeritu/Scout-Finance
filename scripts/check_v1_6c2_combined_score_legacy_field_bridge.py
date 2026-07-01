from __future__ import annotations
import csv, json, py_compile
from pathlib import Path

def ok(m): print("OK   "+m)
def fail(m): print("FAIL "+m); raise SystemExit(1)
def req(c,m): ok(m) if c else fail(m)

def read_first(path: Path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows=list(csv.DictReader(f))
    return rows[0] if rows else {}

def main():
    root=Path(__file__).resolve().parents[1]
    app=root/"app.py"
    src=root/"src/combined_scoring_v1.py"
    active=root/"outputs/scouting/active_real_universe_top_candidates.csv"
    summary=root/"outputs/scoring/combined_score_v1_summary.json"

    print("Scout Finance — v1.6C2 Combined Score Legacy Field Bridge checker")
    print("="*92)

    req(app.exists(), f"File exists: {app}")
    req(src.exists(), f"File exists: {src}")
    text=app.read_text(encoding="utf-8")
    src_text=src.read_text(encoding="utf-8")

    for m in [
        "v1.6C2 combined score legacy field bridge packaged",
        "v1.6C2 COMBINED SCORE LEGACY FIELD BRIDGE UI HELPERS",
        "_sf16c2_humanize_any_ranking_df",
        "clean_df = _sf16c2_humanize_any_ranking_df(clean_df)",
        "Score combinado v1",
        "Alta prioridad combinada",
    ]:
        req(m in text, f"app.py contains marker: {m}")

    for m in [
        "v1.6C2 legacy UI compatibility bridge",
        'out["local_score_v0"] = combined',
        'out["score_final"] = combined',
        'out["display_score"] = combined',
        'out["category"] = cat',
        'out["category_label"] = human_category(cat)',
        'out["status"] = "COMBINED_SCORE_V1"',
    ]:
        req(m in src_text, f"combined_scoring_v1.py contains marker: {m}")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(src), doraise=True)
    ok("combined_scoring_v1.py compiles")

    if summary.exists() and active.exists():
        s=json.loads(summary.read_text(encoding="utf-8"))
        req(s.get("phase")=="v1.6C", "Summary phase OK")
        row=read_first(active)
        req(row.get("stage3_status")=="COMBINED_SCORE_V1", "Active row status is combined")
        req(row.get("category_final","").startswith("combined_score_"), "Active row category is combined")
        req(row.get("combined_score_v1") == row.get("score") or row.get("combined_score_v1") == row.get("local_score_v0"), "Legacy score fields point to combined score")
    else:
        ok("Combined outputs not regenerated yet; run --score")

    print()
    print("Result")
    print("-"*92)
    print("OK   v1.6C2 Combined Score Legacy Field Bridge is valid")

if __name__=="__main__":
    main()
