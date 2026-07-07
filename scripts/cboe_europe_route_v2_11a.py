from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.11A"
METHOD = "cboe_europe_route_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

LSE_CLOSURE_JSON = OUT_DIR / "lse_closure_report_v2_10g.json"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

PROVIDER_ID = "cboe_europe_reference_data"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID

CBOE_EU_REFERENCE_DATA_URL = "https://www.cboe.com/europe/equities/support/reference_data/"
CBOE_EU_CXE_SYMBOLS_TRADED_URL = "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=cxe"
CBOE_EU_BXE_SYMBOLS_TRADED_URL = "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=bxe"
CBOE_EU_DXE_SYMBOLS_TRADED_URL = "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=dxe"
CBOE_EU_TRF_SYMBOLS_TRADED_URL = "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=trf"

OUT_JSON = OUT_DIR / "cboe_europe_route_v2_11a.json"
OUT_MD = OUT_DIR / "cboe_europe_route_v2_11a.md"
ROUTE_CANDIDATES_CSV = OUT_DIR / "cboe_europe_route_candidates_v2_11a.csv"
PLANNED_OUTPUTS_CSV = OUT_DIR / "cboe_europe_planned_outputs_v2_11a.csv"

CURRENT_EXPANDED_ROWS = 9200
CURRENT_EXCLUSIONS_ROWS = 10056

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

ROWS_NEEDED_FIRST_EXPANSION = 5800
ROWS_NEEDED_FULL_SOURCE = 40800


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

    lse_closure = read_json(LSE_CLOSURE_JSON)

    if not lse_closure.get("_exists"):
        blockers.append(f"Missing v2.10G LSE closure artifact: {rel(LSE_CLOSURE_JSON)}")
    else:
        positives.append(f"v2.10G LSE closure artifact found: {rel(LSE_CLOSURE_JSON)}")

    closure_status = lse_closure.get("closure_status")
    closure_decision = lse_closure.get("closure_decision")
    recommended_next_phase = lse_closure.get("recommended_next_phase")

    if closure_status == "LSE_CLOSED_ACCESSIBLE_BUT_NOT_USABLE_FOR_REBUILD":
        positives.append(f"v2.10G closure status accepted: {closure_status}")
    else:
        blockers.append(f"Unexpected v2.10G closure status: {closure_status}")

    if closure_decision == "LSE_CLOSED_NO_REBUILD_FALLBACK_REQUIRED":
        positives.append(f"v2.10G closure decision accepted: {closure_decision}")
    else:
        blockers.append(f"Unexpected v2.10G closure decision: {closure_decision}")

    if "Cboe Europe" in str(recommended_next_phase):
        positives.append(f"v2.10G recommended next phase accepted: {recommended_next_phase}")
    else:
        blockers.append(f"Unexpected v2.10G recommended next phase: {recommended_next_phase}")

    for path in [CURRENT_EXPANDED_CSV, CURRENT_EXCLUSIONS_CSV]:
        if path.exists():
            positives.append(f"Current source input available: {rel(path)}")
        else:
            blockers.append(f"Missing current source input: {rel(path)}")

    route_candidates = [
        {
            "priority": 1,
            "route_id": "cboe_europe_reference_data_page_probe",
            "name": "Cboe Europe Reference Data page",
            "url": CBOE_EU_REFERENCE_DATA_URL,
            "method": "GET",
            "expected_content_type": "text/html",
            "expected_value": "HIGH",
            "risk": "LOW_MEDIUM",
            "network_allowed_in": "v2.11B/v2.11C",
            "treatment": "Discover official Live Symbols CSV and Live Symbols Enhanced CSV links from the Cboe Europe Reference Data page.",
        },
        {
            "priority": 2,
            "route_id": "cboe_europe_live_symbols_csv",
            "name": "Cboe Europe Live Symbols CSV files",
            "url": "DISCOVER_FROM_REFERENCE_DATA_PAGE",
            "method": "GET",
            "expected_content_type": "text/csv",
            "expected_value": "HIGH",
            "risk": "LOW",
            "network_allowed_in": "v2.11C",
            "treatment": "Download only discovered official CSV files for BXE/CXE/DXE/TRF EU/TRF UK/SIS if present.",
        },
        {
            "priority": 3,
            "route_id": "cboe_europe_live_symbols_enhanced_csv",
            "name": "Cboe Europe Live Symbols Enhanced CSV files",
            "url": "DISCOVER_FROM_REFERENCE_DATA_PAGE",
            "method": "GET",
            "expected_content_type": "text/csv",
            "expected_value": "HIGH",
            "risk": "LOW",
            "network_allowed_in": "v2.11C",
            "treatment": "Prefer enhanced CSV if schema includes richer fields for symbol, name, currency, MIC, country, supported services or asset classification.",
        },
        {
            "priority": 4,
            "route_id": "cboe_europe_symbols_traded_pages",
            "name": "Cboe Europe Symbols Traded pages",
            "url": "CXE/BXE/DXE/TRF symbols_traded pages",
            "method": "GET",
            "expected_content_type": "text/html",
            "expected_value": "MEDIUM",
            "risk": "MEDIUM",
            "network_allowed_in": "v2.11C",
            "treatment": "Fallback page probe only if Reference Data page does not expose direct CSV files.",
        },
    ]

    planned_symbol_pages = [
        {
            "market": "CXE",
            "url": CBOE_EU_CXE_SYMBOLS_TRADED_URL,
            "planned_target": rel(PROVIDER_DIR / "cboe_europe_cxe_symbols_traded_page.html"),
        },
        {
            "market": "BXE",
            "url": CBOE_EU_BXE_SYMBOLS_TRADED_URL,
            "planned_target": rel(PROVIDER_DIR / "cboe_europe_bxe_symbols_traded_page.html"),
        },
        {
            "market": "DXE",
            "url": CBOE_EU_DXE_SYMBOLS_TRADED_URL,
            "planned_target": rel(PROVIDER_DIR / "cboe_europe_dxe_symbols_traded_page.html"),
        },
        {
            "market": "TRF",
            "url": CBOE_EU_TRF_SYMBOLS_TRADED_URL,
            "planned_target": rel(PROVIDER_DIR / "cboe_europe_trf_symbols_traded_page.html"),
        },
    ]

    planned_outputs = [
        {
            "output_type": "provider_dir",
            "path": rel(PROVIDER_DIR),
        },
        {
            "output_type": "route_plan_json",
            "path": rel(OUT_JSON),
        },
        {
            "output_type": "route_plan_md",
            "path": rel(OUT_MD),
        },
        {
            "output_type": "route_candidates_csv",
            "path": rel(ROUTE_CANDIDATES_CSV),
        },
        {
            "output_type": "planned_outputs_csv",
            "path": rel(PLANNED_OUTPUTS_CSV),
        },
        {
            "output_type": "v2_11b_acquisition_plan_json",
            "path": "outputs/full_universe_source_acquisition/cboe_europe_acquisition_plan_v2_11b.json",
        },
        {
            "output_type": "v2_11c_acquisition_real_json",
            "path": "outputs/full_universe_source_acquisition/cboe_europe_acquisition_real_v2_11c.json",
        },
        {
            "output_type": "v2_11d_validation_json",
            "path": "outputs/full_universe_source_acquisition/cboe_europe_validation_v2_11d.json",
        },
    ]

    expected_schema_candidates = {
        "symbol": ["symbol", "bats_name", "ticker", "instrument", "isin"],
        "issuer_name": ["company", "company_name", "name", "issuer", "security_name"],
        "market": ["market", "exchange", "book", "venue", "mic", "primary_market"],
        "asset_class": ["asset_class", "asset type", "security_type", "instrument_type"],
        "currency": ["currency", "trading_currency", "price_currency"],
        "country": ["country", "country_of_incorporation", "domicile"],
        "isin": ["isin", "isin_code"],
    }

    validation_questions = [
        "Does Cboe Europe expose stable official Live Symbols CSV files?",
        "Are CSV files available for BXE, CXE, DXE, TRF EU, TRF UK and/or SIS?",
        "Does enhanced CSV contain richer symbol/name/MIC/country/currency fields?",
        "How many rows exist before net-new filtering?",
        "How many exchange+ticker or MIC+ticker keys are net-new against expanded_universe_v2_8e?",
        "Are rows ordinary shares, ETFs, funds, ETCs or mixed instruments?",
        "Can Cboe Europe rows be normalized conservatively without brittle scraping?",
        "Does Cboe Europe unlock the 15000-row first expansion threshold?",
        "Should Cboe Europe be source provider, candidate provider, enrichment, reference-only or deferred?",
    ]

    warnings.append("v2.11A is route-selection only; no Cboe Europe data is downloaded in this phase.")
    warnings.append("Cboe Europe may include non-US symbols, multiple venues, MIC semantics and duplicate instruments across books.")
    warnings.append("European symbol semantics must not be merged blindly with US tickers.")
    warnings.append("Rows from TRF/APA/reporting routes may need separate classification from lit order book symbols.")
    warnings.append("Full 59k remains blocked until source reaches at least 50000 rows.")

    if blockers:
        route_status = "CBOE_EUROPE_ROUTE_BLOCKED"
        readiness_score = 0
        route_decision = "BLOCKED"
        next_phase = "Resolve blockers"
    else:
        route_status = "CBOE_EUROPE_ROUTE_READY"
        readiness_score = 92
        route_decision = "CBOE_EUROPE_SELECTED_AS_NEXT_PROVIDER_ROUTE"
        next_phase = "v2.11B ? Cboe Europe Acquisition Plan"

    with ROUTE_CANDIDATES_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "priority",
                "route_id",
                "name",
                "url",
                "method",
                "expected_content_type",
                "expected_value",
                "risk",
                "network_allowed_in",
                "treatment",
            ],
        )
        writer.writeheader()
        writer.writerows(route_candidates)

    with PLANNED_OUTPUTS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["output_type", "path"])
        writer.writeheader()
        writer.writerows(planned_outputs)

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "route_status": route_status,
        "readiness_score": readiness_score,
        "route_decision": route_decision,
        "recommended_next_phase": next_phase,
        "provider": {
            "provider_id": PROVIDER_ID,
            "provider_dir": rel(PROVIDER_DIR),
            "primary_route": "cboe_europe_reference_data_page_probe",
            "preferred_files": [
                "Live Symbols CSV",
                "Live Symbols Enhanced CSV",
            ],
            "markets_or_services_to_probe": [
                "BXE",
                "CXE",
                "DXE",
                "TRF EU",
                "TRF UK",
                "SIS",
            ],
        },
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
            "first_expansion_unlocked": False,
            "full_source_unlocked": False,
        },
        "route_candidates": route_candidates,
        "planned_symbol_pages": planned_symbol_pages,
        "planned_outputs": planned_outputs,
        "expected_schema_candidates": expected_schema_candidates,
        "validation_questions": validation_questions,
        "decision_gate": {
            "minimum_net_new_rows_to_consider_rebuild": ROWS_NEEDED_FIRST_EXPANSION,
            "rebuild_allowed_only_after": "v2.11D validation confirms usable schema, duplicate control and net-new rows.",
            "fallback_if_blocked": "Close Cboe Europe as blocked/reference-only and choose next provider route.",
        },
        "outputs": {
            "route_candidates_csv": rel(ROUTE_CANDIDATES_CSV),
            "planned_outputs_csv": rel(PLANNED_OUTPUTS_CSV),
            "route_json": rel(OUT_JSON),
            "route_md": rel(OUT_MD),
        },
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
            "route_selection_only": True,
        },
        "recommendation": (
            "Proceed to v2.11B Cboe Europe Acquisition Plan. Do not download until controlled acquisition contract is defined."
            if not blockers
            else "Resolve blockers before Cboe Europe route planning."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.11A Cboe Europe Route")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Route status: **{route_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Route decision: **{route_decision}**")
    md.append(f"- Recommended next phase: **{next_phase}**")
    md.append("")
    md.append("## Provider")
    md.append("")
    md.append(f"- Provider ID: `{PROVIDER_ID}`")
    md.append(f"- Provider dir: `{rel(PROVIDER_DIR)}`")
    md.append("- Primary route: `cboe_europe_reference_data_page_probe`")
    md.append("- Preferred files: `Live Symbols CSV`, `Live Symbols Enhanced CSV`")
    md.append("- Markets/services to probe: BXE, CXE, DXE, TRF EU, TRF UK, SIS")
    md.append("")
    md.append("## Current state")
    md.append("")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Current exclusions rows: {CURRENT_EXCLUSIONS_ROWS}")
    md.append(f"- Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}")
    md.append(f"- Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}")
    md.append("")
    md.append("## Route candidates")
    md.append("")
    for item in route_candidates:
        md.append(f"### {item['priority']}. {item['name']}")
        md.append("")
        md.append(f"- Route ID: `{item['route_id']}`")
        md.append(f"- URL: `{item['url']}`")
        md.append(f"- Method: {item['method']}")
        md.append(f"- Expected content type: {item['expected_content_type']}")
        md.append(f"- Expected value: {item['expected_value']}")
        md.append(f"- Risk: {item['risk']}")
        md.append(f"- Network allowed in: {item['network_allowed_in']}")
        md.append(f"- Treatment: {item['treatment']}")
        md.append("")
    md.append("## Planned symbol pages")
    md.append("")
    for item in planned_symbol_pages:
        md.append(f"- {item['market']}: `{item['url']}` -> `{item['planned_target']}`")
    md.append("")
    md.append("## Expected schema candidates")
    md.append("")
    for key, values in expected_schema_candidates.items():
        md.append(f"- {key}: {', '.join(values)}")
    md.append("")
    md.append("## Validation questions")
    md.append("")
    for item in validation_questions:
        md.append(f"- {item}")
    md.append("")
    md.append("## Decision gate")
    md.append("")
    md.append(f"- Minimum net-new rows to consider rebuild: {ROWS_NEEDED_FIRST_EXPANSION}")
    md.append("- Rebuild allowed only after v2.11D validates schema, duplicate control and net-new rows.")
    md.append("- Full 59k remains blocked until source reaches at least 50000 rows.")
    md.append("")
    md.append("## Outputs")
    md.append("")
    md.append(f"- Route candidates CSV: `{rel(ROUTE_CANDIDATES_CSV)}`")
    md.append(f"- Planned outputs CSV: `{rel(PLANNED_OUTPUTS_CSV)}`")
    md.append(f"- Route JSON: `{rel(OUT_JSON)}`")
    md.append(f"- Route report: `{rel(OUT_MD)}`")
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
    md.append("- Route selection only: true")
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
    md.append("Important: v2.11A is route-selection only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.11A Cboe Europe Route")
    print("=" * 92)
    print(f"OK   Route status: {route_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Route decision: {route_decision}")
    print(f"OK   Recommended next phase: {next_phase}")
    print(f"OK   Provider: {PROVIDER_ID}")
    print(f"OK   Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    print(f"OK   Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}")
    print(f"OK   Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}")
    print(f"OK   Route candidates: {len(route_candidates)}")
    print(f"OK   Planned symbol pages: {len(planned_symbol_pages)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Route candidates CSV written: {ROUTE_CANDIDATES_CSV}")
    print(f"OK   Planned outputs CSV written: {PLANNED_OUTPUTS_CSV}")
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
