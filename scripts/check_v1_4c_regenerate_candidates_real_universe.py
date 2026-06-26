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

    print("Scout Finance — v1.4C Regenerate Candidates From Real Universe checker")
    print("=" * 92)

    required = [
        root / "app.py",
        root / "src" / "real_universe_candidates.py",
        root / "scripts" / "check_v1_4c_regenerate_candidates_real_universe.py",
        root / "docs" / "v1" / "V1_4C_REGENERATE_CANDIDATES_REAL_UNIVERSE.md",
    ]

    for path in required:
        require(path.exists(), f"File exists: {path}")

    py_compile.compile(str(root / "app.py"), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(root / "src" / "real_universe_candidates.py"), doraise=True)
    ok("real_universe_candidates.py compiles")

    app_text = (root / "app.py").read_text(encoding="utf-8")
    for marker in [
        "v1.4C real universe candidates packaged",
        "active_real_universe_top_candidates.csv",
        "real_universe_candidates.csv",
        "v1.4C REAL UNIVERSE CANDIDATES HELPERS",
        "_sf14c_render_real_candidates_panel",
        "Candidatos desde universo real",
    ]:
        require(marker in app_text, f"app.py contains marker: {marker}")

    summary_path = out / "real_universe_candidates_summary.json"
    active_path = out / "active_real_universe_top_candidates.csv"
    candidates_path = out / "real_universe_candidates.csv"
    report_path = out / "real_universe_candidates_report.md"

    for path in [summary_path, active_path, candidates_path, report_path]:
        require(path.exists(), f"Generated file exists: {path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    require(summary.get("phase") == "v1.4C", "Summary phase OK")
    require(summary.get("status") in {"OK", "EMPTY"}, "Summary status valid")
    require(summary.get("scoring_is_placeholder_order_only") is True, "Placeholder scoring warning OK")
    require(summary.get("openai_called") is False, "OpenAI control false")
    require(summary.get("api_called") is False, "API control false")
    require(summary.get("yfinance_called") is False, "yfinance control false")
    require(summary.get("pipeline_recalculated") is False, "Pipeline control false")
    require(summary.get("scoring_recalculated") is False, "Scoring control false")

    if summary.get("status") == "OK":
        require(summary.get("candidates_generated", 0) > 0, "Candidates generated > 0")
        active_text = active_path.read_text(encoding="utf-8")
        require("INPUT_ONLY" in active_text, "Active candidates marked INPUT_ONLY")
        require("data/real/real_universe.csv" in active_text, "Active candidates source is real_universe.csv")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.4C Regenerate Candidates From Real Universe is valid")


if __name__ == "__main__":
    main()
