from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.7A"
METHOD = "rebuild_expanded_source_with_sec_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

SEC_ANALYSIS_JSON = OUT_DIR / "sec_incremental_coverage_analysis_v2_6e.json"
SEC_REBUILD_CANDIDATES_CSV = OUT_DIR / "sec_incremental_rebuild_candidates_v2_6e.csv"
SEC_ENRICHMENT_CSV = OUT_DIR / "sec_incremental_enrichment_rows_v2_6e.csv"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_4b.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_4b.csv"

SEC_PROVIDER_CSV = ROOT / "data" / "raw" / "source_providers" / "sec_company_tickers_exchange" / "sec_company_tickers_exchange.csv"

PLANNED_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_7b.csv"
PLANNED_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_7b.csv"

OUT_JSON = OUT_DIR / "rebuild_expanded_source_with_sec_plan_v2_7a.json"
OUT_MD = OUT_DIR / "rebuild_expanded_source_with_sec_plan_v2_7a.md"

CURRENT_EXPANDED_ROWS = 5648
SEC_PRIMARY_NET_NEW_KEYS = 2359
SEC_ENRICHMENT_OR_EXCLUSION_ROWS = 2747
PLANNED_MAX_ROWS_AFTER_SEC = 8007

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

    sec_analysis = read_json(SEC_ANALYSIS_JSON)

    if not sec_analysis.get("_exists"):
        blockers.append(f"Missing v2.6E SEC incremental analysis artifact: {rel(SEC_ANALYSIS_JSON)}")
    else:
        positives.append(f"v2.6E SEC incremental analysis artifact found: {rel(SEC_ANALYSIS_JSON)}")

    analysis_status = sec_analysis.get("analysis_status")
    decision = sec_analysis.get("decision")

    if analysis_status == "SEC_INCREMENTAL_COVERAGE_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.6E analysis status accepted: {analysis_status}")
    else:
        blockers.append(f"Unexpected v2.6E analysis status: {analysis_status}")

    if decision == "REBUILD_WITH_SEC_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.6E decision accepted: {decision}")
    else:
        blockers.append(f"Unexpected v2.6E decision: {decision}")

    required_inputs = [
        CURRENT_EXPANDED_CSV,
        CURRENT_EXCLUSIONS_CSV,
        SEC_PROVIDER_CSV,
        SEC_REBUILD_CANDIDATES_CSV,
        SEC_ENRICHMENT_CSV,
    ]

    for path in required_inputs:
        if not path.exists():
            blockers.append(f"Missing required input for v2.7B plan: {rel(path)}")
        else:
            positives.append(f"Required input available: {rel(path)}")

    rows_needed_first_expansion_after_sec = max(TARGET_FIRST_EXPANSION_ROWS - PLANNED_MAX_ROWS_AFTER_SEC, 0)
    rows_needed_full_source_after_sec = max(MIN_FULL_SOURCE_ROWS - PLANNED_MAX_ROWS_AFTER_SEC, 0)

    if PLANNED_MAX_ROWS_AFTER_SEC < TARGET_FIRST_EXPANSION_ROWS:
        warnings.append(
            f"SEC rebuild will not unlock first expansion target: {PLANNED_MAX_ROWS_AFTER_SEC} < {TARGET_FIRST_EXPANSION_ROWS}"
        )

    if PLANNED_MAX_ROWS_AFTER_SEC < MIN_FULL_SOURCE_ROWS:
        warnings.append(
            f"SEC rebuild will not unlock full-source threshold: {PLANNED_MAX_ROWS_AFTER_SEC} < {MIN_FULL_SOURCE_ROWS}"
        )

    warnings.append(
        "SEC OTC/None rows must remain exclusions/enrichment and must not be merged into primary expanded universe."
    )

    provider_precedence = [
        {
            "priority": 1,
            "provider": "existing_expanded_universe_v2_4b",
            "role": "base_validated_source",
            "input": rel(CURRENT_EXPANDED_CSV),
            "treatment": "Preserve existing validated Nasdaq Trader derived rows unless duplicate policy explicitly replaces metadata.",
        },
        {
            "priority": 2,
            "provider": "sec_company_tickers_exchange_primary_net_new",
            "role": "partial_provider_and_identifier_enrichment",
            "input": rel(SEC_REBUILD_CANDIDATES_CSV),
            "treatment": "Add only PRIMARY_NET_NEW rows with exchange in NASDAQ, NYSE, CBOE and key not already present as exchange+ticker.",
        },
        {
            "priority": 3,
            "provider": "sec_company_tickers_exchange_enrichment_or_exclusion",
            "role": "enrichment_exclusion_reference",
            "input": rel(SEC_ENRICHMENT_CSV),
            "treatment": "Do not add to primary universe. Preserve in exclusions/reference output for future enrichment and provider diagnostics.",
        },
    ]

    canonical_output_columns = [
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
        "raw_cik",
        "raw_exchange",
        "provider_precedence",
        "merge_action",
        "merge_reason",
    ]

    deduplication_rules = [
        "Primary deduplication key: exchange+ticker.",
        "Normalize ticker as uppercase trimmed string.",
        "Normalize exchange as trimmed string.",
        "Existing v2.4B rows win on duplicate exchange+ticker keys.",
        "SEC primary net-new rows are added only when exchange+ticker key is absent from v2.4B.",
        "SEC OTC/None/blank exchange rows are never added to primary expanded universe in v2.7B.",
        "SEC duplicate exchange+ticker count must remain zero, as validated in v2.6D.",
        "If a SEC row has unknown exchange, route it to exclusions/review, not primary universe.",
    ]

    classification_rules = [
        "Existing v2.4B classification fields are preserved.",
        "SEC rows keep instrument_type UNKNOWN_PENDING_CLASSIFICATION unless downstream classification is implemented.",
        "SEC rows keep instrument_scope UNKNOWN_PENDING_CLASSIFICATION unless downstream classification is implemented.",
        "SEC rows use classification_confidence LOW until a listing-specific provider confirms instrument class.",
        "SEC CIK is stored as raw_cik for identifier enrichment.",
        "SEC raw exchange is preserved as raw_exchange.",
    ]

    outputs_planned = {
        "expanded_universe_v2_7b_csv": rel(PLANNED_EXPANDED_CSV),
        "expanded_universe_exclusions_v2_7b_csv": rel(PLANNED_EXCLUSIONS_CSV),
        "rebuild_report_json": "outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_real_v2_7b.json",
        "rebuild_report_md": "outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_real_v2_7b.md",
        "provider_breakdown_csv": "outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_provider_breakdown_v2_7b.csv",
        "merge_audit_csv": "outputs/full_universe_source_acquisition/rebuild_expanded_source_with_sec_merge_audit_v2_7b.csv",
    }

    acceptance_criteria_v2_7b = [
        "No network download performed.",
        "No OpenAI call.",
        "No broker call.",
        "No scoring recalculation.",
        "No full 59k universe launch.",
        "No active MVP output overwrite.",
        "Create new versioned expanded_universe_v2_7b.csv only.",
        "Create new versioned expanded_universe_exclusions_v2_7b.csv only.",
        "Preserve v2.4B outputs unchanged.",
        "Final included rows should be approximately 8007 unless duplicate logic reveals a documented variance.",
        "OTC/None SEC rows must stay out of primary universe.",
        "Report provider breakdown and merge audit.",
    ]

    if blockers:
        plan_status = "REBUILD_EXPANDED_SOURCE_WITH_SEC_PLAN_BLOCKED"
        readiness_score = 0
        recommended_next_phase = "Resolve blockers"
    else:
        plan_status = "REBUILD_EXPANDED_SOURCE_WITH_SEC_PLAN_READY"
        readiness_score = 95
        recommended_next_phase = "v2.7B ? Rebuild Expanded Source With SEC Real"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "plan_status": plan_status,
        "readiness_score": readiness_score,
        "recommended_next_phase": recommended_next_phase,
        "source_decision_from_v2_6e": {
            "analysis_status": analysis_status,
            "decision": decision,
            "sec_primary_net_new_keys": SEC_PRIMARY_NET_NEW_KEYS,
            "planned_max_rows_after_sec": PLANNED_MAX_ROWS_AFTER_SEC,
            "first_expansion_unlocked": False,
            "full_source_unlocked": False,
        },
        "inputs": {
            "current_expanded_csv": rel(CURRENT_EXPANDED_CSV),
            "current_exclusions_csv": rel(CURRENT_EXCLUSIONS_CSV),
            "sec_provider_csv": rel(SEC_PROVIDER_CSV),
            "sec_rebuild_candidates_csv": rel(SEC_REBUILD_CANDIDATES_CSV),
            "sec_enrichment_csv": rel(SEC_ENRICHMENT_CSV),
            "sec_analysis_json": rel(SEC_ANALYSIS_JSON),
        },
        "planned_outputs": outputs_planned,
        "provider_precedence": provider_precedence,
        "canonical_output_columns": canonical_output_columns,
        "deduplication_rules": deduplication_rules,
        "classification_rules": classification_rules,
        "acceptance_criteria_v2_7b": acceptance_criteria_v2_7b,
        "summary": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "sec_primary_net_new_keys": SEC_PRIMARY_NET_NEW_KEYS,
            "sec_enrichment_or_exclusion_rows": SEC_ENRICHMENT_OR_EXCLUSION_ROWS,
            "planned_max_rows_after_sec_rebuild": PLANNED_MAX_ROWS_AFTER_SEC,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "rows_needed_first_expansion_after_sec": rows_needed_first_expansion_after_sec,
            "rows_needed_full_source_after_sec": rows_needed_full_source_after_sec,
            "first_expansion_unlocked_after_sec": False,
            "full_source_unlocked_after_sec": False,
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
        },
        "recommendation": (
            "Proceed to v2.7B to execute a controlled versioned rebuild with SEC. Do not overwrite v2.4B or active MVP outputs."
            if not blockers
            else "Resolve blockers before executing SEC rebuild."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.7A Rebuild Expanded Source With SEC Plan")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Plan status: **{plan_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Decision inherited from v2.6E")
    md.append("")
    md.append(f"- Analysis status: **{analysis_status}**")
    md.append(f"- Decision: **{decision}**")
    md.append(f"- SEC primary net new keys: {SEC_PRIMARY_NET_NEW_KEYS}")
    md.append(f"- Planned max rows after SEC rebuild: {PLANNED_MAX_ROWS_AFTER_SEC}")
    md.append("- First expansion unlocked: false")
    md.append("- Full source unlocked: false")
    md.append("")
    md.append("## Inputs")
    md.append("")
    for key, value in payload["inputs"].items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Planned outputs for v2.7B")
    md.append("")
    for key, value in outputs_planned.items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Provider precedence")
    md.append("")
    for provider in provider_precedence:
        md.append(f"### {provider['priority']}. {provider['provider']}")
        md.append("")
        md.append(f"- Role: {provider['role']}")
        md.append(f"- Input: `{provider['input']}`")
        md.append(f"- Treatment: {provider['treatment']}")
        md.append("")
    md.append("## Deduplication rules")
    md.append("")
    for rule in deduplication_rules:
        md.append(f"- {rule}")
    md.append("")
    md.append("## Classification rules")
    md.append("")
    for rule in classification_rules:
        md.append(f"- {rule}")
    md.append("")
    md.append("## Rebuild impact estimate")
    md.append("")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- SEC primary net new keys: {SEC_PRIMARY_NET_NEW_KEYS}")
    md.append(f"- SEC enrichment/exclusion rows: {SEC_ENRICHMENT_OR_EXCLUSION_ROWS}")
    md.append(f"- Planned max rows after SEC rebuild: {PLANNED_MAX_ROWS_AFTER_SEC}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Rows still needed for first expansion after SEC: {rows_needed_first_expansion_after_sec}")
    md.append(f"- Rows still needed for full source after SEC: {rows_needed_full_source_after_sec}")
    md.append("")
    md.append("## Acceptance criteria for v2.7B")
    md.append("")
    for criterion in acceptance_criteria_v2_7b:
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
    md.append("Important: v2.7A is a plan-only step. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.7A Rebuild Expanded Source With SEC Plan")
    print("=" * 92)
    print(f"OK   Plan status: {plan_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    print(f"OK   SEC primary net new keys: {SEC_PRIMARY_NET_NEW_KEYS}")
    print(f"OK   Planned max rows after SEC rebuild: {PLANNED_MAX_ROWS_AFTER_SEC}")
    print(f"OK   Rows still needed first expansion: {rows_needed_first_expansion_after_sec}")
    print(f"OK   Rows still needed full source: {rows_needed_full_source_after_sec}")
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
