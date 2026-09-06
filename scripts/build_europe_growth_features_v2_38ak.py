#!/usr/bin/env python3
"""Build deterministic v2.38AK Europe growth features (year-over-year
trend, not single-period ratios) from every real multi-year structured
fundamentals block on file. No network, no scoring, no ranking.

v2.38X already computes same-period ratios (net_margin, ROA, ROE, etc.)
from each company's single most recent reporting period. That is
structurally unable to distinguish "a healthy company" from "a company
whose fundamentals are improving" -- the user's explicit priority once
this project turned toward a genuine growth-potential shortlist. This
script fills that specific gap by reusing the same real methodology
already validated for the US side (v2.38G's `yoy()` + growth/flag
logic), adapted from v2.38G's fy-integer period keys to this dataset's
ISO `period_end` date-string keys (Europe's iXBRL/Bilanz extractors
never captured a fiscal-year integer, only a period end date).

Today the only country with more than one fiscal year of real
structured fundamentals on file is Austria (v2.38AI, firmenakte.at,
up to 5 years per company) -- GB/Ireland's iXBRL extraction has always
captured a single period per company. A company with fewer than 2
periods on file simply has no growth evidence yet and is marked
INSUFFICIENT_FEATURE_EVIDENCE, never guessed. Austria's captured
concepts do not include operating cash flow or capex, so the US
script's free-cash-flow-derived features (free_cash_flow,
capex_to_revenue, cash_conversion_ratio, positive_fcf_flag,
fundamental_momentum_flag) have no Austrian equivalent and are not
reproduced here -- only revenue, net profit, total assets and equity
growth are computed, since those are the four canonical concepts every
Austrian company's data actually populates.
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
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ak_europe_growth_features"
PHASE = "v2.38AK-europe-growth-features"
# Every real block on file with more than one fiscal year per company.
# GB/Ireland's iXBRL extraction (v2.38W/v2.38Y) only ever captured a
# single period, so including those files here would be harmless (they
# simply never clear the >=2-period bar) but is deliberately left out to
# keep this script's scope honest about what it actually was built for.
DEFAULT_RECORDS_INPUTS = [
    ROOT / "outputs/full_universe_source_acquisition/v2_38ai_europe_austria_fundamentals/europe_austria_fundamental_records_v2_38ai.jsonl",
]

FEATURE_FIELDS = [
    "asset_id", "ticker", "company_name", "company_number",
    "current_period_end", "previous_period_end", "periods_available",
    "feature_quality_status", "features_calculated", "features_missing",
    "quality_flags", "revenue_yoy_growth", "net_profit_yoy_growth",
    "assets_yoy_growth", "equity_yoy_growth", "growth_acceleration_flag",
    "margin_expansion_flag", "phase",
]
QUALITY_FIELDS = ["asset_id", "ticker", "company_name", "company_number", "periods_available", "features_calculated", "features_missing", "feature_quality_status", "quality_flags"]
REJECTION_FIELDS = ["asset_id", "ticker", "company_number", "feature", "reason", "current_period_end", "previous_period_end", "phase"]
FEATURES = ["revenue_yoy_growth", "net_profit_yoy_growth", "assets_yoy_growth", "equity_yoy_growth", "growth_acceleration_flag", "margin_expansion_flag"]

# Same canonical-concept resolution as v2.38X (build_europe_fundamental_
# features_v2_38x.py) -- kept as a separate copy rather than a shared
# import because the two scripts have different lifecycles (v2.38X gets
# reconstructed whenever a new same-period ratio is added; this script's
# concept list only needs to grow when a new country's multi-year data
# arrives) and this project has consistently preferred small, independently
# runnable scripts over a shared library layer for these builders.
CONCEPT_ALIASES = {
    "revenue": ["ifrs-full:Revenue", "umsatzerloese"],
    "net_profit": ["ifrs-full:ProfitLoss", "jahresueberschuss"],
    "total_assets": ["ifrs-full:Assets", "bilanzSumme"],
    "equity": ["ifrs-full:Equity", "eigenkapital"],
}
GROWTH_FEATURES = {
    "revenue_yoy_growth": "revenue",
    "net_profit_yoy_growth": "net_profit",
    "assets_yoy_growth": "total_assets",
    "equity_yoy_growth": "equity",
}


def canonicalize_concepts(period_records: list[dict[str, Any]]) -> dict[str, float]:
    by_raw = {r["concept"]: r["value"] for r in period_records if r.get("value") is not None}
    by_canonical: dict[str, float] = {}
    for canonical, aliases in CONCEPT_ALIASES.items():
        for alias in aliases:
            if alias in by_raw:
                by_canonical[canonical] = by_raw[alias]
                break
    return by_canonical


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


def read_jsonl_many(paths: Path | list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    path_list = [paths] if isinstance(paths, Path) else list(paths)
    all_records: list[dict[str, Any]] = []
    sources_used: list[str] = []
    for path in path_list:
        records = read_jsonl(path)
        if records:
            try:
                sources_used.append(str(path.relative_to(ROOT)))
            except ValueError:
                sources_used.append(str(path))
        all_records.extend(records)
    return all_records, sources_used


def rounded(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, 6)


def yoy(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous <= 0:
        return None
    return rounded((current - previous) / previous)


def ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den <= 0:
        return None
    return rounded(num / den)


def build_company(company_records: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    base = company_records[0]
    company_number = base.get("company_number") or base.get("fnr", "")
    company_name = base.get("company_name") or base.get("ticker", "")
    by_period: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in company_records:
        if r.get("period_end"):
            by_period[r["period_end"]].append(r)
    periods = sorted(by_period)  # ISO date strings sort chronologically
    canon_by_period = {p: canonicalize_concepts(recs) for p, recs in by_period.items()}

    row: dict[str, Any] = {field: None for field in FEATURE_FIELDS}
    row.update({
        "asset_id": base["asset_id"], "ticker": base["ticker"], "company_name": company_name,
        "company_number": company_number, "periods_available": len(periods), "phase": PHASE,
        "growth_acceleration_flag": False, "margin_expansion_flag": False,
    })
    rejections: list[dict[str, str]] = []

    if len(periods) < 2:
        row["feature_quality_status"] = "INSUFFICIENT_FEATURE_EVIDENCE"
        row["features_missing"] = "|".join(FEATURES)
        row["quality_flags"] = "fewer_than_two_periods_on_file"
        return row, [{"asset_id": base["asset_id"], "ticker": base["ticker"], "company_number": company_number, "feature": f, "reason": "fewer_than_two_periods_on_file", "current_period_end": "", "previous_period_end": "", "phase": PHASE} for f in FEATURES]

    current_period, previous_period = periods[-1], periods[-2]
    current, previous = canon_by_period[current_period], canon_by_period[previous_period]
    row["current_period_end"] = current_period
    row["previous_period_end"] = previous_period

    missing: list[str] = []
    for feature, concept in GROWTH_FEATURES.items():
        value = yoy(current.get(concept), previous.get(concept))
        row[feature] = value
        if value is None:
            missing.append(feature)
            if concept not in current:
                reason = "missing_current_period_value"
            elif concept not in previous:
                reason = "missing_previous_period_value"
            else:
                reason = "nonpositive_previous_period_value"
            rejections.append({"asset_id": base["asset_id"], "ticker": base["ticker"], "company_number": company_number, "feature": feature, "reason": reason, "current_period_end": current_period, "previous_period_end": previous_period, "phase": PHASE})

    revenue_growth = row["revenue_yoy_growth"]
    if len(periods) >= 3:
        two_back = canon_by_period[periods[-3]]
        previous_revenue_growth = yoy(previous.get("revenue"), two_back.get("revenue"))
        row["growth_acceleration_flag"] = bool(revenue_growth is not None and previous_revenue_growth is not None and revenue_growth > previous_revenue_growth)
    current_margin = ratio(current.get("net_profit"), current.get("revenue"))
    previous_margin = ratio(previous.get("net_profit"), previous.get("revenue"))
    row["margin_expansion_flag"] = bool(current_margin is not None and previous_margin is not None and current_margin > previous_margin)

    calculated = [f for f in FEATURES if row.get(f) is not None]
    row["features_calculated"] = len(calculated)
    row["features_missing"] = "|".join(sorted(missing))
    row["quality_flags"] = "|".join(sorted(f for f in ("growth_acceleration_flag", "margin_expansion_flag") if row[f]))
    if len(calculated) == len(FEATURES):
        row["feature_quality_status"] = "FEATURES_READY"
    elif calculated:
        row["feature_quality_status"] = "FEATURES_PARTIAL"
    else:
        row["feature_quality_status"] = "INSUFFICIENT_FEATURE_EVIDENCE"
    return row, rejections


def build(records_paths: Path | list[Path], output_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records, sources_used = read_jsonl_many(records_paths)
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
    write_csv(output_dir / "europe_growth_features_v2_38ak.csv", feature_rows, FEATURE_FIELDS)
    write_csv(output_dir / "europe_growth_feature_quality_v2_38ak.csv", feature_rows, QUALITY_FIELDS)
    write_csv(output_dir / "europe_growth_feature_rejections_v2_38ak.csv", rejection_rows, REJECTION_FIELDS)

    quality_counts = {status: sum(1 for r in feature_rows if r["feature_quality_status"] == status) for status in {"FEATURES_READY", "FEATURES_PARTIAL", "INSUFFICIENT_FEATURE_EVIDENCE"}}
    report = {
        "phase": PHASE, "companies_input": len(grouped),
        "companies_features_ready": quality_counts["FEATURES_READY"],
        "companies_features_partial": quality_counts["FEATURES_PARTIAL"],
        "companies_insufficient": quality_counts["INSUFFICIENT_FEATURE_EVIDENCE"],
        "rejected_rows": len(rejection_rows), "network_used": False, "scoring_created": False,
        "ranking_created": False, "recommendations_created": False, "phase9c_authorized": False,
        "records_sources_used": sources_used,
        "note": "Growth features require >=2 fiscal periods on file for a company; today only Austria (v2.38AI) has real multi-year fundamentals in this pipeline. GB/Ireland's single-period iXBRL extraction never clears this bar and correctly reports INSUFFICIENT_FEATURE_EVIDENCE if ever included as an input. Free-cash-flow-derived features from the US v2.38G methodology (free_cash_flow, capex_to_revenue, cash_conversion_ratio, positive_fcf_flag, fundamental_momentum_flag) are not reproduced here: Austria's captured concepts include no operating cash flow or capex figures.",
    }
    write_text(output_dir / "europe_growth_features_report_v2_38ak.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report, feature_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records-input", type=Path, nargs="+", default=DEFAULT_RECORDS_INPUTS, help="one or more fundamentals records JSONL files to merge (defaults to every real multi-year block on file: v2.38AI)")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report, _ = build(args.records_input, args.output_dir)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
