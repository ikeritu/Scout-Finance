
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOUTING_OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "scouting"

SUMMARY = SCOUTING_OUTPUTS_DIR / "clean_500_stability_summary.json"
METRICS = SCOUTING_OUTPUTS_DIR / "clean_500_stability_metrics.csv"
REJECTIONS = SCOUTING_OUTPUTS_DIR / "clean_500_stage1_rejection_distribution.csv"
REPORT_MD = SCOUTING_OUTPUTS_DIR / "clean_500_stability_report.md"
ENRICHED = PROJECT_ROOT / "data" / "raw" / "universe_source_real_clean_market_enriched_500.csv"


def ok(message: str) -> None:
    print(f"OK   {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 7A.6 clean 500 stability checker")
    print("=" * 76)

    for path in [SUMMARY, METRICS, REJECTIONS, REPORT_MD, ENRICHED]:
        if not path.exists():
            fail(f"Missing output: {path}")
            return 1
        ok(f"Output exists: {path}")

    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read summary JSON: {exc}")
        return 1

    if summary.get("phase") != "7A.6":
        fail(f"Summary phase is not 7A.6: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7A.6")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("openai_called") is False:
        ok("OpenAI was not called")
    else:
        fail("Summary indicates OpenAI was called")
        return 1

    if summary.get("paid_api_called") is False:
        ok("Paid API was not called")
    else:
        fail("Summary indicates paid API was called")
        return 1

    if summary.get("yfinance_called") is True:
        ok("yfinance call acknowledged for free market-data enrichment")
    else:
        warn("Summary does not acknowledge yfinance call")

    if summary.get("app_modified") is False:
        ok("app.py was not modified")
    else:
        fail("Summary indicates app.py was modified")
        return 1

    if summary.get("release_v0_6_modified") is False:
        ok("release v0.6 was not modified")
    else:
        fail("Summary indicates release v0.6 was modified")
        return 1

    enriched_df = pd.read_csv(ENRICHED)
    if len(enriched_df) != summary.get("market_data_processed_rows"):
        warn("Enriched CSV row count differs from market_data_processed_rows")
    else:
        ok("Enriched CSV row count matches summary")

    stage1_total = (
        int(summary.get("stage1_passed") or 0)
        + int(summary.get("stage1_watchlist") or 0)
        + int(summary.get("stage1_rejected") or 0)
    )

    if stage1_total != int(summary.get("stage1_input") or 0):
        fail("Stage 1 passed/watchlist/rejected does not sum to input")
        return 1
    ok("Stage 1 counts are consistent")

    print()
    print("Summary")
    print("-" * 76)
    print(f"Market-data success rate: {summary.get('market_data_success_rate_percent')}%")
    print(f"Stage 1 pass/watchlist/reject: {summary.get('stage1_passed')} / {summary.get('stage1_watchlist')} / {summary.get('stage1_rejected')}")
    print(f"Stage 1 rates: {summary.get('stage1_pass_rate_percent')}% / {summary.get('stage1_watchlist_rate_percent')}% / {summary.get('stage1_rejection_rate_percent')}%")
    print(f"Companies ready for Stage 2: {summary.get('companies_ready_for_stage2')}")
    print(f"Companies not ready for Stage 2: {summary.get('companies_not_ready_for_stage2')}")

    print()
    print("Result")
    print("-" * 76)
    ok("Phase 7A.6 clean 500 stability is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
