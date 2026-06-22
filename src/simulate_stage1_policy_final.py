
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

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_report.md"
SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_summary.csv"
DECISIONS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_decisions.csv"
ALIGNMENT_CSV = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_current_base_alignment.csv"

POLICIES = {
    "current_base": {
        "label": "Actual/base final",
        "description": "Final aligned approximation of real Stage 1 behavior.",
        "min_market_cap": 100_000_000,
        "watch_market_cap": 300_000_000,
        "min_price": 1.0,
        "strong_price_watch": 3.0,
        "weak_price_watch": 5.0,
        "min_dollar_volume": 500_000,
        "watch_dollar_volume": 2_000_000,
    },
    "conservative": {
        "label": "Conservador",
        "description": "Higher quality/liquidity bar; fewer but cleaner candidates.",
        "min_market_cap": 300_000_000,
        "watch_market_cap": 1_000_000_000,
        "min_price": 2.0,
        "strong_price_watch": 4.0,
        "weak_price_watch": 8.0,
        "min_dollar_volume": 2_000_000,
        "watch_dollar_volume": 10_000_000,
    },
    "balanced": {
        "label": "Equilibrado",
        "description": "Professional middle ground; keeps small-cap optionality while improving quality.",
        "min_market_cap": 150_000_000,
        "watch_market_cap": 500_000_000,
        "min_price": 1.5,
        "strong_price_watch": 3.0,
        "weak_price_watch": 5.0,
        "min_dollar_volume": 1_000_000,
        "watch_dollar_volume": 5_000_000,
    },
    "aggressive": {
        "label": "Agresivo",
        "description": "More permissive; captures earlier/smaller opportunities with more noise.",
        "min_market_cap": 50_000_000,
        "watch_market_cap": 150_000_000,
        "min_price": 0.75,
        "strong_price_watch": 1.5,
        "weak_price_watch": 2.0,
        "min_dollar_volume": 250_000,
        "watch_dollar_volume": 1_000_000,
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
    rename_map = {"Symbol": "ticker", "Name": "name", "Market Cap": "market_cap", "Last Sale": "price", "Volume": "avg_volume_90d"}
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
    hard, watch, weak = [], [], []
    mc = row.get("market_cap")
    price = row.get("price")
    dv = row.get("dollar_volume_90d")

    if pd.isna(mc):
        hard.append("MISSING_MARKET_CAP")
    elif mc < policy["min_market_cap"]:
        hard.append("MARKET_CAP_BELOW_MINIMUM")
    elif mc < policy["watch_market_cap"]:
        watch.append("MARKET_CAP_WATCHLIST_RANGE")

    if pd.isna(price):
        hard.append("MISSING_PRICE")
    elif price < policy["min_price"]:
        hard.append("PRICE_BELOW_MINIMUM")
    elif price < policy["strong_price_watch"]:
        watch.append("PRICE_STRONG_WATCHLIST_RANGE")
    elif price < policy["weak_price_watch"]:
        weak.append("PRICE_WEAK_WATCHLIST_RANGE")

    if pd.isna(dv):
        hard.append("MISSING_DOLLAR_VOLUME")
    elif dv < policy["min_dollar_volume"]:
        hard.append("LOW_DOLLAR_VOLUME")
    elif dv < policy["watch_dollar_volume"]:
        watch.append("DOLLAR_VOLUME_WATCHLIST_RANGE")

    reasons = hard + watch + weak
    if hard:
        return "REJECTED", reasons, weak
    if watch:
        return "WATCHLIST", reasons, weak
    return "PASSED", reasons, weak


def _rate(n: int, d: int) -> float:
    return round((n / d) * 100, 2) if d else 0.0


def _simulate_policy(df: pd.DataFrame, scenario: str, policy: dict[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    rows = []
    for _, row in df.iterrows():
        decision, reasons, weak = _evaluate_row(row, policy)
        rows.append({
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
            "weak_reasons": ", ".join(weak),
        })
    decisions = pd.DataFrame(rows)
    total = len(decisions)
    passed = int((decisions["simulated_decision"] == "PASSED").sum())
    watchlist = int((decisions["simulated_decision"] == "WATCHLIST").sum())
    rejected = int((decisions["simulated_decision"] == "REJECTED").sum())
    return {
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
    }, decisions


def _real_stage1_decisions() -> pd.DataFrame:
    parts = []
    for path, decision in [(REAL_STAGE1_PASSED, "PASSED"), (REAL_STAGE1_WATCHLIST, "WATCHLIST"), (REAL_STAGE1_REJECTED, "REJECTED")]:
        df = _read_csv(path)
        if not df.empty:
            if "ticker" not in df.columns and "Symbol" in df.columns:
                df["ticker"] = df["Symbol"]
            df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
            df["real_decision"] = decision
            parts.append(df[["ticker", "real_decision"]].copy())
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["ticker", "real_decision"])


def _alignment(sim_current: pd.DataFrame) -> dict[str, Any]:
    real = _real_stage1_decisions()
    if real.empty or sim_current.empty:
        return {"available": False, "total_compared": 0, "matched": 0, "mismatched": 0, "match_rate_percent": 0, "mismatch_summary": [], "alignment_csv": str(ALIGNMENT_CSV)}
    compare = real.merge(
        sim_current[["ticker", "simulated_decision", "simulated_reasons", "market_cap", "price", "dollar_volume_90d"]],
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
        if mismatched else []
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
        "# Scout Finance — Phase 7B.4 Stage 1 Simulator Final Alignment",
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
        lines.append(f"| {row.get('scenario_label')} | {row.get('passed')} | {row.get('watchlist')} | {row.get('rejected')} | {row.get('pass_rate_percent')}% | {row.get('watchlist_rate_percent')}% | {row.get('rejection_rate_percent')}% |")
    lines += [
        "",
        "## Final price rule",
        "",
        "- price < 1: rejected.",
        "- 1 <= price < 3: strong watchlist.",
        "- 3 <= price < 5: weak warning only.",
        "- price >= 5: no price warning.",
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
    return "\n".join(lines)


def build_final_stage1_policy_simulation(input_path: Path = DEFAULT_INPUT) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}. Run Phase 7A.6 first.")
    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    df = _normalize_input(pd.read_csv(input_path))
    scenario_summaries, all_decisions = [], []
    current_decisions = pd.DataFrame()
    for scenario, policy in POLICIES.items():
        summary, decisions = _simulate_policy(df, scenario, policy)
        scenario_summaries.append(summary)
        all_decisions.append(decisions)
        if scenario == "current_base":
            current_decisions = decisions.copy()
    pd.concat(all_decisions, ignore_index=True).to_csv(DECISIONS_CSV, index=False, encoding="utf-8-sig")

    summary_rows = []
    for row in scenario_summaries:
        thresholds = row["thresholds"]
        summary_rows.append({
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
            "strong_price_watch": thresholds["strong_price_watch"],
            "weak_price_watch": thresholds["weak_price_watch"],
            "min_dollar_volume": thresholds["min_dollar_volume"],
            "watch_dollar_volume": thresholds["watch_dollar_volume"],
        })
    pd.DataFrame(summary_rows).to_csv(SUMMARY_CSV, index=False, encoding="utf-8-sig")
    alignment = _alignment(current_decisions)
    report = {
        "phase": "7B.4",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "input_path": str(input_path),
        "input_rows": int(len(df)),
        "final_price_rule": {
            "price_below_min": "REJECTED",
            "min_to_strong_watch": "WATCHLIST",
            "strong_watch_to_weak_watch": "WEAK_WARNING_ONLY",
            "above_weak_watch": "NO_PRICE_WARNING",
        },
        "scenario_summaries": scenario_summaries,
        "alignment": alignment,
        "recommendation": "The simulator is ready as the decision-support baseline for Stage 1 policy selection. Production filters were not changed.",
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
    print("Scout Finance — Phase 7B.4 Stage 1 simulator final alignment")
    print("=" * 78)
    print(f"Status: {report.get('status')}")
    a = report.get("alignment", {})
    print(f"Alignment current_base vs real Stage 1: {a.get('matched')} matched / {a.get('mismatched')} mismatched ({a.get('match_rate_percent')}%)")
    print()
    print("Scenario comparison")
    print("-" * 78)
    for row in report.get("scenario_summaries", []):
        print(f"{row.get('scenario_label')}: passed={row.get('passed')} ({row.get('pass_rate_percent')}%), watchlist={row.get('watchlist')} ({row.get('watchlist_rate_percent')}%), rejected={row.get('rejected')} ({row.get('rejection_rate_percent')}%)")
    print()
    print("No production filters were modified.")


def main() -> int:
    report = build_final_stage1_policy_simulation()
    print_summary(report)
    return 0 if report.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
