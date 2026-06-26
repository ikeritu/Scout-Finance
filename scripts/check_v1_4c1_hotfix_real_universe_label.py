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

    print("Scout Finance — v1.4C1 Hotfix Real Universe Label checker")
    print("=" * 92)

    require(app.exists(), f"File exists: {app}")
    text = app.read_text(encoding="utf-8")

    markers = [
        "v1.4C1 hotfix real universe label packaged",
        "Universo real input",
        "real_universe_input",
        "active_real_universe_top_candidates.csv",
        "Estado INPUT_ONLY: no es scoring financiero real",
        "Estado: `INPUT_ONLY`; no es scoring financiero real.",
        "INPUT_ONLY · no scoring financiero real",
        "normalized.attrs[\"sf12a_source\"] = \"real_universe_input\"",
    ]

    for marker in markers:
        require(marker in text, f"app.py contains marker: {marker}")

    py_compile.compile(str(app), doraise=True)
    ok("app.py compiles")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.4C1 Hotfix Real Universe Label is valid")


if __name__ == "__main__":
    main()
