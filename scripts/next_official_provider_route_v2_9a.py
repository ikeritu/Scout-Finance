from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.9A"
METHOD = "next_official_provider_route_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

CBOE_CLOSURE_JSON = OUT_DIR / "expanded_source_with_cboe_closure_report_v2_8g.json"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

OUT_JSON = OUT_DIR / "next_official_provider_route_v2_9a.json"
OUT_MD = OUT_DIR / "next_official_provider_route_v2_9a.md"

CURRENT_EXPANDED_ROWS = 9200
CURRENT_EXCLUSIONS_ROWS = 10056

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

ROWS_NEEDED_FIRST_EXPANSION = 5800
ROWS_NEEDED_FULL_SOURCE = 40800

PRIMARY_PROVIDER_ID = "otc_markets_stock_screener"

OTC_MARKETS_STOCK_SCREENER_URL = "https://www.otcmarkets.com/research/stock-screener"
OTC_MARKETS_DOWNLOAD_CSV_CANDIDATE_URL = "https://www.otcmarkets.com/research/stock-screener/api/downloadCSV?ce=true&sortField=volume&sortOrder=desc"

NASDAQ_SCREENER_URL = "https://www.nasdaq.com/market-activity/stocks/screener"
NYSE_DEEP_JS_STATUS = "DEFERRED_REQUIRES_DEEP_JS_PAYLOAD_REVIEW"
OPENFIGI_STATUS = "REFERENCE_OR_ENRICHMENT_ROUTE_REQUIRES_API_CONSTRAINT_REVIEW"


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

    cboe_closure = read_json(CBOE_CLOSURE_JSON)

    if not cboe_closure.get("_exists"):
        blockers.append(f"Missing v2.8G Cboe closure artifact: {rel(CBOE_CLOSURE_JSON)}")
    else:
        positives.append(f"v2.8G Cboe closure artifact found: {rel(CBOE_CLOSURE_JSON)}")

    closure_status = cboe_closure.get("closure_status")
    closure_decision = cboe_closure.get("closure_decision")

    if closure_status == "EXPANDED_SOURCE_WITH_CBOE_CLOSED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.8G closure status accepted: {closure_status}")
    else:
        blockers.append(f"Unexpected v2.8G closure status: {closure_status}")

    if closure_decision == "CBOE_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.8G closure decision accepted: {closure_decision}")
    else:
        blockers.append(f"Unexpected v2.8G closure decision: {closure_decision}")

    for path in [CURRENT_EXPANDED_CSV, CURRENT_EXCLUSIONS_CSV]:
        if path.exists():
            positives.append(f"Current source input available: {rel(path)}")
        else:
            blockers.append(f"Missing current source input: {rel(path)}")

    first_expansion_unlocked = CURRENT_EXPANDED_ROWS >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = CURRENT_EXPANDED_ROWS >= MIN_FULL_SOURCE_ROWS

    warnings.append(f"Current expanded source remains below first expansion threshold: {CURRENT_EXPANDED_ROWS} < {TARGET_FIRST_EXPANSION_ROWS}")
    warnings.append(f"Current expanded source remains below full-source threshold: {CURRENT_EXPANDED_ROWS} < {MIN_FULL_SOURCE_ROWS}")
    warnings.append("OTC Markets route may include OTCQX, OTCQB, OTCID, Pink Limited, international ordinary shares, ADRs and other securities; classification must be conservative.")
    warnings.append("OTC Markets CSV schema and licensing/usage constraints must be checked in v2.9B/v2.9C before rebuild.")
    warnings.append("Do not mix OTC candidates into main universe until a dedicated validation phase confirms schema, net-new rows, and instrument semantics.")

    route_candidates = [
        {
            "priority": 1,
            "provider_id": "otc_markets_stock_screener",
            "name": "OTC Markets Stock Screener",
            "source_url": OTC_MARKETS_STOCK_SCREENER_URL,
            "download_candidate_url": OTC_MARKETS_DOWNLOAD_CSV_CANDIDATE_URL,
            "route_type": "official_otc_markets_stock_screener_csv_candidate",
            "expected_value": "HIGH_FOR_15000_THRESHOLD",
            "risk": "MEDIUM",
            "expected_coverage": "Large OTC universe; may be enough to exceed 15000 if usable and net-new.",
            "why": "After Nasdaq Trader, SEC and Cboe, the remaining gap to 15000 is 5800 rows. OTC Markets has a broad official screener and download route candidate.",
            "planned_treatment": "Plan controlled acquisition first. Preserve raw CSV. Validate schema and net-new exchange+ticker rows before any rebuild.",
            "decision": "SELECTED_PRIMARY_ROUTE",
        },
        {
            "priority": 2,
            "provider_id": "nasdaq_stock_screener",
            "name": "Nasdaq Stock Screener",
            "source_url": NASDAQ_SCREENER_URL,
            "download_candidate_url": "",
            "route_type": "official_or_semi_official_nasdaq_screener_review",
            "expected_value": "LOW_TO_MEDIUM",
            "risk": "MEDIUM_HIGH",
            "expected_coverage": "May overlap heavily with Nasdaq Trader and SEC.",
            "why": "Could provide names/metadata but likely not enough net-new after existing Nasdaq/SEC routes.",
            "planned_treatment": "Keep as fallback or enrichment route.",
            "decision": "FALLBACK_ROUTE",
        },
        {
            "priority": 3,
            "provider_id": "nyse_deep_js_payload_review",
            "name": "NYSE Deep JS Payload Review",
            "source_url": "",
            "download_candidate_url": "",
            "route_type": "deferred_deep_js_route",
            "expected_value": "UNKNOWN",
            "risk": "HIGH",
            "expected_coverage": "Unknown until deep JS payload route is solved.",
            "why": "Previously deferred because v2.5G required deep JS payload review.",
            "planned_treatment": "Do not reopen until OTC route is resolved or explicitly prioritized.",
            "decision": NYSE_DEEP_JS_STATUS,
        },
        {
            "priority": 4,
            "provider_id": "openfigi_symbology",
            "name": "OpenFIGI / FIGI Symbology",
            "source_url": "https://www.openfigi.com/",
            "download_candidate_url": "",
            "route_type": "identifier_enrichment_or_api_route",
            "expected_value": "MEDIUM_FOR_ENRICHMENT_LOW_FOR_BULK_SOURCE",
            "risk": "MEDIUM_HIGH",
            "expected_coverage": "Potentially useful for identifier enrichment, but bulk universe acquisition requires API and limits review.",
            "why": "Good candidate for enrichment, not necessarily the next bulk source provider.",
            "planned_treatment": "Defer as enrichment route unless source expansion stalls.",
            "decision": OPENFIGI_STATUS,
        },
    ]

    planned_outputs_v2_9b = {
        "provider_dir": f"data/raw/source_providers/{PRIMARY_PROVIDER_ID}",
        "route_plan_json": "outputs/full_universe_source_acquisition/otc_markets_acquisition_plan_v2_9b.json",
        "route_plan_md": "outputs/full_universe_source_acquisition/otc_markets_acquisition_plan_v2_9b.md",
        "raw_csv_target": f"data/raw/source_providers/{PRIMARY_PROVIDER_ID}/otc_markets_stock_screener_raw.csv",
        "schema_probe_csv": "outputs/full_universe_source_acquisition/otc_markets_schema_probe_v2_9c.csv",
        "acquisition_json": "outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.json",
        "acquisition_md": "outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.md",
    }

    planned_controls = [
        "v2.9B must be plan-only.",
        "v2.9C may download only OTC Markets route candidates selected in v2.9B.",
        "Preserve raw CSV exactly.",
        "Report URL, status code, content type, size and SHA256.",
        "Do not rebuild expanded_universe in acquisition phase.",
        "Do not overwrite active MVP outputs.",
        "Do not run scoring.",
        "Do not call OpenAI.",
        "Do not call broker APIs.",
        "Do not launch full 59k universe.",
        "Classify OTC rows conservatively until post-acquisition validation.",
    ]

    validation_questions = [
        "How many rows are available in OTC Markets CSV?",
        "Which columns are present?",
        "Is there a clear ticker/symbol field?",
        "Is there a company/security name field?",
        "Is market tier available: OTCQX, OTCQB, OTCID, Pink Limited, etc.?",
        "Is country available?",
        "How many exchange+ticker keys are net-new against expanded_universe_v2_8e?",
        "Are rows equities, ADRs, funds, preferreds, warrants, or mixed instruments?",
        "Can OTC Markets unlock 15000 rows safely?",
        "Should OTC Markets be primary source, candidate-provider source, enrichment source, or deferred?",
    ]

    if blockers:
        route_status = "NEXT_OFFICIAL_PROVIDER_ROUTE_BLOCKED"
        readiness_score = 0
        route_decision = "BLOCKED"
        selected_provider = None
        recommended_next_phase = "Resolve blockers"
    else:
        route_status = "NEXT_OFFICIAL_PROVIDER_ROUTE_READY"
        readiness_score = 92
        route_decision = "OTC_MARKETS_SELECTED_AS_NEXT_PROVIDER_ROUTE"
        selected_provider = PRIMARY_PROVIDER_ID
        recommended_next_phase = "v2.9B ? OTC Markets Acquisition Plan"

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
        "planned_outputs_v2_9b_v2_9c": planned_outputs_v2_9b,
        "planned_controls": planned_controls,
        "validation_questions": validation_questions,
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
            "plan_only": True,
        },
        "recommendation": (
            "Proceed to v2.9B with OTC Markets acquisition plan. Do not download or rebuild until v2.9B defines the controlled acquisition contract."
            if not blockers
            else "Resolve blockers before selecting next provider."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.9A Next Official Provider Route")
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
    md.append("## Planned outputs for v2.9B/v2.9C")
    md.append("")
    for key, value in planned_outputs_v2_9b.items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Planned controls")
    md.append("")
    for control in planned_controls:
        md.append(f"- {control}")
    md.append("")
    md.append("## Validation questions")
    md.append("")
    for question in validation_questions:
        md.append(f"- {question}")
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
    md.append("Important: v2.9A is route-selection plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.9A Next Official Provider Route")
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
