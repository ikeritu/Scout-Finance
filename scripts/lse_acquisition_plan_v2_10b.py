from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.10B"
METHOD = "lse_acquisition_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

ROUTE_JSON = OUT_DIR / "next_provider_route_v2_10a.json"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

PROVIDER_ID = "lse_issuers_and_instruments_reports"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID

LSE_REPORTS_URL = "https://www.londonstockexchange.com/reports"
LSE_ISSUERS_REPORTS_URL = "https://www.londonstockexchange.com/reports?tab=issuers"
LSE_INSTRUMENTS_REPORTS_URL = "https://www.londonstockexchange.com/reports?tab=instruments"
LSE_HISTORICAL_ANALYTICS_URL = "https://www.londonstockexchange.com/equities-trading/market-data/historical-analytics-data-products"
CBOE_EU_REFERENCE_DATA_URL = "https://www.cboe.com/europe/equities/support/reference_data/"

OUT_JSON = OUT_DIR / "lse_acquisition_plan_v2_10b.json"
OUT_MD = OUT_DIR / "lse_acquisition_plan_v2_10b.md"
PLANNED_LINKS_CSV = OUT_DIR / "lse_discovered_links_v2_10b.csv"
ROUTE_PROBE_CSV = OUT_DIR / "lse_route_probe_v2_10b.csv"

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

    route = read_json(ROUTE_JSON)

    if not route.get("_exists"):
        blockers.append(f"Missing v2.10A route artifact: {rel(ROUTE_JSON)}")
    else:
        positives.append(f"v2.10A route artifact found: {rel(ROUTE_JSON)}")

    route_status = route.get("route_status")
    route_decision = route.get("route_decision")
    selected_provider = route.get("selected_provider")

    if route_status == "NEXT_PROVIDER_ROUTE_READY":
        positives.append(f"v2.10A route status accepted: {route_status}")
    else:
        blockers.append(f"Unexpected v2.10A route status: {route_status}")

    if route_decision == "LSE_SELECTED_AS_NEXT_PROVIDER_ROUTE":
        positives.append(f"v2.10A route decision accepted: {route_decision}")
    else:
        blockers.append(f"Unexpected v2.10A route decision: {route_decision}")

    if selected_provider == PROVIDER_ID:
        positives.append(f"Selected provider accepted: {selected_provider}")
    else:
        blockers.append(f"Unexpected selected provider: {selected_provider}")

    for path in [CURRENT_EXPANDED_CSV, CURRENT_EXCLUSIONS_CSV]:
        if path.exists():
            positives.append(f"Current source input available: {rel(path)}")
        else:
            blockers.append(f"Missing current source input: {rel(path)}")

    warnings.append("LSE reports may be dynamic and may require route discovery in v2.10C.")
    warnings.append("Prefer stable official report downloads over brittle scraping.")
    warnings.append("LSE may include mixed instruments: shares, ETFs, funds, bonds, warrants or other securities.")
    warnings.append("MIC, currency, segment and country semantics must be preserved conservatively.")
    warnings.append("Full 59k remains blocked until source reaches at least 50000 rows.")

    planned_routes = [
        {
            "priority": 1,
            "route_id": "lse_reports_page_probe",
            "name": "LSE Reports page probe",
            "url": LSE_REPORTS_URL,
            "method": "GET",
            "expected_content_type": "text/html",
            "network_allowed_in": "v2.10C",
            "expected_value": "HIGH",
            "risk": "LOW_MEDIUM",
            "treatment": "Download official Reports page HTML, preserve raw, discover issuer/instrument report links.",
        },
        {
            "priority": 2,
            "route_id": "lse_issuers_reports_tab_probe",
            "name": "LSE Issuers reports tab/page probe",
            "url": LSE_ISSUERS_REPORTS_URL,
            "method": "GET",
            "expected_content_type": "text/html",
            "network_allowed_in": "v2.10C",
            "expected_value": "HIGH",
            "risk": "MEDIUM",
            "treatment": "Probe issuer-specific report route if tab URL resolves server-side or exposes embedded data.",
        },
        {
            "priority": 3,
            "route_id": "lse_instruments_reports_tab_probe",
            "name": "LSE Instruments reports tab/page probe",
            "url": LSE_INSTRUMENTS_REPORTS_URL,
            "method": "GET",
            "expected_content_type": "text/html",
            "network_allowed_in": "v2.10C",
            "expected_value": "HIGH",
            "risk": "MEDIUM",
            "treatment": "Probe instrument-specific report route if tab URL resolves server-side or exposes embedded data.",
        },
        {
            "priority": 4,
            "route_id": "lse_historical_analytics_data_products_probe",
            "name": "LSE Historical and analytics data products probe",
            "url": LSE_HISTORICAL_ANALYTICS_URL,
            "method": "GET",
            "expected_content_type": "text/html",
            "network_allowed_in": "v2.10C",
            "expected_value": "MEDIUM",
            "risk": "MEDIUM",
            "treatment": "Reference route for Daily Tradeable Instruments Report or product documentation if public download route exists.",
        },
    ]

    fallback_routes = [
        {
            "priority": 1,
            "provider_id": "cboe_europe_reference_data",
            "name": "Cboe Europe Equities Reference Data",
            "url": CBOE_EU_REFERENCE_DATA_URL,
            "decision": "FALLBACK_IF_LSE_BLOCKED",
            "reason": "Official European exchange/operator source for reference data.",
        }
    ]

    planned_outputs_v2_10c = {
        "provider_dir": rel(PROVIDER_DIR),
        "raw_reports_page_html": rel(PROVIDER_DIR / "lse_reports_page.html"),
        "raw_issuers_page_html": rel(PROVIDER_DIR / "lse_issuers_reports_page.html"),
        "raw_instruments_page_html": rel(PROVIDER_DIR / "lse_instruments_reports_page.html"),
        "raw_historical_analytics_page_html": rel(PROVIDER_DIR / "lse_historical_analytics_data_products_page.html"),
        "downloaded_report_candidates_dir": rel(PROVIDER_DIR / "report_candidates"),
        "acquisition_json": "outputs/full_universe_source_acquisition/lse_acquisition_real_v2_10c.json",
        "acquisition_md": "outputs/full_universe_source_acquisition/lse_acquisition_real_v2_10c.md",
        "discovered_links_csv": "outputs/full_universe_source_acquisition/lse_discovered_links_v2_10c.csv",
        "schema_probe_csv": "outputs/full_universe_source_acquisition/lse_schema_probe_v2_10c.csv",
        "sample_csv": "outputs/full_universe_source_acquisition/lse_sample_v2_10c.csv",
    }

    acquisition_controls_v2_10c = [
        "Network download allowed only for planned LSE routes.",
        "Preserve every raw HTML/report file exactly.",
        "Report URL, status code, content type, size and SHA256 for every request.",
        "Discover candidate links only from official LSE pages downloaded in v2.10C.",
        "Download only official CSV/XLS/XLSX/ZIP/JSON report candidates discovered from LSE pages.",
        "Do not normalize into expanded_universe during acquisition.",
        "Do not rebuild expanded_universe.",
        "Do not overwrite active MVP outputs.",
        "Do not execute scoring.",
        "Do not call OpenAI.",
        "Do not call broker APIs.",
        "Do not launch full 59k universe.",
    ]

    expected_schema_candidates = {
        "symbol_candidates": [
            "symbol",
            "ticker",
            "tidm",
            "sedol",
            "isin",
            "instrument code",
            "epic",
        ],
        "name_candidates": [
            "issuer name",
            "company name",
            "security name",
            "instrument name",
            "name",
        ],
        "market_candidates": [
            "market",
            "segment",
            "trading service",
            "market segment",
            "admission market",
        ],
        "instrument_type_candidates": [
            "instrument type",
            "security type",
            "type",
            "sector",
            "asset class",
        ],
        "country_candidates": [
            "country",
            "country of incorporation",
            "domicile",
            "issuer country",
        ],
        "currency_candidates": [
            "currency",
            "trading currency",
            "price currency",
        ],
        "isin_candidates": [
            "isin",
            "isin code",
        ],
    }

    validation_contract_v2_10d = [
        "Validate whether LSE produced any downloadable report file usable for source expansion.",
        "Detect row count and schema for each downloaded candidate file.",
        "Detect usable identifier fields: TIDM/ticker, ISIN, SEDOL, issuer name, market/segment and instrument type.",
        "Avoid treating ISIN-only rows as ticker-ready unless a market symbol is present.",
        "Normalize candidates conservatively with source_provider=lse_issuers_and_instruments_reports.",
        "Compute duplicate keys inside LSE candidate source.",
        "Compute net-new candidate rows against expanded_universe_v2_8e.",
        "Decide whether LSE is usable for isolated rebuild, reference/enrichment only, or blocked.",
        "Confirm whether LSE can unlock the 15000-row first expansion threshold.",
    ]

    planned_decision_gate = {
        "minimum_net_new_rows_to_consider_rebuild": ROWS_NEEDED_FIRST_EXPANSION,
        "rebuild_allowed_if": [
            "At least one official LSE report file is downloaded successfully.",
            "Schema has usable symbol/ticker or safely mappable market identifier.",
            "Rows can be normalized to canonical schema without brittle scraping.",
            "Net-new rows are meaningful enough to justify rebuild.",
            "Duplicate keys are controlled.",
            "Instrument semantics are acceptable or conservatively classified.",
        ],
        "rebuild_not_allowed_if": [
            "LSE page is fully dynamic and exposes no stable report/download path.",
            "Only PDFs or non-tabular documents are available.",
            "No usable symbol/ticker/identifier field is available.",
            "Rows are too ambiguous or mixed without safe classification.",
            "Licensing/usage constraints make storage unsuitable.",
            "Net-new rows are far below threshold.",
        ],
        "fallback_if_blocked": "Switch to v2.11A Cboe Europe Reference Data Route or close LSE as blocked.",
    }

    if blockers:
        plan_status = "LSE_ACQUISITION_PLAN_BLOCKED"
        readiness_score = 0
        plan_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        plan_status = "LSE_ACQUISITION_PLAN_READY"
        readiness_score = 90
        plan_decision = "LSE_CONTROLLED_ACQUISITION_APPROVED"
        recommended_next_phase = "v2.10C ? LSE Acquisition Real"

    with PLANNED_LINKS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "priority",
                "route_id",
                "name",
                "url",
                "method",
                "expected_content_type",
                "network_allowed_in",
                "expected_value",
                "risk",
                "treatment",
            ],
        )
        writer.writeheader()
        writer.writerows(planned_routes)

    with ROUTE_PROBE_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "provider_id",
                "route_id",
                "route_status",
                "network_download_performed",
                "planned_for_phase",
                "notes",
            ],
        )
        writer.writeheader()
        for route_item in planned_routes:
            writer.writerow({
                "provider_id": PROVIDER_ID,
                "route_id": route_item["route_id"],
                "route_status": "PLANNED_NOT_DOWNLOADED",
                "network_download_performed": "False",
                "planned_for_phase": "v2.10C",
                "notes": route_item["treatment"],
            })

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "plan_status": plan_status,
        "readiness_score": readiness_score,
        "plan_decision": plan_decision,
        "recommended_next_phase": recommended_next_phase,
        "provider": {
            "provider_id": PROVIDER_ID,
            "provider_dir": rel(PROVIDER_DIR),
            "primary_route": "lse_reports_page_probe",
            "fallback_provider": "cboe_europe_reference_data",
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
        "planned_routes_v2_10c": planned_routes,
        "fallback_routes": fallback_routes,
        "planned_outputs_v2_10c": planned_outputs_v2_10c,
        "expected_schema_candidates": expected_schema_candidates,
        "acquisition_controls_v2_10c": acquisition_controls_v2_10c,
        "validation_contract_v2_10d": validation_contract_v2_10d,
        "planned_decision_gate": planned_decision_gate,
        "outputs": {
            "planned_links_csv": rel(PLANNED_LINKS_CSV),
            "route_probe_csv": rel(ROUTE_PROBE_CSV),
            "plan_json": rel(OUT_JSON),
            "plan_md": rel(OUT_MD),
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
            "plan_only": True,
        },
        "recommendation": (
            "Proceed to v2.10C controlled LSE acquisition. Do not rebuild until v2.10D validates schema and net-new coverage."
            if not blockers
            else "Resolve blockers before LSE acquisition."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.10B LSE Acquisition Plan")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Plan status: **{plan_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Plan decision: **{plan_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Provider")
    md.append("")
    md.append(f"- Provider ID: `{PROVIDER_ID}`")
    md.append(f"- Provider dir: `{rel(PROVIDER_DIR)}`")
    md.append("- Primary route: `lse_reports_page_probe`")
    md.append("- Fallback provider: `cboe_europe_reference_data`")
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
    md.append("")
    md.append("## Planned routes for v2.10C")
    md.append("")
    for route_item in planned_routes:
        md.append(f"### {route_item['priority']}. {route_item['name']}")
        md.append("")
        md.append(f"- Route ID: `{route_item['route_id']}`")
        md.append(f"- URL: `{route_item['url']}`")
        md.append(f"- Method: {route_item['method']}")
        md.append(f"- Expected content type: {route_item['expected_content_type']}")
        md.append(f"- Network allowed in: {route_item['network_allowed_in']}")
        md.append(f"- Expected value: {route_item['expected_value']}")
        md.append(f"- Risk: {route_item['risk']}")
        md.append(f"- Treatment: {route_item['treatment']}")
        md.append("")
    md.append("## Fallback routes")
    md.append("")
    for route_item in fallback_routes:
        md.append(f"- {route_item['name']} ? `{route_item['url']}` ? {route_item['decision']}")
    md.append("")
    md.append("## Planned outputs for v2.10C")
    md.append("")
    for key, value in planned_outputs_v2_10c.items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Expected schema candidates")
    md.append("")
    for key, values in expected_schema_candidates.items():
        md.append(f"- {key}: {', '.join(values)}")
    md.append("")
    md.append("## Acquisition controls for v2.10C")
    md.append("")
    for item in acquisition_controls_v2_10c:
        md.append(f"- {item}")
    md.append("")
    md.append("## Validation contract for v2.10D")
    md.append("")
    for item in validation_contract_v2_10d:
        md.append(f"- {item}")
    md.append("")
    md.append("## Decision gate")
    md.append("")
    md.append(f"- Minimum net-new rows to consider rebuild: {ROWS_NEEDED_FIRST_EXPANSION}")
    md.append(f"- Fallback if blocked: {planned_decision_gate['fallback_if_blocked']}")
    md.append("")
    md.append("### Rebuild allowed if")
    md.append("")
    for item in planned_decision_gate["rebuild_allowed_if"]:
        md.append(f"- {item}")
    md.append("")
    md.append("### Rebuild not allowed if")
    md.append("")
    for item in planned_decision_gate["rebuild_not_allowed_if"]:
        md.append(f"- {item}")
    md.append("")
    md.append("## Outputs")
    md.append("")
    md.append(f"- Planned links CSV: `{rel(PLANNED_LINKS_CSV)}`")
    md.append(f"- Route probe CSV: `{rel(ROUTE_PROBE_CSV)}`")
    md.append(f"- Plan JSON: `{rel(OUT_JSON)}`")
    md.append(f"- Plan report: `{rel(OUT_MD)}`")
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
    md.append("Important: v2.10B is plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.10B LSE Acquisition Plan")
    print("=" * 92)
    print(f"OK   Plan status: {plan_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Plan decision: {plan_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Provider: {PROVIDER_ID}")
    print(f"OK   Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    print(f"OK   Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}")
    print(f"OK   Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}")
    print(f"OK   Planned routes: {len(planned_routes)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Planned links written: {PLANNED_LINKS_CSV}")
    print(f"OK   Route probe written: {ROUTE_PROBE_CSV}")
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
