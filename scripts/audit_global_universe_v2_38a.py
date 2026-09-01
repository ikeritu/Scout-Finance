#!/usr/bin/env python3
"""Deterministic, offline census audit for Scout Finance phase 9A."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import lzma
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/global_universe_audit_contract_v1.json"
OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38a_global_universe_audit"
AUDIT_FIELDS = [
    "asset_id", "row_number", "ticker", "company_name", "exchange", "country", "mic", "currency", "isin",
    "sector", "industry", "market_cap",
    "source_provider", "instrument_type", "instrument_bucket", "identity_status", "eligibility_status",
    "enrichment_readiness", "route_status", "blocker_reason", "data_quality_flags", "audit_phase",
]

ROUTES = {
    "JPX": ("J-Quants", "PILOT_VALIDATED_NOT_SCALED", "personal_use_confirmed", "42/3701 price pilot; fundamentals only for 42 phase-5 assets"),
    "TWSE": ("TWSE official open data", "PILOT_VALIDATED_NOT_SCALED", "open_government_data", "8/696 price and fundamental pilot; prices unadjusted"),
    "NASDAQ": ("Twelve Data candidate", "USER_ACCOUNT_AND_PILOT_REQUIRED", "personal_cache_terms_unresolved", "no validated global acquisition"),
    "NYSE": ("Twelve Data candidate", "USER_ACCOUNT_AND_PILOT_REQUIRED", "personal_cache_terms_unresolved", "no validated global acquisition"),
    "NYSE American": ("Twelve Data candidate", "USER_ACCOUNT_AND_PILOT_REQUIRED", "personal_cache_terms_unresolved", "no validated global acquisition"),
    "Cboe BZX": ("Twelve Data candidate", "USER_ACCOUNT_AND_PILOT_REQUIRED", "personal_cache_terms_unresolved", "no validated global acquisition"),
    "CBOE_EUROPE": ("none actionable", "EXCLUDED_NO_ACTIONABLE_SOURCE", "not_applicable", "home exchange mapping and free source unresolved"),
    "ASX": ("none free", "EXCLUDED_NO_FREE_SOURCE", "paid_license_required", "official historical access requires paid distribution"),
    "BVC": ("SFC summary only", "EXCLUDED_INSUFFICIENT_SOURCE", "not_applicable", "no validated daily historical series"),
    "XETR": ("not evaluated", "BLOCKED_METADATA_SCHEMA", "not_evaluated", "source name field corruption retained by v2.33B2"),
    "SGX": ("not evaluated", "BLOCKED_METADATA_SCHEMA", "not_evaluated", "source schema displacement retained by v2.33B2"),
    "HKEX": ("not evaluated", "SOURCE_RESEARCH_REQUIRED", "not_evaluated", "eligible population is zero under current policy"),
    "NSE": ("not evaluated", "SOURCE_RESEARCH_REQUIRED", "not_evaluated", "eligible population is zero under current policy"),
    "CBOE": ("not evaluated", "SOURCE_RESEARCH_REQUIRED", "not_evaluated", "eligible population is zero under current policy"),
    "NYSE Arca": ("not evaluated", "SOURCE_RESEARCH_REQUIRED", "not_evaluated", "eligible population is zero under current policy"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def load_rows(path: Path) -> list[dict[str, str]]:
    with lzma.open(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def classify(row: dict[str, str], metadata: dict[str, str], eligible_value: str) -> dict[str, object]:
    decision = row["eligibility_decision_v2_33b2"]
    if decision == eligible_value:
        eligibility = "ELIGIBLE"
    elif decision.startswith("excluded_"):
        eligibility = "EXCLUDED"
    elif decision.startswith("hold_"):
        eligibility = "BLOCKED"
    else:
        eligibility = "REVIEW"

    missing_identity = [name for name in ("ticker", "company_name", "exchange", "source_provider") if not row.get(name, "").strip()]
    if eligibility == "BLOCKED" and row["exchange"] in {"XETR", "SGX"}:
        identity = "BLOCKED_SCHEMA"
    elif missing_identity:
        identity = "PARTIAL"
    else:
        identity = "COMPLETE"

    route = ROUTES.get(row["exchange"], ("not evaluated", "SOURCE_RESEARCH_REQUIRED", "not_evaluated", "market route absent"))
    if eligibility == "EXCLUDED":
        readiness = "NOT_ELIGIBLE"
        blocker = row["eligibility_reason_v2_33b2"]
    elif eligibility == "REVIEW":
        readiness = "REVIEW_REQUIRED"
        blocker = row["eligibility_reason_v2_33b2"]
    elif eligibility == "BLOCKED":
        readiness = "METADATA_REPAIR_REQUIRED"
        blocker = row["eligibility_reason_v2_33b2"]
    elif route[1] in {"PILOT_VALIDATED_NOT_SCALED", "USER_ACCOUNT_AND_PILOT_REQUIRED"}:
        readiness = "READY_FOR_SOURCE_PLANNING" if route[1] == "PILOT_VALIDATED_NOT_SCALED" else "CONDITIONAL_SOURCE"
        blocker = route[3]
    else:
        readiness = "CONDITIONAL_SOURCE"
        blocker = route[3]

    quality_flags = []
    for field in ("country", "mic", "currency", "isin", "sector", "industry", "market_cap"):
        value = metadata.get(field, "") if field in {"mic", "sector", "industry", "market_cap"} else row.get(field, "")
        if not value.strip():
            quality_flags.append(f"missing_{field}")
    return {
        "asset_id": f"U{int(row['row_number']):05d}",
        "row_number": int(row["row_number"]),
        "ticker": row["ticker"].strip(),
        "company_name": row["company_name"].strip(),
        "exchange": row["exchange"].strip(),
        "country": row["country"].strip(),
        "mic": metadata.get("mic", "").strip(),
        "currency": row["currency"].strip(),
        "isin": row["isin"].strip(),
        "sector": metadata.get("sector", "").strip(),
        "industry": metadata.get("industry", "").strip(),
        "market_cap": metadata.get("market_cap", "").strip(),
        "source_provider": row["source_provider"].strip(),
        "instrument_type": row["instrument_type"].strip(),
        "instrument_bucket": row["type_bucket_v2_33a"].strip(),
        "identity_status": identity,
        "eligibility_status": eligibility,
        "enrichment_readiness": readiness,
        "route_status": route[1],
        "blocker_reason": blocker,
        "data_quality_flags": "|".join(quality_flags),
        "audit_phase": "v2.38A",
    }


def write_csv(path: Path, fields: list[str], rows: list[dict], compressed: bool = False) -> None:
    handle_context = lzma.open(path, "wt", encoding="utf-8", newline="") if compressed else path.open("w", encoding="utf-8", newline="")
    with handle_context as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def breakdown(rows: list[dict], field: str) -> list[dict]:
    counts = Counter(str(row[field]) or "<MISSING>" for row in rows)
    total = len(rows)
    return [{field: value, "rows": count, "pct_total": round(count / total * 100, 6)} for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    contract = load_contract()
    source = ROOT / contract["canonical_dataset"]
    metadata_source = ROOT / contract["metadata_dataset"]
    actual_sha = sha256(source)
    if actual_sha != contract["canonical_sha256"]:
        raise SystemExit(f"BLOCKED: canonical SHA mismatch: {actual_sha}")
    if sha256(metadata_source) != contract["metadata_sha256"]:
        raise SystemExit("BLOCKED: metadata SHA mismatch")
    rows = load_rows(source)
    with metadata_source.open(encoding="utf-8-sig", newline="") as handle:
        metadata_rows = list(csv.DictReader(handle))
    missing_columns = sorted(set(contract["required_fields"]) - set(rows[0]))
    if missing_columns or len(rows) != contract["expected_rows"]:
        raise SystemExit(f"BLOCKED: canonical contract mismatch: rows={len(rows)} missing={missing_columns}")
    if len(metadata_rows) != len(rows) or any(
        (row["ticker"], row["company_name"], row["exchange"]) != (meta["ticker"], meta["company_name"], meta["exchange"])
        for row, meta in zip(rows, metadata_rows)
    ):
        raise SystemExit("BLOCKED: metadata row alignment mismatch")
    audited = [classify(row, meta, contract["eligible_status"]) for row, meta in zip(rows, metadata_rows)]
    if len({row["asset_id"] for row in audited}) != len(audited):
        raise SystemExit("BLOCKED: duplicate audit identity")
    if sum(row["eligibility_status"] == "ELIGIBLE" for row in audited) != contract["expected_eligible_rows"]:
        raise SystemExit("BLOCKED: eligible count mismatch")

    args.output.mkdir(parents=True, exist_ok=True)
    detailed = args.output / "global_universe_audited_v2_38a.csv.xz"
    write_csv(detailed, AUDIT_FIELDS, audited, compressed=True)

    candidate_fields = ["candidate_path", "rows", "sha256", "role", "selected"]
    candidates = [
        {"candidate_path": contract["canonical_dataset"], "rows": 43089, "sha256": actual_sha, "role": "latest refined eligibility census", "selected": "true"},
        {"candidate_path": "outputs/full_universe_source_acquisition/expanded_universe_v2_21h_activated_operational_reference.csv", "rows": 43089, "sha256": "72a02a82851c6b6e14a43944e817700010516286defd8f9984991fb4d1ea50d4", "role": "identity operational reference without current eligibility", "selected": "false"},
        {"candidate_path": "outputs/full_universe_source_acquisition/expanded_universe_v2_24f_metadata_promoted.csv", "rows": 43089, "sha256": "01fef82316a458c65d42c08cb993feed9e0cc8178f4f7bf4f08835f169bfa74c", "role": "metadata-enriched identity base without current eligibility", "selected": "false"},
    ]
    write_csv(args.output / "canonical_dataset_candidates_v2_38a.csv", candidate_fields, candidates)

    breakdown_map = {
        "country": "country", "exchange": "exchange", "mic": "mic", "currency": "currency",
        "source_provider": "source_provider", "instrument": "instrument_bucket", "eligibility": "eligibility_status",
        "readiness": "enrichment_readiness", "blocker": "blocker_reason",
    }
    for filename, field in breakdown_map.items():
        data = breakdown(audited, field)
        write_csv(args.output / f"breakdown_by_{filename}_v2_38a.csv", [field, "rows", "pct_total"], data)

    route_rows = []
    for exchange, (provider, status, license_status, limitation) in sorted(ROUTES.items()):
        exchange_rows = [row for row in audited if row["exchange"] == exchange]
        route_rows.append({
            "exchange": exchange, "rows": len(exchange_rows), "eligible_rows": sum(r["eligibility_status"] == "ELIGIBLE" for r in exchange_rows),
            "candidate_provider": provider, "route_status": status, "license_status": license_status,
            "limitation": limitation, "network_calls": 0,
        })
    route_fields = ["exchange", "rows", "eligible_rows", "candidate_provider", "route_status", "license_status", "limitation", "network_calls"]
    write_csv(args.output / "provider_route_matrix_v2_38a.csv", route_fields, route_rows)

    counts = {field: dict(sorted(Counter(str(row[field]) for row in audited).items())) for field in ("identity_status", "eligibility_status", "enrichment_readiness", "route_status")}
    metadata_fields = ("ticker", "company_name", "country", "mic", "currency", "isin", "sector", "industry", "market_cap")
    missingness = {field: sum(not str(row[field]).strip() for row in audited) for field in metadata_fields}
    summary = {
        "phase": "v2.38A-global-universe-audit", "status": "AUDITED_OFFLINE", "canonical_rows": len(audited),
        "canonical_sha256": actual_sha, "eligible_rows": counts["eligibility_status"].get("ELIGIBLE", 0),
        "counts": counts, "missingness": missingness, "network_calls": 0, "credentials_used": False, "scoring_calculated": False,
        "ranking_calculated": False, "recommendations_generated": False, "phase9b_authorized": False,
    }
    summary_path = args.output / "global_universe_summary_v2_38a.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "phase": summary["phase"], "decision": "COMPLETED_GLOBAL_CENSUS_READY_FOR_SOURCE_PLANNING",
        "input": {"path": contract["canonical_dataset"], "sha256": actual_sha, "rows": len(rows)},
        "metadata_input": {"path": contract["metadata_dataset"], "sha256": contract["metadata_sha256"], "rows": len(metadata_rows), "join": "row order verified by ticker+company_name+exchange"},
        "outputs": {}, "row_conservation": {"input": len(rows), "audited": len(audited), "equal": len(rows) == len(audited)},
        "guardrails": {"network_calls": 0, "credentials_used": False, "allow_ranking": False, "production_scoring_authorized": False, "phase9b_authorized": False},
    }
    for path in sorted(args.output.glob("*")):
        if path.is_file() and path.name != "global_universe_manifest_v2_38a.json":
            manifest["outputs"][path.name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    manifest_path = args.output / "global_universe_manifest_v2_38a.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "rows": len(rows), "eligible": summary["eligible_rows"], "decision": manifest["decision"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
