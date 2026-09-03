#!/usr/bin/env python3
"""Build the v2.38N Europe home-exchange resolution layer without network calls."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_home_exchange_resolution_contract_v1.json"
EU_CENSUS = ROOT / "outputs/full_universe_source_acquisition/v2_38c_us_eu_priority_coverage/eu_universe_census_v2_38c.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38n_europe_home_exchange_resolution"
PHASE = "v2.38N-europe-home-exchange-resolution"

RESOLUTION_FIELDS = [
    "asset_id",
    "ticker",
    "company_name",
    "country",
    "currency",
    "exchange",
    "mic",
    "inferred_region",
    "source_provider",
    "home_exchange",
    "home_mic",
    "home_country",
    "home_currency",
    "listing_role",
    "resolution_status",
    "provider_route",
    "provider_route_status",
    "evidence_source",
    "evidence_strength",
    "review_reason",
    "phase",
    "scoring_calculated",
    "ranking_calculated",
    "recommendations_generated",
    "phase9c_authorized",
]

HOME_MARKETS = {
    "GB": ("LSE", "XLON", "GB", "GBP"),
    "UNITED KINGDOM": ("LSE", "XLON", "GB", "GBP"),
    "DE": ("XETRA", "XETR", "DE", "EUR"),
    "GERMANY": ("XETRA", "XETR", "DE", "EUR"),
    "FR": ("Euronext Paris", "XPAR", "FR", "EUR"),
    "FRANCE": ("Euronext Paris", "XPAR", "FR", "EUR"),
    "NL": ("Euronext Amsterdam", "XAMS", "NL", "EUR"),
    "NETHERLANDS": ("Euronext Amsterdam", "XAMS", "NL", "EUR"),
    "BE": ("Euronext Brussels", "XBRU", "BE", "EUR"),
    "BELGIUM": ("Euronext Brussels", "XBRU", "BE", "EUR"),
    "PT": ("Euronext Lisbon", "XLIS", "PT", "EUR"),
    "PORTUGAL": ("Euronext Lisbon", "XLIS", "PT", "EUR"),
    "ES": ("BME", "XMAD", "ES", "EUR"),
    "SPAIN": ("BME", "XMAD", "ES", "EUR"),
    "IT": ("Borsa Italiana", "MTAA", "IT", "EUR"),
    "ITALY": ("Borsa Italiana", "MTAA", "IT", "EUR"),
    "CH": ("SIX Swiss Exchange", "XSWX", "CH", "CHF"),
    "SWITZERLAND": ("SIX Swiss Exchange", "XSWX", "CH", "CHF"),
    "SE": ("Nasdaq Stockholm", "XSTO", "SE", "SEK"),
    "SWEDEN": ("Nasdaq Stockholm", "XSTO", "SE", "SEK"),
    "DK": ("Nasdaq Copenhagen", "XCSE", "DK", "DKK"),
    "DENMARK": ("Nasdaq Copenhagen", "XCSE", "DK", "DKK"),
    "FI": ("Nasdaq Helsinki", "XHEL", "FI", "EUR"),
    "FINLAND": ("Nasdaq Helsinki", "XHEL", "FI", "EUR"),
    "NO": ("Oslo Bors", "XOSL", "NO", "NOK"),
    "NORWAY": ("Oslo Bors", "XOSL", "NO", "NOK"),
    "IE": ("Euronext Dublin", "XDUB", "IE", "EUR"),
    "IRELAND": ("Euronext Dublin", "XDUB", "IE", "EUR"),
    "AT": ("Vienna Stock Exchange", "XWBO", "AT", "EUR"),
    "AUSTRIA": ("Vienna Stock Exchange", "XWBO", "AT", "EUR"),
}

EXCHANGE_TO_HOME = {
    "LSE": ("LSE", "XLON", "GB", "GBP"),
    "XLON": ("LSE", "XLON", "GB", "GBP"),
    "XETR": ("XETRA", "XETR", "DE", "EUR"),
    "XETRA": ("XETRA", "XETR", "DE", "EUR"),
    "EURONEXT PARIS": ("Euronext Paris", "XPAR", "FR", "EUR"),
    "XPAR": ("Euronext Paris", "XPAR", "FR", "EUR"),
    "EURONEXT AMSTERDAM": ("Euronext Amsterdam", "XAMS", "NL", "EUR"),
    "XAMS": ("Euronext Amsterdam", "XAMS", "NL", "EUR"),
    "EURONEXT BRUSSELS": ("Euronext Brussels", "XBRU", "BE", "EUR"),
    "XBRU": ("Euronext Brussels", "XBRU", "BE", "EUR"),
    "EURONEXT LISBON": ("Euronext Lisbon", "XLIS", "PT", "EUR"),
    "XLIS": ("Euronext Lisbon", "XLIS", "PT", "EUR"),
    "BME": ("BME", "XMAD", "ES", "EUR"),
    "XMAD": ("BME", "XMAD", "ES", "EUR"),
    "BORSA ITALIANA": ("Borsa Italiana", "MTAA", "IT", "EUR"),
    "MTAA": ("Borsa Italiana", "MTAA", "IT", "EUR"),
    "SIX": ("SIX Swiss Exchange", "XSWX", "CH", "CHF"),
    "XSWX": ("SIX Swiss Exchange", "XSWX", "CH", "CHF"),
    "NASDAQ STOCKHOLM": ("Nasdaq Stockholm", "XSTO", "SE", "SEK"),
    "XSTO": ("Nasdaq Stockholm", "XSTO", "SE", "SEK"),
    "NASDAQ COPENHAGEN": ("Nasdaq Copenhagen", "XCSE", "DK", "DKK"),
    "XCSE": ("Nasdaq Copenhagen", "XCSE", "DK", "DKK"),
    "NASDAQ HELSINKI": ("Nasdaq Helsinki", "XHEL", "FI", "EUR"),
    "XHEL": ("Nasdaq Helsinki", "XHEL", "FI", "EUR"),
    "OSLO BORS": ("Oslo Bors", "XOSL", "NO", "NOK"),
    "XOSL": ("Oslo Bors", "XOSL", "NO", "NOK"),
    "EURONEXT DUBLIN": ("Euronext Dublin", "XDUB", "IE", "EUR"),
    "XDUB": ("Euronext Dublin", "XDUB", "IE", "EUR"),
    "VIENNA STOCK EXCHANGE": ("Vienna Stock Exchange", "XWBO", "AT", "EUR"),
    "XWBO": ("Vienna Stock Exchange", "XWBO", "AT", "EUR"),
}

CBOE_MARKERS = ("CBOE", "BATS", "CHI-X", "CHIX", "CXE", "BXE", "DXE", "TRF", "CBOE_EUROPE")
DR_TYPES = {"DR", "ADR", "GDR"}
NON_EUROPE_COUNTRIES = {"US", "USA", "CA", "CANADA", "AU", "AUSTRALIA", "CN", "CHINA"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bool_text(value: bool) -> str:
    return "false" if not value else "true"


def is_cboe(row: dict[str, str]) -> bool:
    joined = " ".join([row.get("exchange", ""), row.get("mic", ""), row.get("source_provider", "")]).upper()
    return any(marker in joined for marker in CBOE_MARKERS)


def mapped_home(row: dict[str, str]) -> tuple[str, str, str, str] | None:
    country_key = (row.get("country") or "").strip().upper()
    exchange_key = (row.get("exchange") or "").strip().upper()
    mic_key = (row.get("mic") or "").strip().upper()
    if country_key in HOME_MARKETS:
        return HOME_MARKETS[country_key]
    if mic_key in EXCHANGE_TO_HOME:
        return EXCHANGE_TO_HOME[mic_key]
    if exchange_key in EXCHANGE_TO_HOME:
        return EXCHANGE_TO_HOME[exchange_key]
    return None


def route_for(home_mic: str) -> tuple[str, str]:
    if home_mic == "XETR":
        return "stooq_daily_prices", "READY_FOR_PRICE_HISTORY_PILOT"
    if home_mic in {"XLON", "XPAR", "XAMS", "XBRU", "XLIS", "XMAD", "MTAA", "XSWX", "XSTO", "XCSE", "XHEL", "XOSL", "XDUB", "XWBO"}:
        return "eodhd_europe_prices", "READY_FOR_IDENTITY_PILOT"
    return "manual_review_required", "MANUAL_REVIEW_REQUIRED"


def resolve(row: dict[str, str]) -> dict[str, object]:
    base = {
        "asset_id": row.get("asset_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "country": row.get("country", ""),
        "currency": row.get("currency", ""),
        "exchange": row.get("exchange", ""),
        "mic": row.get("mic", ""),
        "inferred_region": "EUROPE",
        "source_provider": row.get("source_provider", ""),
        "home_exchange": "",
        "home_mic": "",
        "home_country": "",
        "home_currency": "",
        "listing_role": "UNKNOWN_REVIEW",
        "resolution_status": "INSUFFICIENT_IDENTITY_EVIDENCE",
        "provider_route": "manual_review_required",
        "provider_route_status": "MANUAL_REVIEW_REQUIRED",
        "evidence_source": "v2.38C EU census",
        "evidence_strength": "NONE",
        "review_reason": "",
        "phase": PHASE,
        "scoring_calculated": bool_text(False),
        "ranking_calculated": bool_text(False),
        "recommendations_generated": bool_text(False),
        "phase9c_authorized": bool_text(False),
    }
    instrument_type = (row.get("instrument_type") or "").strip().upper()
    country = (row.get("country") or "").strip().upper()
    if country in NON_EUROPE_COUNTRIES:
        base.update({
            "inferred_region": "OUT_OF_SCOPE",
            "resolution_status": "OUT_OF_SCOPE_NON_EUROPE",
            "provider_route": "blocked_provider_required",
            "provider_route_status": "BLOCKED_PROVIDER_REQUIRED",
            "review_reason": "Issuer country is outside the Europe priority scope for this phase.",
        })
        return base
    if instrument_type in DR_TYPES:
        base.update({
            "listing_role": "ADR_GDR",
            "resolution_status": "ADR_GDR_REVIEW_REQUIRED",
            "provider_route": "manual_review_required",
            "provider_route_status": "MANUAL_REVIEW_REQUIRED",
            "evidence_strength": "LOW",
            "review_reason": "Depositary receipt requires issuer home-market validation before European enrichment.",
        })
        return base
    if is_cboe(row):
        base.update({
            "listing_role": "SECONDARY_CBOE_EUROPE",
            "resolution_status": "CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED",
            "provider_route": "exchange_official_reference",
            "provider_route_status": "BLOCKED_HOME_EXCHANGE_REQUIRED",
            "evidence_strength": "HIGH",
            "review_reason": "Cboe Europe is treated as a secondary venue until the issuer home exchange is resolved.",
        })
        return base
    home = mapped_home(row)
    if home is None:
        base.update({
            "resolution_status": "INSUFFICIENT_IDENTITY_EVIDENCE",
            "provider_route": "manual_review_required",
            "provider_route_status": "MANUAL_REVIEW_REQUIRED",
            "review_reason": "No deterministic country, exchange, or MIC mapping to a supported Europe home exchange.",
        })
        return base
    home_exchange, home_mic, home_country, home_currency = home
    route, route_status = route_for(home_mic)
    base.update({
        "home_exchange": home_exchange,
        "home_mic": home_mic,
        "home_country": home_country,
        "home_currency": home_currency,
        "listing_role": "PRIMARY_HOME_EXCHANGE",
        "resolution_status": "HOME_EXCHANGE_RESOLVED",
        "provider_route": route,
        "provider_route_status": route_status,
        "evidence_strength": "MEDIUM",
        "review_reason": "Resolved by deterministic country/exchange/MIC mapping; still requires provider pilot before data enrichment.",
    })
    if country and country != home_country:
        base.update({
            "listing_role": "SECONDARY_MULTILISTING",
            "resolution_status": "COUNTRY_EXCHANGE_MISMATCH_REVIEW",
            "provider_route": "manual_review_required",
            "provider_route_status": "MANUAL_REVIEW_REQUIRED",
            "evidence_strength": "LOW",
            "review_reason": "Country and mapped exchange imply different home markets; manual validation required.",
        })
    return base


def summary_rows(rows: list[dict[str, object]], field: str) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(field, ""))].append(row)
    out = []
    for key in sorted(grouped):
        subset = grouped[key]
        statuses = Counter(str(r["resolution_status"]) for r in subset)
        out.append({
            field: key,
            "rows": len(subset),
            "home_exchange_resolved": sum(r["resolution_status"] == "HOME_EXCHANGE_RESOLVED" for r in subset),
            "cboe_secondary_blocked": sum(r["resolution_status"] == "CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED" for r in subset),
            "manual_review_required": sum(str(r["provider_route_status"]) == "MANUAL_REVIEW_REQUIRED" for r in subset),
            "primary_status": statuses.most_common(1)[0][0],
        })
    return out


def route_matrix(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["home_exchange"] or row["exchange"]), str(row["provider_route"]), str(row["provider_route_status"]))].append(row)
    out = []
    for (market, route, status), subset in sorted(grouped.items()):
        out.append({
            "market": market,
            "provider_route": route,
            "provider_route_status": status,
            "rows": len(subset),
            "home_exchange_resolved": sum(r["resolution_status"] == "HOME_EXCHANGE_RESOLVED" for r in subset),
            "blocker": "" if status.startswith("READY") else "identity/home-exchange/provider validation required before price history pilot",
        })
    return out


def batch_plan(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    actionable = [
        r for r in rows
        if r["provider_route_status"] in {"READY_FOR_PRICE_HISTORY_PILOT", "READY_FOR_IDENTITY_PILOT"}
    ]
    blocked = [
        r for r in rows
        if r["provider_route_status"] not in {"READY_FOR_PRICE_HISTORY_PILOT", "READY_FOR_IDENTITY_PILOT"}
    ]
    out = []
    for index, start in enumerate(range(0, len(actionable), 100), start=1):
        chunk = actionable[start:start + 100]
        out.append({
            "batch_id": f"EU_HOME_READY_{index:03d}",
            "batch_type": "provider_pilot_candidate",
            "assets": len(chunk),
            "asset_ids": "|".join(str(r["asset_id"]) for r in chunk),
            "provider_route_status": chunk[0]["provider_route_status"] if chunk else "",
            "network_allowed": "false",
            "phase9c_authorized": "false",
        })
    if blocked:
        out.append({
            "batch_id": "EU_HOME_BLOCKED_REVIEW",
            "batch_type": "blocked_review_register",
            "assets": len(blocked),
            "asset_ids": "|".join(str(r["asset_id"]) for r in blocked[:250]),
            "provider_route_status": "BLOCKED_OR_MANUAL_REVIEW",
            "network_allowed": "false",
            "phase9c_authorized": "false",
        })
    return out


def manifest() -> dict[str, object]:
    outputs = {}
    for path in sorted(OUT.iterdir()):
        if path.is_file():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "phase": PHASE,
        "status": "COMPLETED_EUROPE_HOME_EXCHANGE_RESOLUTION_NOT_ENRICHMENT",
        "outputs": outputs,
        "guardrails": {
            "network_calls": 0,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
            "phase9c_authorized": False,
            "financial_advice": False,
            "broker_actions_allowed": False,
        },
    }


def write_docs(report: dict[str, object]) -> None:
    (OUT / "README.md").write_text(
        "\n".join([
            "# v2.38N Europe Home-Exchange Resolution",
            "",
            "This folder contains the static Europe home-exchange resolution foundation.",
            "Cboe Europe records are treated as secondary venues by default and remain blocked until a reliable home exchange is established.",
            "",
            "No network calls, scoring, ranking, final recommendations, broker actions, or Phase 9C authorization are produced here.",
            "",
            f"Rows processed: {report['europe_rows']}",
            f"Home-exchange resolved: {report['home_exchange_resolved']}",
            f"Cboe secondary blocked: {report['cboe_secondary_home_required']}",
            "",
        ]),
        encoding="utf-8",
    )
    (OUT / "EUROPE_HOME_EXCHANGE_RESOLUTION_CONTRACT_v2_38n.md").write_text(
        "\n".join([
            "# Europe Home-Exchange Resolution Contract v2.38N",
            "",
            "- Cboe Europe is secondary by default.",
            "- Home exchange is required before European price-history acquisition.",
            "- Ambiguous multilisting and depositary receipt cases remain in review.",
            "- Static/offline phase only; no data-provider calls are made.",
            "- No scoring, ranking, final recommendations, financial advice, or broker actions.",
            "",
        ]),
        encoding="utf-8",
    )
    (OUT / "PHASE9N_EUROPE_HOME_EXCHANGE_GATE_v2_38n.md").write_text(
        "\n".join([
            "# Phase 9N Gate",
            "",
            "Status: COMPLETED_EUROPE_HOME_EXCHANGE_RESOLUTION_NOT_ENRICHMENT",
            "",
            "Gate result: Europe is prepared for provider-specific pilots only after home-exchange validation.",
            "Cboe Europe cannot be used as the primary listing source in this phase.",
            "",
            "Guardrails: no network, no scoring, no ranking, no recommendations, no Phase 9C.",
            "",
        ]),
        encoding="utf-8",
    )


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if not contract["cboe_europe_is_secondary_by_default"]:
        raise SystemExit("BLOCKED: Cboe Europe secondary guardrail missing")
    rows = read_csv(EU_CENSUS)
    OUT.mkdir(parents=True, exist_ok=True)
    resolved = [resolve(row) for row in rows]
    review = [r for r in resolved if r["resolution_status"] != "HOME_EXCHANGE_RESOLVED"]
    write_csv(OUT / "europe_home_exchange_resolution_v2_38n.csv", resolved, RESOLUTION_FIELDS)
    write_csv(OUT / "europe_home_exchange_review_v2_38n.csv", review, RESOLUTION_FIELDS)
    write_csv(
        OUT / "europe_home_exchange_country_summary_v2_38n.csv",
        summary_rows(resolved, "home_country"),
        ["home_country", "rows", "home_exchange_resolved", "cboe_secondary_blocked", "manual_review_required", "primary_status"],
    )
    write_csv(
        OUT / "europe_home_exchange_route_matrix_v2_38n.csv",
        route_matrix(resolved),
        ["market", "provider_route", "provider_route_status", "rows", "home_exchange_resolved", "blocker"],
    )
    write_csv(
        OUT / "europe_home_exchange_batch_plan_v2_38n.csv",
        batch_plan(resolved),
        ["batch_id", "batch_type", "assets", "asset_ids", "provider_route_status", "network_allowed", "phase9c_authorized"],
    )
    status_counts = Counter(str(r["resolution_status"]) for r in resolved)
    route_counts = Counter(str(r["provider_route_status"]) for r in resolved)
    report = {
        "phase": PHASE,
        "status": "COMPLETED_EUROPE_HOME_EXCHANGE_RESOLUTION_NOT_ENRICHMENT",
        "input_universe_rows_expected": contract["input_universe_rows_expected"],
        "europe_rows": len(resolved),
        "home_exchange_resolved": status_counts["HOME_EXCHANGE_RESOLVED"],
        "cboe_secondary_home_required": status_counts["CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED"],
        "adr_gdr_review_required": status_counts["ADR_GDR_REVIEW_REQUIRED"],
        "manual_review_or_blocked": len(review),
        "status_counts": dict(sorted(status_counts.items())),
        "provider_route_status_counts": dict(sorted(route_counts.items())),
        "guardrails": {
            "network_calls": 0,
            "cboe_europe_is_secondary_by_default": True,
            "home_exchange_required_for_europe_enrichment": True,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
            "phase9c_authorized": False,
            "financial_advice": False,
            "broker_actions_allowed": False,
        },
    }
    (OUT / "europe_home_exchange_aggregate_report_v2_38n.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_docs(report)
    (OUT / "europe_home_exchange_manifest_v2_38n.json").write_text(
        json.dumps(manifest(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "europe_rows": report["europe_rows"],
        "home_exchange_resolved": report["home_exchange_resolved"],
        "cboe_secondary_home_required": report["cboe_secondary_home_required"],
        "recommendations_generated": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
