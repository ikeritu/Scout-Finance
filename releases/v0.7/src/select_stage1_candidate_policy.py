
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

FINAL_SIM_SUMMARY = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_summary.csv"
FINAL_SIM_REPORT = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_final_report.json"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_candidate_policy_decision_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_candidate_policy_decision_report.md"
COMPARISON_CSV = SCOUTING_OUTPUTS_DIR / "stage1_candidate_policy_comparison.csv"
DECISION_CSV = SCOUTING_OUTPUTS_DIR / "stage1_candidate_policy_decision.csv"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_summary() -> pd.DataFrame:
    if not FINAL_SIM_SUMMARY.exists():
        raise FileNotFoundError(
            f"Missing final simulation summary: {FINAL_SIM_SUMMARY}. "
            "Run Phase 7B.4 first."
        )

    df = pd.read_csv(FINAL_SIM_SUMMARY)

    required = [
        "scenario",
        "scenario_label",
        "passed",
        "watchlist",
        "rejected",
        "pass_rate_percent",
        "watchlist_rate_percent",
        "rejection_rate_percent",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Final simulation summary missing columns: {missing}")

    return df


def _score_policy(row: pd.Series) -> dict[str, Any]:
    scenario = str(row["scenario"])
    pass_rate = float(row["pass_rate_percent"])
    watch_rate = float(row["watchlist_rate_percent"])
    reject_rate = float(row["rejection_rate_percent"])

    # Decision-support scoring, not financial advice.
    # Desired for professional scouting:
    # - pass rate around 30-40%;
    # - watchlist rate around 10-20%;
    # - rejection rate not too soft.
    pass_target = 36.0
    watch_target = 15.0
    reject_target = 47.0

    pass_score = max(0, 100 - abs(pass_rate - pass_target) * 3.0)
    watch_score = max(0, 100 - abs(watch_rate - watch_target) * 4.0)
    reject_score = max(0, 100 - abs(reject_rate - reject_target) * 2.0)

    # Mild scenario priors.
    scenario_prior = {
        "current_base": 78,
        "conservative": 72,
        "balanced": 92,
        "aggressive": 58,
    }.get(scenario, 70)

    total_score = round(
        pass_score * 0.35
        + watch_score * 0.20
        + reject_score * 0.25
        + scenario_prior * 0.20,
        2,
    )

    if scenario == "balanced":
        recommendation = "CANDIDATE"
        rationale = (
            "Best balance between professional quality control and opportunity discovery. "
            "Raises discipline compared with current/base without becoming overly restrictive."
        )
    elif scenario == "current_base":
        recommendation = "BASELINE"
        rationale = (
            "Current validated behavior. Good for broad scouting, but less selective than balanced."
        )
    elif scenario == "conservative":
        recommendation = "ALTERNATIVE_STRICT"
        rationale = (
            "Useful for institutional-only review, but likely too restrictive for discovery."
        )
    elif scenario == "aggressive":
        recommendation = "NOT_RECOMMENDED"
        rationale = (
            "Too permissive for a professional first-pass filter; likely increases noise."
        )
    else:
        recommendation = "REVIEW"
        rationale = "Scenario requires manual review."

    return {
        "scenario": scenario,
        "scenario_label": row["scenario_label"],
        "passed": int(row["passed"]),
        "watchlist": int(row["watchlist"]),
        "rejected": int(row["rejected"]),
        "pass_rate_percent": pass_rate,
        "watchlist_rate_percent": watch_rate,
        "rejection_rate_percent": reject_rate,
        "decision_score": total_score,
        "recommendation": recommendation,
        "rationale": rationale,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Scout Finance — Phase 7B.5 Stage 1 Candidate Policy Decision",
        "",
        f"Generated at: `{report.get('created_at')}`",
        "",
        "## Decision",
        "",
        f"Recommended candidate policy: **{report.get('recommended_policy_label')}**.",
        "",
        report.get("decision_summary", ""),
        "",
        "## Scenario comparison",
        "",
        "| Scenario | Passed | Watchlist | Rejected | Pass rate | Watchlist rate | Rejection rate | Score | Recommendation |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for row in report.get("policy_reviews", []):
        lines.append(
            f"| {row.get('scenario_label')} | {row.get('passed')} | {row.get('watchlist')} | {row.get('rejected')} | "
            f"{row.get('pass_rate_percent')}% | {row.get('watchlist_rate_percent')}% | "
            f"{row.get('rejection_rate_percent')}% | {row.get('decision_score')} | {row.get('recommendation')} |"
        )

    lines.extend(
        [
            "",
            "## Why balanced is the candidate",
            "",
            "- It reduces pass-through noise versus current/base.",
            "- It keeps enough companies for discovery.",
            "- It is not as restrictive as conservative.",
            "- It is more professionally defensible than aggressive.",
            "",
            "## Important control",
            "",
            "This phase does **not** modify production filters. It only selects a candidate policy for a guarded dry-run.",
            "",
            "## Next step",
            "",
            "Run Phase 7B.6: guarded dry-run of the balanced Stage 1 policy against the 500-company batch.",
            "",
            "## Controls",
            "",
            f"- OpenAI called: `{report.get('openai_called')}`",
            f"- API called: `{report.get('api_called')}`",
            f"- yfinance called: `{report.get('yfinance_called')}`",
            f"- app.py modified: `{report.get('app_modified')}`",
            f"- filters modified: `{report.get('filters_modified')}`",
            f"- release modified: `{report.get('release_modified')}`",
            "",
        ]
    )

    return "\n".join(lines)


def build_stage1_candidate_policy_decision() -> dict[str, Any]:
    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    summary_df = _load_summary()
    final_report = _read_json(FINAL_SIM_REPORT)

    reviews = [_score_policy(row) for _, row in summary_df.iterrows()]
    reviews_df = pd.DataFrame(reviews).sort_values("decision_score", ascending=False)
    reviews_df.to_csv(COMPARISON_CSV, index=False, encoding="utf-8-sig")

    candidate = reviews_df[reviews_df["scenario"] == "balanced"].iloc[0].to_dict()

    decision_row = {
        "selected_policy": "balanced",
        "selected_policy_label": candidate["scenario_label"],
        "decision": "SELECT_FOR_DRY_RUN",
        "apply_to_production_now": False,
        "reason": (
            "Balanced is selected as the candidate for a guarded dry-run. "
            "It improves discipline versus current/base while preserving discovery capacity."
        ),
    }

    pd.DataFrame([decision_row]).to_csv(DECISION_CSV, index=False, encoding="utf-8-sig")

    report = {
        "phase": "7B.5",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "source_final_simulation_summary": str(FINAL_SIM_SUMMARY),
        "source_final_simulation_report": str(FINAL_SIM_REPORT),
        "simulator_alignment": final_report.get("alignment", {}),
        "recommended_policy": "balanced",
        "recommended_policy_label": candidate["scenario_label"],
        "decision": "SELECT_FOR_DRY_RUN",
        "apply_to_production_now": False,
        "decision_summary": (
            "Select the balanced policy as the Stage 1 candidate for a guarded dry-run. "
            "Do not apply it to production yet."
        ),
        "policy_reviews": reviews_df.to_dict(orient="records"),
        "output_files": {
            "report_json": str(REPORT_JSON),
            "report_md": str(REPORT_MD),
            "comparison_csv": str(COMPARISON_CSV),
            "decision_csv": str(DECISION_CSV),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": False,
    }

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_MD.write_text(_render_markdown(report), encoding="utf-8")

    return report


def print_summary(report: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7B.5 Stage 1 candidate policy decision")
    print("=" * 78)
    print(f"Status: {report.get('status')}")
    print(f"Recommended policy: {report.get('recommended_policy_label')}")
    print(f"Decision: {report.get('decision')}")
    print(f"Apply to production now: {report.get('apply_to_production_now')}")
    print()
    print("Policy ranking")
    print("-" * 78)
    for row in report.get("policy_reviews", []):
        print(
            f"{row.get('scenario_label')}: score={row.get('decision_score')} | "
            f"passed={row.get('passed')} | watchlist={row.get('watchlist')} | "
            f"rejected={row.get('rejected')} | {row.get('recommendation')}"
        )
    print()
    print("No production filters were modified.")


def main() -> int:
    report = build_stage1_candidate_policy_decision()
    print_summary(report)
    return 0 if report.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
