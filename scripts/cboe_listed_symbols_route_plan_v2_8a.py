from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.8A"
METHOD = "cboe_listed_symbols_route_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

SEC_CLOSURE_JSON = OUT_DIR / "expanded_source_with_sec_closure_report_v2_7d.json"

OUT_JSON = OUT_DIR / "cboe_listed_symbols_route_plan_v2_8a.json"
OUT_MD = OUT_DIR / "cboe_listed_symbols_route_plan_v2_8a.md"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_7b.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_7b.csv"

PROVIDER_ID = "cboe_listed_symbols"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID

CBOE_LISTED_SYMBOLS_URL = "https://www.cboe.com/us/equities/market_statistics/listed_symbols/"
CBOE_SYMBOLS_TRADED_URL = "https://www.cboe.com/us/equities/market_statistics/symbols_traded/"

CURRENT_EXPANDED_ROWS = 8007
CURRENT_EXCLUSIONS_ROWS = 10056

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

ROWS_NEEDED_FIRST_EXPANSION = 6993
ROWS_NEEDED_FULL_SOURCE = 41993


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

    sec_closure = read_json(SEC_CLOSURE_JSON)

    if not sec_closure.get("_exists"):
        blockers.append(f"Missing v2.7D SEC closure artifact: {rel(SEC_CLOSURE_JSON)}")
    else:
        positives.append(f"v2.7D SEC closure artifact found: {rel(SEC_CLOSURE_JSON)}")

    closure_status = sec_closure.get("closure_status")
    closure_decision = sec_closure.get("closure_decision")

    if closure_status == "EXPANDED_SOURCE_WITH_SEC_CLOSED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.7D closure status accepted: {closure_status}")
    else:
        blockers.append(f"Unexpected v2.7D closure status: {closure_status}")

    if closure_decision == "SEC_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.7D closure decision accepted: {closure_decision}")
    else:
        blockers.append(f"Unexpected v2.7D closure decision: {closure_decision}")

    required_inputs = [
        CURRENT_EXPANDED_CSV,
        CURRENT_EXCLUSIONS_CSV,
    ]

    for path in required_inputs:
        if not path.exists():
            blockers.append(f"Missing required current source file: {rel(path)}")
        else:
            positives.append(f"Required current source file available: {rel(path)}")

    warnings.append("Cboe route may add limited rows because current universe already includes Cboe BZX rows from Nasdaq Trader otherlisted.")
    warnings.append("Cboe Listed Symbols may be narrower than Symbols Traded; v2.8B should preserve raw files and report row/schema before any rebuild.")
    warnings.append("Full 59k remains blocked until enough additional official provider rows are validated.")

    route_candidates = [
        {
            "priority": 1,
            "route_id": "cboe_us_equities_listed_symbols",
            "name": "Cboe U.S. Equities Listed Symbols",
            "source_url": CBOE_LISTED_SYMBOLS_URL,
            "route_type": "official_cboe_listed_symbols",
            "expected_download_options": ["CSV", "XML"],
            "expected_value": "MEDIUM",
            "risk": "MEDIUM",
            "why": "Official Cboe listed-symbol page. Most relevant if it provides securities actually listed on Cboe.",
            "planned_treatment": "Acquire raw CSV/XML in isolated provider folder, normalize only after schema detection, then validate net new rows against expanded_universe_v2_7b.",
        },
        {
            "priority": 2,
            "route_id": "cboe_us_equities_symbols_traded",
            "name": "Cboe U.S. Equities Symbols Traded",
            "source_url": CBOE_SYMBOLS_TRADED_URL,
            "route_type": "official_cboe_symbols_traded_reference",
            "expected_download_options": ["CSV", "XML"],
            "expected_value": "LOW_TO_MEDIUM",
            "risk": "MEDIUM",
            "why": "Official Cboe symbols-traded reference page. Useful for reference coverage, but may include symbols traded on Cboe rather than listed by Cboe.",
            "planned_treatment": "Acquire only as secondary/reference route unless listed-symbols route fails or has insufficient schema.",
        },
    ]

    planned_outputs_v2_8b = {
        "provider_dir": rel(PROVIDER_DIR),
        "raw_listed_symbols_file": rel(PROVIDER_DIR / "cboe_listed_symbols_raw.csv"),
        "raw_symbols_traded_file": rel(PROVIDER_DIR / "cboe_symbols_traded_raw.csv"),
        "normalized_csv": rel(PROVIDER_DIR / "cboe_listed_symbols_normalized.csv"),
        "acquisition_json": "outputs/full_universe_source_acquisition/cboe_listed_symbols_acquisition_real_v2_8b.json",
        "acquisition_md": "outputs/full_universe_source_acquisition/cboe_listed_symbols_acquisition_real_v2_8b.md",
        "schema_probe_csv": "outputs/full_universe_source_acquisition/cboe_listed_symbols_schema_probe_v2_8b.csv",
    }

    expected_normalized_columns = [
        "ticker",
        "company_name",
        "exchange",
        "country",
        "source_provider",
        "source_file",
        "instrument_type",
        "instrument_scope",
        "classification_confidence",
        "classification_reason",
        "sector",
        "industry",
        "market_cap",
        "raw_symbol",
        "raw_name",
        "raw_exchange",
        "raw_listing_market",
    ]

    acquisition_controls_v2_8b = [
        "No OpenAI.",
        "No broker.",
        "No scoring recalculation.",
        "No full 59k universe launch.",
        "No active output overwrite.",
        "No expanded_universe rebuild.",
        "Network download allowed only for Cboe official route candidates.",
        "Raw files must be preserved.",
        "Normalized CSV is written only if schema is detected confidently.",
        "All downloaded URLs, status codes, sizes and SHA256 hashes must be reported.",
    ]

    validation_questions_for_v2_8c = [
        "How many rows are present in each raw Cboe route?",
        "Which fields are available in CSV/XML?",
        "Does listed_symbols differ from symbols_traded?",
        "How many exchange+ticker keys are net new against expanded_universe_v2_7b?",
        "Are rows true listed securities or merely tradable symbols?",
        "Should Cboe be used as a primary provider, enrichment source, or be deferred?",
    ]

    if blockers:
        plan_status = "CBOE_LISTED_SYMBOLS_ROUTE_PLAN_BLOCKED"
        readiness_score = 0
        recommended_next_phase = "Resolve blockers"
    else:
        plan_status = "CBOE_LISTED_SYMBOLS_ROUTE_PLAN_READY"
        readiness_score = 90
        recommended_next_phase = "v2.8B ? Cboe Listed Symbols Acquisition Real"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "plan_status": plan_status,
        "readiness_score": readiness_score,
        "recommended_next_phase": recommended_next_phase,
        "provider": {
            "provider_id": PROVIDER_ID,
            "provider_dir": rel(PROVIDER_DIR),
            "primary_route": "cboe_us_equities_listed_symbols",
            "secondary_route": "cboe_us_equities_symbols_traded",
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
        "planned_outputs_v2_8b": planned_outputs_v2_8b,
        "expected_normalized_columns": expected_normalized_columns,
        "acquisition_controls_v2_8b": acquisition_controls_v2_8b,
        "validation_questions_for_v2_8c": validation_questions_for_v2_8c,
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
            "Proceed to v2.8B with controlled acquisition of Cboe official CSV/XML routes. Do not rebuild until v2.8C validates net new coverage."
            if not blockers
            else "Resolve blockers before Cboe acquisition."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.8A Cboe Listed Symbols Route Plan")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Plan status: **{plan_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
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
    md.append("")
    md.append("## Route candidates")
    md.append("")
    for route in route_candidates:
        md.append(f"### {route['priority']}. {route['name']}")
        md.append("")
        md.append(f"- Route ID: `{route['route_id']}`")
        md.append(f"- Source URL: `{route['source_url']}`")
        md.append(f"- Type: {route['route_type']}")
        md.append(f"- Expected download options: {', '.join(route['expected_download_options'])}")
        md.append(f"- Expected value: {route['expected_value']}")
        md.append(f"- Risk: {route['risk']}")
        md.append(f"- Why: {route['why']}")
        md.append(f"- Planned treatment: {route['planned_treatment']}")
        md.append("")
    md.append("## Planned outputs for v2.8B")
    md.append("")
    for key, value in planned_outputs_v2_8b.items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Expected normalized columns")
    md.append("")
    for column in expected_normalized_columns:
        md.append(f"- `{column}`")
    md.append("")
    md.append("## Acquisition controls for v2.8B")
    md.append("")
    for control in acquisition_controls_v2_8b:
        md.append(f"- {control}")
    md.append("")
    md.append("## Validation questions for v2.8C")
    md.append("")
    for question in validation_questions_for_v2_8c:
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
    md.append("Important: v2.8A is plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.8A Cboe Listed Symbols Route Plan")
    print("=" * 92)
    print(f"OK   Plan status: {plan_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
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
