from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.9G"
METHOD = "otc_markets_closure_report_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

ROUTE_JSON = OUT_DIR / "next_official_provider_route_v2_9a.json"
PLAN_JSON = OUT_DIR / "otc_markets_acquisition_plan_v2_9b.json"
ACQUISITION_JSON = OUT_DIR / "otc_markets_acquisition_real_v2_9c.json"
VALIDATION_JSON = OUT_DIR / "otc_markets_validation_v2_9d.json"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

RAW_CSV = ROOT / "data" / "raw" / "source_providers" / "otc_markets_stock_screener" / "otc_markets_stock_screener_raw.csv"
RAW_HTML = ROOT / "data" / "raw" / "source_providers" / "otc_markets_stock_screener" / "otc_markets_stock_screener_page.html"

OUT_JSON = OUT_DIR / "otc_markets_closure_report_v2_9g.json"
OUT_MD = OUT_DIR / "otc_markets_closure_report_v2_9g.md"

CURRENT_EXPANDED_ROWS = 9200
CURRENT_EXCLUSIONS_ROWS = 10056

OTC_RAW_ROWS = 25
OTC_NORMALIZED_ROWS = 25
OTC_NET_NEW_ROWS = 25
OTC_DUPLICATE_KEYS = 0
OTC_ISSUES = 0
PROJECTED_ROWS_IF_REBUILT = 9225

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

ROWS_NEEDED_FIRST_EXPANSION_BEFORE_OTC = 5800
ROWS_NEEDED_FULL_SOURCE_BEFORE_OTC = 40800
ROWS_STILL_NEEDED_FIRST_EXPANSION_AFTER_OTC = 5775
ROWS_STILL_NEEDED_FULL_SOURCE_AFTER_OTC = 40775


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
    plan = read_json(PLAN_JSON)
    acquisition = read_json(ACQUISITION_JSON)
    validation = read_json(VALIDATION_JSON)

    required_artifacts = [
        (ROUTE_JSON, route, "v2.9A route artifact"),
        (PLAN_JSON, plan, "v2.9B OTC acquisition plan artifact"),
        (ACQUISITION_JSON, acquisition, "v2.9C OTC acquisition real artifact"),
        (VALIDATION_JSON, validation, "v2.9D OTC validation artifact"),
    ]

    for path, data, label in required_artifacts:
        if not data.get("_exists"):
            blockers.append(f"Missing {label}: {rel(path)}")
        else:
            positives.append(f"{label} found: {rel(path)}")

    required_files = [
        CURRENT_EXPANDED_CSV,
        CURRENT_EXCLUSIONS_CSV,
        RAW_CSV,
        RAW_HTML,
    ]

    for path in required_files:
        if path.exists():
            positives.append(f"Closure input available: {rel(path)}")
        else:
            blockers.append(f"Missing closure input: {rel(path)}")

    if route.get("route_status") == "NEXT_OFFICIAL_PROVIDER_ROUTE_READY":
        positives.append(f"v2.9A route status accepted: {route.get('route_status')}")
    else:
        blockers.append(f"Unexpected v2.9A route status: {route.get('route_status')}")

    if route.get("route_decision") == "OTC_MARKETS_SELECTED_AS_NEXT_PROVIDER_ROUTE":
        positives.append(f"v2.9A route decision accepted: {route.get('route_decision')}")
    else:
        blockers.append(f"Unexpected v2.9A route decision: {route.get('route_decision')}")

    if plan.get("plan_status") == "OTC_MARKETS_ACQUISITION_PLAN_READY":
        positives.append(f"v2.9B plan status accepted: {plan.get('plan_status')}")
    else:
        blockers.append(f"Unexpected v2.9B plan status: {plan.get('plan_status')}")

    if plan.get("plan_decision") == "OTC_MARKETS_CONTROLLED_ACQUISITION_APPROVED":
        positives.append(f"v2.9B plan decision accepted: {plan.get('plan_decision')}")
    else:
        blockers.append(f"Unexpected v2.9B plan decision: {plan.get('plan_decision')}")

    if acquisition.get("acquisition_status") == "OTC_MARKETS_ACQUISITION_COMPLETED":
        positives.append(f"v2.9C acquisition status accepted: {acquisition.get('acquisition_status')}")
    else:
        blockers.append(f"Unexpected v2.9C acquisition status: {acquisition.get('acquisition_status')}")

    if acquisition.get("acquisition_decision") == "OTC_MARKETS_RAW_SOURCE_READY_FOR_VALIDATION":
        positives.append(f"v2.9C acquisition decision accepted: {acquisition.get('acquisition_decision')}")
    else:
        blockers.append(f"Unexpected v2.9C acquisition decision: {acquisition.get('acquisition_decision')}")

    if validation.get("validation_status") == "OTC_MARKETS_VALIDATED_INSUFFICIENT_FOR_EXPANSION":
        positives.append(f"v2.9D validation status accepted: {validation.get('validation_status')}")
    else:
        blockers.append(f"Unexpected v2.9D validation status: {validation.get('validation_status')}")

    if validation.get("validation_decision") == "OTC_MARKETS_VALID_BUT_NOT_ENOUGH_REFERENCE_OR_ENRICHMENT_ONLY":
        positives.append(f"v2.9D validation decision accepted: {validation.get('validation_decision')}")
    else:
        blockers.append(f"Unexpected v2.9D validation decision: {validation.get('validation_decision')}")

    warnings.append("OTC Markets route downloaded and validated successfully, but only 25 net-new rows were found.")
    warnings.append("OTC Markets is not enough to unlock the 15000-row first expansion target.")
    warnings.append("OTC Markets is not enough to unlock the 50000-row full-source threshold.")
    warnings.append("v2.9E rebuild is explicitly skipped because 25 net-new rows are far below the 5800-row minimum needed.")
    warnings.append("Full 59k dry-run remains blocked.")

    first_expansion_unlocked = PROJECTED_ROWS_IF_REBUILT >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = PROJECTED_ROWS_IF_REBUILT >= MIN_FULL_SOURCE_ROWS

    if blockers:
        closure_status = "OTC_MARKETS_CLOSURE_BLOCKED"
        readiness_score = 0
        closure_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        closure_status = "OTC_MARKETS_CLOSED_VALID_BUT_NOT_ENOUGH"
        readiness_score = 95
        closure_decision = "OTC_MARKETS_CLOSED_REFERENCE_OR_ENRICHMENT_ONLY_NO_REBUILD"
        recommended_next_phase = "v2.10A ? Next Provider Route"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "closure_status": closure_status,
        "readiness_score": readiness_score,
        "closure_decision": closure_decision,
        "recommended_next_phase": recommended_next_phase,
        "closed_block": {
            "block_name": "v2.9 ? OTC Markets / next provider",
            "phases_closed": [
                "v2.9A ? Next Official Provider Route",
                "v2.9B ? OTC Markets Acquisition Plan",
                "v2.9C ? OTC Markets Acquisition Real",
                "v2.9D ? OTC Markets Validation",
                "v2.9G ? OTC Markets Closure Report",
            ],
            "phases_skipped": [
                "v2.9E ? Rebuild Expanded Source With OTC Markets",
                "v2.9F ? Validate Expanded Source With OTC Markets",
            ],
            "skip_reason": "OTC Markets produced only 25 net-new rows, below the 5800 rows required to consider expansion rebuild.",
        },
        "inputs": {
            "route_json": rel(ROUTE_JSON),
            "plan_json": rel(PLAN_JSON),
            "acquisition_json": rel(ACQUISITION_JSON),
            "validation_json": rel(VALIDATION_JSON),
            "current_expanded_csv": rel(CURRENT_EXPANDED_CSV),
            "current_exclusions_csv": rel(CURRENT_EXCLUSIONS_CSV),
            "raw_otc_csv": rel(RAW_CSV),
            "raw_otc_html": rel(RAW_HTML),
        },
        "final_result": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "current_exclusions_rows": CURRENT_EXCLUSIONS_ROWS,
            "otc_raw_rows": OTC_RAW_ROWS,
            "otc_normalized_candidate_rows": OTC_NORMALIZED_ROWS,
            "otc_net_new_candidate_rows": OTC_NET_NEW_ROWS,
            "otc_duplicate_exchange_ticker_keys": OTC_DUPLICATE_KEYS,
            "otc_issues": OTC_ISSUES,
            "projected_rows_if_rebuilt": PROJECTED_ROWS_IF_REBUILT,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "first_expansion_unlocked_if_rebuilt": first_expansion_unlocked,
            "full_source_unlocked_if_rebuilt": full_source_unlocked,
            "rows_needed_first_expansion_before_otc": ROWS_NEEDED_FIRST_EXPANSION_BEFORE_OTC,
            "rows_needed_full_source_before_otc": ROWS_NEEDED_FULL_SOURCE_BEFORE_OTC,
            "rows_still_needed_first_expansion_after_otc": ROWS_STILL_NEEDED_FIRST_EXPANSION_AFTER_OTC,
            "rows_still_needed_full_source_after_otc": ROWS_STILL_NEEDED_FULL_SOURCE_AFTER_OTC,
        },
        "provider_assessment": {
            "provider_id": "otc_markets_stock_screener",
            "schema_valid": True,
            "raw_download_success": True,
            "net_new_rows": OTC_NET_NEW_ROWS,
            "duplicate_keys": OTC_DUPLICATE_KEYS,
            "issues": OTC_ISSUES,
            "usable_for_bulk_expansion": False,
            "usable_for_reference": True,
            "usable_for_enrichment": True,
            "rebuild_allowed": False,
            "reason": "Valid schema and 25 net-new rows, but insufficient for expansion target.",
        },
        "next_options": [
            {
                "option": "A",
                "name": "Continue source expansion with next provider",
                "recommended_phase": "v2.10A ? Next Provider Route",
                "status": "RECOMMENDED",
                "reason": "OTC Markets did not provide enough rows to move toward 15000 or 50000.",
            },
            {
                "option": "B",
                "name": "Return to product/MVP with validated 9200-row universe",
                "recommended_phase": "Product/MVP roadmap refresh",
                "status": "AVAILABLE",
                "reason": "The current universe remains clean and validated, but still below expansion thresholds.",
            },
        ],
        "tag_recommendation": "v2.9_otc_markets_closed_valid_but_not_enough",
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
            "closure_only": True,
            "rebuild_skipped": True,
        },
        "recommendation": (
            "Close v2.9 with tag, skip v2.9E/v2.9F, and proceed to v2.10A Next Provider Route."
            if not blockers
            else "Resolve blockers before closing v2.9."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.9G OTC Markets Closure Report")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Closure status: **{closure_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Closure decision: **{closure_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Closed block")
    md.append("")
    for phase in payload["closed_block"]["phases_closed"]:
        md.append(f"- {phase}")
    md.append("")
    md.append("## Skipped phases")
    md.append("")
    for phase in payload["closed_block"]["phases_skipped"]:
        md.append(f"- {phase}")
    md.append("")
    md.append(f"Skip reason: {payload['closed_block']['skip_reason']}")
    md.append("")
    md.append("## Final result")
    md.append("")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Current exclusions rows: {CURRENT_EXCLUSIONS_ROWS}")
    md.append(f"- OTC raw rows: {OTC_RAW_ROWS}")
    md.append(f"- OTC normalized candidate rows: {OTC_NORMALIZED_ROWS}")
    md.append(f"- OTC net-new candidate rows: {OTC_NET_NEW_ROWS}")
    md.append(f"- OTC duplicate exchange+ticker keys: {OTC_DUPLICATE_KEYS}")
    md.append(f"- OTC issues: {OTC_ISSUES}")
    md.append(f"- Projected rows if rebuilt: {PROJECTED_ROWS_IF_REBUILT}")
    md.append("")
    md.append("## Threshold status")
    md.append("")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Expected full rows: {EXPECTED_FULL_ROWS}")
    md.append(f"- First expansion unlocked if rebuilt: {first_expansion_unlocked}")
    md.append(f"- Full source unlocked if rebuilt: {full_source_unlocked}")
    md.append(f"- Rows still needed first expansion after OTC: {ROWS_STILL_NEEDED_FIRST_EXPANSION_AFTER_OTC}")
    md.append(f"- Rows still needed full source after OTC: {ROWS_STILL_NEEDED_FULL_SOURCE_AFTER_OTC}")
    md.append("")
    md.append("## Provider assessment")
    md.append("")
    md.append("- Schema valid: true")
    md.append("- Raw download success: true")
    md.append("- Usable for bulk expansion: false")
    md.append("- Usable for reference: true")
    md.append("- Usable for enrichment: true")
    md.append("- Rebuild allowed: false")
    md.append("- Reason: valid schema and 25 net-new rows, but insufficient for expansion target.")
    md.append("")
    md.append("## Decision")
    md.append("")
    md.append("```text")
    md.append("OTC_MARKETS_CLOSED_VALID_BUT_NOT_ENOUGH")
    md.append("OTC_MARKETS_REFERENCE_OR_ENRICHMENT_ONLY")
    md.append("REBUILD_SKIPPED")
    md.append("FULL_59K_REMAINS_BLOCKED")
    md.append("NEXT_RECOMMENDED_PHASE: v2.10A_NEXT_PROVIDER_ROUTE")
    md.append("```")
    md.append("")
    md.append("## Next options")
    md.append("")
    md.append("### Option A ? Continue source expansion")
    md.append("")
    md.append("- Next phase: `v2.10A ? Next Provider Route`")
    md.append("- Status: recommended")
    md.append("")
    md.append("### Option B ? Return to product/MVP")
    md.append("")
    md.append("- Next phase: product/MVP roadmap refresh")
    md.append("- Status: available")
    md.append("")
    md.append("## Tag recommendation")
    md.append("")
    md.append("- `v2.9_otc_markets_closed_valid_but_not_enough`")
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
    md.append("- Closure only: true")
    md.append("- Rebuild skipped: true")
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
    md.append("Important: v2.9G is closure-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.9G OTC Markets Closure Report")
    print("=" * 92)
    print(f"OK   Closure status: {closure_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Closure decision: {closure_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    print(f"OK   OTC raw rows: {OTC_RAW_ROWS}")
    print(f"OK   OTC net-new rows: {OTC_NET_NEW_ROWS}")
    print(f"OK   Projected rows if rebuilt: {PROJECTED_ROWS_IF_REBUILT}")
    print(f"OK   Rebuild skipped: True")
    print(f"OK   First expansion unlocked if rebuilt: {first_expansion_unlocked}")
    print(f"OK   Full source unlocked if rebuilt: {full_source_unlocked}")
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
