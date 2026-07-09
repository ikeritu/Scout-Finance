from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.14G"
PHASE = "Deutsche Boerse Xetra Closure Report"
PHASE_TYPE = "closure-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

REBUILD_MANIFEST_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_rebuild_manifest_v2_14e.json"
VALIDATION_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_expanded_validation_v2_14f.json"
PROVIDER_BREAKDOWN_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_provider_breakdown_v2_14f.csv"

CLOSURE_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_closure_report_v2_14g.json"
CLOSURE_MD = OUTPUT_DIR / "deutsche_boerse_xetra_closure_report_v2_14g.md"
CLOSURE_SUMMARY_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_closure_summary_v2_14g.csv"

FULL_SOURCE_THRESHOLD = 50000
BASELINE_BEFORE_XETRA = 36863
GLOBAL_COMPLETED = 42
GLOBAL_PENDING = 58


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [CLOSURE_JSON, CLOSURE_MD, CLOSURE_SUMMARY_CSV]
    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.14G outputs:\n"
            + "\n".join(existing)
        )


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    no_overwrite_guard()

    rebuild = read_json(REBUILD_MANIFEST_JSON)
    validation = read_json(VALIDATION_JSON)
    provider_breakdown = read_csv(PROVIDER_BREAKDOWN_CSV)

    rebuild_counts = rebuild.get("counts", {})
    validation_counts = validation.get("counts", {})
    current_state = validation.get("current_state", {})

    expanded_rows = int(current_state.get("expanded_rows", rebuild_counts.get("expanded_rows", 38287)))
    xetra_rows_added = int(validation_counts.get("xetra_additions", rebuild_counts.get("xetra_rows_added", 1424)))
    xetra_rows_excluded = int(validation_counts.get("xetra_exclusions", rebuild_counts.get("xetra_rows_excluded", 3645)))
    duplicate_exchange_ticker_keys = int(validation_counts.get("duplicate_exchange_ticker_keys", 0))
    critical_failed_checks = int(validation_counts.get("critical_failed_checks", 0))
    warning_failed_checks = int(validation_counts.get("warning_failed_checks", 0))

    rows_needed_after_xetra = max(0, FULL_SOURCE_THRESHOLD - expanded_rows)
    source_to_50k_completed = round((expanded_rows / FULL_SOURCE_THRESHOLD) * 100, 1)
    source_to_50k_pending = round(100 - source_to_50k_completed, 1)

    full_source_unlocked = expanded_rows >= FULL_SOURCE_THRESHOLD

    closure_status = (
        "DEUTSCHE_BOERSE_XETRA_CLOSED_CONSERVATIVE_REBUILD_VALIDATED_FULL_SOURCE_BLOCKED"
        if critical_failed_checks == 0 and not full_source_unlocked
        else "DEUTSCHE_BOERSE_XETRA_CLOSURE_REQUIRES_REVIEW"
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "closure_status": closure_status,
        "generated_at_utc": utc_now(),
        "selected_provider": "deutsche_boerse_xetra_all_tradable_instruments",
        "source_decision": "DEUTSCHE_BOERSE_XETRA_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE",
        "current_state": {
            "baseline_before_xetra": BASELINE_BEFORE_XETRA,
            "xetra_rows_added": xetra_rows_added,
            "xetra_rows_excluded": xetra_rows_excluded,
            "expanded_after_xetra": expanded_rows,
            "expanded_delta": expanded_rows - BASELINE_BEFORE_XETRA,
            "duplicate_exchange_ticker_keys": duplicate_exchange_ticker_keys,
            "critical_failed_checks": critical_failed_checks,
            "warning_failed_checks": warning_failed_checks,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_after_xetra": rows_needed_after_xetra,
            "source_to_50k_completed_percent": source_to_50k_completed,
            "source_to_50k_pending_percent": source_to_50k_pending,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
        },
        "project_percentages": {
            "global_completed": GLOBAL_COMPLETED,
            "global_pending": GLOBAL_PENDING,
            "source_to_50k_completed": source_to_50k_completed,
            "source_to_50k_pending": source_to_50k_pending,
            "full_source_gate_completed": 0,
            "full_source_gate_pending": 100,
            "full_59k_dry_run_completed": 0,
            "full_59k_dry_run_pending": 100,
        },
        "provider_breakdown": provider_breakdown,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed": False,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "previous_phase_commit": "f3ccc8c",
        "recommended_next_phase": "v2.15A - Next Provider Route For Remaining Full Source Gap",
    }

    write_json(CLOSURE_JSON, payload)

    summary_rows = [
        {"metric": "closure_status", "value": closure_status},
        {"metric": "selected_provider", "value": "deutsche_boerse_xetra_all_tradable_instruments"},
        {"metric": "source_decision", "value": "DEUTSCHE_BOERSE_XETRA_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE"},
        {"metric": "baseline_before_xetra", "value": BASELINE_BEFORE_XETRA},
        {"metric": "xetra_rows_added", "value": xetra_rows_added},
        {"metric": "xetra_rows_excluded", "value": xetra_rows_excluded},
        {"metric": "expanded_after_xetra", "value": expanded_rows},
        {"metric": "duplicate_exchange_ticker_keys", "value": duplicate_exchange_ticker_keys},
        {"metric": "critical_failed_checks", "value": critical_failed_checks},
        {"metric": "warning_failed_checks", "value": warning_failed_checks},
        {"metric": "source_to_50k_completed_percent", "value": source_to_50k_completed},
        {"metric": "source_to_50k_pending_percent", "value": source_to_50k_pending},
        {"metric": "rows_needed_after_xetra", "value": rows_needed_after_xetra},
        {"metric": "global_completed", "value": GLOBAL_COMPLETED},
        {"metric": "global_pending", "value": GLOBAL_PENDING},
        {"metric": "full_source_unlocked", "value": str(full_source_unlocked)},
        {"metric": "full_59k_status", "value": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED"},
        {"metric": "recommended_next_phase", "value": "v2.15A - Next Provider Route For Remaining Full Source Gap"},
    ]

    write_csv(CLOSURE_SUMMARY_CSV, summary_rows, ["metric", "value"])

    provider_lines = "\n".join(
        f"- {row.get('provider', '')}: {row.get('rows', '')}"
        for row in provider_breakdown
    )

    CLOSURE_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{closure_status}**

Phase type: **closure-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `{payload["generated_at_utc"]}`

## Decision

- Source decision: **DEUTSCHE_BOERSE_XETRA_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE**
- Full source unlocked: **{str(full_source_unlocked).lower()}**
- Full 59k: **blocked**
- Recommended next phase: **v2.15A - Next Provider Route For Remaining Full Source Gap**

## Final Xetra outcome

- Baseline before Xetra: {BASELINE_BEFORE_XETRA}
- Xetra rows added: {xetra_rows_added}
- Xetra rows excluded: {xetra_rows_excluded}
- Expanded after Xetra: {expanded_rows}
- Expanded delta: {expanded_rows - BASELINE_BEFORE_XETRA}
- Duplicate exchange+ticker keys: {duplicate_exchange_ticker_keys}
- Critical failed checks: {critical_failed_checks}
- Warning failed checks: {warning_failed_checks}

## Source progress

- Source-to-50k completed: {source_to_50k_completed}%
- Source-to-50k pending: {source_to_50k_pending}%
- Rows needed after Xetra: {rows_needed_after_xetra}

## Project percentages

- GLOBAL corrected: {GLOBAL_COMPLETED}% completed / {GLOBAL_PENDING}% pending
- Source to 50k: {source_to_50k_completed}% completed / {source_to_50k_pending}% pending
- Full source gate: 0% completed / 100% pending
- Full 59k dry-run: 0% completed / 100% pending

## Provider breakdown

{provider_lines}

## Guards

- Network download performed in v2.14G: false
- Raw files downloaded in v2.14G: false
- Raw files modified after write: false
- Workbook/CSV parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase closes Deutsche Börse/Xetra only. It does not modify the expanded universe.
""",
        encoding="utf-8",
    )

    print("v2.14G Deutsche Boerse Xetra closure-only completed.")
    print(f"- closure json: {CLOSURE_JSON}")
    print(f"- closure report: {CLOSURE_MD}")
    print(f"- closure summary csv: {CLOSURE_SUMMARY_CSV}")
    print("")
    print("DECISION:")
    print(f"- closure_status: {closure_status}")
    print("- source_decision: DEUTSCHE_BOERSE_XETRA_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE")
    print("- recommended_next_phase: v2.15A - Next Provider Route For Remaining Full Source Gap")
    print("")
    print("COUNTS:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("PERCENTAGES:")
    for key, value in payload["project_percentages"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
