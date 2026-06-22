
"""
Scout Finance — Phase 7B.2 Align Stage 1 simulator with real Stage 1.

Purpose:
- Compare real Stage 1 outputs with simulated current_base outputs.
- Identify mismatches.
- Produce JSON, CSV and Markdown reports.
- Do not modify real filters yet.

This module:
- does not call OpenAI;
- does not call APIs;
- does not call yfinance;
- does not modify app.py;
- does not modify releases/v0.6;
- does not modify src/filter_stage1.py.

Run:
    ./.venv/Scripts/python.exe -m src.align_stage1_simulator
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

STAGE1_PASSED = PROJECT_ROOT / "data" / "stages" / "stage1_passed.csv"
STAGE1_WATCHLIST = PROJECT_ROOT / "data" / "stages" / "stage1_watchlist.csv"
STAGE1_REJECTED = PROJECT_ROOT / "data" / "stages" / "stage1_rejected.csv"
STAGE1_REJECTION_LOG = PROJECT_ROOT / "data" / "stages" / "stage1_rejection_log.csv"

SIM_DECISIONS = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_decisions.csv"
SIM_SUMMARY = SCOUTING_OUTPUTS_DIR / "stage1_policy_simulation_summary.csv"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_simulator_alignment_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_simulator_alignment_report.md"
MISMATCHES_CSV = SCOUTING_OUTPUTS_DIR / "stage1_simulator_alignment_mismatches.csv"
MISMATCH_SUMMARY_CSV = SCOUTING_OUTPUTS_DIR / "stage1_simulator_alignment_mismatch_summary.csv"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _with_real_decision(df: pd.DataFrame, decision: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy()
    out["real_decision"] = decision
    return out


def _make_real_decisions() -> pd.DataFrame:
    passed = _with_real_decision(_read_csv(STAGE1_PASSED), "PASSED")
    watchlist = _with_real_decision(_read_csv(STAGE1_WATCHLIST), "WATCHLIST")
    rejected = _with_real_decision(_read_csv(STAGE1_REJECTED), "REJECTED")

    parts = [df for df in [passed, watchlist, rejected] if not df.empty]

    if not parts:
        return pd.DataFrame()

    real = pd.concat(parts, ignore_index=True)

    # Normalize ticker column if needed.
    if "ticker" not in real.columns and "Symbol" in real.columns:
        real["ticker"] = real["Symbol"]

    real["ticker"] = real["ticker"].astype(str).str.upper().str.strip()

    return real


def _make_sim_base_decisions() -> pd.DataFrame:
    sim = _read_csv(SIM_DECISIONS)

    if sim.empty:
        return pd.DataFrame()

    if "scenario" in sim.columns:
        sim = sim[sim["scenario"].astype(str) == "current_base"].copy()

    if "ticker" not in sim.columns and "Symbol" in sim.columns:
        sim["ticker"] = sim["Symbol"]

    sim["ticker"] = sim["ticker"].astype(str).str.upper().str.strip()

    return sim


def _add_rejection_reasons(mismatches: pd.DataFrame) -> pd.DataFrame:
    if mismatches.empty:
        return mismatches

    log = _read_csv(STAGE1_REJECTION_LOG)

    if log.empty or "ticker" not in log.columns or "reason_code" not in log.columns:
        mismatches["real_rejection_log_reasons"] = ""
        return mismatches

    log["ticker"] = log["ticker"].astype(str).str.upper().str.strip()

    reasons = (
        log.groupby("ticker")["reason_code"]
        .apply(lambda x: ", ".join(sorted(set(str(v) for v in x if pd.notna(v)))))
        .reset_index(name="real_rejection_log_reasons")
    )

    return mismatches.merge(reasons, on="ticker", how="left")


def _safe_col(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series([None] * len(df))


def build_stage1_simulator_alignment_report() -> dict[str, Any]:
    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    real = _make_real_decisions()
    sim = _make_sim_base_decisions()

    if real.empty:
        raise FileNotFoundError("Real Stage 1 outputs are missing or empty. Run Phase 7A.6 first.")

    if sim.empty:
        raise FileNotFoundError("Simulation decisions are missing or empty. Run Phase 7B.1 first.")

    sim_keep_cols = [
        c for c in [
            "ticker",
            "simulated_decision",
            "simulated_reasons",
            "market_cap",
            "price",
            "avg_volume_90d",
            "dollar_volume_90d",
        ]
        if c in sim.columns
    ]

    real_keep_cols = [
        c for c in [
            "ticker",
            "name",
            "real_decision",
            "market_cap",
            "price",
            "avg_volume_90d",
            "dollar_volume_90d",
        ]
        if c in real.columns
    ]

    merged = real[real_keep_cols].merge(
        sim[sim_keep_cols],
        on="ticker",
        how="outer",
        suffixes=("_real", "_sim"),
        indicator=True,
    )

    merged["alignment_status"] = merged.apply(
        lambda row: "MATCH" if row.get("real_decision") == row.get("simulated_decision") else "MISMATCH",
        axis=1,
    )

    mismatches = merged[merged["alignment_status"] == "MISMATCH"].copy()
    mismatches = _add_rejection_reasons(mismatches)

    # Choose useful column order.
    preferred_cols = [
        "ticker",
        "name",
        "real_decision",
        "simulated_decision",
        "simulated_reasons",
        "real_rejection_log_reasons",
        "market_cap_real",
        "price_real",
        "avg_volume_90d_real",
        "dollar_volume_90d_real",
        "market_cap_sim",
        "price_sim",
        "avg_volume_90d_sim",
        "dollar_volume_90d_sim",
        "_merge",
    ]
    cols = [c for c in preferred_cols if c in mismatches.columns]
    mismatches = mismatches[cols].copy()

    mismatches.to_csv(MISMATCHES_CSV, index=False, encoding="utf-8-sig")

    real_counts = real["real_decision"].value_counts().to_dict()
    sim_counts = sim["simulated_decision"].value_counts().to_dict()

    mismatch_summary = (
        merged[merged["alignment_status"] == "MISMATCH"]
        .groupby(["real_decision", "simulated_decision"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    mismatch_summary.to_csv(MISMATCH_SUMMARY_CSV, index=False, encoding="utf-8-sig")

    total = int(len(merged))
    matched = int((merged["alignment_status"] == "MATCH").sum())
    mismatched = int((merged["alignment_status"] == "MISMATCH").sum())
    match_rate = round((matched / total) * 100, 2) if total else 0

    likely_causes = []

    if mismatched:
        likely_causes.append(
            "The simulator approximates Stage 1 but may not replicate every internal condition from src/filter_stage1.py."
        )
        likely_causes.append(
            "Most important differences should be inspected in stage1_simulator_alignment_mismatches.csv."
        )
        likely_causes.append(
            "If mismatches are mostly PASSED vs WATCHLIST, hard rejection thresholds may already match while watchlist-band logic differs."
        )
    else:
        likely_causes.append(
            "The simulator is aligned with real Stage 1 for current_base on this batch."
        )

    report = {
        "phase": "7B.2",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "total_companies_compared": total,
        "matched": matched,
        "mismatched": mismatched,
        "match_rate_percent": match_rate,
        "real_counts": {str(k): int(v) for k, v in real_counts.items()},
        "simulated_current_base_counts": {str(k): int(v) for k, v in sim_counts.items()},
        "mismatch_summary": mismatch_summary.to_dict(orient="records"),
        "likely_causes": likely_causes,
        "outputs": {
            "report_json": str(REPORT_JSON),
            "report_md": str(REPORT_MD),
            "mismatches_csv": str(MISMATCHES_CSV),
            "mismatch_summary_csv": str(MISMATCH_SUMMARY_CSV),
        },
        "recommendation": (
            "Do not apply Stage 1 threshold changes until current_base simulation matches real Stage 1 "
            "or until documented differences are intentionally accepted."
        ),
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


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Scout Finance — Phase 7B.2 Stage 1 Simulator Alignment",
        "",
        f"Generated at: `{report.get('created_at')}`",
        "",
        "## Executive summary",
        "",
        f"- Companies compared: **{report.get('total_companies_compared')}**.",
        f"- Matched: **{report.get('matched')}**.",
        f"- Mismatched: **{report.get('mismatched')}**.",
        f"- Match rate: **{report.get('match_rate_percent')}%**.",
        "",
        "## Real vs simulated counts",
        "",
        "### Real Stage 1",
        "",
    ]

    for key, value in report.get("real_counts", {}).items():
        lines.append(f"- {key}: **{value}**")

    lines.extend(["", "### Simulated current_base", ""])

    for key, value in report.get("simulated_current_base_counts", {}).items():
        lines.append(f"- {key}: **{value}**")

    lines.extend(
        [
            "",
            "## Mismatch summary",
            "",
            "| Real decision | Simulated decision | Count |",
            "|---|---|---:|",
        ]
    )

    for row in report.get("mismatch_summary", []):
        lines.append(
            f"| {row.get('real_decision')} | {row.get('simulated_decision')} | {row.get('count')} |"
        )

    lines.extend(["", "## Likely causes", ""])

    for note in report.get("likely_causes", []):
        lines.append(f"- {note}")

    lines.extend(
        [
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


def print_summary(report: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7B.2 Stage 1 simulator alignment")
    print("=" * 78)
    print(f"Status: {report.get('status')}")
    print(f"Compared: {report.get('total_companies_compared')}")
    print(f"Matched: {report.get('matched')}")
    print(f"Mismatched: {report.get('mismatched')}")
    print(f"Match rate: {report.get('match_rate_percent')}%")
    print()
    print("Real counts")
    print("-" * 78)
    for key, value in report.get("real_counts", {}).items():
        print(f"{key}: {value}")
    print()
    print("Simulated current_base counts")
    print("-" * 78)
    for key, value in report.get("simulated_current_base_counts", {}).items():
        print(f"{key}: {value}")
    print()
    print("Mismatch summary")
    print("-" * 78)
    for row in report.get("mismatch_summary", []):
        print(f"{row.get('real_decision')} -> {row.get('simulated_decision')}: {row.get('count')}")
    print()
    print("Output files")
    print("-" * 78)
    for label, path in report.get("outputs", {}).items():
        print(f"- {label}: {path}")


def main() -> int:
    report = build_stage1_simulator_alignment_report()
    print_summary(report)
    return 0 if report.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
