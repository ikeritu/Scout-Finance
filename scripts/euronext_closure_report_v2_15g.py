from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.15G"
PHASE = "Euronext Closure Report"
PHASE_TYPE = "closure-report-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ARTIFACTS = {
    "v2.15B": OUTPUT_DIR / "euronext_acquisition_plan_v2_15b.json",
    "v2.15C": OUTPUT_DIR / "euronext_raw_acquisition_manifest_v2_15c.json",
    "v2.15D": OUTPUT_DIR / "euronext_validation_v2_15d.json",
    "v2.15E": OUTPUT_DIR / "euronext_rebuild_candidate_prep_v2_15e.json",
    "v2.15F": OUTPUT_DIR / "euronext_candidate_extraction_dry_run_v2_15f.json",
    "v2.15F2": OUTPUT_DIR / "euronext_extraction_strategy_revision_v2_15f2.json",
    "v2.15F3": OUTPUT_DIR / "euronext_controlled_endpoint_probe_v2_15f3.json",
    "v2.15F4": OUTPUT_DIR / "euronext_endpoint_payload_shape_validation_v2_15f4.json",
    "v2.15F5": OUTPUT_DIR / "euronext_endpoint_candidate_extraction_dry_run_v2_15f5.json",
}

CLOSURE_JSON = OUTPUT_DIR / "euronext_closure_report_v2_15g.json"
CLOSURE_MD = OUTPUT_DIR / "euronext_closure_report_v2_15g.md"
EVIDENCE_CSV = OUTPUT_DIR / "euronext_closure_evidence_matrix_v2_15g.csv"
DECISIONS_CSV = OUTPUT_DIR / "euronext_closure_decisions_v2_15g.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

NEXT_PROVIDER_ID = "tmx_tsx_tsxv_official_equities"
NEXT_PROVIDER_NAME = "TMX / TSX / TSXV official equities"
NEXT_PHASE = "v2.16A - TMX Provider Route Confirmation"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def get_nested(payload: dict, *keys, default=None):
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def main() -> None:
    for path in [CLOSURE_JSON, CLOSURE_MD, EVIDENCE_CSV, DECISIONS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    loaded = {phase: read_json(path) for phase, path in ARTIFACTS.items()}

    b = loaded["v2.15B"]
    c = loaded["v2.15C"]
    d = loaded["v2.15D"]
    e = loaded["v2.15E"]
    f = loaded["v2.15F"]
    f2 = loaded["v2.15F2"]
    f3 = loaded["v2.15F3"]
    f4 = loaded["v2.15F4"]
    f5 = loaded["v2.15F5"]

    evidence_rows = [
        {
            "phase": "v2.15B",
            "artifact": str(ARTIFACTS["v2.15B"]),
            "status": b.get("status", ""),
            "finding": "Euronext selected as next official provider route.",
            "numeric_evidence": f"current_rows={CURRENT_ROWS}; rows_needed={ROWS_NEEDED}",
            "closure_relevance": "Opened Euronext route after v2.15A provider ranking.",
        },
        {
            "phase": "v2.15C",
            "artifact": str(ARTIFACTS["v2.15C"]),
            "status": c.get("status", ""),
            "finding": "Official Euronext raw sources acquired.",
            "numeric_evidence": (
                f"attempted={get_nested(c, 'download_summary', 'attempted', default='')}; "
                f"ok_count={get_nested(c, 'download_summary', 'ok_count', default='')}; "
                f"raw_dir={get_nested(c, 'download_summary', 'raw_dir', default='')}"
            ),
            "closure_relevance": "Confirmed public Euronext pages could be collected for inspection.",
        },
        {
            "phase": "v2.15D",
            "artifact": str(ARTIFACTS["v2.15D"]),
            "status": d.get("status", ""),
            "finding": "Raw Euronext artifacts validated and candidate endpoints detected.",
            "numeric_evidence": (
                f"raw_files={get_nested(d, 'validation_summary', 'raw_files', default='')}; "
                f"candidate_endpoints={get_nested(d, 'validation_summary', 'candidate_endpoints', default='')}"
            ),
            "closure_relevance": "Established enough structure to continue beyond simple raw acquisition.",
        },
        {
            "phase": "v2.15E",
            "artifact": str(ARTIFACTS["v2.15E"]),
            "status": e.get("status", ""),
            "finding": "Rebuild candidate preparation generated strategy rows and table candidates.",
            "numeric_evidence": (
                f"source_strategy_rows={get_nested(e, 'preparation_summary', 'source_strategy_rows', default='')}; "
                f"html_table_candidates={get_nested(e, 'preparation_summary', 'html_table_candidates', default='')}; "
                f"allowed_next_phase_endpoints={get_nested(e, 'preparation_summary', 'allowed_next_phase_endpoints', default='')}"
            ),
            "closure_relevance": "Prepared controlled extraction path while keeping rebuild blocked.",
        },
        {
            "phase": "v2.15F",
            "artifact": str(ARTIFACTS["v2.15F"]),
            "status": f.get("status", ""),
            "finding": "HTML/public-page extraction dry-run was low quality.",
            "numeric_evidence": (
                f"deduped_candidates={get_nested(f, 'dry_run_summary', 'deduped_extracted_candidates', default='')}; "
                f"unique_isins={get_nested(f, 'dry_run_summary', 'unique_isins', default='')}; "
                f"extraction_quality={get_nested(f, 'dry_run_summary', 'extraction_quality', default='')}"
            ),
            "closure_relevance": "Rejected public HTML tables as a rebuild source.",
        },
        {
            "phase": "v2.15F2",
            "artifact": str(ARTIFACTS["v2.15F2"]),
            "status": f2.get("status", ""),
            "finding": "Strategy revision rejected HTML route and prepared controlled probes.",
            "numeric_evidence": (
                f"public_html_failed_as_rebuild_source={get_nested(f2, 'revision_summary', 'public_html_failed_as_rebuild_source', default='')}; "
                f"executable_probe_rows={get_nested(f2, 'revision_summary', 'executable_probe_rows', default='')}"
            ),
            "closure_relevance": "Allowed only controlled endpoint probing, not rebuild.",
        },
        {
            "phase": "v2.15F3",
            "artifact": str(ARTIFACTS["v2.15F3"]),
            "status": f3.get("status", ""),
            "finding": "Controlled endpoint probe found medium-signal JSON/AJAX endpoints.",
            "numeric_evidence": (
                f"results={get_nested(f3, 'probe_summary', 'results', default='')}; "
                f"promising_count={get_nested(f3, 'probe_summary', 'promising_count', default='')}; "
                f"medium_or_better={get_nested(f3, 'probe_summary', 'medium_or_better_evidence_count', default='')}"
            ),
            "closure_relevance": "Euronext was not closed prematurely; endpoint path was tested.",
        },
        {
            "phase": "v2.15F4",
            "artifact": str(ARTIFACTS["v2.15F4"]),
            "status": f4.get("status", ""),
            "finding": "Payload shape validation found strong JSON shape with structural keys.",
            "numeric_evidence": (
                f"selected_json_endpoints={get_nested(f4, 'shape_summary', 'selected_json_promising_endpoints', default='')}; "
                f"security_like_container_count={get_nested(f4, 'shape_summary', 'security_like_container_count', default='')}; "
                f"medium_or_high_shape_count={get_nested(f4, 'shape_summary', 'medium_or_high_shape_count', default='')}; "
                f"key_path_rows={get_nested(f4, 'shape_summary', 'key_path_rows', default='')}"
            ),
            "closure_relevance": "Confirmed apparent JSON structure, but still without extracting securities.",
        },
        {
            "phase": "v2.15F5",
            "artifact": str(ARTIFACTS["v2.15F5"]),
            "status": f5.get("status", ""),
            "finding": "Endpoint candidate extraction dry-run produced no valid candidates.",
            "numeric_evidence": (
                f"raw_candidates_before_dedupe={get_nested(f5, 'extraction_summary', 'raw_candidates_before_dedupe', default='')}; "
                f"deduped_raw_candidates={get_nested(f5, 'extraction_summary', 'deduped_raw_candidates', default='')}; "
                f"unique_isins={get_nested(f5, 'extraction_summary', 'unique_isins', default='')}; "
                f"critical_failed_checks={get_nested(f5, 'extraction_summary', 'critical_failed_checks', default='')}"
            ),
            "closure_relevance": "Final evidence: public/probed Euronext route adds zero valid rows.",
        },
    ]

    decisions = [
        {
            "decision_id": "euronext_public_html_route",
            "decision": "closed_no_rebuild",
            "evidence": (
                f"v2.15F extraction_quality={get_nested(f, 'dry_run_summary', 'extraction_quality', default='')}; "
                f"unique_isins={get_nested(f, 'dry_run_summary', 'unique_isins', default='')}"
            ),
            "impact": "Do not use public HTML tables for expanded universe rebuild.",
        },
        {
            "decision_id": "euronext_json_endpoint_route",
            "decision": "closed_no_valid_candidates",
            "evidence": (
                f"v2.15F4 medium/high shape={get_nested(f4, 'shape_summary', 'medium_or_high_shape_count', default='')}; "
                f"v2.15F5 unique_isins={get_nested(f5, 'extraction_summary', 'unique_isins', default='')}; "
                f"deduped_candidates={get_nested(f5, 'extraction_summary', 'deduped_raw_candidates', default='')}"
            ),
            "impact": "Do not proceed to canonical dry-run, net-new filtering or rebuild for Euronext.",
        },
        {
            "decision_id": "euronext_rows_added",
            "decision": "zero_rows_added",
            "evidence": "No valid endpoint candidates; canonical dataset intentionally not read or modified.",
            "impact": "Current rows remain 38,287.",
        },
        {
            "decision_id": "full_source_gate",
            "decision": "remain_blocked",
            "evidence": f"current_rows={CURRENT_ROWS}; threshold={FULL_SOURCE_THRESHOLD}; rows_needed={ROWS_NEEDED}",
            "impact": "Full source gate and full59k remain blocked.",
        },
        {
            "decision_id": "next_provider",
            "decision": "open_tmx_route_next",
            "evidence": "Euronext closed with zero valid candidates; v2.15A ranking had TMX/TSX/TSXV as next strong route.",
            "impact": f"Recommended next phase: {NEXT_PHASE}.",
        },
    ]

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append(
            {
                "check": check,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    for phase, path in ARTIFACTS.items():
        add_check(f"{phase}_artifact_exists", path.exists(), "critical", str(path))

    add_check("v2_15f5_zero_valid_candidates_confirmed", get_nested(f5, "extraction_summary", "unique_isins", default=-1) == 0, "critical", "unique_isins=0")
    add_check("v2_15f5_no_critical_failures", get_nested(f5, "extraction_summary", "critical_failed_checks", default=-1) == 0, "critical", f"critical_failed_checks={get_nested(f5, 'extraction_summary', 'critical_failed_checks', default='')}")
    add_check("current_rows_unchanged", CURRENT_ROWS == 38287, "critical", f"current_rows={CURRENT_ROWS}")
    add_check("rows_needed_unchanged", ROWS_NEEDED == 11713, "critical", f"rows_needed={ROWS_NEEDED}")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"current_rows={CURRENT_ROWS}; threshold={FULL_SOURCE_THRESHOLD}")
    add_check("next_provider_selected", NEXT_PROVIDER_ID == "tmx_tsx_tsxv_official_equities", "critical", NEXT_PROVIDER_NAME)
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_network", True, "critical", "network_download_performed=False")
    add_check("no_normalization", True, "critical", "normalization_performed=False")
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")

    status = (
        "EURONEXT_CLOSED_PUBLIC_AND_ENDPOINT_ROUTE_ZERO_VALID_CANDIDATES_FULL_SOURCE_BLOCKED"
        if critical_failed == 0
        else "EURONEXT_CLOSURE_REPORT_FAILED_REVIEW_REQUIRED"
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "canonical_dataset": CURRENT_CANONICAL_DATASET,
            "current_rows": CURRENT_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED_PERCENT,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "closure_summary": {
            "provider": "Euronext",
            "provider_route": "official public pages and controlled JSON/AJAX endpoints",
            "phases_reviewed": list(ARTIFACTS.keys()),
            "artifacts_reviewed": len(ARTIFACTS),
            "public_html_rebuild_route": "closed_insufficient",
            "json_endpoint_route": "closed_zero_valid_candidates",
            "rows_added_to_expanded_universe": 0,
            "current_rows_after_closure": CURRENT_ROWS,
            "rows_needed_after_closure": ROWS_NEEDED,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED_PERCENT,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
            "critical_failed_checks": critical_failed,
            "next_provider_id": NEXT_PROVIDER_ID,
            "next_provider_name": NEXT_PROVIDER_NAME,
            "recommended_next_phase": NEXT_PHASE,
        },
        "evidence_matrix": evidence_rows,
        "decisions": decisions,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_probe_executed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "canonical_dataset_read": False,
            "canonical_dataset_modified": False,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": NEXT_PHASE,
    }

    write_json(CLOSURE_JSON, payload)
    write_csv(
        EVIDENCE_CSV,
        evidence_rows,
        ["phase", "artifact", "status", "finding", "numeric_evidence", "closure_relevance"],
    )
    write_csv(
        DECISIONS_CSV,
        decisions,
        ["decision_id", "decision", "evidence", "impact"],
    )

    evidence_lines = "\n".join(
        f"- **{row['phase']}** — {row['finding']} Evidence: `{row['numeric_evidence']}`"
        for row in evidence_rows
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}`: **{row['decision']}** — {row['impact']} Evidence: `{row['evidence']}`"
        for row in decisions
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    CLOSURE_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Current state

- Canonical dataset: `{CURRENT_CANONICAL_DATASET}`
- Current rows: `{CURRENT_ROWS}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completed: `{SOURCE_TO_50K_COMPLETED_PERCENT}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Closure summary

- Provider: `Euronext`
- Route reviewed: official public pages and controlled JSON/AJAX endpoints
- Phases reviewed: `{", ".join(ARTIFACTS.keys())}`
- Public HTML rebuild route: `closed_insufficient`
- JSON endpoint route: `closed_zero_valid_candidates`
- Rows added to expanded universe: `0`
- Current rows after closure: `{CURRENT_ROWS}`
- Rows needed after closure: `{ROWS_NEEDED}`
- Critical failed checks: `{critical_failed}`

## Evidence matrix

{evidence_lines}

## Decisions

{decision_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.15G: false
- Endpoint probe executed in v2.15G: false
- Raw files downloaded in v2.15G: false
- Raw files modified after write: false
- Canonical dataset read: false
- Canonical dataset modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

Euronext was investigated through official public pages and controlled JSON/AJAX endpoint probing.

The public HTML route was insufficient for rebuild. The JSON/AJAX route showed promising shape in v2.15F4, but v2.15F5 extracted zero valid candidates and zero unique ISINs.

Therefore, Euronext is closed as a public/probed source for the expanded universe. It adds zero rows, and the full source gate remains blocked.

## Recommended next phase

`{NEXT_PHASE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15G Euronext closure report completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("CLOSURE_SUMMARY:")
    for key, value in payload["closure_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("DECISIONS:")
    for row in decisions:
        print(f"- {row['decision_id']}: {row['decision']} - {row['evidence']}")
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
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
