
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.enrich_market_data_yfinance import enrich_market_data_yfinance
from src.run_real_universe_pilot import run_real_universe_pilot

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real_clean.csv"
DEFAULT_ENRICHED_OUTPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real_clean_market_enriched_500.csv"

SUMMARY_PATH = SCOUTING_OUTPUTS_DIR / "clean_500_stability_summary.json"
METRICS_CSV = SCOUTING_OUTPUTS_DIR / "clean_500_stability_metrics.csv"
REJECTION_DISTRIBUTION_CSV = SCOUTING_OUTPUTS_DIR / "clean_500_stage1_rejection_distribution.csv"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "clean_500_stability_report.md"

STAGE1_REJECTION_LOG = PROJECT_ROOT / "data" / "stages" / "stage1_rejection_log.csv"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _reason_distribution() -> list[dict[str, Any]]:
    if not STAGE1_REJECTION_LOG.exists():
        return []
    try:
        df = pd.read_csv(STAGE1_REJECTION_LOG)
    except Exception:
        return []
    if df.empty or "reason_code" not in df.columns:
        return []
    counts = df["reason_code"].value_counts(dropna=False).reset_index()
    counts.columns = ["reason_code", "count"]
    counts["count"] = counts["count"].astype(int)
    return counts.to_dict(orient="records")


def _render_markdown(summary: dict[str, Any]) -> str:
    rows = summary.get("stage1_rejection_distribution", [])
    lines = [
        "# Scout Finance — Phase 7A.6 Clean 500 Stability Report",
        "",
        f"Generated at: `{summary.get('created_at')}`",
        "",
        "## Core metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Limit | {summary.get('limit')} |",
        f"| Market-data processed rows | {summary.get('market_data_processed_rows')} |",
        f"| Market-data success | {summary.get('market_data_success')} |",
        f"| Market-data success rate | {summary.get('market_data_success_rate_percent')}% |",
        f"| Market-data failed/incomplete | {summary.get('market_data_failed_or_incomplete')} |",
        f"| Stage 1 input | {summary.get('stage1_input')} |",
        f"| Stage 1 passed | {summary.get('stage1_passed')} |",
        f"| Stage 1 watchlist | {summary.get('stage1_watchlist')} |",
        f"| Stage 1 rejected | {summary.get('stage1_rejected')} |",
        f"| Stage 1 pass rate | {summary.get('stage1_pass_rate_percent')}% |",
        f"| Stage 1 watchlist rate | {summary.get('stage1_watchlist_rate_percent')}% |",
        f"| Stage 1 rejection rate | {summary.get('stage1_rejection_rate_percent')}% |",
        "",
        "## Stage 1 rejection distribution",
        "",
        "| Reason code | Count |",
        "|---|---:|",
    ]
    if rows:
        for row in rows:
            lines.append(f"| {row.get('reason_code')} | {row.get('count')} |")
    else:
        lines.append("| No rejection reasons found | 0 |")
    lines.extend([
        "",
        "## Controls",
        "",
        f"- OpenAI called: `{summary.get('openai_called')}`",
        f"- Paid API called: `{summary.get('paid_api_called')}`",
        f"- yfinance called: `{summary.get('yfinance_called')}`",
        f"- app.py modified: `{summary.get('app_modified')}`",
        f"- release v0.6 modified: `{summary.get('release_v0_6_modified')}`",
        "",
        "## Interpretation",
        "",
        "This phase is a scale/stability test. It does not yet evaluate fundamentals.",
        "Companies that pass Stage 1 are investable-universe candidates, not final investment recommendations.",
        "",
    ])
    return "\n".join(lines)


def run_clean_500_stability_pilot(
    input_path: Path = DEFAULT_INPUT,
    enriched_output_path: Path = DEFAULT_ENRICHED_OUTPUT,
    limit: int = 500,
    sleep_seconds: float = 0.3,
    source: str = "yfinance_clean_market_data_500",
) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Clean universe input not found: {input_path}. "
            "Run first: python -m src.clean_universe_institutional"
        )

    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    started_at = _utc_now_iso()
    start = time.perf_counter()

    market_summary = enrich_market_data_yfinance(
        input_path=input_path,
        output_path=enriched_output_path,
        limit=limit,
        sleep_seconds=sleep_seconds,
        cache_max_age_days=2,
        include_cached=True,
    )

    pilot_summary = run_real_universe_pilot(
        input_path=enriched_output_path,
        limit=limit,
        source=source,
    )

    counts = pilot_summary.get("counts", {})
    rejection_distribution = _reason_distribution()

    market_processed = int(market_summary.get("processed_rows", 0) or 0)
    market_success = int(market_summary.get("success_with_core_market_data", 0) or 0)
    market_failed = int(market_summary.get("failed_or_incomplete_rows", 0) or 0)

    stage1_input = int(counts.get("stage0_input_companies") or 0)
    stage1_passed = int(counts.get("stage1_passed") or 0)
    stage1_watchlist = int(counts.get("stage1_watchlist") or 0)
    stage1_rejected = int(counts.get("stage1_rejected") or 0)

    summary = {
        "phase": "7A.6",
        "status": "OK" if pilot_summary.get("status") == "OK" and market_summary.get("status") == "OK" else "FAILED",
        "created_at": _utc_now_iso(),
        "started_at": started_at,
        "elapsed_seconds": round(time.perf_counter() - start, 3),
        "input_path": str(input_path),
        "enriched_output_path": str(enriched_output_path),
        "limit": limit,
        "sleep_seconds": sleep_seconds,
        "source": source,
        "market_data_processed_rows": market_processed,
        "market_data_success": market_success,
        "market_data_failed_or_incomplete": market_failed,
        "market_data_success_rate_percent": _rate(market_success, market_processed),
        "stage1_input": stage1_input,
        "stage1_passed": stage1_passed,
        "stage1_watchlist": stage1_watchlist,
        "stage1_rejected": stage1_rejected,
        "stage1_pass_rate_percent": _rate(stage1_passed, stage1_input),
        "stage1_watchlist_rate_percent": _rate(stage1_watchlist, stage1_input),
        "stage1_rejection_rate_percent": _rate(stage1_rejected, stage1_input),
        "companies_ready_for_stage2": counts.get("companies_ready_for_stage2"),
        "companies_not_ready_for_stage2": counts.get("companies_not_ready_for_stage2"),
        "average_core_stage2_coverage_percent": counts.get("average_core_stage2_coverage_percent"),
        "stage1_rejection_distribution": rejection_distribution,
        "output_files": {
            "summary": str(SUMMARY_PATH),
            "metrics_csv": str(METRICS_CSV),
            "rejection_distribution_csv": str(REJECTION_DISTRIBUTION_CSV),
            "report_md": str(REPORT_MD),
            "enriched_output": str(enriched_output_path),
        },
        "openai_called": False,
        "paid_api_called": False,
        "yfinance_called": True,
        "app_modified": False,
        "release_v0_6_modified": False,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    pd.DataFrame([
        {"metric": "market_data_success_rate_percent", "value": summary["market_data_success_rate_percent"]},
        {"metric": "stage1_pass_rate_percent", "value": summary["stage1_pass_rate_percent"]},
        {"metric": "stage1_watchlist_rate_percent", "value": summary["stage1_watchlist_rate_percent"]},
        {"metric": "stage1_rejection_rate_percent", "value": summary["stage1_rejection_rate_percent"]},
        {"metric": "market_data_success", "value": summary["market_data_success"]},
        {"metric": "stage1_passed", "value": summary["stage1_passed"]},
        {"metric": "stage1_watchlist", "value": summary["stage1_watchlist"]},
        {"metric": "stage1_rejected", "value": summary["stage1_rejected"]},
    ]).to_csv(METRICS_CSV, index=False, encoding="utf-8-sig")

    pd.DataFrame(rejection_distribution).to_csv(REJECTION_DISTRIBUTION_CSV, index=False, encoding="utf-8-sig")
    REPORT_MD.write_text(_render_markdown(summary), encoding="utf-8")
    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7A.6 clean 500 stability pilot")
    print("=" * 78)
    print(f"Status: {summary.get('status')}")
    print(f"Limit: {summary.get('limit')}")
    print(f"Elapsed seconds: {summary.get('elapsed_seconds')}")
    print()
    print("Market data")
    print("-" * 78)
    print(f"Processed: {summary.get('market_data_processed_rows')}")
    print(f"Success: {summary.get('market_data_success')}")
    print(f"Failed/incomplete: {summary.get('market_data_failed_or_incomplete')}")
    print(f"Success rate: {summary.get('market_data_success_rate_percent')}%")
    print()
    print("Stage 1")
    print("-" * 78)
    print(f"Input: {summary.get('stage1_input')}")
    print(f"Passed: {summary.get('stage1_passed')} ({summary.get('stage1_pass_rate_percent')}%)")
    print(f"Watchlist: {summary.get('stage1_watchlist')} ({summary.get('stage1_watchlist_rate_percent')}%)")
    print(f"Rejected: {summary.get('stage1_rejected')} ({summary.get('stage1_rejection_rate_percent')}%)")
    print()
    print("Output files")
    print("-" * 78)
    for label, path in summary.get("output_files", {}).items():
        print(f"- {label}: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_ENRICHED_OUTPUT))
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--sleep", type=float, default=0.3)
    parser.add_argument("--source", default="yfinance_clean_market_data_500")
    args = parser.parse_args()

    summary = run_clean_500_stability_pilot(
        input_path=Path(args.input),
        enriched_output_path=Path(args.output),
        limit=args.limit,
        sleep_seconds=args.sleep,
        source=args.source,
    )

    print_summary(summary)
    return 0 if summary.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
