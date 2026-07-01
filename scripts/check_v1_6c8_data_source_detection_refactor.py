from __future__ import annotations
import csv
import json
import py_compile
import re
from pathlib import Path

def ok(msg: str) -> None:
    print("OK   " + msg)

def fail(msg: str) -> None:
    print("FAIL " + msg)
    raise SystemExit(1)

def require(condition: bool, msg: str) -> None:
    ok(msg) if condition else fail(msg)

def function_body(text: str, name: str) -> str:
    match = re.search(rf"^def {re.escape(name)}\b.*?(?=^def |\Z)", text, flags=re.M | re.S)
    if not match:
        fail(f"Function not found: {name}")
    return match.group(0)

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    app = root / "app.py"
    src = root / "src" / "combined_scoring_v1.py"
    active = root / "outputs" / "scouting" / "active_real_universe_top_candidates.csv"
    summary = root / "outputs" / "scoring" / "combined_score_v1_summary.json"

    print("Scout Finance â€” v1.6C8 Data Source Detection Refactor checker")
    print("=" * 92)

    require(app.exists(), f"File exists: {app}")
    require(src.exists(), f"File exists: {src}")

    text = app.read_text(encoding="utf-8")
    src_text = src.read_text(encoding="utf-8")

    for marker in [
        "v1.6C8 data source detection refactor packaged",
        "COMBINED_SCORE_V1 is now a first-class source",
        '"active_source": "combined_score_v1"',
        '"label": "Score combinado v1"',
        "Ranking activo generado por COMBINED_SCORE_V1",
        'c1.metric("Fuente", status["label"])',
        'if status["active_source"] == "combined_score_v1"',
    ]:
        require(marker in text, f"app.py contains marker: {marker}")

    detect = function_body(text, "_sf14a_detect_active_source")
    render = function_body(text, "_sf14a_render_data_source_panel")

    require("_sf12a_load_revalidated_candidates" in detect, "Detector checks active/fallback dataframe")
    require("combined_score_v1" in detect, "Detector has combined_score_v1 branch")
    require("latest_final_view" in detect, "Detector still supports latest final view")
    require("real_universe_input" in detect, "Detector still supports real universe input")
    require("revalidated_funnel_fallback" in detect, "Detector still supports legacy fallback")

    require("_sf16c5_source_card_label" not in render, "Render no longer depends on v1.6C5 source helper")
    require("final_df.attrs" not in render, "Render no longer depends on unrelated final_df attrs")
    require('status["label"]' in render, "Render uses status label directly")

    require("v1.6C8 data source detection refactor compatible" in src_text, "combined_scoring_v1.py contains v1.6C8 marker")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(src), doraise=True)
    ok("combined_scoring_v1.py compiles")

    if summary.exists() and active.exists():
        s = json.loads(summary.read_text(encoding="utf-8"))
        require(s.get("phase") == "v1.6C", "Summary phase OK")
        require(s.get("status") == "OK", "Summary status OK")
        with active.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        require(bool(rows), "Active ranking has rows")
        row = rows[0]
        require(row.get("stage3_status") == "COMBINED_SCORE_V1", "Active ranking status combined")
        require(row.get("combined_score_v1") == row.get("score"), "Active score is combined")
    else:
        ok("Combined outputs not regenerated yet; run --score")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.6C8 Data Source Detection Refactor is valid")

if __name__ == "__main__":
    main()

