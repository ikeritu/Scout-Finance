#!/usr/bin/env python3
"""Resolve only deterministic EODHD symbols; leave ambiguous listings blocked."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

EXPECTED_SAMPLE_SHA256 = "b4c8c49cc5ecc7006049b5dfb69f98eb79236d7313ad30e874a14d57afc8fb5c"
US_EXCHANGES = {"NASDAQ", "NYSE", "NYSE American", "NYSE Arca", "Cboe BZX"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve(row: dict[str, str]) -> tuple[str, str, str]:
    ticker, exchange = row["ticker"].strip(), row["exchange"].strip()
    if exchange in US_EXCHANGES:
        return f"{ticker}.US", "resolved_deterministic", "official_unified_us_exchange_code"
    if exchange == "ASX" and ticker.upper().endswith(".AX"):
        return f"{ticker[:-3]}.AU", "resolved_deterministic", "official_asx_au_suffix"
    if exchange == "TWSE" and ticker.upper().endswith(".TW"):
        return ticker, "resolved_deterministic", "official_taiwan_tw_suffix"
    if exchange == "CBOE_EUROPE":
        return "", "unresolved", "cross_listing_requires_home_exchange_or_identifier_mapping"
    if exchange == "JPX":
        return "", "unresolved", "requires_eodhd_exchange_catalog_confirmation"
    if exchange == "BVC":
        return "", "unresolved", "requires_provider_search_or_identifier_mapping"
    return "", "unresolved", "no_approved_deterministic_rule"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--skip-known-hash", action="store_true")
    args = parser.parse_args()
    source_sha = sha256(args.sample)
    if not args.skip_known_hash and EXPECTED_SAMPLE_SHA256 != "PLACEHOLDER" and source_sha != EXPECTED_SAMPLE_SHA256:
        raise SystemExit(f"Unexpected pilot sample SHA-256: {source_sha}")
    with args.sample.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        symbol, status, reason = resolve(row)
        row["provider_symbol"] = symbol
        row["provider_symbol_status"] = status
        row["provider_symbol_reason"] = reason
        row["price_collection_status"] = "ready_pending_authorized_api_token" if status.startswith("resolved") else "blocked_pending_provider_mapping"
    if len(rows) != 240 or len({row["pilot_id"] for row in rows}) != 240:
        raise SystemExit("Expected 240 unique pilot rows")
    resolved = sum(row["provider_symbol_status"].startswith("resolved") for row in rows)
    unresolved = len(rows) - resolved
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "price_pilot_symbols_v2_33d.csv"
    fields = list(rows[0])
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    report = {
        "phase": "v2.33D-symbol-resolution",
        "status": "PARTIAL_FAIL_CLOSED",
        "input_rows": len(rows),
        "resolved_deterministic": resolved,
        "unresolved": unresolved,
        "resolved_by_market": {
            exchange: sum(row["exchange"] == exchange and row["provider_symbol_status"].startswith("resolved") for row in rows)
            for exchange in sorted({row["exchange"] for row in rows})
        },
        "unresolved_reasons": {
            reason: sum(row["provider_symbol_reason"] == reason for row in rows)
            for reason in sorted({row["provider_symbol_reason"] for row in rows if row["provider_symbol_status"] == "unresolved"})
        },
        "network_calls": 0,
        "credentials_used": False,
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }
    (args.output_dir / "symbol_resolution_report_v2_33d.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("PASS: v2.33D-symbols/deterministic-only/ambiguous-blocked/no-network/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
