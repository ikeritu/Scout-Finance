#!/usr/bin/env python3
"""Build deterministic v2.38X Europe fundamental features (ratios only)
from the real v2.38W iXBRL extraction. No network, no scoring, no ranking.

Unlike the US SEC features (v2.38G), no growth features are computed here:
v2.38W's extractor deliberately keeps only the single most recent
reporting period per concept (see its own docstring), so there is no
second year on file to compare against yet. Every feature below is a
same-period ratio, computable from one balance sheet / income statement.
Growth features stay explicitly out of scope until a phase re-runs the
extractor against a prior-year filing too.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38x_europe_candidate_feature_matrix"
PHASE = "v2.38X-europe-fundamental-features"
RECORDS_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38w_europe_ixbrl_fundamentals/europe_ixbrl_fundamental_records_v2_38w.jsonl"

FEATURE_FIELDS = [
    "asset_id", "ticker", "company_name", "company_number", "feature_period_end",
    "feature_quality_status", "features_calculated", "features_missing", "quality_flags",
    "net_margin", "operating_margin", "pretax_margin", "return_on_assets", "return_on_equity",
    "liabilities_to_assets", "equity_to_assets", "cash_to_assets", "current_ratio",
    "profitability_positive_flag", "balance_strength_flag", "phase",
]
QUALITY_FIELDS = ["asset_id", "ticker", "company_name", "company_number", "features_calculated", "features_missing", "feature_quality_status", "quality_flags"]
REJECTION_FIELDS = ["asset_id", "ticker", "company_number", "feature", "reason", "phase"]
FEATURES = ["net_margin", "operating_margin", "pretax_margin", "return_on_assets", "return_on_equity", "liabilities_to_assets", "equity_to_assets", "cash_to_assets", "current_ratio"]
RATIO_RULES = {
    "net_margin": ("ifrs-full:ProfitLoss", "ifrs-full:Revenue"),
    "operating_margin": ("ifrs-full:ProfitLossFromOperatingActivities", "ifrs-full:Revenue"),
    "pretax_margin": ("ifrs-full:ProfitLossBeforeTax", "ifrs-full:Revenue"),
    "return_on_assets": ("ifrs-full:ProfitLoss", "ifrs-full:Assets"),
    "return_on_equity": ("ifrs-full:ProfitLoss", "ifrs-full:Equity"),
    "liabilities_to_assets": ("ifrs-full:Liabilities", "ifrs-full:Assets"),
    "equity_to_assets": ("ifrs-full:Equity", "ifrs-full:Assets"),
    "cash_to_assets": ("ifrs-full:CashAndCashEquivalents", "ifrs-full:Assets"),
    "current_ratio": ("ifrs-full:CurrentAssets", "ifrs-full:CurrentLiabilities"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def rounded(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, 6)


def ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0:
        return None
    return rounded(num / den)


def build_company(company_records: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    base = company_records[0]
    by_concept = {r["concept"]: r["value"] for r in company_records if r["value"] is not None}
    period_ends = {r["period_end"] for r in company_records if r.get("period_end")}
    row: dict[str, Any] = {field: None for field in FEATURE_FIELDS}
    row.update({
        "asset_id": base["asset_id"], "ticker": base["ticker"], "company_name": base["company_name"],
        "company_number": base["company_number"], "feature_period_end": max(period_ends) if period_ends else "",
        "phase": PHASE,
    })
    rejections: list[dict[str, str]] = []
    missing: list[str] = []
    flags: set[str] = set()
    for feature, (num_concept, den_concept) in RATIO_RULES.items():
        value = ratio(by_concept.get(num_concept), by_concept.get(den_concept))
        row[feature] = value
        if value is None:
            missing.append(feature)
            reason = "missing_numerator" if num_concept not in by_concept else ("missing_or_zero_denominator" if den_concept not in by_concept else "unknown")
            rejections.append({"asset_id": base["asset_id"], "ticker": base["ticker"], "company_number": base["company_number"], "feature": feature, "reason": reason, "phase": PHASE})
    if row["net_margin"] is not None and row["net_margin"] > 0:
        flags.add("net_margin_positive")
    if row["liabilities_to_assets"] is not None and row["equity_to_assets"] is not None and row["liabilities_to_assets"] < 0.75 and row["equity_to_assets"] > 0.25:
        flags.add("balance_strength_flag")
    row["profitability_positive_flag"] = bool(row["net_margin"] is not None and row["net_margin"] > 0)
    row["balance_strength_flag"] = "balance_strength_flag" in flags
    calculated = [f for f in FEATURES if row.get(f) is not None]
    row["features_calculated"] = len(calculated)
    row["features_missing"] = "|".join(sorted(missing))
    row["quality_flags"] = "|".join(sorted(flags))
    if len(calculated) == len(FEATURES):
        row["feature_quality_status"] = "FEATURES_READY"
    elif calculated:
        row["feature_quality_status"] = "FEATURES_PARTIAL"
    else:
        row["feature_quality_status"] = "INSUFFICIENT_FEATURE_EVIDENCE"
    return row, rejections


def build(records_path: Path, output_dir: Path) -> dict[str, Any]:
    records = read_jsonl(records_path)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["asset_id"])].append(record)

    feature_rows = []
    rejection_rows: list[dict[str, str]] = []
    for asset_id in sorted(grouped):
        row, rejections = build_company(grouped[asset_id])
        feature_rows.append(row)
        rejection_rows.extend(rejections)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_fundamental_features_v2_38x.csv", feature_rows, FEATURE_FIELDS)
    write_csv(output_dir / "europe_fundamental_feature_quality_v2_38x.csv", feature_rows, QUALITY_FIELDS)
    write_csv(output_dir / "europe_fundamental_feature_rejections_v2_38x.csv", rejection_rows, REJECTION_FIELDS)

    quality_counts = {status: sum(1 for r in feature_rows if r["feature_quality_status"] == status) for status in {"FEATURES_READY", "FEATURES_PARTIAL", "INSUFFICIENT_FEATURE_EVIDENCE"}}
    report = {
        "phase": PHASE, "companies_input": len(grouped), "companies_features_ready": quality_counts["FEATURES_READY"],
        "companies_features_partial": quality_counts["FEATURES_PARTIAL"], "companies_insufficient": quality_counts["INSUFFICIENT_FEATURE_EVIDENCE"],
        "rejected_rows": len(rejection_rows), "network_used": False, "scoring_created": False, "ranking_created": False,
        "recommendations_created": False, "phase9c_authorized": False,
        "note": "Growth features are out of scope: v2.38W extracts only the single most recent reporting period per concept, so no prior-year comparison exists yet.",
    }
    write_text(output_dir / "europe_fundamental_features_report_v2_38x.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report, feature_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records-input", type=Path, default=RECORDS_INPUT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report, _ = build(args.records_input, args.output_dir)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
