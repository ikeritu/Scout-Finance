from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.13G"
PHASE = "JPX Closure Report"
PHASE_TYPE = "closure-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

VALIDATION_D_JSON = OUTPUT_DIR / "jpx_validation_v2_13d.json"
REBUILD_E_JSON = OUTPUT_DIR / "jpx_rebuild_summary_v2_13e.json"
VALIDATION_F_JSON = OUTPUT_DIR / "jpx_expanded_validation_v2_13f.json"

CLOSURE_JSON = OUTPUT_DIR / "jpx_closure_report_v2_13g.json"
CLOSURE_MD = OUTPUT_DIR / "jpx_closure_report_v2_13g.md"
CLOSURE_DECISION_CSV = OUTPUT_DIR / "jpx_closure_decision_v2_13g.csv"
ROADMAP_CSV = OUTPUT_DIR / "jpx_post_closure_roadmap_v2_13g.csv"

BASELINE_BEFORE_JPX = 33158
JPX_ROWS_ADDED = 3705
JPX_ROWS_EXCLUDED = 732
EXPANDED_AFTER_JPX = 36863
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_AFTER_JPX = 13137

GLOBAL_COMPLETED = 96
GLOBAL_PENDING = 4
EXPANDED_SOURCE_COMPLETED = 93
EXPANDED_SOURCE_PENDING = 7


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        CLOSURE_JSON,
        CLOSURE_MD,
        CLOSURE_DECISION_CSV,
        ROADMAP_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.13G outputs:\n"
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

    validation_d = read_json(VALIDATION_D_JSON)
    rebuild_e = read_json(REBUILD_E_JSON)
    validation_f = read_json(VALIDATION_F_JSON)

    closure_status = "JPX_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED"
    source_decision = "JPX_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE"
    recommended_next_phase = "v2.14A - Next Provider Route For Remaining Full Source Gap"

    hard_guards = {
        "phase_type": PHASE_TYPE,
        "network_download_performed": False,
        "raw_files_downloaded": False,
        "raw_files_modified": False,
        "workbook_or_csv_parsed": False,
        "normalization_performed": False,
        "net_new_filtering_performed": False,
        "expanded_universe_rebuilt": False,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
    }

    critical_checks = {
        "v2_13d_validation_passed": validation_d.get("rebuild_allowed_by_validation") is True,
        "v2_13e_rebuild_completed": rebuild_e.get("status") == "JPX_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED",
        "v2_13f_validation_passed": validation_f.get("status") == "JPX_EXPANDED_VALIDATION_PASSED_FULL_SOURCE_STILL_BLOCKED",
        "expanded_rows_match_expected": validation_f.get("counts", {}).get("expanded_rows") == EXPANDED_AFTER_JPX,
        "duplicate_exchange_ticker_keys_zero": validation_f.get("counts", {}).get("duplicate_exchange_ticker_keys") == 0,
        "critical_failed_checks_zero": validation_f.get("counts", {}).get("critical_failed_checks") == 0,
        "warning_failed_checks_zero": validation_f.get("counts", {}).get("warning_failed_checks") == 0,
        "full_source_unlocked_false": validation_f.get("counts", {}).get("full_source_unlocked") is False,
        "full_59k_universe_not_launched": validation_f.get("counts", {}).get("full_59k_universe_launched") is False,
    }

    all_checks_passed = all(critical_checks.values())

    if not all_checks_passed:
        closure_status = "JPX_CLOSURE_REVIEW_REQUIRED"

    decision_row = {
        "version": VERSION,
        "phase_type": PHASE_TYPE,
        "closure_status": closure_status,
        "source_decision": source_decision if all_checks_passed else "JPX_CLOSURE_REVIEW_REQUIRED",
        "baseline_before_jpx": BASELINE_BEFORE_JPX,
        "jpx_rows_added": JPX_ROWS_ADDED,
        "jpx_rows_excluded": JPX_ROWS_EXCLUDED,
        "expanded_after_jpx": EXPANDED_AFTER_JPX,
        "duplicate_exchange_ticker_keys": validation_f.get("counts", {}).get("duplicate_exchange_ticker_keys"),
        "critical_failed_checks": validation_f.get("counts", {}).get("critical_failed_checks"),
        "warning_failed_checks": validation_f.get("counts", {}).get("warning_failed_checks"),
        "full_source_threshold": FULL_SOURCE_THRESHOLD,
        "full_source_unlocked": False,
        "rows_needed_after_jpx": ROWS_NEEDED_AFTER_JPX,
        "full_59k_universe_launched": False,
        "recommended_next_phase": recommended_next_phase,
    }

    roadmap_rows = [
        {
            "phase": "v2.13A",
            "name": "Next Provider Route For Full Source 50k",
            "status": "closed",
            "commit": "642de26",
        },
        {
            "phase": "v2.13B",
            "name": "JPX Acquisition Plan",
            "status": "closed",
            "commit": "28ba59f",
        },
        {
            "phase": "v2.13C",
            "name": "JPX Acquisition Real",
            "status": "closed",
            "commit": "2348a84",
        },
        {
            "phase": "v2.13D",
            "name": "JPX Validation",
            "status": "closed",
            "commit": "51e66dd",
        },
        {
            "phase": "v2.13E",
            "name": "Rebuild Expanded Source With JPX",
            "status": "closed",
            "commit": "feaa354",
        },
        {
            "phase": "v2.13F",
            "name": "Validate Expanded Source With JPX",
            "status": "closed",
            "commit": "6c680ca",
        },
        {
            "phase": "v2.13G",
            "name": "JPX Closure Report",
            "status": "ready_to_commit_after_validation",
            "commit": "",
        },
        {
            "phase": "v2.14A",
            "name": "Next Provider Route For Remaining Full Source Gap",
            "status": "recommended_next",
            "commit": "",
        },
    ]

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "closure_status": closure_status,
        "source_decision": source_decision if all_checks_passed else "JPX_CLOSURE_REVIEW_REQUIRED",
        "generated_at_utc": utc_now(),
        "hard_guards": hard_guards,
        "critical_checks": critical_checks,
        "counts": {
            "baseline_before_jpx": BASELINE_BEFORE_JPX,
            "jpx_rows_added": JPX_ROWS_ADDED,
            "jpx_rows_excluded": JPX_ROWS_EXCLUDED,
            "expanded_after_jpx": EXPANDED_AFTER_JPX,
            "duplicate_exchange_ticker_keys": validation_f.get("counts", {}).get("duplicate_exchange_ticker_keys"),
            "critical_failed_checks": validation_f.get("counts", {}).get("critical_failed_checks"),
            "warning_failed_checks": validation_f.get("counts", {}).get("warning_failed_checks"),
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "full_source_unlocked": False,
            "rows_needed_after_jpx": ROWS_NEEDED_AFTER_JPX,
            "full_59k_universe_launched": False,
        },
        "accepted_jpx_breakdown": rebuild_e.get("accepted_by_market_segment", {}),
        "excluded_jpx_breakdown": rebuild_e.get("excluded_by_reason", {}),
        "provider_breakdown": validation_f.get("provider_breakdown", []),
        "project_percentages": {
            "v2_13_jpx_completed_after_commit": 100,
            "v2_13_jpx_pending_after_commit": 0,
            "expanded_real_source_completed": EXPANDED_SOURCE_COMPLETED,
            "expanded_real_source_pending": EXPANDED_SOURCE_PENDING,
            "full_source_50k_59k_completed": 0,
            "full_source_50k_59k_pending": 100,
            "full_59k_dry_run_completed": 0,
            "full_59k_dry_run_pending": 100,
            "global_completed": GLOBAL_COMPLETED,
            "global_pending": GLOBAL_PENDING,
        },
        "decision": decision_row,
        "roadmap": roadmap_rows,
        "recommended_next_phase": recommended_next_phase,
        "scope_note": (
            "v2.13G is closure-only. It summarizes already validated JPX phases and does not "
            "download, parse raw workbooks, normalize, filter net-new rows, rebuild, score, call OpenAI, "
            "call broker APIs or launch full 59k."
        ),
    }

    write_json(CLOSURE_JSON, payload)

    write_csv(
        CLOSURE_DECISION_CSV,
        [decision_row],
        [
            "version",
            "phase_type",
            "closure_status",
            "source_decision",
            "baseline_before_jpx",
            "jpx_rows_added",
            "jpx_rows_excluded",
            "expanded_after_jpx",
            "duplicate_exchange_ticker_keys",
            "critical_failed_checks",
            "warning_failed_checks",
            "full_source_threshold",
            "full_source_unlocked",
            "rows_needed_after_jpx",
            "full_59k_universe_launched",
            "recommended_next_phase",
        ],
    )

    write_csv(
        ROADMAP_CSV,
        roadmap_rows,
        ["phase", "name", "status", "commit"],
    )

    check_lines = "\n".join(
        f"- {key}: {value}" for key, value in critical_checks.items()
    )

    guard_lines = "\n".join(
        f"- {key}: {value}" for key, value in hard_guards.items()
    )

    provider_lines = "\n".join(
        f"- {row.get('provider')}: {row.get('rows')}"
        for row in validation_f.get("provider_breakdown", [])
    )

    accepted_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in rebuild_e.get("accepted_by_market_segment", {}).items()
    )

    excluded_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in rebuild_e.get("excluded_by_reason", {}).items()
    )

    md = f"""# {VERSION} - {PHASE}

Status: **{closure_status}**

Phase type: **closure-only**

Generated at UTC: `{payload["generated_at_utc"]}`

## Final decision

- Source decision: **{payload["source_decision"]}**
- Recommended next phase: **{recommended_next_phase}**
- Full source unlocked: **false**
- Full 59k universe launched: **false**

## JPX final counts

- Baseline before JPX: {BASELINE_BEFORE_JPX}
- JPX rows added: {JPX_ROWS_ADDED}
- JPX rows excluded: {JPX_ROWS_EXCLUDED}
- Expanded rows after JPX: {EXPANDED_AFTER_JPX}
- Duplicate exchange+ticker keys: {decision_row["duplicate_exchange_ticker_keys"]}
- Critical failed checks: {decision_row["critical_failed_checks"]}
- Warning failed checks: {decision_row["warning_failed_checks"]}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Rows needed after JPX: {ROWS_NEEDED_AFTER_JPX}

## Accepted JPX rows

{accepted_lines}

## Excluded JPX rows

{excluded_lines}

## Provider breakdown after JPX

{provider_lines}

## Critical checks

{check_lines}

## Hard guards

{guard_lines}

## Project percentages after v2.13G commit

- v2.13 JPX block: 100% completed / 0% pending
- Fuente real expandida: {EXPANDED_SOURCE_COMPLETED}% completed / {EXPANDED_SOURCE_PENDING}% pending
- Fuente real completa 50k-59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: {GLOBAL_COMPLETED}% completed / {GLOBAL_PENDING}% pending

## Closure summary

JPX is accepted as a conservative expanded-source provider.

The expanded universe increased from **33,158** to **36,863** rows.

The 50k full-source gate remains blocked because **13,137** additional rows are still needed.

Full 59k dry-run remains blocked until source is complete and an explicit gate is approved.

## Outputs

- `{CLOSURE_JSON}`
- `{CLOSURE_MD}`
- `{CLOSURE_DECISION_CSV}`
- `{ROADMAP_CSV}`
"""

    CLOSURE_MD.write_text(md, encoding="utf-8")

    print("v2.13G JPX closure-only completed.")
    print(f"- closure json: {CLOSURE_JSON}")
    print(f"- closure report: {CLOSURE_MD}")
    print(f"- closure decision csv: {CLOSURE_DECISION_CSV}")
    print(f"- post-closure roadmap csv: {ROADMAP_CSV}")
    print("")
    print("DECISION:")
    print(f"- closure_status: {closure_status}")
    print(f"- source_decision: {payload['source_decision']}")
    print(f"- recommended_next_phase: {recommended_next_phase}")
    print("")
    print("COUNTS:")
    for key, value in payload["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
