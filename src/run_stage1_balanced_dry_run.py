
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"
DRY_RUN_DIR = SCOUTING_OUTPUTS_DIR / "stage1_balanced_dry_run"

FINAL_DECISIONS = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_decisions.csv"
CANDIDATE_DECISION = SCOUTING_OUTPUTS_DIR / "stage1_candidate_policy_decision_report.json"

REAL_STAGE1_PASSED = PROJECT_ROOT / "data" / "stages" / "stage1_passed.csv"
REAL_STAGE1_WATCHLIST = PROJECT_ROOT / "data" / "stages" / "stage1_watchlist.csv"
REAL_STAGE1_REJECTED = PROJECT_ROOT / "data" / "stages" / "stage1_rejected.csv"

PASSED_OUT = DRY_RUN_DIR / "balanced_dry_run_passed.csv"
WATCHLIST_OUT = DRY_RUN_DIR / "balanced_dry_run_watchlist.csv"
REJECTED_OUT = DRY_RUN_DIR / "balanced_dry_run_rejected.csv"
TRANSITIONS_OUT = DRY_RUN_DIR / "balanced_dry_run_transitions.csv"
SUMMARY_JSON = DRY_RUN_DIR / "balanced_dry_run_summary.json"
REPORT_MD = DRY_RUN_DIR / "balanced_dry_run_report.md"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _with_real_decision(path: Path, decision: str) -> pd.DataFrame:
    df = _read_csv(path)
    if df.empty:
        return pd.DataFrame()
    if "ticker" not in df.columns and "Symbol" in df.columns:
        df["ticker"] = df["Symbol"]
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    df["real_decision"] = decision
    return df


def _real_stage1() -> pd.DataFrame:
    parts = [
        _with_real_decision(REAL_STAGE1_PASSED, "PASSED"),
        _with_real_decision(REAL_STAGE1_WATCHLIST, "WATCHLIST"),
        _with_real_decision(REAL_STAGE1_REJECTED, "REJECTED"),
    ]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame()
    real = pd.concat(parts, ignore_index=True)
    keep = [c for c in ["ticker", "real_decision"] if c in real.columns]
    return real[keep].copy()


def _load_balanced_decisions() -> pd.DataFrame:
    if not FINAL_DECISIONS.exists():
        raise FileNotFoundError(
            f"Missing final decisions CSV: {FINAL_DECISIONS}. Run Phase 7B.4 first."
        )

    df = pd.read_csv(FINAL_DECISIONS)

    if "scenario" not in df.columns:
        raise ValueError("Final decisions CSV has no scenario column.")

    balanced = df[df["scenario"].astype(str) == "balanced"].copy()

    if balanced.empty:
        raise ValueError("No balanced scenario rows found in final decisions CSV.")

    if "ticker" not in balanced.columns:
        raise ValueError("Balanced decisions have no ticker column.")

    balanced["ticker"] = balanced["ticker"].astype(str).str.upper().str.strip()

    return balanced


def _rate(n: int, d: int) -> float:
    return round((n / d) * 100, 2) if d else 0.0


def _transition_summary(transitions: pd.DataFrame) -> list[dict[str, Any]]:
    if transitions.empty:
        return []

    grouped = (
        transitions.groupby(["real_decision", "balanced_decision"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    return grouped.to_dict(orient="records")


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Scout Finance — Phase 7B.6 Balanced Policy Protected Dry-Run",
        "",
        f"Generated at: `{summary.get('created_at')}`",
        "",
        "## Executive summary",
        "",
        f"- Input companies: **{summary.get('input_companies')}**.",
        f"- Balanced passed: **{summary.get('balanced_passed')}** ({summary.get('balanced_pass_rate_percent')}%).",
        f"- Balanced watchlist: **{summary.get('balanced_watchlist')}** ({summary.get('balanced_watchlist_rate_percent')}%).",
        f"- Balanced rejected: **{summary.get('balanced_rejected')}** ({summary.get('balanced_rejection_rate_percent')}%).",
        "",
        "## Current/base vs balanced",
        "",
        "| Transition | Count |",
        "|---|---:|",
    ]

    for row in summary.get("transition_summary", []):
        lines.append(
            f"| {row.get('real_decision')} → {row.get('balanced_decision')} | {row.get('count')} |"
        )

    lines.extend(
        [
            "",
            "## Safety interpretation",
            "",
            f"- Passed retained as passed: **{summary.get('passed_retained_as_passed')}**.",
            f"- Passed moved to watchlist: **{summary.get('passed_to_watchlist')}**.",
            f"- Passed moved to rejected: **{summary.get('passed_to_rejected')}**.",
            "",
            "The dry-run does not change production outputs. It only writes separated dry-run files under `outputs/scouting/stage1_balanced_dry_run`.",
            "",
            "## Controls",
            "",
            f"- OpenAI called: `{summary.get('openai_called')}`",
            f"- API called: `{summary.get('api_called')}`",
            f"- yfinance called: `{summary.get('yfinance_called')}`",
            f"- app.py modified: `{summary.get('app_modified')}`",
            f"- filters modified: `{summary.get('filters_modified')}`",
            f"- production Stage 1 overwritten: `{summary.get('production_stage1_overwritten')}`",
            f"- release modified: `{summary.get('release_modified')}`",
            "",
        ]
    )

    return "\n".join(lines)


def run_balanced_policy_dry_run() -> dict[str, Any]:
    DRY_RUN_DIR.mkdir(parents=True, exist_ok=True)

    candidate = _read_json(CANDIDATE_DECISION)
    if candidate.get("recommended_policy") not in (None, "balanced"):
        raise ValueError(
            f"Candidate policy is not balanced: {candidate.get('recommended_policy')}"
        )

    balanced = _load_balanced_decisions()
    real = _real_stage1()

    balanced = balanced.rename(columns={"simulated_decision": "balanced_decision"})
    balanced["balanced_decision"] = balanced["balanced_decision"].astype(str)

    passed = balanced[balanced["balanced_decision"] == "PASSED"].copy()
    watchlist = balanced[balanced["balanced_decision"] == "WATCHLIST"].copy()
    rejected = balanced[balanced["balanced_decision"] == "REJECTED"].copy()

    passed.to_csv(PASSED_OUT, index=False, encoding="utf-8-sig")
    watchlist.to_csv(WATCHLIST_OUT, index=False, encoding="utf-8-sig")
    rejected.to_csv(REJECTED_OUT, index=False, encoding="utf-8-sig")

    transitions = balanced.merge(real, on="ticker", how="left")
    transitions = transitions[
        [
            c for c in [
                "ticker",
                "name",
                "real_decision",
                "balanced_decision",
                "simulated_reasons",
                "weak_reasons",
                "market_cap",
                "price",
                "avg_volume_90d",
                "dollar_volume_90d",
            ]
            if c in transitions.columns
        ]
    ].copy()

    transitions["transition"] = transitions["real_decision"].astype(str) + "->" + transitions["balanced_decision"].astype(str)
    transitions.to_csv(TRANSITIONS_OUT, index=False, encoding="utf-8-sig")

    total = len(balanced)
    passed_count = len(passed)
    watch_count = len(watchlist)
    rejected_count = len(rejected)

    passed_to_watchlist = int(((transitions["real_decision"] == "PASSED") & (transitions["balanced_decision"] == "WATCHLIST")).sum())
    passed_to_rejected = int(((transitions["real_decision"] == "PASSED") & (transitions["balanced_decision"] == "REJECTED")).sum())
    passed_retained_as_passed = int(((transitions["real_decision"] == "PASSED") & (transitions["balanced_decision"] == "PASSED")).sum())

    summary = {
        "phase": "7B.6",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "candidate_policy": "balanced",
        "decision_source": str(CANDIDATE_DECISION),
        "input_companies": total,
        "balanced_passed": passed_count,
        "balanced_watchlist": watch_count,
        "balanced_rejected": rejected_count,
        "balanced_pass_rate_percent": _rate(passed_count, total),
        "balanced_watchlist_rate_percent": _rate(watch_count, total),
        "balanced_rejection_rate_percent": _rate(rejected_count, total),
        "transition_summary": _transition_summary(transitions),
        "passed_retained_as_passed": passed_retained_as_passed,
        "passed_to_watchlist": passed_to_watchlist,
        "passed_to_rejected": passed_to_rejected,
        "output_files": {
            "passed": str(PASSED_OUT),
            "watchlist": str(WATCHLIST_OUT),
            "rejected": str(REJECTED_OUT),
            "transitions": str(TRANSITIONS_OUT),
            "summary": str(SUMMARY_JSON),
            "report_md": str(REPORT_MD),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filters_modified": False,
        "production_stage1_overwritten": False,
        "release_modified": False,
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_MD.write_text(_render_markdown(summary), encoding="utf-8")

    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7B.6 balanced policy protected dry-run")
    print("=" * 78)
    print(f"Status: {summary.get('status')}")
    print(f"Input companies: {summary.get('input_companies')}")
    print()
    print("Balanced dry-run")
    print("-" * 78)
    print(f"Passed: {summary.get('balanced_passed')} ({summary.get('balanced_pass_rate_percent')}%)")
    print(f"Watchlist: {summary.get('balanced_watchlist')} ({summary.get('balanced_watchlist_rate_percent')}%)")
    print(f"Rejected: {summary.get('balanced_rejected')} ({summary.get('balanced_rejection_rate_percent')}%)")
    print()
    print("Safety")
    print("-" * 78)
    print(f"Passed retained as passed: {summary.get('passed_retained_as_passed')}")
    print(f"Passed moved to watchlist: {summary.get('passed_to_watchlist')}")
    print(f"Passed moved to rejected: {summary.get('passed_to_rejected')}")
    print()
    print("No production Stage 1 files were overwritten.")


def main() -> int:
    summary = run_balanced_policy_dry_run()
    print_summary(summary)
    return 0 if summary.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
