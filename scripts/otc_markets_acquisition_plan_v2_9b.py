from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.9B"
METHOD = "otc_markets_acquisition_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

ROUTE_JSON = OUT_DIR / "next_official_provider_route_v2_9a.json"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

PROVIDER_ID = "otc_markets_stock_screener"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID

OTC_SCREENER_PAGE_URL = "https://www.otcmarkets.com/research/stock-screener"
OTC_DOWNLOAD_CSV_URL = "https://www.otcmarkets.com/research/stock-screener/api/downloadCSV?ce=true&sortField=volume&sortOrder=desc"

OUT_JSON = OUT_DIR / "otc_markets_acquisition_plan_v2_9b.json"
OUT_MD = OUT_DIR / "otc_markets_acquisition_plan_v2_9b.md"

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
        blockers.append(f"Missing v2.9A route artifact: {rel(ROUTE_JSON)}")
    else:
        positives.append(f"v2.9A route artifact found: {rel(ROUTE_JSON)}")

    route_status = route.get("route_status")
    route_decision = route.get("route_decision")
    selected_provider = route.get("selected_provider")

    if route_status == "NEXT_OFFICIAL_PROVIDER_ROUTE_READY":
        positives.append(f"v2.9A route status accepted: {route_status}")
    else:
        blockers.append(f"Unexpected v2.9A route status: {route_status}")

    if route_decision == "OTC_MARKETS_SELECTED_AS_NEXT_PROVIDER_ROUTE":
        positives.append(f"v2.9A route decision accepted: {route_decision}")
    else:
        blockers.append(f"Unexpected v2.9A route decision: {route_decision}")

    if selected_provider == PROVIDER_ID:
        positives.append(f"Selected provider accepted: {selected_provider}")
    else:
        blockers.append(f"Unexpected selected provider: {selected_provider}")

    for path in [CURRENT_EXPANDED_CSV, CURRENT_EXCLUSIONS_CSV]:
        if path.exists():
            positives.append(f"Current source input available: {rel(path)}")
        else:
            blockers.append(f"Missing current source input: {rel(path)}")

    warnings.append("OTC Markets may include mixed instruments: equities, ADRs, preferreds, funds, rights, warrants or international securities.")
    warnings.append("OTC market tier and instrument semantics must be validated before any rebuild.")
    warnings.append("Rows must be treated as candidate-provider rows until v2.9D validation confirms usability.")
    warnings.append("Do not use OTC data downstream before validation and optional isolated rebuild.")
    warnings.append("Full 59k remains blocked until source reaches at least 50000 rows.")

    planned_routes = [
        {
            "priority": 1,
            "route_id": "otc_markets_stock_screener_download_csv",
            "name": "OTC Markets Stock Screener CSV download",
            "page_url": OTC_SCREENER_PAGE_URL,
            "download_url": OTC_DOWNLOAD_CSV_URL,
            "method": "GET",
            "expected_content_type": "text/csv_or_octet_stream",
            "expected_value": "HIGH",
            "risk": "MEDIUM",
            "treatment": "Primary route for v2.9C. Download raw CSV only, preserve exact bytes, then schema probe.",
        },
        {
            "priority": 2,
            "route_id": "otc_markets_stock_screener_page_probe",
            "name": "OTC Markets Stock Screener page probe",
            "page_url": OTC_SCREENER_PAGE_URL,
            "download_url": OTC_SCREENER_PAGE_URL,
            "method": "GET",
            "expected_content_type": "text/html",
            "expected_value": "MEDIUM",
            "risk": "LOW_MEDIUM",
            "treatment": "Secondary route for HTML/page metadata and possible alternative download discovery.",
        },
    ]

    planned_outputs_v2_9c = {
        "provider_dir": rel(PROVIDER_DIR),
        "raw_page_html": rel(PROVIDER_DIR / "otc_markets_stock_screener_page.html"),
        "raw_csv": rel(PROVIDER_DIR / "otc_markets_stock_screener_raw.csv"),
        "schema_probe_csv": "outputs/full_universe_source_acquisition/otc_markets_schema_probe_v2_9c.csv",
        "sample_csv": "outputs/full_universe_source_acquisition/otc_markets_sample_v2_9c.csv",
        "acquisition_json": "outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.json",
        "acquisition_md": "outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.md",
    }

    expected_schema_candidates = {
        "symbol_candidates": [
            "symbol",
            "ticker",
            "security symbol",
            "otc symbol",
        ],
        "name_candidates": [
            "security name",
            "company name",
            "name",
            "issuer name",
        ],
        "market_tier_candidates": [
            "market",
            "market tier",
            "tier",
            "otc market",
        ],
        "country_candidates": [
            "country",
            "country of incorporation",
            "domicile",
        ],
        "security_type_candidates": [
            "security type",
            "type",
            "instrument type",
        ],
    }

    acquisition_controls_v2_9c = [
        "Network download allowed only for OTC Markets planned routes.",
        "Preserve raw HTML and raw CSV exactly.",
        "Report URL, status code, content type, size and SHA256 for every request.",
        "Do not normalize into expanded_universe during acquisition.",
        "Do not rebuild expanded_universe.",
        "Do not overwrite active MVP outputs.",
        "Do not execute scoring.",
        "Do not call OpenAI.",
        "Do not call broker APIs.",
        "Do not launch full 59k universe.",
        "Write schema probe and sample only.",
    ]

    validation_contract_v2_9d = [
        "Validate row count of OTC raw CSV.",
        "Detect symbol/ticker field.",
        "Detect company/security name field.",
        "Detect market tier if present.",
        "Detect country if present.",
        "Detect instrument/security type if present.",
        "Normalize candidates conservatively.",
        "Compute duplicate exchange+ticker keys inside OTC source.",
        "Compute net-new exchange+ticker keys against expanded_universe_v2_8e.",
        "Classify OTC rows as candidate-provider rows until post-rebuild validation.",
        "Decide whether OTC is usable as provider, enrichment source, reference-only or deferred.",
        "Confirm whether OTC can unlock 15000 rows.",
    ]

    planned_decision_gate = {
        "minimum_net_new_rows_to_consider_rebuild": ROWS_NEEDED_FIRST_EXPANSION,
        "rebuild_allowed_if": [
            "OTC CSV download succeeds.",
            "Schema has usable symbol/ticker field.",
            "Rows can be normalized to canonical schema.",
            "Net-new exchange+ticker rows are meaningful.",
            "Duplicate keys are controlled.",
            "Instrument semantics are acceptable or conservatively classified.",
        ],
        "rebuild_not_allowed_if": [
            "No usable symbol/ticker field.",
            "CSV is blocked, empty, HTML disguised as CSV, or not reproducible.",
            "Schema cannot be interpreted without brittle scraping.",
            "Rows are not securities or are too ambiguous.",
            "Licensing/usage constraints make storage unsuitable.",
        ],
    }

    if blockers:
        plan_status = "OTC_MARKETS_ACQUISITION_PLAN_BLOCKED"
        readiness_score = 0
        plan_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        plan_status = "OTC_MARKETS_ACQUISITION_PLAN_READY"
        readiness_score = 92
        plan_decision = "OTC_MARKETS_CONTROLLED_ACQUISITION_APPROVED"
        recommended_next_phase = "v2.9C ? OTC Markets Acquisition Real"

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
            "primary_route": "otc_markets_stock_screener_download_csv",
            "secondary_route": "otc_markets_stock_screener_page_probe",
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
        "planned_routes_v2_9c": planned_routes,
        "planned_outputs_v2_9c": planned_outputs_v2_9c,
        "expected_schema_candidates": expected_schema_candidates,
        "acquisition_controls_v2_9c": acquisition_controls_v2_9c,
        "validation_contract_v2_9d": validation_contract_v2_9d,
        "planned_decision_gate": planned_decision_gate,
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
            "Proceed to v2.9C controlled OTC Markets acquisition. Do not rebuild until v2.9D validates schema and net-new coverage."
            if not blockers
            else "Resolve blockers before OTC Markets acquisition."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.9B OTC Markets Acquisition Plan")
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
    md.append(f"- Primary route: `otc_markets_stock_screener_download_csv`")
    md.append(f"- Secondary route: `otc_markets_stock_screener_page_probe`")
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
    md.append("## Planned routes for v2.9C")
    md.append("")
    for route in planned_routes:
        md.append(f"### {route['priority']}. {route['name']}")
        md.append("")
        md.append(f"- Route ID: `{route['route_id']}`")
        md.append(f"- Page URL: `{route['page_url']}`")
        md.append(f"- Download URL: `{route['download_url']}`")
        md.append(f"- Method: {route['method']}")
        md.append(f"- Expected content type: {route['expected_content_type']}")
        md.append(f"- Expected value: {route['expected_value']}")
        md.append(f"- Risk: {route['risk']}")
        md.append(f"- Treatment: {route['treatment']}")
        md.append("")
    md.append("## Planned outputs for v2.9C")
    md.append("")
    for key, value in planned_outputs_v2_9c.items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Expected schema candidates")
    md.append("")
    for key, values in expected_schema_candidates.items():
        md.append(f"- {key}: {', '.join(values)}")
    md.append("")
    md.append("## Acquisition controls for v2.9C")
    md.append("")
    for control in acquisition_controls_v2_9c:
        md.append(f"- {control}")
    md.append("")
    md.append("## Validation contract for v2.9D")
    md.append("")
    for item in validation_contract_v2_9d:
        md.append(f"- {item}")
    md.append("")
    md.append("## Decision gate")
    md.append("")
    md.append(f"- Minimum net-new rows to consider rebuild: {ROWS_NEEDED_FIRST_EXPANSION}")
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
    md.append("Important: v2.9B is plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.9B OTC Markets Acquisition Plan")
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
