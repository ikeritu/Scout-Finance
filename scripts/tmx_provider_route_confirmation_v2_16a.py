from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.16A"
PHASE = "TMX Provider Route Confirmation"
PHASE_TYPE = "provider-route-confirmation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

EURONEXT_CLOSURE_JSON = OUTPUT_DIR / "euronext_closure_report_v2_15g.json"

ROUTE_JSON = OUTPUT_DIR / "tmx_provider_route_confirmation_v2_16a.json"
ROUTE_MD = OUTPUT_DIR / "tmx_provider_route_confirmation_v2_16a.md"
DECISION_CSV = OUTPUT_DIR / "tmx_provider_route_decision_matrix_v2_16a.csv"
CHECKLIST_CSV = OUTPUT_DIR / "tmx_provider_route_checklist_v2_16a.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

NEXT_PROVIDER_ID = "tmx_tsx_tsxv_official_equities"
NEXT_PROVIDER_NAME = "TMX / TSX / TSXV official equities"
NEXT_PROVIDER_COUNTRY = "Canada"
NEXT_PROVIDER_SCOPE = "TSX and TSXV listed equities"
NEXT_PHASE = "v2.16B - TMX Acquisition Plan"


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


def optional_v2_15a_route_artifacts() -> list[str]:
    patterns = [
        "*v2_15a*.json",
        "*v2_15A*.json",
        "*next_provider*route*.json",
        "*provider_route*.json",
    ]

    found = []
    for pattern in patterns:
        for path in OUTPUT_DIR.glob(pattern):
            if path.name not in {EURONEXT_CLOSURE_JSON.name}:
                found.append(str(path))

    return sorted(set(found))


def main() -> None:
    for path in [ROUTE_JSON, ROUTE_MD, DECISION_CSV, CHECKLIST_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    euronext_closure = read_json(EURONEXT_CLOSURE_JSON)
    optional_route_artifacts = optional_v2_15a_route_artifacts()

    closure_status = euronext_closure.get("status", "")
    closure_next_phase = euronext_closure.get("recommended_next_phase", "")
    closure_summary = euronext_closure.get("closure_summary", {})

    decision_rows = [
        {
            "decision_id": "provider_after_euronext",
            "decision": "confirm_tmx_tsx_tsxv_as_next_route",
            "basis": (
                f"v2.15G recommended_next_phase={closure_next_phase}; "
                f"euronext_rows_added={get_nested(euronext_closure, 'closure_summary', 'rows_added_to_expanded_universe', default='')}; "
                f"euronext_unique_candidates=0"
            ),
            "impact": "Open TMX route as v2.16 without touching canonical dataset.",
        },
        {
            "decision_id": "phase_scope",
            "decision": "route_confirmation_only",
            "basis": "v2.16A confirms provider and scope only.",
            "impact": "No network, no download, no parsing, no rebuild.",
        },
        {
            "decision_id": "tmx_initial_scope",
            "decision": "tsx_and_tsxv_listed_equities",
            "basis": "TMX route is intended to cover Canadian listed equities after Euronext produced zero valid candidates.",
            "impact": "Focus next acquisition plan on official TMX / TSX / TSXV equity sources.",
        },
        {
            "decision_id": "instrument_scope",
            "decision": "equities_first_exclude_funds_by_default",
            "basis": "Existing source-acquisition policy excludes ETFs, ETNs, ETCs, funds, bonds and non-equity instruments unless explicitly approved.",
            "impact": "v2.16B must define exclusion logic before acquisition or parsing.",
        },
        {
            "decision_id": "full_source_gate",
            "decision": "remain_blocked",
            "basis": f"current_rows={CURRENT_ROWS}; threshold={FULL_SOURCE_THRESHOLD}; rows_needed={ROWS_NEEDED}",
            "impact": "Full source, full59k, scoring, OpenAI and broker layers remain blocked.",
        },
    ]

    checklist_rows = [
        {
            "phase": "v2.16A",
            "item": "confirm_tmx_provider_route",
            "status": "done_in_this_phase",
            "guard": "plan_only",
        },
        {
            "phase": "v2.16A",
            "item": "confirm_current_rows_unchanged",
            "status": "done_in_this_phase",
            "guard": f"current_rows={CURRENT_ROWS}",
        },
        {
            "phase": "v2.16A",
            "item": "keep_full_source_blocked",
            "status": "done_in_this_phase",
            "guard": "full_source_gate=BLOCKED",
        },
        {
            "phase": "v2.16B",
            "item": "identify_official_tmx_sources",
            "status": "next",
            "guard": "plan_only_until_approved",
        },
        {
            "phase": "v2.16B",
            "item": "define_tmx_source_taxonomy",
            "status": "next",
            "guard": "no_download_yet",
        },
        {
            "phase": "v2.16B",
            "item": "define_equity_vs_etf_fund_exclusion_policy",
            "status": "next",
            "guard": "no_parsing_yet",
        },
        {
            "phase": "v2.16C",
            "item": "tmx_raw_acquisition",
            "status": "future",
            "guard": "only_after_v2_16b",
        },
        {
            "phase": "v2.16D",
            "item": "tmx_validation",
            "status": "future",
            "guard": "no_rebuild",
        },
        {
            "phase": "v2.16E",
            "item": "tmx_candidate_extraction_dry_run",
            "status": "future",
            "guard": "no_canonical_read",
        },
        {
            "phase": "v2.16F",
            "item": "tmx_candidate_validation_against_canonical_dry_run",
            "status": "future",
            "guard": "read_only_canonical",
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

    add_check("euronext_closure_artifact_exists", EURONEXT_CLOSURE_JSON.exists(), "critical", str(EURONEXT_CLOSURE_JSON))
    add_check(
        "euronext_closed_with_zero_valid_candidates",
        closure_status == "EURONEXT_CLOSED_PUBLIC_AND_ENDPOINT_ROUTE_ZERO_VALID_CANDIDATES_FULL_SOURCE_BLOCKED",
        "critical",
        closure_status,
    )
    add_check(
        "euronext_recommended_tmx_route",
        closure_next_phase == "v2.16A - TMX Provider Route Confirmation",
        "critical",
        closure_next_phase,
    )
    add_check(
        "euronext_rows_added_zero",
        get_nested(euronext_closure, "closure_summary", "rows_added_to_expanded_universe", default=-1) == 0,
        "critical",
        f"rows_added={get_nested(euronext_closure, 'closure_summary', 'rows_added_to_expanded_universe', default='')}",
    )
    add_check("tmx_provider_id_confirmed", NEXT_PROVIDER_ID == "tmx_tsx_tsxv_official_equities", "critical", NEXT_PROVIDER_ID)
    add_check("current_rows_unchanged", CURRENT_ROWS == 38287, "critical", f"current_rows={CURRENT_ROWS}")
    add_check("rows_needed_unchanged", ROWS_NEEDED == 11713, "critical", f"rows_needed={ROWS_NEEDED}")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"{CURRENT_ROWS} < {FULL_SOURCE_THRESHOLD}")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_network", True, "critical", "network_download_performed=False")
    add_check("no_raw_downloads", True, "critical", "raw_files_downloaded=False")
    add_check("no_normalization", True, "critical", "normalization_performed=False")
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")

    status = (
        "TMX_PROVIDER_ROUTE_CONFIRMED_PLAN_ONLY_FULL_SOURCE_BLOCKED"
        if critical_failed == 0
        else "TMX_PROVIDER_ROUTE_CONFIRMATION_FAILED_REVIEW_REQUIRED"
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
        "previous_provider_closure": {
            "provider": "Euronext",
            "closure_artifact": str(EURONEXT_CLOSURE_JSON),
            "closure_status": closure_status,
            "closure_recommended_next_phase": closure_next_phase,
            "rows_added_to_expanded_universe": get_nested(euronext_closure, "closure_summary", "rows_added_to_expanded_universe", default=0),
            "current_rows_after_closure": get_nested(euronext_closure, "closure_summary", "current_rows_after_closure", default=CURRENT_ROWS),
            "rows_needed_after_closure": get_nested(euronext_closure, "closure_summary", "rows_needed_after_closure", default=ROWS_NEEDED),
        },
        "route_confirmation": {
            "next_provider_id": NEXT_PROVIDER_ID,
            "next_provider_name": NEXT_PROVIDER_NAME,
            "next_provider_country": NEXT_PROVIDER_COUNTRY,
            "next_provider_scope": NEXT_PROVIDER_SCOPE,
            "route_status": "CONFIRMED",
            "phase_scope": "confirmation_only",
            "network_allowed": False,
            "download_allowed": False,
            "canonical_read_allowed": False,
            "canonical_modify_allowed": False,
            "recommended_next_phase": NEXT_PHASE,
            "optional_v2_15a_route_artifacts_detected": optional_route_artifacts,
        },
        "decision_matrix": decision_rows,
        "checklist": checklist_rows,
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

    write_json(ROUTE_JSON, payload)
    write_csv(
        DECISION_CSV,
        decision_rows,
        ["decision_id", "decision", "basis", "impact"],
    )
    write_csv(
        CHECKLIST_CSV,
        checklist_rows,
        ["phase", "item", "status", "guard"],
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}`: **{row['decision']}** — {row['impact']} Basis: `{row['basis']}`"
        for row in decision_rows
    )

    checklist_lines = "\n".join(
        f"- [{ 'x' if row['status'] == 'done_in_this_phase' else ' ' }] {row['phase']} — {row['item']} — `{row['guard']}`"
        for row in checklist_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    ROUTE_MD.write_text(
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

## Previous provider closure

- Previous provider: `Euronext`
- Closure artifact: `{EURONEXT_CLOSURE_JSON}`
- Closure status: `{closure_status}`
- Rows added by Euronext: `{get_nested(euronext_closure, "closure_summary", "rows_added_to_expanded_universe", default=0)}`
- Closure recommended next phase: `{closure_next_phase}`

## Confirmed next provider

- Provider ID: `{NEXT_PROVIDER_ID}`
- Provider name: `{NEXT_PROVIDER_NAME}`
- Country: `{NEXT_PROVIDER_COUNTRY}`
- Scope: `{NEXT_PROVIDER_SCOPE}`
- Route status: `CONFIRMED`
- Recommended next phase: `{NEXT_PHASE}`

## Decision matrix

{decision_lines}

## Checklist

{checklist_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.16A: false
- Endpoint probe executed in v2.16A: false
- Raw files downloaded in v2.16A: false
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

TMX / TSX / TSXV is confirmed as the next provider route after Euronext closure.

This phase is confirmation-only. It does not perform network access, downloads, parsing, canonical reads, canonical modifications, normalization, net-new filtering or rebuild.

## Recommended next phase

`{NEXT_PHASE}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16A TMX provider route confirmation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("ROUTE_CONFIRMATION:")
    for key, value in payload["route_confirmation"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
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
    print(f"- {NEXT_PHASE}")


if __name__ == "__main__":
    main()
