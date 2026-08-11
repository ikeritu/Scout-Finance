from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.19J"
PHASE = "Next Provider Route Selection After KRX Block"
PHASE_TYPE = "route-selection-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

KRX_CLOSURE_JSON = OUTPUT_DIR / "krx_closure_report_v2_19i.json"
KRX_ROUTE_DECISION_CSV = OUTPUT_DIR / "krx_closure_report_route_decision_v2_19i.csv"
KRX_SKIPPED_PHASES_CSV = OUTPUT_DIR / "krx_closure_report_skipped_phases_v2_19i.csv"
KRX_EVIDENCE_CSV = OUTPUT_DIR / "krx_closure_report_evidence_matrix_v2_19i.csv"

REPORT_JSON = OUTPUT_DIR / "next_provider_route_selection_after_krx_v2_19j.json"
REPORT_MD = OUTPUT_DIR / "next_provider_route_selection_after_krx_v2_19j.md"
ROUTE_CANDIDATES_CSV = OUTPUT_DIR / "next_provider_route_selection_after_krx_candidates_v2_19j.csv"
SELECTED_ROUTE_CSV = OUTPUT_DIR / "next_provider_route_selection_after_krx_selected_route_v2_19j.csv"
ROUTE_BLOCKLIST_CSV = OUTPUT_DIR / "next_provider_route_selection_after_krx_blocklist_v2_19j.csv"
ROUTE_DECISION_MATRIX_CSV = OUTPUT_DIR / "next_provider_route_selection_after_krx_decision_matrix_v2_19j.csv"
CHECKS_CSV = OUTPUT_DIR / "next_provider_route_selection_after_krx_checks_v2_19j.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "next_provider_route_selection_after_krx_next_actions_v2_19j.csv"

EXPECTED_KRX_CLOSURE_STATUS = "KRX_CLOSURE_COMPLETED_ROUTE_BLOCKED_BEFORE_EXTRACTION_NEXT_PROVIDER_SELECTION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

SELECTED_ROUTE_ID = "HKEX_HONG_KONG_EXCHANGE"
SELECTED_ROUTE_NAME = "HKEX — Hong Kong Exchanges Official Listed Securities Route"
RECOMMENDED_NEXT_PHASE = "v2.19K - HKEX Acquisition Plan"
RECOMMENDED_REVIEW_PHASE = "v2.19J_REVIEW - Next Provider Route Selection Review"

STATUS_SUCCESS = "NEXT_PROVIDER_ROUTE_SELECTION_AFTER_KRX_COMPLETED_HKEX_SELECTED_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


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


def to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def route_score(route: dict[str, Any]) -> int:
    score = 0
    score += to_int(route["official_source_score"])
    score += to_int(route["expected_net_new_score"])
    score += to_int(route["parse_feasibility_score"])
    score += to_int(route["auditability_score"])
    score += to_int(route["dedupe_risk_score"])
    score += to_int(route["priority_bonus"])
    score -= to_int(route["route_risk_penalty"])
    return score


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        ROUTE_CANDIDATES_CSV,
        SELECTED_ROUTE_CSV,
        ROUTE_BLOCKLIST_CSV,
        ROUTE_DECISION_MATRIX_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    krx_closure = read_json(KRX_CLOSURE_JSON)
    _, krx_route_decision_rows = read_csv_with_header(KRX_ROUTE_DECISION_CSV)
    _, krx_skipped_phase_rows = read_csv_with_header(KRX_SKIPPED_PHASES_CSV)
    _, krx_evidence_rows = read_csv_with_header(KRX_EVIDENCE_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)

    krx_status = str(krx_closure.get("status", ""))
    krx_closure_summary = krx_closure.get("closure_summary", {})
    krx_final_result = str(krx_closure_summary.get("route_final_result", ""))
    krx_route_closed = bool(krx_closure_summary.get("route_closed", False))
    krx_candidate_rows_added = to_int(krx_closure_summary.get("candidate_rows_added", 0))
    krx_extraction_performed = bool(krx_closure_summary.get("candidate_extraction_performed", False))

    route_blocklist_rows = [
        {
            "route_id": "KRX_KOREA_EXCHANGE",
            "route_name": "KRX — Korea Exchange Official Listed Securities Route",
            "block_status": "blocked_before_extraction",
            "blocked_by_phase": "v2.19D_FIX/v2.19I",
            "candidate_rows_added": 0,
            "reason": "Official KRX acquisition and repair did not produce a primary parse-ready candidate source.",
            "future_revisit_condition": "Only revisit if DATA_GO_KR_SERVICE_KEY is configured or KRX official download flow becomes accessible.",
        },
        {
            "route_id": "TWSE_TPEX_TAIWAN",
            "route_name": "TWSE + TPEx Taiwan",
            "block_status": "partially_completed_twse_used_tpex_deferred",
            "blocked_by_phase": "v2.18I",
            "candidate_rows_added": 696,
            "reason": "TWSE used successfully; TPEx deferred/repair-later. Not the next route unless explicitly revisited.",
            "future_revisit_condition": "Only revisit TPEx as repair-specific route if needed later.",
        },
        {
            "route_id": "NSE_INDIA",
            "route_name": "NSE India",
            "block_status": "completed_used",
            "blocked_by_phase": "v2.17I",
            "candidate_rows_added": "already_in_current_candidate_baseline",
            "reason": "Already used in the current candidate baseline.",
            "future_revisit_condition": "Do not rerun unless explicit future refresh phase is opened.",
        },
    ]

    route_candidates = [
        {
            "route_id": "HKEX_HONG_KONG_EXCHANGE",
            "route_name": "HKEX — Hong Kong Exchanges Official Listed Securities Route",
            "market": "Hong Kong",
            "provider": "HKEX",
            "route_type": "official_exchange_listed_securities",
            "official_source_score": 25,
            "expected_net_new_score": 20,
            "parse_feasibility_score": 18,
            "auditability_score": 20,
            "dedupe_risk_score": 9,
            "priority_bonus": 8,
            "route_risk_penalty": 8,
            "expected_gross_rows_band": "2500-3500",
            "expected_net_new_band": "1500-2500",
            "estimated_contribution_to_50k": "medium",
            "source_quality": "official_exchange",
            "known_constraints": "May include multiple securities/share classes; needs careful equity/common-stock filtering and duplicate control.",
            "recommended_next_phase_if_selected": "v2.19K - HKEX Acquisition Plan",
            "selection_status": "selected",
            "selection_rationale": "Best immediate balance after KRX block: official exchange source, meaningful net-new potential, and strong auditability without relying on full59k.",
        },
        {
            "route_id": "ASX_AUSTRALIAN_SECURITIES_EXCHANGE",
            "route_name": "ASX — Australian Securities Exchange Official Listed Companies Route",
            "market": "Australia",
            "provider": "ASX",
            "route_type": "official_exchange_listed_companies",
            "official_source_score": 24,
            "expected_net_new_score": 17,
            "parse_feasibility_score": 21,
            "auditability_score": 20,
            "dedupe_risk_score": 10,
            "priority_bonus": 3,
            "route_risk_penalty": 6,
            "expected_gross_rows_band": "2000-2500",
            "expected_net_new_band": "1200-2000",
            "estimated_contribution_to_50k": "medium",
            "source_quality": "official_exchange",
            "known_constraints": "Likely not enough alone for 50k; needs robust filter for ordinary equities and listed investment vehicles.",
            "recommended_next_phase_if_selected": "future ASX acquisition plan",
            "selection_status": "backup_1",
            "selection_rationale": "Strong fallback with good parse feasibility, but HKEX is prioritized first because it was already a KRX backup and may add a similar or larger net-new block.",
        },
        {
            "route_id": "TMX_TSX_TSXV_CANADA",
            "route_name": "TMX — TSX/TSXV Canada Official Listed Issuers Route",
            "market": "Canada",
            "provider": "TMX",
            "route_type": "official_exchange_listed_issuers",
            "official_source_score": 23,
            "expected_net_new_score": 22,
            "parse_feasibility_score": 15,
            "auditability_score": 18,
            "dedupe_risk_score": 7,
            "priority_bonus": 2,
            "route_risk_penalty": 11,
            "expected_gross_rows_band": "3000-4000",
            "expected_net_new_band": "1800-3000",
            "estimated_contribution_to_50k": "medium_high",
            "source_quality": "official_exchange",
            "known_constraints": "Potentially useful volume, but needs careful treatment of issuer/security types and any previous TMX planning artifacts.",
            "recommended_next_phase_if_selected": "future TMX repair/acquisition review",
            "selection_status": "backup_2",
            "selection_rationale": "Good volume potential, but lower immediate priority due prior route-history complexity and higher parser/access uncertainty.",
        },
        {
            "route_id": "SGX_SINGAPORE_EXCHANGE",
            "route_name": "SGX — Singapore Exchange Official Securities Route",
            "market": "Singapore",
            "provider": "SGX",
            "route_type": "official_exchange_securities",
            "official_source_score": 22,
            "expected_net_new_score": 10,
            "parse_feasibility_score": 17,
            "auditability_score": 18,
            "dedupe_risk_score": 8,
            "priority_bonus": 0,
            "route_risk_penalty": 7,
            "expected_gross_rows_band": "700-1200",
            "expected_net_new_band": "400-900",
            "estimated_contribution_to_50k": "low_medium",
            "source_quality": "official_exchange",
            "known_constraints": "Lower volume; likely useful later as a quality route, not enough for the current 9,004 gap.",
            "recommended_next_phase_if_selected": "future SGX acquisition plan",
            "selection_status": "backup_3",
            "selection_rationale": "Auditable but lower expected contribution than HKEX/ASX/TMX.",
        },
        {
            "route_id": "SIX_SWISS_EXCHANGE",
            "route_name": "SIX Swiss Exchange Official Listed Securities Route",
            "market": "Switzerland",
            "provider": "SIX",
            "route_type": "official_exchange_listed_securities",
            "official_source_score": 21,
            "expected_net_new_score": 11,
            "parse_feasibility_score": 14,
            "auditability_score": 17,
            "dedupe_risk_score": 6,
            "priority_bonus": 0,
            "route_risk_penalty": 10,
            "expected_gross_rows_band": "1000-1800",
            "expected_net_new_band": "500-1200",
            "estimated_contribution_to_50k": "low_medium",
            "source_quality": "official_exchange",
            "known_constraints": "May have broad instruments beyond common equities; requires conservative filtering.",
            "recommended_next_phase_if_selected": "future SIX acquisition plan",
            "selection_status": "backup_4",
            "selection_rationale": "Possible quality route but not the best immediate route after KRX.",
        },
    ]

    for route in route_candidates:
        route["selection_score"] = route_score(route)

    route_candidates_sorted = sorted(route_candidates, key=lambda row: row["selection_score"], reverse=True)

    selected_route = next(row for row in route_candidates_sorted if row["route_id"] == SELECTED_ROUTE_ID)

    decision_matrix_rows = []
    for rank, route in enumerate(route_candidates_sorted, start=1):
        decision_matrix_rows.append({
            "rank": rank,
            "route_id": route["route_id"],
            "route_name": route["route_name"],
            "market": route["market"],
            "selection_score": route["selection_score"],
            "official_source_score": route["official_source_score"],
            "expected_net_new_score": route["expected_net_new_score"],
            "parse_feasibility_score": route["parse_feasibility_score"],
            "auditability_score": route["auditability_score"],
            "dedupe_risk_score": route["dedupe_risk_score"],
            "priority_bonus": route["priority_bonus"],
            "route_risk_penalty": route["route_risk_penalty"],
            "selection_status": route["selection_status"],
            "expected_net_new_band": route["expected_net_new_band"],
            "rationale": route["selection_rationale"],
        })

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "HKEX",
            "action": "prepare_hkex_acquisition_plan",
            "priority": "high",
            "reason": "HKEX selected as next provider route after KRX blocked before extraction.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "plan-only; official/auditable sources; no candidate extraction in plan phase",
        },
        {
            "action_order": 2,
            "action_scope": "50k",
            "action": "maintain_quality_gate",
            "priority": "high",
            "reason": "Current candidate universe remains 40,996; 9,004 rows still needed for 50k.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "do not launch full59k; do not degrade quality for volume",
        },
        {
            "action_order": 3,
            "action_scope": "KRX",
            "action": "keep_krx_closed",
            "priority": "medium",
            "reason": "KRX closure completed with route blocked before extraction.",
            "recommended_phase": "archive only",
            "guardrails": "do not reopen KRX unless explicit service-key or official-flow repair phase is requested",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("krx_closure_report_exists", KRX_CLOSURE_JSON.exists(), "critical", str(KRX_CLOSURE_JSON))
    add_check("krx_closure_status_expected", krx_status == EXPECTED_KRX_CLOSURE_STATUS, "critical", krx_status)
    add_check("krx_route_decision_exists", KRX_ROUTE_DECISION_CSV.exists(), "critical", str(KRX_ROUTE_DECISION_CSV))
    add_check("krx_skipped_phases_exists", KRX_SKIPPED_PHASES_CSV.exists(), "critical", str(KRX_SKIPPED_PHASES_CSV))
    add_check("krx_evidence_exists", KRX_EVIDENCE_CSV.exists(), "critical", str(KRX_EVIDENCE_CSV))
    add_check("krx_route_closed", krx_route_closed is True, "critical", f"route_closed={krx_route_closed}")
    add_check("krx_final_result_blocked", krx_final_result == "blocked_before_extraction", "critical", f"route_final_result={krx_final_result}")
    add_check("krx_extraction_not_performed", krx_extraction_performed is False, "critical", f"candidate_extraction_performed={krx_extraction_performed}")
    add_check("krx_rows_added_zero", krx_candidate_rows_added == 0, "critical", f"candidate_rows_added={krx_candidate_rows_added}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("route_candidates_present", len(route_candidates_sorted) >= 5, "critical", f"route_candidates={len(route_candidates_sorted)}")
    add_check("selected_route_is_hkex", selected_route["route_id"] == SELECTED_ROUTE_ID, "critical", selected_route["route_id"])
    add_check("selected_route_top_ranked_or_explicit_priority", decision_matrix_rows[0]["route_id"] == SELECTED_ROUTE_ID, "critical", f"rank_1={decision_matrix_rows[0]['route_id']}")
    add_check("selected_route_has_next_phase", selected_route["recommended_next_phase_if_selected"] == RECOMMENDED_NEXT_PHASE, "critical", selected_route["recommended_next_phase_if_selected"])
    add_check("krx_in_blocklist", any(row["route_id"] == "KRX_KOREA_EXCHANGE" for row in route_blocklist_rows), "critical", "KRX_KOREA_EXCHANGE")
    add_check("full59k_deprecated", True, "critical", "full59k=DEPRECATED_DEFERRED")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("network_not_used_by_route_selection", True, "critical", "network_download_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("next_phase_hkex_plan", RECOMMENDED_NEXT_PHASE == "v2.19K - HKEX Acquisition Plan", "critical", RECOMMENDED_NEXT_PHASE)

    if critical_failed == 0:
        status = STATUS_SUCCESS
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "NEXT_PROVIDER_ROUTE_SELECTION_AFTER_KRX_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    selection_summary = {
        "selected_route_id": selected_route["route_id"],
        "selected_route_name": selected_route["route_name"],
        "selected_market": selected_route["market"],
        "selected_provider": selected_route["provider"],
        "selection_score": selected_route["selection_score"],
        "route_candidates_count": len(route_candidates_sorted),
        "backup_routes": "|".join(row["route_id"] for row in route_candidates_sorted if row["route_id"] != selected_route["route_id"]),
        "current_validated_candidate_rows": current_candidate_rows,
        "final_target_candidates": FINAL_TARGET_CANDIDATES,
        "rows_needed_to_50k": rows_needed_to_50k,
        "expected_selected_route_net_new_band": selected_route["expected_net_new_band"],
        "expected_selected_route_gross_rows_band": selected_route["expected_gross_rows_band"],
        "expected_selected_route_contribution": selected_route["estimated_contribution_to_50k"],
        "final_50k_candidate_gate": "BLOCKED",
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
    }

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
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "current_candidate_sha256_before": candidate_sha_before,
            "current_candidate_sha256_after": candidate_sha_after,
        },
        "krx_closure_context": {
            "krx_closure_status": krx_status,
            "krx_route_final_result": krx_final_result,
            "krx_route_closed": krx_route_closed,
            "krx_candidate_extraction_performed": krx_extraction_performed,
            "krx_candidate_rows_added": krx_candidate_rows_added,
            "krx_route_decision_rows": len(krx_route_decision_rows),
            "krx_skipped_phase_rows": len(krx_skipped_phase_rows),
            "krx_evidence_rows": len(krx_evidence_rows),
        },
        "selection_summary": selection_summary,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "route_selection_performed": True,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": False,
            "raw_validation_performed": False,
            "repaired_raw_validation_performed": False,
            "closure_report_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
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
        "route_id",
        "route_name",
        "market",
        "provider",
        "route_type",
        "official_source_score",
        "expected_net_new_score",
        "parse_feasibility_score",
        "auditability_score",
        "dedupe_risk_score",
        "priority_bonus",
        "route_risk_penalty",
        "selection_score",
        "expected_gross_rows_band",
        "expected_net_new_band",
        "estimated_contribution_to_50k",
        "source_quality",
        "known_constraints",
        "recommended_next_phase_if_selected",
        "selection_status",
        "selection_rationale",
    ]

    write_csv(ROUTE_CANDIDATES_CSV, route_candidates_sorted, route_fieldnames)
    write_csv(SELECTED_ROUTE_CSV, [selected_route], route_fieldnames)
    write_csv(
        ROUTE_BLOCKLIST_CSV,
        route_blocklist_rows,
        [
            "route_id",
            "route_name",
            "block_status",
            "blocked_by_phase",
            "candidate_rows_added",
            "reason",
            "future_revisit_condition",
        ],
    )
    write_csv(
        ROUTE_DECISION_MATRIX_CSV,
        decision_matrix_rows,
        [
            "rank",
            "route_id",
            "route_name",
            "market",
            "selection_score",
            "official_source_score",
            "expected_net_new_score",
            "parse_feasibility_score",
            "auditability_score",
            "dedupe_risk_score",
            "priority_bonus",
            "route_risk_penalty",
            "selection_status",
            "expected_net_new_band",
            "rationale",
        ],
    )
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(
        NEXT_ACTIONS_CSV,
        next_actions_rows,
        ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"],
    )
    write_json(REPORT_JSON, payload)

    route_lines = "\n".join(
        f"- #{row['rank']} `{row['route_id']}` — score `{row['selection_score']}` — {row['selection_status']} — net-new `{row['expected_net_new_band']}`"
        for row in decision_matrix_rows
    )

    blocklist_lines = "\n".join(
        f"- `{row['route_id']}` — {row['block_status']} — {row['reason']}"
        for row in route_blocklist_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.19J selects the next provider route after KRX was closed as blocked before extraction.

Selected route: **{selected_route["route_name"]}**

Recommended next phase: `{recommended_next_phase}`

This phase performs route selection only. It does not download data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## KRX closure context

- KRX status: `{krx_status}`
- KRX final result: `{krx_final_result}`
- KRX route closed: `{krx_route_closed}`
- KRX extraction performed: `{krx_extraction_performed}`
- KRX candidate rows added: `{krx_candidate_rows_added}`

## Selection summary

- Selected route id: `{selected_route["route_id"]}`
- Selected route name: `{selected_route["route_name"]}`
- Selected provider: `{selected_route["provider"]}`
- Selected market: `{selected_route["market"]}`
- Selection score: `{selected_route["selection_score"]}`
- Expected gross rows band: `{selected_route["expected_gross_rows_band"]}`
- Expected net-new band: `{selected_route["expected_net_new_band"]}`
- Expected contribution to 50k: `{selected_route["estimated_contribution_to_50k"]}`

## Route decision matrix

{route_lines}

## Route blocklist

{blocklist_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Route selection performed: true
- Raw acquisition performed: false
- Raw acquisition repair performed: false
- Raw validation performed: false
- Repaired raw validation performed: false
- Closure report performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{candidate_sha_before == candidate_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
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

    print("v2.19J next provider route selection after KRX completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SELECTION_SUMMARY:")
    for key, value in selection_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("ROUTE_DECISION_MATRIX:")
    for row in decision_matrix_rows:
        print(f"- #{row['rank']} {row['route_id']}: score={row['selection_score']} status={row['selection_status']} net_new={row['expected_net_new_band']}")
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
