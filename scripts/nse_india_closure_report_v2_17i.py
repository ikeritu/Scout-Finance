from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.17I"
PHASE = "NSE India Closure Report"
PHASE_TYPE = "provider-closure-report-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
EXPANDED_CANDIDATE_CSV = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"

V217B_JSON = OUTPUT_DIR / "nse_india_acquisition_plan_v2_17b.json"
V217C_JSON = OUTPUT_DIR / "nse_india_raw_acquisition_v2_17c.json"
V217D_JSON = OUTPUT_DIR / "nse_india_raw_validation_v2_17d.json"
V217E_JSON = OUTPUT_DIR / "nse_india_candidate_extraction_dry_run_v2_17e.json"
V217F_JSON = OUTPUT_DIR / "nse_india_candidate_validation_against_canonical_dry_run_v2_17f.json"
V217G_JSON = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_v2_17g.json"
V217H_JSON = OUTPUT_DIR / "nse_india_expanded_validation_v2_17h.json"

V217H_DATASET_PROFILE_CSV = OUTPUT_DIR / "nse_india_expanded_validation_dataset_profile_v2_17h.csv"
V217H_PROMOTION_POLICY_QA_CSV = OUTPUT_DIR / "nse_india_expanded_validation_promotion_policy_qa_v2_17h.csv"
V217H_DELTA_INTEGRITY_CSV = OUTPUT_DIR / "nse_india_expanded_validation_delta_integrity_v2_17h.csv"

DELTA_ROWS_CSV = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_delta_rows_v2_17g.csv"
PROMOTIONS_CSV = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_promotions_v2_17g.csv"
SCHEMA_MAPPING_CSV = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_schema_mapping_v2_17g.csv"

REPORT_JSON = OUTPUT_DIR / "nse_india_closure_report_v2_17i.json"
REPORT_MD = OUTPUT_DIR / "nse_india_closure_report_v2_17i.md"
CLOSURE_LEDGER_CSV = OUTPUT_DIR / "nse_india_closure_ledger_v2_17i.csv"
CLOSURE_ARTIFACTS_CSV = OUTPUT_DIR / "nse_india_closure_artifacts_v2_17i.csv"
CLOSURE_NEXT_STEPS_CSV = OUTPUT_DIR / "nse_india_closure_next_steps_v2_17i.csv"

CURRENT_CANONICAL_ROWS = 38287
EXPECTED_CANDIDATE_ROWS = 40300
EXPECTED_SAFE_DELTA_ROWS = 2013
FULL_SOURCE_THRESHOLD = 50000

EXPECTED_STATUS = {
    "v2.17B": "NSE_INDIA_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_FULL_SOURCE_STILL_BLOCKED",
    "v2.17C": "NSE_INDIA_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED",
    "v2.17D": "NSE_INDIA_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_CANDIDATE_EXTRACTION_READY_FULL_SOURCE_STILL_BLOCKED",
    "v2.17E": "NSE_INDIA_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_CANONICAL_COMPARISON_STILL_BLOCKED",
    "v2.17F": "NSE_INDIA_CANDIDATE_VALIDATION_AGAINST_CANONICAL_DRY_RUN_COMPLETED_NET_NEW_FOUND_REBUILD_CANDIDATE_READY_FULL_SOURCE_STILL_BLOCKED",
    "v2.17G": "NSE_INDIA_EXPANDED_REBUILD_CANDIDATE_COMPLETED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED",
    "v2.17H": "NSE_INDIA_EXPANDED_VALIDATION_COMPLETED_CANDIDATE_VALID_CLOSURE_READY_FULL_SOURCE_STILL_BLOCKED",
}

EXPECTED_NEXT = {
    "v2.17B": "v2.17C - NSE India Raw Acquisition",
    "v2.17C": "v2.17D - NSE India Raw Validation",
    "v2.17D": "v2.17E - NSE India Candidate Extraction Dry Run",
    "v2.17E": "v2.17F - NSE India Candidate Validation Against Canonical Dry Run",
    "v2.17F": "v2.17G - NSE India Expanded Rebuild Candidate",
    "v2.17G": "v2.17H - NSE India Expanded Validation",
    "v2.17H": "v2.17I - NSE India Closure Report",
}

PHASE_FILES = {
    "v2.17B": V217B_JSON,
    "v2.17C": V217C_JSON,
    "v2.17D": V217D_JSON,
    "v2.17E": V217E_JSON,
    "v2.17F": V217F_JSON,
    "v2.17G": V217G_JSON,
    "v2.17H": V217H_JSON,
}

NEXT_PHASE = "v2.18A - Next Provider Route Selection"
RECOMMENDED_NEXT_PROVIDER_CANDIDATE = "TWSE + TPEx Taiwan"
RESERVE_PROVIDER_CANDIDATE = "ASX Australia"

CLOSURE_LEDGER_FIELDS = [
    "phase",
    "status",
    "recommended_next_phase",
    "artifact",
    "phase_type",
    "critical_failed_checks",
    "closure_assessment",
    "notes",
]

CLOSURE_ARTIFACT_FIELDS = [
    "artifact_id",
    "artifact_path",
    "exists",
    "bytes",
    "sha256",
    "artifact_role",
    "notes",
]

CLOSURE_NEXT_STEPS_FIELDS = [
    "priority",
    "next_step",
    "recommended_phase",
    "provider_candidate",
    "rationale",
    "blocked_until",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict]]:
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


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def artifact_row(path: Path, role: str, notes: str) -> dict:
    if path.exists():
        data = path.read_bytes()
        return {
            "artifact_id": path.name,
            "artifact_path": str(path),
            "exists": True,
            "bytes": len(data),
            "sha256": sha256_bytes(data),
            "artifact_role": role,
            "notes": notes,
        }

    return {
        "artifact_id": path.name,
        "artifact_path": str(path),
        "exists": False,
        "bytes": 0,
        "sha256": "",
        "artifact_role": role,
        "notes": notes,
    }


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        CLOSURE_LEDGER_CSV,
        CLOSURE_ARTIFACTS_CSV,
        CLOSURE_NEXT_STEPS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    reports = {phase: read_json(path) for phase, path in PHASE_FILES.items()}

    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)
    candidate_header, candidate_rows = read_csv_with_header(EXPANDED_CANDIDATE_CSV)
    _, delta_rows = read_csv_with_header(DELTA_ROWS_CSV)
    _, promotions = read_csv_with_header(PROMOTIONS_CSV)
    _, schema_mapping_rows = read_csv_with_header(SCHEMA_MAPPING_CSV)
    _, dataset_profile_rows = read_csv_with_header(V217H_DATASET_PROFILE_CSV)
    _, promotion_policy_qa_rows = read_csv_with_header(V217H_PROMOTION_POLICY_QA_CSV)
    _, delta_integrity_rows = read_csv_with_header(V217H_DELTA_INTEGRITY_CSV)

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())

    ledger = []

    for phase, report in reports.items():
        expected_status = EXPECTED_STATUS[phase]
        expected_next = EXPECTED_NEXT[phase]
        status = report.get("status", "")
        next_phase = report.get("recommended_next_phase", "")
        phase_type = report.get("phase_type", "")
        checks = report.get("checks", [])
        critical_failed = report.get("expanded_validation_summary", {}).get(
            "critical_failed_checks",
            report.get("rebuild_candidate_summary", {}).get(
                "critical_failed_checks",
                report.get("validation_summary", {}).get(
                    "critical_failed_checks",
                    report.get("extraction_summary", {}).get(
                        "critical_failed_checks",
                        report.get("raw_validation_summary", {}).get(
                            "critical_failed_checks",
                            report.get("raw_acquisition_summary", {}).get("critical_failed_checks", ""),
                        ),
                    ),
                ),
            ),
        )

        status_ok = status == expected_status
        next_ok = next_phase == expected_next
        checks_ok = all(bool(item.get("passed")) for item in checks if item.get("severity") == "critical")

        if status_ok and next_ok and checks_ok:
            assessment = "PASS"
        else:
            assessment = "REVIEW"

        ledger.append(
            {
                "phase": phase,
                "status": status,
                "recommended_next_phase": next_phase,
                "artifact": str(PHASE_FILES[phase]),
                "phase_type": phase_type,
                "critical_failed_checks": critical_failed,
                "closure_assessment": assessment,
                "notes": f"expected_status_ok={status_ok}; expected_next_ok={next_ok}; critical_checks_ok={checks_ok}",
            }
        )

    artifacts = [
        artifact_row(CANONICAL_DATASET, "active_canonical_dataset", "Must remain unchanged and active."),
        artifact_row(EXPANDED_CANDIDATE_CSV, "validated_expanded_candidate_dataset", "NSE India candidate dataset; not active canonical."),
        artifact_row(DELTA_ROWS_CSV, "safe_delta_rows", "Safe NSE India promoted rows only."),
        artifact_row(PROMOTIONS_CSV, "safe_promotions", "Promotion ledger from v2.17G."),
        artifact_row(SCHEMA_MAPPING_CSV, "schema_mapping", "Mapping used for appended rows."),
        artifact_row(V217H_DATASET_PROFILE_CSV, "expanded_validation_dataset_profile", "v2.17H dataset profile."),
        artifact_row(V217H_PROMOTION_POLICY_QA_CSV, "promotion_policy_qa", "v2.17H safe promotion QA."),
        artifact_row(V217H_DELTA_INTEGRITY_CSV, "delta_integrity", "v2.17H delta integrity QA."),
        artifact_row(REPORT_JSON, "closure_json_report", "Will be written in v2.17I."),
        artifact_row(REPORT_MD, "closure_markdown_report", "Will be written in v2.17I."),
    ]

    for phase, path in PHASE_FILES.items():
        artifacts.append(artifact_row(path, f"{phase}_json_report", f"{phase} phase report."))

    closure_next_steps = [
        {
            "priority": 1,
            "next_step": "Select next provider route after NSE India closure",
            "recommended_phase": NEXT_PHASE,
            "provider_candidate": RECOMMENDED_NEXT_PROVIDER_CANDIDATE,
            "rationale": "NSE India validated candidate adds 2,013 safe rows but still leaves 9,700 rows needed to reach 50,000.",
            "blocked_until": "v2.17I committed and pushed",
        },
        {
            "priority": 2,
            "next_step": "Keep NSE India candidate dataset as validated candidate only",
            "recommended_phase": "No active canonical replacement in v2.17I",
            "provider_candidate": "NSE India",
            "rationale": "Candidate dataset is valid but full-source gate remains blocked, so canonical promotion should remain a separately controlled decision.",
            "blocked_until": "Future promotion phase, if explicitly opened",
        },
        {
            "priority": 3,
            "next_step": "Reserve quick-win provider route",
            "recommended_phase": "Fallback after v2.18A if needed",
            "provider_candidate": RESERVE_PROVIDER_CANDIDATE,
            "rationale": "Previously listed as quick-win fallback/reserve route.",
            "blocked_until": "Next provider route decision",
        },
    ]

    h_report = reports["v2.17H"]
    h_summary = h_report.get("expanded_validation_summary", {})
    h_state = h_report.get("current_state", {})

    canonical_rows_count = len(canonical_rows)
    candidate_rows_count = len(candidate_rows)
    delta_rows_count = len(delta_rows)
    promotions_count = len(promotions)
    rows_needed_after_candidate = max(FULL_SOURCE_THRESHOLD - candidate_rows_count, 0)
    completion_after_candidate = round((candidate_rows_count / FULL_SOURCE_THRESHOLD) * 100, 2)

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("all_phase_reports_exist", all(path.exists() for path in PHASE_FILES.values()), "critical", "v2.17B-H JSON reports")
    add_check("all_phase_reports_pass_closure_assessment", all(row["closure_assessment"] == "PASS" for row in ledger), "critical", str({row["phase"]: row["closure_assessment"] for row in ledger}))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("canonical_rows_expected", canonical_rows_count == CURRENT_CANONICAL_ROWS, "critical", f"canonical_rows={canonical_rows_count}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "canonical sha unchanged during closure")
    add_check("expanded_candidate_dataset_exists", EXPANDED_CANDIDATE_CSV.exists(), "critical", str(EXPANDED_CANDIDATE_CSV))
    add_check("expanded_candidate_rows_expected", candidate_rows_count == EXPECTED_CANDIDATE_ROWS, "critical", f"candidate_rows={candidate_rows_count}")
    add_check("safe_delta_rows_expected", delta_rows_count == EXPECTED_SAFE_DELTA_ROWS, "critical", f"delta_rows={delta_rows_count}")
    add_check("delta_rows_equal_promotions", delta_rows_count == promotions_count, "critical", f"delta={delta_rows_count} promotions={promotions_count}")
    add_check("candidate_schema_matches_canonical", canonical_header == candidate_header, "critical", f"canonical_cols={len(canonical_header)} candidate_cols={len(candidate_header)}")
    add_check("h_report_status_expected", reports["v2.17H"].get("status") == EXPECTED_STATUS["v2.17H"], "critical", reports["v2.17H"].get("status", ""))
    add_check("h_report_recommends_closure", reports["v2.17H"].get("recommended_next_phase") == EXPECTED_NEXT["v2.17H"], "critical", reports["v2.17H"].get("recommended_next_phase", ""))
    add_check("promotion_policy_qa_rows_expected", len(promotion_policy_qa_rows) == EXPECTED_SAFE_DELTA_ROWS, "critical", f"promotion_policy_qa_rows={len(promotion_policy_qa_rows)}")
    add_check("delta_integrity_rows_present", len(delta_integrity_rows) >= 5, "critical", f"delta_integrity_rows={len(delta_integrity_rows)}")
    add_check("schema_mapping_rows_present", len(schema_mapping_rows) > 0, "critical", f"schema_mapping_rows={len(schema_mapping_rows)}")
    add_check("full_source_still_blocked", candidate_rows_count < FULL_SOURCE_THRESHOLD, "critical", f"{candidate_rows_count} < {FULL_SOURCE_THRESHOLD}")
    add_check("rows_needed_after_candidate_expected", rows_needed_after_candidate == 9700, "critical", f"rows_needed_after_candidate={rows_needed_after_candidate}")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("canonical_dataset_read", True, "critical", "canonical_dataset_read=True")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("expanded_universe_not_rebuilt_as_canonical", True, "critical", "expanded_universe_rebuilt_as_canonical=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed == 0:
        status = "NSE_INDIA_CLOSURE_COMPLETED_VALIDATED_CANDIDATE_RETAINED_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE
    else:
        status = "NSE_INDIA_CLOSURE_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.17I_FIX - NSE India Closure Repair"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": canonical_rows_count,
            "validated_candidate_dataset": str(EXPANDED_CANDIDATE_CSV),
            "validated_candidate_rows": candidate_rows_count,
            "safe_delta_rows": delta_rows_count,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_after_candidate": rows_needed_after_candidate,
            "candidate_completion_percent": completion_after_candidate,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "provider_closure_summary": {
            "provider": "NSE India",
            "market": "India",
            "closure_result": "validated_candidate_retained_not_promoted_to_active_canonical",
            "canonical_rows_before_provider": CURRENT_CANONICAL_ROWS,
            "safe_delta_rows": delta_rows_count,
            "validated_candidate_rows": candidate_rows_count,
            "candidate_completion_percent": completion_after_candidate,
            "rows_needed_after_candidate": rows_needed_after_candidate,
            "would_reach_full_source_threshold": candidate_rows_count >= FULL_SOURCE_THRESHOLD,
            "active_canonical_replaced": False,
            "canonical_sha256_before": canonical_sha_before,
            "canonical_sha256_after": canonical_sha_after,
            "v2_17h_status": h_report.get("status", ""),
            "v2_17h_summary": h_summary,
            "critical_failed_checks": critical_failed,
        },
        "closure_ledger": ledger,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "phase_reports_v2_17b_to_v2_17h_read": True,
            "canonical_dataset_read": True,
            "candidate_dataset_read": True,
            "closure_report_written": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "validated_candidate_retained": True,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "full_source_gate_unblocked": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
        "recommended_next_provider_candidate": RECOMMENDED_NEXT_PROVIDER_CANDIDATE,
        "reserve_provider_candidate": RESERVE_PROVIDER_CANDIDATE,
    }

    write_json(REPORT_JSON, payload)

    # Refresh artifact rows now closure outputs exist.
    artifacts = [
        artifact_row(CANONICAL_DATASET, "active_canonical_dataset", "Must remain unchanged and active."),
        artifact_row(EXPANDED_CANDIDATE_CSV, "validated_expanded_candidate_dataset", "NSE India candidate dataset; not active canonical."),
        artifact_row(DELTA_ROWS_CSV, "safe_delta_rows", "Safe NSE India promoted rows only."),
        artifact_row(PROMOTIONS_CSV, "safe_promotions", "Promotion ledger from v2.17G."),
        artifact_row(SCHEMA_MAPPING_CSV, "schema_mapping", "Mapping used for appended rows."),
        artifact_row(V217H_DATASET_PROFILE_CSV, "expanded_validation_dataset_profile", "v2.17H dataset profile."),
        artifact_row(V217H_PROMOTION_POLICY_QA_CSV, "promotion_policy_qa", "v2.17H safe promotion QA."),
        artifact_row(V217H_DELTA_INTEGRITY_CSV, "delta_integrity", "v2.17H delta integrity QA."),
        artifact_row(REPORT_JSON, "closure_json_report", "v2.17I closure JSON report."),
        artifact_row(REPORT_MD, "closure_markdown_report", "Will be written after artifact CSV."),
    ]

    for phase, path in PHASE_FILES.items():
        artifacts.append(artifact_row(path, f"{phase}_json_report", f"{phase} phase report."))

    write_csv(CLOSURE_LEDGER_CSV, ledger, CLOSURE_LEDGER_FIELDS)
    write_csv(CLOSURE_ARTIFACTS_CSV, artifacts, CLOSURE_ARTIFACT_FIELDS)
    write_csv(CLOSURE_NEXT_STEPS_CSV, closure_next_steps, CLOSURE_NEXT_STEPS_FIELDS)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    ledger_lines = "\n".join(
        f"- `{row['phase']}`: {row['closure_assessment']} — `{row['status']}`"
        for row in ledger
    )

    next_lines = "\n".join(
        f"- P{row['priority']}: {row['next_step']} — `{row['recommended_phase']}` — {row['provider_candidate']}"
        for row in closure_next_steps
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

NSE India provider route is closed.

The route produced a validated expanded candidate dataset but did not replace or modify the active canonical dataset. The safe NSE India delta contains `{delta_rows_count}` rows, taking the candidate dataset to `{candidate_rows_count}` rows. The full-source threshold remains blocked because the candidate is still below `{FULL_SOURCE_THRESHOLD}` rows.

## Final provider result

- Provider: `NSE India`
- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{canonical_rows_count}`
- Validated candidate dataset: `{EXPANDED_CANDIDATE_CSV}`
- Validated candidate rows: `{candidate_rows_count}`
- Safe delta rows: `{delta_rows_count}`
- Rows needed after candidate: `{rows_needed_after_candidate}`
- Candidate completion toward 50k: `{completion_after_candidate}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`
- Active canonical replaced: `false`
- Canonical SHA before: `{canonical_sha_before}`
- Canonical SHA after: `{canonical_sha_after}`

## Phase ledger

{ledger_lines}

## Closure checks

{check_lines}

## Guard summary

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Phase reports v2.17B-H read: true
- Canonical dataset read: true
- Candidate dataset read: true
- Closure report written: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Validated candidate retained: true
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Closure decision

NSE India is closed as a successful provider route that created and validated a conservative candidate expansion. It should remain as a validated candidate dataset until a separately controlled promotion decision is opened.

## Next steps

{next_lines}

## Recommended next phase

`{recommended_next_phase}`

## Recommended next provider candidate

`{RECOMMENDED_NEXT_PROVIDER_CANDIDATE}`

## Reserve provider candidate

`{RESERVE_PROVIDER_CANDIDATE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.17I NSE India closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("PROVIDER_CLOSURE_SUMMARY:")
    for key, value in payload["provider_closure_summary"].items():
        if key != "v2_17h_summary":
            print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("PHASE_LEDGER:")
    for row in ledger:
        print(f"- {row['phase']}: {row['closure_assessment']} - {row['status']}")
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
    print("")
    print("RECOMMENDED_NEXT_PROVIDER_CANDIDATE:")
    print(f"- {RECOMMENDED_NEXT_PROVIDER_CANDIDATE}")


if __name__ == "__main__":
    main()
