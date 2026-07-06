from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.6A"
METHOD = "next_official_provider_route_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "next_official_provider_route_v2_6a.json"
OUT_MD = OUT_DIR / "next_official_provider_route_v2_6a.md"

NYSE_DECISION_JSON = OUT_DIR / "nyse_usability_decision_gate_v2_5g.json"
REVALIDATION_JSON = OUT_DIR / "expanded_source_revalidation_gate_v2_5a.json"

CURRENT_INCLUDED_ROWS = 5648
TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    nyse_decision = read_json(NYSE_DECISION_JSON)
    revalidation = read_json(REVALIDATION_JSON)

    if not nyse_decision.get("_exists"):
        blockers.append(f"Missing v2.5G NYSE decision artifact: {rel(NYSE_DECISION_JSON)}")
    else:
        positives.append(f"v2.5G NYSE decision artifact found: {rel(NYSE_DECISION_JSON)}")

    if not revalidation.get("_exists"):
        blockers.append(f"Missing v2.5A revalidation artifact: {rel(REVALIDATION_JSON)}")
    else:
        positives.append(f"v2.5A revalidation artifact found: {rel(REVALIDATION_JSON)}")

    nyse_status = nyse_decision.get("decision_status")
    nyse_usability = nyse_decision.get("nyse_usability_decision")

    if nyse_usability == "REQUIRES_DEEP_JS_PAYLOAD_REVIEW":
        positives.append(f"NYSE correctly deferred from rebuild path: {nyse_usability}")
    else:
        warnings.append(f"Unexpected NYSE usability decision: {nyse_usability}")

    rows_needed_first_expansion = max(TARGET_FIRST_EXPANSION_ROWS - CURRENT_INCLUDED_ROWS, 0)
    rows_needed_full_source = max(MIN_FULL_SOURCE_ROWS - CURRENT_INCLUDED_ROWS, 0)

    provider_routes = [
        {
            "priority": 1,
            "provider_id": "sec_company_tickers_exchange",
            "provider_name": "SEC company_tickers_exchange.json",
            "provider_type": "official_regulatory_identifier_mapping",
            "route_status": "RECOMMENDED_NEXT_CONTROLLED_ROUTE",
            "expected_value": "HIGH",
            "risk": "MEDIUM",
            "network_required": True,
            "source_url": "https://www.sec.gov/files/company_tickers_exchange.json",
            "why_next": (
                "Official SEC file with company name, CIK, ticker and exchange mapping. "
                "Useful to expand and validate ticker universe with exchange metadata, although it is not a pure exchange listing file."
            ),
            "expected_outputs_if_acquired": [
                "data/raw/source_providers/sec_company_tickers_exchange/company_tickers_exchange.json",
                "data/raw/source_providers/sec_company_tickers_exchange/sec_company_tickers_exchange.csv",
                "outputs/full_universe_source_acquisition/sec_company_tickers_exchange_acquisition_v2_6b.json",
                "outputs/full_universe_source_acquisition/sec_company_tickers_exchange_acquisition_v2_6b.md",
            ],
            "controls": [
                "Use SEC-compliant User-Agent.",
                "No scoring.",
                "No OpenAI.",
                "No broker.",
                "No full 59k launch.",
                "No active output overwrite.",
                "Do not rebuild expanded_universe until validation report is reviewed.",
            ],
            "acceptance_criteria": [
                "Download succeeds or fails with controlled report.",
                "Raw JSON is preserved.",
                "CSV normalization is produced only if schema is recognized.",
                "Report row count, exchanges, duplicate ticker/exchange keys and missing fields.",
            ],
        },
        {
            "priority": 2,
            "provider_id": "cboe_listed_symbols",
            "provider_name": "Cboe Listed Symbols",
            "provider_type": "official_exchange_listing_source",
            "route_status": "SECOND_ROUTE_AFTER_SEC_OR_PARALLEL_IF_NEEDED",
            "expected_value": "MEDIUM",
            "risk": "MEDIUM",
            "network_required": True,
            "source_url": "https://www.cboe.com/us/equities/market_statistics/listed_symbols/",
            "why_next": (
                "Official Cboe listed-symbol route with CSV/XML indications. "
                "Likely useful for BZX-listed securities, but may be narrower than SEC mapping."
            ),
            "expected_outputs_if_acquired": [
                "data/raw/source_providers/cboe_listed_symbols/",
                "outputs/full_universe_source_acquisition/cboe_listed_symbols_acquisition_v2_6x.json",
                "outputs/full_universe_source_acquisition/cboe_listed_symbols_acquisition_v2_6x.md",
            ],
            "controls": [
                "No scoring.",
                "No OpenAI.",
                "No broker.",
                "No full 59k launch.",
                "No active output overwrite.",
            ],
            "acceptance_criteria": [
                "Identify stable CSV/XML route.",
                "Download raw file in isolated provider directory.",
                "Report row count and schema.",
                "Do not rebuild until validation gate passes.",
            ],
        },
        {
            "priority": 3,
            "provider_id": "cboe_bzx_daily_listed_securities_report",
            "provider_name": "Cboe BZX Daily Listed Securities Report",
            "provider_type": "official_exchange_listing_report",
            "route_status": "FOLLOW_UP_IF_CBOE_ROUTE_IS_SELECTED",
            "expected_value": "MEDIUM",
            "risk": "MEDIUM",
            "network_required": True,
            "source_url": "Cboe BZX daily listed securities report documentation",
            "why_next": (
                "Cboe documentation describes a daily listed securities report for issues listed on BZX. "
                "Useful if a stable public file route can be confirmed."
            ),
            "expected_outputs_if_acquired": [],
            "controls": [
                "Documentation-first.",
                "No scoring.",
                "No OpenAI.",
                "No broker.",
                "No full 59k launch.",
            ],
            "acceptance_criteria": [
                "Confirm public accessibility.",
                "Confirm format and schema.",
                "Only then implement real acquisition.",
            ],
        },
        {
            "priority": 4,
            "provider_id": "third_party_aggregated_datasets",
            "provider_name": "Third-party aggregated datasets",
            "provider_type": "non_primary_external_dataset",
            "route_status": "DEFER",
            "expected_value": "VARIABLE",
            "risk": "HIGH",
            "network_required": True,
            "source_url": None,
            "why_next": (
                "Could add rows, but license, freshness and provenance risks make it unsuitable before official routes are exhausted."
            ),
            "expected_outputs_if_acquired": [],
            "controls": [
                "License review required.",
                "Freshness review required.",
                "Do not use as primary source without explicit approval.",
            ],
            "acceptance_criteria": [
                "License documented.",
                "Freshness documented.",
                "Official source alternatives exhausted.",
            ],
        },
    ]

    if blockers:
        route_status = "NEXT_OFFICIAL_PROVIDER_ROUTE_BLOCKED"
        readiness_score = 0
        recommended_next_phase = "Resolve blockers"
    else:
        route_status = "NEXT_OFFICIAL_PROVIDER_ROUTE_READY"
        readiness_score = 90
        recommended_next_phase = "v2.6B ? SEC Company Tickers Exchange Acquisition Plan"

    warnings.append(f"Rows still needed for first expansion target: {rows_needed_first_expansion}")
    warnings.append(f"Rows still needed for full-source threshold: {rows_needed_full_source}")
    warnings.append("NYSE remains deferred unless deep JS payload review is explicitly chosen later.")

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "route_status": route_status,
        "readiness_score": readiness_score,
        "recommended_next_phase": recommended_next_phase,
        "current_state": {
            "current_included_rows": CURRENT_INCLUDED_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "rows_needed_first_expansion": rows_needed_first_expansion,
            "rows_needed_full_source": rows_needed_full_source,
            "nyse_decision_status": nyse_status,
            "nyse_usability_decision": nyse_usability,
            "expanded_universe_rebuild_allowed": False,
            "full_59000_remains_blocked": True,
        },
        "provider_routes": provider_routes,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "network_download_performed": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
        },
        "recommendation": (
            "Proceed with v2.6B as a plan-only SEC company_tickers_exchange acquisition route. Do not download until that plan is reviewed."
            if not blockers
            else "Resolve blockers before selecting a new official provider route."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.6A Next Official Provider Route")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Route status: **{route_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Current state")
    md.append("")
    md.append(f"- Current included rows: {CURRENT_INCLUDED_ROWS}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Rows needed for first expansion target: {rows_needed_first_expansion}")
    md.append(f"- Rows needed for full-source threshold: {rows_needed_full_source}")
    md.append(f"- NYSE decision status: **{nyse_status}**")
    md.append(f"- NYSE usability decision: **{nyse_usability}**")
    md.append("- Expanded universe rebuild allowed: false")
    md.append("- Full 59k remains blocked: true")
    md.append("")
    md.append("## Provider route ranking")
    md.append("")
    for route in provider_routes:
        md.append(f"### {route['priority']}. {route['provider_name']}")
        md.append("")
        md.append(f"- Provider ID: `{route['provider_id']}`")
        md.append(f"- Type: {route['provider_type']}")
        md.append(f"- Route status: **{route['route_status']}**")
        md.append(f"- Expected value: {route['expected_value']}")
        md.append(f"- Risk: {route['risk']}")
        md.append(f"- Network required: {route['network_required']}")
        if route["source_url"]:
            md.append(f"- Source URL/reference: `{route['source_url']}`")
        md.append(f"- Why next: {route['why_next']}")
        md.append("")
        md.append("Acceptance criteria:")
        for criterion in route["acceptance_criteria"]:
            md.append(f"- {criterion}")
        md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Network download performed: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("")
    md.append("## Positives")
    md.append("")
    for item in positives:
        md.append(f"- {item}")
    md.append("")
    md.append("## Blockers")
    md.append("")
    if blockers:
        for item in blockers:
            md.append(f"- {item}")
    else:
        md.append("- No blockers detected.")
    md.append("")
    md.append("## Warnings")
    md.append("")
    for item in warnings:
        md.append(f"- {item}")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.6A is a route-selection artifact only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.6A Next Official Provider Route")
    print("=" * 92)
    print(f"OK   Route status: {route_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Current included rows: {CURRENT_INCLUDED_ROWS}")
    print(f"OK   Rows needed first expansion: {rows_needed_first_expansion}")
    print(f"OK   Rows needed full source: {rows_needed_full_source}")
    print(f"OK   NYSE usability decision: {nyse_usability}")
    print(f"OK   Provider routes ranked: {len(provider_routes)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
