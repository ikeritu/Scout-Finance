
"""
Scout Finance — Phase 7B.1 Stage 1 policy simulator.

Purpose:
- Simulate alternative Stage 1 threshold policies without modifying real filters.
- Compare base/current, conservative, balanced and aggressive policies.
- Use current 500-company enriched universe output.
- Produce JSON, CSV and Markdown reports.

This module:
- does not call OpenAI;
- does not call APIs;
- does not call yfinance;
- does not modify app.py;
- does not modify releases/v0.6;
- does not modify src/filter_stage1.py.

Run:
    ./.venv/Scripts/python.exe -m src.simulate_stage1_policy
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real_clean_market_enriched_500.csv"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_report.md"
SCENARIO_SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_summary.csv"
SCENARIO_DECISIONS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_decisions.csv"
SCENARIO_BUCKETS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_bucket_summary.csv"


POLICIES = {
    "current_base": {
        "label": "Actual/base",
        "description": "Approximation of current Stage 1 thresholds.",
        "min_market_cap": 100_000_000,
        "watch_market_cap": 300_000_000,
        "min_price": 1.0,
        "watch_price": 5.0,
        "min_dollar_volume": 500_000,
        "watch_dollar_volume": 2_000_000,
    },
    "conservative": {
        "label": "Conservador",
        "description": "Higher quality/liquidity bar; fewer but cleaner candidates.",
        "min_market_cap": 300_000_000,
        "watch_market_cap": 1_000_000_000,
        "min_price": 2.0,
        "watch_price": 8.0,
        "min_dollar_volume": 2_000_000,
        "watch_dollar_volume": 10_000_000,
    },
    "balanced": {
        "label": "Equilibrado",
        "description": "Professional middle ground; keeps small-cap optionality while improving quality.",
        "min_market_cap": 150_000_000,
        "watch_market_cap": 500_000_000,
        "min_price": 1.5,
        "watch_price": 5.0,
        "min_dollar_volume": 1_000_000,
        "watch_dollar_volume": 5_000_000,
    },
    "aggressive": {
        "label": "Agresivo",
        "description": "More permissive; captures earlier/smaller opportunities with more noise.",
        "min_market_cap": 50_000_000,
        "watch_market_cap": 150_000_000,
        "min_price": 0.75,
        "watch_price": 2.0,
        "min_dollar_volume": 250_000,
        "watch_dollar_volume": 1_000_000,
    },
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_input(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    rename_map = {
        "Symbol": "ticker",
        "Name": "name",
        "Market Cap": "market_cap",
        "Last Sale": "price",
        "Volume": "avg_volume_90d",
    }

    for old, new in rename_map.items():
        if old in out.columns and new not in out.columns:
            out[new] = out[old]

    required = ["ticker", "name", "market_cap", "price", "avg_volume_90d"]

    for col in required:
        if col not in out.columns:
            out[col] = None

    out["market_cap"] = pd.to_numeric(out["market_cap"], errors="coerce")
    out["price"] = pd.to_numeric(out["price"], errors="coerce")
    out["avg_volume_90d"] = pd.to_numeric(out["avg_volume_90d"], errors="coerce")

    if "dollar_volume_90d" not in out.columns:
        out["dollar_volume_90d"] = out["price"] * out["avg_volume_90d"]
    else:
        out["dollar_volume_90d"] = pd.to_numeric(out["dollar_volume_90d"], errors="coerce")
        missing = out["dollar_volume_90d"].isna()
        out.loc[missing, "dollar_volume_90d"] = out.loc[missing, "price"] * out.loc[missing, "avg_volume_90d"]

    return out


def _evaluate_row(row: pd.Series, policy: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []

    market_cap = row.get("market_cap")
    price = row.get("price")
    dollar_volume = row.get("dollar_volume_90d")

    hard_fail = False
    watch = False

    if pd.isna(market_cap):
        hard_fail = True
        reasons.append("MISSING_MARKET_CAP")
    elif market_cap < policy["min_market_cap"]:
        hard_fail = True
        reasons.append("MARKET_CAP_BELOW_MINIMUM")
    elif market_cap < policy["watch_market_cap"]:
        watch = True
        reasons.append("MARKET_CAP_WATCHLIST_RANGE")

    if pd.isna(price):
        hard_fail = True
        reasons.append("MISSING_PRICE")
    elif price < policy["min_price"]:
        hard_fail = True
        reasons.append("PRICE_BELOW_MINIMUM")
    elif price < policy["watch_price"]:
        watch = True
        reasons.append("PRICE_WATCHLIST_RANGE")

    if pd.isna(dollar_volume):
        hard_fail = True
        reasons.append("MISSING_DOLLAR_VOLUME")
    elif dollar_volume < policy["min_dollar_volume"]:
        hard_fail = True
        reasons.append("LOW_DOLLAR_VOLUME")
    elif dollar_volume < policy["watch_dollar_volume"]:
        watch = True
        reasons.append("DOLLAR_VOLUME_WATCHLIST_RANGE")

    if hard_fail:
        return "REJECTED", reasons

    if watch:
        return "WATCHLIST", reasons

    return "PASSED", reasons


def _describe_group(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "count": 0,
            "median_market_cap": None,
            "median_price": None,
            "median_dollar_volume_90d": None,
        }

    return {
        "count": int(len(df)),
        "median_market_cap": _safe_median(df, "market_cap"),
        "median_price": _safe_median(df, "price"),
        "median_dollar_volume_90d": _safe_median(df, "dollar_volume_90d"),
    }


def _safe_median(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None

    s = pd.to_numeric(df[column], errors="coerce").dropna()

    if s.empty:
        return None

    return round(float(s.median()), 4)


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0

    return round((numerator / denominator) * 100, 2)


def _simulate_policy(df: pd.DataFrame, policy_key: str, policy: dict[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    rows = []

    for _, row in df.iterrows():
        decision, reasons = _evaluate_row(row, policy)

        rows.append(
            {
                "scenario": policy_key,
                "scenario_label": policy["label"],
                "ticker": row.get("ticker"),
                "name": row.get("name"),
                "market_cap": row.get("market_cap"),
                "price": row.get("price"),
                "avg_volume_90d": row.get("avg_volume_90d"),
                "dollar_volume_90d": row.get("dollar_volume_90d"),
                "simulated_decision": decision,
                "simulated_reasons": ", ".join(reasons),
            }
        )

    decisions = pd.DataFrame(rows)

    total = len(decisions)
    passed = int((decisions["simulated_decision"] == "PASSED").sum())
    watchlist = int((decisions["simulated_decision"] == "WATCHLIST").sum())
    rejected = int((decisions["simulated_decision"] == "REJECTED").sum())

    summary = {
        "scenario": policy_key,
        "scenario_label": policy["label"],
        "description": policy["description"],
        "total": total,
        "passed": passed,
        "watchlist": watchlist,
        "rejected": rejected,
        "pass_rate_percent": _rate(passed, total),
        "watchlist_rate_percent": _rate(watchlist, total),
        "rejection_rate_percent": _rate(rejected, total),
        "thresholds": policy,
        "passed_profile": _describe_group(decisions[decisions["simulated_decision"] == "PASSED"]),
        "watchlist_profile": _describe_group(decisions[decisions["simulated_decision"] == "WATCHLIST"]),
        "rejected_profile": _describe_group(decisions[decisions["simulated_decision"] == "REJECTED"]),
    }

    return summary, decisions


def _reason_distribution(decisions: pd.DataFrame) -> pd.DataFrame:
    if decisions.empty:
        return pd.DataFrame(columns=["scenario", "reason_code", "count"])

    rows = []

    for _, row in decisions.iterrows():
        scenario = row.get("scenario")
        reasons = str(row.get("simulated_reasons") or "").split(",")

        for reason in reasons:
            clean = reason.strip()

            if clean:
                rows.append({"scenario": scenario, "reason_code": clean})

    if not rows:
        return pd.DataFrame(columns=["scenario", "reason_code", "count"])

    df = pd.DataFrame(rows)
    return df.groupby(["scenario", "reason_code"]).size().reset_index(name="count").sort_values(["scenario", "count"], ascending=[True, False])


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Scout Finance — Phase 7B.1 Stage 1 Policy Simulation",
        "",
        f"Generated at: `{report.get('created_at')}`",
        "",
        "## Executive summary",
        "",
        "This report simulates alternative Stage 1 policies without modifying production filters.",
        "",
        "## Scenario comparison",
        "",
        "| Scenario | Passed | Watchlist | Rejected | Pass rate | Watchlist rate | Rejection rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for row in report.get("scenario_summaries", []):
        lines.append(
            f"| {row.get('scenario_label')} | {row.get('passed')} | {row.get('watchlist')} | {row.get('rejected')} | "
            f"{row.get('pass_rate_percent')}% | {row.get('watchlist_rate_percent')}% | {row.get('rejection_rate_percent')}% |"
        )

    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            report.get("recommended_policy_note", ""),
            "",
            "## Scenario rationale",
            "",
        ]
    )

    for row in report.get("scenario_summaries", []):
        lines.append(f"### {row.get('scenario_label')}")
        lines.append("")
        lines.append(row.get("description", ""))
        lines.append("")
        thresholds = row.get("thresholds", {})
        lines.append(
            f"- Minimum market cap: `{thresholds.get('min_market_cap')}`; watch below `{thresholds.get('watch_market_cap')}`."
        )
        lines.append(
            f"- Minimum price: `{thresholds.get('min_price')}`; watch below `{thresholds.get('watch_price')}`."
        )
        lines.append(
            f"- Minimum dollar volume: `{thresholds.get('min_dollar_volume')}`; watch below `{thresholds.get('watch_dollar_volume')}`."
        )
        lines.append("")

    lines.extend(
        [
            "## Controls",
            "",
            f"- OpenAI called: `{report.get('openai_called')}`",
            f"- API called: `{report.get('api_called')}`",
            f"- yfinance called: `{report.get('yfinance_called')}`",
            f"- app.py modified: `{report.get('app_modified')}`",
            f"- filters modified: `{report.get('filters_modified')}`",
            f"- release v0.6 modified: `{report.get('release_v0_6_modified')}`",
            "",
        ]
    )

    return "\n".join(lines)


def build_stage1_policy_simulation(input_path: Path = DEFAULT_INPUT) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input not found: {input_path}. Run Phase 7A.6 first."
        )

    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(input_path)
    df = _normalize_input(raw)

    scenario_summaries = []
    all_decisions = []

    for key, policy in POLICIES.items():
        summary, decisions = _simulate_policy(df, key, policy)
        scenario_summaries.append(summary)
        all_decisions.append(decisions)

    decisions_df = pd.concat(all_decisions, ignore_index=True)
    decisions_df.to_csv(SCENARIO_DECISIONS_CSV, index=False, encoding="utf-8-sig")

    summary_rows = []

    for row in scenario_summaries:
        summary_rows.append(
            {
                "scenario": row["scenario"],
                "scenario_label": row["scenario_label"],
                "total": row["total"],
                "passed": row["passed"],
                "watchlist": row["watchlist"],
                "rejected": row["rejected"],
                "pass_rate_percent": row["pass_rate_percent"],
                "watchlist_rate_percent": row["watchlist_rate_percent"],
                "rejection_rate_percent": row["rejection_rate_percent"],
                "min_market_cap": row["thresholds"]["min_market_cap"],
                "watch_market_cap": row["thresholds"]["watch_market_cap"],
                "min_price": row["thresholds"]["min_price"],
                "watch_price": row["thresholds"]["watch_price"],
                "min_dollar_volume": row["thresholds"]["min_dollar_volume"],
                "watch_dollar_volume": row["thresholds"]["watch_dollar_volume"],
            }
        )

    pd.DataFrame(summary_rows).to_csv(SCENARIO_SUMMARY_CSV, index=False, encoding="utf-8-sig")

    reasons_df = _reason_distribution(decisions_df)
    reasons_df.to_csv(SCENARIO_BUCKETS_CSV, index=False, encoding="utf-8-sig")

    report = {
        "phase": "7B.1",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "input_path": str(input_path),
        "input_rows": int(len(df)),
        "scenario_summaries": scenario_summaries,
        "recommended_policy": "balanced",
        "recommended_policy_note": (
            "Recommended next step: use the balanced scenario as the first candidate policy for review, "
            "but do not apply it automatically. It raises market-cap and liquidity discipline while preserving "
            "small-cap discovery potential. Conservative may be more suitable for institutional-only portfolios; "
            "aggressive is useful for early-stage scouting but increases noise."
        ),
        "output_files": {
            "report_json": str(REPORT_JSON),
            "report_md": str(REPORT_MD),
            "scenario_summary_csv": str(SCENARIO_SUMMARY_CSV),
            "scenario_decisions_csv": str(SCENARIO_DECISIONS_CSV),
            "scenario_reason_distribution_csv": str(SCENARIO_BUCKETS_CSV),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filters_modified": False,
        "release_v0_6_modified": False,
    }

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_MD.write_text(_render_markdown(report), encoding="utf-8")

    return report


def print_summary(report: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7B.1 Stage 1 policy simulation")
    print("=" * 78)
    print(f"Status: {report.get('status')}")
    print(f"Input rows: {report.get('input_rows')}")
    print()
    print("Scenario comparison")
    print("-" * 78)

    for row in report.get("scenario_summaries", []):
        print(
            f"{row.get('scenario_label')}: "
            f"passed={row.get('passed')} ({row.get('pass_rate_percent')}%), "
            f"watchlist={row.get('watchlist')} ({row.get('watchlist_rate_percent')}%), "
            f"rejected={row.get('rejected')} ({row.get('rejection_rate_percent')}%)"
        )

    print()
    print(f"Recommended policy for review: {report.get('recommended_policy')}")
    print("No filters were modified.")


def main() -> int:
    report = build_stage1_policy_simulation()
    print_summary(report)
    return 0 if report.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
