#!/usr/bin/env python3
"""Normalize SEC companyfacts into traceable v2.38F records without network calls."""
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
CONTRACT = ROOT / "config/us_sec_fundamental_normalization_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38f_us_sec_fundamental_normalization"
QUALITY_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "cik", "enrichment_status",
    "records", "metrics_available", "annual_records", "quarterly_records",
    "latest_filed", "latest_period_end", "quality_status", "missing_metrics",
    "quality_flags",
]
REJECT_FIELDS = ["asset_id", "ticker", "cik", "metric", "source_concept", "reason", "form", "fy", "fp", "filed", "end", "unit", "phase"]
METRIC_CONCEPTS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"],
    "net_income": ["NetIncomeLoss"],
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "eps_basic": ["EarningsPerShareBasic"],
    "eps_diluted": ["EarningsPerShareDiluted"],
}
QUALITY_FLAGS = {
    "missing_filed_date", "missing_period_end", "missing_fy", "missing_fp",
    "missing_form", "missing_value", "invalid_numeric_value", "unsupported_unit",
    "duplicate_lower_priority", "amendment_form", "non_primary_form",
    "quarterly_without_10q", "annual_without_10k", "negative_value_allowed",
    "negative_value_review", "cache_missing", "companyfacts_missing",
    "taxonomy_missing", "concept_missing",
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def reject(row: dict[str, str], metric: str, concept: str, fact: dict[str, Any] | None, unit: str, reason: str) -> dict[str, str]:
    fact = fact or {}
    return {
        "asset_id": row["asset_id"],
        "ticker": row["ticker"],
        "cik": row["cik"],
        "metric": metric,
        "source_concept": concept,
        "reason": reason,
        "form": str(fact.get("form", "")),
        "fy": str(fact.get("fy", "")),
        "fp": str(fact.get("fp", "")),
        "filed": str(fact.get("filed", "")),
        "end": str(fact.get("end", "")),
        "unit": unit,
        "phase": "v2.38F",
    }


def period_type(fp: str, form: str) -> str:
    if fp == "FY" or form in {"10-K", "20-F"}:
        return "annual"
    return "quarterly"


def supported_unit(metric: str, unit: str) -> bool:
    if metric.startswith("eps_"):
        return unit == "USD/shares" or unit.endswith("/shares")
    return unit == "USD"


def normalize_fact(row: dict[str, str], metric: str, concept: str, unit: str, fact: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    for key, reason in (
        ("filed", "missing_filed_date"),
        ("end", "missing_period_end"),
        ("fy", "missing_fy"),
        ("fp", "missing_fp"),
        ("form", "missing_form"),
        ("val", "missing_value"),
    ):
        if fact.get(key) in {None, ""}:
            return None, reason
    try:
        value = float(fact["val"])
    except (TypeError, ValueError):
        return None, "invalid_numeric_value"
    if not math.isfinite(value):
        return None, "invalid_numeric_value"
    if not supported_unit(metric, unit):
        return None, "unsupported_unit"
    flags: list[str] = []
    form = str(fact["form"])
    fp = str(fact["fp"])
    if form.endswith("/A"):
        flags.append("amendment_form")
    ptype = period_type(fp, form)
    if ptype == "annual" and form not in {"10-K", "20-F"}:
        flags.append("annual_without_10k")
    if ptype == "quarterly" and form != "10-Q":
        flags.append("quarterly_without_10q" if form == "8-K" else "non_primary_form")
    if value < 0:
        flags.append("negative_value_allowed" if metric in {"net_income", "operating_cash_flow", "capex", "eps_basic", "eps_diluted"} else "negative_value_review")
    return {
        "asset_id": row["asset_id"],
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "exchange": row["exchange"],
        "cik": row["cik"],
        "metric": metric,
        "value": value,
        "unit": unit,
        "fy": int(fact["fy"]),
        "fp": fp,
        "form": form,
        "filed": str(fact["filed"]),
        "end": str(fact["end"]),
        "frame": str(fact.get("frame", "")),
        "source_concept": concept,
        "taxonomy": "us-gaap",
        "quality_flags": flags,
        "period_type": ptype,
        "phase": "v2.38F",
    }, None


def normalize_company(row: dict[str, str], cache_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str]]:
    flags: list[str] = []
    records: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    companyfacts = load_json(cache_dir / "companyfacts" / f"CIK{row['cik']}.json")
    if not companyfacts:
        return [], [reject(row, "", "", None, "", "companyfacts_missing")], ["companyfacts_missing"]
    facts = companyfacts.get("facts", {})
    if not isinstance(facts, dict) or "us-gaap" not in facts:
        return [], [reject(row, "", "", None, "", "taxonomy_missing")], ["taxonomy_missing"]
    us_gaap = facts.get("us-gaap", {})
    seen: set[tuple] = set()
    for metric, concepts in METRIC_CONCEPTS.items():
        accepted_metric = 0
        for priority, concept in enumerate(concepts):
            concept_payload = us_gaap.get(concept)
            if not concept_payload:
                if priority == len(concepts) - 1 and accepted_metric == 0:
                    rejected.append(reject(row, metric, concept, None, "", "concept_missing"))
                continue
            units = concept_payload.get("units", {})
            if not isinstance(units, dict):
                rejected.append(reject(row, metric, concept, None, "", "concept_missing"))
                continue
            for unit, facts_list in units.items():
                if not isinstance(facts_list, list):
                    continue
                for fact in facts_list:
                    if not isinstance(fact, dict):
                        continue
                    record, reason = normalize_fact(row, metric, concept, unit, fact)
                    if reason:
                        rejected.append(reject(row, metric, concept, fact, unit, reason))
                        continue
                    key = (record["asset_id"], record["metric"], record["fy"], record["fp"], record["form"], record["end"], record["source_concept"], record["unit"], record["value"])
                    if key in seen:
                        rejected.append(reject(row, metric, concept, fact, unit, "duplicate_lower_priority"))
                        continue
                    seen.add(key)
                    records.append(record)
                    accepted_metric += 1
        if accepted_metric == 0:
            flags.append("concept_missing")
    return records, rejected, sorted(set(flags))


def quality_row(row: dict[str, str], records: list[dict[str, Any]], flags: list[str]) -> dict[str, str]:
    metrics = sorted({r["metric"] for r in records})
    missing = sorted(set(METRIC_CONCEPTS) - set(metrics))
    annual = sum(r["period_type"] == "annual" for r in records)
    quarterly = sum(r["period_type"] == "quarterly" for r in records)
    latest_filed = max([r["filed"] for r in records], default="")
    latest_end = max([r["end"] for r in records], default="")
    if not records:
        status = "NO_NORMALIZABLE_FACTS"
    elif not missing:
        status = "NORMALIZED_READY"
    else:
        status = "NORMALIZED_PARTIAL"
    return {
        "asset_id": row["asset_id"],
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "exchange": row["exchange"],
        "cik": row["cik"],
        "enrichment_status": row["enrichment_status"],
        "records": str(len(records)),
        "metrics_available": "|".join(metrics),
        "annual_records": str(annual),
        "quarterly_records": str(quarterly),
        "latest_filed": latest_filed,
        "latest_period_end": latest_end,
        "quality_status": status,
        "missing_metrics": "|".join(missing),
        "quality_flags": "|".join(sorted(set(flags))),
    }


def build(cache_dir: Path, readiness_override: Path | None = None, output_dir: Path = OUT) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    readiness_path = readiness_override or ROOT / contract["input_readiness"]
    rows = read_csv(readiness_path)
    if len(rows) != contract["expected_us_rows"]:
        raise SystemExit("BLOCKED: v2.38E readiness row count mismatch")
    enriched_rows = [r for r in rows if r["enrichment_status"] == "ENRICHED_SEC_READY"]
    output_dir.mkdir(parents=True, exist_ok=True)
    all_records: list[dict[str, Any]] = []
    all_rejected: list[dict[str, str]] = []
    quality: list[dict[str, str]] = []
    for row in enriched_rows:
        records, rejected, flags = normalize_company(row, cache_dir)
        all_records.extend(records)
        all_rejected.extend(rejected)
        quality.append(quality_row(row, records, flags))
    records_path = output_dir / "us_sec_fundamental_records_v2_38f.jsonl"
    with records_path.open("w", encoding="utf-8", newline="\n") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    write_csv(output_dir / "us_sec_fundamental_quality_v2_38f.csv", quality, QUALITY_FIELDS)
    write_csv(output_dir / "us_sec_fundamental_rejected_v2_38f.csv", all_rejected, REJECT_FIELDS)
    quality_counts = Counter(r["quality_status"] for r in quality)
    metrics_coverage = Counter(r["metric"] for r in all_records)
    status = "COMPLETED_US_SEC_FUNDAMENTAL_NORMALIZATION_NOT_SCORING" if all_records else "PARTIAL_US_SEC_FUNDAMENTAL_NORMALIZATION_NOT_SCORING"
    report = {
        "phase": "v2.38F-us-sec-fundamental-normalization",
        "status": status,
        "input_us_rows": contract["expected_us_rows"],
        "input_us_eligible": contract["expected_us_eligible"],
        "input_cik_resolved": contract["expected_cik_resolved"],
        "input_enriched_sec_ready": len(enriched_rows),
        "companies_processed": len(enriched_rows),
        "companies_normalized_ready": quality_counts["NORMALIZED_READY"],
        "companies_normalized_partial": quality_counts["NORMALIZED_PARTIAL"],
        "companies_no_normalizable_facts": quality_counts["NO_NORMALIZABLE_FACTS"],
        "records_written": len(all_records),
        "metrics_coverage": dict(sorted(metrics_coverage.items())),
        "quality_status_counts": dict(sorted(quality_counts.items())),
        "rejected_rows": len(all_rejected),
        "raw_cache_published": False,
        "guardrails": {
            "network_calls": 0,
            "phase9c_authorized": False,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
        },
    }
    (output_dir / "us_sec_fundamental_aggregate_report_v2_38f.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "README.md").write_text("# v2.38F US SEC fundamental normalization\n\nNormalizes cached SEC companyfacts into traceable fundamental records. No network, scoring, ranking or recommendations.\n", encoding="utf-8", newline="\n")
    (output_dir / "US_SEC_FUNDAMENTAL_NORMALIZATION_CONTRACT_v2_38f.md").write_text("# US SEC Fundamental Normalization Contract v2.38F\n\nThis phase reads local SEC cache and writes normalized fundamental records only. It does not authorize scoring, ranking, recommendations, phase 9C, broker actions or trading.\n", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9F US SEC Normalization Gate v2.38F

Decision: {report['status']}

- Input US rows: {report['input_us_rows']}
- Input US eligible: {report['input_us_eligible']}
- Input CIK resolved baseline: {report['input_cik_resolved']}
- Input enriched SEC ready: {report['input_enriched_sec_ready']}
- Companies processed: {report['companies_processed']}
- Records written: {report['records_written']}
- Companies normalized ready: {report['companies_normalized_ready']}
- Companies normalized partial: {report['companies_normalized_partial']}
- Rejected rows: {report['rejected_rows']}
- Raw cache published: false

This phase does not calculate ratios, scoring, ranking, recommendations, predictions, broker actions, trading or phase 9C signals.
"""
    (output_dir / "PHASE9F_US_SEC_NORMALIZATION_GATE_v2_38f.md").write_text(gate, encoding="utf-8", newline="\n")
    manifest = {
        "phase": "v2.38F-us-sec-fundamental-normalization",
        "decision": status,
        "inputs": {
            contract["input_readiness"]: {"bytes": readiness_path.stat().st_size, "sha256": sha256(readiness_path)}
        },
        "outputs": {},
        "guardrails": report["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.is_file() and path.name != "us_sec_fundamental_manifest_v2_38f.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (output_dir / "us_sec_fundamental_manifest_v2_38f.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "outputs/full_universe_source_acquisition/v2_38e_us_sec_enrichment_expansion/sec_raw_cache_v2_38e")
    parser.add_argument("--readiness-path", type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.cache_dir, args.readiness_path, args.output_dir)
    print(json.dumps({"status": report["status"], "companies_processed": report["companies_processed"], "records_written": report["records_written"], "recommendations_generated": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
