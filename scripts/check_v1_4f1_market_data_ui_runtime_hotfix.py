from __future__ import annotations

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

    print("Scout Finance — v1.4F1 Market Data UI Runtime Hotfix checker")
    print("=" * 92)

    require(app.exists(), f"File exists: {app}")
    text = app.read_text(encoding="utf-8")

    markers = [
        "v1.4F1 market data UI runtime hotfix packaged",
        "v1.4F1 MARKET DATA UI RUNTIME HOTFIX HELPERS",
        "_sf14f_is_market_data_row",
        "_sf14f_provider_label",
        "_sf14f_render_market_data_notice",
        "MARKET_DATA_SCORE_MANUAL",
        "manual_market_data.csv",
    ]

    for marker in markers:
        require(marker in text, f"app.py contains marker: {marker}")

    helper_pos = text.find("def _sf14f_is_market_data_row")
    detail_pos = text.find("def _render_company_detail")
    main_call_pos = text.rfind("main()")

    require(helper_pos != -1, "Helper function exists")
    require(detail_pos != -1, "Company detail function exists")
    require(main_call_pos != -1, "main call exists")
    require(helper_pos < detail_pos, "Helper is defined before company detail")
    require(helper_pos < main_call_pos, "Helper is defined before main call")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.4F1 Market Data UI Runtime Hotfix is valid")


if __name__ == "__main__":
    main()
