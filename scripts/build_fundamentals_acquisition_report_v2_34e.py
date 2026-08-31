#!/usr/bin/env python3
"""Block E acquisition report: reads the raw collections already produced by
the block-D adapters (no network, no credentials) and reports requested /
obtained / missing / blocked / errored counts, call counts (from each
adapter's own download_report), historical periods actually obtained, and a
rough per-metric raw-field presence count for each source. This is a
coverage report over RAW provider fields, not a run of the block-F
normalizer -- it exists to give block E's gate decision real evidence before
block F is built.

Deterministic: running this twice against the same local files produces
byte-identical JSON (sorted keys, no timestamps in the payload).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MANIFEST_PATH = ROOT / "outputs/full_universe_source_acquisition/v2_34a_fundamental_universe_audit/fundamental_universe_manifest_v2_34a.csv"
JQUANTS_RAW_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_34d_fundamentals_acquisition/jquants_fundamentals_raw_v2_34d"
TWSE_RAW_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_34d_fundamentals_acquisition/twse_mops_raw_v2_34d"

# Raw-field -> canonical metric id, used here ONLY to count presence for the
# block E coverage report. Block F owns the real normalizer; this mapping
# will be reused there rather than redefined, per config/fundamental_metrics_v1.json.
JQUANTS_FIELD_TO_METRIC = {
    "Sales": "revenue", "OP": "operating_income", "OdP": "ordinary_income", "NP": "net_income",
    "EPS": "eps_basic", "DEPS": "eps_diluted", "TA": "total_assets", "Eq": "total_equity",
    "ShEq": "total_equity", "EqAR": "equity_ratio_reported", "BPS": "book_value_per_share",
    "CFO": "operating_cash_flow", "CFI": "investing_cash_flow", "CFF": "financing_cash_flow",
    "CashEq": "cash_and_equivalents", "ROE": "roe_reported",
    "ShOutFY": "shares_outstanding", "AvgSh": "shares_outstanding",
}
JQUANTS_DIVIDEND_FIELDS = ["Div1Q", "Div2Q", "Div3Q", "DivFY", "DivAnn"]

MOPS_FIELD_TO_METRIC = {
    "營業收入": "revenue", "營業成本": "cost_of_sales", "營業毛利（毛損）淨額": "gross_profit",
    "營業利益（損失）": "operating_income", "稅前淨利（淨損）": "pretax_income",
    "本期淨利（淨損）": "net_income", "流動資產": "current_assets", "資產總計": "total_assets",
    "流動負債": "current_liabilities", "負債總計": "total_liabilities", "權益總計": "total_equity",
}


def load_manifest_counts() -> dict[str, int]:
    import csv
    with MANIFEST_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {"JPX": sum(1 for r in rows if r["exchange"] == "JPX"), "TWSE": sum(1 for r in rows if r["exchange"] == "TWSE")}


def summarize_jquants() -> dict:
    report_path = JQUANTS_RAW_DIR / "download_report_v2_34d.json"
    download_report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else None

    files = sorted(JQUANTS_RAW_DIR.glob("P*.json"))
    metric_presence = Counter()
    period_types_seen = Counter()
    fiscal_year_ranges = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        disclosures = payload["disclosures"]
        for disc in disclosures:
            period_types_seen[disc.get("CurPerType", "")] += 1
            if disc.get("CurFYSt"):
                fiscal_year_ranges.append(disc["CurFYSt"])
            for field, metric in JQUANTS_FIELD_TO_METRIC.items():
                if disc.get(field, "") not in ("", None):
                    metric_presence[metric] += 1
            if any(disc.get(f, "") not in ("", None) for f in JQUANTS_DIVIDEND_FIELDS):
                metric_presence["dividends_paid"] += 1

    return {
        "provider": "jquants_fins_summary",
        "obtained_assets": len(files),
        "download_report": download_report,
        "total_disclosures": sum(period_types_seen.values()),
        "period_type_counts": dict(sorted(period_types_seen.items())),
        "earliest_fiscal_year_start": min(fiscal_year_ranges) if fiscal_year_ranges else None,
        "latest_fiscal_year_start": max(fiscal_year_ranges) if fiscal_year_ranges else None,
        "metric_presence_disclosure_count": dict(sorted(metric_presence.items())),
    }


def summarize_twse() -> dict:
    report_path = TWSE_RAW_DIR / "download_report_v2_34d.json"
    download_report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else None

    files = sorted(TWSE_RAW_DIR.glob("P*.json"))
    metric_presence = Counter()
    fiscal_periods_seen = Counter()
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        snapshot_files = payload["snapshot_files"]
        for row in snapshot_files.get("income_statement", []) + snapshot_files.get("balance_sheet", []):
            fiscal_periods_seen[f"{row.get('年度', '')}-Q{row.get('季別', '')}"] += 1
            for field, metric in MOPS_FIELD_TO_METRIC.items():
                if row.get(field, "") not in ("", None):
                    metric_presence[metric] += 1

    return {
        "provider": "twse_mops_opendata",
        "obtained_assets": len(files),
        "download_report": download_report,
        "fiscal_periods_seen": dict(sorted(fiscal_periods_seen.items())),
        "metric_presence_row_count": dict(sorted(metric_presence.items())),
    }


def build_report() -> dict:
    expected = load_manifest_counts()
    jquants = summarize_jquants()
    twse = summarize_twse()
    return {
        "schema_version": "1.0.0",
        "block": "v2.34E",
        "expected_assets": expected,
        "sources": {"jquants_fins_summary": jquants, "twse_mops_opendata": twse},
        "gate": {
            "jpx_full_coverage": jquants["obtained_assets"] == expected["JPX"] and (jquants["download_report"] or {}).get("failed", 1) == 0,
            "twse_full_coverage": twse["obtained_assets"] == expected["TWSE"] and (twse["download_report"] or {}).get("failed", 1) == 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/full_universe_source_acquisition/v2_34e_controlled_acquisition/fundamentals_acquisition_report_v2_34e.json")
    args = parser.parse_args()

    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = args.output.with_suffix(".json.tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(args.output)
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
