#!/usr/bin/env python3
"""Block v2.38BO: define, for every one of the 43,089 census companies,
whether it has ENOUGH real structural data to be considered for scoring
at all -- never computing a score, a rank, or a factor value itself.

Why this exists: the user asked to "define the eligible subset for
scoring" as the step before authorizing Phase 9C. This project has
never had an explicit answer to that question at the scale of the full
census -- the old 50-asset product (src/ui_v2_37/repository.py) answers
it implicitly, hardcoded to one fixed population. This block makes the
same kind of judgment explicit and auditable for all 43,089 companies,
reusing v2.38AL's already-computed identity/fundamentals/growth/price
ladder rather than re-deriving anything.

Design, explained (each choice traces back to a real, already-documented
finding elsewhere in this project):

1. Growth is the real floor for "eligible", not merely fundamentals.
   v2.38AL's own docstring treats identity->fundamentals->growth as one
   depth ladder because each stage strictly requires the one before it.
   A company with only a single usable fundamental period (no year-over-
   year comparison at all) cannot support the "multi-year real growth"
   framing the user chose after the project's own growth-shortlist
   reframing -- so it is still marked eligible, but in the lowest-
   confidence tier, exactly like TWSE's single-period companies were in
   the old 50-asset product (PARTIAL_COMPARABILITY, not excluded, not
   equal to the main ranking).

2. Price is tracked as a real signal here, but never a hard requirement.
   v2.38AL deliberately keeps price_status OUT of the coverage ladder,
   because Europe's confirmed 0% free price coverage (v2.38AJ) would
   otherwise make every Europe growth-ready company indistinguishable
   from one with no data at all. The same principle applies here: a
   company can be genuinely eligible on fundamentals+growth alone
   (quality/valuation/growth factors), just in a lower-confidence tier
   than one that also has real price for a momentum/technical pillar.
   PRICE_FEATURES_PARTIAL is treated as real price for this purpose (not
   PRICE_FEATURES_READY-only) -- a partial price history is still a real
   signal, unlike NOT_ATTEMPTED or a confirmed no-source finding.

3. Financial institutions are flagged for review, never silently scored
   with generic industrial ratios. The old 50-asset product's own P178
   ("financial_institution_requires_separate_factor_contract") already
   established this precedent for a single bank; this block generalizes
   it via a real, but admittedly imperfect, company-name heuristic (bank,
   bancorp, bancshares, insurance, assurance, reinsurance, savings,
   "financial group", trust/thrift). This is NOT a verified SIC/NAICS
   classification -- some real financial institutions with no such word
   in their name will be missed, and this is documented honestly as a
   known limitation, not silently assumed to be complete.

4. Every NOT_ELIGIBLE row keeps its real, already-computed reason
   (v2.38AL's own overall_coverage_status) rather than a generic
   rejection -- consistent with this project's discipline of never
   hiding why something is excluded.

This block computes zero scores, zero ranks, and zero factor values.
Phase 9C remains explicitly unauthorized.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import lzma
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38BO-global-scoring-eligibility"
COVERAGE_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38al_global_coverage_matrix/global_coverage_matrix_v2_38al.csv.xz"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bo_global_scoring_eligibility"

GROWTH_STATUSES = {"GROWTH_READY", "GROWTH_PARTIAL"}
FUNDAMENTALS_ONLY_STATUSES = {"FUNDAMENTALS_READY_NO_GROWTH_YET", "FUNDAMENTALS_PARTIAL_NO_GROWTH_YET"}
REAL_PRICE_STATUSES = {"PRICE_FEATURES_READY", "PRICE_FEATURES_PARTIAL"}

# A real-name heuristic, not a verified SIC/NAICS classification -- see
# point 3 in the module docstring. Deliberately broad (better to over-
# flag for manual review than to silently apply industrial ratios to a
# bank), never used to exclude a company, only to route it to review.
FINANCIAL_INSTITUTION_PATTERN = re.compile(r"\b(?:bank|bancorp\w*|bancshares|insurance|assurance|reinsurance|savings|financial group|trust financial|thrift)\b", re.IGNORECASE)

FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "country",
    "overall_coverage_status", "price_status", "is_financial_institution_heuristic",
    "eligibility_tier", "eligibility_reason", "phase",
]


def read_coverage(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"BLOCKED: required v2.38AL global coverage matrix not found: {path}")
    opener = lzma.open if path.suffix == ".xz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def is_financial_institution(company_name: str) -> bool:
    return bool(FINANCIAL_INSTITUTION_PATTERN.search(company_name or ""))


def classify(row: dict[str, str]) -> tuple[str, str]:
    status = row.get("overall_coverage_status", "")
    financial = is_financial_institution(row.get("company_name", ""))

    if status in GROWTH_STATUSES:
        if financial:
            return "REVIEW_REQUIRED_FINANCIAL_INSTITUTION", "real_growth_data_but_financial_institution_needs_separate_factor_contract"
        if row.get("price_status") in REAL_PRICE_STATUSES:
            return "ELIGIBLE_FULL", "real_identity_fundamentals_growth_and_price"
        return "ELIGIBLE_PARTIAL_NO_PRICE", "real_identity_fundamentals_growth_but_no_real_price_signal"
    if status in FUNDAMENTALS_ONLY_STATUSES:
        if financial:
            return "REVIEW_REQUIRED_FINANCIAL_INSTITUTION", "real_fundamentals_but_financial_institution_needs_separate_factor_contract"
        return "ELIGIBLE_PARTIAL_SINGLE_PERIOD", "real_fundamentals_present_but_no_year_over_year_growth_evidence_yet"
    return "NOT_ELIGIBLE", status.lower()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build(coverage_path: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    coverage_rows = read_coverage(coverage_path)

    rows: list[dict[str, Any]] = []
    for row in coverage_rows:
        tier, reason = classify(row)
        rows.append({
            "asset_id": row.get("asset_id", ""), "ticker": row.get("ticker", ""), "company_name": row.get("company_name", ""),
            "exchange": row.get("exchange", ""), "country": row.get("country", ""),
            "overall_coverage_status": row.get("overall_coverage_status", ""), "price_status": row.get("price_status", ""),
            "is_financial_institution_heuristic": is_financial_institution(row.get("company_name", "")),
            "eligibility_tier": tier, "eligibility_reason": reason, "phase": PHASE,
        })

    write_csv(output_dir / "global_scoring_eligibility_v2_38bo.csv", rows, FIELDS)

    tier_counts = Counter(r["eligibility_tier"] for r in rows)
    not_eligible_reason_counts = Counter(r["eligibility_reason"] for r in rows if r["eligibility_tier"] == "NOT_ELIGIBLE")
    by_country_eligible = Counter(r["country"] for r in rows if r["eligibility_tier"].startswith("ELIGIBLE"))

    report = {
        "phase": PHASE,
        "status": "COMPLETED_GLOBAL_SCORING_ELIGIBILITY_DEFINED_NOT_SCORED",
        "companies_total": len(rows),
        "eligibility_tier_counts": dict(sorted(tier_counts.items())),
        "not_eligible_reason_counts": dict(sorted(not_eligible_reason_counts.items())),
        "eligible_by_country_top": dict(sorted(by_country_eligible.items(), key=lambda kv: -kv[1])[:10]),
        "note": "Defines who is structurally eligible for a future scoring phase -- computes zero scores, zero ranks, zero factor values. ELIGIBLE_FULL requires the real identity->fundamentals->growth ladder (v2.38AL) plus a real price signal (PRICE_FEATURES_READY/PARTIAL, never just attempted). ELIGIBLE_PARTIAL_NO_PRICE has the full growth ladder but no real price -- deliberately not penalized for Europe's confirmed 0% free price coverage (v2.38AJ) or for the new US Cboe-secondary population's not-yet-attempted price. ELIGIBLE_PARTIAL_SINGLE_PERIOD has real fundamentals but no year-over-year growth evidence, the lowest-confidence eligible tier, same spirit as the old 50-asset product's TWSE PARTIAL_COMPARABILITY treatment. REVIEW_REQUIRED_FINANCIAL_INSTITUTION flags real companies (via an admittedly imperfect company-name heuristic, not a verified SIC/NAICS classification) that need a separate factor contract before generic industrial ratios could ever apply to them -- same precedent as the old product's own P178 exception, generalized. NOT_ELIGIBLE always keeps the real, already-computed v2.38AL reason, never a generic rejection.",
        "guardrails": {"network_used": False, "scoring_calculated": False, "ranking_calculated": False, "recommendations_generated": False, "phase9c_authorized": False},
    }
    write_text(output_dir / "global_scoring_eligibility_report_v2_38bo.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest = {"phase": PHASE, "outputs": {"global_scoring_eligibility_v2_38bo.csv": {"bytes": (output_dir / "global_scoring_eligibility_v2_38bo.csv").stat().st_size, "sha256": sha256(output_dir / "global_scoring_eligibility_v2_38bo.csv")}}, "guardrails": report["guardrails"]}
    write_text(output_dir / "global_scoring_eligibility_manifest_v2_38bo.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-input", type=Path, default=COVERAGE_INPUT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.coverage_input, args.output_dir)
    print(json.dumps({k: report[k] for k in ("phase", "status", "companies_total", "eligibility_tier_counts")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
