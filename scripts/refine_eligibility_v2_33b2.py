#!/usr/bin/env python3
"""Refine v2.33B eligibility using full-population name and provider preflight rules."""
from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import re
from pathlib import Path

import pandas as pd

EXPECTED_INPUT_SHA256 = "a073209d4e12257e5408439e5352d3cd7d9e61fe928bc13e5d19249352685cca"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_census", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--skip-known-hash", action="store_true")
    args = parser.parse_args()
    input_sha = sha256(args.input_census)
    if not args.skip_known_hash and input_sha != EXPECTED_INPUT_SHA256:
        raise SystemExit(f"Unexpected v2.33B census SHA-256: {input_sha}")
    with lzma.open(args.input_census, "rt", encoding="utf-8") as handle:
        census = pd.read_csv(handle, dtype=str, keep_default_na=False)
    if len(census) != 43_089:
        raise SystemExit(f"Unexpected row count: {len(census)}")

    result = census.copy()
    prior_eligible = result["eligibility_decision_v2_33b"].eq("eligible_for_financial_enrichment")
    names = result["company_name"].str.upper().str.strip()
    decision = result["eligibility_decision_v2_33b"].copy()
    reason = result["eligibility_reason_v2_33b"].copy()

    rules = [
        ("hold_provider_schema_sgx", "sgx_ticker_and_name_fields_require_source_schema_repair", result["source_provider"].eq("sgx_structured_endpoint")),
        ("hold_provider_schema_xetra", "xetra_company_name_field_contains_classification_codes", result["source_provider"].eq("deutsche_boerse_xetra_all_tradable_instruments")),
        ("excluded_invalid_placeholder", "placeholder_company_name", names.isin({"DUMMY", "TEST", "N/A", "UNKNOWN"}) | names.str.fullmatch(r"TEST[A-Z0-9._-]*", na=False)),
        ("excluded_exchange_traded_product", "company_name_indicates_etf_etn_or_exchange_traded_product", names.str.contains(r"\b(?:ETFS?|ETNS?|EXCHANGE[- ]TRADED)\b", regex=True)),
        ("excluded_non_common_preferred", "company_name_indicates_preferred_security", names.str.contains(r"\bPREFERRED\b", regex=True)),
        ("review_fund_or_trust", "company_name_indicates_fund_or_trust", names.str.contains(r"\b(?:FUNDS?|TRUSTS?)\b", regex=True)),
        ("review_spac", "company_name_indicates_acquisition_company_or_blank_check", names.str.contains(r"\b(?:ACQUISITION|BLANK CHECK)\b", regex=True)),
        ("review_warrant_right_or_unit", "company_name_indicates_warrant_right_or_unit", names.str.contains(r"\b(?:WARRANTS?|RIGHTS?|UNITS?)\b", regex=True)),
    ]
    refinements = pd.Series("", index=result.index, dtype="object")
    for new_decision, new_reason, condition in rules:
        mask = prior_eligible & refinements.eq("") & condition
        refinements.loc[mask] = new_decision
        decision.loc[mask] = new_decision
        reason.loc[mask] = new_reason

    unchanged_eligible = prior_eligible & refinements.eq("")
    decision.loc[unchanged_eligible] = "eligible_for_financial_enrichment_v2_33b2"
    reason.loc[unchanged_eligible] = "common_equity_or_depositary_receipt_passed_full_population_preflight"
    result["eligibility_decision_v2_33b2"] = decision
    result["eligibility_reason_v2_33b2"] = reason
    result["eligibility_refinement_v2_33b2"] = refinements.mask(refinements.eq(""), "unchanged_or_passed")
    result["eligible_for_financial_enrichment"] = decision.eq("eligible_for_financial_enrichment_v2_33b2")
    result["eligible_for_opportunity_ranking"] = False

    counts = {str(k): int(v) for k, v in decision.value_counts().items()}
    eligible_count = counts.get("eligible_for_financial_enrichment_v2_33b2", 0)
    excluded_statuses = {
        "excluded_from_equity_opportunity_universe", "excluded_exchange_traded_product",
        "excluded_non_common_preferred", "excluded_invalid_placeholder"
    }
    excluded_count = int(decision.isin(excluded_statuses).sum())
    review_count = len(result) - eligible_count - excluded_count
    refined_counts = {str(k): int(v) for k, v in refinements[refinements.ne("")].value_counts().items()}
    report = {
        "phase": "v2.33B2",
        "status": "PASS",
        "input_rows": len(result),
        "input_sha256": input_sha,
        "prior_eligible": int(prior_eligible.sum()),
        "refined_rows": int(refinements.ne("").sum()),
        "refinement_counts": refined_counts,
        "decision_summary": {
            "eligible_for_financial_enrichment": eligible_count,
            "excluded_from_equity_opportunity_universe": excluded_count,
            "requires_review_or_repair": review_count,
        },
        "decision_counts": counts,
        "all_rows_decided": bool(decision.ne("").all()),
        "operational_dataset_modified": False,
        "operational_pointers_modified": False,
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }
    if report["decision_summary"] != {
        "eligible_for_financial_enrichment": 21_165,
        "excluded_from_equity_opportunity_universe": 10_432,
        "requires_review_or_repair": 11_492,
    }:
        raise SystemExit(f"Unexpected refined counts: {report['decision_summary']}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    encoded = result.to_csv(index=False).encode("utf-8")
    final_census = args.output_dir / "eligibility_census_v2_33b2.csv.xz"
    temporary_census = args.output_dir / "eligibility_census_v2_33b2.csv.xz.tmp"
    with lzma.open(temporary_census, "wb", preset=9) as handle:
        handle.write(encoded)
    # Validate a complete XZ stream before replacing the previous artifact.
    with lzma.open(temporary_census, "rb") as handle:
        if len(handle.read()) != len(encoded):
            raise SystemExit("Compressed census verification failed")
    temporary_census.replace(final_census)
    (args.output_dir / "eligibility_refinement_report_v2_33b2.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("PASS: v2.33B2/43089/21165-enrichment/10432-excluded/11492-review/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
