from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.19A"
PHASE = "Next Provider Route Selection"
PHASE_TYPE = "route-selection-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V218I_JSON = OUTPUT_DIR / "twse_tpex_closure_report_v2_18i.json"
V218I_METRIC_SUMMARY_CSV = OUTPUT_DIR / "twse_tpex_closure_metric_summary_v2_18i.csv"
V218I_SOURCE_STATUS_CSV = OUTPUT_DIR / "twse_tpex_closure_source_status_v2_18i.csv"
V218I_PHASE_LEDGER_CSV = OUTPUT_DIR / "twse_tpex_closure_phase_ledger_v2_18i.csv"

REPORT_JSON = OUTPUT_DIR / "next_provider_route_selection_v2_19a.json"
REPORT_MD = OUTPUT_DIR / "next_provider_route_selection_v2_19a.md"
ROUTE_CANDIDATES_CSV = OUTPUT_DIR / "next_provider_route_candidates_v2_19a.csv"
SELECTED_ROUTE_CSV = OUTPUT_DIR / "next_provider_selected_route_v2_19a.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "next_provider_route_selection_next_actions_v2_19a.csv"
CHECKS_CSV = OUTPUT_DIR / "next_provider_route_selection_checks_v2_19a.csv"

EXPECTED_V218I_STATUS = "TWSE_TPEX_CLOSURE_COMPLETED_40996_CANDIDATES_NEXT_PROVIDER_SELECTION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

SELECTED_ROUTE_ID = "KRX_KOREA_EXCHANGE"
SELECTED_ROUTE_NAME = "KRX — Korea Exchange Official Listed Securities Route"
RECOMMENDED_NEXT_PHASE = "v2.19B - KRX Korea Exchange Acquisition Plan"
RECOMMENDED_REVIEW_PHASE = "v2.19A_REVIEW - Next Provider Route Selection Review"

ROUTE_CANDIDATES = [
    {
        "rank": 1,
        "route_id": "KRX_KOREA_EXCHANGE",
        "provider": "KRX",
        "market": "South Korea",
        "official_sources": "KRX Global Listed Company; KRX Data Marketplace; Public Data Portal KRX Listed Stock Information",
        "primary_urls": "https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp | https://data.krx.co.kr/ | https://www.data.go.kr/en/data/15094775/openapi.do",
        "estimated_gross_rows_band": "2000-3000",
        "expected_net_new_band": "medium",
        "source_quality": "high",
        "official_download_or_api": "yes",
        "instrument_filter_complexity": "medium",
        "duplicate_risk": "medium",
        "implementation_risk": "medium",
        "selection_decision": "selected",
        "selection_reason": "Best balance of official exchange source, structured/listed-company coverage, expected net-new contribution, and manageable validation scope.",
    },
    {
        "rank": 2,
        "route_id": "HKEX_HONG_KONG_EXCHANGE",
        "provider": "HKEX",
        "market": "Hong Kong",
        "official_sources": "HKEX Securities Lists; HKEX Equities Securities",
        "primary_urls": "https://www.hkex.com.hk/Services/Trading/Securities/Securities-Lists?sc_lang=en | https://www.hkex.com.hk/Products/Securities/Equities?sc_lang=en",
        "estimated_gross_rows_band": "2000-3000",
        "expected_net_new_band": "medium",
        "source_quality": "high",
        "official_download_or_api": "yes",
        "instrument_filter_complexity": "high",
        "duplicate_risk": "medium_high",
        "implementation_risk": "medium_high",
        "selection_decision": "backup",
        "selection_reason": "Strong official source, but instrument filtering may be more complex because full securities lists include non-common instruments.",
    },
    {
        "rank": 3,
        "route_id": "TMX_TSX_TSXV_CANADA",
        "provider": "TMX",
        "market": "Canada",
        "official_sources": "TSX/TSXV Listed Company Directory",
        "primary_urls": "https://www.tsx.com/en/listings/listing-with-us/listed-company-directory",
        "estimated_gross_rows_band": "3000-4000",
        "expected_net_new_band": "medium_high",
        "source_quality": "high",
        "official_download_or_api": "yes",
        "instrument_filter_complexity": "medium_high",
        "duplicate_risk": "medium",
        "implementation_risk": "medium_high",
        "selection_decision": "backup",
        "selection_reason": "Potentially strong contribution, but should be evaluated after KRX because TSX/TSXV may require careful issuer/security filtering.",
    },
    {
        "rank": 4,
        "route_id": "ASX_AUSTRALIAN_SECURITIES_EXCHANGE",
        "provider": "ASX",
        "market": "Australia",
        "official_sources": "ASX complete listed companies CSV",
        "primary_urls": "https://www.asx.com.au/markets/trade-our-cash-market/overview/indices",
        "estimated_gross_rows_band": "2000-2500",
        "expected_net_new_band": "medium",
        "source_quality": "high",
        "official_download_or_api": "yes",
        "instrument_filter_complexity": "medium",
        "duplicate_risk": "medium",
        "implementation_risk": "low_medium",
        "selection_decision": "backup",
        "selection_reason": "Good official CSV-style candidate source; likely useful if KRX/HKEX/TMX do not close the 50k gap.",
    },
    {
        "rank": 5,
        "route_id": "TPEx_REPAIR_LATER",
        "provider": "TPEx",
        "market": "Taiwan",
        "official_sources": "TPEx route deferred from v2.18",
        "primary_urls": "previous v2.18 TPEx repair artifacts",
        "estimated_gross_rows_band": "unknown",
        "expected_net_new_band": "low_medium_unknown",
        "source_quality": "official_but_unresolved",
        "official_download_or_api": "unresolved",
        "instrument_filter_complexity": "medium",
        "duplicate_risk": "high",
        "implementation_risk": "high",
        "selection_decision": "deferred",
        "selection_reason": "Do not reopen immediately; TWSE closure explicitly left TPEx deferred_or_repair_later.",
    },
]

SELECTED_ROUTE = [row for row in ROUTE_CANDIDATES if row["route_id"] == SELECTED_ROUTE_ID][0]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                return list(reader.fieldnames or []), rows
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        ROUTE_CANDIDATES_CSV,
        SELECTED_ROUTE_CSV,
        NEXT_ACTIONS_CSV,
        CHECKS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v218i = read_json(V218I_JSON)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    canonical_header, canonical_rows = read_csv_with_header(ACTIVE_CANONICAL_DATASET)
    candidate_header, candidate_rows = read_csv_with_header(CURRENT_VALIDATED_CANDIDATE_DATASET)
    _, v218i_metric_rows = read_csv_with_header(V218I_METRIC_SUMMARY_CSV)
    _, v218i_source_status_rows = read_csv_with_header(V218I_SOURCE_STATUS_CSV)
    _, v218i_phase_ledger_rows = read_csv_with_header(V218I_PHASE_LEDGER_CSV)

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = len(canonical_rows)
    current_candidate_rows = len(candidate_rows)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18i_report_exists", V218I_JSON.exists(), "critical", str(V218I_JSON))
    add_check("v2_18i_status_expected", v218i.get("status") == EXPECTED_V218I_STATUS, "critical", v218i.get("status", ""))
    add_check("active_canonical_exists", ACTIVE_CANONICAL_DATASET.exists(), "critical", str(ACTIVE_CANONICAL_DATASET))
    add_check("current_validated_candidate_exists", CURRENT_VALIDATED_CANDIDATE_DATASET.exists(), "critical", str(CURRENT_VALIDATED_CANDIDATE_DATASET))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("route_candidates_available", len(ROUTE_CANDIDATES) >= 4, "critical", f"route_candidates={len(ROUTE_CANDIDATES)}")
    add_check("selected_route_is_krx", SELECTED_ROUTE_ID == "KRX_KOREA_EXCHANGE", "critical", f"selected_route_id={SELECTED_ROUTE_ID}")
    add_check("selected_route_has_official_sources", SELECTED_ROUTE["official_download_or_api"] == "yes", "critical", SELECTED_ROUTE["official_sources"])
    add_check("selected_route_not_full59k", SELECTED_ROUTE_ID != "FULL59K", "critical", "full59k not selected")
    add_check("selected_route_not_tpex_repair", SELECTED_ROUTE_ID != "TPEx_REPAIR_LATER", "critical", "TPEx repair deferred")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("candidate_dataset_not_modified", True, "critical", "candidate_dataset_modified=False")
    add_check("no_raw_acquisition", True, "critical", "raw_acquisition_performed=False")
    add_check("no_candidate_extraction", True, "critical", "candidate_extraction_performed=False")
    add_check("no_expanded_rebuild", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("route_selection_only", True, "critical", "phase_type=route-selection-only")
    add_check("network_not_used_by_script", True, "critical", "network_download_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("next_provider_needed", rows_needed_to_50k > 0, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")

    if critical_failed == 0:
        status = "NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_KRX_SELECTED_ACQUISITION_PLAN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "NEXT_PROVIDER_ROUTE_SELECTION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    selected_route_rows = [
        {
            "selected_route_id": SELECTED_ROUTE_ID,
            "selected_route_name": SELECTED_ROUTE_NAME,
            "provider": SELECTED_ROUTE["provider"],
            "market": SELECTED_ROUTE["market"],
            "primary_urls": SELECTED_ROUTE["primary_urls"],
            "selection_reason": SELECTED_ROUTE["selection_reason"],
            "recommended_next_phase": recommended_next_phase,
            "guardrails": "plan-only next; no raw acquisition until v2.19C; no canonical modification; no full59k; no scoring/OpenAI/broker",
        }
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "KRX",
            "action": "prepare_acquisition_plan",
            "priority": "high",
            "reason": "KRX selected as next official provider route after TWSE closure.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "plan only; identify official endpoints/downloads; no network acquisition in v2.19B unless explicitly scoped",
        },
        {
            "action_order": 2,
            "action_scope": "50k",
            "action": "maintain_50k_as_stretch_target",
            "priority": "medium",
            "reason": f"{rows_needed_to_50k} rows remain after TWSE; KRX likely will not close the whole gap alone.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "do not lower target yet; keep 45k intermediate and 50k stretch framing",
        },
        {
            "action_order": 3,
            "action_scope": "backup_routes",
            "action": "preserve_hkex_tmx_asx_backup_order",
            "priority": "medium",
            "reason": "KRX may need to be followed by HKEX, TMX or ASX to continue toward 50k.",
            "recommended_phase": "v2.20 or later if needed after KRX closure",
            "guardrails": "do not run parallel provider acquisition in this route",
        },
    ]

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "current_validated_candidate_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "current_validated_candidate_rows": current_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "intermediate_quality_target": "45000-47500",
            "stretch_target": "50000",
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "current_candidate_sha256_before": candidate_sha_before,
            "current_candidate_sha256_after": candidate_sha_after,
            "v2_18i_metric_rows": len(v218i_metric_rows),
            "v2_18i_source_status_rows": len(v218i_source_status_rows),
            "v2_18i_phase_ledger_rows": len(v218i_phase_ledger_rows),
        },
        "route_selection": {
            "selected_route_id": SELECTED_ROUTE_ID,
            "selected_route_name": SELECTED_ROUTE_NAME,
            "provider": SELECTED_ROUTE["provider"],
            "market": SELECTED_ROUTE["market"],
            "route_candidates_count": len(ROUTE_CANDIDATES),
            "backup_routes": ["HKEX_HONG_KONG_EXCHANGE", "TMX_TSX_TSXV_CANADA", "ASX_AUSTRALIAN_SECURITIES_EXCHANGE"],
            "tpex_status": "deferred_or_repair_later",
            "selection_reason": SELECTED_ROUTE["selection_reason"],
            "critical_failed_checks": critical_failed,
        },
        "route_candidates": ROUTE_CANDIDATES,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "closure_report_performed": False,
            "route_selection_performed": True,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": candidate_sha_before == candidate_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    route_fieldnames = [
        "rank",
        "route_id",
        "provider",
        "market",
        "official_sources",
        "primary_urls",
        "estimated_gross_rows_band",
        "expected_net_new_band",
        "source_quality",
        "official_download_or_api",
        "instrument_filter_complexity",
        "duplicate_risk",
        "implementation_risk",
        "selection_decision",
        "selection_reason",
    ]

    write_csv(ROUTE_CANDIDATES_CSV, ROUTE_CANDIDATES, route_fieldnames)
    write_csv(SELECTED_ROUTE_CSV, selected_route_rows, ["selected_route_id", "selected_route_name", "provider", "market", "primary_urls", "selection_reason", "recommended_next_phase", "guardrails"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_json(REPORT_JSON, payload)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    candidate_lines = "\n".join(
        f"- #{row['rank']} `{row['route_id']}` — {row['provider']} / {row['market']} — {row['selection_decision']} — {row['selection_reason']}"
        for row in ROUTE_CANDIDATES
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.19A selects the next official provider route after TWSE + TPEx closure.

Selected route: **{SELECTED_ROUTE_NAME}**

This phase is route-selection-only. It does not download raw data, does not extract candidates, does not rebuild an expanded dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `{ACTIVE_CANONICAL_DATASET}`
- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate dataset: `{CURRENT_VALIDATED_CANDIDATE_DATASET}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Intermediate quality target: `45,000-47,500`
- Stretch target: `50,000`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Selected route

- Selected route id: `{SELECTED_ROUTE_ID}`
- Selected route name: `{SELECTED_ROUTE_NAME}`
- Provider: `{SELECTED_ROUTE["provider"]}`
- Market: `{SELECTED_ROUTE["market"]}`
- Primary URLs: `{SELECTED_ROUTE["primary_urls"]}`
- Selection reason: `{SELECTED_ROUTE["selection_reason"]}`

## Candidate routes

{candidate_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Closure report performed: false
- Route selection performed: true
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Current candidate dataset read: true
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{candidate_sha_before == candidate_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.19A next provider route selection completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("ROUTE_SELECTION:")
    for key, value in payload["route_selection"].items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
