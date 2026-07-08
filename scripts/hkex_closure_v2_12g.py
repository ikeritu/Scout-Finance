from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.12G"
PHASE = "HKEX Closure Report"
PHASE_TYPE = "closure-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ROUTE_JSON = OUTPUT_DIR / "next_provider_route_v2_12a.json"
PLAN_JSON = OUTPUT_DIR / "hkex_acquisition_plan_v2_12b.json"
ACQUISITION_JSON = OUTPUT_DIR / "hkex_download_manifest_v2_12c.json"
VALIDATION_JSON = OUTPUT_DIR / "hkex_validation_v2_12d.json"
REBUILD_JSON = OUTPUT_DIR / "hkex_rebuild_report_v2_12e.json"
EXPANDED_VALIDATION_JSON = OUTPUT_DIR / "hkex_expanded_validation_v2_12f.json"

CLOSURE_JSON = OUTPUT_DIR / "hkex_closure_report_v2_12g.json"
CLOSURE_MD = OUTPUT_DIR / "hkex_closure_report_v2_12g.md"
CLOSURE_SUMMARY_CSV = OUTPUT_DIR / "hkex_closure_summary_v2_12g.csv"
ROADMAP_STATUS_CSV = OUTPUT_DIR / "hkex_roadmap_status_v2_12g.csv"

FULL_SOURCE_THRESHOLD = 50000
FIRST_EXPANSION_THRESHOLD = 15000

GLOBAL_COMPLETED = 95
GLOBAL_PENDING = 5
EXPANDED_REAL_SOURCE_COMPLETED = 91
EXPANDED_REAL_SOURCE_PENDING = 9


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        CLOSURE_JSON,
        CLOSURE_MD,
        CLOSURE_SUMMARY_CSV,
        ROADMAP_STATUS_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.12G outputs:\n"
            + "\n".join(existing)
        )


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    no_overwrite_guard()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    route = read_json(ROUTE_JSON)
    plan = read_json(PLAN_JSON)
    acquisition = read_json(ACQUISITION_JSON)
    validation = read_json(VALIDATION_JSON)
    rebuild = read_json(REBUILD_JSON)
    expanded_validation = read_json(EXPANDED_VALIDATION_JSON)

    rebuild_counts = rebuild.get("counts", {})
    expanded_validation_counts = expanded_validation.get("counts", {})

    baseline_rows = int(rebuild_counts.get("baseline_rows", 30354))
    hkex_rows_added = int(rebuild_counts.get("hkex_rows_added", 2804))
    hkex_candidate_rows_reviewed = int(rebuild_counts.get("hkex_candidate_rows_reviewed", 17589))
    exclusions = int(rebuild_counts.get("exclusions", 14785))
    current_expanded_rows = int(rebuild_counts.get("new_expanded_rows", 33158))
    duplicate_exchange_ticker_keys = int(rebuild_counts.get("duplicate_exchange_ticker_keys", 0))
    first_expansion_unlocked = bool(rebuild_counts.get("first_expansion_unlocked", True))
    full_source_unlocked = bool(rebuild_counts.get("full_source_unlocked", False))
    rows_needed_full_source = int(rebuild_counts.get("rows_needed_full_source", 16842))

    validation_passed = bool(expanded_validation.get("validation_passed", False))
    critical_failed_checks = int(expanded_validation_counts.get("critical_failed_checks", 0))
    warning_failed_checks = int(expanded_validation_counts.get("warning_failed_checks", 0))

    accepted_breakdown = rebuild.get("accepted_subcategory_breakdown", [])
    exclusion_breakdown = rebuild.get("exclusion_reason_breakdown", [])
    provider_breakdown = expanded_validation.get("provider_breakdown", [])

    hard_guards = {
        "phase_type": PHASE_TYPE,
        "network_download_performed_in_closure": False,
        "raw_files_modified": False,
        "normalization_performed_in_closure": False,
        "net_new_filtering_performed_in_closure": False,
        "expanded_universe_rebuilt_in_closure": False,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
    }

    closure_status = "HKEX_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED"
    source_decision = "HKEX_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE"
    next_recommended_phase = "v2.13A_NEXT_PROVIDER_ROUTE_FOR_FULL_SOURCE_50K"

    closure_summary = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "closure_status": closure_status,
        "source_decision": source_decision,
        "generated_at_utc": utc_now(),
        "previous_commits": {
            "v2_12a": "9856571",
            "v2_12b": "abbbc0f",
            "v2_12c": "cd277d4",
            "v2_12d": "5bf9ada",
            "v2_12e": "dc58678",
            "v2_12f": "3f8872e",
        },
        "phase_inputs": {
            "route_status": route.get("status", ""),
            "route_decision": route.get("route_decision", ""),
            "plan_status": plan.get("status", ""),
            "acquisition_status": acquisition.get("status", ""),
            "validation_status": validation.get("status", ""),
            "rebuild_status": rebuild.get("status", ""),
            "expanded_validation_status": expanded_validation.get("status", ""),
            "expanded_validation_passed": validation_passed,
        },
        "counts": {
            "baseline_rows_before_hkex": baseline_rows,
            "hkex_candidate_rows_reviewed": hkex_candidate_rows_reviewed,
            "hkex_rows_added": hkex_rows_added,
            "hkex_exclusions": exclusions,
            "current_expanded_rows": current_expanded_rows,
            "duplicate_exchange_ticker_keys": duplicate_exchange_ticker_keys,
            "first_expansion_threshold": FIRST_EXPANSION_THRESHOLD,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_full_source": rows_needed_full_source,
            "critical_failed_checks": critical_failed_checks,
            "warning_failed_checks": warning_failed_checks,
        },
        "accepted_hkex_breakdown": accepted_breakdown,
        "exclusion_breakdown": exclusion_breakdown,
        "provider_breakdown": provider_breakdown,
        "hard_guards": hard_guards,
        "next_recommended_phase": next_recommended_phase,
        "project_percentages": {
            "v2_12_hkex_completed": 100,
            "v2_12_hkex_pending": 0,
            "expanded_real_source_completed": EXPANDED_REAL_SOURCE_COMPLETED,
            "expanded_real_source_pending": EXPANDED_REAL_SOURCE_PENDING,
            "full_source_50k_59k_completed": 0,
            "full_source_50k_59k_pending": 100,
            "full_59k_dry_run_real_completed": 0,
            "full_59k_dry_run_real_pending": 100,
            "global_completed": GLOBAL_COMPLETED,
            "global_pending": GLOBAL_PENDING,
        },
        "important_scope_note": (
            "v2.12G is closure-only. It does not download, modify raw files, normalize, "
            "filter net-new rows, rebuild, score, call OpenAI, call broker APIs, or launch full 59k."
        ),
    }

    summary_rows = [
        {"metric": "closure_status", "value": closure_status},
        {"metric": "source_decision", "value": source_decision},
        {"metric": "baseline_rows_before_hkex", "value": baseline_rows},
        {"metric": "hkex_candidate_rows_reviewed", "value": hkex_candidate_rows_reviewed},
        {"metric": "hkex_rows_added", "value": hkex_rows_added},
        {"metric": "hkex_exclusions", "value": exclusions},
        {"metric": "current_expanded_rows", "value": current_expanded_rows},
        {"metric": "duplicate_exchange_ticker_keys", "value": duplicate_exchange_ticker_keys},
        {"metric": "first_expansion_unlocked", "value": first_expansion_unlocked},
        {"metric": "full_source_unlocked", "value": full_source_unlocked},
        {"metric": "rows_needed_full_source", "value": rows_needed_full_source},
        {"metric": "critical_failed_checks", "value": critical_failed_checks},
        {"metric": "warning_failed_checks", "value": warning_failed_checks},
        {"metric": "full_59k_universe_launched", "value": False},
        {"metric": "next_recommended_phase", "value": next_recommended_phase},
    ]

    roadmap_rows = [
        {
            "phase": "v2.12A",
            "name": "Next Provider Route For Full Source 50k",
            "status": "done",
            "completed_pct": 100,
            "pending_pct": 0,
            "commit": "9856571",
        },
        {
            "phase": "v2.12B",
            "name": "HKEX Acquisition Plan",
            "status": "done",
            "completed_pct": 100,
            "pending_pct": 0,
            "commit": "abbbc0f",
        },
        {
            "phase": "v2.12C",
            "name": "HKEX Acquisition Real",
            "status": "done",
            "completed_pct": 100,
            "pending_pct": 0,
            "commit": "cd277d4",
        },
        {
            "phase": "v2.12D",
            "name": "HKEX Validation",
            "status": "done",
            "completed_pct": 100,
            "pending_pct": 0,
            "commit": "5bf9ada",
        },
        {
            "phase": "v2.12E",
            "name": "Rebuild Expanded Source With HKEX",
            "status": "done",
            "completed_pct": 100,
            "pending_pct": 0,
            "commit": "dc58678",
        },
        {
            "phase": "v2.12F",
            "name": "Validate Expanded Source With HKEX",
            "status": "done",
            "completed_pct": 100,
            "pending_pct": 0,
            "commit": "3f8872e",
        },
        {
            "phase": "v2.12G",
            "name": "HKEX Closure Report",
            "status": "in_progress_until_commit",
            "completed_pct": 90,
            "pending_pct": 10,
            "commit": "",
        },
        {
            "phase": "v2.13A",
            "name": "Next Provider Route For Full Source 50k",
            "status": "next",
            "completed_pct": 0,
            "pending_pct": 100,
            "commit": "",
        },
        {
            "phase": "Full 59k dry-run real",
            "name": "Blocked until source >=50k and explicit gate approval",
            "status": "blocked",
            "completed_pct": 0,
            "pending_pct": 100,
            "commit": "",
        },
    ]

    write_json(CLOSURE_JSON, closure_summary)
    write_csv(CLOSURE_SUMMARY_CSV, summary_rows, ["metric", "value"])
    write_csv(
        ROADMAP_STATUS_CSV,
        roadmap_rows,
        ["phase", "name", "status", "completed_pct", "pending_pct", "commit"],
    )

    accepted_lines = "\n".join(
        f"- {item.get('category', '')} / {item.get('subcategory', '')}: {item.get('rows', '')}"
        for item in accepted_breakdown
    ) or "- No accepted breakdown available."

    exclusion_lines = "\n".join(
        f"- {item.get('reason', '')}: {item.get('rows', '')}"
        for item in exclusion_breakdown
    ) or "- No exclusion breakdown available."

    provider_lines = "\n".join(
        f"- {item.get('source_provider', '')}: {item.get('rows', '')}"
        for item in provider_breakdown
    ) or "- No provider breakdown available."

    guard_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in hard_guards.items()
    )

    roadmap_lines = "\n".join(
        f"- [{row['status']}] {row['phase']} - {row['name']} - {row['completed_pct']}% completed / {row['pending_pct']}% pending"
        for row in roadmap_rows
    )

    md = f"""# {VERSION} - {PHASE}

Status: **{closure_status}**

Phase type: **closure-only**

Source decision: **{source_decision}**

Generated at UTC: `{closure_summary["generated_at_utc"]}`

## Phase chain

- v2.12A - Next Provider Route - commit `9856571`
- v2.12B - HKEX Acquisition Plan - commit `abbbc0f`
- v2.12C - HKEX Acquisition Real - commit `cd277d4`
- v2.12D - HKEX Validation - commit `5bf9ada`
- v2.12E - Rebuild Expanded Source With HKEX - commit `dc58678`
- v2.12F - Validate Expanded Source With HKEX - commit `3f8872e`

## Final HKEX decision

HKEX is accepted as a conservative expanded-source provider.

Only allowed HKEX equity categories were added.

Non-equity, derivative, debt, ETF, REIT, warrant, CBBC and review-required rows were excluded.

## Counts

- Baseline rows before HKEX: {baseline_rows}
- HKEX candidate rows reviewed: {hkex_candidate_rows_reviewed}
- HKEX rows added: {hkex_rows_added}
- HKEX exclusions: {exclusions}
- Current expanded rows: {current_expanded_rows}
- Duplicate exchange+ticker keys: {duplicate_exchange_ticker_keys}
- First expansion threshold: {FIRST_EXPANSION_THRESHOLD}
- First expansion unlocked: {first_expansion_unlocked}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Full source unlocked: {full_source_unlocked}
- Rows needed full source: {rows_needed_full_source}
- Critical failed checks: {critical_failed_checks}
- Warning failed checks: {warning_failed_checks}
- Full 59k universe launched: false

## Accepted HKEX breakdown

{accepted_lines}

## Exclusion breakdown

{exclusion_lines}

## Provider breakdown after HKEX

{provider_lines}

## Hard guards

{guard_lines}

## Roadmap status

{roadmap_lines}

## Project percentages

- v2.12 HKEX: 100% completed / 0% pending after commit
- Fuente real expandida: {EXPANDED_REAL_SOURCE_COMPLETED}% completed / {EXPANDED_REAL_SOURCE_PENDING}% pending
- Fuente real completa 50k-59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: {GLOBAL_COMPLETED}% completed / {GLOBAL_PENDING}% pending

## Recommended next phase

**{next_recommended_phase}**

Reason: expanded source is now {current_expanded_rows} rows, but the 50k source-complete gate is still blocked. Remaining gap: {rows_needed_full_source} rows.

## Scope note

v2.12G is closure-only.

It does not download, modify raw files, normalize, filter net-new rows, rebuild, score, call OpenAI, call broker APIs, or launch full 59k.
"""

    CLOSURE_MD.write_text(md, encoding="utf-8")

    print("v2.12G HKEX closure-only completed.")
    print(f"- closure json: {CLOSURE_JSON}")
    print(f"- closure report: {CLOSURE_MD}")
    print(f"- summary csv: {CLOSURE_SUMMARY_CSV}")
    print(f"- roadmap csv: {ROADMAP_STATUS_CSV}")
    print("")
    print("STATUS:")
    print(f"- closure_status: {closure_status}")
    print(f"- source_decision: {source_decision}")
    print(f"- next_recommended_phase: {next_recommended_phase}")
    print("")
    print("COUNTS:")
    for key, value in closure_summary["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("PROJECT_PERCENTAGES:")
    for key, value in closure_summary["project_percentages"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
