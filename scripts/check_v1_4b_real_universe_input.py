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

    print("Scout Finance — v1.4B Real Universe Input checker")
    print("=" * 92)

    required = [
        root / "app.py",
        root / "src" / "real_universe_input.py",
        root / "scripts" / "check_v1_4b_real_universe_input.py",
        root / "docs" / "v1" / "V1_4B_REAL_UNIVERSE_INPUT.md",
        root / "data" / "real" / "universe_template.csv",
    ]

    for path in required:
        require(path.exists(), f"File exists: {path}")

    py_compile.compile(str(root / "app.py"), doraise=True)
    ok("app.py compiles")
    py_compile.compile(str(root / "src" / "real_universe_input.py"), doraise=True)
    ok("real_universe_input.py compiles")

    app_text = (root / "app.py").read_text(encoding="utf-8")
    for marker in [
        "v1.4B real universe input packaged",
        "v1.4B REAL UNIVERSE INPUT MVP HELPERS",
        "_sf14b_render_real_universe_panel",
        "Universo real de entrada",
        "real_universe.csv",
        "universe_template.csv",
    ]:
        require(marker in app_text, f"app.py contains marker: {marker}")

    template = (root / "data" / "real" / "universe_template.csv").read_text(encoding="utf-8")
    header = template.splitlines()[0].strip()
    require(header == "ticker,name,exchange,country,sector,industry", "Template header OK")

    summary_path = root / "outputs" / "scouting" / "real_universe_input_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        require(summary.get("phase") == "v1.4B", "Summary phase OK")
        require(summary.get("openai_called") is False, "OpenAI control false")
        require(summary.get("api_called") is False, "API control false")
        require(summary.get("yfinance_called") is False, "yfinance control false")
        require(summary.get("pipeline_recalculated") is False, "Pipeline control false")
    else:
        ok("Summary not generated yet; validate real_universe.csv to create it")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.4B Real Universe Input is valid")


if __name__ == "__main__":
    main()
