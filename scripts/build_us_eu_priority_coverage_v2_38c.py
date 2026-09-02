#!/usr/bin/env python3
"""Build the phase-9B US/EU priority coverage census without network calls."""
from __future__ import annotations

import csv
import hashlib
import json
import lzma
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/us_eu_priority_coverage_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38c_us_eu_priority_coverage"

US_EXCHANGES = {"NASDAQ", "NYSE", "NYSE American", "Cboe BZX"}
EUROPE_EXCHANGES = {"CBOE_EUROPE", "XETR", "LSE", "Euronext", "SIX", "Borsa Italiana", "Nordics"}

US_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "mic", "country", "currency",
    "instrument_type", "source_provider", "eligibility_status", "identity_status",
    "readiness_status", "blocker_reason", "normalized_exchange_group",
    "sec_identity_status", "price_route_status", "fundamental_route_status",
    "phase",
]
EU_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "mic", "country", "currency",
    "instrument_type", "source_provider", "eligibility_status", "identity_status",
    "readiness_status", "blocker_reason", "normalized_exchange_group",
    "home_exchange_candidate", "duplicate_group_candidate", "home_exchange_status",
    "price_route_status", "fundamental_route_status", "phase",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows(contract: dict) -> list[dict[str, str]]:
    source = ROOT / contract["input_manifest"]
    actual_hash = sha256(source)
    if actual_hash != contract["input_sha256"]:
        raise SystemExit(f"BLOCKED: v2.38A input hash mismatch: {actual_hash}")
    with lzma.open(source, "rt", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != contract["expected_rows"]:
        raise SystemExit("BLOCKED: canonical universe row count mismatch")
    if sum(r["eligibility_status"] == "ELIGIBLE" for r in rows) != contract["expected_eligible_rows"]:
        raise SystemExit("BLOCKED: eligible row count mismatch")
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalize_us_exchange(exchange: str) -> str:
    if exchange in {"NASDAQ", "NYSE", "NYSE American", "Cboe BZX"}:
        return exchange
    return "US_OTHER"


def us_status(row: dict[str, str]) -> tuple[str, str, str, str]:
    if row["eligibility_status"] != "ELIGIBLE":
        return "NOT_ELIGIBLE", "NOT_APPLICABLE", "NOT_APPLICABLE", row["blocker_reason"]
    if row["exchange"] == "Cboe BZX":
        return "US_SOURCE_REQUIRED", "US_PRICE_SOURCE_MISSING", "US_SOURCE_REQUIRED", "single eligible Cboe BZX record requires source confirmation"
    if row["identity_status"] != "COMPLETE":
        return "US_MANUAL_REVIEW", "US_PRICE_SOURCE_MISSING", "US_MISSING_CIK", "identity incomplete before SEC route"
    return "US_TICKER_EXCHANGE_READY", "US_PRICE_CREDENTIAL_REQUIRED", "US_CIK_MAPPING_REQUIRED", "SEC CIK route and adjusted price provider pilot required"


def build_us(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        if row["country"] == "USA" or row["exchange"] in US_EXCHANGES:
            readiness, price_route, fundamental_route, blocker = us_status(row)
            out.append({
                "asset_id": row["asset_id"],
                "ticker": row["ticker"],
                "company_name": row["company_name"],
                "exchange": row["exchange"],
                "mic": row["mic"],
                "country": row["country"],
                "currency": row["currency"],
                "instrument_type": row["instrument_type"],
                "source_provider": row["source_provider"],
                "eligibility_status": row["eligibility_status"],
                "identity_status": row["identity_status"],
                "readiness_status": readiness,
                "blocker_reason": blocker,
                "normalized_exchange_group": normalize_us_exchange(row["exchange"]),
                "sec_identity_status": fundamental_route,
                "price_route_status": price_route,
                "fundamental_route_status": fundamental_route,
                "phase": "v2.38C",
            })
    return out


def eu_home_candidate(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    if row["eligibility_status"] != "ELIGIBLE":
        return "", "", "NOT_ELIGIBLE", "NOT_APPLICABLE", row["blocker_reason"]
    if row["exchange"] == "CBOE_EUROPE":
        if row["isin"]:
            return "", row["isin"], "EU_HOME_EXCHANGE_AMBIGUOUS", "EU_SOURCE_REQUIRED", "Cboe Europe is a secondary venue until home exchange is verified"
        return "", "", "EU_ISIN_MISSING", "EU_SOURCE_REQUIRED", "Cboe Europe requires ISIN/home-exchange mapping"
    return row["exchange"], row["isin"], "EU_SOURCE_REQUIRED", "EU_SOURCE_REQUIRED", "European market provider and license route must be confirmed"


def build_eu(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        is_europe = row["exchange"] in EUROPE_EXCHANGES or row["source_provider"] == "cboe_europe_reference_data"
        if not is_europe:
            continue
        home, dup, home_status, route_status, blocker = eu_home_candidate(row)
        out.append({
            "asset_id": row["asset_id"],
            "ticker": row["ticker"],
            "company_name": row["company_name"],
            "exchange": row["exchange"],
            "mic": row["mic"],
            "country": row["country"],
            "currency": row["currency"],
            "instrument_type": row["instrument_type"],
            "source_provider": row["source_provider"],
            "eligibility_status": row["eligibility_status"],
            "identity_status": row["identity_status"],
            "readiness_status": home_status,
            "blocker_reason": blocker,
            "normalized_exchange_group": "CBOE_EUROPE" if row["exchange"] == "CBOE_EUROPE" else row["exchange"],
            "home_exchange_candidate": home,
            "duplicate_group_candidate": dup,
            "home_exchange_status": home_status,
            "price_route_status": route_status,
            "fundamental_route_status": route_status,
            "phase": "v2.38C",
        })
    return out


def breakdown(rows: list[dict[str, str]], group_field: str, status_field: str) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[group_field]].append(row)
    out = []
    for key in sorted(grouped):
        subset = grouped[key]
        statuses = Counter(r[status_field] for r in subset)
        out.append({
            group_field: key,
            "rows": len(subset),
            "eligible_rows": sum(r["eligibility_status"] == "ELIGIBLE" for r in subset),
            "primary_status": statuses.most_common(1)[0][0],
        })
    return out


def make_provider_matrix(us_rows: list[dict[str, str]], eu_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {"region": "US", "market": "NASDAQ", "identity_route": "SEC company tickers / CIK mapping", "price_route": "adjusted price provider required", "fundamental_route": "SEC XBRL companyfacts/submissions", "status": "USER_ACTION_REQUIRED", "blocker": "credential/license pilot required for adjusted prices"},
        {"region": "US", "market": "NYSE", "identity_route": "SEC company tickers / CIK mapping", "price_route": "adjusted price provider required", "fundamental_route": "SEC XBRL companyfacts/submissions", "status": "USER_ACTION_REQUIRED", "blocker": "credential/license pilot required for adjusted prices"},
        {"region": "US", "market": "NYSE American", "identity_route": "SEC company tickers / CIK mapping", "price_route": "adjusted price provider required", "fundamental_route": "SEC XBRL companyfacts/submissions", "status": "USER_ACTION_REQUIRED", "blocker": "credential/license pilot required for adjusted prices"},
        {"region": "US", "market": "Cboe BZX", "identity_route": "SEC company tickers / CIK mapping", "price_route": "provider source confirmation required", "fundamental_route": "SEC XBRL companyfacts/submissions", "status": "USER_ACTION_REQUIRED", "blocker": "single venue record requires source confirmation"},
        {"region": "EU", "market": "CBOE_EUROPE", "identity_route": "ISIN to home exchange required", "price_route": "blocked until home market resolved", "fundamental_route": "blocked until issuer/home market resolved", "status": "SOURCE_REQUIRED", "blocker": "secondary venue cannot be treated as primary listing"},
        {"region": "EU", "market": "Xetra/Euronext/LSE/SIX/Borsa Italiana/Nordics", "identity_route": "ISIN/MIC/LEI candidate route", "price_route": "market-specific provider required", "fundamental_route": "market/issuer filing route required", "status": "SOURCE_UNKNOWN", "blocker": "provider matrix not yet validated by market"},
    ]


def make_pilot(us_rows: list[dict[str, str]], eu_rows: list[dict[str, str]]) -> dict:
    us_eligible = [r for r in us_rows if r["eligibility_status"] == "ELIGIBLE"]
    eu_eligible = [r for r in eu_rows if r["eligibility_status"] == "ELIGIBLE"]
    return {
        "phase": "v2.38C-us-eu-priority-coverage",
        "status": "PILOT_DEFINED_NOT_EXECUTED",
        "guardrails": {
            "network_calls": 0,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
            "phase9c_authorized": False,
        },
        "samples": {
            "US": [r["asset_id"] for r in us_eligible[:25]],
            "EU": [r["asset_id"] for r in eu_eligible[:25]],
            "JPX_TWSE": "comparison only; no mass JPX expansion in this phase",
        },
        "measurement_plan": [
            "identity_resolved",
            "adjusted_prices_available",
            "fundamentals_available",
            "publication_dates_available",
            "corporate_actions_available",
            "comparability_status",
            "missing_data_reasons",
        ],
    }


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    rows = load_rows(contract)
    OUT.mkdir(parents=True, exist_ok=True)
    us_rows = build_us(rows)
    eu_rows = build_eu(rows)
    write_csv(OUT / "us_universe_census_v2_38c.csv", us_rows, US_FIELDS)
    write_csv(OUT / "eu_universe_census_v2_38c.csv", eu_rows, EU_FIELDS)
    write_csv(OUT / "us_exchange_breakdown_v2_38c.csv", breakdown(us_rows, "normalized_exchange_group", "readiness_status"), ["normalized_exchange_group", "rows", "eligible_rows", "primary_status"])
    write_csv(OUT / "eu_exchange_breakdown_v2_38c.csv", breakdown(eu_rows, "normalized_exchange_group", "home_exchange_status"), ["normalized_exchange_group", "rows", "eligible_rows", "primary_status"])
    matrix = make_provider_matrix(us_rows, eu_rows)
    write_csv(OUT / "us_eu_provider_route_matrix_v2_38c.csv", matrix, ["region", "market", "identity_route", "price_route", "fundamental_route", "status", "blocker"])
    cboe = [r for r in eu_rows if r["exchange"] == "CBOE_EUROPE"]
    write_csv(OUT / "cboe_europe_home_exchange_candidates_v2_38c.csv", cboe, EU_FIELDS)

    us_status_counts = Counter(r["readiness_status"] for r in us_rows)
    eu_status_counts = Counter(r["home_exchange_status"] for r in eu_rows)
    summary = {
        "phase": "v2.38C-us-eu-priority-coverage",
        "status": "COMPLETED_PARTIAL_COVERAGE",
        "universe_rows": len(rows),
        "eligible_rows": sum(r["eligibility_status"] == "ELIGIBLE" for r in rows),
        "us_rows": len(us_rows),
        "us_eligible_rows": sum(r["eligibility_status"] == "ELIGIBLE" for r in us_rows),
        "eu_rows": len(eu_rows),
        "eu_eligible_rows": sum(r["eligibility_status"] == "ELIGIBLE" for r in eu_rows),
        "us_ready_for_identity_route": sum(r["readiness_status"] == "US_TICKER_EXCHANGE_READY" for r in us_rows),
        "eu_home_exchange_ready": sum(r["home_exchange_status"] == "EU_HOME_EXCHANGE_READY" for r in eu_rows),
        "cboe_europe_secondary_venue_rows": len(cboe),
        "us_status_counts": dict(sorted(us_status_counts.items())),
        "eu_status_counts": dict(sorted(eu_status_counts.items())),
        "guardrails": {
            "network_calls": 0,
            "credentials_used": False,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
            "phase9c_authorized": False,
        },
        "limitations": [
            "US adjusted price provider still requires credential/license pilot.",
            "US SEC route is defined but full CIK/XBRL enrichment is not executed in this phase.",
            "Cboe Europe is treated as a secondary venue until home exchange mapping is verified.",
            "European provider routes remain market-specific and fail-closed until source/license validation.",
        ],
    }
    (OUT / "us_coverage_summary_v2_38c.json").write_text(json.dumps({k: summary[k] for k in ["phase", "status", "us_rows", "us_eligible_rows", "us_ready_for_identity_route", "us_status_counts", "guardrails"]}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (OUT / "eu_coverage_summary_v2_38c.json").write_text(json.dumps({k: summary[k] for k in ["phase", "status", "eu_rows", "eu_eligible_rows", "eu_home_exchange_ready", "cboe_europe_secondary_venue_rows", "eu_status_counts", "guardrails"]}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (OUT / "multi_region_coverage_pilot_v2_38c.json").write_text(json.dumps(make_pilot(us_rows, eu_rows), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    gate = f"""# Phase 9B-US/EU Final Gate v2.38C

Decision: COMPLETED_PARTIAL_COVERAGE

Scout Finance remains aligned to the global roadmap: the application must eventually scan all 43,089 companies and recommend only evidence-backed opportunities with causal explanations. This phase does not calculate scoring, ranking, recommendations or phase-9C geopolitical signals.

## Coverage

- Universe rows: {summary['universe_rows']}
- Eligible rows: {summary['eligible_rows']}
- US rows: {summary['us_rows']}
- US eligible rows: {summary['us_eligible_rows']}
- US ready for SEC identity route: {summary['us_ready_for_identity_route']}
- Europe rows: {summary['eu_rows']}
- Europe eligible rows: {summary['eu_eligible_rows']}
- Cboe Europe secondary-venue rows: {summary['cboe_europe_secondary_venue_rows']}

## Gate

US is prioritized for SEC CIK/XBRL routing and adjusted-price provider validation. Europe is prioritized through home-exchange resolution, especially for Cboe Europe, which must not be treated as a primary exchange without evidence.

Blocked actions remain blocked: no scoring, no ranking, no recommendations, no phase 9C, no broker and no trading.
"""
    (OUT / "PHASE9B_US_EU_FINAL_GATE_v2_38c.md").write_text(gate, encoding="utf-8", newline="\n")
    (OUT / "README.md").write_text("# v2.38C US/EU priority coverage\n\nOffline, fail-closed census and route planning for US and Europe priority coverage.\n", encoding="utf-8", newline="\n")

    manifest = {
        "phase": summary["phase"],
        "decision": summary["status"],
        "input": {"path": contract["input_manifest"], "sha256": sha256(ROOT / contract["input_manifest"]), "rows": len(rows)},
        "outputs": {},
        "guardrails": summary["guardrails"],
    }
    for path in sorted(OUT.glob("*")):
        if path.is_file() and path.name != "manifest_v2_38c.json":
            manifest["outputs"][path.name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    (OUT / "manifest_v2_38c.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": summary["status"], "us_eligible": summary["us_eligible_rows"], "eu_eligible": summary["eu_eligible_rows"], "recommendations_generated": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
