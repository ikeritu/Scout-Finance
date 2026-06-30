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

    print("Scout Finance — v1.5A Local Scoring v0 checker")
    print("=" * 92)

    for path in [
        root / "app.py",
        root / "src" / "local_scoring_v0.py",
        root / "scripts" / "check_v1_5a_local_scoring_v0.py",
        root / "docs" / "v1" / "V1_5A_LOCAL_SCORING_V0.md",
    ]:
        require(path.exists(), f"File exists: {path}")

    py_compile.compile(str(root / "app.py"), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(root / "src" / "local_scoring_v0.py"), doraise=True)
    ok("local_scoring_v0.py compiles")

    app_text = (root / "app.py").read_text(encoding="utf-8")
    for marker in [
        "v1.5A local scoring v0 packaged",
        "v1.5A LOCAL SCORING V0 HELPERS",
        "_sf15a_render_local_scoring_panel",
        "_sf15a_is_local_score_row",
        "LOCAL_SCORE_V0",
        "local_score_v0",
    ]:
        require(marker in app_text, f"app.py contains marker: {marker}")

    summary_path = score_dir / "local_score_v0_summary.json"
    if summary_path.exists():
        for path in [
            summary_path,
            score_dir / "local_score_v0_breakdown.csv",
            score_dir / "local_score_v0_report.md",
            scout / "local_score_v0_candidates.csv",
            scout / "active_real_universe_top_candidates.csv",
        ]:
            require(path.exists(), f"Generated file exists: {path}")

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        require(summary.get("phase") == "v1.5A", "Summary phase OK")
        require(summary.get("status") in {"OK", "EMPTY"}, "Summary status valid")
        require(summary.get("score_method") == "local_score_v0", "Score method OK")
        require(summary.get("openai_called") is False, "OpenAI control false")
        require(summary.get("broker_called") is False, "Broker control false")
        require(summary.get("pipeline_recalculated") is False, "Pipeline control false")
        require(summary.get("yfinance_called") is False, "yfinance control false")
        require(summary.get("financial_statement_scoring_recalculated") is False, "Financial statement scoring control false")

        with (scout / "active_real_universe_top_candidates.csv").open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        if rows:
            required_cols = [
                "local_score_v0",
                "metadata_component_score",
                "market_data_component_score",
                "liquidity_component_score",
                "momentum_component_score",
                "data_quality_component_score",
                "penalty_score",
                "local_score_reason",
            ]
            for col in required_cols:
                require(col in rows[0], f"Active candidates contain column: {col}")
            require(any(r.get("stage3_status") == "LOCAL_SCORE_V0" for r in rows), "Active candidates contain LOCAL_SCORE_V0 status")
    else:
        ok("Local score summary not generated yet; run --score")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.5A Local Scoring v0 is valid")


if __name__ == "__main__":
    main()
