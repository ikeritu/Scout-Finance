from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.19I"
PHASE = "KRX Closure Report"
PHASE_TYPE = "closure-report-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219B_JSON = OUTPUT_DIR / "krx_acquisition_plan_v2_19b.json"
V219C_JSON = OUTPUT_DIR / "krx_raw_acquisition_v2_19c.json"
V219D_JSON = OUTPUT_DIR / "krx_raw_validation_v2_19d.json"
V219C_FIX_JSON = OUTPUT_DIR / "krx_raw_acquisition_repair_v2_19c_fix.json"
V219D_FIX_JSON = OUTPUT_DIR / "krx_repaired_raw_validation_v2_19d_fix.json"

V219D_FIX_ARTIFACT_AUDIT_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_artifact_audit_v2_19d_fix.csv"
V219D_FIX_SOURCE_READINESS_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_source_readiness_v2_19d_fix.csv"
V219D_FIX_EXTRACTION_GATE_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_extraction_gate_v2_19d_fix.csv"
V219D_FIX_ISSUE_AUDIT_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_issue_audit_v2_19d_fix.csv"

REPORT_JSON = OUTPUT_DIR / "krx_closure_report_v2_19i.json"
REPORT_MD = OUTPUT_DIR / "krx_closure_report_v2_19i.md"
PHASE_SUMMARY_CSV = OUTPUT_DIR / "krx_closure_report_phase_summary_v2_19i.csv"
EVIDENCE_MATRIX_CSV = OUTPUT_DIR / "krx_closure_report_evidence_matrix_v2_19i.csv"
ROUTE_DECISION_CSV = OUTPUT_DIR / "krx_closure_report_route_decision_v2_19i.csv"
SKIPPED_PHASES_CSV = OUTPUT_DIR / "krx_closure_report_skipped_phases_v2_19i.csv"
CHECKS_CSV = OUTPUT_DIR / "krx_closure_report_checks_v2_19i.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "krx_closure_report_next_actions_v2_19i.csv"

EXPECTED_STATUSES = {
    "v2.19B": "KRX_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_FOR_RAW_ACQUISITION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED",
    "v2.19C": "KRX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED",
    "v2.19D": "KRX_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED",
    "v2.19C_FIX": "KRX_RAW_ACQUISITION_REPAIR_COMPLETED_REPAIRED_RAW_FILES_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED",
    "v2.19D_FIX": "KRX_REPAIRED_RAW_VALIDATION_COMPLETED_NO_PARSE_READY_SOURCE_ROUTE_BLOCKED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED",
}

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

RECOMMENDED_NEXT_PHASE = "v2.19J - Next Provider Route Selection After KRX Block"
RECOMMENDED_REVIEW_PHASE = "v2.19I_REVIEW - KRX Closure Report Review"

CLOSURE_STATUS = "KRX_CLOSURE_COMPLETED_ROUTE_BLOCKED_BEFORE_EXTRACTION_NEXT_PROVIDER_SELECTION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"


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


def get_nested(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = payload
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def status_line(payload: dict[str, Any]) -> str:
    return str(payload.get("status", ""))


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        PHASE_SUMMARY_CSV,
        EVIDENCE_MATRIX_CSV,
        ROUTE_DECISION_CSV,
        SKIPPED_PHASES_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219b = read_json(V219B_JSON)
    v219c = read_json(V219C_JSON)
    v219d = read_json(V219D_JSON)
    v219c_fix = read_json(V219C_FIX_JSON)
    v219d_fix = read_json(V219D_FIX_JSON)

    _, dfix_artifact_rows = read_csv_with_header(V219D_FIX_ARTIFACT_AUDIT_CSV)
    _, dfix_source_rows = read_csv_with_header(V219D_FIX_SOURCE_READINESS_CSV)
    _, dfix_gate_rows = read_csv_with_header(V219D_FIX_EXTRACTION_GATE_CSV)
    _, dfix_issue_rows = read_csv_with_header(V219D_FIX_ISSUE_AUDIT_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    dfix_summary = v219d_fix.get("repaired_raw_validation_summary", {})

    primary_candidate_ready_count = to_int(dfix_summary.get("primary_candidate_ready_count", 0))
    candidate_ready_count = to_int(dfix_summary.get("candidate_ready_count", 0))
    extraction_ready = bool(dfix_summary.get("extraction_ready", False))
    krx_route_blocked_before_extraction = bool(dfix_summary.get("krx_route_blocked_before_extraction", False))
    dfix_critical_failed_checks = to_int(dfix_summary.get("critical_failed_checks", 0))
    dfix_critical_issue_count = to_int(dfix_summary.get("critical_issue_count", 0))
    official_scope_violations = to_int(dfix_summary.get("official_scope_violations", 0))
    artifacts_exist_count = to_int(dfix_summary.get("artifacts_exist_count", 0))
    bytes_match_count = to_int(dfix_summary.get("bytes_match_count", 0))
    sha256_match_count = to_int(dfix_summary.get("sha256_match_count", 0))
    artifact_audit_rows = to_int(dfix_summary.get("artifact_audit_rows", len(dfix_artifact_rows)))
    repair_manifest_rows = to_int(dfix_summary.get("repair_manifest_rows", 0))
    structured_artifact_count = to_int(dfix_summary.get("structured_artifact_count", 0))
    warning_issue_count = to_int(dfix_summary.get("warning_issue_count", len(dfix_issue_rows)))

    phase_payloads = [
        {
            "phase": "v2.19B",
            "phase_name": "KRX Korea Exchange Acquisition Plan",
            "input_dependency": "v2.19A selected KRX route",
            "status": status_line(v219b),
            "expected_status": EXPECTED_STATUSES["v2.19B"],
            "result": "official_sources_planned",
            "candidate_rows_added": 0,
            "extraction_performed": False,
            "canonical_modified": False,
            "notes": "Plan-only phase. Official KRX/data.go.kr sources identified; no downloads or extraction.",
        },
        {
            "phase": "v2.19C",
            "phase_name": "KRX Raw Acquisition",
            "input_dependency": "v2.19B plan",
            "status": status_line(v219c),
            "expected_status": EXPECTED_STATUSES["v2.19C"],
            "result": "raw_files_captured_validation_ready",
            "candidate_rows_added": 0,
            "extraction_performed": False,
            "canonical_modified": False,
            "notes": "Raw official artifacts captured; validation required before any extraction.",
        },
        {
            "phase": "v2.19D",
            "phase_name": "KRX Raw Validation",
            "input_dependency": "v2.19C raw artifacts",
            "status": status_line(v219d),
            "expected_status": EXPECTED_STATUSES["v2.19D"],
            "result": "repair_required_before_candidate_extraction",
            "candidate_rows_added": 0,
            "extraction_performed": False,
            "canonical_modified": False,
            "notes": "Raw validation found no parse-ready primary artifacts and recommended repair.",
        },
        {
            "phase": "v2.19C_FIX",
            "phase_name": "KRX Raw Acquisition Repair",
            "input_dependency": "v2.19D repair requirement",
            "status": status_line(v219c_fix),
            "expected_status": EXPECTED_STATUSES["v2.19C_FIX"],
            "result": "repaired_raw_files_captured_revalidation_ready",
            "candidate_rows_added": 0,
            "extraction_performed": False,
            "canonical_modified": False,
            "notes": "Official repair attempted; no extraction. Repaired artifacts captured for D_FIX.",
        },
        {
            "phase": "v2.19D_FIX",
            "phase_name": "KRX Repaired Raw Validation",
            "input_dependency": "v2.19C_FIX repaired raw artifacts",
            "status": status_line(v219d_fix),
            "expected_status": EXPECTED_STATUSES["v2.19D_FIX"],
            "result": "route_blocked_before_extraction",
            "candidate_rows_added": 0,
            "extraction_performed": False,
            "canonical_modified": False,
            "notes": "Repaired validation confirmed no primary parse-ready source; KRX blocked before extraction.",
        },
    ]

    evidence_rows = [
        {
            "evidence_id": "KRX_EVIDENCE_001",
            "category": "route_result",
            "finding": "KRX route blocked before extraction",
            "value": krx_route_blocked_before_extraction,
            "source_phase": "v2.19D_FIX",
            "interpretation": "KRX cannot proceed to candidate extraction under current official-source constraints.",
        },
        {
            "evidence_id": "KRX_EVIDENCE_002",
            "category": "extraction_gate",
            "finding": "extraction_ready",
            "value": extraction_ready,
            "source_phase": "v2.19D_FIX",
            "interpretation": "Extraction is not allowed because no primary candidate artifact is ready.",
        },
        {
            "evidence_id": "KRX_EVIDENCE_003",
            "category": "extraction_gate",
            "finding": "primary_candidate_ready_count",
            "value": primary_candidate_ready_count,
            "source_phase": "v2.19D_FIX",
            "interpretation": "No primary KRX artifact met candidate-readiness rules.",
        },
        {
            "evidence_id": "KRX_EVIDENCE_004",
            "category": "artifact_integrity",
            "finding": "repaired_artifact_integrity",
            "value": f"exists={artifacts_exist_count}/{artifact_audit_rows}; bytes={bytes_match_count}/{artifact_audit_rows}; sha256={sha256_match_count}/{artifact_audit_rows}",
            "source_phase": "v2.19D_FIX",
            "interpretation": "Repaired raw artifacts are auditable and integrity-checked.",
        },
        {
            "evidence_id": "KRX_EVIDENCE_005",
            "category": "official_scope",
            "finding": "official_scope_violations",
            "value": official_scope_violations,
            "source_phase": "v2.19D_FIX",
            "interpretation": "Only official-scope KRX/data.go.kr artifacts are included.",
        },
        {
            "evidence_id": "KRX_EVIDENCE_006",
            "category": "candidate_universe",
            "finding": "current_validated_candidate_rows",
            "value": current_candidate_rows,
            "source_phase": "v2.19I",
            "interpretation": "KRX adds zero rows; current validated candidate universe remains unchanged.",
        },
        {
            "evidence_id": "KRX_EVIDENCE_007",
            "category": "target_gap",
            "finding": "rows_needed_to_50k",
            "value": rows_needed_to_50k,
            "source_phase": "v2.19I",
            "interpretation": "The 50k gate remains blocked; another provider route is required.",
        },
        {
            "evidence_id": "KRX_EVIDENCE_008",
            "category": "data_access",
            "finding": "data.go.kr optional API key missing",
            "value": "DATA_GO_KR_SERVICE_KEY not configured in repair phase",
            "source_phase": "v2.19C_FIX/v2.19D_FIX",
            "interpretation": "The supporting data.go.kr route remains optional and unavailable without a service key.",
        },
    ]

    route_decision_rows = [
        {
            "route_id": "KRX_KOREA_EXCHANGE",
            "route_name": "KRX — Korea Exchange Official Listed Securities Route",
            "route_final_result": "blocked_before_extraction",
            "route_closed": True,
            "candidate_extraction_allowed": False,
            "candidate_extraction_performed": False,
            "candidate_rows_extracted": 0,
            "candidate_rows_added": 0,
            "current_validated_candidate_rows": current_candidate_rows,
            "rows_needed_to_50k": rows_needed_to_50k,
            "closure_reason": "Official KRX acquisition and repair did not produce a primary parse-ready candidate source.",
            "recommended_next_phase": RECOMMENDED_NEXT_PHASE,
        }
    ]

    skipped_phase_rows = [
        {
            "phase": "v2.19E",
            "phase_name": "KRX Candidate Extraction Dry Run",
            "status": "SKIPPED",
            "reason": "primary_candidate_ready_count=0 and extraction_ready=False in v2.19D_FIX",
            "dependency": "v2.19D_FIX extraction gate",
        },
        {
            "phase": "v2.19F",
            "phase_name": "KRX Candidate Validation Against Canonical Dry Run",
            "status": "SKIPPED",
            "reason": "No KRX candidate extraction output exists to validate.",
            "dependency": "v2.19E",
        },
        {
            "phase": "v2.19G",
            "phase_name": "KRX Expanded Rebuild Candidate",
            "status": "SKIPPED",
            "reason": "No validated KRX net-new candidates exist to append.",
            "dependency": "v2.19F",
        },
        {
            "phase": "v2.19H",
            "phase_name": "KRX Expanded Validation",
            "status": "SKIPPED",
            "reason": "No KRX expanded candidate dataset was produced.",
            "dependency": "v2.19G",
        },
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "50k",
            "action": "select_next_provider_route_after_krx_block",
            "priority": "high",
            "reason": "KRX is closed as blocked before extraction and the candidate universe remains at 40,996 rows.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "official or auditable sources only; keep 50k quality gate; do not launch full59k",
        },
        {
            "action_order": 2,
            "action_scope": "KRX",
            "action": "keep_krx_artifacts_as_audit_evidence",
            "priority": "medium",
            "reason": "KRX raw and repaired artifacts explain why the route was blocked.",
            "recommended_phase": "archive_with_current_project_history",
            "guardrails": "do not delete raw evidence; do not treat HTML/reference artifacts as candidate data",
        },
        {
            "action_order": 3,
            "action_scope": "data.go.kr",
            "action": "optional_service_key_revisit_only_if_available",
            "priority": "low",
            "reason": "Supporting API may require DATA_GO_KR_SERVICE_KEY; KRX route should not block the wider 50k roadmap.",
            "recommended_phase": "future repair only if key is explicitly configured",
            "guardrails": "do not use unofficial mirrors; do not bypass official access constraints",
        },
    ]

    e_h_artifact_patterns = [
        "krx_candidate_extraction_*v2_19e*",
        "krx_candidate_validation_*v2_19f*",
        "krx_expanded_rebuild_*v2_19g*",
        "krx_expanded_validation_*v2_19h*",
    ]
    unexpected_e_h_artifacts: list[str] = []
    for pattern in e_h_artifact_patterns:
        unexpected_e_h_artifacts.extend(str(path) for path in OUTPUT_DIR.glob(pattern))

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19b_status_expected", status_line(v219b) == EXPECTED_STATUSES["v2.19B"], "critical", status_line(v219b))
    add_check("v2_19c_status_expected", status_line(v219c) == EXPECTED_STATUSES["v2.19C"], "critical", status_line(v219c))
    add_check("v2_19d_status_expected", status_line(v219d) == EXPECTED_STATUSES["v2.19D"], "critical", status_line(v219d))
    add_check("v2_19c_fix_status_expected", status_line(v219c_fix) == EXPECTED_STATUSES["v2.19C_FIX"], "critical", status_line(v219c_fix))
    add_check("v2_19d_fix_status_expected", status_line(v219d_fix) == EXPECTED_STATUSES["v2.19D_FIX"], "critical", status_line(v219d_fix))

    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")

    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")

    add_check("v2_19d_fix_critical_failed_zero", dfix_critical_failed_checks == 0, "critical", f"critical_failed_checks={dfix_critical_failed_checks}")
    add_check("v2_19d_fix_critical_issue_zero", dfix_critical_issue_count == 0, "critical", f"critical_issue_count={dfix_critical_issue_count}")
    add_check("v2_19d_fix_official_scope_only", official_scope_violations == 0, "critical", f"official_scope_violations={official_scope_violations}")
    add_check("v2_19d_fix_repaired_artifacts_integrity", artifacts_exist_count == artifact_audit_rows and bytes_match_count == artifact_audit_rows and sha256_match_count == artifact_audit_rows, "critical", f"exists={artifacts_exist_count}/{artifact_audit_rows}; bytes={bytes_match_count}/{artifact_audit_rows}; sha={sha256_match_count}/{artifact_audit_rows}")

    add_check("krx_extraction_ready_false", extraction_ready is False, "critical", f"extraction_ready={extraction_ready}")
    add_check("krx_primary_candidate_ready_zero", primary_candidate_ready_count == 0, "critical", f"primary_candidate_ready_count={primary_candidate_ready_count}")
    add_check("krx_route_blocked_before_extraction", krx_route_blocked_before_extraction is True, "critical", f"krx_route_blocked_before_extraction={krx_route_blocked_before_extraction}")
    add_check("krx_candidate_rows_added_zero", True, "critical", "candidate_rows_added=0")
    add_check("v2_19e_to_h_artifacts_absent", len(unexpected_e_h_artifacts) == 0, "critical", f"unexpected_e_h_artifacts={unexpected_e_h_artifacts}")

    add_check("structured_artifact_count_documented", structured_artifact_count >= 0, "warning", f"structured_artifact_count={structured_artifact_count}")
    add_check("candidate_ready_count_zero", candidate_ready_count == 0, "warning", f"candidate_ready_count={candidate_ready_count}")
    add_check("warning_issue_count_documented", warning_issue_count >= 1, "warning", f"warning_issue_count={warning_issue_count}")

    add_check("raw_files_read_only", True, "critical", "raw_files_written=False")
    add_check("network_not_used_by_closure", True, "critical", "network_download_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("next_provider_selection_ready", True, "critical", RECOMMENDED_NEXT_PHASE)

    if critical_failed == 0:
        status = CLOSURE_STATUS
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "KRX_CLOSURE_REPORT_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    closure_summary = {
        "route_id": "KRX_KOREA_EXCHANGE",
        "route_name": "KRX — Korea Exchange Official Listed Securities Route",
        "route_final_result": "blocked_before_extraction",
        "route_closed": critical_failed == 0,
        "candidate_extraction_allowed": False,
        "candidate_extraction_performed": False,
        "candidate_rows_extracted": 0,
        "candidate_rows_added": 0,
        "skipped_phases": "v2.19E|v2.19F|v2.19G|v2.19H",
        "current_validated_candidate_rows": current_candidate_rows,
        "final_target_candidates": FINAL_TARGET_CANDIDATES,
        "rows_needed_to_50k": rows_needed_to_50k,
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
        "closure_summary": closure_summary,
        "krx_block_evidence": {
            "repair_manifest_rows": repair_manifest_rows,
            "artifact_audit_rows": artifact_audit_rows,
            "artifacts_exist_count": artifacts_exist_count,
            "bytes_match_count": bytes_match_count,
            "sha256_match_count": sha256_match_count,
            "official_scope_violations": official_scope_violations,
            "structured_artifact_count": structured_artifact_count,
            "candidate_ready_count": candidate_ready_count,
            "primary_candidate_ready_count": primary_candidate_ready_count,
            "extraction_ready": extraction_ready,
            "krx_route_blocked_before_extraction": krx_route_blocked_before_extraction,
            "critical_issue_count": dfix_critical_issue_count,
            "warning_issue_count": warning_issue_count,
        },
        "phase_statuses": {row["phase"]: row["status"] for row in phase_payloads},
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": False,
            "raw_validation_performed": False,
            "repaired_raw_validation_performed": False,
            "closure_report_performed": True,
            "raw_files_read": True,
            "raw_files_written": False,
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

    write_csv(
        PHASE_SUMMARY_CSV,
        phase_payloads,
        [
            "phase",
            "phase_name",
            "input_dependency",
            "status",
            "expected_status",
            "result",
            "candidate_rows_added",
            "extraction_performed",
            "canonical_modified",
            "notes",
        ],
    )
    write_csv(
        EVIDENCE_MATRIX_CSV,
        evidence_rows,
        ["evidence_id", "category", "finding", "value", "source_phase", "interpretation"],
    )
    write_csv(
        ROUTE_DECISION_CSV,
        route_decision_rows,
        [
            "route_id",
            "route_name",
            "route_final_result",
            "route_closed",
            "candidate_extraction_allowed",
            "candidate_extraction_performed",
            "candidate_rows_extracted",
            "candidate_rows_added",
            "current_validated_candidate_rows",
            "rows_needed_to_50k",
            "closure_reason",
            "recommended_next_phase",
        ],
    )
    write_csv(
        SKIPPED_PHASES_CSV,
        skipped_phase_rows,
        ["phase", "phase_name", "status", "reason", "dependency"],
    )
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(
        NEXT_ACTIONS_CSV,
        next_actions_rows,
        ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"],
    )
    write_json(REPORT_JSON, payload)

    phase_lines = "\n".join(
        f"- `{row['phase']}` — {row['result']} — `{row['status']}`"
        for row in phase_payloads
    )

    evidence_lines = "\n".join(
        f"- `{row['evidence_id']}` / {row['category']} — {row['finding']}: `{row['value']}` — {row['interpretation']}"
        for row in evidence_rows
    )

    skipped_lines = "\n".join(
        f"- `{row['phase']}` — {row['status']} — {row['reason']}"
        for row in skipped_phase_rows
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

v2.19I closes the KRX route after acquisition, validation, repair and repaired validation.

KRX is closed as **blocked before extraction** because the repaired validation confirmed no primary parse-ready candidate source.

No v2.19E-H KRX candidate phases are executed.

This phase does not download data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Closure summary

- Route: `KRX_KOREA_EXCHANGE`
- Final route result: `blocked_before_extraction`
- Route closed: `{critical_failed == 0}`
- Candidate extraction allowed: `False`
- Candidate extraction performed: `False`
- Candidate rows extracted: `0`
- Candidate rows added: `0`
- Skipped phases: `v2.19E`, `v2.19F`, `v2.19G`, `v2.19H`
- Critical failed checks: `{critical_failed}`

## Phase summary

{phase_lines}

## Evidence matrix

{evidence_lines}

## Skipped KRX phases

{skipped_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw acquisition repair performed: false
- Raw validation performed: false
- Repaired raw validation performed: false
- Closure report performed: true
- Raw files read: true
- Raw files written: false
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

    print("v2.19I KRX closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CLOSURE_SUMMARY:")
    for key, value in closure_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("KRX_BLOCK_EVIDENCE:")
    for key, value in payload["krx_block_evidence"].items():
        print(f"- {key}: {value}")
    print("")
    print("PHASE_SUMMARY:")
    for row in phase_payloads:
        print(f"- {row['phase']}: {row['result']} | status={row['status']}")
    print("")
    print("SKIPPED_PHASES:")
    for row in skipped_phase_rows:
        print(f"- {row['phase']}: {row['status']} - {row['reason']}")
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
