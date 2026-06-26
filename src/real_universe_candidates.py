from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_REAL = ROOT / "data" / "real"
OUT = ROOT / "outputs" / "scouting"
INPUT = DATA_REAL / "real_universe.csv"

OUT_CANDIDATES = OUT / "real_universe_candidates.csv"
OUT_ACTIVE = OUT / "active_real_universe_top_candidates.csv"
OUT_SUMMARY = OUT / "real_universe_candidates_summary.json"
OUT_REPORT = OUT / "real_universe_candidates_report.md"

CONTROLS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "scoring_recalculated": False,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_input_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def norm(value: Any) -> str:
    return str(value or "").strip()


def norm_ticker(value: Any) -> str:
    return norm(value).upper()


def generate_candidates() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    if not INPUT.exists():
        summary = {
            "phase": "v1.4C",
            "title": "Regenerate Candidates From Real Universe",
            "status": "MISSING_INPUT",
            "input_path": str(INPUT.relative_to(ROOT)),
            "created_at": now_utc(),
            "rows_input": 0,
            "candidates_generated": 0,
            "top_tickers": "",
            "scoring_is_placeholder_order_only": True,
            **CONTROLS,
        }
        write_outputs(summary, [])
        return summary

    rows = read_input_rows(INPUT)
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []

    for idx, row in enumerate(rows, start=1):
        ticker = norm_ticker(row.get("ticker"))
        if not ticker or ticker in seen:
            continue

        seen.add(ticker)
        order_score = max(1.0, 100.0 - (idx - 1))

        candidates.append(
            {
                "ticker": ticker,
                "name": norm(row.get("name")) or ticker,
                "company_name": norm(row.get("name")) or ticker,
                "exchange": norm(row.get("exchange")),
                "country": norm(row.get("country")),
                "sector": norm(row.get("sector")),
                "industry": norm(row.get("industry")),
                "market_cap": "",
                "final_stage3_score": round(order_score, 2),
                "stage3_category": "real_universe_input_candidate",
                "stage3_status": "INPUT_ONLY",
                "risk_score": "",
                "data_quality_score": 100.0,
                "business_quality_score": "",
                "financial_health_score": "",
                "growth_score": "",
                "valuation_score": "",
                "moat_proxy_score": "",
                "momentum_score": "",
                "liquidity_score": "",
                "source": "data/real/real_universe.csv",
                "note": "Input-only candidate generated from real_universe.csv. Not financial scoring.",
            }
        )

    summary = {
        "phase": "v1.4C",
        "title": "Regenerate Candidates From Real Universe",
        "status": "OK" if candidates else "EMPTY",
        "input_path": str(INPUT.relative_to(ROOT)),
        "created_at": now_utc(),
        "rows_input": len(rows),
        "candidates_generated": len(candidates),
        "top_tickers": ", ".join([c["ticker"] for c in candidates[:10]]),
        "outputs": [
            str(OUT_CANDIDATES.relative_to(ROOT)),
            str(OUT_ACTIVE.relative_to(ROOT)),
            str(OUT_SUMMARY.relative_to(ROOT)),
            str(OUT_REPORT.relative_to(ROOT)),
        ],
        "scoring_is_placeholder_order_only": True,
        "warning": "This phase does not perform financial scoring. It creates UI-test candidates from the real universe input.",
        **CONTROLS,
    }

    write_outputs(summary, candidates)
    return summary


def write_candidates_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(summary: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    write_candidates_csv(OUT_CANDIDATES, candidates)
    write_candidates_csv(OUT_ACTIVE, candidates)
    write_json(OUT_SUMMARY, summary)

    lines = [
        "# Scout Finance — v1.4C Real Universe Candidates Report",
        "",
        f"Status: **{summary.get('status')}**",
        "",
        "## Summary",
        "",
        f"- Input rows: {summary.get('rows_input')}",
        f"- Candidates generated: {summary.get('candidates_generated')}",
        f"- Top tickers: {summary.get('top_tickers')}",
        "",
        "## Important warning",
        "",
        "This is **not financial scoring**. It is an input-only candidate generation step used to test the UI with real tickers.",
        "",
        "## Controls",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "- Scoring recalculated: False",
        "",
        "## Outputs",
        "",
    ]

    for output in summary.get("outputs", []):
        lines.append(f"- `{output}`")

    lines.extend(["", "## Candidates", ""])

    for candidate in candidates[:100]:
        lines.append(f"- `{candidate['ticker']}` — {candidate['name']} — `{candidate['stage3_status']}`")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate UI-test candidates from data/real/real_universe.csv.")
    parser.add_argument("--generate", action="store_true", help="Generate real-universe input candidates.")
    args = parser.parse_args()

    if not args.generate:
        parser.print_help()
        return

    summary = generate_candidates()

    print("Scout Finance — v1.4C Regenerate Candidates From Real Universe")
    print("=" * 92)
    print(f"Status: {summary['status']}")
    print(f"Input rows: {summary['rows_input']}")
    print(f"Candidates generated: {summary['candidates_generated']}")
    print(f"Top tickers: {summary['top_tickers']}")
    print("Scoring is placeholder/order-only: True")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print("Report: outputs/scouting/real_universe_candidates_report.md")


if __name__ == "__main__":
    main()
