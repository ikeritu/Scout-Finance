from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.5C"
METHOD = "controlled_nyse_provider_acquisition_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "controlled_nyse_provider_acquisition_plan_v2_5c.json"
OUT_MD = OUT_DIR / "controlled_nyse_provider_acquisition_plan_v2_5c.md"

NEXT_PROVIDER_PLAN_JSON = OUT_DIR / "next_provider_acquisition_plan_v2_5b.json"
REVALIDATION_JSON = OUT_DIR / "expanded_source_revalidation_gate_v2_5a.json"

CURRENT_INCLUDED_ROWS_EXPECTED = 5648
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


def read_json(path: Path) -> dict:
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

    next_provider_plan = read_json(NEXT_PROVIDER_PLAN_JSON)
    revalidation = read_json(REVALIDATION_JSON)

    if not next_provider_plan.get("_exists"):
        blockers.append(f"Missing v2.5B provider plan artifact: {rel(NEXT_PROVIDER_PLAN_JSON)}")
    else:
        positives.append(f"v2.5B provider plan artifact found: {rel(NEXT_PROVIDER_PLAN_JSON)}")

    if not revalidation.get("_exists"):
        blockers.append(f"Missing v2.5A revalidation artifact: {rel(REVALIDATION_JSON)}")
    else:
        positives.append(f"v2.5A revalidation artifact found: {rel(REVALIDATION_JSON)}")

    v2_5b_status = next_provider_plan.get("plan_status")
    if v2_5b_status == "NEXT_PROVIDER_PLAN_READY":
        positives.append(f"v2.5B plan status accepted: {v2_5b_status}")
    else:
        blockers.append(f"Unexpected v2.5B plan status: {v2_5b_status}")

    current_state = next_provider_plan.get("current_state", {}) if isinstance(next_provider_plan.get("current_state"), dict) else {}
    current_rows = int(current_state.get("current_included_rows") or CURRENT_INCLUDED_ROWS_EXPECTED)

    rows_needed_first_expansion = max(TARGET_FIRST_EXPANSION_ROWS - current_rows, 0)
    rows_needed_full_source = max(MIN_FULL_SOURCE_ROWS - current_rows, 0)

    if current_rows > 0:
        positives.append(f"Current expanded source rows confirmed: {current_rows}")
    else:
        blockers.append("Current expanded source row count is zero or unavailable.")

    warnings.append(f"Rows still needed for first expansion target before NYSE acquisition: {rows_needed_first_expansion}")
    warnings.append(f"Rows still needed for full-source threshold before NYSE acquisition: {rows_needed_full_source}")

    nyse_provider_plan = {
        "provider_id": "nyse_listed_directory",
        "provider_name": "NYSE Listed Directory",
        "provider_type": "official_exchange_listing_source",
        "priority": 1,
        "phase_for_real_acquisition": "v2.5D",
        "mode": "PLAN_ONLY_NO_DOWNLOAD",
        "expected_role": "Add official NYSE-listed instrument coverage and compare/merge with existing Nasdaq Trader otherlisted coverage.",
        "expected_inputs": [
            {
                "logical_name": "nyse_listed_directory_source",
                "expected_location": "data/raw/source_providers/nyse_listed_directory/",
                "expected_format": "csv_or_downloaded_exchange_file",
                "required_before_build": True,
            }
        ],
        "expected_canonical_columns_after_normalization": [
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
            "raw_exchange_code",
            "raw_etf_flag",
            "raw_test_issue_flag",
        ],
        "deduplication_rules": [
            "Primary uniqueness key must remain exchange+ticker.",
            "If NYSE rows duplicate existing Nasdaq Trader otherlisted NYSE rows, keep one canonical record.",
            "Prefer official exchange-specific provider row when provider confidence is higher.",
            "Never overwrite active MVP outputs during provider acquisition.",
            "Write NYSE raw and normalized files in isolated provider folder.",
        ],
        "risk_register": [
            {
                "risk": "Overlap with Nasdaq Trader otherlisted NYSE rows",
                "severity": "HIGH",
                "mitigation": "Run post-acquisition duplicate comparison by exchange+ticker before rebuilding expanded source.",
            },
            {
                "risk": "Provider schema drift",
                "severity": "MEDIUM",
                "mitigation": "Validate headers and row count before canonical normalization.",
            },
            {
                "risk": "Non-common-stock instruments included",
                "severity": "MEDIUM",
                "mitigation": "Reuse current instrument classification/exclusion rules before inclusion.",
            },
            {
                "risk": "Low incremental row gain",
                "severity": "MEDIUM",
                "mitigation": "Report gross rows, duplicate rows, excluded rows, and net new included rows separately.",
            },
            {
                "risk": "Network/download instability",
                "severity": "LOW",
                "mitigation": "Keep network acquisition isolated in v2.5D with timeout and no downstream rebuild by default.",
            },
        ],
        "acceptance_criteria_for_v2_5D": [
            "Download or acquire NYSE provider file into isolated raw provider folder.",
            "No OpenAI calls.",
            "No broker calls.",
            "No scoring recalculation.",
            "No full 59k launch.",
            "No overwrite of active MVP outputs.",
            "Produce raw acquisition JSON and Markdown report.",
            "Report network status, URL/source path, file size, row count, headers, and errors.",
        ],
        "acceptance_criteria_before_rebuild_v2_5E": [
            "NYSE provider file exists and is readable.",
            "Headers/schema are understood.",
            "Row count is reported.",
            "Duplicate risk against existing expanded source is measured.",
            "Instrument classification rules are prepared.",
            "Commit checkpoint exists before rebuild.",
        ],
    }

    if blockers:
        plan_status = "CONTROLLED_NYSE_PROVIDER_PLAN_BLOCKED"
        readiness_score = 0
    else:
        plan_status = "CONTROLLED_NYSE_PROVIDER_PLAN_READY"
        readiness_score = 95

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "plan_status": plan_status,
        "readiness_score": readiness_score,
        "current_state": {
            "current_included_rows": current_rows,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "rows_needed_first_expansion": rows_needed_first_expansion,
            "rows_needed_full_source": rows_needed_full_source,
        },
        "nyse_provider_plan": nyse_provider_plan,
        "recommended_next_phase": {
            "phase": "v2.5D",
            "name": "Controlled NYSE Provider Acquisition Real",
            "mode": "NETWORK_ACQUISITION_ISOLATED",
            "reason": "NYSE provider route is now planned and can be acquired in a controlled isolated step.",
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
        },
        "recommendation": (
            "Proceed to v2.5D as isolated real NYSE provider acquisition. Do not rebuild expanded source until NYSE acquisition output is reviewed."
            if not blockers
            else "Resolve blockers before attempting NYSE acquisition."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.5C Controlled NYSE Provider Acquisition Plan")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Plan status: **{plan_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Current included rows: {current_rows}")
    md.append(f"- Rows needed for first expansion target: {rows_needed_first_expansion}")
    md.append(f"- Rows needed for full-source threshold: {rows_needed_full_source}")
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
    md.append("")
    md.append("## NYSE provider plan")
    md.append("")
    md.append(f"- Provider ID: `{nyse_provider_plan['provider_id']}`")
    md.append(f"- Provider name: {nyse_provider_plan['provider_name']}")
    md.append(f"- Provider type: {nyse_provider_plan['provider_type']}")
    md.append(f"- Priority: {nyse_provider_plan['priority']}")
    md.append(f"- Real acquisition phase: {nyse_provider_plan['phase_for_real_acquisition']}")
    md.append(f"- Mode: {nyse_provider_plan['mode']}")
    md.append(f"- Expected role: {nyse_provider_plan['expected_role']}")
    md.append("")
    md.append("## Expected inputs")
    md.append("")
    for item in nyse_provider_plan["expected_inputs"]:
        md.append(f"- {item['logical_name']}: `{item['expected_location']}` ? format: {item['expected_format']}")
    md.append("")
    md.append("## Expected canonical columns")
    md.append("")
    for column in nyse_provider_plan["expected_canonical_columns_after_normalization"]:
        md.append(f"- `{column}`")
    md.append("")
    md.append("## Deduplication rules")
    md.append("")
    for rule in nyse_provider_plan["deduplication_rules"]:
        md.append(f"- {rule}")
    md.append("")
    md.append("## Risk register")
    md.append("")
    for risk in nyse_provider_plan["risk_register"]:
        md.append(f"- **{risk['severity']}** ? {risk['risk']}: {risk['mitigation']}")
    md.append("")
    md.append("## Acceptance criteria for v2.5D")
    md.append("")
    for criterion in nyse_provider_plan["acceptance_criteria_for_v2_5D"]:
        md.append(f"- {criterion}")
    md.append("")
    md.append("## Acceptance criteria before v2.5E rebuild")
    md.append("")
    for criterion in nyse_provider_plan["acceptance_criteria_before_rebuild_v2_5E"]:
        md.append(f"- {criterion}")
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
    md.append("Important: v2.5C is a planning artifact only. It does not download data, call OpenAI, call a broker, execute scoring, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.5C Controlled NYSE Provider Acquisition Plan")
    print("=" * 92)
    print(f"OK   Plan status: {plan_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Current included rows: {current_rows}")
    print(f"OK   Rows needed first expansion: {rows_needed_first_expansion}")
    print(f"OK   Rows needed full source: {rows_needed_full_source}")
    print(f"OK   Provider planned: {nyse_provider_plan['provider_id']}")
    print(f"OK   Recommended next phase: v2.5D Controlled NYSE Provider Acquisition Real")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
