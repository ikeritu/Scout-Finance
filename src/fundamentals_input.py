from __future__ import annotations
import argparse, csv, json, math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "real"
OUT = ROOT / "outputs" / "fundamentals"

TEMPLATE = DATA / "manual_fundamentals_template.csv"
FUNDAMENTALS = DATA / "manual_fundamentals.csv"
UNIVERSE = DATA / "real_universe.csv"

SUMMARY = OUT / "fundamentals_input_summary.json"
REPORT = OUT / "fundamentals_input_report.md"
VALID_ROWS = OUT / "manual_fundamentals_valid_rows.csv"
ISSUES = OUT / "manual_fundamentals_issues.csv"

REQUIRED_COLUMNS = [
    "ticker", "period", "period_end", "revenue", "revenue_growth_yoy",
    "gross_margin", "operating_margin", "net_margin", "free_cash_flow",
    "total_cash", "total_debt", "shares_diluted", "currency", "source_note"
]
NUMERIC_COLUMNS = [
    "revenue", "revenue_growth_yoy", "gross_margin", "operating_margin",
    "net_margin", "free_cash_flow", "total_cash", "total_debt", "shares_diluted"
]


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def norm(v: Any) -> str:
    return str(v or "").strip()


def ticker(v: Any) -> str:
    return norm(v).upper().replace("$", "")


def fl(v: Any) -> float | None:
    try:
        txt = norm(v)
        if not txt:
            return None
        n = float(txt)
        return None if math.isnan(n) else n
    except Exception:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def init_template() -> Path:
    DATA.mkdir(parents=True, exist_ok=True)
    TEMPLATE.write_text(
        "ticker,period,period_end,revenue,revenue_growth_yoy,gross_margin,operating_margin,net_margin,free_cash_flow,total_cash,total_debt,shares_diluted,currency,source_note\n"
        "AAPL,TTM,2026-06-29,385000000000,2.1,45.0,30.0,26.0,105000000000,62000000000,98000000000,15500000000,USD,manual test data\n"
        "MSFT,TTM,2026-06-29,245000000000,12.0,69.0,44.0,36.0,74000000000,80000000000,47000000000,7430000000,USD,manual test data\n"
        "ASML,TTM,2026-06-29,27500000000,8.5,51.0,31.0,27.0,8500000000,7500000000,4500000000,394000000,EUR,manual test data\n",
        encoding="utf-8"
    )
    return TEMPLATE


def validate_rows() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = read_csv(FUNDAMENTALS)
    universe = read_csv(UNIVERSE)
    universe_tickers = {ticker(r.get("ticker")) for r in universe if ticker(r.get("ticker"))}

    issues: list[dict[str, Any]] = []
    valid: list[dict[str, Any]] = []

    if not FUNDAMENTALS.exists():
        issues.append({"level": "ERROR", "row": "", "ticker": "", "field": "file", "message": "manual_fundamentals.csv does not exist"})
    if not rows:
        issues.append({"level": "ERROR", "row": "", "ticker": "", "field": "file", "message": "manual_fundamentals.csv is empty or unreadable"})

    if rows:
        cols = set(rows[0].keys())
        for col in REQUIRED_COLUMNS:
            if col not in cols:
                issues.append({"level": "ERROR", "row": "", "ticker": "", "field": col, "message": f"Missing required column: {col}"})

    if any(i["level"] == "ERROR" and i["field"] != "ticker" for i in issues):
        summary = build_summary(rows, valid, issues, universe_tickers)
        persist(summary, valid, issues)
        return summary

    seen: set[str] = set()

    for idx, row in enumerate(rows, start=2):
        t = ticker(row.get("ticker"))
        row_issues: list[dict[str, Any]] = []

        if not t:
            row_issues.append({"level": "ERROR", "row": idx, "ticker": "", "field": "ticker", "message": "Empty ticker"})
        elif t in seen:
            row_issues.append({"level": "ERROR", "row": idx, "ticker": t, "field": "ticker", "message": "Duplicate ticker"})
        seen.add(t)

        if universe_tickers and t and t not in universe_tickers:
            row_issues.append({"level": "WARNING", "row": idx, "ticker": t, "field": "ticker", "message": "Ticker not present in real_universe.csv"})

        if norm(row.get("period")).upper() not in {"TTM", "FY", "MRQ", "ANNUAL", "QUARTER"}:
            row_issues.append({"level": "WARNING", "row": idx, "ticker": t, "field": "period", "message": "Unexpected period value"})

        for col in NUMERIC_COLUMNS:
            value = fl(row.get(col))
            if value is None:
                row_issues.append({"level": "ERROR", "row": idx, "ticker": t, "field": col, "message": f"Non numeric or empty value: {col}"})
            elif col in {"revenue", "shares_diluted"} and value <= 0:
                row_issues.append({"level": "ERROR", "row": idx, "ticker": t, "field": col, "message": f"{col} must be positive"})
            elif col in {"gross_margin", "operating_margin", "net_margin"} and not (-100 <= value <= 100):
                row_issues.append({"level": "WARNING", "row": idx, "ticker": t, "field": col, "message": f"Suspicious margin percentage: {value}"})

        issues.extend(row_issues)

        if not any(i["level"] == "ERROR" for i in row_issues):
            out = dict(row)
            out["ticker"] = t
            out["fundamentals_status"] = "FUNDAMENTALS_INPUT_VALID"
            out["fundamentals_source"] = "manual_fundamentals.csv"
            out["fundamentals_method"] = "manual_fundamentals_input_v0"
            valid.append(out)

    summary = build_summary(rows, valid, issues, universe_tickers)
    persist(summary, valid, issues)
    return summary


def build_summary(rows: list[dict[str, Any]], valid: list[dict[str, Any]], issues: list[dict[str, Any]], universe_tickers: set[str]) -> dict[str, Any]:
    errors = [i for i in issues if i.get("level") == "ERROR"]
    warnings = [i for i in issues if i.get("level") == "WARNING"]
    valid_tickers = {ticker(r.get("ticker")) for r in valid if ticker(r.get("ticker"))}
    coverage = round(len(valid_tickers & universe_tickers) / len(universe_tickers), 4) if universe_tickers else 0.0
    return {
        "phase": "v1.6A",
        "title": "Fundamentals Input Bridge",
        "status": "OK" if rows and not errors else "ERROR",
        "created_at": now(),
        "rows_total": len(rows),
        "valid_rows": len(valid),
        "valid_tickers": len(valid_tickers),
        "universe_tickers": len(universe_tickers),
        "coverage_ratio": coverage,
        "errors": len(errors),
        "warnings": len(warnings),
        "top_tickers": ", ".join(sorted(valid_tickers)[:10]),
        "openai_called": False,
        "broker_called": False,
        "pipeline_recalculated": False,
        "yfinance_called": False,
        "fundamentals_api_called": False,
    }


def persist(summary: dict[str, Any], valid: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
    write_json(SUMMARY, summary)
    valid_fields = (REQUIRED_COLUMNS + ["fundamentals_status", "fundamentals_source", "fundamentals_method"])
    write_csv(VALID_ROWS, valid, fields=valid_fields)
    write_csv(ISSUES, issues, fields=["level", "row", "ticker", "field", "message"])

    REPORT.write_text(
        "# Scout Finance — v1.6A Fundamentals Input Bridge Report\n\n"
        f"Status: **{summary['status']}**\n\n"
        "## Summary\n\n"
        f"- Rows total: {summary['rows_total']}\n"
        f"- Valid rows: {summary['valid_rows']}\n"
        f"- Valid tickers: {summary['valid_tickers']}\n"
        f"- Universe tickers: {summary['universe_tickers']}\n"
        f"- Coverage ratio: {summary['coverage_ratio']}\n"
        f"- Errors: {summary['errors']}\n"
        f"- Warnings: {summary['warnings']}\n\n"
        "## Controls\n\n"
        "- OpenAI called: False\n"
        "- Broker called: False\n"
        "- Pipeline recalculated: False\n"
        "- yfinance called: False\n"
        "- Fundamentals API called: False\n",
        encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate manual fundamentals input CSV.")
    parser.add_argument("--init-template", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.init_template:
        path = init_template()
        print("Scout Finance — v1.6A Fundamentals Input Bridge")
        print("=" * 92)
        print(f"Template ready: {path}")

    if args.validate:
        summary = validate_rows()
        print("Scout Finance — v1.6A Fundamentals Input Bridge")
        print("=" * 92)
        print(f"Status: {summary['status']}")
        print(f"Rows total: {summary['rows_total']}")
        print(f"Valid rows: {summary['valid_rows']}")
        print(f"Valid tickers: {summary['valid_tickers']}")
        print(f"Universe tickers: {summary['universe_tickers']}")
        print(f"Coverage ratio: {summary['coverage_ratio']}")
        print(f"Errors: {summary['errors']}")
        print(f"Warnings: {summary['warnings']}")
        print("OpenAI called: False")
        print("Broker called: False")
        print("Pipeline recalculated: False")
        print("yfinance called: False")
        print("Fundamentals API called: False")
        print("Report: outputs/fundamentals/fundamentals_input_report.md")

    if not args.init_template and not args.validate:
        parser.print_help()


if __name__ == "__main__":
    main()
