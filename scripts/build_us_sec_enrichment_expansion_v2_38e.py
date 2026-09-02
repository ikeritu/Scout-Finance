#!/usr/bin/env python3
"""Build v2.38E SEC enrichment readiness artifacts from local cache."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_sec_enrichment_expansion_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38e_us_sec_enrichment_expansion"
FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "cik", "identity_status",
    "enrichment_status", "submissions_available", "companyfacts_available",
    "basic_concepts_available", "available_forms", "latest_filing_date",
    "latest_10k_date", "latest_10q_date", "sec_taxonomies", "facts_count",
    "review_reason", "evidence_hash", "phase",
]
ALLOWED_FORMS = {"10-K", "10-Q", "8-K", "20-F", "6-K"}
BASIC_CONCEPTS = {
    "revenue": {"RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"},
    "net_income": {"NetIncomeLoss"},
    "assets": {"Assets"},
    "liabilities": {"Liabilities"},
    "equity": {"StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"},
    "operating_cash_flow": {"NetCashProvidedByUsedInOperatingActivities"},
    "capex": {"PaymentsToAcquirePropertyPlantAndEquipment"},
    "eps": {"EarningsPerShareBasic", "EarningsPerShareDiluted"},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_hash(row: dict[str, str]) -> str:
    parts = [row.get(field, "") for field in FIELDS if field != "evidence_hash"]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def forms_from_submissions(payload: dict) -> dict[str, str]:
    recent = payload.get("filings", {}).get("recent", {}) if payload else {}
    forms = recent.get("form", []) if isinstance(recent, dict) else []
    dates = recent.get("filingDate", []) if isinstance(recent, dict) else []
    available = sorted({form for form in forms if form in ALLOWED_FORMS})
    by_form: dict[str, list[str]] = {}
    for form, date in zip(forms, dates):
        if form in ALLOWED_FORMS and date:
            by_form.setdefault(form, []).append(date)
    return {
        "available_forms": "|".join(available),
        "latest_filing_date": max([d for d in dates if d], default=""),
        "latest_10k_date": max(by_form.get("10-K", []), default=""),
        "latest_10q_date": max(by_form.get("10-Q", []), default=""),
    }


def facts_from_companyfacts(payload: dict) -> dict[str, str]:
    facts = payload.get("facts", {}) if payload else {}
    taxonomies = sorted(facts) if isinstance(facts, dict) else []
    us_gaap = facts.get("us-gaap", {}) if isinstance(facts, dict) else {}
    concepts = set(us_gaap) if isinstance(us_gaap, dict) else set()
    basic = sorted(name for name, aliases in BASIC_CONCEPTS.items() if concepts & aliases)
    facts_count = sum(len(v) for v in facts.values() if isinstance(v, dict)) if isinstance(facts, dict) else 0
    return {
        "basic_concepts_available": "|".join(basic),
        "sec_taxonomies": "|".join(taxonomies),
        "facts_count": str(facts_count),
    }


def classify(row: dict[str, str], cache_dir: Path) -> dict[str, str]:
    cik = row.get("cik", "")
    identity_status = row.get("identity_status", "")
    base = {
        "asset_id": row["asset_id"],
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "exchange": row["exchange"],
        "cik": cik,
        "identity_status": identity_status,
        "submissions_available": "false",
        "companyfacts_available": "false",
        "basic_concepts_available": "",
        "available_forms": "",
        "latest_filing_date": "",
        "latest_10k_date": "",
        "latest_10q_date": "",
        "sec_taxonomies": "",
        "facts_count": "0",
        "review_reason": "",
        "phase": "v2.38E",
    }
    if identity_status == "US_SEC_NOT_ELIGIBLE":
        base["enrichment_status"] = "SEC_NOT_ELIGIBLE"
        base["review_reason"] = row.get("review_reason", "not eligible")
    elif identity_status != "US_SEC_CIK_RESOLVED" or not cik:
        base["enrichment_status"] = "SEC_CIK_REVIEW_REQUIRED"
        base["review_reason"] = row.get("review_reason", "CIK not resolved")
    else:
        submissions = load_json(cache_dir / "submissions" / f"CIK{cik}.json")
        companyfacts = load_json(cache_dir / "companyfacts" / f"CIK{cik}.json")
        if submissions:
            base["submissions_available"] = "true"
            base.update(forms_from_submissions(submissions))
        if companyfacts:
            base["companyfacts_available"] = "true"
            base.update(facts_from_companyfacts(companyfacts))
        if submissions and companyfacts:
            base["enrichment_status"] = "ENRICHED_SEC_READY"
        elif companyfacts:
            base["enrichment_status"] = "ENRICHED_PARTIAL_COMPANYFACTS_ONLY"
            base["review_reason"] = "submissions missing"
        elif submissions:
            base["enrichment_status"] = "ENRICHED_PARTIAL_SUBMISSIONS_ONLY"
            base["review_reason"] = "companyfacts missing"
        else:
            base["enrichment_status"] = "SEC_CIK_RESOLVED_PENDING_COLLECTION"
            base["review_reason"] = "SEC submissions/companyfacts not cached"
    base["evidence_hash"] = row_hash(base)
    return base


def build(cache_dir: Path, limit: int) -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    overlay_path = ROOT / contract["input_us_sec_overlay"]
    census_path = ROOT / contract["input_us_census"]
    overlay = read_csv(overlay_path)
    census = read_csv(census_path)
    if len(census) != contract["expected_us_rows"]:
        raise SystemExit("BLOCKED: US census row count mismatch")
    if sum(r["eligibility_status"] == "ELIGIBLE" for r in census) != contract["expected_us_eligible_rows"]:
        raise SystemExit("BLOCKED: US eligible count mismatch")
    if not 1 <= limit <= contract["maximum_batch_assets"]:
        raise SystemExit("BLOCKED: batch limit must be 1..250")
    rows = [classify(row, cache_dir) for row in overlay]
    write_csv(OUT / "us_sec_enrichment_readiness_v2_38e.csv", rows, FIELDS)
    review = [r for r in rows if r["enrichment_status"] != "ENRICHED_SEC_READY"]
    write_csv(OUT / "us_sec_enrichment_review_v2_38e.csv", review, FIELDS)
    pending = [r for r in rows if r["enrichment_status"] == "SEC_CIK_RESOLVED_PENDING_COLLECTION"]
    write_csv(
        OUT / "us_sec_enrichment_batch_plan_v2_38e.csv",
        [{"asset_id": r["asset_id"], "ticker": r["ticker"], "company_name": r["company_name"], "exchange": r["exchange"], "cik": r["cik"], "selection_reason": "deterministic_pending_sec_collection"} for r in pending[:limit]],
        ["asset_id", "ticker", "company_name", "exchange", "cik", "selection_reason"],
    )
    enriched = [r for r in rows if r["enrichment_status"] == "ENRICHED_SEC_READY"]
    write_csv(
        OUT / "us_sec_enrichment_batch_ledger_v2_38e.csv",
        [{"batch_source": "local_sec_cache", "assets_detected": str(len(enriched)), "raw_cache_published": "false", "phase9c_authorized": "false"}],
        ["batch_source", "assets_detected", "raw_cache_published", "phase9c_authorized"],
    )
    counts = Counter(r["enrichment_status"] for r in rows)
    cik_resolved = sum(r["identity_status"] == "US_SEC_CIK_RESOLVED" for r in rows)
    report = {
        "phase": "v2.38E-us-sec-enrichment-expansion",
        "status": "COMPLETED_US_SEC_ENRICHMENT_EXPANSION_NOT_SCORING" if counts["ENRICHED_SEC_READY"] == cik_resolved and cik_resolved else "PARTIAL_US_SEC_ENRICHMENT_EXPANSION_NOT_SCORING",
        "us_rows": len(census),
        "us_eligible": contract["expected_us_eligible_rows"],
        "cik_resolved": cik_resolved,
        "enriched_sec_ready": counts["ENRICHED_SEC_READY"],
        "partial": counts["ENRICHED_PARTIAL_COMPANYFACTS_ONLY"] + counts["ENRICHED_PARTIAL_SUBMISSIONS_ONLY"],
        "pending_collection": counts["SEC_CIK_RESOLVED_PENDING_COLLECTION"],
        "review_required": counts["SEC_CIK_REVIEW_REQUIRED"],
        "not_eligible": counts["SEC_NOT_ELIGIBLE"],
        "submissions_available": sum(r["submissions_available"] == "true" for r in rows),
        "companyfacts_available": sum(r["companyfacts_available"] == "true" for r in rows),
        "with_basic_concepts": sum(bool(r["basic_concepts_available"]) for r in rows),
        "raw_cache_published": False,
        "enrichment_status_counts": dict(sorted(counts.items())),
        "guardrails": {
            "phase9c_authorized": False,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
        },
        "limitations": [
            "SEC enrichment records availability and metadata only; no scoring or recommendations.",
            "Raw SEC JSON remains local and ignored by git.",
            "Adjusted prices and comparable normalized fundamentals are deferred to later phases.",
        ],
    }
    (OUT / "us_sec_enrichment_aggregate_report_v2_38e.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (OUT / "README.md").write_text("# v2.38E US SEC enrichment expansion\n\nControlled SEC enrichment expansion for US eligible companies. Raw SEC JSON is local-only; committed artifacts are aggregate/readiness outputs only.\n", encoding="utf-8", newline="\n")
    (OUT / "US_SEC_ENRICHMENT_EXPANSION_CONTRACT_v2_38e.md").write_text("# US SEC Enrichment Expansion Contract v2.38E\n\nThis phase expands SEC submissions/companyfacts coverage for US eligible companies without scoring, ranking, recommendations, broker actions or phase 9C authorization.\n", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9E US SEC Enrichment Gate v2.38E

Decision: {report['status']}

- US rows: {report['us_rows']}
- US eligible: {report['us_eligible']}
- CIK resolved: {report['cik_resolved']}
- SEC-ready enriched rows: {report['enriched_sec_ready']}
- Partial SEC rows: {report['partial']}
- Pending collection: {report['pending_collection']}
- Review required: {report['review_required']}
- Raw cache published: false

This phase does not calculate scoring, ranking, recommendations, predictions, broker actions, trading or phase 9C signals.
"""
    (OUT / "PHASE9E_US_SEC_ENRICHMENT_GATE_v2_38e.md").write_text(gate, encoding="utf-8", newline="\n")
    manifest = {
        "phase": "v2.38E-us-sec-enrichment-expansion",
        "decision": report["status"],
        "inputs": {
            contract["input_us_census"]: {"bytes": census_path.stat().st_size, "sha256": sha256(census_path)},
            contract["input_us_sec_overlay"]: {"bytes": overlay_path.stat().st_size, "sha256": sha256(overlay_path)},
        },
        "outputs": {},
        "guardrails": report["guardrails"],
    }
    for path in sorted(OUT.glob("*")):
        if path.is_file() and path.name != "us_sec_enrichment_manifest_v2_38e.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (OUT / "us_sec_enrichment_manifest_v2_38e.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=OUT / "sec_raw_cache_v2_38e")
    parser.add_argument("--limit", type=int, default=250)
    args = parser.parse_args()
    report = build(args.cache_dir, args.limit)
    print(json.dumps({"status": report["status"], "us_rows": report["us_rows"], "cik_resolved": report["cik_resolved"], "enriched_sec_ready": report["enriched_sec_ready"], "recommendations_generated": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
