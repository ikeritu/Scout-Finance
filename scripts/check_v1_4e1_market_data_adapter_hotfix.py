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
    market = root / "outputs" / "market_data"
    scouting = root / "outputs" / "scouting"

    print("Scout Finance - v1.4E1 Market Data Adapter Hotfix checker")
    print("=" * 92)

    for path in [
        root / "app.py",
        root / "src" / "real_market_data_adapter.py",
        root / "scripts" / "check_v1_4e1_market_data_adapter_hotfix.py",
        root / "docs" / "v1" / "V1_4E1_MARKET_DATA_ADAPTER_HOTFIX.md",
    ]:
        require(path.exists(), f"File exists: {path}")

    py_compile.compile(str(root / "app.py"), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(root / "src" / "real_market_data_adapter.py"), doraise=True)
    ok("real_market_data_adapter.py compiles")

    app_text = (root / "app.py").read_text(encoding="utf-8")
    for marker in [
        "v1.4E1 market data adapter hotfix packaged",
        "market_data_score_yfinance_cache_v0",
        "MARKET_DATA_SCORE",
        "Market data adapter",
    ]:
        require(marker in app_text, f"app.py contains marker: {marker}")

    src_text = (root / "src" / "real_market_data_adapter.py").read_text(encoding="utf-8")
    for marker in [
        "v1.4E1 UTF-8 console hotfix",
        "sys.stdout.reconfigure",
        "replace(\"$\", \"\")",
    ]:
        require(marker in src_text, f"adapter contains marker: {marker}")

    summary_path = market / "real_market_data_summary.json"
    if summary_path.exists():
        for path in [
            summary_path,
            market / "real_market_data_rows.csv",
            market / "real_market_data_report.md",
            scouting / "real_universe_market_data_candidates.csv",
            scouting / "active_real_universe_top_candidates.csv",
        ]:
            require(path.exists(), f"Generated file exists: {path}")

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        require(summary.get("phase") in {"v1.4E", "v1.4E1"}, "Summary phase OK")
        require(summary.get("status") in {"OK", "PARTIAL_OR_ERROR", "MISSING_INPUT", "EMPTY"}, "Summary status valid")
        require(summary.get("score_method") == "market_data_score_yfinance_cache_v0", "Score method OK")
        require(summary.get("openai_called") is False, "OpenAI control false")
        require(summary.get("broker_called") is False, "Broker control false")
        require(summary.get("pipeline_recalculated") is False, "Pipeline control false")
        require(summary.get("financial_statement_scoring_recalculated") is False, "Financial statement scoring control false")

        active_text = (scouting / "active_real_universe_top_candidates.csv").read_text(encoding="utf-8")
        require("MARKET_DATA" in active_text, "Active candidates contain market data state")
    else:
        ok("Market data summary not generated yet; run src.real_market_data_adapter --fetch")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.4E1 Market Data Adapter Hotfix is valid")


if __name__ == "__main__":
    main()
