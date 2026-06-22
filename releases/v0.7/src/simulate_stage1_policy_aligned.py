
"""
Scout Finance — Phase 7B.3 aligned Stage 1 policy simulator.

Purpose:
- Repair the Stage 1 simulator so current_base matches real Stage 1.
- Treat PRICE_WATCHLIST_RANGE as a weak warning, not as automatic watchlist.
- Keep conservative/balanced/aggressive scenarios.
- Do not modify production filters.

This module:
- does not call OpenAI;
- does not call APIs;
- does not call yfinance;
- does not modify app.py;
- does not modify releases/v0.6;
- does not modify src/filter_stage1.py.

Run:
    ./.venv/Scripts/python.exe -m src.simulate_stage1_policy_aligned
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

REAL_STAGE1_PASSED = PROJECT_ROOT / "data" / "stages" / "stage1_passed.csv"
REAL_STAGE1_WATCHLIST = PROJECT_ROOT / "data" / "stages" / "stage1_watchlist.csv"
REAL_STAGE1_REJECTED = PROJECT_ROOT / "data" / "stages" / "stage1_rejected.csv"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_aligned_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_aligned_report.md"
SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_aligned_summary.csv"
DECISIONS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_aligned_decisions.csv"
ALIGNMENT_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_aligned_current_base_alignment.csv"


POLICIES = {
    "current_base": {
        "label": "Actual/base alineado",
        "description": "Aligned approximation of real Stage 1 behavior.",
        "min_market_cap": 100_000_000,
        "watch_market_cap": 300_000_000,
        "min_price": 1.0,
        "watch_price": 5.0,
        "min_dollar_volume": 500_000,
        "watch_dollar_volume": 2_000_000,
        "price_watchlist_is_weak": True,
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
        "price_watchlist_is_weak": True,
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
        "price_watchlist_is_weak": True,
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
        "price_watchlist_is_weak": True,
    },
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


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

    for col in ["ticker", "name", "market_cap", "price", "avg_volume_90d"]:
        if col not in out.columns:
            out[col] = None

    out["ticker"] = out["ticker"].astype(str).str.upper().str.strip()
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


def _evaluate_row(row: pd.Series, policy: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    hard_fail_reasons: list[str] = []
    watch_reasons: list[str] = []
    weak_watch_reasons: list[str] = []

    market_cap = row.get("market_cap")
    price = row.get("price")
    dollar_volume = row.get("dollar_volume_90d")

    if pd.isna(market_cap):
        hard_fail_reasons.append("MISSING_MARKET_CAP")
    elif market_cap < policy["min_market_cap"]:
        hard_fail_reasons.append("MARKET_CAP_BELOW_MINIMUM")
    elif market_cap < policy["watch_market_cap"]:
        watch_reasons.append("MARKET_CAP_WATCHLIST_RANGE")

    if pd.isna(price):
        hard_fail_reasons.append("MISSING_PRICE")
    elif price < policy["min_price"]:
        hard_fail_reasons.append("PRICE_BELOW_MINIMUM")
    elif price < policy["watch_price"]:
        if policy.get("price_watchlist_is_weak", True):
            weak_watch_reasons.append("PRICE_WATCHLIST_RANGE")
        else:
            watch_reasons.append("PRICE_WATCHLIST_RANGE")

    if pd.isna(dollar_volume):
        hard_fail_reasons.append("MISSING_DOLLAR_VOLUME")
    elif dollar_volume < policy["min_dollar_volume"]:
        hard_fail_reasons.append("LOW_DOLLAR_VOLUME")
    elif dollar_volume < policy["watch_dollar_volume"]:
        watch_reasons.append("DOLLAR_VOLUME_WATCHLIST_RANGE")

    all_reasons = hard_fail_reasons + watch_reasons + weak_watch_reasons

    if hard_fail_reasons:
        return "REJECTED", all_reasons, weak_watch_reasons

    # Key alignment: price watchlist alone does not create WATCHLIST.
    if watch_reasons:
        return "WATCHLIST", all_reasons, weak_watch_reasons

    return "PASSED", all_reasons, weak_watch_reasons


def _simulate_policy(df: pd.DataFrame, scenario: str, policy: dict[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    rows = []

    for _, row in df.iterrows():
        decision, reasons, weak_reasons = _evaluate_row(row, policy)
        rows.append(
            {
                "scenario": scenario,
                "scenario_label": policy["label"],
                "ticker": row.get("ticker"),
                "name": row.get("name"),
                "market_cap": row.get("market_cap"),
                "price": row.get("price"),
                "avg_volume_90d": row.get("avg_volume_90d"),
                "dollar_volume_90d": row.get("dollar_volume_90d"),
                "simulated_decision": decision,
                "simulated_reasons": ", ".join(reasons),
                "weak_watch_reasons": ", ".join(weak_reasons),
            }
        )

    decisions = pd.DataFrame(rows)

    total = len(decisions)
    passed = int((decisions["simulated_decision"] == "PASSED").sum())
    watchlist = int((decisions["simulated_decision"] == "WATCHLIST").sum())
    rejected = int((decisions["simulated_decision"] == "REJECTED").sum())

    summary = {
        "scenario": scenario,
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
    }

    return summary, decisions


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _real_stage1_decisions() -> pd.DataFrame:
    parts = []

    for path, decision in [
        (REAL_STAGE1_PASSED, "PASSED"),
        (REAL_STAGE1_WATCHLIST, "WATCHLIST"),
        (REAL_STAGE1_REJECTED, "REJECTED"),
    ]:
        df = _read_csv(path)
        if not df.empty:
            if "ticker" not in df.columns and "Symbol" in df.columns:
                df["ticker"] = df["Symbol"]
            df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
            df["real_decision"] = decision
            parts.append(df[["ticker", "real_decision"]].copy())

    if not parts:
        return pd.DataFrame(columns=["ticker", "real_decision"])

    return pd.concat(parts, ignore_index=True)


def _alignment(sim_current: pd.DataFrame) -> dict[str, Any]:
    real = _real_stage1_decisions()

    if real.empty or sim_current.empty:
        return {
            "available": False,
            "total_compared": 0,
            "matched": 0,
            "mismatched": 0,
            "match_rate_percent": 0,
        }

    compare = real.merge(
        sim_current[["ticker", "simulated_decision", "simulated_reasons"]],
        on="ticker",
        how="outer",
        indicator=True,
    )

    compare["alignment_status"] = compare.apply(
        lambda row: "MATCH" if row.get("real_decision") == row.get("simulated_decision") else "MISMATCH",
        axis=1,
    )

    compare.to_csv(ALIGNMENT_CSV, index=False, encoding="utf-8-sig")

    total = int(len(compare))
    matched = int((compare["alignment_status"] == "MATCH").sum())
    mismatched = int((compare["alignment_status"] == "MISMATCH").sum())

    mismatch_summary = (
        compare[compare["alignment_status"] == "MISMATCH"]
        .groupby(["real_decision", "simulated_decision"])
        .size()
        .reset_index(name="count")
        .to_dict(orient="records")
    )

    return {
        "available": True,
        "total_compared": total,
        "matched": matched,
        "mismatched": mismatched,
        "match_rate_percent": _rate(matched, total),
        "mismatch_summary": mismatch_summary,
        "alignment_csv": str(ALIGNMENT_CSV),
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Scout Finance — Phase 7B.3 Aligned Stage 1 Policy Simulator",
        "",
        f"Generated at: `{report.get('created_at')}`",
        "",
        "## Alignment result",
        "",
        f"- Compared: **{report.get('alignment', {}).get('total_compared')}**.",
        f"- Matched: **{report.get('alignment', {}).get('matched')}**.",
        f"- Mismatched: **{report.get('alignment', {}).get('mismatched')}**.",
        f"- Match rate: **{report.get('alignment', {}).get('match_rate_percent')}%**.",
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
            "## Rule correction",
            "",
            "PRICE_WATCHLIST_RANGE is now treated as a weak warning. It does not create WATCHLIST by itself.",
            "A company below the watch price can still pass if market cap and dollar volume are healthy.",
            "",
            "## Recommendation",
            "",
            report.get("recommendation", ""),
            "",
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


def build_aligned_stage1_policy_simulation(input_path: Path = DEFAULT_INPUT) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}. Run Phase 7A.6 first.")

    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    df = _normalize_input(pd.read_csv(input_path))

    scenario_summaries = []
    all_decisions = []
    current_decisions = pd.DataFrame()

    for scenario, policy in POLICIES.items():
        summary, decisions = _simulate_policy(df, scenario, policy)
        scenario_summaries.append(summary)
        all_decisions.append(decisions)

        if scenario == "current_base":
            current_decisions = decisions.copy()

    decisions_df = pd.concat(all_decisions, ignore_index=True)
    decisions_df.to_csv(DECISIONS_CSV, index=False, encoding="utf-8-sig")

    summary_rows = []
    for row in scenario_summaries:
        thresholds = row["thresholds"]
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
                "min_market_cap": thresholds["min_market_cap"],
                "watch_market_cap": thresholds["watch_market_cap"],
                "min_price": thresholds["min_price"],
                "watch_price": thresholds["watch_price"],
                "min_dollar_volume": thresholds["min_dollar_volume"],
                "watch_dollar_volume": thresholds["watch_dollar_volume"],
                "price_watchlist_is_weak": thresholds.get("price_watchlist_is_weak", True),
            }
        )

    pd.DataFrame(summary_rows).to_csv(SUMMARY_CSV, index=False, encoding="utf-8-sig")

    alignment = _alignment(current_decisions)

    report = {
        "phase": "7B.3",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "input_path": str(input_path),
        "input_rows": int(len(df)),
        "rule_correction": "PRICE_WATCHLIST_RANGE is weak; it does not create WATCHLIST by itself.",
        "scenario_summaries": scenario_summaries,
        "alignment": alignment,
        "recommendation": (
            "Use this aligned simulator as the decision-support tool for Stage 1 policy review. "
            "Do not modify production filters until a scenario is selected and validated."
        ),
        "output_files": {
            "report_json": str(REPORT_JSON),
            "report_md": str(REPORT_MD),
            "summary_csv": str(SUMMARY_CSV),
            "decisions_csv": str(DECISIONS_CSV),
            "alignment_csv": str(ALIGNMENT_CSV),
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
    print("Scout Finance — Phase 7B.3 aligned Stage 1 policy simulator")
    print("=" * 78)
    print(f"Status: {report.get('status')}")
    alignment = report.get("alignment", {})
    print(
        "Alignment current_base vs real Stage 1: "
        f"{alignment.get('matched')} matched / {alignment.get('mismatched')} mismatched "
        f"({alignment.get('match_rate_percent')}%)"
    )

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
    print("No production filters were modified.")


def main() -> int:
    report = build_aligned_stage1_policy_simulation()
    print_summary(report)
    return 0 if report.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
