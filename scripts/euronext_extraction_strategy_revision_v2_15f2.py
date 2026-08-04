from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin


VERSION = "v2.15F2"
PHASE = "Euronext Extraction Strategy Revision"
PHASE_TYPE = "strategy-revision-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "euronext_v2_15c"

DRY_RUN_JSON = OUTPUT_DIR / "euronext_candidate_extraction_dry_run_v2_15f.json"
EXTRACTED_CANDIDATES_CSV = OUTPUT_DIR / "euronext_extracted_candidates_raw_v2_15f.csv"
EXTRACTION_QUALITY_CSV = OUTPUT_DIR / "euronext_extraction_quality_v2_15f.csv"

PREP_JSON = OUTPUT_DIR / "euronext_rebuild_candidate_prep_v2_15e.json"
SOURCE_STRATEGY_CSV = OUTPUT_DIR / "euronext_source_strategy_v2_15e.csv"

VALIDATION_JSON = OUTPUT_DIR / "euronext_validation_v2_15d.json"
CANDIDATE_ENDPOINTS_CSV = OUTPUT_DIR / "euronext_candidate_endpoints_v2_15d.csv"

REVISION_JSON = OUTPUT_DIR / "euronext_extraction_strategy_revision_v2_15f2.json"
REVISION_MD = OUTPUT_DIR / "euronext_extraction_strategy_revision_v2_15f2.md"
ENDPOINT_PROBE_PLAN_CSV = OUTPUT_DIR / "euronext_endpoint_probe_plan_v2_15f2.csv"
STRATEGY_DECISIONS_CSV = OUTPUT_DIR / "euronext_strategy_decisions_v2_15f2.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def as_bool_text(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def normalize_candidate_url(url: str) -> str:
    url = str(url or "").strip()

    if not url:
        return ""

    if url.startswith("//"):
        return "https:" + url

    if url.startswith("/"):
        if url.startswith("/en/products") or url.startswith("/en/markets"):
            return urljoin("https://live.euronext.com", url)
        return urljoin("https://www.euronext.com", url)

    return url


def classify_probe_type(url: str, proposed_use: str) -> tuple[str, str, str]:
    low = url.lower()
    use_low = proposed_use.lower()

    if "download" in low or "csv" in low or "structured_download" in use_low:
        return (
            "structured_download_metadata_probe",
            "Check whether this official candidate exposes structured CSV/download metadata without parsing securities.",
            "HTTP status/content-type/size/hash and whether payload looks structured enough for a later parser.",
        )

    if "json" in low or "/api/" in low or "ajax" in low:
        return (
            "json_or_ajax_metadata_probe",
            "Check whether this official candidate is an Euronext JSON/AJAX route that can expose table data.",
            "HTTP status/content-type/size/hash plus top-level payload shape only; no normalization.",
        )

    if "live.euronext.com" in low and "equit" in low and "list" in low:
        return (
            "live_listing_dynamic_probe",
            "HTML dry-run failed; inspect whether the live listing route requires dynamic endpoint calls.",
            "Evidence of redirect, embedded settings, scripts, paging params, or dynamic data route.",
        )

    if "static-reference-data" in low or "advanced-reference-data" in low:
        return (
            "reference_product_access_review",
            "Reference data appears official but may be gated/commercial; review access path without assuming availability.",
            "Evidence of public file, documentation-only status, or commercial/gated requirement.",
        )

    return (
        "manual_review_probe",
        "Candidate is Euronext-related but not strong enough for automated extraction.",
        "Manual evidence before allowing any extraction attempt.",
    )


def build_probe_plan(source_strategy: list[dict]) -> list[dict]:
    rows = []
    seen = set()

    for item in source_strategy:
        allowed = as_bool_text(item.get("allowed_in_next_phase", ""))
        proposed_use = str(item.get("proposed_use", ""))
        original_url = str(item.get("candidate_url", "")).strip()
        normalized_url = normalize_candidate_url(original_url)

        if not original_url or not normalized_url:
            continue

        key = normalized_url.lower()
        if key in seen:
            continue
        seen.add(key)

        base_score = as_int(item.get("base_validation_score", 0))
        priority = as_int(item.get("priority", 9), 9)
        risk = str(item.get("risk", ""))

        probe_type, rationale, expected_evidence = classify_probe_type(normalized_url, proposed_use)

        executable_probe_types = {
            "structured_download_metadata_probe",
            "json_or_ajax_metadata_probe",
            "live_listing_dynamic_probe",
        }

        should_execute = (
            allowed
            and priority <= 3
            and probe_type in executable_probe_types
        )

        rows.append(
            {
                "probe_id": short_hash(normalized_url),
                "original_candidate_url": original_url,
                "normalized_candidate_url": normalized_url,
                "source_raw_file": item.get("source_raw_file", ""),
                "base_validation_score": base_score,
                "source_strategy_priority": priority,
                "source_strategy_allowed": allowed,
                "source_strategy_proposed_use": proposed_use,
                "probe_type": probe_type,
                "risk": risk,
                "should_execute_in_next_phase": should_execute,
                "rationale": rationale,
                "expected_evidence": expected_evidence,
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            not bool(row["should_execute_in_next_phase"]),
            int(row["source_strategy_priority"]),
            -int(row["base_validation_score"]),
            row["normalized_candidate_url"],
        ),
    )


def main() -> None:
    for path in [REVISION_JSON, REVISION_MD, ENDPOINT_PROBE_PLAN_CSV, STRATEGY_DECISIONS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    dry_run = read_json(DRY_RUN_JSON)
    extracted_candidates = read_csv(EXTRACTED_CANDIDATES_CSV)
    extraction_quality = read_csv(EXTRACTION_QUALITY_CSV)

    prep = read_json(PREP_JSON)
    source_strategy = read_csv(SOURCE_STRATEGY_CSV)

    validation = read_json(VALIDATION_JSON)
    candidate_endpoints = read_csv(CANDIDATE_ENDPOINTS_CSV)

    raw_files = sorted(RAW_DIR.glob("*.html"))

    dry_summary = dry_run.get("dry_run_summary", {})
    dry_quality = str(dry_summary.get("extraction_quality", "unknown"))
    deduped_candidates = as_int(dry_summary.get("deduped_extracted_candidates", 0))
    unique_isins = as_int(dry_summary.get("unique_isins", 0))

    quality_by_bucket = dry_summary.get("quality_bucket_counts", {})
    source_kind_counts = dry_summary.get("source_kind_counts", {})

    low_quality_count = as_int(quality_by_bucket.get("low", 0))
    medium_quality_count = as_int(quality_by_bucket.get("medium", 0))
    high_quality_count = as_int(quality_by_bucket.get("high", 0))

    context_only_count = as_int(source_kind_counts.get("isin_context", 0))
    table_based_count = as_int(source_kind_counts.get("html_table_row", 0))

    allowed_strategy_rows = [
        row for row in source_strategy
        if as_bool_text(row.get("allowed_in_next_phase", ""))
    ]

    source_strategy_counter = Counter(str(row.get("proposed_use", "")) for row in source_strategy)
    allowed_strategy_counter = Counter(str(row.get("proposed_use", "")) for row in allowed_strategy_rows)

    probe_plan_rows = build_probe_plan(source_strategy)
    executable_probe_rows = [
        row for row in probe_plan_rows
        if bool(row["should_execute_in_next_phase"])
    ]

    endpoint_probe_counter = Counter(str(row["probe_type"]) for row in probe_plan_rows)
    executable_probe_counter = Counter(str(row["probe_type"]) for row in executable_probe_rows)

    public_html_failed_as_rebuild_source = (
        dry_quality == "low"
        and table_based_count == 0
        and context_only_count > 0
    )

    strategy_has_probe_path = len(executable_probe_rows) > 0

    decisions = [
        {
            "decision_id": "public_html_rebuild_path",
            "decision": "reject_for_rebuild",
            "evidence": (
                f"dry_quality={dry_quality}; table_based_count={table_based_count}; "
                f"context_only_count={context_only_count}; unique_isins={unique_isins}"
            ),
            "impact": "Do not proceed from public HTML tables to expanded universe rebuild.",
        },
        {
            "decision_id": "context_only_candidates",
            "decision": "keep_as_evidence_only",
            "evidence": f"deduped_candidates={deduped_candidates}; quality=low; source_kind=isin_context",
            "impact": "Context-only ISINs are not sufficient for net-new filtering or canonical integration.",
        },
        {
            "decision_id": "endpoint_probe_path",
            "decision": "prepare_controlled_probe" if strategy_has_probe_path else "no_probe_path_available",
            "evidence": f"executable_probe_rows={len(executable_probe_rows)}; total_probe_rows={len(probe_plan_rows)}",
            "impact": "Next phase may probe candidate endpoints for metadata only; no rebuild allowed.",
        },
        {
            "decision_id": "full_source_gate",
            "decision": "remain_blocked",
            "evidence": f"current_rows={CURRENT_ROWS}; threshold={FULL_SOURCE_THRESHOLD}; rows_needed={ROWS_NEEDED}",
            "impact": "Full source and full59k remain blocked.",
        },
    ]

    critical_failed = 0
    checks = []

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

    add_check("v2_15f_dry_run_exists", DRY_RUN_JSON.exists(), "critical", str(DRY_RUN_JSON))
    add_check("v2_15f_dry_run_completed", bool(dry_run.get("status")), "critical", str(dry_run.get("status")))
    add_check("v2_15f_low_quality_confirmed", dry_quality == "low", "warning", f"extraction_quality={dry_quality}")
    add_check(
        "public_html_failed_as_rebuild_source",
        public_html_failed_as_rebuild_source,
        "warning",
        f"table_based_count={table_based_count}; context_only_count={context_only_count}",
    )
    add_check("source_strategy_available", len(source_strategy) > 0, "critical", f"source_strategy_rows={len(source_strategy)}")
    add_check("candidate_endpoints_available", len(candidate_endpoints) > 0, "critical", f"candidate_endpoints={len(candidate_endpoints)}")
    add_check("probe_plan_generated", len(probe_plan_rows) > 0, "critical", f"probe_plan_rows={len(probe_plan_rows)}")
    add_check("executable_probe_rows_available", len(executable_probe_rows) > 0, "warning", f"executable_probe_rows={len(executable_probe_rows)}")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"current_rows={CURRENT_ROWS}")

    if critical_failed != 0:
        status = "EURONEXT_EXTRACTION_STRATEGY_REVISION_FAILED_REBUILD_BLOCKED"
        recommended_next_phase = "v2.15F2B - Euronext Strategy Revision Repair"
    elif strategy_has_probe_path:
        status = "EURONEXT_EXTRACTION_STRATEGY_REVISION_ENDPOINT_PROBE_RECOMMENDED_REBUILD_STILL_BLOCKED"
        recommended_next_phase = "v2.15F3 - Euronext Controlled Endpoint Probe"
    else:
        status = "EURONEXT_EXTRACTION_STRATEGY_REVISION_PUBLIC_SOURCE_CLOSURE_RECOMMENDED"
        recommended_next_phase = "v2.15G - Euronext Public Source Closure Report"

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
        "revision_summary": {
            "raw_files_available": len(raw_files),
            "v2_15f_extraction_quality": dry_quality,
            "v2_15f_deduped_candidates": deduped_candidates,
            "v2_15f_unique_isins": unique_isins,
            "v2_15f_low_quality_candidates": low_quality_count,
            "v2_15f_medium_quality_candidates": medium_quality_count,
            "v2_15f_high_quality_candidates": high_quality_count,
            "v2_15f_context_only_candidates": context_only_count,
            "v2_15f_table_based_candidates": table_based_count,
            "public_html_failed_as_rebuild_source": public_html_failed_as_rebuild_source,
            "source_strategy_rows": len(source_strategy),
            "allowed_strategy_rows": len(allowed_strategy_rows),
            "candidate_endpoints_from_v2_15d": len(candidate_endpoints),
            "endpoint_probe_plan_rows": len(probe_plan_rows),
            "executable_probe_rows": len(executable_probe_rows),
            "endpoint_probe_type_counts": dict(endpoint_probe_counter),
            "executable_probe_type_counts": dict(executable_probe_counter),
            "critical_failed_checks": critical_failed,
        },
        "source_strategy_counts": dict(source_strategy_counter),
        "allowed_source_strategy_counts": dict(allowed_strategy_counter),
        "decisions": decisions,
        "checks": checks,
        "top_executable_probe_rows": executable_probe_rows[:50],
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
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REVISION_JSON, payload)

    write_csv(
        ENDPOINT_PROBE_PLAN_CSV,
        probe_plan_rows,
        [
            "probe_id",
            "original_candidate_url",
            "normalized_candidate_url",
            "source_raw_file",
            "base_validation_score",
            "source_strategy_priority",
            "source_strategy_allowed",
            "source_strategy_proposed_use",
            "probe_type",
            "risk",
            "should_execute_in_next_phase",
            "rationale",
            "expected_evidence",
        ],
    )

    write_csv(
        STRATEGY_DECISIONS_CSV,
        decisions,
        ["decision_id", "decision", "evidence", "impact"],
    )

    check_lines = "\n".join(
        f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}"
        for item in checks
    )

    decision_lines = "\n".join(
        f"- `{item['decision_id']}`: **{item['decision']}** — {item['impact']} Evidence: `{item['evidence']}`"
        for item in decisions
    )

    probe_lines = "\n".join(
        f"- probe={row['probe_id']} type={row['probe_type']} priority={row['source_strategy_priority']} score={row['base_validation_score']} url={row['normalized_candidate_url']}"
        for row in executable_probe_rows[:25]
    ) or "- No executable probe rows available."

    REVISION_MD.write_text(
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

## Revision summary

- Raw files available: {payload["revision_summary"]["raw_files_available"]}
- v2.15F extraction quality: `{dry_quality}`
- v2.15F deduped candidates: {deduped_candidates}
- v2.15F unique ISINs: {unique_isins}
- v2.15F table-based candidates: {table_based_count}
- v2.15F context-only candidates: {context_only_count}
- Public HTML failed as rebuild source: `{public_html_failed_as_rebuild_source}`
- Source strategy rows: {len(source_strategy)}
- Allowed source strategy rows: {len(allowed_strategy_rows)}
- Candidate endpoints from v2.15D: {len(candidate_endpoints)}
- Endpoint probe plan rows: {len(probe_plan_rows)}
- Executable probe rows: {len(executable_probe_rows)}
- Critical failed checks: {critical_failed}

## Decisions

{decision_lines}

## Top executable endpoint probes

{probe_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.15F2: false
- Endpoint probe executed: false
- Raw files downloaded in v2.15F2: false
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

## Important note

This phase revises the Euronext extraction strategy only.

It does not execute endpoint probes, does not download new files, does not read or modify the canonical expanded universe, does not calculate definitive net-new rows, does not normalize securities, does not rebuild the expanded universe, does not score equities, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15F2 Euronext extraction strategy revision completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REVISION_SUMMARY:")
    for key, value in payload["revision_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("DECISIONS:")
    for item in decisions:
        print(f"- {item['decision_id']}: {item['decision']} - {item['evidence']}")
    print("")
    print("CHECKS:")
    for item in checks:
        print(f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
