from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.5B"
METHOD = "next_provider_acquisition_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "next_provider_acquisition_plan_v2_5b.json"
OUT_MD = OUT_DIR / "next_provider_acquisition_plan_v2_5b.md"

REVALIDATION_JSON = OUT_DIR / "expanded_source_revalidation_gate_v2_5a.json"
CLOSURE_JSON = OUT_DIR / "expanded_source_partial_closure_v2_4d.json"

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
CURRENT_INCLUDED_ROWS_EXPECTED = 5648


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

    revalidation = read_json(REVALIDATION_JSON)
    closure = read_json(CLOSURE_JSON)

    if not revalidation.get("_exists"):
        blockers.append(f"Missing v2.5A revalidation artifact: {rel(REVALIDATION_JSON)}")
    else:
        positives.append(f"v2.5A revalidation artifact found: {rel(REVALIDATION_JSON)}")

    if not closure.get("_exists"):
        blockers.append(f"Missing v2.4D closure artifact: {rel(CLOSURE_JSON)}")
    else:
        positives.append(f"v2.4D closure artifact found: {rel(CLOSURE_JSON)}")

    gate_decision = revalidation.get("gate_decision")
    revalidation_source = revalidation.get("expanded_source", {}) if isinstance(revalidation.get("expanded_source"), dict) else {}
    current_rows = int(revalidation_source.get("included_rows") or CURRENT_INCLUDED_ROWS_EXPECTED)

    if gate_decision == "EXPANDED_SOURCE_REVALIDATED_PARTIAL_BELOW_TARGET":
        positives.append(f"v2.5A gate decision accepted: {gate_decision}")
    else:
        warnings.append(f"Unexpected or different v2.5A gate decision: {gate_decision}")

    rows_needed_first_expansion = max(TARGET_FIRST_EXPANSION_ROWS - current_rows, 0)
    rows_needed_full_source = max(MIN_FULL_SOURCE_ROWS - current_rows, 0)

    if current_rows > 0:
        positives.append(f"Current expanded source has usable rows: {current_rows}")
    else:
        blockers.append("Current expanded source has no usable rows.")

    if rows_needed_first_expansion > 0:
        warnings.append(f"Rows still needed for first expansion target: {rows_needed_first_expansion}")

    if rows_needed_full_source > 0:
        warnings.append(f"Rows still needed for full-source threshold: {rows_needed_full_source}")

    provider_candidates = [
        {
            "priority": 1,
            "provider_id": "nyse_listed_directory",
            "provider_name": "NYSE Listed Directory",
            "role": "Close gap for NYSE coverage and validate against Nasdaq Trader otherlisted overlap.",
            "expected_value": "HIGH",
            "risk": "MEDIUM",
            "network_required": True,
            "recommended_phase": "v2.5C",
            "decision": "NEXT_PROVIDER_CANDIDATE",
            "notes": "Use as the next controlled provider because it was already identified in the source expansion inventory.",
        },
        {
            "priority": 2,
            "provider_id": "exchange_official_listings_additional",
            "provider_name": "Additional official exchange listing files",
            "role": "Increase public equity universe beyond Nasdaq Trader partial coverage.",
            "expected_value": "HIGH",
            "risk": "MEDIUM",
            "network_required": True,
            "recommended_phase": "v2.5D_or_later",
            "decision": "QUEUE_AFTER_NYSE",
            "notes": "Only add after NYSE route is implemented and validated.",
        },
        {
            "priority": 3,
            "provider_id": "sec_company_tickers",
            "provider_name": "SEC company tickers/company facts mapping",
            "role": "Improve identifier mapping and public company coverage, not necessarily exchange-listed universe completeness.",
            "expected_value": "MEDIUM",
            "risk": "MEDIUM",
            "network_required": True,
            "recommended_phase": "v2.6_or_later",
            "decision": "OPTIONAL_IDENTIFIER_ENRICHMENT",
            "notes": "Useful later for CIK/ticker mapping, but should not be treated as full listing source by itself.",
        },
        {
            "priority": 4,
            "provider_id": "kaggle_or_third_party_datasets",
            "provider_name": "Third-party public datasets",
            "role": "Possible row-count expansion, but requires stricter license and freshness review.",
            "expected_value": "MEDIUM",
            "risk": "HIGH",
            "network_required": True,
            "recommended_phase": "not_first_choice",
            "decision": "DEFER",
            "notes": "Do not use before official provider routes unless explicitly reviewed.",
        },
    ]

    if blockers:
        plan_status = "NEXT_PROVIDER_PLAN_BLOCKED"
        readiness_score = 0
    else:
        plan_status = "NEXT_PROVIDER_PLAN_READY"
        readiness_score = 90

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "plan_status": plan_status,
        "readiness_score": readiness_score,
        "current_state": {
            "v2_5a_gate_decision": gate_decision,
            "current_included_rows": current_rows,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "rows_needed_first_expansion": rows_needed_first_expansion,
            "rows_needed_full_source": rows_needed_full_source,
        },
        "provider_candidates": provider_candidates,
        "recommended_next_phase": {
            "phase": "v2.5C",
            "name": "Controlled NYSE Provider Acquisition Plan",
            "mode": "PLAN_FIRST_NO_DOWNLOAD",
            "reason": "NYSE was already a primary first-expansion provider candidate and should be handled with a plan/gate before any network acquisition.",
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
            "Proceed with v2.5C as a plan-only NYSE provider acquisition gate. Do not download more data until that plan is reviewed."
            if not blockers
            else "Resolve blockers before planning further provider acquisition."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.5B Next Provider Acquisition Plan")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Plan status: **{plan_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Current included rows: {current_rows}")
    md.append(f"- First expansion target: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Full-source threshold: {MIN_FULL_SOURCE_ROWS}")
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
    md.append("## Provider candidates")
    md.append("")
    for provider in provider_candidates:
        md.append(f"### {provider['priority']}. {provider['provider_name']}")
        md.append("")
        md.append(f"- Provider ID: `{provider['provider_id']}`")
        md.append(f"- Decision: **{provider['decision']}**")
        md.append(f"- Expected value: {provider['expected_value']}")
        md.append(f"- Risk: {provider['risk']}")
        md.append(f"- Recommended phase: {provider['recommended_phase']}")
        md.append(f"- Role: {provider['role']}")
        md.append(f"- Notes: {provider['notes']}")
        md.append("")
    md.append("## Recommended next phase")
    md.append("")
    md.append("- **v2.5C ? Controlled NYSE Provider Acquisition Plan**")
    md.append("- Mode: plan first, no download")
    md.append("- Reason: NYSE was already identified as first-expansion provider candidate.")
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
    md.append("Important: v2.5B is a planning artifact only. It does not download data, call OpenAI, call a broker, execute scoring, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.5B Next Provider Acquisition Plan")
    print("=" * 92)
    print(f"OK   Plan status: {plan_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Current included rows: {current_rows}")
    print(f"OK   Rows needed first expansion: {rows_needed_first_expansion}")
    print(f"OK   Rows needed full source: {rows_needed_full_source}")
    print(f"OK   Provider candidates: {len(provider_candidates)}")
    print(f"OK   Recommended next phase: v2.5C Controlled NYSE Provider Acquisition Plan")
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
