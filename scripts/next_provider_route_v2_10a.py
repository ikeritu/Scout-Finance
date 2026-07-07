from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.10A"
METHOD = "next_provider_route_after_otc_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

OTC_CLOSURE_JSON = OUT_DIR / "otc_markets_closure_report_v2_9g.json"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

OUT_JSON = OUT_DIR / "next_provider_route_v2_10a.json"
OUT_MD = OUT_DIR / "next_provider_route_v2_10a.md"

CURRENT_EXPANDED_ROWS = 9200
CURRENT_EXCLUSIONS_ROWS = 10056

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

ROWS_NEEDED_FIRST_EXPANSION = 5800
ROWS_NEEDED_FULL_SOURCE = 40800

PRIMARY_PROVIDER_ID = "lse_issuers_and_instruments_reports"

LSE_REPORTS_URL = "https://www.londonstockexchange.com/reports"
CBOE_EU_REFERENCE_DATA_URL = "https://www.cboe.com/europe/equities/support/reference_data/"
DATAHUB_NYSE_OTHER_LISTINGS_URL = "https://datahub.io/core/nyse-other-listings"
NASDAQ_SCREENER_URL = "https://www.nasdaq.com/market-activity/stocks/screener"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
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

    otc_closure = read_json(OTC_CLOSURE_JSON)

    if not otc_closure.get("_exists"):
        blockers.append(f"Missing v2.9G OTC closure artifact: {rel(OTC_CLOSURE_JSON)}")
    else:
        positives.append(f"v2.9G OTC closure artifact found: {rel(OTC_CLOSURE_JSON)}")

    closure_status = otc_closure.get("closure_status")
    closure_decision = otc_closure.get("closure_decision")

    if closure_status == "OTC_MARKETS_CLOSED_VALID_BUT_NOT_ENOUGH":
        positives.append(f"v2.9G closure status accepted: {closure_status}")
    else:
        blockers.append(f"Unexpected v2.9G closure status: {closure_status}")

    if closure_decision == "OTC_MARKETS_CLOSED_REFERENCE_OR_ENRICHMENT_ONLY_NO_REBUILD":
        positives.append(f"v2.9G closure decision accepted: {closure_decision}")
    else:
        blockers.append(f"Unexpected v2.9G closure decision: {closure_decision}")

    for path in [CURRENT_EXPANDED_CSV, CURRENT_EXCLUSIONS_CSV]:
        if path.exists():
            positives.append(f"Current source input available: {rel(path)}")
        else:
            blockers.append(f"Missing current source input: {rel(path)}")

    first_expansion_unlocked = CURRENT_EXPANDED_ROWS >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = CURRENT_EXPANDED_ROWS >= MIN_FULL_SOURCE_ROWS

    warnings.append("Current expanded source remains below first expansion threshold: 9200 < 15000.")
    warnings.append("Current expanded source remains below full-source threshold: 9200 < 50000.")
    warnings.append("v2.10A is route-selection only; do not download LSE or Cboe Europe data in this phase.")
    warnings.append("LSE may contain multiple report formats, archives or dynamic pages; v2.10B must define a controlled acquisition contract before network access.")
    warnings.append("International venues may introduce non-US instruments, currencies, MICs and symbol semantics; classification must be conservative.")

    route_candidates = [
        {
            "priority": 1,
            "provider_id": "lse_issuers_and_instruments_reports",
            "name": "London Stock Exchange ? Issuers and Instruments Reports",
            "source_url": LSE_REPORTS_URL,
            "download_candidate_url": "",
            "route_type": "official_exchange_reports_route",
            "expected_value": "HIGH_FOR_NON_US_EXPANSION",
            "risk": "MEDIUM",
            "expected_coverage": "Potentially useful for UK and international instruments admitted to LSE markets, depending on available report exports.",
            "why": "After OTC produced only 25 net-new rows, the next route should target an official venue/reporting source with broader coverage than a small screener result.",
            "planned_treatment": "v2.10B must inspect/report planned LSE acquisition routes without downloading. v2.10C may download only routes approved by v2.10B.",
            "decision": "SELECTED_PRIMARY_ROUTE",
        },
        {
            "priority": 2,
            "provider_id": "cboe_europe_reference_data",
            "name": "Cboe Europe Equities Reference Data",
            "source_url": CBOE_EU_REFERENCE_DATA_URL,
            "download_candidate_url": "",
            "route_type": "official_european_reference_data_route",
            "expected_value": "MEDIUM_TO_HIGH",
            "risk": "MEDIUM",
            "expected_coverage": "Potentially useful for pan-European reference data if downloadable instruments files are exposed.",
            "why": "Official European exchange/operator source. Kept as fallback if LSE route is blocked or too dynamic.",
            "planned_treatment": "Keep as fallback for v2.11A or switch route only if v2.10B blocks LSE.",
            "decision": "FALLBACK_OFFICIAL_ROUTE",
        },
        {
            "priority": 3,
            "provider_id": "datahub_nyse_other_listings",
            "name": "DataHub NYSE Other Listings",
            "source_url": DATAHUB_NYSE_OTHER_LISTINGS_URL,
            "download_candidate_url": "",
            "route_type": "third_party_packaged_reference_route",
            "expected_value": "LOW",
            "risk": "MEDIUM_HIGH",
            "expected_coverage": "Likely overlap with existing Nasdaq Trader otherlisted data and may be too small.",
            "why": "Useful as reference or QA comparison, but not ideal as next primary provider because it is not the primary exchange source and likely overlaps.",
            "planned_treatment": "Reference/QA only unless official routes fail.",
            "decision": "REFERENCE_ONLY_FALLBACK",
        },
        {
            "priority": 4,
            "provider_id": "nasdaq_stock_screener_revisit",
            "name": "Nasdaq Stock Screener Revisit",
            "source_url": NASDAQ_SCREENER_URL,
            "download_candidate_url": "",
            "route_type": "official_or_semi_official_screener_review",
            "expected_value": "LOW_TO_MEDIUM",
            "risk": "MEDIUM_HIGH",
            "expected_coverage": "Likely overlaps with existing Nasdaq Trader and SEC sources.",
            "why": "Could enrich names/metadata, but less promising for large net-new expansion.",
            "planned_treatment": "Keep deferred unless LSE and Cboe Europe fail.",
            "decision": "DEFERRED_FALLBACK",
        },
    ]

    planned_outputs_v2_10b = {
        "provider_dir": f"data/raw/source_providers/{PRIMARY_PROVIDER_ID}",
        "route_plan_json": "outputs/full_universe_source_acquisition/lse_acquisition_plan_v2_10b.json",
        "route_plan_md": "outputs/full_universe_source_acquisition/lse_acquisition_plan_v2_10b.md",
        "discovered_links_csv": "outputs/full_universe_source_acquisition/lse_discovered_links_v2_10b.csv",
        "route_probe_csv": "outputs/full_universe_source_acquisition/lse_route_probe_v2_10b.csv",
    }

    planned_controls = [
        "v2.10B must be plan-only.",
        "No LSE download in v2.10A.",
        "No expanded_universe rebuild in v2.10A or v2.10B.",
        "No active MVP output overwrite.",
        "No scoring.",
        "No OpenAI.",
        "No broker calls.",
        "No full 59k launch.",
        "Prefer official downloadable CSV/XLS/XLSX/report files over dynamic page scraping.",
        "If LSE route is dynamic or blocked, close as blocked and switch to Cboe Europe route.",
    ]

    validation_questions = [
        "Does LSE expose a stable downloadable issuer/instrument report?",
        "What file format is available: CSV, XLS, XLSX, HTML table, ZIP, PDF?",
        "Does the report contain a usable symbol, issuer name, instrument type, market/segment and country?",
        "Does the report include ordinary shares, ETFs, funds, bonds or mixed instruments?",
        "Can rows be normalized to the canonical source schema without brittle scraping?",
        "How many rows are available before net-new filtering?",
        "How many exchange+ticker or MIC+ticker keys are net-new against expanded_universe_v2_8e?",
        "Does LSE unlock the 15000-row first expansion threshold?",
        "Should LSE be treated as source provider, candidate provider, enrichment, reference-only or deferred?",
    ]

    if blockers:
        route_status = "NEXT_PROVIDER_ROUTE_BLOCKED"
        readiness_score = 0
        route_decision = "BLOCKED"
        selected_provider = None
        recommended_next_phase = "Resolve blockers"
    else:
        route_status = "NEXT_PROVIDER_ROUTE_READY"
        readiness_score = 90
        route_decision = "LSE_SELECTED_AS_NEXT_PROVIDER_ROUTE"
        selected_provider = PRIMARY_PROVIDER_ID
        recommended_next_phase = "v2.10B ? LSE Acquisition Plan"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "route_status": route_status,
        "readiness_score": readiness_score,
        "route_decision": route_decision,
        "selected_provider": selected_provider,
        "recommended_next_phase": recommended_next_phase,
        "current_state": {
            "current_expanded_csv": rel(CURRENT_EXPANDED_CSV),
            "current_exclusions_csv": rel(CURRENT_EXCLUSIONS_CSV),
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "current_exclusions_rows": CURRENT_EXCLUSIONS_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "rows_needed_first_expansion": ROWS_NEEDED_FIRST_EXPANSION,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
        },
        "route_candidates": route_candidates,
        "planned_outputs_v2_10b": planned_outputs_v2_10b,
        "planned_controls": planned_controls,
        "validation_questions": validation_questions,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "network_download_performed": False,
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
            "plan_only": True,
        },
        "recommendation": (
            "Proceed to v2.10B LSE Acquisition Plan. Do not download or rebuild until the controlled acquisition contract is defined."
            if not blockers
            else "Resolve blockers before selecting the next provider."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.10A Next Provider Route")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Route status: **{route_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Route decision: **{route_decision}**")
    md.append(f"- Selected provider: **{selected_provider}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Current state")
    md.append("")
    md.append(f"- Current expanded universe: `{rel(CURRENT_EXPANDED_CSV)}`")
    md.append(f"- Current exclusions: `{rel(CURRENT_EXCLUSIONS_CSV)}`")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Current exclusions rows: {CURRENT_EXCLUSIONS_ROWS}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}")
    md.append(f"- Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}")
    md.append(f"- First expansion unlocked: {first_expansion_unlocked}")
    md.append(f"- Full source unlocked: {full_source_unlocked}")
    md.append("")
    md.append("## Route candidates")
    md.append("")
    for route in route_candidates:
        md.append(f"### {route['priority']}. {route['name']}")
        md.append("")
        md.append(f"- Provider ID: `{route['provider_id']}`")
        md.append(f"- Source URL: `{route['source_url']}`")
        md.append(f"- Download candidate URL: `{route['download_candidate_url']}`")
        md.append(f"- Type: {route['route_type']}")
        md.append(f"- Expected value: {route['expected_value']}")
        md.append(f"- Risk: {route['risk']}")
        md.append(f"- Expected coverage: {route['expected_coverage']}")
        md.append(f"- Why: {route['why']}")
        md.append(f"- Planned treatment: {route['planned_treatment']}")
        md.append(f"- Decision: **{route['decision']}**")
        md.append("")
    md.append("## Planned outputs for v2.10B")
    md.append("")
    for key, value in planned_outputs_v2_10b.items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Planned controls")
    md.append("")
    for item in planned_controls:
        md.append(f"- {item}")
    md.append("")
    md.append("## Validation questions")
    md.append("")
    for item in validation_questions:
        md.append(f"- {item}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- Network download performed: false")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("- Plan only: true")
    md.append("")
    md.append("## Positives")
    md.append("")
    if positives:
        for item in positives:
            md.append(f"- {item}")
    else:
        md.append("- No positives detected.")
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
    if warnings:
        for item in warnings:
            md.append(f"- {item}")
    else:
        md.append("- No warnings detected.")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.10A is route-selection plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.10A Next Provider Route")
    print("=" * 92)
    print(f"OK   Route status: {route_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Route decision: {route_decision}")
    print(f"OK   Selected provider: {selected_provider}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    print(f"OK   Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}")
    print(f"OK   Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}")
    print(f"OK   Route candidates: {len(route_candidates)}")
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
