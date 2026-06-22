
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = ROOT / "data" / "stages" / "stage1_passed_enriched.csv"
CURRENT_STAGE2_SUMMARY = ROOT / "outputs" / "scouting" / "stage2_summary.json"
CURRENT_STAGE2_LOG = ROOT / "data" / "stages" / "stage2_rejection_log.csv"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_summary.json"
REPORT_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_report.md"
RESULTS_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_results.csv"
REASONS_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_reasons.csv"
TRANSITIONS_PATH = OUT_DIR / "stage2_yfinance_policy_dryrun_transition_summary.csv"

EXPECTED_INPUT = 182

OLD_BLOCKING_REASON = "MISSING_SHARES_DILUTION"
NEW_PROVIDER_REASON = "MISSING_SHARES_DILUTION_PROVIDER_LIMITATION"

# Keep the existing Stage 2 meaning of these reasons.
HARD_REJECT_CODES = {
    "MISSING_DATA_COMPLETENESS",
    "LOW_DATA_COMPLETENESS",
    "MISSING_REVENUE",
    "OPERATING_MARGIN_TOO_NEGATIVE",
    "FCF_MARGIN_TOO_NEGATIVE",
    "DEBT_TOO_HIGH",
    "HIGH_DILUTION",
}

NON_BLOCKING_WARNING_CODES = {
    NEW_PROVIDER_REASON,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_stage2_statuses() -> dict[str, str]:
    status_map: dict[str, str] = {}
    for filename, status in [
        ("stage2_passed.csv", "PASSED"),
        ("stage2_watchlist.csv", "WATCHLIST"),
        ("stage2_rejected.csv", "REJECTED"),
    ]:
        path = ROOT / "data" / "stages" / filename
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "ticker" not in df.columns:
            continue
        for ticker in df["ticker"].astype(str).str.upper().str.strip():
            if ticker:
                status_map[ticker] = status
    return status_map


def read_reasons_by_ticker() -> dict[str, list[dict[str, Any]]]:
    reasons: dict[str, list[dict[str, Any]]] = defaultdict(list)

    if not CURRENT_STAGE2_LOG.exists():
        return reasons

    log = pd.read_csv(CURRENT_STAGE2_LOG)
    if "ticker" not in log.columns or "reason_code" not in log.columns:
        return reasons

    for _, row in log.iterrows():
        ticker = str(row.get("ticker") or "").upper().strip()
        if not ticker:
            continue
        reasons[ticker].append({
            "reason_code": row.get("reason_code"),
            "reason_text": row.get("reason_text"),
            "metric_name": row.get("metric_name"),
            "metric_value": row.get("metric_value"),
            "threshold": row.get("threshold"),
            "severity": row.get("severity"),
            "recoverable": row.get("recoverable"),
        })

    return reasons


def adjust_reasons_for_yfinance(reasons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    adjusted = []

    had_missing_dilution = False
    for reason in reasons:
        if reason.get("reason_code") == OLD_BLOCKING_REASON:
            had_missing_dilution = True
            continue
        adjusted.append(dict(reason))

    if had_missing_dilution:
        adjusted.append({
            "reason_code": NEW_PROVIDER_REASON,
            "reason_text": "Shares dilution 3Y is unavailable from yfinance; tracked as provider limitation, not as a clean-pass blocker.",
            "metric_name": "shares_dilution_3y",
            "metric_value": None,
            "threshold": "provider limitation",
            "severity": "low",
            "recoverable": True,
        })

    return adjusted


def classify_from_adjusted_reasons(adjusted_reasons: list[dict[str, Any]]) -> str:
    if any(reason.get("reason_code") in HARD_REJECT_CODES for reason in adjusted_reasons):
        return "REJECTED"

    blocking_reasons = [
        reason for reason in adjusted_reasons
        if reason.get("reason_code") not in NON_BLOCKING_WARNING_CODES
    ]

    if blocking_reasons:
        return "WATCHLIST"

    return "PASSED"


def primary_reason(reasons: list[dict[str, Any]]) -> str:
    for reason in reasons:
        code = reason.get("reason_code")
        if code and code not in NON_BLOCKING_WARNING_CODES:
            return str(code)
    return str(reasons[0].get("reason_code") if reasons else "")


def all_reasons(reasons: list[dict[str, Any]]) -> str:
    return "|".join(str(reason.get("reason_code") or "") for reason in reasons)


def render_report(summary: dict[str, Any]) -> str:
    actual = summary["current_stage2_counts"]
    simulated = summary["simulated_counts"]

    top_reasons = "\n".join(
        f"- {item['reason_code']}: {item['count']}"
        for item in summary["top_simulated_reasons"][:20]
    )

    transitions = "\n".join(
        f"- {item['transition']}: {item['count']}"
        for item in summary["transition_summary"][:20]
    )

    return f"""# Scout Finance — Phase 7C.2 v2 Stage 2 yfinance policy dry-run

Generated at: `{summary["created_at"]}`

## Purpose

Dry-run a Stage 2 policy aligned with yfinance limitations without calling internal `filter_stage2.py` functions.

The only simulated policy change is:

```text
MISSING_SHARES_DILUTION -> MISSING_SHARES_DILUTION_PROVIDER_LIMITATION
```

Missing 3Y dilution from yfinance is tracked as a provider limitation but does not block a clean pass by itself.

## Current Stage 2

| Bucket | Count |
|---|---:|
| Passed | {actual["passed"]} |
| Watchlist | {actual["watchlist"]} |
| Rejected | {actual["rejected"]} |

## Simulated yfinance-aligned Stage 2

| Bucket | Count |
|---|---:|
| Passed | {simulated["passed"]} |
| Watchlist | {simulated["watchlist"]} |
| Rejected | {simulated["rejected"]} |

## Main simulated reasons

{top_reasons}

## Transitions

{transitions}

## Decision

- Recommended decision: **{summary["recommended_decision"]}**
- Recommended next phase: **{summary["recommended_next_phase"]}**

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- app.py modified: `{summary["app_modified"]}`
- filter_stage2.py modified: `{summary["filter_stage2_modified"]}`
- release modified: `{summary["release_modified"]}`
"""


def main() -> int:
    print("Scout Finance — Phase 7C.2 v2 Stage 2 yfinance policy dry-run")
    print("=" * 82)

    if not INPUT_PATH.exists():
        print(f"FAIL Missing input file: {INPUT_PATH}")
        return 1
    if not CURRENT_STAGE2_LOG.exists():
        print(f"FAIL Missing Stage 2 rejection log: {CURRENT_STAGE2_LOG}")
        return 1

    input_df = pd.read_csv(INPUT_PATH)

    if "ticker" not in input_df.columns:
        print("FAIL Input file has no ticker column")
        return 1

    print(f"Input companies: {len(input_df)}")
    if len(input_df) != EXPECTED_INPUT:
        print(f"WARN Expected {EXPECTED_INPUT} rows, got {len(input_df)}")

    current_map = read_stage2_statuses()
    reasons_by_ticker = read_reasons_by_ticker()
    current_summary = load_json(CURRENT_STAGE2_SUMMARY)

    result_rows = []
    reason_rows = []
    transition_counter = Counter()
    old_missing_dilution_count = 0
    provider_warning_count = 0

    for _, row in input_df.iterrows():
        ticker = str(row.get("ticker") or "").upper().strip()
        current_status = current_map.get(ticker, "UNKNOWN")
        original_reasons = reasons_by_ticker.get(ticker, [])

        old_missing_dilution_count += sum(
            1 for r in original_reasons if r.get("reason_code") == OLD_BLOCKING_REASON
        )

        adjusted_reasons = adjust_reasons_for_yfinance(original_reasons)
        provider_warning_count += sum(
            1 for r in adjusted_reasons if r.get("reason_code") == NEW_PROVIDER_REASON
        )

        simulated_status = classify_from_adjusted_reasons(adjusted_reasons)
        transition = f"{current_status}->{simulated_status}"
        transition_counter[transition] += 1

        result_rows.append({
            "ticker": ticker,
            "current_stage2_status": current_status,
            "simulated_stage2_status": simulated_status,
            "transition": transition,
            "simulated_primary_reason": primary_reason(adjusted_reasons),
            "simulated_all_reasons": all_reasons(adjusted_reasons),
        })

        for reason in adjusted_reasons:
            reason_rows.append({
                "ticker": ticker,
                "simulated_stage2_status": simulated_status,
                "reason_code": reason.get("reason_code"),
                "reason_text": reason.get("reason_text"),
                "metric_name": reason.get("metric_name"),
                "metric_value": reason.get("metric_value"),
                "threshold": reason.get("threshold"),
                "severity": reason.get("severity"),
                "recoverable": reason.get("recoverable"),
            })

    result_df = pd.DataFrame(result_rows)
    reasons_df = pd.DataFrame(reason_rows)

    simulated_counts = {
        "passed": int((result_df["simulated_stage2_status"] == "PASSED").sum()),
        "watchlist": int((result_df["simulated_stage2_status"] == "WATCHLIST").sum()),
        "rejected": int((result_df["simulated_stage2_status"] == "REJECTED").sum()),
    }

    current_counts = {
        "passed": int(current_summary.get("passed_companies", 0)),
        "watchlist": int(current_summary.get("watchlist_companies", 0)),
        "rejected": int(current_summary.get("rejected_companies", 0)),
    }

    top_reasons = (
        reasons_df["reason_code"].value_counts().head(30).reset_index()
        if not reasons_df.empty
        else pd.DataFrame(columns=["reason_code", "count"])
    )
    if not top_reasons.empty:
        top_reasons.columns = ["reason_code", "count"]

    transitions_df = pd.DataFrame(
        [{"transition": key, "count": value} for key, value in transition_counter.items()]
    ).sort_values("count", ascending=False)

    passed = simulated_counts["passed"]
    rejected = simulated_counts["rejected"]

    if 30 <= passed <= 110 and 15 <= rejected <= 80:
        decision = "APPROVE_FOR_GUARDED_IMPLEMENTATION"
        next_phase = "7C.3 — Guarded Stage 2 yfinance policy implementation"
    elif passed == 0:
        decision = "REJECT_POLICY_STILL_TOO_STRICT"
        next_phase = "7C.2b — Continue Stage 2 policy diagnosis"
    elif passed > 130:
        decision = "REJECT_POLICY_TOO_LOOSE"
        next_phase = "7C.2b — Tighten Stage 2 yfinance policy"
    else:
        decision = "REVIEW_MANUALLY"
        next_phase = "7C.2b — Inspect transition details before patch"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(RESULTS_PATH, index=False, encoding="utf-8-sig")
    reasons_df.to_csv(REASONS_PATH, index=False, encoding="utf-8-sig")
    transitions_df.to_csv(TRANSITIONS_PATH, index=False, encoding="utf-8-sig")

    summary = {
        "phase": "7C.2",
        "version": "v2",
        "status": "OK",
        "created_at": utc_now(),
        "input_file": str(INPUT_PATH),
        "input_companies": int(len(input_df)),
        "current_stage2_counts": current_counts,
        "simulated_counts": simulated_counts,
        "passed_delta": simulated_counts["passed"] - current_counts["passed"],
        "watchlist_delta": simulated_counts["watchlist"] - current_counts["watchlist"],
        "rejected_delta": simulated_counts["rejected"] - current_counts["rejected"],
        "old_missing_shares_dilution_count": int(old_missing_dilution_count),
        "provider_limitation_warning_count": int(provider_warning_count),
        "top_simulated_reasons": top_reasons.to_dict(orient="records"),
        "transition_summary": transitions_df.to_dict(orient="records"),
        "recommended_decision": decision,
        "recommended_next_phase": next_phase,
        "policy_change_simulated": {
            "old_reason": OLD_BLOCKING_REASON,
            "new_reason": NEW_PROVIDER_REASON,
            "provider_limitation_does_not_block_pass": True,
        },
        "output_files": {
            "summary_json": str(SUMMARY_PATH),
            "report_md": str(REPORT_PATH),
            "results_csv": str(RESULTS_PATH),
            "reasons_csv": str(REASONS_PATH),
            "transitions_csv": str(TRANSITIONS_PATH),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filter_stage2_modified": False,
        "release_modified": False,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Current Stage 2")
    print("-" * 82)
    print(current_counts)

    print()
    print("Simulated yfinance-aligned Stage 2")
    print("-" * 82)
    print(simulated_counts)

    print()
    print("Missing dilution handling")
    print("-" * 82)
    print(f"Old blocking MISSING_SHARES_DILUTION count: {old_missing_dilution_count}")
    print(f"New provider warning count: {provider_warning_count}")

    print()
    print("Decision")
    print("-" * 82)
    print(decision)
    print(next_phase)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
