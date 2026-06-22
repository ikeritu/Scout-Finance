
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase8a_dashboard_final_design_summary.json"
REPORT_PATH = OUT_DIR / "phase8a_dashboard_final_design_report.md"
MATRIX_PATH = OUT_DIR / "phase8a_dashboard_final_design_matrix.csv"


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    print("Scout Finance — Phase 8A dashboard final design checker")
    print("=" * 88)

    for path in [SUMMARY_PATH, REPORT_PATH, MATRIX_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = read_json(SUMMARY_PATH)

    checks = [
        (summary.get("phase") == "8A", "Summary phase is 8A", f"Summary phase is not 8A: {summary.get('phase')}"),
        (summary.get("status") == "OK", "Summary status OK", f"Summary status is not OK: {summary.get('status')}"),
        (summary.get("phase7g_frozen") is True, "v0.7 frozen state detected", "v0.7 frozen state was not detected"),
        (summary.get("validated_funnel") == "500 → 182 → 63 → 6", "Funnel OK: 500 → 182 → 63 → 6", f"Unexpected funnel: {summary.get('validated_funnel')}"),
        (summary.get("final_tabs_count") == 9, "Final tabs count OK: 9", f"Unexpected final tabs count: {summary.get('final_tabs_count')}"),
    ]
    for passed, ok_msg, fail_msg in checks:
        if not passed:
            fail(fail_msg)
            return 1
        ok(ok_msg)

    controls = summary.get("controls", {})
    for key in ["openai_called", "api_called", "yfinance_called", "app_modified", "filters_modified", "pipeline_recalculated", "release_modified"]:
        if controls.get(key) is not False:
            fail(f"Invalid control {key}: {controls.get(key)}")
            return 1
        ok(f"Control OK: {key}=False")

    before = summary.get("signatures_before", {})
    after = summary.get("signatures_after", {})
    for name in ["app.py", "src/filters.py"]:
        if before.get(name) != after.get(name):
            fail(f"Signature changed unexpectedly: {name}")
            return 1
        ok(f"Signature unchanged: {name}")

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    for required in ["Inicio ejecutivo", "Ranking final", "Ficha de empresa", "Comparador", "Funnel y auditoría", "Datos y cobertura", "Feedback", "Exportaciones", "Configuración"]:
        if required not in report_text:
            fail(f"Report missing section/tab: {required}")
            return 1
        ok(f"Report contains: {required}")

    print()
    print("Result")
    print("-" * 88)
    ok("Phase 8A dashboard final design is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
