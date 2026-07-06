from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.5G"
METHOD = "nyse_usability_decision_gate_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "nyse_usability_decision_gate_v2_5g.json"
OUT_MD = OUT_DIR / "nyse_usability_decision_gate_v2_5g.md"

ACQUISITION_JSON = OUT_DIR / "controlled_nyse_provider_acquisition_real_v2_5d.json"
DISCOVERY_JSON = OUT_DIR / "nyse_endpoint_discovery_review_v2_5e.json"
VALIDATION_JSON = OUT_DIR / "nyse_endpoint_candidate_validation_v2_5f.json"

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

    acquisition = read_json(ACQUISITION_JSON)
    discovery = read_json(DISCOVERY_JSON)
    validation = read_json(VALIDATION_JSON)

    if not acquisition.get("_exists"):
        blockers.append(f"Missing v2.5D acquisition artifact: {rel(ACQUISITION_JSON)}")
    else:
        positives.append(f"v2.5D acquisition artifact found: {rel(ACQUISITION_JSON)}")

    if not discovery.get("_exists"):
        blockers.append(f"Missing v2.5E discovery artifact: {rel(DISCOVERY_JSON)}")
    else:
        positives.append(f"v2.5E discovery artifact found: {rel(DISCOVERY_JSON)}")

    if not validation.get("_exists"):
        blockers.append(f"Missing v2.5F validation artifact: {rel(VALIDATION_JSON)}")
    else:
        positives.append(f"v2.5F validation artifact found: {rel(VALIDATION_JSON)}")

    acquisition_status = acquisition.get("acquisition_status")
    discovery_status = discovery.get("discovery_status")
    validation_status = validation.get("validation_status")
    validation_usability = validation.get("usability_decision")

    acquisition_summary = acquisition.get("extraction", {}) if isinstance(acquisition.get("extraction"), dict) else {}
    discovery_summary = discovery.get("summary", {}) if isinstance(discovery.get("summary"), dict) else {}
    endpoint_validation = validation.get("endpoint_validation", {}) if isinstance(validation.get("endpoint_validation"), dict) else {}
    js_validation = validation.get("javascript_asset_validation", {}) if isinstance(validation.get("javascript_asset_validation"), dict) else {}

    extracted_rows = int(acquisition_summary.get("extracted_rows") or 0)
    api_candidates = int(discovery_summary.get("api_candidates") or 0)
    csv_candidates = int(discovery_summary.get("csv_candidates") or 0)
    javascript_assets = int(discovery_summary.get("javascript_assets") or 0)

    endpoint_status = endpoint_validation.get("status")
    endpoint_status_code = endpoint_validation.get("status_code")
    js_findings = int(js_validation.get("finding_count") or 0)
    js_assets_inspected = len(js_validation.get("downloaded_assets", [])) if isinstance(js_validation.get("downloaded_assets"), list) else 0

    if acquisition_status == "NYSE_PROVIDER_ACQUISITION_RAW_ONLY_REVIEW_REQUIRED":
        positives.append(f"v2.5D status accepted: {acquisition_status}")
    else:
        warnings.append(f"Unexpected v2.5D status: {acquisition_status}")

    if discovery_status == "NYSE_ENDPOINT_DISCOVERY_API_CANDIDATE_FOUND":
        positives.append(f"v2.5E status accepted: {discovery_status}")
    else:
        warnings.append(f"Unexpected v2.5E status: {discovery_status}")

    if validation_status == "NYSE_ENDPOINT_CANDIDATE_VALIDATION_JS_HINTS_FOUND":
        positives.append(f"v2.5F status accepted: {validation_status}")
    else:
        warnings.append(f"Unexpected v2.5F status: {validation_status}")

    if extracted_rows == 0:
        positives.append("NYSE raw acquisition produced 0 normalized rows, so rebuild remains blocked.")
    else:
        warnings.append(f"NYSE extracted rows detected: {extracted_rows}")

    if csv_candidates == 0:
        positives.append("No direct CSV candidate detected.")
    else:
        warnings.append(f"CSV candidates detected and require review: {csv_candidates}")

    if api_candidates > 0:
        positives.append(f"API candidates detected: {api_candidates}")
    else:
        warnings.append("No API candidates detected.")

    if endpoint_status == "ENDPOINT_HTTP_FAILED" and str(endpoint_status_code) == "404":
        positives.append("Proxy endpoint direct request failed with 404, so it is not directly usable.")
    elif endpoint_status:
        warnings.append(f"Endpoint returned non-final status: {endpoint_status} / {endpoint_status_code}")

    if js_findings > 0:
        positives.append(f"JS hints detected: {js_findings}")
    else:
        warnings.append("No JS hints detected.")

    if js_assets_inspected > 0:
        positives.append(f"JS assets inspected: {js_assets_inspected}")
    else:
        warnings.append("No JS assets inspected.")

    rows_needed_first_expansion = max(TARGET_FIRST_EXPANSION_ROWS - CURRENT_INCLUDED_ROWS, 0)
    rows_needed_full_source = max(MIN_FULL_SOURCE_ROWS - CURRENT_INCLUDED_ROWS, 0)

    warnings.append(f"Rows still needed for first expansion target: {rows_needed_first_expansion}")
    warnings.append(f"Rows still needed for full-source threshold: {rows_needed_full_source}")

    if blockers:
        decision_status = "NYSE_USABILITY_DECISION_BLOCKED"
        readiness_score = 0
        nyse_usability_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    elif extracted_rows > 0 and endpoint_status not in {"ENDPOINT_HTTP_FAILED", None}:
        decision_status = "NYSE_USABILITY_DECISION_CONDITIONALLY_USABLE"
        readiness_score = 80
        nyse_usability_decision = "CONDITIONALLY_USABLE_AFTER_SCHEMA_REVIEW"
        recommended_next_phase = "v2.5H ? NYSE Schema Review"
    elif validation_usability == "REQUIRES_DEEP_JS_PAYLOAD_REVIEW" and js_findings > 0:
        decision_status = "NYSE_USABILITY_DECISION_DEEP_JS_REVIEW_REQUIRED"
        readiness_score = 70
        nyse_usability_decision = "REQUIRES_DEEP_JS_PAYLOAD_REVIEW"
        recommended_next_phase = "v2.5H ? NYSE Deep JS Payload Review"
    elif acquisition_status == "NYSE_PROVIDER_ACQUISITION_RAW_ONLY_REVIEW_REQUIRED":
        decision_status = "NYSE_USABILITY_DECISION_RAW_ONLY_NOT_USABLE_YET"
        readiness_score = 55
        nyse_usability_decision = "RAW_ONLY_NOT_USABLE_YET"
        recommended_next_phase = "v2.6A ? Next Official Provider Route"
    else:
        decision_status = "NYSE_USABILITY_DECISION_DEFERRED"
        readiness_score = 50
        nyse_usability_decision = "DEFERRED"
        recommended_next_phase = "v2.6A ? Next Official Provider Route"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "decision_status": decision_status,
        "readiness_score": readiness_score,
        "nyse_usability_decision": nyse_usability_decision,
        "recommended_next_phase": recommended_next_phase,
        "inputs": {
            "v2_5d_acquisition": {
                "path": rel(ACQUISITION_JSON),
                "exists": acquisition.get("_exists"),
                "acquisition_status": acquisition_status,
                "extracted_rows": extracted_rows,
            },
            "v2_5e_discovery": {
                "path": rel(DISCOVERY_JSON),
                "exists": discovery.get("_exists"),
                "discovery_status": discovery_status,
                "api_candidates": api_candidates,
                "csv_candidates": csv_candidates,
                "javascript_assets": javascript_assets,
            },
            "v2_5f_validation": {
                "path": rel(VALIDATION_JSON),
                "exists": validation.get("_exists"),
                "validation_status": validation_status,
                "usability_decision": validation_usability,
                "endpoint_status": endpoint_status,
                "endpoint_status_code": endpoint_status_code,
                "js_assets_inspected": js_assets_inspected,
                "js_findings": js_findings,
            },
        },
        "source_expansion_state": {
            "current_included_rows": CURRENT_INCLUDED_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "rows_needed_first_expansion": rows_needed_first_expansion,
            "rows_needed_full_source": rows_needed_full_source,
            "full_59000_remains_blocked": True,
            "expanded_universe_rebuild_allowed": False,
        },
        "decision_matrix": {
            "raw_html_downloaded": acquisition.get("_exists") and acquisition_status is not None,
            "normalized_rows_available": extracted_rows > 0,
            "direct_csv_candidate_available": csv_candidates > 0,
            "api_candidate_available": api_candidates > 0,
            "proxy_directly_usable": endpoint_status not in {"ENDPOINT_HTTP_FAILED", None},
            "js_payload_hints_available": js_findings > 0,
            "safe_to_rebuild_expanded_universe": False,
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
            "Do not rebuild expanded_universe from NYSE yet. Continue only with deep JS payload review, or defer NYSE and move to another official provider."
            if not blockers
            else "Resolve blockers before making NYSE usability decision."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.5G NYSE Usability Decision Gate")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Decision status: **{decision_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- NYSE usability decision: **{nyse_usability_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Consolidated evidence")
    md.append("")
    md.append(f"- v2.5D acquisition status: **{acquisition_status}**")
    md.append(f"- v2.5D extracted rows: {extracted_rows}")
    md.append(f"- v2.5E discovery status: **{discovery_status}**")
    md.append(f"- v2.5E API candidates: {api_candidates}")
    md.append(f"- v2.5E CSV candidates: {csv_candidates}")
    md.append(f"- v2.5E JavaScript assets: {javascript_assets}")
    md.append(f"- v2.5F validation status: **{validation_status}**")
    md.append(f"- v2.5F endpoint status: **{endpoint_status}**")
    md.append(f"- v2.5F endpoint status code: {endpoint_status_code}")
    md.append(f"- v2.5F JS assets inspected: {js_assets_inspected}")
    md.append(f"- v2.5F JS findings: {js_findings}")
    md.append("")
    md.append("## Source expansion state")
    md.append("")
    md.append(f"- Current included rows: {CURRENT_INCLUDED_ROWS}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Rows needed for first expansion target: {rows_needed_first_expansion}")
    md.append(f"- Rows needed for full-source threshold: {rows_needed_full_source}")
    md.append("- Full 59k remains blocked: true")
    md.append("- Expanded universe rebuild allowed: false")
    md.append("")
    md.append("## Decision matrix")
    md.append("")
    for key, value in payload["decision_matrix"].items():
        md.append(f"- {key}: {value}")
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
    md.append("Important: v2.5G is a decision gate only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.5G NYSE Usability Decision Gate")
    print("=" * 92)
    print(f"OK   Decision status: {decision_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   NYSE usability decision: {nyse_usability_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Extracted rows: {extracted_rows}")
    print(f"OK   API candidates: {api_candidates}")
    print(f"OK   CSV candidates: {csv_candidates}")
    print(f"OK   Endpoint status: {endpoint_status}")
    print(f"OK   Endpoint status code: {endpoint_status_code}")
    print(f"OK   JS findings: {js_findings}")
    print(f"OK   Rebuild allowed: False")
    print(f"OK   Full 59k remains blocked: True")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
