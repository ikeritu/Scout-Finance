
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRY_RUN_DIR = PROJECT_ROOT / "outputs" / "scouting" / "stage1_balanced_dry_run"
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

TRANSITIONS = DRY_RUN_DIR / "balanced_dry_run_transitions.csv"
DRY_RUN_SUMMARY = DRY_RUN_DIR / "balanced_dry_run_summary.json"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_approval_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_approval_report.md"
TRANSITION_SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_transition_summary.csv"
REASON_SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_reason_summary.csv"
APPROVAL_CSV = SCOUTING_OUTPUTS_DIR / "stage1_balanced_impact_approval_decision.csv"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _split_reasons(series: pd.Series) -> pd.DataFrame:
    rows = []
    for value in series.fillna("").astype(str):
        for item in value.split(","):
            reason = item.strip()
            if reason:
                rows.append({"reason_code": reason})
    return pd.DataFrame(rows)


def _rate(n: int, d: int) -> float:
    return round((n / d) * 100, 2) if d else 0.0


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Scout Finance — Phase 7B.7 Balanced Stage 1 Impact Approval",
        "",
        f"Generated at: `{report.get('created_at')}`",
        "",
        "## Executive decision",
        "",
        f"- Decision: **{report.get('decision')}**.",
        f"- Apply to production now: **{report.get('apply_to_production_now')}**.",
        f"- Recommended next step: **{report.get('recommended_next_step')}**.",
        "",
        "## Impact summary",
        "",
        f"- Input companies: **{report.get('input_companies')}**.",
        f"- Balanced passed: **{report.get('balanced_passed')}** ({report.get('balanced_pass_rate_percent')}%).",
        f"- Balanced watchlist: **{report.get('balanced_watchlist')}** ({report.get('balanced_watchlist_rate_percent')}%).",
        f"- Balanced rejected: **{report.get('balanced_rejected')}** ({report.get('balanced_rejection_rate_percent')}%).",
        "",
        "## Transition summary",
        "",
        "| Transition | Count |",
        "|---|---:|",
    ]

    for row in report.get("transition_summary", []):
        lines.append(f"| {row.get('transition')} | {row.get('count')} |")

    lines.extend([
        "",
        "## Safety findings",
        "",
        f"- Passed retained as passed: **{report.get('passed_retained_as_passed')}**.",
        f"- Passed moved to watchlist: **{report.get('passed_to_watchlist')}**.",
        f"- Passed moved to rejected: **{report.get('passed_to_rejected')}**.",
        f"- Watchlist moved to rejected: **{report.get('watchlist_to_rejected')}**.",
        "",
        "## Professional interpretation",
        "",
    ])

    for item in report.get("professional_interpretation", []):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Main reasons affected",
        "",
        "| Reason code | Count |",
        "|---|---:|",
    ])

    for row in report.get("reason_summary", []):
        lines.append(f"| {row.get('reason_code')} | {row.get('count')} |")

    lines.extend([
        "",
        "## Approval guardrails",
        "",
        "- Do not overwrite production Stage 1 files without a backup.",
        "- Apply only through a guarded patch phase.",
        "- After applying, rerun the 500-company validation.",
        "- Compare new production outputs against the 7B.6 dry-run.",
        "- Keep actual/base outputs available for rollback.",
        "",
        "## Controls",
        "",
        f"- OpenAI called: `{report.get('openai_called')}`",
        f"- API called: `{report.get('api_called')}`",
        f"- yfinance called: `{report.get('yfinance_called')}`",
        f"- app.py modified: `{report.get('app_modified')}`",
        f"- filters modified: `{report.get('filters_modified')}`",
        f"- production Stage 1 overwritten: `{report.get('production_stage1_overwritten')}`",
        f"- release modified: `{report.get('release_modified')}`",
        "",
    ])

    return "\n".join(lines)


def build_balanced_impact_approval() -> dict[str, Any]:
    if not TRANSITIONS.exists():
        raise FileNotFoundError(
            f"Missing transitions CSV: {TRANSITIONS}. Run Phase 7B.6 first."
        )

    transitions = pd.read_csv(TRANSITIONS)
    dry_summary = _read_json(DRY_RUN_SUMMARY)

    if transitions.empty:
        raise ValueError("Transitions CSV is empty.")

    if "transition" not in transitions.columns:
        transitions["transition"] = transitions["real_decision"].astype(str) + "->" + transitions["balanced_decision"].astype(str)

    transition_summary_df = (
        transitions.groupby("transition")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    transition_summary_df.to_csv(TRANSITION_SUMMARY_CSV, index=False, encoding="utf-8-sig")

    reason_df = _split_reasons(transitions.get("simulated_reasons", pd.Series(dtype=str)))
    if reason_df.empty:
        reason_summary_df = pd.DataFrame(columns=["reason_code", "count"])
    else:
        reason_summary_df = (
            reason_df.groupby("reason_code")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
    reason_summary_df.to_csv(REASON_SUMMARY_CSV, index=False, encoding="utf-8-sig")

    input_companies = int(len(transitions))
    balanced_passed = int((transitions["balanced_decision"] == "PASSED").sum())
    balanced_watchlist = int((transitions["balanced_decision"] == "WATCHLIST").sum())
    balanced_rejected = int((transitions["balanced_decision"] == "REJECTED").sum())

    passed_retained = int(((transitions["real_decision"] == "PASSED") & (transitions["balanced_decision"] == "PASSED")).sum())
    passed_to_watchlist = int(((transitions["real_decision"] == "PASSED") & (transitions["balanced_decision"] == "WATCHLIST")).sum())
    passed_to_rejected = int(((transitions["real_decision"] == "PASSED") & (transitions["balanced_decision"] == "REJECTED")).sum())
    watchlist_to_rejected = int(((transitions["real_decision"] == "WATCHLIST") & (transitions["balanced_decision"] == "REJECTED")).sum())

    if passed_to_rejected == 0 and balanced_passed > 0 and watchlist_to_rejected >= 0:
        decision = "APPROVE_FOR_GUARDED_APPLICATION"
        recommended_next_step = "Phase 7B.8 guarded implementation patch"
    else:
        decision = "HOLD_FOR_REVIEW"
        recommended_next_step = "Review transition impact before implementation"

    interpretation = [
        "Balanced policy reduces pass-through noise while keeping a substantial discovery pool.",
        "No current PASSED company is moved directly to REJECTED.",
        "PASSED to WATCHLIST transitions are review downgrades, not hard exclusions.",
        "WATCHLIST to REJECTED transitions are primarily the intended cleanup area.",
        "Production filters should only be changed in a guarded implementation phase with backup and rollback.",
    ]

    report = {
        "phase": "7B.7",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "source_dry_run_summary": str(DRY_RUN_SUMMARY),
        "source_transitions": str(TRANSITIONS),
        "input_companies": input_companies,
        "balanced_passed": balanced_passed,
        "balanced_watchlist": balanced_watchlist,
        "balanced_rejected": balanced_rejected,
        "balanced_pass_rate_percent": _rate(balanced_passed, input_companies),
        "balanced_watchlist_rate_percent": _rate(balanced_watchlist, input_companies),
        "balanced_rejection_rate_percent": _rate(balanced_rejected, input_companies),
        "passed_retained_as_passed": passed_retained,
        "passed_to_watchlist": passed_to_watchlist,
        "passed_to_rejected": passed_to_rejected,
        "watchlist_to_rejected": watchlist_to_rejected,
        "transition_summary": transition_summary_df.to_dict(orient="records"),
        "reason_summary": reason_summary_df.to_dict(orient="records"),
        "professional_interpretation": interpretation,
        "decision": decision,
        "recommended_next_step": recommended_next_step,
        "apply_to_production_now": False,
        "output_files": {
            "report_json": str(REPORT_JSON),
            "report_md": str(REPORT_MD),
            "transition_summary_csv": str(TRANSITION_SUMMARY_CSV),
            "reason_summary_csv": str(REASON_SUMMARY_CSV),
            "approval_csv": str(APPROVAL_CSV),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filters_modified": False,
        "production_stage1_overwritten": False,
        "release_modified": False,
    }

    approval_row = {
        "phase": report["phase"],
        "decision": decision,
        "recommended_next_step": recommended_next_step,
        "apply_to_production_now": False,
        "candidate_policy": "balanced",
        "passed_to_rejected": passed_to_rejected,
        "passed_to_watchlist": passed_to_watchlist,
        "watchlist_to_rejected": watchlist_to_rejected,
    }
    pd.DataFrame([approval_row]).to_csv(APPROVAL_CSV, index=False, encoding="utf-8-sig")

    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_MD.write_text(_render_markdown(report), encoding="utf-8")

    return report


def print_summary(report: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7B.7 balanced policy impact approval")
    print("=" * 78)
    print(f"Status: {report.get('status')}")
    print(f"Decision: {report.get('decision')}")
    print(f"Apply to production now: {report.get('apply_to_production_now')}")
    print(f"Recommended next step: {report.get('recommended_next_step')}")
    print()
    print("Impact")
    print("-" * 78)
    print(f"Balanced passed/watchlist/rejected: {report.get('balanced_passed')} / {report.get('balanced_watchlist')} / {report.get('balanced_rejected')}")
    print(f"Passed retained as passed: {report.get('passed_retained_as_passed')}")
    print(f"Passed to watchlist: {report.get('passed_to_watchlist')}")
    print(f"Passed to rejected: {report.get('passed_to_rejected')}")
    print(f"Watchlist to rejected: {report.get('watchlist_to_rejected')}")
    print()
    print("No production filters were modified.")


def main() -> int:
    report = build_balanced_impact_approval()
    print_summary(report)
    return 0 if report.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
