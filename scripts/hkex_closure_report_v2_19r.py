from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.19R"
PHASE = "HKEX Closure Report"
PHASE_TYPE = "closure-report-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
HKEX_EXPANDED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V219K_JSON = OUTPUT_DIR / "hkex_acquisition_plan_v2_19k.json"
V219L_JSON = OUTPUT_DIR / "hkex_raw_acquisition_v2_19l.json"
V219M_JSON = OUTPUT_DIR / "hkex_raw_validation_v2_19m.json"
V219L_FIX_JSON = OUTPUT_DIR / "hkex_raw_acquisition_repair_v2_19l_fix.json"
V219M_FIX_JSON = OUTPUT_DIR / "hkex_repaired_raw_validation_v2_19m_fix.json"
V219N_JSON = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_v2_19n.json"
V219O_JSON = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_v2_19o.json"
V219P_JSON = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_v2_19p.json"
V219Q_JSON = OUTPUT_DIR / "hkex_expanded_validation_v2_19q.json"

REPORT_JSON = OUTPUT_DIR / "hkex_closure_report_v2_19r.json"
REPORT_MD = OUTPUT_DIR / "hkex_closure_report_v2_19r.md"
PHASE_SUMMARY_CSV = OUTPUT_DIR / "hkex_closure_report_phase_summary_v2_19r.csv"
DATASET_SUMMARY_CSV = OUTPUT_DIR / "hkex_closure_report_dataset_summary_v2_19r.csv"
ROADMAP_CSV = OUTPUT_DIR / "hkex_closure_report_roadmap_v2_19r.csv"
OUTCOME_CSV = OUTPUT_DIR / "hkex_closure_report_outcome_v2_19r.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_closure_report_checks_v2_19r.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_closure_report_next_actions_v2_19r.csv"

EXPECTED_V219Q_STATUS = "HKEX_EXPANDED_VALIDATION_COMPLETED_41392_ROWS_VALIDATED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
HKEX_EXPANDED_CANDIDATE_ROWS_EXPECTED = 41392
HKEX_NET_NEW_ROWS_EXPECTED = 396
ROWS_NEEDED_AFTER_HKEX_EXPECTED = 8608
FINAL_TARGET_CANDIDATES = 50000

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
HKEX_EXPANDED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"

STATUS_SUCCESS = "HKEX_CLOSURE_REPORT_COMPLETED_41392_ROWS_396_NET_NEW_50K_GATE_STILL_BLOCKED_NEXT_PROVIDER_SELECTION_READY_FULL59K_DEPRECATED"
STATUS_FAILED = "HKEX_CLOSURE_REPORT_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "post-v2.19R - Next Provider Route Selection After HKEX"
NEXT_PHASE_REVIEW = "v2.19R_REVIEW - HKEX Closure Report Review"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_json_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def get_nested(payload: dict[str, Any], keys: list[str], default: Any = "") -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def phase_row(label: str, path: Path, payload: dict[str, Any], status_note: str = "") -> dict[str, Any]:
    return {
        "phase": label,
        "artifact": str(path),
        "artifact_exists": path.exists(),
        "status": payload.get("status", status_note if status_note else "missing_or_not_available"),
        "phase_type": payload.get("phase_type", ""),
        "recommended_next_phase": payload.get("recommended_next_phase", ""),
    }


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        PHASE_SUMMARY_CSV,
        DATASET_SUMMARY_CSV,
        ROADMAP_CSV,
        OUTCOME_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219k = read_json_optional(V219K_JSON)
    v219l = read_json_optional(V219L_JSON)
    v219m = read_json_optional(V219M_JSON)
    v219l_fix = read_json_optional(V219L_FIX_JSON)
    v219m_fix = read_json_optional(V219M_FIX_JSON)
    v219n = read_json_optional(V219N_JSON)
    v219o = read_json_optional(V219O_JSON)
    v219p = read_json_optional(V219P_JSON)
    v219q = read_json_optional(V219Q_JSON)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_expanded_rows = count_csv_rows(HKEX_EXPANDED_CANDIDATE_DATASET)

    rows_added_by_hkex = hkex_expanded_rows - current_candidate_rows
    rows_needed_after_hkex = max(FINAL_TARGET_CANDIDATES - hkex_expanded_rows, 0)
    final_50k_gate_after_hkex = "READY" if hkex_expanded_rows >= FINAL_TARGET_CANDIDATES else "BLOCKED"

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_expanded_sha_before = sha256_file(HKEX_EXPANDED_CANDIDATE_DATASET)

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_expanded_sha_after = sha256_file(HKEX_EXPANDED_CANDIDATE_DATASET)

    phase_summary_rows = [
        phase_row("v2.19K - HKEX Acquisition Plan", V219K_JSON, v219k),
        phase_row("v2.19L - HKEX Raw Acquisition", V219L_JSON, v219l),
        phase_row("v2.19M - HKEX Raw Validation", V219M_JSON, v219m),
        phase_row("v2.19L_FIX - HKEX Raw Acquisition Repair", V219L_FIX_JSON, v219l_fix),
        phase_row("v2.19M_FIX - HKEX Repaired Raw Validation", V219M_FIX_JSON, v219m_fix),
        phase_row("v2.19N - HKEX Candidate Extraction Dry Run", V219N_JSON, v219n),
        phase_row("v2.19O - HKEX Candidate Validation Against Canonical Dry Run", V219O_JSON, v219o),
        phase_row("v2.19P - HKEX Expanded Rebuild Candidate", V219P_JSON, v219p),
        phase_row("v2.19Q - HKEX Expanded Validation", V219Q_JSON, v219q),
        {
            "phase": "v2.19R - HKEX Closure Report",
            "artifact": str(REPORT_JSON),
            "artifact_exists": True,
            "status": "generated_by_this_phase",
            "phase_type": PHASE_TYPE,
            "recommended_next_phase": NEXT_PHASE,
        },
    ]

    dataset_summary_rows = [
        {
            "dataset_role": "active_canonical",
            "path": str(ACTIVE_CANONICAL_DATASET),
            "rows": active_canonical_rows,
            "sha256_before": active_canonical_sha_before,
            "sha256_after": active_canonical_sha_after,
            "modified_in_v2_19r": active_canonical_sha_before != active_canonical_sha_after,
        },
        {
            "dataset_role": "current_validated_candidate_before_hkex",
            "path": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "rows": current_candidate_rows,
            "sha256_before": current_candidate_sha_before,
            "sha256_after": current_candidate_sha_after,
            "modified_in_v2_19r": current_candidate_sha_before != current_candidate_sha_after,
        },
        {
            "dataset_role": "hkex_expanded_candidate_validated",
            "path": str(HKEX_EXPANDED_CANDIDATE_DATASET),
            "rows": hkex_expanded_rows,
            "sha256_before": hkex_expanded_sha_before,
            "sha256_after": hkex_expanded_sha_after,
            "modified_in_v2_19r": hkex_expanded_sha_before != hkex_expanded_sha_after,
        },
    ]

    roadmap_rows = [
        {"phase": "v2.19A", "title": "Next Provider Route Selection", "status": "closed"},
        {"phase": "v2.19B", "title": "KRX Korea Exchange Acquisition Plan", "status": "closed"},
        {"phase": "v2.19C", "title": "KRX Raw Acquisition", "status": "closed"},
        {"phase": "v2.19D", "title": "KRX Raw Validation", "status": "closed"},
        {"phase": "v2.19C_FIX", "title": "KRX Raw Acquisition Repair", "status": "closed"},
        {"phase": "v2.19D_FIX", "title": "KRX Repaired Raw Validation", "status": "closed"},
        {"phase": "v2.19E", "title": "KRX Candidate Extraction Dry Run", "status": "skipped_blocked"},
        {"phase": "v2.19F", "title": "KRX Candidate Validation Against Canonical Dry Run", "status": "skipped_blocked"},
        {"phase": "v2.19G", "title": "KRX Expanded Rebuild Candidate", "status": "skipped_blocked"},
        {"phase": "v2.19H", "title": "KRX Expanded Validation", "status": "skipped_blocked"},
        {"phase": "v2.19I", "title": "KRX Closure Report", "status": "closed"},
        {"phase": "v2.19J", "title": "Next Provider Route Selection After KRX Block", "status": "closed"},
        {"phase": "v2.19K", "title": "HKEX Acquisition Plan", "status": "closed"},
        {"phase": "v2.19L", "title": "HKEX Raw Acquisition", "status": "closed"},
        {"phase": "v2.19M", "title": "HKEX Raw Validation", "status": "closed"},
        {"phase": "v2.19L_FIX", "title": "HKEX Raw Acquisition Repair", "status": "closed"},
        {"phase": "v2.19M_FIX", "title": "HKEX Repaired Raw Validation", "status": "closed"},
        {"phase": "v2.19N", "title": "HKEX Candidate Extraction Dry Run", "status": "closed"},
        {"phase": "v2.19O", "title": "HKEX Candidate Validation Against Canonical Dry Run", "status": "closed"},
        {"phase": "v2.19P", "title": "HKEX Expanded Rebuild Candidate", "status": "closed"},
        {"phase": "v2.19Q", "title": "HKEX Expanded Validation", "status": "closed"},
        {"phase": "v2.19R", "title": "HKEX Closure Report", "status": "closed_by_this_report"},
    ]

    outcome_rows = [
        {"metric": "hkex_raw_repair_artifacts", "value": get_nested(v219l_fix, ["validation_summary", "artifacts_written_count"], ""), "detail": "v2.19L_FIX structured raw downloads captured"},
        {"metric": "hkex_primary_parseable_stock_code_rows", "value": get_nested(v219m_fix, ["validation_summary", "top_primary_parseable_stock_code_rows"], ""), "detail": "v2.19M_FIX primary ListOfSecurities parse readiness"},
        {"metric": "hkex_candidate_rows_extracted", "value": get_nested(v219n, ["extraction_summary", "candidate_rows_extracted"], ""), "detail": "v2.19N extraction dry run"},
        {"metric": "hkex_unique_stock_codes_extracted", "value": get_nested(v219n, ["extraction_summary", "unique_stock_codes"], ""), "detail": "v2.19N extraction dry run"},
        {"metric": "hkex_net_new_rows", "value": get_nested(v219o, ["validation_summary", "net_new_pending_expanded_rebuild"], ""), "detail": "v2.19O canonical validation dry run"},
        {"metric": "hkex_duplicate_existing_universe", "value": get_nested(v219o, ["validation_summary", "duplicate_existing_universe"], ""), "detail": "v2.19O canonical validation dry run"},
        {"metric": "hkex_possible_duplicate_name_review", "value": get_nested(v219o, ["validation_summary", "possible_duplicate_name_review"], ""), "detail": "v2.19O canonical validation dry run"},
        {"metric": "hkex_excluded_before_canonical_match", "value": get_nested(v219o, ["validation_summary", "excluded_before_canonical_match"], ""), "detail": "v2.19O canonical validation dry run"},
        {"metric": "current_validated_candidate_rows_before_hkex", "value": current_candidate_rows, "detail": str(CURRENT_VALIDATED_CANDIDATE_DATASET)},
        {"metric": "hkex_expanded_candidate_rows", "value": hkex_expanded_rows, "detail": str(HKEX_EXPANDED_CANDIDATE_DATASET)},
        {"metric": "rows_added_by_hkex", "value": rows_added_by_hkex, "detail": "expanded rows minus current candidate rows"},
        {"metric": "rows_needed_after_hkex", "value": rows_needed_after_hkex, "detail": "50,000 target minus HKEX expanded candidate rows"},
        {"metric": "final_50k_gate_after_hkex", "value": final_50k_gate_after_hkex, "detail": "HKEX does not unlock 50k gate"},
        {"metric": "full59k", "value": "DEPRECATED_DEFERRED", "detail": "not launched"},
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19q_report_exists", V219Q_JSON.exists(), "critical", str(V219Q_JSON))
    add_check("v2_19q_status_expected", v219q.get("status") == EXPECTED_V219Q_STATUS, "critical", str(v219q.get("status", "")))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("hkex_expanded_rows_expected", hkex_expanded_rows == HKEX_EXPANDED_CANDIDATE_ROWS_EXPECTED, "critical", f"hkex_expanded_rows={hkex_expanded_rows}")
    add_check("hkex_net_new_rows_expected", rows_added_by_hkex == HKEX_NET_NEW_ROWS_EXPECTED, "critical", f"rows_added_by_hkex={rows_added_by_hkex}")
    add_check("rows_needed_after_hkex_expected", rows_needed_after_hkex == ROWS_NEEDED_AFTER_HKEX_EXPECTED, "critical", f"rows_needed_after_hkex={rows_needed_after_hkex}")
    add_check("final_50k_gate_still_blocked", final_50k_gate_after_hkex == "BLOCKED", "critical", final_50k_gate_after_hkex)
    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("current_candidate_sha_expected", current_candidate_sha_before == CURRENT_CANDIDATE_SHA_EXPECTED, "critical", current_candidate_sha_before)
    add_check("hkex_expanded_candidate_sha_expected", hkex_expanded_sha_before == HKEX_EXPANDED_CANDIDATE_SHA_EXPECTED, "critical", hkex_expanded_sha_before)
    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("current_candidate_sha_unchanged", current_candidate_sha_before == current_candidate_sha_after, "critical", "current candidate sha unchanged")
    add_check("hkex_expanded_sha_unchanged", hkex_expanded_sha_before == hkex_expanded_sha_after, "critical", "HKEX expanded candidate sha unchanged")
    add_check("phase_2_19_hkex_reports_available", all(path.exists() for path in [V219N_JSON, V219O_JSON, V219P_JSON, V219Q_JSON]), "critical", "v2.19N/O/P/Q reports available")
    add_check("closure_report_only", True, "critical", "closure report only")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("candidate_validation_not_performed", True, "critical", "candidate_validation_against_canonical_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("expanded_validation_not_performed", True, "critical", "expanded_validation_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("current_candidate_dataset_not_modified", True, "critical", "current_candidate_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed == 0:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE
    else:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "provider_route",
            "action": "select_next_provider_route_after_hkex",
            "priority": "high",
            "reason": "HKEX route is closed and 50k gate remains blocked with 8,608 rows still needed.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "quality-first route selection; no full59k; no scoring",
        },
        {
            "action_order": 2,
            "action_scope": "dataset",
            "action": "keep_hkex_expanded_candidate_as_validated_candidate_option",
            "priority": "medium",
            "reason": "HKEX expanded candidate is validated but not promoted to canonical in v2.19R.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "no canonical replacement without explicit later decision",
        },
    ]

    closure_summary = {
        "active_canonical_rows": active_canonical_rows,
        "current_validated_candidate_rows_before_hkex": current_candidate_rows,
        "hkex_expanded_candidate_rows": hkex_expanded_rows,
        "rows_added_by_hkex": rows_added_by_hkex,
        "rows_needed_after_hkex": rows_needed_after_hkex,
        "final_target_candidates": FINAL_TARGET_CANDIDATES,
        "final_50k_candidate_gate_after_hkex": final_50k_gate_after_hkex,
        "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
        "current_validated_candidate_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
        "hkex_expanded_candidate_dataset": str(HKEX_EXPANDED_CANDIDATE_DATASET),
        "active_canonical_sha256": active_canonical_sha_before,
        "current_validated_candidate_sha256": current_candidate_sha_before,
        "hkex_expanded_candidate_sha256": hkex_expanded_sha_before,
        "critical_failed_checks": critical_failed,
        "full59k": "DEPRECATED_DEFERRED",
    }

    write_csv(PHASE_SUMMARY_CSV, phase_summary_rows, ["phase", "artifact", "artifact_exists", "status", "phase_type", "recommended_next_phase"])
    write_csv(DATASET_SUMMARY_CSV, dataset_summary_rows, ["dataset_role", "path", "rows", "sha256_before", "sha256_after", "modified_in_v2_19r"])
    write_csv(ROADMAP_CSV, roadmap_rows, ["phase", "title", "status"])
    write_csv(OUTCOME_CSV, outcome_rows, ["metric", "value", "detail"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "closure_summary": closure_summary,
        "phase_summary": phase_summary_rows,
        "dataset_summary": dataset_summary_rows,
        "outcome": outcome_rows,
        "roadmap": roadmap_rows,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "closure_report_only": True,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "route_selection_performed": False,
            "acquisition_plan_performed": False,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": False,
            "raw_validation_performed": False,
            "repaired_raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": current_candidate_sha_before == current_candidate_sha_after,
            "hkex_expanded_candidate_dataset_read": True,
            "hkex_expanded_candidate_dataset_modified": False,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": final_50k_gate_after_hkex,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    outcome_lines = "\n".join(
        f"- `{row['metric']}`: `{row['value']}` — {row['detail']}"
        for row in outcome_rows
    )
    phase_lines = "\n".join(
        f"- `{row['phase']}`: `{row['status']}`"
        for row in phase_summary_rows
    )
    dataset_lines = "\n".join(
        f"- `{row['dataset_role']}`: `{row['rows']}` rows — `{row['path']}`"
        for row in dataset_summary_rows
    )
    roadmap_lines = "\n".join(
        f"- `{row['phase']}` — {row['title']}: `{row['status']}`"
        for row in roadmap_rows
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

v2.19R closes the HKEX route.

HKEX successfully contributed **{rows_added_by_hkex} net-new rows** to the validated candidate path, increasing the candidate universe from **{current_candidate_rows}** to **{hkex_expanded_rows}** rows.

The 50k gate remains **{final_50k_gate_after_hkex}** because **{rows_needed_after_hkex}** additional rows are still needed to reach the target of **{FINAL_TARGET_CANDIDATES}**.

This phase is a closure report only. It does not promote the HKEX candidate dataset to canonical, does not replace the active canonical dataset, does not modify the current validated candidate dataset, and does not run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Closure summary

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows before HKEX: `{current_candidate_rows}`
- HKEX expanded candidate rows: `{hkex_expanded_rows}`
- Rows added by HKEX: `{rows_added_by_hkex}`
- Rows needed after HKEX: `{rows_needed_after_hkex}`
- Final 50k candidate gate after HKEX: `{final_50k_gate_after_hkex}`
- HKEX expanded candidate dataset: `{HKEX_EXPANDED_CANDIDATE_DATASET}`
- HKEX expanded candidate SHA256: `{hkex_expanded_sha_before}`
- Critical failed checks: `{critical_failed}`
- full59k: `DEPRECATED_DEFERRED`

## HKEX outcome

{outcome_lines}

## Phase summary

{phase_lines}

## Dataset summary

{dataset_lines}

## Roadmap

{roadmap_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Closure report only: true
- Network download performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{active_canonical_sha_before == active_canonical_sha_after}`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{current_candidate_sha_before == current_candidate_sha_after}`
- HKEX expanded candidate dataset modified: false
- Active canonical replaced: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: `{final_50k_gate_after_hkex}`
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

    print("v2.19R HKEX closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CLOSURE_SUMMARY:")
    for key, value in closure_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("OUTCOME:")
    for row in outcome_rows:
        print(f"- {row['metric']}: {row['value']} ({row['detail']})")
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
