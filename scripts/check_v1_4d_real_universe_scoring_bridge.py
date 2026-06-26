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
    out = root / "outputs" / "scouting"

    print("Scout Finance — v1.4D Real Universe Scoring Bridge checker")
    print("=" * 92)

    required = [
        root / "app.py",
        root / "src" / "real_universe_scoring_bridge.py",
        root / "scripts" / "check_v1_4d_real_universe_scoring_bridge.py",
        root / "docs" / "v1" / "V1_4D_REAL_UNIVERSE_SCORING_BRIDGE.md",
    ]

    for path in required:
        require(path.exists(), f"File exists: {path}")

    py_compile.compile(str(root / "app.py"), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(root / "src" / "real_universe_scoring_bridge.py"), doraise=True)
    ok("real_universe_scoring_bridge.py compiles")

    app_text = (root / "app.py").read_text(encoding="utf-8")
    for marker in [
        "v1.4D real universe scoring bridge packaged",
        "v1.4D REAL UNIVERSE SCORING BRIDGE HELPERS",
        "_sf14d_render_scoring_bridge_panel",
        "Scoring bridge universo real",
        "METADATA_SCORE",
        "no scoring financiero completo",
    ]:
        require(marker in app_text, f"app.py contains marker: {marker}")

    summary_path = out / "real_universe_scoring_bridge_summary.json"
    scored_path = out / "real_universe_scored_candidates.csv"
    active_path = out / "active_real_universe_top_candidates.csv"
    report_path = out / "real_universe_scoring_bridge_report.md"

    for path in [summary_path, scored_path, active_path, report_path]:
        require(path.exists(), f"Generated file exists: {path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    require(summary.get("phase") == "v1.4D", "Summary phase OK")
    require(summary.get("status") in {"OK", "EMPTY"}, "Summary status valid")
    require(summary.get("score_method") == "metadata_score_local_no_market_data", "Score method OK")
    require(summary.get("openai_called") is False, "OpenAI control false")
    require(summary.get("api_called") is False, "API control false")
    require(summary.get("yfinance_called") is False, "yfinance control false")
    require(summary.get("market_data_called") is False, "Market data control false")
    require(summary.get("pipeline_recalculated") is False, "Pipeline control false")
    require(summary.get("financial_scoring_recalculated") is False, "Financial scoring control false")

    if summary.get("status") == "OK":
        require(summary.get("candidates_scored", 0) > 0, "Candidates scored > 0")
        active_text = active_path.read_text(encoding="utf-8")
        require("METADATA_SCORE" in active_text, "Active candidates marked METADATA_SCORE")
        require("metadata_score_local_no_market_data" in active_text, "Active candidates contain score method")
        require("data/real/real_universe.csv" in active_text, "Active candidates source is real_universe.csv")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.4D Real Universe Scoring Bridge is valid")


if __name__ == "__main__":
    main()
