
"""
Scout Finance — Phase 6B fundamental data coverage report.

Purpose:
- Analyze data/stages/stage1_passed.csv
- Measure which fundamental columns required for Stage 2 are present/missing
- Produce reports before connecting APIs or enriching real data

This module does not call external APIs.
It does not call OpenAI.
It does not modify app.py.

Run from project root:

    ./.venv/Scripts/python.exe -m src.fundamental_coverage_report
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.funnel_paths import SCOUTING_OUTPUTS_DIR, STAGES_DIR, ensure_funnel_directories


STAGE1_PASSED_PATH = STAGES_DIR / "stage1_passed.csv"

COVERAGE_JSON_PATH = SCOUTING_OUTPUTS_DIR / "fundamental_coverage_report.json"
COVERAGE_CSV_PATH = SCOUTING_OUTPUTS_DIR / "fundamental_coverage_report.csv"
MISSING_BY_COMPANY_PATH = SCOUTING_OUTPUTS_DIR / "fundamental_missing_by_company.csv"


CORE_STAGE2_COLUMNS = [
    "revenue_ttm",
    "operating_margin",
    "fcf_margin",
    "net_debt_to_ebitda",
    "shares_dilution_3y",
    "data_completeness_score",
    "financial_data_date",
    "special_case",
]


RECOMMENDED_STAGE2_COLUMNS = [
    "revenue_growth_1y",
    "revenue_growth_3y",
    "gross_margin",
    "net_margin",
    "ebitda",
    "free_cash_flow",
    "total_debt",
    "cash",
    "net_debt",
    "debt_to_equity",
    "current_ratio",
    "interest_coverage",
]


STAGE3_EXTRA_COLUMNS = [
    "pe_ratio",
    "forward_pe",
    "ev_ebitda",
    "price_sales",
    "fcf_yield",
    "price_change_6m",
    "price_change_12m",
    "relative_strength_6m",
    "drawdown_from_52w_high",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _column_coverage(df: pd.DataFrame, column: str, category: str) -> dict[str, Any]:
    total_rows = int(len(df))

    if column not in df.columns:
        present_count = 0
        missing_count = total_rows
        exists = False
    else:
        exists = True
        present_count = int(df[column].notna().sum())
        missing_count = int(df[column].isna().sum())

    coverage_rate = present_count / total_rows if total_rows else 0.0

    return {
        "category": category,
        "column": column,
        "exists": exists,
        "present_count": present_count,
        "missing_count": missing_count,
        "coverage_rate": round(coverage_rate, 4),
        "coverage_percent": round(coverage_rate * 100, 2),
    }


def _missing_columns_for_company(row: pd.Series, columns: list[str]) -> list[str]:
    missing: list[str] = []

    for column in columns:
        if column not in row.index:
            missing.append(column)
            continue

        value = row.get(column)

        if pd.isna(value):
            missing.append(column)

    return missing


def build_fundamental_coverage_report(
    input_path: Path = STAGE1_PASSED_PATH,
    coverage_json_path: Path = COVERAGE_JSON_PATH,
    coverage_csv_path: Path = COVERAGE_CSV_PATH,
    missing_by_company_path: Path = MISSING_BY_COMPANY_PATH,
) -> dict[str, Any]:
    """
    Build fundamental data coverage report.
    """

    ensure_funnel_directories()

    if not input_path.exists():
        raise FileNotFoundError(
            f"Stage 1 passed file not found: {input_path}. "
            "Run Stage 1 first: python -m src.run_stage1_filter"
        )

    df = pd.read_csv(input_path)

    coverage_rows = []

    for column in CORE_STAGE2_COLUMNS:
        coverage_rows.append(_column_coverage(df, column, "core_stage2"))

    for column in RECOMMENDED_STAGE2_COLUMNS:
        coverage_rows.append(_column_coverage(df, column, "recommended_stage2"))

    for column in STAGE3_EXTRA_COLUMNS:
        coverage_rows.append(_column_coverage(df, column, "stage3_extra"))

    coverage_df = pd.DataFrame(coverage_rows)
    coverage_df.to_csv(coverage_csv_path, index=False, encoding="utf-8-sig")

    missing_company_rows = []

    for _, row in df.iterrows():
        ticker = str(row.get("ticker", "")).upper().strip()
        name = row.get("name", "")

        missing_core = _missing_columns_for_company(row, CORE_STAGE2_COLUMNS)
        missing_recommended = _missing_columns_for_company(row, RECOMMENDED_STAGE2_COLUMNS)
        missing_stage3 = _missing_columns_for_company(row, STAGE3_EXTRA_COLUMNS)

        core_present = len(CORE_STAGE2_COLUMNS) - len(missing_core)
        core_coverage_rate = core_present / len(CORE_STAGE2_COLUMNS) if CORE_STAGE2_COLUMNS else 0

        missing_company_rows.append(
            {
                "ticker": ticker,
                "name": name,
                "core_stage2_present": core_present,
                "core_stage2_total": len(CORE_STAGE2_COLUMNS),
                "core_stage2_coverage_percent": round(core_coverage_rate * 100, 2),
                "can_run_stage2_cleanly": len(missing_core) == 0,
                "missing_core_stage2": "|".join(missing_core),
                "missing_recommended_stage2": "|".join(missing_recommended),
                "missing_stage3_extra": "|".join(missing_stage3),
            }
        )

    missing_company_df = pd.DataFrame(missing_company_rows)
    missing_company_df.to_csv(missing_by_company_path, index=False, encoding="utf-8-sig")

    core_coverage = coverage_df[coverage_df["category"] == "core_stage2"].copy()

    if not core_coverage.empty:
        average_core_coverage = float(core_coverage["coverage_percent"].mean())
        fully_covered_core_columns = int((core_coverage["coverage_percent"] == 100).sum())
    else:
        average_core_coverage = 0.0
        fully_covered_core_columns = 0

    companies_ready_for_stage2 = (
        int(missing_company_df["can_run_stage2_cleanly"].sum()) if not missing_company_df.empty else 0
    )

    top_missing_core = (
        core_coverage.sort_values("coverage_percent", ascending=True)
        .head(10)[["column", "coverage_percent", "missing_count"]]
        .to_dict(orient="records")
    )

    report = {
        "phase": "6B",
        "created_at": _utc_now_iso(),
        "input_file": str(input_path),
        "input_companies": int(len(df)),
        "core_stage2_columns": CORE_STAGE2_COLUMNS,
        "recommended_stage2_columns": RECOMMENDED_STAGE2_COLUMNS,
        "stage3_extra_columns": STAGE3_EXTRA_COLUMNS,
        "average_core_stage2_coverage_percent": round(average_core_coverage, 2),
        "fully_covered_core_stage2_columns": fully_covered_core_columns,
        "total_core_stage2_columns": len(CORE_STAGE2_COLUMNS),
        "companies_ready_for_stage2": companies_ready_for_stage2,
        "companies_not_ready_for_stage2": int(len(df) - companies_ready_for_stage2),
        "top_missing_core_stage2_columns": top_missing_core,
        "output_files": {
            "coverage_json": str(coverage_json_path),
            "coverage_csv": str(coverage_csv_path),
            "missing_by_company": str(missing_by_company_path),
        },
        "openai_called": False,
        "api_called": False,
        "app_modified": False,
    }

    coverage_json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return report


def print_fundamental_coverage_report(report: dict[str, Any]) -> None:
    print("Scout Finance — Phase 6B fundamental coverage report")
    print("=" * 64)
    print(f"Input companies: {report.get('input_companies')}")
    print(f"Average core Stage 2 coverage: {report.get('average_core_stage2_coverage_percent')}%")
    print(
        "Core Stage 2 columns fully covered: "
        f"{report.get('fully_covered_core_stage2_columns')} / {report.get('total_core_stage2_columns')}"
    )
    print(f"Companies ready for Stage 2: {report.get('companies_ready_for_stage2')}")
    print(f"Companies not ready for Stage 2: {report.get('companies_not_ready_for_stage2')}")
    print()
    print("Top missing core Stage 2 columns")
    print("-" * 64)

    for item in report.get("top_missing_core_stage2_columns", []):
        print(
            f"- {item.get('column')}: "
            f"coverage={item.get('coverage_percent')}% | "
            f"missing={item.get('missing_count')}"
        )

    print()
    print("Output files")
    print("-" * 64)

    for label, path in report.get("output_files", {}).items():
        print(f"- {label}: {path}")

    print()
    print("No OpenAI call. No external API call. app.py not modified.")


def main() -> int:
    report = build_fundamental_coverage_report()
    print_fundamental_coverage_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
