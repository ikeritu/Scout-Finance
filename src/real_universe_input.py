from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = ["ticker", "name", "exchange", "country", "sector", "industry"]
TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,15}$")

ROOT = Path(__file__).resolve().parents[1]
DATA_REAL = ROOT / "data" / "real"
OUT = ROOT / "outputs" / "scouting"
TEMPLATE = DATA_REAL / "universe_template.csv"
DEFAULT_INPUT = DATA_REAL / "real_universe.csv"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def init_template() -> Path:
    DATA_REAL.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE.exists():
        TEMPLATE.write_text(
            "ticker,name,exchange,country,sector,industry\n"
            "AAPL,Apple Inc.,NASDAQ,US,Technology,Consumer Electronics\n"
            "MSFT,Microsoft Corporation,NASDAQ,US,Technology,Software\n"
            "ASML,ASML Holding N.V.,NASDAQ,NL,Technology,Semiconductor Equipment\n",
            encoding="utf-8",
        )
    return TEMPLATE


def normalize_ticker(value: str) -> str:
    return str(value or "").strip().upper()


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
        columns = list(reader.fieldnames or [])
    return rows, columns


def validate_universe(path: Path = DEFAULT_INPUT) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    DATA_REAL.mkdir(parents=True, exist_ok=True)

    issues: list[dict[str, Any]] = []
    rows: list[dict[str, str]] = []
    columns: list[str] = []

    if not path.exists():
        summary = {
            "phase": "v1.4B",
            "title": "Real Universe Input MVP",
            "status": "MISSING_INPUT",
            "input_path": str(path.relative_to(ROOT)),
            "created_at": now_utc(),
            "rows_total": 0,
            "valid_tickers": 0,
            "duplicate_tickers": 0,
            "empty_tickers": 0,
            "invalid_tickers": 0,
            "missing_columns": REQUIRED_COLUMNS,
            "top_tickers": "",
            "issues": [{"level": "ERROR", "message": "Input file does not exist."}],
            "openai_called": False,
            "api_called": False,
            "yfinance_called": False,
            "pipeline_recalculated": False,
        }
        write_outputs(summary)
        return summary

    try:
        rows, columns = read_csv_rows(path)
    except Exception as exc:
        summary = {
            "phase": "v1.4B",
            "title": "Real Universe Input MVP",
            "status": "READ_ERROR",
            "input_path": str(path.relative_to(ROOT)),
            "created_at": now_utc(),
            "rows_total": 0,
            "valid_tickers": 0,
            "duplicate_tickers": 0,
            "empty_tickers": 0,
            "invalid_tickers": 0,
            "missing_columns": REQUIRED_COLUMNS,
            "top_tickers": "",
            "issues": [{"level": "ERROR", "message": f"Could not read CSV: {exc}"}],
            "openai_called": False,
            "api_called": False,
            "yfinance_called": False,
            "pipeline_recalculated": False,
        }
        write_outputs(summary)
        return summary

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in columns]
    if missing_columns:
        issues.append({"level": "ERROR", "message": f"Missing required columns: {missing_columns}"})

    seen: set[str] = set()
    duplicates: set[str] = set()
    empty_tickers = 0
    invalid_tickers = 0
    valid_tickers: list[str] = []

    for idx, row in enumerate(rows, start=2):
        ticker = normalize_ticker(row.get("ticker", ""))

        if not ticker:
            empty_tickers += 1
            issues.append({"level": "ERROR", "row": idx, "message": "Empty ticker."})
            continue

        if not TICKER_RE.match(ticker):
            invalid_tickers += 1
            issues.append({"level": "ERROR", "row": idx, "ticker": ticker, "message": "Invalid ticker format."})
            continue

        if ticker in seen:
            duplicates.add(ticker)
            issues.append({"level": "WARNING", "row": idx, "ticker": ticker, "message": "Duplicate ticker."})
        else:
            seen.add(ticker)
            valid_tickers.append(ticker)

        if "exchange" in columns and not str(row.get("exchange", "")).strip():
            issues.append({"level": "WARNING", "row": idx, "ticker": ticker, "message": "Empty exchange."})

        if "country" in columns and not str(row.get("country", "")).strip():
            issues.append({"level": "WARNING", "row": idx, "ticker": ticker, "message": "Empty country."})

    status = "OK"
    if missing_columns or empty_tickers or invalid_tickers:
        status = "ERROR"
    elif duplicates:
        status = "WARNING"

    summary = {
        "phase": "v1.4B",
        "title": "Real Universe Input MVP",
        "status": status,
        "input_path": str(path.relative_to(ROOT)),
        "created_at": now_utc(),
        "rows_total": len(rows),
        "columns": columns,
        "required_columns": REQUIRED_COLUMNS,
        "missing_columns": missing_columns,
        "valid_tickers": len(valid_tickers),
        "duplicate_tickers": len(duplicates),
        "duplicate_ticker_values": sorted(duplicates),
        "empty_tickers": empty_tickers,
        "invalid_tickers": invalid_tickers,
        "top_tickers": ", ".join(valid_tickers[:10]),
        "issues": issues,
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "pipeline_recalculated": False,
    }
    write_outputs(summary)
    return summary


def write_outputs(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary_path = OUT / "real_universe_input_summary.json"
    report_path = OUT / "real_universe_input_report.md"
    write_json(summary_path, summary)

    lines = [
        "# Scout Finance — v1.4B Real Universe Input Report",
        "",
        f"Status: **{summary.get('status')}**",
        "",
        "## Summary",
        "",
        f"- Input: `{summary.get('input_path')}`",
        f"- Rows total: {summary.get('rows_total')}",
        f"- Valid tickers: {summary.get('valid_tickers')}",
        f"- Duplicate tickers: {summary.get('duplicate_tickers')}",
        f"- Empty tickers: {summary.get('empty_tickers')}",
        f"- Invalid tickers: {summary.get('invalid_tickers')}",
        f"- Top tickers: {summary.get('top_tickers')}",
        "",
        "## Controls",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "",
        "## Issues",
        "",
    ]

    issues = summary.get("issues") or []
    if not issues:
        lines.append("- No issues detected.")
    else:
        for issue in issues[:200]:
            lines.append(f"- `{issue.get('level')}` row `{issue.get('row', '-')}` ticker `{issue.get('ticker', '-')}`: {issue.get('message')}")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scout Finance v1.4B real universe input validator.")
    parser.add_argument("--init-template", action="store_true", help="Create data/real/universe_template.csv")
    parser.add_argument("--validate", action="store_true", help="Validate data/real/real_universe.csv")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="CSV file to validate")
    args = parser.parse_args()

    if args.init_template:
        path = init_template()
        print(f"Template ready: {path}")

    if args.validate:
        summary = validate_universe(Path(args.input))
        print("Scout Finance — v1.4B Real Universe Input")
        print("=" * 92)
        print(f"Status: {summary['status']}")
        print(f"Rows total: {summary['rows_total']}")
        print(f"Valid tickers: {summary['valid_tickers']}")
        print(f"Duplicate tickers: {summary['duplicate_tickers']}")
        print(f"Empty tickers: {summary['empty_tickers']}")
        print(f"Invalid tickers: {summary['invalid_tickers']}")
        print("OpenAI called: False")
        print("API called: False")
        print("yfinance called: False")
        print("Pipeline recalculated: False")
        print("Report: outputs/scouting/real_universe_input_report.md")

    if not args.init_template and not args.validate:
        parser.print_help()


if __name__ == "__main__":
    main()
