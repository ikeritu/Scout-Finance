from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.8D"
METHOD = "rebuild_expanded_source_with_cboe_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

VALIDATION_JSON = OUT_DIR / "cboe_listed_symbols_validation_v2_8c.json"
NET_NEW_CANDIDATES_CSV = OUT_DIR / "cboe_listed_symbols_net_new_candidates_v2_8c.csv"
NORMALIZED_CANDIDATES_CSV = OUT_DIR / "cboe_listed_symbols_normalized_candidate_v2_8c.csv"
SCHEMA_DETAIL_CSV = OUT_DIR / "cboe_listed_symbols_schema_detail_v2_8c.csv"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_7b.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_7b.csv"

OUT_JSON = OUT_DIR / "rebuild_expanded_source_with_cboe_plan_v2_8d.json"
OUT_MD = OUT_DIR / "rebuild_expanded_source_with_cboe_plan_v2_8d.md"

CURRENT_EXPANDED_ROWS = 8007
CURRENT_EXCLUSIONS_ROWS = 10056

CBOE_NORMALIZED_CANDIDATES = 1220
CBOE_NET_NEW_CANDIDATES = 1193
PROJECTED_ROWS_AFTER_CBOE = 9200

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

ROWS_NEEDED_FIRST_EXPANSION_AFTER_CBOE = TARGET_FIRST_EXPANSION_ROWS - PROJECTED_ROWS_AFTER_CBOE
ROWS_NEEDED_FULL_SOURCE_AFTER_CBOE = MIN_FULL_SOURCE_ROWS - PROJECTED_ROWS_AFTER_CBOE


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

    validation = read_json(VALIDATION_JSON)

    if not validation.get("_exists"):
        blockers.append(f"Missing v2.8C validation artifact: {rel(VALIDATION_JSON)}")
    else:
        positives.append(f"v2.8C validation artifact found: {rel(VALIDATION_JSON)}")

    validation_status = validation.get("validation_status")
    cboe_decision = validation.get("cboe_decision")

    if validation_status == "CBOE_VALIDATED_WITH_NET_NEW_CANDIDATES":
        positives.append(f"v2.8C validation status accepted: {validation_status}")
    else:
        blockers.append(f"Unexpected v2.8C validation status: {validation_status}")

    if cboe_decision == "CBOE_USABLE_AS_CANDIDATE_PROVIDER_PENDING_REBUILD_PLAN":
        positives.append(f"v2.8C Cboe decision accepted: {cboe_decision}")
    else:
        blockers.append(f"Unexpected v2.8C Cboe decision: {cboe_decision}")

    required_files = [
        NET_NEW_CANDIDATES_CSV,
        NORMALIZED_CANDIDATES_CSV,
        SCHEMA_DETAIL_CSV,
        CURRENT_EXPANDED_CSV,
        CURRENT_EXCLUSIONS_CSV,
    ]

    for path in required_files:
        if path.exists():
            positives.append(f"Required planning input available: {rel(path)}")
        else:
            blockers.append(f"Missing planning input: {rel(path)}")

    warnings.append("Cboe listed_symbols_raw.csv is not usable as direct ticker source because no symbol/ticker field was detected.")
    warnings.append("Cboe candidates came from symbols_traded/lot-size style data and must remain candidate-provider rows until post-rebuild validation.")
    warnings.append("Projected rows after Cboe remain below 15000 and 50000 thresholds.")
    warnings.append("Full 59k dry-run remains blocked after this provider even if rebuild succeeds.")

    first_expansion_unlocked_after_cboe = PROJECTED_ROWS_AFTER_CBOE >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked_after_cboe = PROJECTED_ROWS_AFTER_CBOE >= MIN_FULL_SOURCE_ROWS

    planned_rebuild_outputs = {
        "expanded_universe_with_cboe_csv": "data/raw/expanded_universe/expanded_universe_v2_8e.csv",
        "expanded_universe_exclusions_with_cboe_csv": "data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv",
        "rebuild_json": "outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_real_v2_8e.json",
        "rebuild_md": "outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_real_v2_8e.md",
        "provider_breakdown_csv": "outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_provider_breakdown_v2_8e.csv",
        "merge_audit_csv": "outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_merge_audit_v2_8e.csv",
        "exclusion_breakdown_csv": "outputs/full_universe_source_acquisition/rebuild_expanded_source_with_cboe_exclusion_breakdown_v2_8e.csv",
    }

    planned_rebuild_rules = [
        "Use expanded_universe_v2_7b.csv as immutable input.",
        "Use expanded_universe_exclusions_v2_7b.csv as immutable input.",
        "Use cboe_listed_symbols_net_new_candidates_v2_8c.csv as Cboe candidate input.",
        "Do not use cboe_listed_symbols_raw.csv as ticker source.",
        "Append only net-new exchange+ticker keys.",
        "Preserve existing rows exactly where keys already exist.",
        "Set source_provider to cboe_listed_symbols for appended rows.",
        "Keep classification confidence conservative because Cboe source semantics require validation.",
        "Do not overwrite active MVP outputs.",
        "Do not recalculate scoring.",
        "Do not call OpenAI.",
        "Do not call broker APIs.",
        "Do not launch full 59k universe.",
    ]

    planned_validation_v2_8f = [
        "Confirm final expanded rows equal 9200 if all 1193 net-new candidates are added.",
        "Confirm duplicate exchange+ticker keys remain 0.",
        "Confirm required canonical columns are present.",
        "Confirm provider breakdown includes Cboe candidate rows.",
        "Confirm first expansion remains blocked because 9200 < 15000.",
        "Confirm full source remains blocked because 9200 < 50000.",
        "Confirm no scoring/OpenAI/broker/full 59k was executed.",
    ]

    if blockers:
        plan_status = "REBUILD_EXPANDED_SOURCE_WITH_CBOE_PLAN_BLOCKED"
        readiness_score = 0
        plan_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        plan_status = "REBUILD_EXPANDED_SOURCE_WITH_CBOE_PLAN_READY_WITH_CONDITIONS"
        readiness_score = 90
        plan_decision = "CBOE_REBUILD_PLAN_APPROVED_WITH_CONDITIONS"
        recommended_next_phase = "v2.8E ? Rebuild Expanded Source With Cboe Real"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "plan_status": plan_status,
        "readiness_score": readiness_score,
        "plan_decision": plan_decision,
        "recommended_next_phase": recommended_next_phase,
        "inputs": {
            "validation_json": rel(VALIDATION_JSON),
            "net_new_candidates_csv": rel(NET_NEW_CANDIDATES_CSV),
            "normalized_candidates_csv": rel(NORMALIZED_CANDIDATES_CSV),
            "schema_detail_csv": rel(SCHEMA_DETAIL_CSV),
            "current_expanded_csv": rel(CURRENT_EXPANDED_CSV),
            "current_exclusions_csv": rel(CURRENT_EXCLUSIONS_CSV),
        },
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "current_exclusions_rows": CURRENT_EXCLUSIONS_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "first_expansion_unlocked": False,
            "full_source_unlocked": False,
        },
        "cboe_candidate_summary": {
            "normalized_candidate_rows": CBOE_NORMALIZED_CANDIDATES,
            "net_new_exchange_ticker_rows": CBOE_NET_NEW_CANDIDATES,
            "projected_rows_after_cboe": PROJECTED_ROWS_AFTER_CBOE,
            "rows_needed_first_expansion_after_cboe": ROWS_NEEDED_FIRST_EXPANSION_AFTER_CBOE,
            "rows_needed_full_source_after_cboe": ROWS_NEEDED_FULL_SOURCE_AFTER_CBOE,
            "first_expansion_unlocked_after_cboe": first_expansion_unlocked_after_cboe,
            "full_source_unlocked_after_cboe": full_source_unlocked_after_cboe,
        },
        "planned_rebuild_outputs_v2_8e": planned_rebuild_outputs,
        "planned_rebuild_rules_v2_8e": planned_rebuild_rules,
        "planned_validation_v2_8f": planned_validation_v2_8f,
        "decision_constraints": {
            "listed_symbols_raw_csv_usable_as_ticker_source": False,
            "cboe_candidates_are_primary_provider_rows": False,
            "cboe_candidates_are_candidate_provider_rows": True,
            "rebuild_allowed": not blockers,
            "active_outputs_overwrite_allowed": False,
            "full_59k_unlocked_after_cboe": full_source_unlocked_after_cboe,
        },
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
            "Proceed to v2.8E controlled rebuild with Cboe candidate rows, then validate in v2.8F before any downstream use."
            if not blockers
            else "Resolve blockers before any Cboe rebuild."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.8D Rebuild Expanded Source With Cboe Plan")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Plan status: **{plan_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Plan decision: **{plan_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Current state")
    md.append("")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Current exclusions rows: {CURRENT_EXCLUSIONS_ROWS}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Full 59k expected rows: {EXPECTED_FULL_ROWS}")
    md.append("")
    md.append("## Cboe candidate summary")
    md.append("")
    md.append(f"- Normalized candidate rows: {CBOE_NORMALIZED_CANDIDATES}")
    md.append(f"- Net-new exchange+ticker rows: {CBOE_NET_NEW_CANDIDATES}")
    md.append(f"- Projected rows after Cboe: {PROJECTED_ROWS_AFTER_CBOE}")
    md.append(f"- Rows needed first expansion after Cboe: {ROWS_NEEDED_FIRST_EXPANSION_AFTER_CBOE}")
    md.append(f"- Rows needed full source after Cboe: {ROWS_NEEDED_FULL_SOURCE_AFTER_CBOE}")
    md.append(f"- First expansion unlocked after Cboe: {first_expansion_unlocked_after_cboe}")
    md.append(f"- Full source unlocked after Cboe: {full_source_unlocked_after_cboe}")
    md.append("")
    md.append("## Decision")
    md.append("")
    md.append("```text")
    md.append(plan_decision)
    md.append("CBOE_CANDIDATE_ROWS_ONLY")
    md.append("FULL_59K_REMAINS_BLOCKED")
    md.append("REBUILD_ALLOWED_ONLY_AS_ISOLATED_V2_8E")
    md.append("```")
    md.append("")
    md.append("## Planned outputs for v2.8E")
    md.append("")
    for key, value in planned_rebuild_outputs.items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Planned rebuild rules for v2.8E")
    md.append("")
    for rule in planned_rebuild_rules:
        md.append(f"- {rule}")
    md.append("")
    md.append("## Planned validation for v2.8F")
    md.append("")
    for item in planned_validation_v2_8f:
        md.append(f"- {item}")
    md.append("")
    md.append("## Constraints")
    md.append("")
    md.append("- listed_symbols_raw.csv usable as ticker source: false")
    md.append("- Cboe candidates are primary provider rows: false")
    md.append("- Cboe candidates are candidate-provider rows: true")
    md.append(f"- Rebuild allowed: {str(not blockers).lower()}")
    md.append("- Active outputs overwrite allowed: false")
    md.append(f"- Full 59k unlocked after Cboe: {str(full_source_unlocked_after_cboe).lower()}")
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
    md.append("Important: v2.8D is plan-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.8D Rebuild Expanded Source With Cboe Plan")
    print("=" * 92)
    print(f"OK   Plan status: {plan_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Plan decision: {plan_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    print(f"OK   Cboe net-new candidates: {CBOE_NET_NEW_CANDIDATES}")
    print(f"OK   Projected rows after Cboe: {PROJECTED_ROWS_AFTER_CBOE}")
    print(f"OK   Rows needed first expansion after Cboe: {ROWS_NEEDED_FIRST_EXPANSION_AFTER_CBOE}")
    print(f"OK   Rows needed full source after Cboe: {ROWS_NEEDED_FULL_SOURCE_AFTER_CBOE}")
    print(f"OK   First expansion unlocked after Cboe: {first_expansion_unlocked_after_cboe}")
    print(f"OK   Full source unlocked after Cboe: {full_source_unlocked_after_cboe}")
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
