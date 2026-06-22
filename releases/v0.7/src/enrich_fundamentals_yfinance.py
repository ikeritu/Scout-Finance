
from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STAGE1_PASSED = ROOT / "data" / "stages" / "stage1_passed.csv"
ENRICHED_PATH = ROOT / "data" / "stages" / "stage1_passed_enriched.csv"
RAW_FUNDAMENTALS = ROOT / "data" / "raw" / "fundamentals_source_yfinance.csv"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "fundamentals_yfinance_enrichment_summary.json"
FAILURES_PATH = OUT_DIR / "fundamentals_yfinance_failures.csv"
COVERAGE_PATH = OUT_DIR / "fundamentals_yfinance_enrichment_coverage.csv"
REPORT_PATH = OUT_DIR / "fundamentals_yfinance_enrichment_report.md"

CORE_STAGE2_COLUMNS = [
    "revenue_ttm", "operating_margin", "fcf_margin", "net_debt_to_ebitda",
    "shares_dilution_3y", "data_completeness_score", "financial_data_date", "special_case",
]

OPTIONAL_COLUMNS = [
    "revenue_growth_1y", "gross_margin", "net_margin", "ebitda", "free_cash_flow",
    "total_debt", "cash", "net_debt", "debt_to_equity", "current_ratio",
    "interest_coverage", "pe_ratio", "forward_pe", "ev_ebitda", "price_sales", "fcf_yield",
]

EXPECTED_STAGE1_BALANCED_ROWS = 182


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_ticker(ticker: Any) -> str:
    return str(ticker or "").strip().upper()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        v = float(value)
        if not math.isfinite(v):
            return None
        return v
    except Exception:
        return None


def div(a: Any, b: Any) -> float | None:
    a = safe_float(a)
    b = safe_float(b)
    if a is None or b in (None, 0):
        return None
    return a / b


def get_from_info(info: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = info.get(key)
        if value not in (None, "", "None"):
            return value
    return None


def score_completeness(row: dict[str, Any]) -> float:
    required = ["revenue_ttm", "operating_margin", "fcf_margin", "net_debt_to_ebitda", "financial_data_date", "special_case"]
    present = sum(1 for col in required if row.get(col) not in (None, "", "None"))
    if row.get("shares_dilution_3y") not in (None, "", "None"):
        present += 0.5
    return round(100 * present / 6.5, 2)


def infer_special_case(row: dict[str, Any]) -> str:
    special = []
    ticker = str(row.get("ticker") or "")
    quote_type = str(row.get("quote_type") or "").upper()
    asset_type = str(row.get("asset_type") or "").upper()
    sector = str(row.get("sector_yf") or row.get("sector") or "").lower()
    industry = str(row.get("industry_yf") or row.get("industry") or "").lower()

    if "REIT" in asset_type or "reit" in sector or "reit" in industry:
        special.append("REIT")
    if quote_type and quote_type not in {"EQUITY", "ADR"}:
        special.append(f"QUOTE_TYPE_{quote_type}")
    if ticker.endswith("Y") and row.get("country_yf") not in ("United States", "USA", "US", None):
        special.append("POSSIBLE_ADR")
    return "|".join(special) if special else "none"


def fetch_one_yfinance(ticker: str, pause_seconds: float = 0.05) -> tuple[dict[str, Any], dict[str, Any] | None]:
    try:
        import yfinance as yf
    except Exception as exc:
        raise RuntimeError("yfinance is not installed. Run: .\\.venv\\Scripts\\python.exe -m pip install yfinance") from exc

    try:
        yt = yf.Ticker(ticker)
        info = getattr(yt, "info", {}) or {}

        revenue = safe_float(get_from_info(info, ["totalRevenue", "revenue"]))
        operating_margin = safe_float(get_from_info(info, ["operatingMargins", "operatingMargin"]))
        gross_margin = safe_float(get_from_info(info, ["grossMargins", "grossMargin"]))
        net_margin = safe_float(get_from_info(info, ["profitMargins", "netMargins"]))
        ebitda = safe_float(get_from_info(info, ["ebitda"]))
        free_cash_flow = safe_float(get_from_info(info, ["freeCashflow", "freeCashFlow"]))
        total_debt = safe_float(get_from_info(info, ["totalDebt"]))
        cash = safe_float(get_from_info(info, ["totalCash", "cash"]))
        market_cap = safe_float(get_from_info(info, ["marketCap"]))

        net_debt = (total_debt or 0) - (cash or 0) if (total_debt is not None or cash is not None) else None

        row = {
            "ticker": ticker,
            "yf_success": True,
            "yf_error": "",
            "financial_data_date": utc_now()[:10],
            "quote_type": get_from_info(info, ["quoteType"]),
            "sector_yf": get_from_info(info, ["sector"]),
            "industry_yf": get_from_info(info, ["industry"]),
            "country_yf": get_from_info(info, ["country"]),
            "revenue_ttm": revenue,
            "operating_margin": operating_margin,
            "fcf_margin": div(free_cash_flow, revenue),
            "net_debt_to_ebitda": div(net_debt, ebitda),
            "shares_dilution_3y": None,
            "revenue_growth_1y": safe_float(get_from_info(info, ["revenueGrowth"])),
            "gross_margin": gross_margin,
            "net_margin": net_margin,
            "ebitda": ebitda,
            "free_cash_flow": free_cash_flow,
            "total_debt": total_debt,
            "cash": cash,
            "net_debt": net_debt,
            "debt_to_equity": safe_float(get_from_info(info, ["debtToEquity"])),
            "current_ratio": safe_float(get_from_info(info, ["currentRatio"])),
            "interest_coverage": None,
            "pe_ratio": safe_float(get_from_info(info, ["trailingPE"])),
            "forward_pe": safe_float(get_from_info(info, ["forwardPE"])),
            "ev_ebitda": safe_float(get_from_info(info, ["enterpriseToEbitda"])),
            "price_sales": safe_float(get_from_info(info, ["priceToSalesTrailing12Months"])),
            "fcf_yield": div(free_cash_flow, market_cap),
            "shares_outstanding": safe_float(get_from_info(info, ["sharesOutstanding"])),
            "float_shares": safe_float(get_from_info(info, ["floatShares"])),
            "market_cap_yf": market_cap,
        }
        row["special_case"] = infer_special_case(row)
        row["data_completeness_score"] = score_completeness(row)

        time.sleep(pause_seconds)
        return row, None

    except Exception as exc:
        failure = {"ticker": ticker, "error": str(exc), "created_at": utc_now()}
        row = {
            "ticker": ticker, "yf_success": False, "yf_error": str(exc), "financial_data_date": None,
            "revenue_ttm": None, "operating_margin": None, "fcf_margin": None,
            "net_debt_to_ebitda": None, "shares_dilution_3y": None,
            "data_completeness_score": 0.0, "special_case": "fetch_failed",
        }
        return row, failure


def coverage_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(df)
    for col in CORE_STAGE2_COLUMNS + OPTIONAL_COLUMNS:
        present = int(df[col].notna().sum()) if col in df.columns else 0
        rows.append({
            "column": col,
            "coverage_percent": round(100 * present / total, 2) if total else 0.0,
            "present_count": present,
            "missing_count": total - present,
        })
    return pd.DataFrame(rows)


def render_report(summary: dict) -> str:
    return f"""# Scout Finance — Phase 7C.1 yfinance fundamentals enrichment

Generated at: `{summary["created_at"]}`

## Status

- Status: **{summary["status"]}**
- Input companies: **{summary["input_companies"]}**
- yfinance successful rows: **{summary["yf_success_rows"]}**
- yfinance failed rows: **{summary["yf_failed_rows"]}**
- Companies ready for Stage 2: **{summary["companies_ready_for_stage2"]}**
- Companies not ready for Stage 2: **{summary["companies_not_ready_for_stage2"]}**
- Average core Stage 2 coverage: **{summary["average_core_stage2_coverage_percent"]}%**

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- app.py modified: `{summary["app_modified"]}`
- release modified: `{summary["release_modified"]}`
"""


def main() -> int:
    print("Scout Finance — Phase 7C.1 yfinance fundamentals enrichment")
    print("=" * 74)

    if not STAGE1_PASSED.exists():
        print(f"FAIL Missing Stage 1 passed file: {STAGE1_PASSED}")
        return 1

    df = pd.read_csv(STAGE1_PASSED)
    if "ticker" not in df.columns:
        print("FAIL stage1_passed.csv has no ticker column")
        return 1

    tickers = [clean_ticker(t) for t in df["ticker"].tolist()]
    tickers = [t for t in tickers if t]
    print(f"Input companies: {len(tickers)}")

    if len(tickers) != EXPECTED_STAGE1_BALANCED_ROWS:
        print(f"WARN Expected {EXPECTED_STAGE1_BALANCED_ROWS} Stage 1 Balanced rows, got {len(tickers)}")

    fundamentals, failures = [], []

    for idx, ticker in enumerate(tickers, start=1):
        print(f"[{idx}/{len(tickers)}] {ticker}")
        row, failure = fetch_one_yfinance(ticker)
        fundamentals.append(row)
        if failure:
            failures.append(failure)

    fund_df = pd.DataFrame(fundamentals)
    failure_df = pd.DataFrame(failures, columns=["ticker", "error", "created_at"])

    RAW_FUNDAMENTALS.parent.mkdir(parents=True, exist_ok=True)
    ENRICHED_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fund_df.to_csv(RAW_FUNDAMENTALS, index=False, encoding="utf-8-sig")
    failure_df.to_csv(FAILURES_PATH, index=False, encoding="utf-8-sig")

    enriched = df.merge(fund_df, on="ticker", how="left", suffixes=("", "_fund"))
    enriched.to_csv(ENRICHED_PATH, index=False, encoding="utf-8-sig")

    cov = coverage_table(enriched)
    cov.to_csv(COVERAGE_PATH, index=False, encoding="utf-8-sig")

    hard_required = ["revenue_ttm", "operating_margin", "fcf_margin", "net_debt_to_ebitda", "data_completeness_score", "financial_data_date", "special_case"]
    ready_mask = pd.Series(True, index=enriched.index)
    for col in hard_required:
        ready_mask = ready_mask & enriched[col].notna()

    ready = int(ready_mask.sum())
    not_ready = int(len(enriched) - ready)

    core_coverage = cov[cov["column"].isin(CORE_STAGE2_COLUMNS)]
    avg_coverage = round(float(core_coverage["coverage_percent"].mean()), 2) if not core_coverage.empty else 0.0

    summary = {
        "phase": "7C.1",
        "status": "OK",
        "created_at": utc_now(),
        "input_file": str(STAGE1_PASSED),
        "input_companies": int(len(df)),
        "unique_tickers": int(len(tickers)),
        "yf_success_rows": int(fund_df["yf_success"].sum()) if "yf_success" in fund_df.columns else 0,
        "yf_failed_rows": int((fund_df["yf_success"] == False).sum()) if "yf_success" in fund_df.columns else 0,
        "companies_ready_for_stage2": ready,
        "companies_not_ready_for_stage2": not_ready,
        "average_core_stage2_coverage_percent": avg_coverage,
        "core_stage2_columns": CORE_STAGE2_COLUMNS,
        "hard_required_for_stage2_after_yfinance": hard_required,
        "output_files": {
            "raw_fundamentals": str(RAW_FUNDAMENTALS),
            "stage1_passed_enriched": str(ENRICHED_PATH),
            "summary_json": str(SUMMARY_PATH),
            "failures_csv": str(FAILURES_PATH),
            "coverage_csv": str(COVERAGE_PATH),
            "report_md": str(REPORT_PATH),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": True,
        "app_modified": False,
        "release_modified": False,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Summary")
    print("-" * 74)
    print(f"yfinance successful rows: {summary['yf_success_rows']}")
    print(f"yfinance failed rows: {summary['yf_failed_rows']}")
    print(f"Companies ready for Stage 2: {ready}")
    print(f"Companies not ready for Stage 2: {not_ready}")
    print(f"Average core Stage 2 coverage: {avg_coverage}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
