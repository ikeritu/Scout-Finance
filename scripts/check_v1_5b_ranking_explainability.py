from __future__ import annotations

import csv
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
    score_dir = root / "outputs" / "scoring"
    scout = root / "outputs" / "scouting"

    print("Scout Finance — v1.5B Ranking Explainability checker")
    print("=" * 92)

    for path in [
        root / "app.py",
        root / "src" / "ranking_explainability.py",
        root / "scripts" / "check_v1_5b_ranking_explainability.py",
        root / "docs" / "v1" / "V1_5B_RANKING_EXPLAINABILITY.md",
    ]:
        require(path.exists(), f"File exists: {path}")

    py_compile.compile(str(root / "app.py"), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(root / "src" / "ranking_explainability.py"), doraise=True)
    ok("ranking_explainability.py compiles")

    app_text = (root / "app.py").read_text(encoding="utf-8")
    for marker in [
        "v1.5B ranking explainability packaged",
        "v1.5B RANKING EXPLAINABILITY HELPERS",
        "_sf15b_render_explainability_block",
        "_sf15b_render_explainability_panel",
        "positive_factors",
        "negative_factors",
        "missing_data_flags",
        "review_flags",
        "Ranking Explainability",
    ]:
        require(marker in app_text, f"app.py contains marker: {marker}")

    summary_path = score_dir / "ranking_explainability_summary.json"
    if summary_path.exists():
        for path in [
            summary_path,
            score_dir / "ranking_explainability_factors.csv",
            score_dir / "ranking_explainability_report.md",
            scout / "ranking_explainability_candidates.csv",
            scout / "active_real_universe_top_candidates.csv",
        ]:
            require(path.exists(), f"Generated file exists: {path}")

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        require(summary.get("phase") == "v1.5B", "Summary phase OK")
        require(summary.get("status") in {"OK", "EMPTY"}, "Summary status valid")
        require(summary.get("explainability_method") == "ranking_explainability_v0", "Explainability method OK")
        require(summary.get("openai_called") is False, "OpenAI control false")
        require(summary.get("broker_called") is False, "Broker control false")
        require(summary.get("pipeline_recalculated") is False, "Pipeline control false")
        require(summary.get("yfinance_called") is False, "yfinance control false")

        with (scout / "active_real_universe_top_candidates.csv").open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        if rows:
            for col in ["explainability_summary", "positive_factors", "negative_factors", "missing_data_flags", "review_flags", "explainability_badges"]:
                require(col in rows[0], f"Active candidates contain column: {col}")
    else:
        ok("Explainability summary not generated yet; run --explain")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.5B Ranking Explainability is valid")


if __name__ == "__main__":
    main()
