
"""
Scout Finance — Phase 7B Stage 1 professional diagnostic.

Purpose:
- Diagnose Stage 1 behavior after the clean 500 stability pilot.
- Review passed/watchlist/rejected companies.
- Analyze market cap, price, liquidity and rejection reasons.
- Produce JSON, CSV and Markdown diagnostic reports.
- Do not modify filters yet.

This module:
- does not call OpenAI;
- does not call APIs;
- does not call yfinance;
- does not modify app.py;
- does not modify releases/v0.6.

Run:
    ./.venv/Scripts/python.exe -m src.diagnose_stage1_professional
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

CLEAN_500_SUMMARY = SCOUTING_OUTPUTS_DIR / "clean_500_stability_summary.json"

REPORT_JSON = SCOUTING_OUTPUTS_DIR / "stage1_professional_diagnostic_report.json"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "stage1_professional_diagnostic_report.md"
REJECTION_REASONS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_professional_rejection_reasons.csv"
BUCKETS_CSV = SCOUTING_OUTPUTS_DIR / "stage1_professional_bucket_summary.csv"
WATCHLIST_REVIEW_CSV = SCOUTING_OUTPUTS_DIR / "stage1_professional_watchlist_review.csv"
PASSED_SAMPLE_CSV = SCOUTING_OUTPUTS_DIR / "stage1_professional_passed_sample.csv"


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


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    if df.empty or column not in df.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(df[column], errors="coerce")


def _describe_numeric(df: pd.DataFrame, column: str) -> dict[str, Any]:
    s = _numeric(df, column).dropna()

    if s.empty:
        return {
            "count": 0,
            "min": None,
            "p25": None,
            "median": None,
            "p75": None,
            "max": None,
            "mean": None,
        }

    return {
        "count": int(s.count()),
        "min": round(float(s.min()), 4),
        "p25": round(float(s.quantile(0.25)), 4),
        "median": round(float(s.median()), 4),
        "p75": round(float(s.quantile(0.75)), 4),
        "max": round(float(s.max()), 4),
        "mean": round(float(s.mean()), 4),
    }


def _bucket_market_cap(value: float | int | None) -> str:
    try:
        v = float(value)
    except Exception:
        return "missing"

    if pd.isna(v):
        return "missing"
    if v < 100_000_000:
        return "<100M"
    if v < 300_000_000:
        return "100M-300M"
    if v < 1_000_000_000:
        return "300M-1B"
    if v < 10_000_000_000:
        return "1B-10B"
    if v < 50_000_000_000:
        return "10B-50B"
    return ">50B"


def _bucket_price(value: float | int | None) -> str:
    try:
        v = float(value)
    except Exception:
        return "missing"

    if pd.isna(v):
        return "missing"
    if v < 1:
        return "<1"
    if v < 2:
        return "1-2"
    if v < 5:
        return "2-5"
    if v < 20:
        return "5-20"
    if v < 100:
        return "20-100"
    return ">100"


def _bucket_dollar_volume(value: float | int | None) -> str:
    try:
        v = float(value)
    except Exception:
        return "missing"

    if pd.isna(v):
        return "missing"
    if v < 500_000:
        return "<500K"
    if v < 1_000_000:
        return "500K-1M"
    if v < 5_000_000:
        return "1M-5M"
    if v < 20_000_000:
        return "5M-20M"
    if v < 100_000_000:
        return "20M-100M"
    return ">100M"


def _with_decision(df: pd.DataFrame, decision: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy()
    out["stage1_decision"] = decision
    return out


def _make_combined(passed: pd.DataFrame, watchlist: pd.DataFrame, rejected: pd.DataFrame) -> pd.DataFrame:
    parts = [
        _with_decision(passed, "PASSED"),
        _with_decision(watchlist, "WATCHLIST"),
        _with_decision(rejected, "REJECTED"),
    ]

    parts = [p for p in parts if not p.empty]

    if not parts:
        return pd.DataFrame()

    combined = pd.concat(parts, ignore_index=True)

    for col in ["market_cap", "price", "dollar_volume_90d"]:
        if col in combined.columns:
            combined[col] = pd.to_numeric(combined[col], errors="coerce")

    if "market_cap" in combined.columns:
        combined["market_cap_bucket"] = combined["market_cap"].apply(_bucket_market_cap)
    else:
        combined["market_cap_bucket"] = "missing"

    if "price" in combined.columns:
        combined["price_bucket"] = combined["price"].apply(_bucket_price)
    else:
        combined["price_bucket"] = "missing"

    if "dollar_volume_90d" in combined.columns:
        combined["dollar_volume_bucket"] = combined["dollar_volume_90d"].apply(_bucket_dollar_volume)
    else:
        combined["dollar_volume_bucket"] = "missing"

    return combined


def _decision_distribution(df: pd.DataFrame, bucket_column: str) -> list[dict[str, Any]]:
    if df.empty or bucket_column not in df.columns or "stage1_decision" not in df.columns:
        return []

    pivot = (
        df.groupby([bucket_column, "stage1_decision"])
        .size()
        .reset_index(name="count")
        .sort_values([bucket_column, "stage1_decision"])
    )

    return pivot.to_dict(orient="records")


def _rejection_reason_distribution(rejection_log: pd.DataFrame) -> list[dict[str, Any]]:
    if rejection_log.empty or "reason_code" not in rejection_log.columns:
        return []

    grouped = rejection_log.groupby("reason_code").size().reset_index(name="count")
    grouped = grouped.sort_values("count", ascending=False)
    return grouped.to_dict(orient="records")


def _watchlist_review(watchlist: pd.DataFrame, rejection_log: pd.DataFrame) -> pd.DataFrame:
    if watchlist.empty:
        return pd.DataFrame(columns=["ticker", "name", "market_cap", "price", "dollar_volume_90d", "watchlist_reasons"])

    out = watchlist.copy()

    if not rejection_log.empty and "ticker" in rejection_log.columns and "reason_code" in rejection_log.columns:
        reasons = (
            rejection_log.groupby("ticker")["reason_code"]
            .apply(lambda x: ", ".join(sorted(set(str(v) for v in x if pd.notna(v)))))
            .reset_index(name="watchlist_reasons")
        )
        out = out.merge(reasons, on="ticker", how="left")
    else:
        out["watchlist_reasons"] = ""

    selected = [c for c in ["ticker", "name", "market_cap", "price", "avg_volume_90d", "dollar_volume_90d", "watchlist_reasons"] if c in out.columns]
    return out[selected].copy()


def _interpretation(summary: dict[str, Any]) -> list[str]:
    notes = []

    pass_rate = summary.get("stage1_pass_rate_percent", 0)
    watch_rate = summary.get("stage1_watchlist_rate_percent", 0)
    reject_rate = summary.get("stage1_rejection_rate_percent", 0)

    if 30 <= pass_rate <= 60:
        notes.append("Stage 1 pass rate is within a reasonable diagnostic range for a first investability layer.")
    elif pass_rate > 60:
        notes.append("Stage 1 may be too permissive; too many companies pass the first investability layer.")
    else:
        notes.append("Stage 1 may be too restrictive; too few companies pass the first investability layer.")

    if watch_rate > 20:
        notes.append("Watchlist rate is high; consider tightening or clarifying watchlist bands.")
    elif watch_rate < 5:
        notes.append("Watchlist rate is low; watchlist bands may be narrow or Stage 1 is making hard decisions.")
    else:
        notes.append("Watchlist rate looks usable as an intermediate review bucket.")

    if reject_rate > 60:
        notes.append("Rejection rate is high; review whether thresholds exclude too many small or illiquid names.")
    else:
        notes.append("Rejection rate appears compatible with a broad first-pass filter.")

    notes.append("Stage 1 remains a market/liquidity filter; Stage 2 still needs real fundamentals before professional opportunity ranking.")
    notes.append("No threshold changes are applied in this phase; this is a diagnostic report only.")

    return notes


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Scout Finance — Phase 7B Stage 1 Professional Diagnostic",
        "",
        f"Generated at: `{report.get('created_at')}`",
        "",
        "## Executive summary",
        "",
        f"- Stage 1 input: **{report.get('stage1_input')}** companies.",
        f"- Passed: **{report.get('stage1_passed')}** ({report.get('stage1_pass_rate_percent')}%).",
        f"- Watchlist: **{report.get('stage1_watchlist')}** ({report.get('stage1_watchlist_rate_percent')}%).",
        f"- Rejected: **{report.get('stage1_rejected')}** ({report.get('stage1_rejection_rate_percent')}%).",
        "",
        "## Numeric profile",
        "",
        "### Passed",
        "",
    ]

    for metric, values in report.get("numeric_profile", {}).get("passed", {}).items():
        lines.append(f"- **{metric}**: median `{values.get('median')}`, p25 `{values.get('p25')}`, p75 `{values.get('p75')}`.")

    lines.extend(["", "### Watchlist", ""])

    for metric, values in report.get("numeric_profile", {}).get("watchlist", {}).items():
        lines.append(f"- **{metric}**: median `{values.get('median')}`, p25 `{values.get('p25')}`, p75 `{values.get('p75')}`.")

    lines.extend(["", "### Rejected", ""])

    for metric, values in report.get("numeric_profile", {}).get("rejected", {}).items():
        lines.append(f"- **{metric}**: median `{values.get('median')}`, p25 `{values.get('p25')}`, p75 `{values.get('p75')}`.")

    lines.extend(
        [
            "",
            "## Top rejection reasons",
            "",
            "| Reason code | Count |",
            "|---|---:|",
        ]
    )

    for row in report.get("rejection_reason_distribution", []):
        lines.append(f"| {row.get('reason_code')} | {row.get('count')} |")

    lines.extend(["", "## Professional interpretation", ""])

    for note in report.get("interpretation", []):
        lines.append(f"- {note}")

    lines.extend(
        [
            "",
            "## Controls",
            "",
            f"- OpenAI called: `{report.get('openai_called')}`",
            f"- API called: `{report.get('api_called')}`",
            f"- yfinance called: `{report.get('yfinance_called')}`",
            f"- app.py modified: `{report.get('app_modified')}`",
            f"- release v0.6 modified: `{report.get('release_v0_6_modified')}`",
            "",
        ]
    )

    return "\n".join(lines)


def build_stage1_professional_diagnostic() -> dict[str, Any]:
    SCOUTING_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    passed = _read_csv(STAGE1_PASSED)
    watchlist = _read_csv(STAGE1_WATCHLIST)
    rejected = _read_csv(STAGE1_REJECTED)
    rejection_log = _read_csv(STAGE1_REJECTION_LOG)
    clean_500 = _read_json(CLEAN_500_SUMMARY)

    combined = _make_combined(passed, watchlist, rejected)

    stage1_input = int(len(combined))
    stage1_passed = int(len(passed))
    stage1_watchlist = int(len(watchlist))
    stage1_rejected = int(len(rejected))

    def rate(v: int) -> float:
        return round((v / stage1_input) * 100, 2) if stage1_input else 0.0

    bucket_rows = []
    for bucket in ["market_cap_bucket", "price_bucket", "dollar_volume_bucket"]:
        bucket_rows.extend(
            [
                {"bucket_type": bucket, **row}
                for row in _decision_distribution(combined, bucket)
            ]
        )

    buckets_df = pd.DataFrame(bucket_rows)
    buckets_df.to_csv(BUCKETS_CSV, index=False, encoding="utf-8-sig")

    rejection_reasons = _rejection_reason_distribution(rejection_log)
    pd.DataFrame(rejection_reasons).to_csv(REJECTION_REASONS_CSV, index=False, encoding="utf-8-sig")

    watchlist_review = _watchlist_review(watchlist, rejection_log)
    watchlist_review.to_csv(WATCHLIST_REVIEW_CSV, index=False, encoding="utf-8-sig")

    passed_sample = passed.head(50).copy()
    passed_sample.to_csv(PASSED_SAMPLE_CSV, index=False, encoding="utf-8-sig")

    report = {
        "phase": "7B",
        "status": "OK",
        "created_at": _utc_now_iso(),
        "source_summary": str(CLEAN_500_SUMMARY),
        "stage1_input": stage1_input,
        "stage1_passed": stage1_passed,
        "stage1_watchlist": stage1_watchlist,
        "stage1_rejected": stage1_rejected,
        "stage1_pass_rate_percent": rate(stage1_passed),
        "stage1_watchlist_rate_percent": rate(stage1_watchlist),
        "stage1_rejection_rate_percent": rate(stage1_rejected),
        "clean_500_market_data_success_rate_percent": clean_500.get("market_data_success_rate_percent"),
        "numeric_profile": {
            "passed": {
                "market_cap": _describe_numeric(passed, "market_cap"),
                "price": _describe_numeric(passed, "price"),
                "dollar_volume_90d": _describe_numeric(passed, "dollar_volume_90d"),
            },
            "watchlist": {
                "market_cap": _describe_numeric(watchlist, "market_cap"),
                "price": _describe_numeric(watchlist, "price"),
                "dollar_volume_90d": _describe_numeric(watchlist, "dollar_volume_90d"),
            },
            "rejected": {
                "market_cap": _describe_numeric(rejected, "market_cap"),
                "price": _describe_numeric(rejected, "price"),
                "dollar_volume_90d": _describe_numeric(rejected, "dollar_volume_90d"),
            },
        },
        "rejection_reason_distribution": rejection_reasons,
        "bucket_summary_csv": str(BUCKETS_CSV),
        "rejection_reasons_csv": str(REJECTION_REASONS_CSV),
        "watchlist_review_csv": str(WATCHLIST_REVIEW_CSV),
        "passed_sample_csv": str(PASSED_SAMPLE_CSV),
        "report_json": str(REPORT_JSON),
        "report_md": str(REPORT_MD),
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "release_v0_6_modified": False,
    }

    report["interpretation"] = _interpretation(report)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_MD.write_text(_render_markdown(report), encoding="utf-8")

    return report


def print_summary(report: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7B Stage 1 professional diagnostic")
    print("=" * 78)
    print(f"Status: {report.get('status')}")
    print(f"Stage 1 input: {report.get('stage1_input')}")
    print(
        "Passed / Watchlist / Rejected: "
        f"{report.get('stage1_passed')} / {report.get('stage1_watchlist')} / {report.get('stage1_rejected')}"
    )
    print(
        "Rates: "
        f"{report.get('stage1_pass_rate_percent')}% / "
        f"{report.get('stage1_watchlist_rate_percent')}% / "
        f"{report.get('stage1_rejection_rate_percent')}%"
    )

    print()
    print("Top rejection reasons")
    print("-" * 78)

    for row in report.get("rejection_reason_distribution", [])[:10]:
        print(f"{row.get('reason_code')}: {row.get('count')}")

    print()
    print("Output files")
    print("-" * 78)
    print(f"- report_json: {report.get('report_json')}")
    print(f"- report_md: {report.get('report_md')}")
    print(f"- bucket_summary_csv: {report.get('bucket_summary_csv')}")
    print(f"- rejection_reasons_csv: {report.get('rejection_reasons_csv')}")
    print(f"- watchlist_review_csv: {report.get('watchlist_review_csv')}")
    print(f"- passed_sample_csv: {report.get('passed_sample_csv')}")


def main() -> int:
    report = build_stage1_professional_diagnostic()
    print_summary(report)
    return 0 if report.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
