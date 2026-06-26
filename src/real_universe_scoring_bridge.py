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
OUT_SCORED = OUT / "real_universe_scored_candidates.csv"
OUT_ACTIVE = OUT / "active_real_universe_top_candidates.csv"
OUT_SUMMARY = OUT / "real_universe_scoring_bridge_summary.json"
OUT_REPORT = OUT / "real_universe_scoring_bridge_report.md"

CONTROLS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "market_data_called": False,
    "pipeline_recalculated": False,
    "financial_scoring_recalculated": False,
}

MAJOR_EXCHANGES = {"NASDAQ", "NYSE", "LSE", "XETRA", "EPA", "TSE", "AMS", "BME", "SWX", "HKEX"}
DEVELOPED_MARKETS = {"US", "CA", "GB", "UK", "NL", "DE", "FR", "ES", "IT", "CH", "SE", "DK", "NO", "FI", "JP", "AU", "IE"}
HIGH_SIGNAL_SECTORS = {
    "Technology",
    "Healthcare",
    "Industrials",
    "Financial Services",
    "Consumer Defensive",
    "Communication Services",
    "Semiconductors",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def norm(value: Any) -> str:
    return str(value or "").strip()


def norm_upper(value: Any) -> str:
    return norm(value).upper()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def score_row(row: dict[str, str], order: int) -> dict[str, Any]:
    ticker = norm_upper(row.get("ticker"))
    name = norm(row.get("name")) or ticker
    exchange = norm_upper(row.get("exchange"))
    country = norm_upper(row.get("country"))
    sector = norm(row.get("sector"))
    industry = norm(row.get("industry"))

    completeness_fields = {
        "ticker": ticker,
        "name": name,
        "exchange": exchange,
        "country": country,
        "sector": sector,
        "industry": industry,
    }
    completeness_score = round(
        100.0 * sum(1 for value in completeness_fields.values() if norm(value)) / len(completeness_fields),
        2,
    )

    exchange_score = 100.0 if exchange in MAJOR_EXCHANGES else (60.0 if exchange else 20.0)
    country_score = 100.0 if country in DEVELOPED_MARKETS else (60.0 if country else 20.0)
    sector_score = 85.0 if sector in HIGH_SIGNAL_SECTORS else (65.0 if sector else 20.0)
    industry_score = 80.0 if industry else 20.0
    order_score = max(40.0, 100.0 - (order - 1) * 2.0)

    metadata_score = round(
        0.35 * completeness_score
        + 0.20 * exchange_score
        + 0.20 * country_score
        + 0.15 * sector_score
        + 0.05 * industry_score
        + 0.05 * order_score,
        2,
    )

    data_quality_label = "high" if completeness_score >= 95 else "medium" if completeness_score >= 70 else "low"
    metadata_category = "metadata_high" if metadata_score >= 85 else "metadata_medium" if metadata_score >= 65 else "metadata_low"

    return {
        "ticker": ticker,
        "name": name,
        "company_name": name,
        "exchange": exchange,
        "country": country,
        "sector": sector,
        "industry": industry,
        "market_cap": "",
        "final_stage3_score": metadata_score,
        "stage3_category": metadata_category,
        "stage3_status": "METADATA_SCORE",
        "risk_score": "",
        "data_quality_score": completeness_score,
        "data_quality_label": f"METADATA_SCORE · {data_quality_label}",
        "business_quality_score": "",
        "financial_health_score": "",
        "growth_score": "",
        "valuation_score": "",
        "moat_proxy_score": "",
        "momentum_score": "",
        "liquidity_score": "",
        "metadata_completeness_score": completeness_score,
        "metadata_exchange_score": exchange_score,
        "metadata_country_score": country_score,
        "metadata_sector_score": sector_score,
        "metadata_industry_score": industry_score,
        "metadata_order_score": order_score,
        "source": "data/real/real_universe.csv",
        "score_method": "metadata_score_local_no_market_data",
        "note": "Metadata-only score from local CSV fields. No price, market cap, fundamentals, OpenAI, APIs or yfinance.",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def score_universe() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    if not INPUT.exists():
        summary = {
            "phase": "v1.4D",
            "title": "Real Universe Scoring Bridge",
            "status": "MISSING_INPUT",
            "input_path": str(INPUT.relative_to(ROOT)),
            "created_at": now_utc(),
            "rows_input": 0,
            "candidates_scored": 0,
            "top_tickers": "",
            "score_method": "metadata_score_local_no_market_data",
            **CONTROLS,
        }
        write_outputs(summary, [])
        return summary

    raw_rows = read_rows(INPUT)
    seen: set[str] = set()
    scored: list[dict[str, Any]] = []

    for row in raw_rows:
        ticker = norm_upper(row.get("ticker"))
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        scored.append(score_row(row, len(scored) + 1))

    scored = sorted(scored, key=lambda item: item["final_stage3_score"], reverse=True)

    summary = {
        "phase": "v1.4D",
        "title": "Real Universe Scoring Bridge",
        "status": "OK" if scored else "EMPTY",
        "input_path": str(INPUT.relative_to(ROOT)),
        "created_at": now_utc(),
        "rows_input": len(raw_rows),
        "candidates_scored": len(scored),
        "top_tickers": ", ".join([row["ticker"] for row in scored[:10]]),
        "score_method": "metadata_score_local_no_market_data",
        "score_warning": "Metadata-only score. Not financial scoring, not investment advice.",
        "outputs": [
            str(OUT_SCORED.relative_to(ROOT)),
            str(OUT_ACTIVE.relative_to(ROOT)),
            str(OUT_SUMMARY.relative_to(ROOT)),
            str(OUT_REPORT.relative_to(ROOT)),
        ],
        **CONTROLS,
    }

    write_outputs(summary, scored)
    return summary


def write_outputs(summary: dict[str, Any], scored: list[dict[str, Any]]) -> None:
    write_csv(OUT_SCORED, scored)
    write_csv(OUT_ACTIVE, scored)
    write_json(OUT_SUMMARY, summary)

    lines = [
        "# Scout Finance — v1.4D Real Universe Scoring Bridge Report",
        "",
        f"Status: **{summary.get('status')}**",
        "",
        "## Summary",
        "",
        f"- Input rows: {summary.get('rows_input')}",
        f"- Candidates scored: {summary.get('candidates_scored')}",
        f"- Top tickers: {summary.get('top_tickers')}",
        f"- Score method: `{summary.get('score_method')}`",
        "",
        "## Important warning",
        "",
        "This is **metadata-only scoring**. It does not use price, market cap, fundamentals, OpenAI, APIs or yfinance.",
        "",
        "## Controls",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Market data called: False",
        "- Pipeline recalculated: False",
        "- Financial scoring recalculated: False",
        "",
        "## Score components",
        "",
        "- Metadata completeness",
        "- Exchange presence / known major exchange",
        "- Country presence / developed market proxy",
        "- Sector presence / high-signal sector proxy",
        "- Industry presence",
        "- Stable order tie-breaker",
        "",
        "## Candidates",
        "",
    ]

    for row in scored[:100]:
        lines.append(
            f"- `{row['ticker']}` — {row['company_name']} — score `{row['final_stage3_score']}` — `{row['stage3_status']}`"
        )

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create metadata-only scores from data/real/real_universe.csv.")
    parser.add_argument("--score", action="store_true", help="Generate metadata-only scored candidates.")
    args = parser.parse_args()

    if not args.score:
        parser.print_help()
        return

    summary = score_universe()

    print("Scout Finance — v1.4D Real Universe Scoring Bridge")
    print("=" * 92)
    print(f"Status: {summary['status']}")
    print(f"Input rows: {summary['rows_input']}")
    print(f"Candidates scored: {summary['candidates_scored']}")
    print(f"Top tickers: {summary['top_tickers']}")
    print(f"Score method: {summary['score_method']}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Market data called: False")
    print("Pipeline recalculated: False")
    print("Financial scoring recalculated: False")
    print("Report: outputs/scouting/real_universe_scoring_bridge_report.md")


if __name__ == "__main__":
    main()
