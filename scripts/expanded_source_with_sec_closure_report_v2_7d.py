from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.7D"
METHOD = "expanded_source_with_sec_closure_report_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

VALIDATION_JSON = OUT_DIR / "validate_expanded_source_with_sec_v2_7c.json"
REBUILD_JSON = OUT_DIR / "rebuild_expanded_source_with_sec_real_v2_7b.json"
PLAN_JSON = OUT_DIR / "rebuild_expanded_source_with_sec_plan_v2_7a.json"
SEC_ANALYSIS_JSON = OUT_DIR / "sec_incremental_coverage_analysis_v2_6e.json"

EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_7b.csv"
EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_7b.csv"

OUT_JSON = OUT_DIR / "expanded_source_with_sec_closure_report_v2_7d.json"
OUT_MD = OUT_DIR / "expanded_source_with_sec_closure_report_v2_7d.md"

FINAL_EXPANDED_ROWS = 8007
FINAL_EXCLUSIONS_ROWS = 10056
SEC_ROWS_ADDED = 2359
DUPLICATE_EXCHANGE_TICKER_KEYS = 0
ISSUES_COUNT = 0

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

    validation = read_json(VALIDATION_JSON)
    rebuild = read_json(REBUILD_JSON)
    plan = read_json(PLAN_JSON)
    sec_analysis = read_json(SEC_ANALYSIS_JSON)

    required_artifacts = [
        (VALIDATION_JSON, validation, "v2.7C validation artifact"),
        (REBUILD_JSON, rebuild, "v2.7B rebuild artifact"),
        (PLAN_JSON, plan, "v2.7A plan artifact"),
        (SEC_ANALYSIS_JSON, sec_analysis, "v2.6E SEC incremental analysis artifact"),
    ]

    for path, data, label in required_artifacts:
        if not data.get("_exists"):
            blockers.append(f"Missing {label}: {rel(path)}")
        else:
            positives.append(f"{label} found: {rel(path)}")

    required_files = [
        EXPANDED_CSV,
        EXCLUSIONS_CSV,
    ]

    for path in required_files:
        if not path.exists():
            blockers.append(f"Missing required source output: {rel(path)}")
        else:
            positives.append(f"Required source output found: {rel(path)}")

    validation_status = validation.get("validation_status")
    rebuild_status = rebuild.get("rebuild_status")
    plan_status = plan.get("plan_status")
    sec_decision = sec_analysis.get("decision")

    if validation_status == "EXPANDED_SOURCE_WITH_SEC_VALIDATED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.7C validation status accepted: {validation_status}")
    else:
        blockers.append(f"Unexpected v2.7C validation status: {validation_status}")

    if rebuild_status == "REBUILD_EXPANDED_SOURCE_WITH_SEC_COMPLETED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.7B rebuild status accepted: {rebuild_status}")
    else:
        blockers.append(f"Unexpected v2.7B rebuild status: {rebuild_status}")

    if plan_status == "REBUILD_EXPANDED_SOURCE_WITH_SEC_PLAN_READY":
        positives.append(f"v2.7A plan status accepted: {plan_status}")
    else:
        blockers.append(f"Unexpected v2.7A plan status: {plan_status}")

    if sec_decision == "REBUILD_WITH_SEC_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.6E SEC decision accepted: {sec_decision}")
    else:
        blockers.append(f"Unexpected v2.6E SEC decision: {sec_decision}")

    first_expansion_unlocked = FINAL_EXPANDED_ROWS >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = FINAL_EXPANDED_ROWS >= MIN_FULL_SOURCE_ROWS

    if not first_expansion_unlocked:
        warnings.append(
            f"First expansion target remains blocked: {FINAL_EXPANDED_ROWS} < {TARGET_FIRST_EXPANSION_ROWS}"
        )

    if not full_source_unlocked:
        warnings.append(
            f"Full-source threshold remains blocked: {FINAL_EXPANDED_ROWS} < {MIN_FULL_SOURCE_ROWS}"
        )

    warnings.append("SEC rebuild is useful, but not enough to close source expansion.")
    warnings.append("Next decision required: continue with Cboe/next provider or return to product/MVP with partial expanded universe.")

    if blockers:
        closure_status = "EXPANDED_SOURCE_WITH_SEC_CLOSURE_BLOCKED"
        readiness_score = 0
        closure_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        closure_status = "EXPANDED_SOURCE_WITH_SEC_CLOSED_USEFUL_BUT_NOT_ENOUGH"
        readiness_score = 95
        closure_decision = "SEC_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH"
        recommended_next_phase = "v2.8A ? Cboe Listed Symbols Route Plan OR return to product/MVP"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "closure_status": closure_status,
        "readiness_score": readiness_score,
        "closure_decision": closure_decision,
        "recommended_next_phase": recommended_next_phase,
        "closed_block": {
            "block_name": "v2.7 ? Rebuild Expanded Source With SEC",
            "phases_closed": [
                "v2.7A ? Rebuild Expanded Source With SEC Plan",
                "v2.7B ? Rebuild Expanded Source With SEC Real",
                "v2.7C ? Validate Expanded Source With SEC",
                "v2.7D ? Expanded Source With SEC Closure Report",
            ],
        },
        "inputs": {
            "sec_analysis_json": rel(SEC_ANALYSIS_JSON),
            "plan_json": rel(PLAN_JSON),
            "rebuild_json": rel(REBUILD_JSON),
            "validation_json": rel(VALIDATION_JSON),
            "expanded_universe_v2_7b_csv": rel(EXPANDED_CSV),
            "expanded_universe_exclusions_v2_7b_csv": rel(EXCLUSIONS_CSV),
        },
        "final_result": {
            "expanded_universe_csv": rel(EXPANDED_CSV),
            "expanded_universe_exclusions_csv": rel(EXCLUSIONS_CSV),
            "final_expanded_rows": FINAL_EXPANDED_ROWS,
            "final_exclusions_rows": FINAL_EXCLUSIONS_ROWS,
            "sec_rows_added": SEC_ROWS_ADDED,
            "duplicate_exchange_ticker_keys": DUPLICATE_EXCHANGE_TICKER_KEYS,
            "issues_count": ISSUES_COUNT,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_first_expansion": ROWS_NEEDED_FIRST_EXPANSION,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
        },
        "provider_result": {
            "nasdaq_trader_nasdaqlisted": 3244,
            "nasdaq_trader_otherlisted": 2404,
            "sec_company_tickers_exchange": 2359,
        },
        "next_options": [
            {
                "option": "A",
                "name": "Continue source expansion with Cboe / next official provider",
                "recommended_phase": "v2.8A ? Cboe Listed Symbols Route Plan",
                "reason": "Full 59k remains blocked and additional official providers are needed.",
                "status": "RECOMMENDED_IF_59K_REMAINS_PRIORITY",
            },
            {
                "option": "B",
                "name": "Return to product/MVP with partial expanded universe",
                "recommended_phase": "Product/MVP roadmap refresh",
                "reason": "The project has a validated 8007-row universe and could shift back to dashboard/scoring/research usability.",
                "status": "RECOMMENDED_IF_PRODUCT_UTILITY_IS_PRIORITY",
            },
        ],
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
            "closure_only": True,
        },
        "recommendation": (
            "Close v2.7 with tag and decide whether to continue with v2.8A Cboe route or return to product/MVP with the validated 8007-row universe."
            if not blockers
            else "Resolve blockers before closing v2.7."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.7D Expanded Source With SEC Closure Report")
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
    md.append("- v2.7A ? Rebuild Expanded Source With SEC Plan")
    md.append("- v2.7B ? Rebuild Expanded Source With SEC Real")
    md.append("- v2.7C ? Validate Expanded Source With SEC")
    md.append("- v2.7D ? Expanded Source With SEC Closure Report")
    md.append("")
    md.append("## Final result")
    md.append("")
    md.append(f"- Expanded universe: `{rel(EXPANDED_CSV)}`")
    md.append(f"- Exclusions: `{rel(EXCLUSIONS_CSV)}`")
    md.append(f"- Final expanded rows: {FINAL_EXPANDED_ROWS}")
    md.append(f"- Final exclusions rows: {FINAL_EXCLUSIONS_ROWS}")
    md.append(f"- SEC rows added: {SEC_ROWS_ADDED}")
    md.append(f"- Duplicate exchange+ticker keys: {DUPLICATE_EXCHANGE_TICKER_KEYS}")
    md.append(f"- Issues count: {ISSUES_COUNT}")
    md.append("")
    md.append("## Provider result")
    md.append("")
    md.append("- nasdaq_trader_nasdaqlisted: 3244")
    md.append("- nasdaq_trader_otherlisted: 2404")
    md.append("- sec_company_tickers_exchange: 2359")
    md.append("- Total: 8007")
    md.append("")
    md.append("## Threshold status")
    md.append("")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Expected full rows: {EXPECTED_FULL_ROWS}")
    md.append(f"- First expansion unlocked: {first_expansion_unlocked}")
    md.append(f"- Full source unlocked: {full_source_unlocked}")
    md.append(f"- Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}")
    md.append(f"- Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}")
    md.append("")
    md.append("## Decision")
    md.append("")
    md.append("SEC rebuild is closed as useful but not enough.")
    md.append("")
    md.append("```text")
    md.append("SEC_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH")
    md.append("FULL_59K_REMAINS_BLOCKED")
    md.append("NEXT_DECISION_REQUIRED: CBOE_OR_RETURN_TO_PRODUCT")
    md.append("```")
    md.append("")
    md.append("## Next options")
    md.append("")
    md.append("### Option A ? Continue source expansion")
    md.append("")
    md.append("- Next phase: `v2.8A ? Cboe Listed Symbols Route Plan`")
    md.append("- Use if 59k/full-source remains the priority.")
    md.append("")
    md.append("### Option B ? Return to product/MVP")
    md.append("")
    md.append("- Next phase: product/MVP roadmap refresh.")
    md.append("- Use if practical utility with the validated 8007-row universe is now the priority.")
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
    md.append("- Closure only: true")
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
    md.append("Important: v2.7D is closure-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.7D Expanded Source With SEC Closure Report")
    print("=" * 92)
    print(f"OK   Closure status: {closure_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Closure decision: {closure_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Final expanded rows: {FINAL_EXPANDED_ROWS}")
    print(f"OK   Final exclusions rows: {FINAL_EXCLUSIONS_ROWS}")
    print(f"OK   SEC rows added: {SEC_ROWS_ADDED}")
    print(f"OK   Duplicate exchange+ticker keys: {DUPLICATE_EXCHANGE_TICKER_KEYS}")
    print(f"OK   Issues count: {ISSUES_COUNT}")
    print(f"OK   First expansion unlocked: {first_expansion_unlocked}")
    print(f"OK   Full source unlocked: {full_source_unlocked}")
    print(f"OK   Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}")
    print(f"OK   Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}")
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
