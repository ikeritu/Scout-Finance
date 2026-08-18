#!/usr/bin/env python3
"""Read-only eligibility-input audit for the v2.33A Scout Finance universe."""
from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path

import pandas as pd

EXPECTED_ROWS = 43_089
EXPECTED_SHA256 = "4cbde1e534ccf145542e6d0bd0c1f5aec7dba4d43037aea5f115e1ea9b46d6bf"

TYPE_BUCKETS = {
    "common_equity_candidate": {
        "COMMON_STOCK", "EQTY", "CS", "EQUITY", "EQUITY_COMMON_OR_EQUITY_LIKE",
        "EQUITY_LIKE", "EQUITY_LIKE_REIT", "REIT", "EQUITY_LIKE_TRUST",
        "COLOMBIA_EQUITY_PRICE_SECURITY",
    },
    "depositary_receipt_candidate": {"ADR", "DR"},
    "fund_or_note": {"ETF", "ETC", "ETN"},
    "conditional_investment_vehicle": {"LISTED_INVESTMENT_VEHICLE"},
    "provider_specific_unresolved": {"COLOMBIA_REGISTERED_BVC_SECURITY"},
    "unclassified": {"", "UNKNOWN_PENDING_CLASSIFICATION"},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def normalize_type(value: str) -> str:
    token = value.strip().upper()
    for bucket, values in TYPE_BUCKETS.items():
        if token in values:
            return bucket
    return "provider_specific_unresolved"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--skip-known-hash", action="store_true")
    args = parser.parse_args()

    input_sha = sha256(args.input)
    if not args.skip_known_hash and input_sha != EXPECTED_SHA256:
        raise SystemExit(f"Unexpected input SHA-256: {input_sha}")
    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    if len(df) != EXPECTED_ROWS:
        raise SystemExit(f"Unexpected row count: {len(df)}")
    for column in df.columns:
        df[column] = clean(df[column])

    audit = pd.DataFrame(index=df.index)
    audit["row_number"] = df.index + 2
    for column in ("ticker", "company_name", "exchange", "country", "source_provider", "instrument_type", "isin", "currency"):
        audit[column] = df[column]
    audit["type_bucket_v2_33a"] = df["instrument_type"].map(normalize_type)
    audit["missing_ticker"] = df["ticker"].eq("")
    audit["missing_company_name"] = df["company_name"].eq("")
    audit["missing_country"] = df["country"].eq("")
    audit["missing_isin"] = df["isin"].eq("")
    audit["missing_currency"] = df["currency"].eq("")
    audit["missing_sector"] = df["sector"].eq("")
    audit["missing_industry"] = df["industry"].eq("")
    audit["missing_market_cap"] = df["market_cap"].eq("")
    audit["duplicate_exchange_ticker"] = df["ticker"].ne("") & df.duplicated(["exchange", "ticker"], keep=False)
    audit["duplicate_isin_cross_listing_candidate"] = df["isin"].ne("") & df.duplicated("isin", keep=False)
    audit["identity_complete"] = ~audit[["missing_ticker", "missing_company_name"]].any(axis=1)
    audit["financial_coverage_fields_present"] = (~audit[["missing_currency", "missing_sector", "missing_industry", "missing_market_cap"]]).sum(axis=1)
    audit["v2_33a_status"] = "audited_pending_eligibility_policy_v2_33b"

    def counts(column: str) -> dict[str, int]:
        return {str(k): int(v) for k, v in df[column].value_counts(dropna=False).items()}

    missing = {column: int(df[column].eq("").sum()) for column in (
        "ticker", "company_name", "country", "isin", "currency", "sector", "industry", "market_cap"
    )}
    bucket_counts = {str(k): int(v) for k, v in audit["type_bucket_v2_33a"].value_counts().items()}
    duplicate_isin_rows = int(audit["duplicate_isin_cross_listing_candidate"].sum())
    summary = {
        "phase": "v2.33A",
        "status": "PASS",
        "scope": "read_only_universe_type_duplicate_and_coverage_audit",
        "input": {"rows": len(df), "columns": len(df.columns), "sha256": input_sha},
        "rows_audited": len(audit),
        "type_buckets": bucket_counts,
        "source_instrument_types": counts("instrument_type"),
        "providers": counts("source_provider"),
        "missing_fields": missing,
        "identity": {
            "complete_rows": int(audit["identity_complete"].sum()),
            "incomplete_rows": int((~audit["identity_complete"]).sum()),
            "duplicate_exchange_ticker_rows": int(audit["duplicate_exchange_ticker"].sum()),
            "duplicate_exchange_ticker_groups": int(df[df["ticker"].ne("")].groupby(["exchange", "ticker"]).size().gt(1).sum()),
            "duplicate_isin_rows": duplicate_isin_rows,
            "duplicate_isin_groups": int(df[df["isin"].ne("")].groupby("isin").size().gt(1).sum()),
            "duplicate_isin_interpretation": "cross_listing_or_duplicate_candidate_requires_v2_33b_review",
        },
        "financial_coverage": {
            "rows_with_market_cap": len(df) - missing["market_cap"],
            "rows_with_sector": len(df) - missing["sector"],
            "rows_with_industry": len(df) - missing["industry"],
            "rows_with_currency": len(df) - missing["currency"],
            "fundamental_scoring_possible_from_current_catalog_alone": False,
        },
        "decisions_deferred_to_v2_33b": [
            "final_eligibility_by_instrument_type",
            "cross_listing_and_isin_deduplication_policy",
            "treatment_of_missing_ticker_or_company_name",
        ],
        "production_scoring_authorized": False,
        "allow_ranking": False,
        "input_modified": False,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit_csv = audit.to_csv(index=False).encode("utf-8")
    with lzma.open(args.output_dir / "universe_row_audit_v2_33a.csv.xz", "wb", preset=9) as handle:
        handle.write(audit_csv)
    (args.output_dir / "audit_summary_v2_33a.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("PASS: v2.33A/43089/read-only/type-normalization/duplicates/coverage/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
