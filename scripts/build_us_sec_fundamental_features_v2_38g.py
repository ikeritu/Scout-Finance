#!/usr/bin/env python3
"""Build deterministic v2.38G US SEC fundamental features without scoring."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_sec_fundamental_features_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38g_us_sec_fundamental_features"
FEATURE_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "cik", "feature_asof_fy",
    "latest_filed", "latest_period_end", "evidence_years", "evidence_quarters",
    "feature_quality_status", "features_calculated", "features_missing",
    "quality_flags", "revenue_yoy_growth", "net_income_yoy_growth",
    "operating_cash_flow_yoy_growth", "assets_yoy_growth", "equity_yoy_growth",
    "net_margin", "return_on_assets", "return_on_equity",
    "operating_cash_flow_margin", "liabilities_to_assets", "equity_to_assets",
    "free_cash_flow", "free_cash_flow_margin", "capex_to_revenue",
    "cash_conversion_ratio", "growth_acceleration_flag", "margin_expansion_flag",
    "positive_fcf_flag", "balance_strength_flag", "fundamental_momentum_flag",
    "phase",
]
QUALITY_FIELDS = [
    "asset_id", "ticker", "company_name", "cik", "features_calculated",
    "features_missing", "feature_quality_status", "latest_filed",
    "latest_period_end", "evidence_years", "evidence_quarters", "quality_flags",
]
REJECTION_FIELDS = [
    "asset_id", "ticker", "cik", "feature", "reason", "current_fy",
    "previous_fy", "metric", "phase",
]
FORM_PRIORITY = {"10-K": 0, "20-F": 1, "10-Q": 2}
FEATURES = [
    "revenue_yoy_growth", "net_income_yoy_growth", "operating_cash_flow_yoy_growth",
    "assets_yoy_growth", "equity_yoy_growth", "net_margin", "return_on_assets",
    "return_on_equity", "operating_cash_flow_margin", "liabilities_to_assets",
    "equity_to_assets", "free_cash_flow", "free_cash_flow_margin",
    "capex_to_revenue", "cash_conversion_ratio", "growth_acceleration_flag",
    "margin_expansion_flag", "positive_fcf_flag", "balance_strength_flag",
    "fundamental_momentum_flag",
]
GROWTH_FEATURES = {
    "revenue_yoy_growth": "revenue",
    "net_income_yoy_growth": "net_income",
    "operating_cash_flow_yoy_growth": "operating_cash_flow",
    "assets_yoy_growth": "assets",
    "equity_yoy_growth": "equity",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"BLOCKED: required local v2.38F normalized records not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def form_rank(form: str) -> int:
    return FORM_PRIORITY.get(form, 99)


def better_record(candidate: dict[str, Any], current: dict[str, Any] | None) -> bool:
    if current is None:
        return True
    return (
        str(candidate.get("filed", "")),
        -form_rank(str(candidate.get("form", ""))),
        str(candidate.get("end", "")),
        -int(candidate.get("_line_no", 0)),
    ) > (
        str(current.get("filed", "")),
        -form_rank(str(current.get("form", ""))),
        str(current.get("end", "")),
        -int(current.get("_line_no", 0)),
    )


def selected_annual(records: list[dict[str, Any]]) -> dict[int, dict[str, float]]:
    selected: dict[tuple[int, str], dict[str, Any]] = {}
    for record in records:
        if record.get("period_type") != "annual":
            continue
        key = (int(record["fy"]), str(record["metric"]))
        if better_record(record, selected.get(key)):
            selected[key] = record
    by_fy: dict[int, dict[str, float]] = defaultdict(dict)
    for (fy, metric), record in selected.items():
        by_fy[fy][metric] = float(record["value"])
    return dict(by_fy)


def latest_dates(records: list[dict[str, Any]]) -> tuple[str, str]:
    return (
        max((str(r.get("filed", "")) for r in records), default=""),
        max((str(r.get("end", "")) for r in records), default=""),
    )


def reject(base: dict[str, Any], feature: str, reason: str, current_fy: int | str = "", previous_fy: int | str = "", metric: str = "") -> dict[str, str]:
    return {
        "asset_id": str(base.get("asset_id", "")),
        "ticker": str(base.get("ticker", "")),
        "cik": str(base.get("cik", "")),
        "feature": feature,
        "reason": reason,
        "current_fy": str(current_fy),
        "previous_fy": str(previous_fy),
        "metric": metric,
        "phase": "v2.38G",
    }


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


def as_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def build_company(records: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    base = records[0]
    rejections: list[dict[str, str]] = []
    annual = selected_annual(records)
    years = sorted(annual)
    latest_filed, latest_end = latest_dates(records)
    quarters = len({(int(r["fy"]), str(r["fp"]), str(r["metric"])) for r in records if r.get("period_type") == "quarterly"})
    if not years:
        row = base_row(base, 0, latest_filed, latest_end, 0, quarters)
        row["feature_quality_status"] = "INSUFFICIENT_FEATURE_EVIDENCE"
        row["features_missing"] = "|".join(FEATURES)
        row["quality_flags"] = "no_annual_evidence"
        return row, [reject(base, feature, "no_annual_evidence") for feature in FEATURES]
    current_fy = years[-1]
    previous_fy = current_fy - 1
    current = annual[current_fy]
    previous = annual.get(previous_fy, {})
    row = base_row(base, current_fy, latest_filed, latest_end, len(years), quarters)
    missing: list[str] = []
    flags: set[str] = set()
    for feature, metric in GROWTH_FEATURES.items():
        value = yoy(current.get(metric), previous.get(metric))
        row[feature] = value
        if value is None:
            missing.append(feature)
            reason = "missing_previous_year" if metric not in previous else "invalid_or_nonpositive_previous_denominator"
            rejections.append(reject(base, feature, reason, current_fy, previous_fy, metric))
    row["net_margin"] = ratio(current.get("net_income"), current.get("revenue"))
    row["return_on_assets"] = ratio(current.get("net_income"), current.get("assets"))
    row["return_on_equity"] = ratio(current.get("net_income"), current.get("equity"))
    row["operating_cash_flow_margin"] = ratio(current.get("operating_cash_flow"), current.get("revenue"))
    row["liabilities_to_assets"] = ratio(current.get("liabilities"), current.get("assets"))
    row["equity_to_assets"] = ratio(current.get("equity"), current.get("assets"))
    ocf = current.get("operating_cash_flow")
    capex = current.get("capex")
    free_cash_flow = None if ocf is None or capex is None else rounded(ocf - abs(capex))
    row["free_cash_flow"] = free_cash_flow
    row["free_cash_flow_margin"] = ratio(free_cash_flow, current.get("revenue"))
    row["capex_to_revenue"] = ratio(abs(capex) if capex is not None else None, current.get("revenue"))
    row["cash_conversion_ratio"] = ratio(ocf, current.get("net_income"))
    denominator_rules = {
        "net_margin": ("revenue", "missing_or_invalid_revenue"),
        "return_on_assets": ("assets", "missing_or_invalid_assets"),
        "return_on_equity": ("equity", "missing_or_invalid_equity"),
        "operating_cash_flow_margin": ("revenue", "missing_or_invalid_revenue"),
        "liabilities_to_assets": ("assets", "missing_or_invalid_assets"),
        "equity_to_assets": ("assets", "missing_or_invalid_assets"),
        "free_cash_flow": ("operating_cash_flow|capex", "missing_cash_flow_or_capex"),
        "free_cash_flow_margin": ("revenue", "missing_or_invalid_revenue_or_fcf"),
        "capex_to_revenue": ("revenue", "missing_or_invalid_revenue_or_capex"),
        "cash_conversion_ratio": ("net_income", "missing_or_invalid_net_income"),
    }
    for feature, (metric, reason) in denominator_rules.items():
        if row[feature] is None:
            missing.append(feature)
            rejections.append(reject(base, feature, reason, current_fy, "", metric))
    if capex is not None and capex > 0:
        flags.add("capex_positive_treated_as_outflow")
    revenue_growth = row["revenue_yoy_growth"]
    previous_revenue_growth = None
    if len(years) >= 3 and current_fy - 2 in annual:
        previous_revenue_growth = yoy(previous.get("revenue"), annual[current_fy - 2].get("revenue"))
    row["growth_acceleration_flag"] = bool(revenue_growth is not None and previous_revenue_growth is not None and revenue_growth > previous_revenue_growth)
    previous_margin = ratio(previous.get("net_income"), previous.get("revenue"))
    row["margin_expansion_flag"] = bool(row["net_margin"] is not None and previous_margin is not None and row["net_margin"] > previous_margin)
    row["positive_fcf_flag"] = bool(free_cash_flow is not None and free_cash_flow > 0)
    row["balance_strength_flag"] = bool(row["liabilities_to_assets"] is not None and row["liabilities_to_assets"] < 0.6 and row["equity_to_assets"] is not None and row["equity_to_assets"] > 0.3)
    row["fundamental_momentum_flag"] = bool((revenue_growth or 0) > 0 and row["margin_expansion_flag"] and row["positive_fcf_flag"])
    calculated = [feature for feature in FEATURES if row.get(feature) not in {None, ""}]
    row["features_calculated"] = len(calculated)
    row["features_missing"] = "|".join(sorted(set(missing)))
    row["quality_flags"] = "|".join(sorted(flags))
    if row["features_calculated"] >= 15:
        row["feature_quality_status"] = "FEATURES_READY"
    elif row["features_calculated"] > 0:
        row["feature_quality_status"] = "FEATURES_PARTIAL"
    else:
        row["feature_quality_status"] = "INSUFFICIENT_FEATURE_EVIDENCE"
    return row, rejections


def base_row(base: dict[str, Any], current_fy: int, latest_filed: str, latest_end: str, years: int, quarters: int) -> dict[str, Any]:
    row = {field: None for field in FEATURE_FIELDS}
    row.update({
        "asset_id": base["asset_id"],
        "ticker": base["ticker"],
        "company_name": base["company_name"],
        "exchange": base["exchange"],
        "cik": base["cik"],
        "feature_asof_fy": current_fy,
        "latest_filed": latest_filed,
        "latest_period_end": latest_end,
        "evidence_years": years,
        "evidence_quarters": quarters,
        "feature_quality_status": "INSUFFICIENT_FEATURE_EVIDENCE",
        "features_calculated": 0,
        "features_missing": "",
        "quality_flags": "",
        "growth_acceleration_flag": False,
        "margin_expansion_flag": False,
        "positive_fcf_flag": False,
        "balance_strength_flag": False,
        "fundamental_momentum_flag": False,
        "phase": "v2.38G",
    })
    return row


def build(input_records: Path, quality_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    quality_rows = read_csv(quality_path) if quality_path.exists() else []
    records = read_jsonl(input_records)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["asset_id"])].append(record)
    feature_rows: list[dict[str, Any]] = []
    rejection_rows: list[dict[str, str]] = []
    for asset_id in sorted(grouped):
        row, rejections = build_company(grouped[asset_id])
        feature_rows.append(row)
        rejection_rows.extend(rejections)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_rows = [{field: as_csv_value(row.get(field)) for field in FEATURE_FIELDS} for row in feature_rows]
    quality = [{field: as_csv_value(row.get(field)) for field in QUALITY_FIELDS} for row in feature_rows]
    write_csv(output_dir / "us_sec_fundamental_features_v2_38g.csv", csv_rows, FEATURE_FIELDS)
    write_csv(output_dir / "us_sec_fundamental_feature_quality_v2_38g.csv", quality, QUALITY_FIELDS)
    write_csv(output_dir / "us_sec_fundamental_feature_rejections_v2_38g.csv", rejection_rows, REJECTION_FIELDS)
    quality_counts = Counter(row["feature_quality_status"] for row in feature_rows)
    coverage = {feature: sum(row.get(feature) not in {None, ""} for row in feature_rows) for feature in FEATURES}
    status = "COMPLETED_US_SEC_FUNDAMENTAL_FEATURES_NOT_SCORING" if feature_rows else "PARTIAL_US_SEC_FUNDAMENTAL_FEATURES_NOT_SCORING"
    report = {
        "phase": "v2.38G-us-sec-fundamental-features",
        "status": status,
        "input_records": len(records),
        "input_quality_companies": len(quality_rows),
        "companies_input": len(grouped),
        "companies_features_ready": quality_counts["FEATURES_READY"],
        "companies_features_partial": quality_counts["FEATURES_PARTIAL"],
        "companies_insufficient": quality_counts["INSUFFICIENT_FEATURE_EVIDENCE"],
        "feature_coverage": dict(sorted(coverage.items())),
        "feature_quality_status_counts": dict(sorted(quality_counts.items())),
        "rejected_rows": len(rejection_rows),
        "raw_cache_published": False,
        "guardrails": {
            "network_calls": 0,
            "phase9c_authorized": False,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
        },
    }
    (output_dir / "us_sec_fundamental_feature_aggregate_report_v2_38g.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "README.md").write_text("# v2.38G US SEC fundamental features\n\nBuilds deterministic per-company features from v2.38F normalized SEC fundamentals. No network, scoring, ranking or recommendations.\n", encoding="utf-8", newline="\n")
    (output_dir / "US_SEC_FUNDAMENTAL_FEATURES_CONTRACT_v2_38g.md").write_text("# US SEC Fundamental Features Contract v2.38G\n\nThis phase converts normalized SEC fundamentals into traceable comparable features. It does not authorize scoring, ranking, recommendations, predictions, phase 9C, broker actions or trading.\n", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9G US SEC Features Gate v2.38G

Decision: {report['status']}

- Input normalized records: {report['input_records']}
- Companies input: {report['companies_input']}
- Companies features ready: {report['companies_features_ready']}
- Companies features partial: {report['companies_features_partial']}
- Companies insufficient: {report['companies_insufficient']}
- Rejected rows: {report['rejected_rows']}
- Raw cache published: false

This phase does not calculate final scores, rankings, recommendations, predictions, broker actions, trading or phase 9C signals.
"""
    (output_dir / "PHASE9G_US_SEC_FEATURES_GATE_v2_38g.md").write_text(gate, encoding="utf-8", newline="\n")
    manifest = {
        "phase": "v2.38G-us-sec-fundamental-features",
        "decision": status,
        "inputs": {
            str(input_records.relative_to(ROOT) if input_records.is_relative_to(ROOT) else input_records): {"bytes": input_records.stat().st_size, "sha256": sha256(input_records)},
            str(quality_path.relative_to(ROOT) if quality_path.exists() and quality_path.is_relative_to(ROOT) else quality_path): {"bytes": quality_path.stat().st_size if quality_path.exists() else 0, "sha256": sha256(quality_path) if quality_path.exists() else ""},
        },
        "outputs": {},
        "guardrails": report["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.is_file() and path.name != "us_sec_fundamental_features_manifest_v2_38g.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (output_dir / "us_sec_fundamental_features_manifest_v2_38g.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-records", type=Path, default=ROOT / contract["input_records"])
    parser.add_argument("--quality-path", type=Path, default=ROOT / contract["input_quality"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.input_records, args.quality_path, args.output_dir)
    print(json.dumps({
        "status": report["status"],
        "companies_input": report["companies_input"],
        "companies_features_ready": report["companies_features_ready"],
        "companies_features_partial": report["companies_features_partial"],
        "companies_insufficient": report["companies_insufficient"],
        "recommendations_generated": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
