from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.6B"
METHOD = "sec_company_tickers_exchange_acquisition_plan_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "sec_company_tickers_exchange_acquisition_plan_v2_6b.json"
OUT_MD = OUT_DIR / "sec_company_tickers_exchange_acquisition_plan_v2_6b.md"

ROUTE_JSON = OUT_DIR / "next_official_provider_route_v2_6a.json"

PROVIDER_ID = "sec_company_tickers_exchange"
PROVIDER_NAME = "SEC company_tickers_exchange.json"
SEC_SOURCE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"

PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID
RAW_JSON = PROVIDER_DIR / "company_tickers_exchange.json"
NORMALIZED_CSV = PROVIDER_DIR / "sec_company_tickers_exchange.csv"

CURRENT_INCLUDED_ROWS = 5648
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

    route = read_json(ROUTE_JSON)

    if not route.get("_exists"):
        blockers.append(f"Missing v2.6A route artifact: {rel(ROUTE_JSON)}")
    else:
        positives.append(f"v2.6A route artifact found: {rel(ROUTE_JSON)}")

    route_status = route.get("route_status")
    recommended_next_phase = route.get("recommended_next_phase")

    if route_status == "NEXT_OFFICIAL_PROVIDER_ROUTE_READY":
        positives.append(f"v2.6A route status accepted: {route_status}")
    else:
        blockers.append(f"Unexpected v2.6A route status: {route_status}")

    if recommended_next_phase == "v2.6B ? SEC Company Tickers Exchange Acquisition Plan":
        positives.append(f"v2.6A recommended phase accepted: {recommended_next_phase}")
    else:
        warnings.append(f"Unexpected v2.6A recommended phase: {recommended_next_phase}")

    rows_needed_first_expansion = max(TARGET_FIRST_EXPANSION_ROWS - CURRENT_INCLUDED_ROWS, 0)
    rows_needed_full_source = max(MIN_FULL_SOURCE_ROWS - CURRENT_INCLUDED_ROWS, 0)

    warnings.append(f"Rows still needed for first expansion target before SEC acquisition: {rows_needed_first_expansion}")
    warnings.append(f"Rows still needed for full-source threshold before SEC acquisition: {rows_needed_full_source}")

    expected_schema = {
        "top_level": {
            "fields": "list[str] expected to include cik, name, ticker, exchange",
            "data": "list[list] records matching fields order",
        },
        "expected_fields": [
            "cik",
            "name",
            "ticker",
            "exchange",
        ],
        "canonical_columns_after_normalization": [
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
        ],
    }

    acquisition_plan = {
        "provider_id": PROVIDER_ID,
        "provider_name": PROVIDER_NAME,
        "provider_type": "official_sec_identifier_exchange_mapping",
        "source_url": SEC_SOURCE_URL,
        "provider_dir": rel(PROVIDER_DIR),
        "raw_json": rel(RAW_JSON),
        "normalized_csv": rel(NORMALIZED_CSV),
        "phase_for_real_acquisition": "v2.6C",
        "mode": "PLAN_ONLY_NO_DOWNLOAD",
        "user_agent_policy": {
            "required": True,
            "recommended_env_var": "SCOUT_FINANCE_SEC_USER_AGENT",
            "fallback_format": "ScoutFinance/1.0 contact@example.com",
            "notes": "Real acquisition must use a declared User-Agent. Replace fallback email with a valid contact before running v2.6C.",
        },
        "rate_limit_policy": {
            "max_requests_per_second": 10,
            "planned_requests": 1,
            "notes": "v2.6C should perform one controlled request only.",
        },
        "expected_schema": expected_schema,
        "normalization_rules": [
            "Map ticker -> ticker uppercase/trimmed.",
            "Map name -> company_name.",
            "Map exchange -> exchange normalized but preserve raw_exchange.",
            "Map cik -> raw_cik as string without losing leading semantics.",
            "Set country to USA for SEC mapping source.",
            "Set source_provider to sec_company_tickers_exchange.",
            "Set source_file to raw JSON relative path.",
            "Do not infer instrument_type as COMMON_STOCK solely from SEC mapping.",
            "Default instrument_type to UNKNOWN_PENDING_CLASSIFICATION unless classified later.",
            "Default instrument_scope to UNKNOWN_PENDING_CLASSIFICATION unless classified later.",
            "Do not merge into expanded_universe in v2.6C.",
        ],
        "validation_rules_for_v2_6C": [
            "Raw JSON exists and is readable.",
            "Top-level fields/data keys exist.",
            "Expected fields include cik, name, ticker, exchange.",
            "Row count is reported.",
            "Empty ticker/name/exchange/cik counts are reported.",
            "Duplicate exchange+ticker keys are reported.",
            "Exchange counts are reported.",
            "Normalized CSV is written only if schema is recognized.",
        ],
        "controls_for_v2_6C": [
            "No OpenAI.",
            "No broker.",
            "No scoring recalculation.",
            "No full 59k universe launch.",
            "No active output overwrite.",
            "No expanded_universe rebuild.",
            "One controlled network request.",
            "Raw JSON preserved.",
            "JSON and Markdown acquisition report produced.",
        ],
    }

    if blockers:
        plan_status = "SEC_COMPANY_TICKERS_EXCHANGE_PLAN_BLOCKED"
        readiness_score = 0
    else:
        plan_status = "SEC_COMPANY_TICKERS_EXCHANGE_PLAN_READY"
        readiness_score = 95

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "plan_status": plan_status,
        "readiness_score": readiness_score,
        "provider": acquisition_plan,
        "current_state": {
            "current_included_rows": CURRENT_INCLUDED_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "rows_needed_first_expansion": rows_needed_first_expansion,
            "rows_needed_full_source": rows_needed_full_source,
            "expanded_universe_rebuild_allowed": False,
            "full_59000_remains_blocked": True,
        },
        "recommended_next_phase": {
            "phase": "v2.6C",
            "name": "SEC Company Tickers Exchange Acquisition Real",
            "mode": "CONTROLLED_SINGLE_REQUEST_ACQUISITION",
            "reason": "Plan is ready; next step can perform one SEC-compliant controlled download into isolated provider directory.",
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
            "Proceed to v2.6C for one controlled SEC download after setting a valid SEC User-Agent contact."
            if not blockers
            else "Resolve blockers before SEC acquisition."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.6B SEC Company Tickers Exchange Acquisition Plan")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Plan status: **{plan_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Provider: **{PROVIDER_NAME}**")
    md.append(f"- Provider ID: `{PROVIDER_ID}`")
    md.append(f"- Source URL: `{SEC_SOURCE_URL}`")
    md.append(f"- Real acquisition phase: **v2.6C**")
    md.append(f"- Mode: **PLAN_ONLY_NO_DOWNLOAD**")
    md.append("")
    md.append("## Current state")
    md.append("")
    md.append(f"- Current included rows: {CURRENT_INCLUDED_ROWS}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Rows needed for first expansion target: {rows_needed_first_expansion}")
    md.append(f"- Rows needed for full-source threshold: {rows_needed_full_source}")
    md.append("- Expanded universe rebuild allowed: false")
    md.append("- Full 59k remains blocked: true")
    md.append("")
    md.append("## SEC User-Agent policy")
    md.append("")
    md.append("- A declared SEC User-Agent is required before v2.6C.")
    md.append("- Recommended environment variable: `SCOUT_FINANCE_SEC_USER_AGENT`")
    md.append("- Fallback format: `ScoutFinance/1.0 contact@example.com`")
    md.append("- Replace fallback email with a valid contact before real acquisition.")
    md.append("")
    md.append("## Expected schema")
    md.append("")
    md.append("Top-level SEC JSON structure expected:")
    md.append("")
    md.append("- `fields`: ordered list of field names")
    md.append("- `data`: list of records matching field order")
    md.append("")
    md.append("Expected fields:")
    for field in expected_schema["expected_fields"]:
        md.append(f"- `{field}`")
    md.append("")
    md.append("Canonical columns after normalization:")
    for column in expected_schema["canonical_columns_after_normalization"]:
        md.append(f"- `{column}`")
    md.append("")
    md.append("## Normalization rules")
    md.append("")
    for rule in acquisition_plan["normalization_rules"]:
        md.append(f"- {rule}")
    md.append("")
    md.append("## Acceptance criteria for v2.6C")
    md.append("")
    for rule in acquisition_plan["validation_rules_for_v2_6C"]:
        md.append(f"- {rule}")
    md.append("")
    md.append("## Controls for v2.6C")
    md.append("")
    for control in acquisition_plan["controls_for_v2_6C"]:
        md.append(f"- {control}")
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
    md.append("Important: v2.6B is a planning artifact only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.6B SEC Company Tickers Exchange Acquisition Plan")
    print("=" * 92)
    print(f"OK   Plan status: {plan_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Provider: {PROVIDER_ID}")
    print(f"OK   Source URL: {SEC_SOURCE_URL}")
    print(f"OK   Current included rows: {CURRENT_INCLUDED_ROWS}")
    print(f"OK   Rows needed first expansion: {rows_needed_first_expansion}")
    print(f"OK   Rows needed full source: {rows_needed_full_source}")
    print(f"OK   Recommended next phase: v2.6C SEC Company Tickers Exchange Acquisition Real")
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
