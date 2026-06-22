
from __future__ import annotations

import importlib
import json
from collections import Counter
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_current_status_map() -> dict[str, str]:
    current = {}
    for name, status in [
        ("stage2_passed.csv", "PASSED"),
        ("stage2_watchlist.csv", "WATCHLIST"),
        ("stage2_rejected.csv", "REJECTED"),
    ]:
        path = ROOT / "data" / "stages" / name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "ticker" not in df.columns:
            continue
        for ticker in df["ticker"].astype(str).str.upper().str.strip():
            current[ticker] = status
    return current


def classify_with_yfinance_policy(row: pd.Series) -> tuple[str, list[dict[str, Any]]]:
    """
    Reuse the real Stage 2 classifier, then remove only the yfinance-provider
    dilution penalty when shares_dilution_3y is missing.

    This is intentionally a dry-run: src/filter_stage2.py is not modified.
    """
    filter_stage2 = importlib.import_module("src.filter_stage2")

    if not hasattr(filter_stage2, "_classify_company"):
        raise RuntimeError("src.filter_stage2._classify_company not found")

    status, reasons = filter_stage2._classify_company(row)
    reasons = [dict(reason) for reason in reasons]

    dilution_missing = [
        reason for reason in reasons
        if reason.get("reason_code") == "MISSING_SHARES_DILUTION"
    ]

    if not dilution_missing:
        return status, reasons

    # Replace the old blocking watchlist reason with a provider-limitation warning.
    adjusted_reasons = [
        reason for reason in reasons
        if reason.get("reason_code") != "MISSING_SHARES_DILUTION"
    ]

    adjusted_reasons.append({
        "reason_code": "MISSING_SHARES_DILUTION_PROVIDER_LIMITATION",
        "reason_text": "Shares dilution 3Y is unavailable from yfinance; tracked as provider limitation, not as a clean-pass blocker.",
        "metric_name": "shares_dilution_3y",
        "metric_value": None,
        "threshold": "provider limitation",
        "severity": "low",
        "recoverable": True,
    })

    # Recompute final status from remaining reasons.
    hard_reject_codes = {
        "MISSING_DATA_COMPLETENESS",
        "LOW_DATA_COMPLETENESS",
        "MISSING_REVENUE",
        "OPERATING_MARGIN_TOO_NEGATIVE",
        "FCF_MARGIN_TOO_NEGATIVE",
        "DEBT_TOO_HIGH",
        "HIGH_DILUTION",
    }

    hard_reject = any(reason.get("reason_code") in hard_reject_codes for reason in adjusted_reasons)

    # Missing dilution provider limitation is not a watchlist blocker.
    non_blocking_warning_codes = {"MISSING_SHARES_DILUTION_PROVIDER_LIMITATION"}
    watchlist = any(
        reason.get("reason_code") not in non_blocking_warning_codes
        for reason in adjusted_reasons
    )

    if hard_reject:
        return "REJECTED", adjusted_reasons
    if watchlist:
        return "WATCHLIST", adjusted_reasons
    return "PASSED", adjusted_reasons


def primary_reason(reasons: list[dict[str, Any]]) -> str:
    # Prefer real blocking reasons over provider limitation warning.
    for reason in reasons:
        if reason.get("reason_code") != "MISSING_SHARES_DILUTION_PROVIDER_LIMITATION":
            return str(reason.get("reason_code") or "")
    return str(reasons[0].get("reason_code") if reasons else "")


def all_reasons(reasons: list[dict[str, Any]]) -> str:
    return "|".join(str(reason.get("reason_code") or "") for reason in reasons)


def render_report(summary: dict[str, Any]) -> str:
    actual = summary["current_stage2_counts"]
    simulated = summary["simulated_counts"]

    top_reasons = "\n".join(
        f"- {item['reason_code']}: {item['count']}"
        for item in summary["top_simulated_reasons"][:15]
    )

    transitions = "\n".join(
        f"- {item['transition']}: {item['count']}"
        for item in summary["transition_summary"][:20]
    )

    return f"""# Scout Finance — Phase 7C.2 Stage 2 yfinance policy dry-run

Generated at: `{summary["created_at"]}`

## Purpose

Dry-run a Stage 2 policy aligned with yfinance limitations.

The only intended policy change is:

```text
MISSING_SHARES_DILUTION -> MISSING_SHARES_DILUTION_PROVIDER_LIMITATION
```

This means missing 3Y dilution from yfinance is tracked as a provider limitation but does not block a clean pass by itself.

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
    print("Scout Finance — Phase 7C.2 Stage 2 yfinance policy dry-run")
    print("=" * 82)

    if not INPUT_PATH.exists():
        print(f"FAIL Missing input file: {INPUT_PATH}")
        return 1

    df = pd.read_csv(INPUT_PATH)

    if "ticker" not in df.columns:
        print("FAIL Input file has no ticker column")
        return 1

    print(f"Input companies: {len(df)}")

    if len(df) != EXPECTED_INPUT:
        print(f"WARN Expected {EXPECTED_INPUT} rows, got {len(df)}")

    current_map = get_current_status_map()

    rows = []
    reason_rows = []
    transition_counter = Counter()

    for _, row in df.iterrows():
        ticker = str(row.get("ticker") or "").upper().strip()
        simulated_status, reasons = classify_with_yfinance_policy(row)
        current_status = current_map.get(ticker, "")

        transition = f"{current_status or 'UNKNOWN'}->{simulated_status}"
        transition_counter[transition] += 1

        rows.append({
            "ticker": ticker,
            "current_stage2_status": current_status,
            "simulated_stage2_status": simulated_status,
            "transition": transition,
            "simulated_primary_reason": primary_reason(reasons),
            "simulated_all_reasons": all_reasons(reasons),
        })

        for reason in reasons:
            reason_row = {
                "ticker": ticker,
                "simulated_stage2_status": simulated_status,
                "reason_code": reason.get("reason_code"),
                "reason_text": reason.get("reason_text"),
                "metric_name": reason.get("metric_name"),
                "metric_value": reason.get("metric_value"),
                "threshold": reason.get("threshold"),
                "severity": reason.get("severity"),
                "recoverable": reason.get("recoverable"),
            }
            reason_rows.append(reason_row)

    result_df = pd.DataFrame(rows)
    reasons_df = pd.DataFrame(reason_rows)

    simulated_counts = {
        "passed": int((result_df["simulated_stage2_status"] == "PASSED").sum()),
        "watchlist": int((result_df["simulated_stage2_status"] == "WATCHLIST").sum()),
        "rejected": int((result_df["simulated_stage2_status"] == "REJECTED").sum()),
    }

    current_summary = load_json(CURRENT_STAGE2_SUMMARY)
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

    # Decision bands: avoid too permissive or too strict.
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
        "status": "OK",
        "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat(),
        "input_file": str(INPUT_PATH),
        "input_companies": int(len(df)),
        "current_stage2_counts": current_counts,
        "simulated_counts": simulated_counts,
        "passed_delta": simulated_counts["passed"] - current_counts["passed"],
        "watchlist_delta": simulated_counts["watchlist"] - current_counts["watchlist"],
        "rejected_delta": simulated_counts["rejected"] - current_counts["rejected"],
        "top_simulated_reasons": top_reasons.to_dict(orient="records"),
        "transition_summary": transitions_df.to_dict(orient="records"),
        "recommended_decision": decision,
        "recommended_next_phase": next_phase,
        "policy_change_simulated": {
            "old_reason": "MISSING_SHARES_DILUTION",
            "new_reason": "MISSING_SHARES_DILUTION_PROVIDER_LIMITATION",
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
    print("Decision")
    print("-" * 82)
    print(decision)
    print(next_phase)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
