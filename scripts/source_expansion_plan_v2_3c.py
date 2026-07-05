from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.3C"
METHOD = "source_expansion_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "source_expansion_plan_v2_3c.json"
OUT_MD = OUT_DIR / "source_expansion_plan_v2_3c.md"

STRATEGY_V2_3B = OUT_DIR / "full_universe_source_strategy_v2_3b.json"

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000
TARGET_FIRST_EXPANSION_ROWS = 15000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}

    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    strategy = read_json(STRATEGY_V2_3B)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    if not strategy.get("_exists"):
        blockers.append(f"Missing required v2.3B strategy artifact: {rel(STRATEGY_V2_3B)}")
        strategy_decision = None
    else:
        strategy_decision = strategy.get("decision")
        positives.append(f"v2.3B strategy found and readable: {rel(STRATEGY_V2_3B)}")

    if strategy_decision == "EXTERNAL_OR_EXPANDED_SOURCE_REQUIRED":
        positives.append("v2.3B confirms that an expanded source is required.")
    elif strategy_decision == "FULL_SOURCE_CANDIDATE_AVAILABLE":
        warnings.append("v2.3B found a full candidate; expansion plan may be optional.")
    else:
        blockers.append(f"v2.3B decision is not compatible with expansion planning: {strategy_decision}")

    canonical_schema = [
        {
            "column": "ticker",
            "required": True,
            "description": "Normalized ticker/symbol. Must be uppercase and non-empty.",
        },
        {
            "column": "company_name",
            "required": True,
            "description": "Company/security name from source.",
        },
        {
            "column": "exchange",
            "required": True,
            "description": "Exchange or market identifier.",
        },
        {
            "column": "country",
            "required": True,
            "description": "Country or market region.",
        },
        {
            "column": "sector",
            "required": False,
            "description": "Sector if available.",
        },
        {
            "column": "industry",
            "required": False,
            "description": "Industry if available.",
        },
        {
            "column": "market_cap",
            "required": False,
            "description": "Market capitalization if available.",
        },
        {
            "column": "source_provider",
            "required": True,
            "description": "Provider or exchange source name.",
        },
        {
            "column": "source_file",
            "required": True,
            "description": "Original source file path or source identifier.",
        },
        {
            "column": "instrument_type",
            "required": True,
            "description": "COMMON_STOCK, ETF, FUND, ADR, PREFERRED, WARRANT, etc.",
        },
        {
            "column": "instrument_scope",
            "required": True,
            "description": "IN_SCOPE or OUT_OF_SCOPE for Scout Finance universe.",
        },
        {
            "column": "classification_confidence",
            "required": True,
            "description": "HIGH, MEDIUM or LOW confidence after classification.",
        },
        {
            "column": "classification_reason",
            "required": True,
            "description": "Short reason for instrument inclusion/exclusion.",
        },
    ]

    source_groups = [
        {
            "priority": 1,
            "group": "US official exchange symbol lists",
            "target_exchanges": ["NASDAQ", "NYSE", "AMEX"],
            "expected_use": "Expand and refresh current US public-market universe.",
            "status": "PRIMARY_ROUTE",
            "risk": "LOW_MEDIUM",
        },
        {
            "priority": 2,
            "group": "Additional North American listings",
            "target_exchanges": ["NYSE Arca", "Cboe", "OTC candidates only if explicitly approved"],
            "expected_use": "Increase coverage after core US exchanges are stable.",
            "status": "SECONDARY_ROUTE",
            "risk": "MEDIUM",
        },
        {
            "priority": 3,
            "group": "European official exchange lists",
            "target_exchanges": ["London", "Euronext", "Frankfurt/Xetra", "Madrid/BME", "SIX"],
            "expected_use": "Move toward global universe once US expansion is reproducible.",
            "status": "LATER_ROUTE",
            "risk": "HIGH",
        },
        {
            "priority": 4,
            "group": "Asia-Pacific official exchange lists",
            "target_exchanges": ["Tokyo", "Hong Kong", "Singapore", "Australia"],
            "expected_use": "Long-term global expansion.",
            "status": "LATER_ROUTE",
            "risk": "HIGH",
        },
    ]

    deduplication_rules = [
        "Primary key must be exchange + ticker, not ticker alone.",
        "Ticker collisions across exchanges must be preserved as separate instruments.",
        "Exact duplicate exchange+ticker rows must be collapsed.",
        "If duplicate rows have conflicting company names, keep the longest non-empty name and flag warning.",
        "If duplicate rows have conflicting country/exchange values, flag blocker for that source.",
        "Never merge different instrument types under one ticker without explicit classification.",
    ]

    exclusion_rules = [
        "Exclude instruments without ticker.",
        "Exclude obvious test rows, placeholders and malformed symbols.",
        "Exclude warrants, rights, units and preferred shares from IN_SCOPE unless explicitly approved.",
        "Classify ETFs/funds separately; do not mix with common-stock scouting unless approved.",
        "ADR treatment must be explicit: either IN_SCOPE_ADR or OUT_OF_SCOPE_ADR.",
        "Rows with low classification confidence must be reviewable before full dry-run.",
    ]

    validation_gates = [
        {
            "gate": "v2.3D",
            "name": "Source Provider Inventory",
            "goal": "Create a machine-readable inventory of target source providers/exchanges.",
            "unlock_condition": "Providers listed with expected schema and acquisition method.",
        },
        {
            "gate": "v2.3E",
            "name": "Expanded Source Builder Skeleton",
            "goal": "Create a no-network skeleton that combines local provider files if present.",
            "unlock_condition": "Builder can run safely without downloads and without scoring.",
        },
        {
            "gate": "v2.3F",
            "name": "Expanded Source Validation",
            "goal": "Validate the expanded source using canonical schema and row thresholds.",
            "unlock_condition": f"At least {TARGET_FIRST_EXPANSION_ROWS} rows for first expansion, later {MIN_FULL_SOURCE_ROWS}+ rows for full gate.",
        },
        {
            "gate": "repeat_v2.2C",
            "name": "Repeat Source Validation",
            "goal": "Run v2.2C against the expanded source.",
            "unlock_condition": "Ticker mapping, duplicates and blockers clean.",
        },
        {
            "gate": "repeat_v2.2E",
            "name": "Repeat Full Dry Run Gate",
            "goal": "Run v2.2E again after expanded source exists.",
            "unlock_condition": f"Source rows >= {MIN_FULL_SOURCE_ROWS} and safety controls clean.",
        },
    ]

    if blockers:
        plan_status = "SOURCE_EXPANSION_PLAN_BLOCKED"
        readiness_score = 0
    elif warnings:
        plan_status = "SOURCE_EXPANSION_PLAN_READY_WITH_WARNINGS"
        readiness_score = 85
    else:
        plan_status = "SOURCE_EXPANSION_PLAN_READY"
        readiness_score = 100

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "plan_status": plan_status,
        "readiness_score": readiness_score,
        "strategy_input": {
            "path": rel(STRATEGY_V2_3B),
            "exists": strategy.get("_exists"),
            "decision": strategy_decision,
        },
        "targets": {
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
        },
        "canonical_schema": canonical_schema,
        "source_groups": source_groups,
        "deduplication_rules": deduplication_rules,
        "exclusion_rules": exclusion_rules,
        "validation_gates": validation_gates,
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
        },
        "recommendation": (
            "Proceed to v2.3D Source Provider Inventory. Do not download data yet."
            if not blockers
            else "Resolve blockers before source expansion."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.3C Source Expansion Plan")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Plan status: **{plan_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Strategy input decision: **{strategy_decision}**")
    md.append(f"- Expected full rows: {EXPECTED_FULL_ROWS}")
    md.append(f"- Minimum full source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
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
    md.append("")
    md.append("## Canonical schema")
    md.append("")
    for item in canonical_schema:
        required = "required" if item["required"] else "optional"
        md.append(f"- `{item['column']}` ? {required}: {item['description']}")
    md.append("")
    md.append("## Source groups")
    md.append("")
    for group in source_groups:
        md.append(f"### Priority {group['priority']} ? {group['group']}")
        md.append("")
        md.append(f"- Status: {group['status']}")
        md.append(f"- Risk: {group['risk']}")
        md.append(f"- Target exchanges: {', '.join(group['target_exchanges'])}")
        md.append(f"- Expected use: {group['expected_use']}")
        md.append("")
    md.append("## Deduplication rules")
    md.append("")
    for item in deduplication_rules:
        md.append(f"- {item}")
    md.append("")
    md.append("## Exclusion rules")
    md.append("")
    for item in exclusion_rules:
        md.append(f"- {item}")
    md.append("")
    md.append("## Validation gates")
    md.append("")
    for gate in validation_gates:
        md.append(f"### {gate['gate']} ? {gate['name']}")
        md.append("")
        md.append(f"- Goal: {gate['goal']}")
        md.append(f"- Unlock condition: {gate['unlock_condition']}")
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
    md.append("Important: v2.3C is a plan only. It does not download data, execute scoring, call OpenAI, call a broker, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.3C Source Expansion Plan")
    print("=" * 92)
    print(f"OK   Plan status: {plan_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Strategy decision: {strategy_decision}")
    print(f"OK   Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    print(f"OK   Minimum full source rows: {MIN_FULL_SOURCE_ROWS}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Network download performed: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
