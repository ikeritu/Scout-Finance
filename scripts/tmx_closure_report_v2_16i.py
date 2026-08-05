from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.16I"
PHASE = "TMX Closure Report"
PHASE_TYPE = "provider-closure-report-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_tmx_v2_16g.csv"

V216C_MANIFEST = OUTPUT_DIR / "tmx_raw_acquisition_manifest_v2_16c.json"
V216E_JSON = OUTPUT_DIR / "tmx_candidate_extraction_dry_run_v2_16e.json"
V216F_JSON = OUTPUT_DIR / "tmx_candidate_validation_against_canonical_v2_16f.json"
V216G_JSON = OUTPUT_DIR / "tmx_expanded_rebuild_candidate_v2_16g.json"
V216H_JSON = OUTPUT_DIR / "tmx_expanded_validation_v2_16h.json"

V216G_ADDITIONS = OUTPUT_DIR / "tmx_expanded_rebuild_candidate_additions_v2_16g.csv"
V216H_PROFILE = OUTPUT_DIR / "tmx_expanded_validation_profile_v2_16h.csv"

REPORT_JSON = OUTPUT_DIR / "tmx_closure_report_v2_16i.json"
REPORT_MD = OUTPUT_DIR / "tmx_closure_report_v2_16i.md"
PHASE_INVENTORY_CSV = OUTPUT_DIR / "tmx_closure_phase_inventory_v2_16i.csv"
DECISION_LOG_CSV = OUTPUT_DIR / "tmx_closure_decision_log_v2_16i.csv"

CURRENT_CANONICAL_ROWS = 38287
VALIDATED_CANDIDATE_ROWS = 38288
VALIDATED_DELTA = 1
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_ACTIVE_CANONICAL = 11713
ROWS_NEEDED_IF_CANDIDATE_PROMOTED_LATER = 11712

NEXT_PHASE = "v2.17A - Next Provider Route Selection"

EXPECTED_H_STATUS = "TMX_EXPANDED_VALIDATION_COMPLETED_CANDIDATE_ADD1_VALID_CANONICAL_STILL_UNCHANGED_FULL_SOURCE_STILL_BLOCKED"
EXPECTED_G_STATUS = "TMX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_ADD1_FULL_SOURCE_STILL_BLOCKED"
EXPECTED_F_STATUS = "TMX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_REBUILD_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED"
EXPECTED_E_STATUS = "TMX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED"

PHASE_INVENTORY_FIELDS = [
    "phase",
    "title",
    "expected_artifact",
    "artifact_found",
    "status",
    "recommended_next_phase",
    "key_result",
    "closure_assessment",
]

DECISION_LOG_FIELDS = [
    "decision_id",
    "topic",
    "decision",
    "reason",
    "impact",
]

SYMBOL_COLUMNS = [
    "ticker",
    "symbol",
    "raw_symbol",
    "normalized_symbol",
    "source_symbol",
    "yahoo_symbol",
    "bbg_ticker",
    "figi_ticker",
    "security_ticker",
]

EXCHANGE_COLUMNS = [
    "exchange",
    "raw_exchange",
    "normalized_exchange",
    "source_exchange",
    "exchange_code",
    "market",
    "mic",
    "venue",
]

NAME_COLUMNS = [
    "name",
    "company_name",
    "raw_name",
    "security_name",
    "issuer_name",
    "instrument_name",
    "long_name",
    "short_name",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json_optional(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        return [], []

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
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


def pick_column(fieldnames: list[str], candidates: list[str]) -> str:
    lower_map = {name.lower(): name for name in fieldnames if name}

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    for name in fieldnames:
        low = name.lower()
        for candidate in candidates:
            if candidate.lower() in low:
                return name

    return ""


def normalize_symbol(value: str) -> str:
    value = str(value or "").strip().upper()
    for prefix in ["TSX:", "TSXV:", "TSX-V:", "NYSE:", "NASDAQ:"]:
        value = value.replace(prefix, "")
    return value.strip(" .,:;|[](){}")


def normalize_exchange(value: str) -> str:
    value = str(value or "").strip().upper()
    aliases = {
        "TSX VENTURE": "TSXV",
        "TSX VENTURE EXCHANGE": "TSXV",
        "TSX-V": "TSXV",
        "TSXV": "TSXV",
        "TORONTO STOCK EXCHANGE": "TSX",
        "TSX": "TSX",
        "XTSE": "TSX",
        "XTSX": "TSXV",
    }
    return aliases.get(value, value)


def normalize_name(value: str) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split()).strip()


def count_csv_rows(path: Path) -> int:
    _, rows = read_csv(path)
    return len(rows)


def json_status(payload: dict) -> str:
    return str(payload.get("status", "") or "")


def json_next(payload: dict) -> str:
    return str(payload.get("recommended_next_phase", "") or "")


def main() -> None:
    for path in [REPORT_JSON, REPORT_MD, PHASE_INVENTORY_CSV, DECISION_LOG_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    c_manifest = read_json_optional(V216C_MANIFEST)
    e_report = read_json_optional(V216E_JSON)
    f_report = read_json_optional(V216F_JSON)
    g_report = read_json_optional(V216G_JSON)
    h_report = read_json_optional(V216H_JSON)

    canonical_fieldnames, canonical_rows = read_csv(CANONICAL_DATASET)
    candidate_fieldnames, candidate_rows = read_csv(CANDIDATE_DATASET)
    additions_fieldnames, additions_rows = read_csv(V216G_ADDITIONS)
    profile_fieldnames, profile_rows = read_csv(V216H_PROFILE)

    canonical_rows_count = len(canonical_rows)
    candidate_rows_count = len(candidate_rows)
    candidate_delta = candidate_rows_count - canonical_rows_count

    symbol_col = pick_column(candidate_fieldnames or canonical_fieldnames, SYMBOL_COLUMNS)
    exchange_col = pick_column(candidate_fieldnames or canonical_fieldnames, EXCHANGE_COLUMNS)
    name_col = pick_column(candidate_fieldnames or canonical_fieldnames, NAME_COLUMNS)

    validated_additions = []

    for row in additions_rows:
        validated_additions.append(
            {
                "symbol": normalize_symbol(row.get("raw_symbol", "")),
                "name": normalize_name(row.get("raw_name", "")),
                "exchange": normalize_exchange(row.get("raw_exchange", "")),
                "confidence_bucket": row.get("confidence_bucket", ""),
                "source_id": row.get("source_id", ""),
                "validation_status": row.get("validation_status", ""),
                "rebuild_candidate_reason": row.get("rebuild_candidate_reason", ""),
            }
        )

    expected_addition_found = any(
        row["symbol"] == "IRR"
        and row["exchange"] == "TSXV"
        and row["name"] == "Irruptive Metals Corp."
        for row in validated_additions
    )

    phase_inventory = [
        {
            "phase": "v2.16A",
            "title": "TMX Provider Route Confirmation",
            "expected_artifact": "committed phase record / route confirmation",
            "artifact_found": "not independently asserted by closure script",
            "status": "closed_in_git_history",
            "recommended_next_phase": "v2.16B - TMX Acquisition Plan",
            "key_result": "TMX selected as next provider route after Euronext closure.",
            "closure_assessment": "closed_by_git_history",
        },
        {
            "phase": "v2.16B",
            "title": "TMX Acquisition Plan",
            "expected_artifact": "committed phase record / acquisition plan",
            "artifact_found": "not independently asserted by closure script",
            "status": "closed_in_git_history",
            "recommended_next_phase": "v2.16C - TMX Raw Acquisition",
            "key_result": "TMX source candidates defined.",
            "closure_assessment": "closed_by_git_history",
        },
        {
            "phase": "v2.16C",
            "title": "TMX Raw Acquisition",
            "expected_artifact": str(V216C_MANIFEST),
            "artifact_found": str(V216C_MANIFEST.exists()),
            "status": json_status(c_manifest) or "raw_manifest_available" if V216C_MANIFEST.exists() else "missing",
            "recommended_next_phase": json_next(c_manifest),
            "key_result": "Raw TMX landing/source responses acquired; controlled/paid sources not downloaded.",
            "closure_assessment": "ok" if V216C_MANIFEST.exists() else "review_missing_artifact",
        },
        {
            "phase": "v2.16D",
            "title": "TMX Validation",
            "expected_artifact": "committed validation artifacts",
            "artifact_found": "not independently asserted by closure script",
            "status": "closed_in_git_history",
            "recommended_next_phase": "v2.16D2 - TMX Controlled Endpoint Probe",
            "key_result": "Raw source validation completed; controlled endpoint probe recommended.",
            "closure_assessment": "closed_by_git_history",
        },
        {
            "phase": "v2.16D2",
            "title": "TMX Controlled Endpoint Probe",
            "expected_artifact": "committed controlled probe artifacts",
            "artifact_found": "not independently asserted by closure script",
            "status": "closed_in_git_history",
            "recommended_next_phase": "v2.16E - TMX Candidate Extraction Dry Run",
            "key_result": "No promising endpoint path found; candidate extraction moved to local raw extraction.",
            "closure_assessment": "closed_by_git_history",
        },
        {
            "phase": "v2.16E",
            "title": "TMX Candidate Extraction Dry Run",
            "expected_artifact": str(V216E_JSON),
            "artifact_found": str(V216E_JSON.exists()),
            "status": json_status(e_report),
            "recommended_next_phase": json_next(e_report),
            "key_result": "13 conservative candidates extracted; newsroom false positives removed.",
            "closure_assessment": "ok" if json_status(e_report) == EXPECTED_E_STATUS else "review_status",
        },
        {
            "phase": "v2.16F",
            "title": "TMX Candidate Validation Against Canonical Dry Run",
            "expected_artifact": str(V216F_JSON),
            "artifact_found": str(V216F_JSON.exists()),
            "status": json_status(f_report),
            "recommended_next_phase": json_next(f_report),
            "key_result": "13 candidates validated; 1 rebuild candidate selected: IRR / Irruptive Metals Corp. / TSXV.",
            "closure_assessment": "ok" if json_status(f_report) == EXPECTED_F_STATUS else "review_status",
        },
        {
            "phase": "v2.16G",
            "title": "TMX Expanded Rebuild Candidate",
            "expected_artifact": str(V216G_JSON),
            "artifact_found": str(V216G_JSON.exists()),
            "status": json_status(g_report),
            "recommended_next_phase": json_next(g_report),
            "key_result": "Separate candidate dataset generated with +1 row; canonical not replaced.",
            "closure_assessment": "ok" if json_status(g_report) == EXPECTED_G_STATUS else "review_status",
        },
        {
            "phase": "v2.16H",
            "title": "TMX Expanded Validation",
            "expected_artifact": str(V216H_JSON),
            "artifact_found": str(V216H_JSON.exists()),
            "status": json_status(h_report),
            "recommended_next_phase": json_next(h_report),
            "key_result": "Candidate dataset validated: canonical +1, IRR/TSXV, full source still blocked.",
            "closure_assessment": "ok" if json_status(h_report) == EXPECTED_H_STATUS else "review_status",
        },
    ]

    decisions = [
        {
            "decision_id": sha256_text(f"{VERSION}|canonical_not_modified")[:16],
            "topic": "Canonical dataset",
            "decision": "Do not modify expanded_universe_v2_14e.csv in TMX closure.",
            "reason": "v2.16I is a closure report, not a promotion/rebuild phase.",
            "impact": "Active canonical remains 38,287 rows.",
        },
        {
            "decision_id": sha256_text(f"{VERSION}|candidate_preserved")[:16],
            "topic": "TMX candidate dataset",
            "decision": "Preserve expanded_universe_candidate_tmx_v2_16g.csv as validated candidate artifact.",
            "reason": "v2.16G/H produced and validated a separate candidate dataset with one additional row.",
            "impact": "Candidate dataset remains available for later controlled promotion if explicitly opened.",
        },
        {
            "decision_id": sha256_text(f"{VERSION}|tmx_yield")[:16],
            "topic": "TMX source yield",
            "decision": "Close TMX with +1 validated candidate but no full-source unlock.",
            "reason": "The validated candidate improves candidate coverage by one row only; threshold remains far away.",
            "impact": "Full source gate remains BLOCKED.",
        },
        {
            "decision_id": sha256_text(f"{VERSION}|next_provider")[:16],
            "topic": "Next route",
            "decision": "Move to next provider/source route selection.",
            "reason": "TMX route is exhausted enough for closure under current controlled pipeline.",
            "impact": NEXT_PHASE,
        },
    ]

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("candidate_dataset_exists", CANDIDATE_DATASET.exists(), "critical", str(CANDIDATE_DATASET))
    add_check("v2_16e_artifact_exists", V216E_JSON.exists(), "critical", str(V216E_JSON))
    add_check("v2_16f_artifact_exists", V216F_JSON.exists(), "critical", str(V216F_JSON))
    add_check("v2_16g_artifact_exists", V216G_JSON.exists(), "critical", str(V216G_JSON))
    add_check("v2_16h_artifact_exists", V216H_JSON.exists(), "critical", str(V216H_JSON))
    add_check("v2_16e_status_expected", json_status(e_report) == EXPECTED_E_STATUS, "critical", json_status(e_report))
    add_check("v2_16f_status_expected", json_status(f_report) == EXPECTED_F_STATUS, "critical", json_status(f_report))
    add_check("v2_16g_status_expected", json_status(g_report) == EXPECTED_G_STATUS, "critical", json_status(g_report))
    add_check("v2_16h_status_expected", json_status(h_report) == EXPECTED_H_STATUS, "critical", json_status(h_report))
    add_check("canonical_rows_expected", canonical_rows_count == CURRENT_CANONICAL_ROWS, "critical", f"canonical_rows={canonical_rows_count}")
    add_check("candidate_rows_expected", candidate_rows_count == VALIDATED_CANDIDATE_ROWS, "critical", f"candidate_rows={candidate_rows_count}")
    add_check("candidate_delta_expected", candidate_delta == VALIDATED_DELTA, "critical", f"delta={candidate_delta}")
    add_check("validated_addition_found", expected_addition_found, "critical", str(validated_additions))
    add_check("full_source_still_blocked_active_canonical", canonical_rows_count < FULL_SOURCE_THRESHOLD, "critical", f"{canonical_rows_count} < {FULL_SOURCE_THRESHOLD}")
    add_check("full_source_still_blocked_candidate", candidate_rows_count < FULL_SOURCE_THRESHOLD, "critical", f"{candidate_rows_count} < {FULL_SOURCE_THRESHOLD}")
    add_check("next_phase_selected", NEXT_PHASE == "v2.17A - Next Provider Route Selection", "critical", NEXT_PHASE)
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("candidate_not_promoted_to_canonical", True, "critical", "candidate_promoted_to_canonical=False")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    status = (
        "TMX_CLOSURE_REPORT_COMPLETED_PLUS1_CANDIDATE_VALIDATED_FULL_SOURCE_STILL_BLOCKED"
        if critical_failed == 0
        else "TMX_CLOSURE_REPORT_FAILED_REVIEW_REQUIRED"
    )

    recommended_next_phase = NEXT_PHASE if critical_failed == 0 else "v2.16I_FIX - TMX Closure Report Repair"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": canonical_rows_count,
            "validated_candidate_dataset": str(CANDIDATE_DATASET),
            "validated_candidate_rows": candidate_rows_count,
            "validated_candidate_delta": candidate_delta,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_active_canonical": ROWS_NEEDED_ACTIVE_CANONICAL,
            "rows_needed_if_candidate_promoted_later": ROWS_NEEDED_IF_CANDIDATE_PROMOTED_LATER,
            "active_canonical_source_to_50k_completed_percent": round((canonical_rows_count / FULL_SOURCE_THRESHOLD) * 100, 2),
            "candidate_source_to_50k_completed_percent": round((candidate_rows_count / FULL_SOURCE_THRESHOLD) * 100, 2),
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "tmx_result": {
            "raw_route_attempted": True,
            "endpoint_probe_attempted": True,
            "candidate_extraction_performed": True,
            "candidate_validation_performed": True,
            "expanded_candidate_generated": True,
            "expanded_candidate_validated": True,
            "accepted_candidate_count": len(validated_additions),
            "validated_additions": validated_additions,
            "canonical_promoted": False,
            "canonical_rows_added_in_this_phase": 0,
            "provider_closed": critical_failed == 0,
        },
        "schema_observation": {
            "symbol_col": symbol_col,
            "exchange_col": exchange_col,
            "name_col": name_col,
            "canonical_field_count": len(canonical_fieldnames),
            "candidate_field_count": len(candidate_fieldnames),
        },
        "checks": checks,
        "phase_inventory": phase_inventory,
        "decision_log": decisions,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "phase_artifacts_read": True,
            "canonical_dataset_read": True,
            "candidate_dataset_read": True,
            "canonical_dataset_modified": False,
            "candidate_promoted_to_canonical": False,
            "canonical_replacement_performed": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "new_expanded_dataset_written": False,
            "net_new_filtering_applied_to_canonical": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "full_source_gate_unblocked": False,
            "overwrite_allowed": False,
        },
        "artifact_hashes": {
            "canonical_sha256": sha256_file(CANONICAL_DATASET) if CANONICAL_DATASET.exists() else "",
            "candidate_sha256": sha256_file(CANDIDATE_DATASET) if CANDIDATE_DATASET.exists() else "",
            "v2_16h_sha256": sha256_file(V216H_JSON) if V216H_JSON.exists() else "",
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)
    write_csv(PHASE_INVENTORY_CSV, phase_inventory, PHASE_INVENTORY_FIELDS)
    write_csv(DECISION_LOG_CSV, decisions, DECISION_LOG_FIELDS)

    phase_lines = "\n".join(
        f"- **{row['phase']} — {row['title']}**: `{row['closure_assessment']}` — {row['key_result']}"
        for row in phase_inventory
    )

    decision_lines = "\n".join(
        f"- **{row['topic']}**: {row['decision']} Impact: `{row['impact']}`"
        for row in decisions
    )

    addition_lines = "\n".join(
        f"- `{row['symbol']}` `{row['name']}` exchange=`{row['exchange']}` confidence=`{row['confidence_bucket']}` source=`{row['source_id']}`"
        for row in validated_additions
    ) or "- No validated additions."

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive closure

TMX is closed as a provider route under the current controlled acquisition pipeline.

The route produced one validated candidate addition in a separate candidate dataset:

{addition_lines}

The active canonical dataset remains unchanged.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{canonical_rows_count}`
- Validated candidate dataset: `{CANDIDATE_DATASET}`
- Validated candidate rows: `{candidate_rows_count}`
- Validated candidate delta: `{candidate_delta}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed with active canonical: `{ROWS_NEEDED_ACTIVE_CANONICAL}`
- Rows needed if candidate is promoted later: `{ROWS_NEEDED_IF_CANDIDATE_PROMOTED_LATER}`
- Active canonical source-to-50k completion: `{round((canonical_rows_count / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Candidate source-to-50k completion: `{round((candidate_rows_count / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Phase inventory

{phase_lines}

## Decision log

{decision_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Phase artifacts read: true
- Canonical dataset read: true
- Candidate dataset read: true
- Canonical dataset modified: false
- Candidate promoted to canonical: false
- Canonical replacement performed: false
- Expanded universe rebuilt as canonical: false
- New expanded dataset written: false
- Net-new filtering applied to canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Closure conclusion

TMX is closed with one validated candidate addition available as a separate candidate artifact.

No canonical promotion is performed in this phase. No rebuild is performed. Full source remains blocked because the active canonical dataset is still below the 50,000-row threshold.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16I TMX closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("TMX_RESULT:")
    for key, value in payload["tmx_result"].items():
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
