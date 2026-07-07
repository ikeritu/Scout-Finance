from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.8G"
METHOD = "expanded_source_with_cboe_closure_report_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

VALIDATION_JSON = OUT_DIR / "validate_expanded_source_with_cboe_v2_8f.json"
REBUILD_JSON = OUT_DIR / "rebuild_expanded_source_with_cboe_real_v2_8e.json"
PLAN_JSON = OUT_DIR / "rebuild_expanded_source_with_cboe_plan_v2_8d.json"
CBOE_VALIDATION_JSON = OUT_DIR / "cboe_listed_symbols_validation_v2_8c.json"

EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

OUT_JSON = OUT_DIR / "expanded_source_with_cboe_closure_report_v2_8g.json"
OUT_MD = OUT_DIR / "expanded_source_with_cboe_closure_report_v2_8g.md"

FINAL_EXPANDED_ROWS = 9200
FINAL_EXCLUSIONS_ROWS = 10056
CBOE_ROWS_ADDED = 1193
DUPLICATE_EXCHANGE_TICKER_KEYS = 0
ISSUES_COUNT = 1

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

    validation = read_json(VALIDATION_JSON)
    rebuild = read_json(REBUILD_JSON)
    plan = read_json(PLAN_JSON)
    cboe_validation = read_json(CBOE_VALIDATION_JSON)

    required_artifacts = [
        (VALIDATION_JSON, validation, "v2.8F Cboe expanded source validation artifact"),
        (REBUILD_JSON, rebuild, "v2.8E Cboe rebuild artifact"),
        (PLAN_JSON, plan, "v2.8D Cboe rebuild plan artifact"),
        (CBOE_VALIDATION_JSON, cboe_validation, "v2.8C Cboe provider validation artifact"),
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
            blockers.append(f"Missing closure input: {rel(path)}")
        else:
            positives.append(f"Closure input available: {rel(path)}")

    validation_status = validation.get("validation_status")
    validation_decision = validation.get("validation_decision")
    rebuild_status = rebuild.get("rebuild_status")
    plan_decision = plan.get("plan_decision")
    cboe_decision = cboe_validation.get("cboe_decision")

    if validation_status == "EXPANDED_SOURCE_WITH_CBOE_VALIDATED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.8F validation status accepted: {validation_status}")
    else:
        blockers.append(f"Unexpected v2.8F validation status: {validation_status}")

    if validation_decision == "CBOE_REBUILD_VALIDATED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.8F validation decision accepted: {validation_decision}")
    else:
        blockers.append(f"Unexpected v2.8F validation decision: {validation_decision}")

    if rebuild_status == "REBUILD_EXPANDED_SOURCE_WITH_CBOE_COMPLETED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.8E rebuild status accepted: {rebuild_status}")
    else:
        blockers.append(f"Unexpected v2.8E rebuild status: {rebuild_status}")

    if plan_decision == "CBOE_REBUILD_PLAN_APPROVED_WITH_CONDITIONS":
        positives.append(f"v2.8D plan decision accepted: {plan_decision}")
    else:
        blockers.append(f"Unexpected v2.8D plan decision: {plan_decision}")

    if cboe_decision == "CBOE_USABLE_AS_CANDIDATE_PROVIDER_PENDING_REBUILD_PLAN":
        positives.append(f"v2.8C Cboe decision accepted: {cboe_decision}")
    else:
        blockers.append(f"Unexpected v2.8C Cboe decision: {cboe_decision}")

    first_expansion_unlocked = FINAL_EXPANDED_ROWS >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = FINAL_EXPANDED_ROWS >= MIN_FULL_SOURCE_ROWS

    warnings.append("Cboe added useful candidate-provider rows, but company names remain empty for Cboe rows.")
    warnings.append("Cboe rows should remain low-confidence pending downstream enrichment or provider cross-check.")
    warnings.append(f"First expansion remains blocked: {FINAL_EXPANDED_ROWS} < {TARGET_FIRST_EXPANSION_ROWS}")
    warnings.append(f"Full-source threshold remains blocked: {FINAL_EXPANDED_ROWS} < {MIN_FULL_SOURCE_ROWS}")
    warnings.append("Full 59k dry-run remains blocked.")

    if blockers:
        closure_status = "EXPANDED_SOURCE_WITH_CBOE_CLOSURE_BLOCKED"
        readiness_score = 0
        closure_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        closure_status = "EXPANDED_SOURCE_WITH_CBOE_CLOSED_USEFUL_BUT_NOT_ENOUGH"
        readiness_score = 95
        closure_decision = "CBOE_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH"
        recommended_next_phase = "v2.9A ? Next Official Provider Route"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "closure_status": closure_status,
        "readiness_score": readiness_score,
        "closure_decision": closure_decision,
        "recommended_next_phase": recommended_next_phase,
        "closed_block": {
            "block_name": "v2.8 ? Cboe / next official provider",
            "phases_closed": [
                "v2.8A ? Cboe Listed Symbols Route Plan",
                "v2.8B ? Cboe Listed Symbols Acquisition Real",
                "v2.8C ? Cboe Listed Symbols Validation",
                "v2.8D ? Rebuild Expanded Source With Cboe Plan",
                "v2.8E ? Rebuild Expanded Source With Cboe Real",
                "v2.8F ? Validate Expanded Source With Cboe",
                "v2.8G ? Expanded Source With Cboe Closure Report",
            ],
        },
        "inputs": {
            "cboe_provider_validation_json": rel(CBOE_VALIDATION_JSON),
            "plan_json": rel(PLAN_JSON),
            "rebuild_json": rel(REBUILD_JSON),
            "validation_json": rel(VALIDATION_JSON),
            "expanded_universe_v2_8e_csv": rel(EXPANDED_CSV),
            "expanded_universe_exclusions_v2_8e_csv": rel(EXCLUSIONS_CSV),
        },
        "final_result": {
            "expanded_universe_csv": rel(EXPANDED_CSV),
            "expanded_universe_exclusions_csv": rel(EXCLUSIONS_CSV),
            "final_expanded_rows": FINAL_EXPANDED_ROWS,
            "final_exclusions_rows": FINAL_EXCLUSIONS_ROWS,
            "cboe_rows_added": CBOE_ROWS_ADDED,
            "duplicate_exchange_ticker_keys": DUPLICATE_EXCHANGE_TICKER_KEYS,
            "issues_count": ISSUES_COUNT,
            "known_issue": "EMPTY_COMPANY_NAME 1193 for Cboe candidate rows",
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
            "cboe_listed_symbols": 1193,
        },
        "next_options": [
            {
                "option": "A",
                "name": "Continue source expansion with next official provider",
                "recommended_phase": "v2.9A ? Next Official Provider Route",
                "reason": "9200 rows is useful but still below 15000 and 50000 thresholds.",
                "status": "RECOMMENDED",
            },
            {
                "option": "B",
                "name": "Return to product/MVP with validated 9200-row universe",
                "recommended_phase": "Product/MVP roadmap refresh",
                "reason": "The project now has a validated expanded universe with Nasdaq, SEC and Cboe candidate rows.",
                "status": "AVAILABLE",
            },
        ],
        "tag_recommendation": "v2.8_expanded_source_with_cboe_closed",
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
            "Close v2.8 with tag, then proceed to v2.9A Next Official Provider Route unless product/MVP utility becomes the priority."
            if not blockers
            else "Resolve blockers before closing v2.8."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.8G Expanded Source With Cboe Closure Report")
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
    md.append("## Final result")
    md.append("")
    md.append(f"- Expanded universe: `{rel(EXPANDED_CSV)}`")
    md.append(f"- Exclusions: `{rel(EXCLUSIONS_CSV)}`")
    md.append(f"- Final expanded rows: {FINAL_EXPANDED_ROWS}")
    md.append(f"- Final exclusions rows: {FINAL_EXCLUSIONS_ROWS}")
    md.append(f"- Cboe rows added: {CBOE_ROWS_ADDED}")
    md.append(f"- Duplicate exchange+ticker keys: {DUPLICATE_EXCHANGE_TICKER_KEYS}")
    md.append(f"- Issues count: {ISSUES_COUNT}")
    md.append("- Known issue: `EMPTY_COMPANY_NAME 1193` for Cboe candidate rows")
    md.append("")
    md.append("## Provider result")
    md.append("")
    md.append("- nasdaq_trader_nasdaqlisted: 3244")
    md.append("- nasdaq_trader_otherlisted: 2404")
    md.append("- sec_company_tickers_exchange: 2359")
    md.append("- cboe_listed_symbols: 1193")
    md.append("- Total: 9200")
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
    md.append("Cboe rebuild is closed as useful but not enough.")
    md.append("")
    md.append("```text")
    md.append("CBOE_REBUILD_CLOSED_USEFUL_BUT_NOT_ENOUGH")
    md.append("FULL_59K_REMAINS_BLOCKED")
    md.append("NEXT_RECOMMENDED_PHASE: v2.9A_NEXT_OFFICIAL_PROVIDER_ROUTE")
    md.append("```")
    md.append("")
    md.append("## Next options")
    md.append("")
    md.append("### Option A ? Continue source expansion")
    md.append("")
    md.append("- Next phase: `v2.9A ? Next Official Provider Route`")
    md.append("- Use if 15k/50k/full-source remains the priority.")
    md.append("")
    md.append("### Option B ? Return to product/MVP")
    md.append("")
    md.append("- Next phase: product/MVP roadmap refresh.")
    md.append("- Use if practical utility with the validated 9200-row universe is now the priority.")
    md.append("")
    md.append("## Tag recommendation")
    md.append("")
    md.append("- `v2.8_expanded_source_with_cboe_closed`")
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
    md.append("Important: v2.8G is closure-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.8G Expanded Source With Cboe Closure Report")
    print("=" * 92)
    print(f"OK   Closure status: {closure_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Closure decision: {closure_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Final expanded rows: {FINAL_EXPANDED_ROWS}")
    print(f"OK   Final exclusions rows: {FINAL_EXCLUSIONS_ROWS}")
    print(f"OK   Cboe rows added: {CBOE_ROWS_ADDED}")
    print(f"OK   Duplicate exchange+ticker keys: {DUPLICATE_EXCHANGE_TICKER_KEYS}")
    print(f"OK   Issues count: {ISSUES_COUNT}")
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
