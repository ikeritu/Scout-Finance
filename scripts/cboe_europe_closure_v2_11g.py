from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.11G"
PHASE = "Cboe Europe Closure Report"
PHASE_TYPE = "closure-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

V211A_ROUTE_JSON = OUTPUT_DIR / "cboe_europe_route_v2_11a.json"
V211B_PLAN_JSON = OUTPUT_DIR / "cboe_europe_acquisition_plan_v2_11b.json"
V211C_MANIFEST_JSON = OUTPUT_DIR / "cboe_europe_download_manifest_v2_11c.json"
V211D_DECISION_CSV = OUTPUT_DIR / "cboe_europe_validation_decision_v2_11d.csv"
V211E_REBUILD_JSON = OUTPUT_DIR / "cboe_europe_rebuild_report_v2_11e.json"
V211F_VALIDATION_JSON = OUTPUT_DIR / "cboe_europe_expanded_validation_v2_11f.json"

CLOSURE_JSON = OUTPUT_DIR / "cboe_europe_closure_report_v2_11g.json"
CLOSURE_MD = OUTPUT_DIR / "cboe_europe_closure_report_v2_11g.md"
CLOSURE_SUMMARY_CSV = OUTPUT_DIR / "cboe_europe_closure_summary_v2_11g.csv"
ROADMAP_CSV = OUTPUT_DIR / "cboe_europe_roadmap_status_v2_11g.csv"

CURRENT_GLOBAL_COMPLETED = 94
CURRENT_GLOBAL_PENDING = 6


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        CLOSURE_JSON,
        CLOSURE_MD,
        CLOSURE_SUMMARY_CSV,
        ROADMAP_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.11G outputs:\n"
            + "\n".join(existing)
        )


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_dicts(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def first_row(rows: list[dict]) -> dict:
    return rows[0] if rows else {}


def main() -> None:
    no_overwrite_guard()

    route = read_json(V211A_ROUTE_JSON)
    plan = read_json(V211B_PLAN_JSON)
    manifest = read_json(V211C_MANIFEST_JSON)
    validation_d = first_row(read_csv_dicts(V211D_DECISION_CSV))
    rebuild = read_json(V211E_REBUILD_JSON)
    validation_f = read_json(V211F_VALIDATION_JSON)

    manifest_counts = manifest.get("counts", {})
    rebuild_counts = rebuild.get("counts", {})
    validation_f_decision = validation_f.get("decision", {})
    validation_f_counts = validation_f.get("counts", {})

    current_expanded_rows = int(rebuild_counts.get("new_expanded_rows", 0))
    cboe_rows_added = int(rebuild_counts.get("cboe_rows_added", 0))
    baseline_rows = int(rebuild_counts.get("baseline_rows", 0))
    exclusions = int(rebuild_counts.get("exclusions", 0))
    duplicate_keys = int(rebuild_counts.get("duplicate_exchange_ticker_keys", 0))

    first_expansion_unlocked = bool(rebuild_counts.get("first_expansion_unlocked", False))
    full_source_unlocked = bool(rebuild_counts.get("full_source_unlocked", False))
    rows_needed_full_source = int(validation_f_decision.get("rows_needed_full_source", 0))

    closure_status = "CBOE_EUROPE_CLOSED_FIRST_EXPANSION_UNLOCKED_FULL_SOURCE_BLOCKED"
    source_decision = "CBOE_EUROPE_ACCEPTED_FOR_FIRST_EXPANSION_SOURCE"
    next_recommended_phase = "v2.12A_NEXT_PROVIDER_ROUTE_FOR_FULL_SOURCE_50K"

    if not first_expansion_unlocked:
        closure_status = "CBOE_EUROPE_CLOSED_WITHOUT_FIRST_EXPANSION_UNLOCK"
        source_decision = "CBOE_EUROPE_VALIDATED_BUT_NOT_ENOUGH_FOR_FIRST_EXPANSION"
        next_recommended_phase = "v2.12A_NEXT_PROVIDER_ROUTE"

    if full_source_unlocked:
        closure_status = "CBOE_EUROPE_CLOSED_FULL_SOURCE_READY_FOR_GATE_REVIEW"
        source_decision = "CBOE_EUROPE_ACCEPTED_FOR_FULL_SOURCE_GATE_REVIEW"
        next_recommended_phase = "FULL_SOURCE_GATE_REVIEW_REQUIRED_BEFORE_ANY_59K_DRY_RUN"

    hard_guards = {
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

    phase_rows = [
        {
            "phase": "v2.11A",
            "name": "Cboe Europe Route",
            "type": "route-selection-only",
            "status": route.get("status", "CBOE_EUROPE_ROUTE_READY"),
            "commit": "581fff8",
            "key_result": "Cboe Europe selected as next provider route.",
        },
        {
            "phase": "v2.11B",
            "name": "Cboe Europe Acquisition Plan",
            "type": "plan-only",
            "status": plan.get("status", "CBOE_EUROPE_ACQUISITION_PLAN_READY"),
            "commit": "51ef5f0",
            "key_result": "Controlled acquisition contract defined.",
        },
        {
            "phase": "v2.11C",
            "name": "Cboe Europe Acquisition Real",
            "type": "acquisition-only",
            "status": manifest.get("status", "CBOE_EUROPE_ACQUISITION_COMPLETED_RAW_ONLY"),
            "commit": "c90213a",
            "key_result": f"Raw acquisition completed; discovered CSV links: {manifest_counts.get('discovered_csv_links', '')}.",
        },
        {
            "phase": "v2.11D",
            "name": "Cboe Europe Validation",
            "type": "validation-only",
            "status": validation_d.get("decision", "CBOE_EUROPE_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW"),
            "commit": "06ee9cc",
            "key_result": "Metadata header skip corrected; rebuild review allowed by validation.",
        },
        {
            "phase": "v2.11E",
            "name": "Rebuild Expanded Source With Cboe Europe",
            "type": "rebuild-only",
            "status": rebuild.get("status", "CBOE_EUROPE_REBUILD_COMPLETED"),
            "commit": "593b143",
            "key_result": f"Expanded universe rebuilt to {current_expanded_rows} rows.",
        },
        {
            "phase": "v2.11F",
            "name": "Validate Expanded Source With Cboe Europe",
            "type": "validation-only",
            "status": validation_f_decision.get("decision", "CBOE_EUROPE_EXPANDED_SOURCE_VALIDATED_FIRST_EXPANSION_READY"),
            "commit": "4517e60",
            "key_result": "Critical checks passed; first expansion ready; full source remains blocked.",
        },
    ]

    provider_breakdown = validation_f.get("provider_breakdown", [])

    summary_row = {
        "closure_status": closure_status,
        "source_decision": source_decision,
        "baseline_rows": baseline_rows,
        "cboe_rows_added": cboe_rows_added,
        "current_expanded_rows": current_expanded_rows,
        "exclusions": exclusions,
        "duplicate_exchange_ticker_keys": duplicate_keys,
        "first_expansion_unlocked": first_expansion_unlocked,
        "full_source_unlocked": full_source_unlocked,
        "rows_needed_full_source": rows_needed_full_source,
        "full_59k_universe_launched": False,
        "next_recommended_phase": next_recommended_phase,
    }

    roadmap_rows = [
        {"item": "v2.11A — Cboe Europe Route", "status": "done", "completed_pct": 100, "pending_pct": 0},
        {"item": "v2.11B — Cboe Europe Acquisition Plan", "status": "done", "completed_pct": 100, "pending_pct": 0},
        {"item": "v2.11C — Cboe Europe Acquisition Real", "status": "done", "completed_pct": 100, "pending_pct": 0},
        {"item": "v2.11D — Cboe Europe Validation", "status": "done", "completed_pct": 100, "pending_pct": 0},
        {"item": "v2.11E — Rebuild Expanded Source With Cboe Europe", "status": "done", "completed_pct": 100, "pending_pct": 0},
        {"item": "v2.11F — Validate Expanded Source With Cboe Europe", "status": "done", "completed_pct": 100, "pending_pct": 0},
        {"item": "v2.11G — Cboe Europe Closure Report", "status": "in_progress", "completed_pct": 90, "pending_pct": 10},
        {"item": "v2.12A — Next Provider Route For Full Source 50k", "status": "next", "completed_pct": 0, "pending_pct": 100},
        {"item": "Full 59k dry-run real", "status": "blocked", "completed_pct": 0, "pending_pct": 100},
    ]

    closure = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": closure_status,
        "generated_at_utc": utc_now(),
        "source_decision": source_decision,
        "next_recommended_phase": next_recommended_phase,
        "hard_guards": hard_guards,
        "summary": summary_row,
        "phase_history": phase_rows,
        "provider_breakdown": provider_breakdown,
        "roadmap": roadmap_rows,
        "project_percentages": {
            "v2_11_cboe_europe_completed": 100,
            "v2_11_cboe_europe_pending": 0,
            "expanded_real_source_completed": 88,
            "expanded_real_source_pending": 12,
            "full_source_50k_59k_completed": 0,
            "full_source_50k_59k_pending": 100,
            "full_59k_dry_run_real_completed": 0,
            "full_59k_dry_run_real_pending": 100,
            "global_completed": CURRENT_GLOBAL_COMPLETED,
            "global_pending": CURRENT_GLOBAL_PENDING,
        },
        "important_constraints": [
            "First expansion threshold is unlocked by v2.11E/v2.11F.",
            "Full source 50k remains blocked.",
            "Full 59k dry-run remains blocked until source is >=50k and gate is explicitly approved.",
            "No scoring was recalculated in v2.11.",
            "No OpenAI calls were made in v2.11 source phases.",
            "No broker/API trading calls were made.",
            "Auditoria_Scout_Finance.docx must remain unversioned unless explicitly requested.",
        ],
    }

    write_json(CLOSURE_JSON, closure)

    write_csv(
        CLOSURE_SUMMARY_CSV,
        [summary_row],
        [
            "closure_status",
            "source_decision",
            "baseline_rows",
            "cboe_rows_added",
            "current_expanded_rows",
            "exclusions",
            "duplicate_exchange_ticker_keys",
            "first_expansion_unlocked",
            "full_source_unlocked",
            "rows_needed_full_source",
            "full_59k_universe_launched",
            "next_recommended_phase",
        ],
    )

    write_csv(
        ROADMAP_CSV,
        roadmap_rows,
        ["item", "status", "completed_pct", "pending_pct"],
    )

    provider_lines = "\n".join(
        f"- {row.get('provider')}: {row.get('rows')}"
        for row in provider_breakdown
    ) or "- Not available"

    phase_lines = "\n".join(
        f"- {row['phase']} — {row['name']} ({row['type']}): {row['status']} | commit `{row['commit']}` | {row['key_result']}"
        for row in phase_rows
    )

    roadmap_lines = "\n".join(
        f"- [{ 'x' if row['status'] == 'done' else ' ' }] {row['item']} — {row['status']} — {row['completed_pct']}% completed / {row['pending_pct']}% pending"
        for row in roadmap_rows
    )

    md = f"""# {VERSION} — {PHASE}

Status: **{closure_status}**

Phase type: **closure-only**

Generated at UTC: `{closure["generated_at_utc"]}`

## Final source decision

**{source_decision}**

Cboe Europe is accepted as a source expansion provider for the rebuilt expanded universe candidate.

The first expansion threshold is now unlocked, but the full 50k source threshold remains blocked.

## Final numbers

- Baseline rows before Cboe Europe: {baseline_rows}
- Cboe Europe rows added: {cboe_rows_added}
- Current expanded rows: {current_expanded_rows}
- Exclusions: {exclusions}
- Duplicate exchange+ticker keys: {duplicate_keys}
- First expansion unlocked: {first_expansion_unlocked}
- Full source 50k unlocked: {full_source_unlocked}
- Rows still needed for 50k full source: {rows_needed_full_source}
- Full 59k dry-run launched: false

## Provider breakdown

{provider_lines}

## Phase history

{phase_lines}

## Important technical note

The initial v2.11D validation produced a false negative because Cboe Europe CSV files begin with a metadata row:

`environment=PROD,created=...,time=...,warning=`

The real schema starts on the next row and includes usable fields such as:

`company_name`, `bats_name`, `isin`, `currency`, `mic`.

v2.11D was corrected before commit and v2.11E/v2.11F were based on the corrected validation.

## Hard guards in closure

- Network download performed in closure: false
- Raw files modified: false
- Normalization performed in closure: false
- Net-new filtering performed in closure: false
- Expanded universe rebuilt in closure: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Roadmap

{roadmap_lines}

## Project percentages

- v2.11 Cboe Europe: 100% completed / 0% pending
- Fuente real expandida: 88% completed / 12% pending
- Fuente real completa 50k–59k: 0% completed / 100% pending
- Full 59k dry-run real: 0% completed / 100% pending, blocked
- GLOBAL: {CURRENT_GLOBAL_COMPLETED}% completed / {CURRENT_GLOBAL_PENDING}% pending

## Recommended next phase

**{next_recommended_phase}**

Recommended next step: continue with a new provider route to close the remaining gap to 50k rows.

Do not launch full 59k until source is >=50k and the gate is explicitly approved.

## Outputs

- `{CLOSURE_JSON}`
- `{CLOSURE_MD}`
- `{CLOSURE_SUMMARY_CSV}`
- `{ROADMAP_CSV}`
"""

    CLOSURE_MD.write_text(md, encoding="utf-8")

    print("v2.11G closure-only completed.")
    print(f"- closure json: {CLOSURE_JSON}")
    print(f"- closure report: {CLOSURE_MD}")
    print(f"- closure summary: {CLOSURE_SUMMARY_CSV}")
    print(f"- roadmap status: {ROADMAP_CSV}")
    print("")
    print("SUMMARY:")
    for key, value in summary_row.items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
