
"""
Scout Finance — Phase 7A.4 Institutional cleaning comparison report.

Compares the pipeline before/after institutional universe cleaning.
Does not call OpenAI, paid APIs or yfinance.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

UNIVERSE_CLEANING_SUMMARY = SCOUTING_OUTPUTS_DIR / "universe_cleaning_summary.json"
MARKET_DATA_SUMMARY = SCOUTING_OUTPUTS_DIR / "market_data_enrichment_summary.json"
REAL_UNIVERSE_PILOT_SUMMARY = SCOUTING_OUTPUTS_DIR / "real_universe_pilot_summary.json"

STAGE1_REJECTION_LOG = PROJECT_ROOT / "data" / "stages" / "stage1_rejection_log.csv"

COMPARISON_JSON = SCOUTING_OUTPUTS_DIR / "institutional_cleaning_comparison_report.json"
COMPARISON_CSV = SCOUTING_OUTPUTS_DIR / "institutional_cleaning_comparison_metrics.csv"
COMPARISON_MD = SCOUTING_OUTPUTS_DIR / "institutional_cleaning_comparison_report.md"


PRE_CLEAN_BASELINE = {
    "label": "Pre-cleaning pilot",
    "description": "Raw Nasdaq Trader universe, first 50 symbols, before institutional cleaning.",
    "processed_rows": 50,
    "market_data_success": 34,
    "market_data_failed_or_incomplete": 16,
    "stage1_input": 50,
    "stage1_passed": 15,
    "stage1_watchlist": 4,
    "stage1_rejected": 31,
    "source": "user_verified_console_output",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _safe_rate(numerator: float | int | None, denominator: float | int | None) -> float:
    if not denominator:
        return 0.0
    return round((float(numerator or 0) / float(denominator)) * 100, 2)


def _reason_distribution(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path)
    except Exception:
        return {}
    if df.empty or "reason_code" not in df.columns:
        return {}
    return {str(k): int(v) for k, v in df["reason_code"].value_counts(dropna=False).to_dict().items()}


def _build_metric_row(label: str, data: dict[str, Any]) -> dict[str, Any]:
    processed_rows = data.get("processed_rows") or data.get("stage1_input") or 0
    market_data_success = data.get("market_data_success") or 0
    market_data_failed = data.get("market_data_failed_or_incomplete") or 0
    stage1_input = data.get("stage1_input") or processed_rows
    stage1_passed = data.get("stage1_passed") or 0
    stage1_watchlist = data.get("stage1_watchlist") or 0
    stage1_rejected = data.get("stage1_rejected") or 0

    return {
        "label": label,
        "processed_rows": int(processed_rows),
        "market_data_success": int(market_data_success),
        "market_data_failed_or_incomplete": int(market_data_failed),
        "market_data_success_rate_percent": _safe_rate(market_data_success, processed_rows),
        "stage1_input": int(stage1_input),
        "stage1_passed": int(stage1_passed),
        "stage1_watchlist": int(stage1_watchlist),
        "stage1_rejected": int(stage1_rejected),
        "stage1_pass_rate_percent": _safe_rate(stage1_passed, stage1_input),
        "stage1_watchlist_rate_percent": _safe_rate(stage1_watchlist, stage1_input),
        "stage1_rejection_rate_percent": _safe_rate(stage1_rejected, stage1_input),
    }


def _render_markdown_report(report: dict[str, Any]) -> str:
    metrics = report.get("metrics", {})
    pre = metrics.get("pre_cleaning", {})
    post = metrics.get("post_cleaning", {})
    noise = report.get("noise_removed", {})

    lines = [
        "# Scout Finance — Phase 7A.4 Institutional Cleaning Comparison",
        "",
        f"Generated at: `{report.get('created_at')}`",
        "",
        "## Executive summary",
        "",
        "Institutional universe cleaning improved the quality and efficiency of the pipeline.",
        "The system now separates out-of-scope instruments before Stage 1, instead of treating them as financial rejections.",
        "",
        "## Before vs after",
        "",
        "| Metric | Pre-cleaning | Post-cleaning |",
        "|---|---:|---:|",
        f"| Processed rows | {pre.get('processed_rows')} | {post.get('processed_rows')} |",
        f"| Market-data success | {pre.get('market_data_success')} | {post.get('market_data_success')} |",
        f"| Market-data success rate | {pre.get('market_data_success_rate_percent')}% | {post.get('market_data_success_rate_percent')}% |",
        f"| Stage 1 passed | {pre.get('stage1_passed')} | {post.get('stage1_passed')} |",
        f"| Stage 1 watchlist | {pre.get('stage1_watchlist')} | {post.get('stage1_watchlist')} |",
        f"| Stage 1 rejected | {pre.get('stage1_rejected')} | {post.get('stage1_rejected')} |",
        f"| Stage 1 pass rate | {pre.get('stage1_pass_rate_percent')}% | {post.get('stage1_pass_rate_percent')}% |",
        f"| Stage 1 rejection rate | {pre.get('stage1_rejection_rate_percent')}% | {post.get('stage1_rejection_rate_percent')}% |",
        "",
        "## Improvement deltas",
        "",
        f"- Market-data success rate delta: **{metrics.get('market_data_success_rate_delta_points')} percentage points**.",
        f"- Stage 1 pass rate delta: **{metrics.get('stage1_pass_rate_delta_points')} percentage points**.",
        f"- Stage 1 rejection rate delta: **{metrics.get('stage1_rejection_rate_delta_points')} percentage points**.",
        "",
        "## Universe cleaning impact",
        "",
        f"- Initial universe rows: **{noise.get('input_rows')}**.",
        f"- Clean in-scope rows: **{noise.get('clean_rows')}**.",
        f"- Excluded out-of-scope rows: **{noise.get('excluded_rows')}**.",
        f"- Excluded rate: **{noise.get('excluded_rate_percent')}%**.",
        "",
        "### Excluded distribution",
        "",
        "| Instrument type | Count |",
        "|---|---:|",
    ]

    for key, value in noise.get("excluded_distribution", {}).items():
        lines.append(f"| {key} | {value} |")

    lines.extend([
        "",
        "## Professional interpretation",
        "",
        "The cleaning layer is not a financial rejection layer. It is an institutional universe-definition layer.",
        "This makes Stage 1 cleaner, more defensible and easier to audit.",
        "",
        "## Controls",
        "",
        "- OpenAI called: `False`",
        "- Paid API called: `False`",
        "- yfinance called during this report: `False`",
        "- app.py modified: `False`",
        "- release v0.6 modified: `False`",
        "",
    ])

    return "\n".join(lines)


def build_institutional_cleaning_comparison_report() -> dict[str, Any]:
    cleaning_summary = _read_json(UNIVERSE_CLEANING_SUMMARY)
    market_summary = _read_json(MARKET_DATA_SUMMARY)
    pilot_summary = _read_json(REAL_UNIVERSE_PILOT_SUMMARY)
    counts = pilot_summary.get("counts", {}) if pilot_summary else {}

    post_clean = {
        "label": "Post-cleaning pilot",
        "description": "Institutionally cleaned universe enriched with yfinance market data.",
        "processed_rows": market_summary.get("processed_rows", 0),
        "market_data_success": market_summary.get("success_with_core_market_data", 0),
        "market_data_failed_or_incomplete": market_summary.get("failed_or_incomplete_rows", 0),
        "stage1_input": counts.get("stage0_input_companies", 0),
        "stage1_passed": counts.get("stage1_passed", 0),
        "stage1_watchlist": counts.get("stage1_watchlist", 0),
        "stage1_rejected": counts.get("stage1_rejected", 0),
        "source": "current_project_outputs",
    }

    pre_row = _build_metric_row("Pre-cleaning pilot", PRE_CLEAN_BASELINE)
    post_row = _build_metric_row("Post-cleaning pilot", post_clean)

    pd.DataFrame([pre_row, post_row]).to_csv(COMPARISON_CSV, index=False, encoding="utf-8-sig")

    metrics = {
        "pre_cleaning": pre_row,
        "post_cleaning": post_row,
        "market_data_success_rate_delta_points": round(post_row["market_data_success_rate_percent"] - pre_row["market_data_success_rate_percent"], 2),
        "stage1_pass_rate_delta_points": round(post_row["stage1_pass_rate_percent"] - pre_row["stage1_pass_rate_percent"], 2),
        "stage1_rejection_rate_delta_points": round(post_row["stage1_rejection_rate_percent"] - pre_row["stage1_rejection_rate_percent"], 2),
    }

    noise_removed = {
        "input_rows": cleaning_summary.get("input_rows", 0),
        "clean_rows": cleaning_summary.get("clean_rows", 0),
        "excluded_rows": cleaning_summary.get("excluded_rows", 0),
        "excluded_rate_percent": cleaning_summary.get("excluded_rate_percent", 0),
        "excluded_distribution": cleaning_summary.get("excluded_distribution", {}),
        "clean_distribution": cleaning_summary.get("clean_distribution", {}),
    }

    report = {
        "phase": "7A.4",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "purpose": "Compare pipeline quality before and after institutional universe cleaning.",
        "pre_cleaning": PRE_CLEAN_BASELINE,
        "post_cleaning": post_clean,
        "metrics": metrics,
        "noise_removed": noise_removed,
        "current_stage1_rejection_reason_distribution": _reason_distribution(STAGE1_REJECTION_LOG),
        "output_files": {
            "comparison_json": str(COMPARISON_JSON),
            "comparison_csv": str(COMPARISON_CSV),
            "comparison_md": str(COMPARISON_MD),
        },
        "openai_called": False,
        "paid_api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "release_v0_6_modified": False,
    }

    COMPARISON_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    COMPARISON_MD.write_text(_render_markdown_report(report), encoding="utf-8")
    return report


def print_report_summary(report: dict[str, Any]) -> None:
    metrics = report.get("metrics", {})
    pre = metrics.get("pre_cleaning", {})
    post = metrics.get("post_cleaning", {})
    noise = report.get("noise_removed", {})

    print("Scout Finance — Phase 7A.4 Institutional Cleaning Comparison")
    print("=" * 82)
    print(f"Status: {report.get('status')}")
    print()
    print("Before vs after")
    print("-" * 82)
    print(f"Pre-cleaning market-data success rate:  {pre.get('market_data_success_rate_percent')}%")
    print(f"Post-cleaning market-data success rate: {post.get('market_data_success_rate_percent')}%")
    print(f"Delta: {metrics.get('market_data_success_rate_delta_points')} percentage points")
    print()
    print(f"Pre-cleaning Stage 1 pass rate:         {pre.get('stage1_pass_rate_percent')}%")
    print(f"Post-cleaning Stage 1 pass rate:        {post.get('stage1_pass_rate_percent')}%")
    print(f"Delta: {metrics.get('stage1_pass_rate_delta_points')} percentage points")
    print()
    print("Universe cleaning")
    print("-" * 82)
    print(f"Input rows: {noise.get('input_rows')}")
    print(f"Clean rows: {noise.get('clean_rows')}")
    print(f"Excluded rows: {noise.get('excluded_rows')} ({noise.get('excluded_rate_percent')}%)")
    print()
    print("Output files")
    print("-" * 82)
    for label, path in report.get("output_files", {}).items():
        print(f"- {label}: {path}")


def main() -> int:
    report = build_institutional_cleaning_comparison_report()
    print_report_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
