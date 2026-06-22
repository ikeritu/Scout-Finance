
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

COMPARISON_JSON = SCOUTING_OUTPUTS_DIR / "institutional_cleaning_comparison_report.json"
COMPARISON_CSV = SCOUTING_OUTPUTS_DIR / "institutional_cleaning_comparison_metrics.csv"
COMPARISON_MD = SCOUTING_OUTPUTS_DIR / "institutional_cleaning_comparison_report.md"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7A.4 Institutional Cleaning Comparison checker")
    print("=" * 82)

    for path in [COMPARISON_JSON, COMPARISON_CSV, COMPARISON_MD]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    try:
        report = json.loads(COMPARISON_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read comparison JSON: {exc}")
        return 1

    if report.get("phase") != "7A.4":
        fail(f"Report phase is not 7A.4: {report.get('phase')}")
        return 1
    ok("Report phase is 7A.4")

    if report.get("status") != "OK":
        fail(f"Report status is not OK: {report.get('status')}")
        return 1
    ok("Report status OK")

    for flag, label in [
        ("openai_called", "OpenAI was not called"),
        ("paid_api_called", "Paid API was not called"),
        ("yfinance_called", "yfinance was not called by this report"),
        ("app_modified", "app.py was not modified"),
        ("release_v0_6_modified", "release v0.6 was not modified"),
    ]:
        if report.get(flag) is False:
            ok(label)
        else:
            fail(f"Invalid flag: {flag}")
            return 1

    try:
        metrics_df = pd.read_csv(COMPARISON_CSV)
    except Exception as exc:
        fail(f"Cannot read comparison CSV: {exc}")
        return 1

    if len(metrics_df) != 2:
        fail("Comparison CSV should contain exactly 2 rows")
        return 1
    ok("Comparison CSV contains pre/post rows")

    required_columns = [
        "label",
        "processed_rows",
        "market_data_success_rate_percent",
        "stage1_pass_rate_percent",
        "stage1_rejection_rate_percent",
    ]
    missing = [column for column in required_columns if column not in metrics_df.columns]
    if missing:
        fail("Comparison CSV missing columns:")
        for column in missing:
            print(f"   - {column}")
        return 1
    ok("Comparison CSV required columns present")

    metrics = report.get("metrics", {})
    print()
    print("Summary")
    print("-" * 82)
    print(f"Market-data success rate delta: {metrics.get('market_data_success_rate_delta_points')} points")
    print(f"Stage 1 pass rate delta: {metrics.get('stage1_pass_rate_delta_points')} points")
    print(f"Stage 1 rejection rate delta: {metrics.get('stage1_rejection_rate_delta_points')} points")
    print(f"Noise removed: {report.get('noise_removed', {}).get('excluded_rows')} rows")

    print()
    print("Result")
    print("-" * 82)
    ok("Phase 7A.4 institutional cleaning comparison is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
