#!/usr/bin/env python3
"""Build the deterministic phase-9B acquisition census without network calls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import lzma
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/global_enrichment_contract_v1.json"
OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38b_global_enrichment"
FIELDS = ["asset_id", "ticker", "exchange", "eligibility_status", "identity_status", "provider_route", "price_provider", "fundamental_provider", "license_status", "provider_symbol", "symbol_resolution_status", "acquisition_status", "batch_eligible", "blocker_reason", "attempt_count", "last_success_date", "evidence_hash", "phase"]
KNOWN_JPX_SYMBOLS = ROOT / "outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/jquants_symbol_resolution_v2_33g.csv"
JPX_RESOLUTION_OVERLAY = OUTPUT / "jpx_symbol_resolution_overlay_25_v2_38b.csv"

MARKET_POLICY = {
    "JPX": ("J-Quants", "J-Quants", "personal_use_confirmed", "PROVIDER_LOOKUP_REQUIRED", "SYMBOL_RESOLUTION_REQUIRED", "exact catalog and company-name match required before acquisition"),
    "TWSE": ("TWSE official open data", "TWSE MOPS", "open_government_data", "DETERMINISTIC_RULE_AVAILABLE", "READY_FOR_CONTROLLED_BATCH", "pilot validated; prices remain unadjusted and publication dates incomplete"),
    "NASDAQ": ("Twelve Data candidate", "unresolved", "cache_terms_unresolved", "PROVIDER_LOOKUP_REQUIRED", "USER_ACTION_REQUIRED", "account, credential, license confirmation and pilot required"),
    "NYSE": ("Twelve Data candidate", "unresolved", "cache_terms_unresolved", "PROVIDER_LOOKUP_REQUIRED", "USER_ACTION_REQUIRED", "account, credential, license confirmation and pilot required"),
    "NYSE American": ("Twelve Data candidate", "unresolved", "cache_terms_unresolved", "PROVIDER_LOOKUP_REQUIRED", "USER_ACTION_REQUIRED", "account, credential, license confirmation and pilot required"),
    "Cboe BZX": ("Twelve Data candidate", "unresolved", "cache_terms_unresolved", "PROVIDER_LOOKUP_REQUIRED", "USER_ACTION_REQUIRED", "account, credential, license confirmation and pilot required"),
    "CBOE_EUROPE": ("none actionable", "unresolved", "not_applicable", "BLOCKED", "SOURCE_RESEARCH_REQUIRED", "home market mapping and actionable source unavailable"),
    "ASX": ("none free", "unresolved", "paid_license_required", "BLOCKED", "LICENSE_BLOCKED", "official historical distribution requires payment"),
    "BVC": ("SFC summary only", "unresolved", "insufficient", "BLOCKED", "SOURCE_RESEARCH_REQUIRED", "validated daily series unavailable"),
    "XETR": ("not evaluated", "unresolved", "not_evaluated", "BLOCKED", "METADATA_REPAIR_REQUIRED", "v2.33B2 schema hold"),
    "SGX": ("not evaluated", "unresolved", "not_evaluated", "BLOCKED", "METADATA_REPAIR_REQUIRED", "v2.33B2 schema hold"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_hash(row: dict[str, str], policy: tuple[str, ...]) -> str:
    payload = "\x1f".join([row["asset_id"], row["ticker"], row["exchange"], row["eligibility_status"], *policy])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def classify(row: dict[str, str], known_jpx: dict[str, str]) -> dict:
    fallback = ("not evaluated", "unresolved", "not_evaluated", "BLOCKED", "SOURCE_RESEARCH_REQUIRED", "market route not evaluated")
    policy = MARKET_POLICY.get(row["exchange"], fallback)
    price, fundamentals, license_status, symbol_status, acquisition_status, blocker = policy
    provider_symbol = ""
    if row["exchange"] == "JPX" and row["ticker"] in known_jpx:
        provider_symbol = known_jpx[row["ticker"]]
        symbol_status, acquisition_status, blocker = "DETERMINISTIC_RULE_AVAILABLE", "READY_FOR_CONTROLLED_BATCH", "resolved by exact J-Quants catalog match in v2.33G"
    elif row["exchange"] == "TWSE" and row["eligibility_status"] == "ELIGIBLE":
        provider_symbol = row["ticker"].removesuffix(".TW")
    if row["eligibility_status"] == "EXCLUDED":
        symbol_status, acquisition_status, blocker = "NOT_APPLICABLE", "NOT_ELIGIBLE", row["blocker_reason"]
    elif row["eligibility_status"] == "REVIEW":
        symbol_status, acquisition_status, blocker = "BLOCKED", "REVIEW_REQUIRED", row["blocker_reason"]
    elif row["eligibility_status"] == "BLOCKED":
        symbol_status, acquisition_status, blocker = "BLOCKED", "METADATA_REPAIR_REQUIRED", row["blocker_reason"]
    batch_eligible = acquisition_status == "READY_FOR_CONTROLLED_BATCH" and row["identity_status"] == "COMPLETE"
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "exchange": row["exchange"],
        "eligibility_status": row["eligibility_status"], "identity_status": row["identity_status"],
        "provider_route": row["route_status"], "price_provider": price, "fundamental_provider": fundamentals,
        "license_status": license_status, "provider_symbol": provider_symbol, "symbol_resolution_status": symbol_status,
        "acquisition_status": acquisition_status, "batch_eligible": str(batch_eligible).lower(),
        "blocker_reason": blocker, "attempt_count": 0, "last_success_date": "",
        "evidence_hash": evidence_hash(row, policy), "phase": "v2.38B",
    }


def write_csv(path: Path, rows: list[dict], fields: list[str] = FIELDS, compressed: bool = False) -> None:
    ctx = lzma.open(path, "wt", encoding="utf-8", newline="") if compressed else path.open("w", encoding="utf-8", newline="")
    with ctx as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    source = ROOT / contract["input_manifest"]
    actual_hash = sha256(source)
    if actual_hash != contract["input_sha256"]:
        raise SystemExit(f"BLOCKED: v2.38A input hash mismatch: {actual_hash}")
    with lzma.open(source, "rt", encoding="utf-8", newline="") as f:
        source_rows = list(csv.DictReader(f))
    if len(source_rows) != contract["expected_rows"]:
        raise SystemExit("BLOCKED: input row count mismatch")
    with KNOWN_JPX_SYMBOLS.open(encoding="utf-8", newline="") as f:
        known_jpx = {r["ticker"]: r["provider_symbol"] for r in csv.DictReader(f) if r["status"].startswith("resolved") and r["provider_symbol"]}
    with JPX_RESOLUTION_OVERLAY.open(encoding="utf-8", newline="") as f:
        overlay = list(csv.DictReader(f))
    if len(known_jpx) != 42 or not 25 <= len(overlay) <= 3659:
        raise SystemExit("BLOCKED: expected 42 prior and 25..3659 overlay JPX resolutions")
    if any(r["resolution_status"] != "EXACT_COMPANY_NAME_MATCH" or not r["provider_symbol"] for r in overlay):
        raise SystemExit("BLOCKED: JPX overlay contains a non-exact or empty resolution")
    overlay_jpx = {r["ticker"]: r["provider_symbol"] for r in overlay}
    if len(overlay_jpx) != len(overlay) or set(known_jpx) & set(overlay_jpx):
        raise SystemExit("BLOCKED: JPX overlay contains duplicate or previously known tickers")
    known_jpx.update(overlay_jpx)
    if len(known_jpx) != 42 + len(overlay):
        raise SystemExit("BLOCKED: verified JPX total does not match prior plus overlay")
    rows = [classify(row, known_jpx) for row in source_rows]
    if len(rows) != len({row["asset_id"] for row in rows}):
        raise SystemExit("BLOCKED: duplicate asset identity")
    if sum(r["eligibility_status"] == "ELIGIBLE" for r in rows) != contract["expected_eligible_rows"]:
        raise SystemExit("BLOCKED: eligible count mismatch")
    args.output.mkdir(parents=True, exist_ok=True)
    detailed = args.output / "global_acquisition_manifest_v2_38b.csv.xz"
    write_csv(detailed, rows, compressed=True)

    markets = []
    for exchange in sorted({r["exchange"] for r in rows}):
        subset = [r for r in rows if r["exchange"] == exchange]
        eligible_subset = [r for r in subset if r["eligibility_status"] == "ELIGIBLE"]
        representative = eligible_subset[0] if eligible_subset else subset[0]
        statuses = Counter(r["acquisition_status"] for r in (eligible_subset or subset))
        markets.append({
            "exchange": exchange, "rows": len(subset), "eligible_rows": sum(r["eligibility_status"] == "ELIGIBLE" for r in subset),
            "batch_eligible_rows": sum(r["batch_eligible"] == "true" for r in subset),
            "primary_status": statuses.most_common(1)[0][0], "price_provider": representative["price_provider"],
            "fundamental_provider": representative["fundamental_provider"], "license_status": representative["license_status"],
            "pilot_required": "true", "real_collection_authorized": "false", "blocker": representative["blocker_reason"],
        })
    market_fields = ["exchange", "rows", "eligible_rows", "batch_eligible_rows", "primary_status", "price_provider", "fundamental_provider", "license_status", "pilot_required", "real_collection_authorized", "blocker"]
    write_csv(args.output / "market_acquisition_plan_v2_38b.csv", markets, market_fields)

    jpx_ready = [r for r in rows if r["exchange"] == "JPX" and r["batch_eligible"] == "true"]
    write_csv(
        args.output / "jpx_verified_symbols_v2_38b.csv",
        [{"pilot_id": r["asset_id"], "ticker": r["ticker"], "exchange": "JPX", "status": "resolved_prior_exact_match", "provider_symbol": r["provider_symbol"]} for r in jpx_ready],
        ["pilot_id", "ticker", "exchange", "status", "provider_symbol"],
    )
    jpx_unresolved = [r for r in rows if r["exchange"] == "JPX" and r["acquisition_status"] == "SYMBOL_RESOLUTION_REQUIRED"][:25]
    source_by_id = {r["asset_id"]: r for r in source_rows}
    write_csv(
        args.output / "jpx_symbol_resolution_pilot_25_v2_38b.csv",
        [{"pilot_id": r["asset_id"], "ticker": r["ticker"], "company_name": source_by_id[r["asset_id"]]["company_name"], "exchange": "JPX"} for r in jpx_unresolved],
        ["pilot_id", "ticker", "company_name", "exchange"],
    )
    twse_ready = [r for r in rows if r["exchange"] == "TWSE" and r["batch_eligible"] == "true"]
    write_csv(
        args.output / "twse_collection_pilot_25_v2_38b.csv",
        [{"pilot_id": r["asset_id"], "ticker": r["ticker"], "company_name": source_by_id[r["asset_id"]]["company_name"], "exchange": "TWSE", "provider_symbol": r["provider_symbol"]} for r in twse_ready[:25]],
        ["pilot_id", "ticker", "company_name", "exchange", "provider_symbol"],
    )

    status_counts = dict(sorted(Counter(r["acquisition_status"] for r in rows).items()))
    summary = {
        "phase": "v2.38B-global-enrichment", "status": "INFRASTRUCTURE_READY_REAL_COLLECTION_BLOCKED",
        "input_rows": len(rows), "eligible_rows": sum(r["eligibility_status"] == "ELIGIBLE" for r in rows),
        "batch_eligible_rows": sum(r["batch_eligible"] == "true" for r in rows),
        "acquisition_status_counts": status_counts, "maximum_batch_assets": contract["maximum_batch_assets"],
        "network_calls": 0, "credentials_used": False, "prices_downloaded": 0, "fundamentals_downloaded": 0,
        "scoring_calculated": False, "ranking_calculated": False, "recommendations_generated": False,
        "phase9c_authorized": False,
    }
    (args.output / "global_enrichment_summary_v2_38b.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "phase": summary["phase"], "decision": "BLOCKED_EXTERNAL_ACTIONS_AFTER_INFRASTRUCTURE_READY",
        "input": {"path": contract["input_manifest"], "sha256": actual_hash, "rows": len(source_rows)},
        "outputs": {}, "guardrails": {"network_calls": 0, "credentials_used": False, "maximum_batch_assets": 500, "phase9c_authorized": False},
    }
    for path in sorted(args.output.glob("*")):
        if path.is_file() and path.name != "global_enrichment_manifest_v2_38b.json":
            manifest["outputs"][path.name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    (args.output / "global_enrichment_manifest_v2_38b.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "rows": len(rows), "batch_eligible": summary["batch_eligible_rows"], "real_collection": "BLOCKED"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
