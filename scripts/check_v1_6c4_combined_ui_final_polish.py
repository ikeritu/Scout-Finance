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

    print("Scout Finance — v1.6C4 Combined UI Final Polish checker")
    print("="*92)

    req(app.exists(), f"File exists: {app}")
    req(src.exists(), f"File exists: {src}")

    text=app.read_text(encoding="utf-8")
    src_text=src.read_text(encoding="utf-8")

    for marker in [
        "v1.6C4 combined UI final polish packaged",
        "v1.6C4 COMBINED UI FINAL POLISH HELPERS",
        "_sf16c4_active_reason",
        "_sf16c4_active_source_label",
        "_sf16c4_is_combined_active",
        "Score combinado v1",
    ]:
        req(marker in text, f"app.py contains marker: {marker}")

    for marker in [
        "v1.6C4 combined UI final polish compatible",
        'out["reason_to_pass_quant"] = summary',
        'out["local_score_reason"] = summary',
    ]:
        req(marker in src_text, f"combined_scoring_v1.py contains marker: {marker}")

    req("_sf16c4_active_reason(row)" in text, "Company reason uses combined active reason helper")
    req("_sf16c4_active_source_label" in text, "Dashboard/source can use combined source helper")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(src), doraise=True)
    ok("combined_scoring_v1.py compiles")

    if active.exists():
        row=read_first(active)
        req(row.get("stage3_status")=="COMBINED_SCORE_V1", "Active row status combined")
        req(str(row.get("score_reason","")).startswith("COMBINED_SCORE_V1"), "Active score_reason starts with COMBINED_SCORE_V1")
    else:
        ok("Active ranking not generated yet; run --score")

    print()
    print("Result")
    print("-"*92)
    print("OK   v1.6C4 Combined UI Final Polish is valid")

if __name__=="__main__":
    main()
