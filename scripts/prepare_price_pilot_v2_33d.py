#!/usr/bin/env python3
"""Create the deterministic, stratified 240-asset v2.33D price pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import re
from pathlib import Path

import pandas as pd

EXPECTED_INPUT_SHA256 = "a073209d4e12257e5408439e5352d3cd7d9e61fe928bc13e5d19249352685cca"
TARGET = 240


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def proportional_quotas(counts: pd.Series, target: int) -> dict[str, int]:
    raw = counts / counts.sum() * target
    quotas = raw.apply(int).clip(lower=1)
    while quotas.sum() < target:
        key = (raw - quotas).idxmax()
        quotas[key] += 1
    while quotas.sum() > target:
        candidates = quotas[quotas > 1]
        key = (quotas[candidates.index] - raw[candidates.index]).idxmax()
        quotas[key] -= 1
    return {str(k): int(v) for k, v in quotas.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("eligibility_census", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--skip-known-hash", action="store_true")
    args = parser.parse_args()
    source_sha = sha256(args.eligibility_census)
    if not args.skip_known_hash and source_sha != EXPECTED_INPUT_SHA256:
        raise SystemExit(f"Unexpected v2.33B census SHA-256: {source_sha}")
    with lzma.open(args.eligibility_census, "rt", encoding="utf-8") as handle:
        census = pd.read_csv(handle, dtype=str, keep_default_na=False)
    eligible = census[census["eligibility_decision_v2_33b"].eq("eligible_for_financial_enrichment")].copy()
    if len(eligible) != 23_888:
        raise SystemExit(f"Unexpected eligible population: {len(eligible)}")

    counts = eligible["source_provider"].value_counts().sort_index()
    quotas = proportional_quotas(counts, TARGET)
    parts = []
    for provider, quota in quotas.items():
        group = eligible[eligible["source_provider"].eq(provider)].sort_values(
            ["exchange", "ticker", "company_name", "row_number"], kind="stable"
        )
        # Deterministic coverage across the full sorted provider range.
        positions = [round(i * (len(group) - 1) / max(quota - 1, 1)) for i in range(quota)]
        parts.append(group.iloc[positions])
    sample = pd.concat(parts, ignore_index=True).sort_values(
        ["source_provider", "exchange", "ticker", "row_number"], kind="stable"
    )
    sample.insert(0, "pilot_id", [f"P{i:03d}" for i in range(1, len(sample) + 1)])
    sample["provider_symbol_status"] = "pending_provider_mapping"
    sample["provider_symbol"] = ""
    sample["price_collection_status"] = "blocked_pending_authorized_api_token"
    names = sample["company_name"].str.upper()
    tickers = sample["ticker"].str.strip()
    reasons = pd.Series("", index=sample.index, dtype="object")

    def add_reason(mask: pd.Series, label: str) -> None:
        nonlocal reasons
        reasons.loc[mask] = reasons.loc[mask].map(lambda current: f"{current}|{label}".strip("|"))

    add_reason(names.isin({"DUMMY", "TEST", "N/A", "UNKNOWN"}), "placeholder_company_name")
    numeric_ticker = tickers.map(lambda value: bool(re.fullmatch(r"\d+(?:\.\d+)?", value)))
    add_reason(numeric_ticker & sample["source_provider"].eq("sgx_structured_endpoint"), "numeric_ticker_suspected_field_shift")
    add_reason(names.str.contains(r"\b(?:ETF|ETN|EXCHANGE[- ]TRADED)\b", regex=True), "name_indicates_exchange_traded_product")
    add_reason(names.str.contains(r"\b(?:ACQUISITION CORP|ACQUISITION CORPORATION|BLANK CHECK)\b", regex=True), "name_indicates_spac")
    add_reason(names.str.contains(r"\b(?:FUND|TRUST)\b", regex=True) & ~names.str.contains(r"\bREIT\b", regex=True), "name_indicates_fund_or_trust_review")
    sample["eligibility_preflight_status"] = reasons.eq("").map({True: "pass", False: "review"})
    sample["eligibility_preflight_reasons"] = reasons
    sample.loc[reasons.ne(""), "price_collection_status"] = "blocked_pending_eligibility_correction"
    keep = [
        "pilot_id", "row_number", "ticker", "company_name", "exchange", "country",
        "source_provider", "instrument_type", "type_bucket_v2_33a", "provider_symbol_status",
        "provider_symbol", "eligibility_preflight_status", "eligibility_preflight_reasons", "price_collection_status"
    ]
    sample = sample[keep]
    if len(sample) != TARGET or sample["row_number"].nunique() != TARGET:
        raise SystemExit("Pilot selection is not exactly 240 unique source rows")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    sample_path = args.output_dir / "price_pilot_sample_v2_33d.csv"
    sample.to_csv(sample_path, index=False)
    manifest = {
        "phase": "v2.33D",
        "status": "READY_FOR_AUTHORIZED_PILOT_NOT_EXECUTED",
        "population": 23_888,
        "sample_rows": len(sample),
        "sample_strategy": "deterministic_proportional_by_source_provider_with_range_spread",
        "provider_quotas": quotas,
        "source_sha256": source_sha,
        "sample_sha256": sha256(sample_path),
        "identity_mapping_complete": False,
        "eligibility_preflight": {
            "pass_rows": int(sample["eligibility_preflight_status"].eq("pass").sum()),
            "review_rows": int(sample["eligibility_preflight_status"].eq("review").sum()),
            "reason_counts": {
                reason: int(sample["eligibility_preflight_reasons"].str.split("|").map(lambda values: reason in values).sum())
                for reason in sorted({reason for value in reasons if value for reason in value.split("|")})
            },
            "v2_33b_reopen_required": bool(reasons.ne("").any())
        },
        "authorized_api_token_present": False,
        "network_collection_executed": False,
        "price_rows_collected": 0,
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }
    (args.output_dir / "price_pilot_manifest_v2_33d.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("PASS: v2.33D-preparation/23888-population/240-stratified/preflight/fail-closed/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
