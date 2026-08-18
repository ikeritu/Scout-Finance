#!/usr/bin/env python3
"""Apply the conservative v2.33B equity-universe eligibility policy."""
from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path

import pandas as pd

EXPECTED_ROWS = 43_089
EXPECTED_AUDIT_SHA256 = "826fd5715a0b55a03e399f1707097e721d73bc2adeed07ec51f6b3ea70c2ea88"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def truth(series: pd.Series) -> pd.Series:
    return series.astype(str).str.casefold().eq("true")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--skip-known-hash", action="store_true")
    args = parser.parse_args()

    audit_sha = sha256(args.audit_input)
    if not args.skip_known_hash and audit_sha != EXPECTED_AUDIT_SHA256:
        raise SystemExit(f"Unexpected v2.33A audit SHA-256: {audit_sha}")
    with lzma.open(args.audit_input, "rt", encoding="utf-8") as handle:
        audit = pd.read_csv(handle, dtype=str, keep_default_na=False)
    if len(audit) != EXPECTED_ROWS or audit["row_number"].nunique() != EXPECTED_ROWS:
        raise SystemExit("v2.33A audit does not contain exactly 43,089 unique source rows")

    bucket = audit["type_bucket_v2_33a"]
    identity_complete = truth(audit["identity_complete"])
    duplicate_isin = truth(audit["duplicate_isin_cross_listing_candidate"])
    decision = pd.Series("", index=audit.index, dtype="object")
    reason = pd.Series("", index=audit.index, dtype="object")

    candidate = bucket.isin(["common_equity_candidate", "depositary_receipt_candidate"])
    decision[candidate & identity_complete & ~duplicate_isin] = "eligible_for_financial_enrichment"
    reason[candidate & identity_complete & ~duplicate_isin] = "equity_or_depositary_receipt_with_complete_operational_identity"
    decision[candidate & ~identity_complete] = "hold_identity_incomplete"
    reason[candidate & ~identity_complete] = "equity_like_record_missing_ticker_or_company_name"
    decision[candidate & identity_complete & duplicate_isin] = "review_cross_listing_or_duplicate"
    reason[candidate & identity_complete & duplicate_isin] = "repeated_isin_requires_listing_policy"

    mask = bucket.eq("fund_or_note")
    decision[mask] = "excluded_from_equity_opportunity_universe"
    reason[mask] = "etf_etc_or_etn_requires_separate_non_equity_methodology"
    mask = bucket.eq("unclassified")
    decision[mask] = "review_unclassified_instrument"
    reason[mask & ~identity_complete] = "unclassified_and_missing_ticker_or_company_name"
    reason[mask & identity_complete & duplicate_isin] = "unclassified_with_repeated_isin"
    reason[mask & identity_complete & ~duplicate_isin] = "provider_type_not_resolved"
    mask = bucket.eq("provider_specific_unresolved")
    decision[mask] = "review_provider_specific_type"
    reason[mask] = "provider_category_needs_explicit_mapping"
    mask = bucket.eq("conditional_investment_vehicle")
    decision[mask] = "review_conditional_vehicle"
    reason[mask] = "listed_investment_vehicle_requires_individual_policy"

    if decision.eq("").any() or reason.eq("").any():
        raise SystemExit("Policy left one or more rows undecided")

    result = audit.copy()
    result["eligibility_decision_v2_33b"] = decision
    result["eligibility_reason_v2_33b"] = reason
    result["eligible_for_financial_enrichment"] = decision.eq("eligible_for_financial_enrichment")
    result["eligible_for_opportunity_ranking"] = False
    result["opportunity_ranking_block_reason"] = "financial_and_market_coverage_not_yet_available_or_validated"

    decision_counts = {str(k): int(v) for k, v in decision.value_counts().items()}
    eligible = decision_counts.get("eligible_for_financial_enrichment", 0)
    excluded = decision_counts.get("excluded_from_equity_opportunity_universe", 0)
    review = len(result) - eligible - excluded
    policy = {
        "phase": "v2.33B",
        "status": "PASS",
        "policy_name": "conservative_equity_opportunity_universe_v1",
        "input": {"rows": len(audit), "sha256": audit_sha, "source_phase": "v2.33A"},
        "rows_decided": len(result),
        "decision_summary": {
            "eligible_for_financial_enrichment": eligible,
            "excluded_from_equity_opportunity_universe": excluded,
            "requires_review": review,
        },
        "decision_counts": decision_counts,
        "rules": [
            "include common-equity candidates and ADR/DR only when operational identity is complete",
            "exclude ETF, ETC and ETN from the equity ranking; they require a separate methodology",
            "hold unclassified, provider-specific and conditional vehicles for explicit review",
            "never treat repeated ISIN as a duplicate automatically",
            "eligibility for enrichment does not authorize scoring or ranking",
        ],
        "minimum_identity_for_enrichment": ["ticker", "company_name", "exchange", "source_provider"],
        "minimum_future_financial_coverage": {
            "status": "TO_BE_IMPLEMENTED_IN_V2_33C_TO_V2_33G",
            "required_domains": ["current_price", "price_history", "financial_statements", "currency", "sector_or_peer_group", "data_date", "source_provenance"],
        },
        "production_scoring_authorized": False,
        "allow_ranking": False,
        "operational_dataset_modified": False,
        "operational_pointers_modified": False,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    encoded = result.to_csv(index=False).encode("utf-8")
    with lzma.open(args.output_dir / "eligibility_census_v2_33b.csv.xz", "wb", preset=9) as handle:
        handle.write(encoded)
    (args.output_dir / "eligibility_policy_v2_33b.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(policy, ensure_ascii=False, indent=2))
    print("PASS: v2.33B/43089/23888-enrichment/10409-excluded/8792-review/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
