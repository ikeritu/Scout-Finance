from __future__ import annotations

import json
import py_compile
from pathlib import Path


def ok(msg: str) -> None:
    print("OK   " + msg)


def fail(msg: str) -> None:
    print("FAIL " + msg)
    raise SystemExit(1)


def require(condition: bool, msg: str) -> None:
    ok(msg) if condition else fail(msg)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    app = root / "app.py"
    src = root / "src" / "combined_scoring_v1.py"
    scoring = root / "outputs" / "scoring"
    scouting = root / "outputs" / "scouting"

    print("Scout Finance — v1.6C Combined Scoring v1 checker")
    print("=" * 92)

    for path in [
        app,
        src,
        root / "scripts" / "check_v1_6c_combined_scoring_v1.py",
        root / "docs" / "v1" / "V1_6C_COMBINED_SCORING_V1.md",
    ]:
        require(path.exists(), f"File exists: {path}")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(src), doraise=True)
    ok("combined_scoring_v1.py compiles")

    app_text = app.read_text(encoding="utf-8")
    for marker in [
        "v1.6C combined scoring v1 packaged",
        "v1.6C COMBINED SCORING V1 UI HELPERS",
        "_sf16c_render_combined_scoring_panel",
        "_sf16c_human_category",
        "_sf16c_human_status",
        "Combined scoring v1",
        "Score combinado v1",
        "Alta prioridad combinada",
    ]:
        require(marker in app_text, f"app.py contains marker: {marker}")

    src_text = src.read_text(encoding="utf-8")
    for marker in [
        "combined_score_v1",
        "metadata_score_component",
        "market_data_score_component",
        "fundamentals_score_component",
        "COMBINED_SCORE_V1",
        "fundamentals_api_called",
        "active_ranking_updated",
    ]:
        require(marker in src_text, f"combined_scoring_v1.py contains marker: {marker}")

    summary_path = scoring / "combined_score_v1_summary.json"
    if summary_path.exists():
        for path in [
            summary_path,
            scoring / "combined_score_v1_breakdown.csv",
            scoring / "combined_score_v1_report.md",
            scouting / "combined_score_v1_candidates.csv",
            scouting / "active_real_universe_top_candidates.csv",
        ]:
            require(path.exists(), f"Generated file exists: {path}")

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        require(summary.get("phase") == "v1.6C", "Summary phase OK")
        require(summary.get("status") == "OK", "Summary status OK")
        require(summary.get("rows_scored", 0) >= 1, "Rows scored >= 1")
        require(summary.get("fundamentals_matched", 0) >= 1, "Fundamentals matched >= 1")
        require(summary.get("openai_called") is False, "OpenAI control false")
        require(summary.get("broker_called") is False, "Broker control false")
        require(summary.get("pipeline_recalculated") is False, "Pipeline control false")
        require(summary.get("yfinance_called") is False, "yfinance control false")
        require(summary.get("fundamentals_api_called") is False, "Fundamentals API control false")
        require(summary.get("active_ranking_updated") is True, "Active ranking updated")
    else:
        ok("Combined scoring summary not generated yet; run --score")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.6C Combined Scoring v1 is valid")


if __name__ == "__main__":
    main()
