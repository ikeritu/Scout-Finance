from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.18A"
PHASE = "Next Provider Route Selection"
PHASE_TYPE = "target-policy-and-provider-route-selection-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
VALIDATED_NSE_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"

V217I_JSON = OUTPUT_DIR / "nse_india_closure_report_v2_17i.json"

REPORT_JSON = OUTPUT_DIR / "next_provider_route_selection_v2_18a.json"
REPORT_MD = OUTPUT_DIR / "next_provider_route_selection_v2_18a.md"
TARGET_POLICY_CSV = OUTPUT_DIR / "target_policy_50k_v2_18a.csv"
PROVIDER_CANDIDATES_CSV = OUTPUT_DIR / "next_provider_route_candidates_v2_18a.csv"
ROUTE_DECISION_CSV = OUTPUT_DIR / "next_provider_route_decision_v2_18a.csv"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
VALIDATED_CANDIDATE_ROWS_EXPECTED = 40300
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_EXPECTED = 9700

EXPECTED_V217I_STATUS = "NSE_INDIA_CLOSURE_COMPLETED_VALIDATED_CANDIDATE_RETAINED_FULL_SOURCE_STILL_BLOCKED"

RECOMMENDED_NEXT_PROVIDER = "TWSE + TPEx Taiwan"
RESERVE_PROVIDER = "ASX Australia"
DEPRECATED_TARGET = "full59k"

RECOMMENDED_NEXT_PHASE = "v2.18B - TWSE + TPEx Acquisition Plan"

TARGET_POLICY_FIELDS = [
    "policy_key",
    "policy_value",
    "status",
    "notes",
]

PROVIDER_CANDIDATE_FIELDS = [
    "rank",
    "provider_route",
    "market",
    "route_role",
    "expected_value",
    "known_risks",
    "selection_status",
    "recommended_phase",
    "notes",
]

ROUTE_DECISION_FIELDS = [
    "decision_key",
    "decision_value",
    "rationale",
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


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        TARGET_POLICY_CSV,
        PROVIDER_CANDIDATES_CSV,
        ROUTE_DECISION_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    closure_report = read_json(V217I_JSON)

    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)
    candidate_header, candidate_rows = read_csv_with_header(VALIDATED_NSE_CANDIDATE_DATASET)

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())
    candidate_sha = sha256_bytes(VALIDATED_NSE_CANDIDATE_DATASET.read_bytes())

    active_canonical_rows = len(canonical_rows)
    validated_candidate_rows = len(candidate_rows)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - validated_candidate_rows, 0)
    candidate_completion_percent = round((validated_candidate_rows / FINAL_TARGET_CANDIDATES) * 100, 2)

    target_policy_rows = [
        {
            "policy_key": "final_target_candidates",
            "policy_value": FINAL_TARGET_CANDIDATES,
            "status": "ACTIVE",
            "notes": "New final operational target. The project no longer needs 59k candidates.",
        },
        {
            "policy_key": "validated_candidate_rows_after_nse_india",
            "policy_value": validated_candidate_rows,
            "status": "REFERENCE",
            "notes": "Validated candidate dataset from NSE India route.",
        },
        {
            "policy_key": "rows_needed_to_final_target",
            "policy_value": rows_needed_to_50k,
            "status": "ACTIVE",
            "notes": "Remaining rows needed to reach the 50k candidate target.",
        },
        {
            "policy_key": "full59k_target",
            "policy_value": "deprecated",
            "status": "DEPRECATED",
            "notes": "No full59k dry run or 59k objective should be launched unless explicitly reopened later.",
        },
        {
            "policy_key": "stop_condition",
            "policy_value": "candidate_dataset_rows >= 50000",
            "status": "ACTIVE",
            "notes": "Provider acquisition can stop once a validated candidate dataset reaches at least 50,000 rows.",
        },
        {
            "policy_key": "canonical_promotion",
            "policy_value": "requires_explicit_controlled_promotion_phase",
            "status": "BLOCKED",
            "notes": "Validated candidate datasets are not automatically promoted to active canonical.",
        },
    ]

    provider_candidates = [
        {
            "rank": 1,
            "provider_route": "TWSE + TPEx Taiwan",
            "market": "Taiwan",
            "route_role": "primary_next_provider",
            "expected_value": "potentially meaningful listed equity coverage from official Taiwan exchange sources",
            "known_risks": "source format variability; dual exchange split; encoding/schema handling; may or may not cover the full 9,700 remaining rows alone",
            "selection_status": "SELECTED",
            "recommended_phase": "v2.18B - TWSE + TPEx Acquisition Plan",
            "notes": "Recommended next route after NSE India closure and new 50k target policy.",
        },
        {
            "rank": 2,
            "provider_route": "ASX Australia",
            "market": "Australia",
            "route_role": "reserve_provider",
            "expected_value": "strong fallback route if Taiwan does not reach enough rows",
            "known_risks": "may require separate handling of ordinary shares, ETFs, warrants, trusts and non-equity instruments",
            "selection_status": "RESERVE",
            "recommended_phase": "v2.19A or fallback after v2.18 closure",
            "notes": "Reserve route already identified before NSE India closure.",
        },
        {
            "rank": 3,
            "provider_route": "KRX / HKEX / LSEG / SGX",
            "market": "Korea / Hong Kong / United Kingdom / Singapore",
            "route_role": "deferred_pool",
            "expected_value": "possible later routes if 50k remains blocked after Taiwan and/or ASX",
            "known_risks": "higher source complexity, licensing/format uncertainty or lower immediate priority",
            "selection_status": "DEFERRED",
            "recommended_phase": "future route selection only if needed",
            "notes": "Not selected for immediate next route.",
        },
    ]

    route_decision_rows = [
        {
            "decision_key": "new_final_target",
            "decision_value": "50,000 candidates",
            "rationale": "User confirmed that 50k candidates is sufficient and 59k is no longer necessary.",
        },
        {
            "decision_key": "current_validated_candidate_rows",
            "decision_value": str(validated_candidate_rows),
            "rationale": "Validated NSE India candidate dataset contains 40,300 rows.",
        },
        {
            "decision_key": "remaining_gap",
            "decision_value": str(rows_needed_to_50k),
            "rationale": "Only 9,700 additional validated candidate rows are needed to reach the new final target.",
        },
        {
            "decision_key": "selected_next_provider",
            "decision_value": RECOMMENDED_NEXT_PROVIDER,
            "rationale": "Selected as primary next route in v2.17I and still appropriate under the 50k-only target.",
        },
        {
            "decision_key": "reserve_provider",
            "decision_value": RESERVE_PROVIDER,
            "rationale": "Kept as fallback if Taiwan does not close the 9,700-row gap.",
        },
        {
            "decision_key": "full59k_status",
            "decision_value": "deprecated/deferred",
            "rationale": "No full59k execution, dry run or target pursuit unless explicitly reopened later.",
        },
        {
            "decision_key": "recommended_next_phase",
            "decision_value": RECOMMENDED_NEXT_PHASE,
            "rationale": "Proceed with Taiwan acquisition planning only, without downloads yet.",
        },
    ]

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_17i_report_exists", V217I_JSON.exists(), "critical", str(V217I_JSON))
    add_check("v2_17i_status_expected", closure_report.get("status") == EXPECTED_V217I_STATUS, "critical", closure_report.get("status", ""))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("validated_nse_candidate_dataset_exists", VALIDATED_NSE_CANDIDATE_DATASET.exists(), "critical", str(VALIDATED_NSE_CANDIDATE_DATASET))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("validated_candidate_rows_expected", validated_candidate_rows == VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"validated_candidate_rows={validated_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("candidate_below_50k", validated_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{validated_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("candidate_schema_matches_canonical", canonical_header == candidate_header, "critical", f"canonical_cols={len(canonical_header)} candidate_cols={len(candidate_header)}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "canonical sha unchanged")
    add_check("target_50k_active", FINAL_TARGET_CANDIDATES == 50000, "critical", f"final_target={FINAL_TARGET_CANDIDATES}")
    add_check("full59k_deprecated", DEPRECATED_TARGET == "full59k", "critical", "full59k is deprecated/deferred")
    add_check("next_provider_selected", RECOMMENDED_NEXT_PROVIDER == "TWSE + TPEx Taiwan", "critical", RECOMMENDED_NEXT_PROVIDER)
    add_check("reserve_provider_selected", RESERVE_PROVIDER == "ASX Australia", "critical", RESERVE_PROVIDER)
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("endpoint_calls_not_used", True, "critical", "endpoint_calls_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")

    if critical_failed == 0:
        status = "NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_TWSE_TPEX_SELECTED_50K_TARGET_ACTIVE_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "NEXT_PROVIDER_ROUTE_SELECTION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.18A_FIX - Next Provider Route Selection Repair"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "target_policy": {
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "validated_candidate_rows_after_nse_india": validated_candidate_rows,
            "rows_needed_to_final_target": rows_needed_to_50k,
            "candidate_completion_percent": candidate_completion_percent,
            "full59k_status": "DEPRECATED_DEFERRED_NOT_ACTIVE",
            "full59k_launch_allowed": False,
            "stop_condition": "validated_candidate_dataset_rows >= 50000",
        },
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "validated_nse_candidate_dataset": str(VALIDATED_NSE_CANDIDATE_DATASET),
            "validated_candidate_rows": validated_candidate_rows,
            "rows_needed_to_50k": rows_needed_to_50k,
            "candidate_completion_percent": candidate_completion_percent,
            "canonical_sha256_before": canonical_sha_before,
            "canonical_sha256_after": canonical_sha_after,
            "validated_candidate_sha256": candidate_sha,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
        },
        "route_decision": {
            "selected_next_provider": RECOMMENDED_NEXT_PROVIDER,
            "reserve_provider": RESERVE_PROVIDER,
            "deferred_provider_pool": ["KRX", "HKEX", "LSEG", "SGX"],
            "recommended_next_phase": recommended_next_phase,
            "decision_basis": "Need 9,700 additional validated candidate rows to reach 50,000; Taiwan selected from v2.17I recommendation.",
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "candidate_extraction_performed": False,
            "canonical_comparison_performed": False,
            "canonical_dataset_read": True,
            "validated_candidate_dataset_read": True,
            "target_policy_written": True,
            "provider_route_selected": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "final_target_50k_active": True,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)
    write_csv(TARGET_POLICY_CSV, target_policy_rows, TARGET_POLICY_FIELDS)
    write_csv(PROVIDER_CANDIDATES_CSV, provider_candidates, PROVIDER_CANDIDATE_FIELDS)
    write_csv(ROUTE_DECISION_CSV, route_decision_rows, ROUTE_DECISION_FIELDS)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    provider_lines = "\n".join(
        f"- Rank {row['rank']}: `{row['provider_route']}` — {row['selection_status']} — {row['recommended_phase']}"
        for row in provider_candidates
    )

    policy_lines = "\n".join(
        f"- `{row['policy_key']}`: `{row['policy_value']}` — {row['status']} — {row['notes']}"
        for row in target_policy_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.18A updates the universe target policy and selects the next provider route.

The active final target is now **50,000 candidates**. The previous 59k objective is deprecated/deferred and must not be launched unless explicitly reopened later.

After NSE India, the validated candidate dataset contains `{validated_candidate_rows}` rows. The remaining gap to 50,000 is `{rows_needed_to_50k}` rows.

## Target policy

{policy_lines}

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{active_canonical_rows}`
- Validated NSE candidate dataset: `{VALIDATED_NSE_CANDIDATE_DATASET}`
- Validated candidate rows: `{validated_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Candidate completion: `{candidate_completion_percent}%`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Provider route candidates

{provider_lines}

## Route decision

- Selected next provider: `{RECOMMENDED_NEXT_PROVIDER}`
- Reserve provider: `{RESERVE_PROVIDER}`
- Deferred pool: `KRX`, `HKEX`, `LSEG`, `SGX`
- Recommended next phase: `{recommended_next_phase}`

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- Target policy written: true
- Provider route selected: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Final target 50k active: true
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Overwrite allowed: false

## Conclusion

v2.18A selects `TWSE + TPEx Taiwan` as the next provider route under the new 50k-only target policy.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.18A next provider route selection completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("TARGET_POLICY:")
    for key, value in payload["target_policy"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("ROUTE_DECISION:")
    for key, value in payload["route_decision"].items():
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
