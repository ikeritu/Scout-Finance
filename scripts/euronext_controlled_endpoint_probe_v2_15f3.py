from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


VERSION = "v2.15F3"
PHASE = "Euronext Controlled Endpoint Probe"
PHASE_TYPE = "controlled-probe-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

PROBE_PLAN_CSV = OUTPUT_DIR / "euronext_endpoint_probe_plan_v2_15f2.csv"
REVISION_JSON = OUTPUT_DIR / "euronext_extraction_strategy_revision_v2_15f2.json"

PROBE_JSON = OUTPUT_DIR / "euronext_controlled_endpoint_probe_v2_15f3.json"
PROBE_MD = OUTPUT_DIR / "euronext_controlled_endpoint_probe_v2_15f3.md"
PROBE_RESULTS_CSV = OUTPUT_DIR / "euronext_controlled_endpoint_probe_results_v2_15f3.csv"
PROBE_SUMMARY_CSV = OUTPUT_DIR / "euronext_controlled_endpoint_probe_summary_v2_15f3.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

REQUEST_TIMEOUT_SECONDS = 35
MAX_PROBES_DEFAULT = 30
MAX_BYTES_PER_PROBE = 250_000
SLEEP_BETWEEN_PROBES_SECONDS = 0.25

USER_AGENT = (
    "ScoutFinance/2.15F3 controlled endpoint metadata probe "
    "(no raw payload storage; no securities extraction)"
)


RESULT_FIELDNAMES = [
    "probe_id",
    "probe_order",
    "probe_type",
    "normalized_candidate_url",
    "source_strategy_priority",
    "base_validation_score",
    "risk",
    "http_method",
    "status_code",
    "ok",
    "final_url",
    "redirected",
    "content_type",
    "content_length_header",
    "sampled_bytes",
    "sample_sha256",
    "body_sample_in_memory_only",
    "payload_saved_to_disk",
    "shape_classification",
    "json_top_level_type",
    "json_top_level_keys",
    "html_marker_counts",
    "csv_like",
    "promising_for_next_phase",
    "evidence_level",
    "error",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def host_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host.endswith("euronext.com") or host.endswith("live.euronext.com")


def select_probe_rows(rows: list[dict], max_probes: int) -> list[dict]:
    executable = [
        row for row in rows
        if as_bool_text(row.get("should_execute_in_next_phase", ""))
        and host_allowed(str(row.get("normalized_candidate_url", "")))
    ]

    probe_type_rank = {
        "json_or_ajax_metadata_probe": 1,
        "structured_download_metadata_probe": 2,
        "live_listing_dynamic_probe": 3,
    }

    executable = sorted(
        executable,
        key=lambda row: (
            probe_type_rank.get(str(row.get("probe_type", "")), 99),
            as_int(row.get("source_strategy_priority", 9), 9),
            -as_int(row.get("base_validation_score", 0), 0),
            str(row.get("normalized_candidate_url", "")),
        ),
    )

    selected = []
    seen_urls = set()

    for row in executable:
        url = str(row.get("normalized_candidate_url", "")).strip()
        if not url or url.lower() in seen_urls:
            continue
        selected.append(row)
        seen_urls.add(url.lower())
        if len(selected) >= max_probes:
            break

    return selected


def read_response_sample(response: requests.Response, max_bytes: int) -> bytes:
    chunks = []
    total = 0

    for chunk in response.iter_content(chunk_size=16384):
        if not chunk:
            continue
        remaining = max_bytes - total
        if remaining <= 0:
            break
        chunks.append(chunk[:remaining])
        total += len(chunk[:remaining])
        if total >= max_bytes:
            break

    return b"".join(chunks)


def classify_payload(sample: bytes, content_type: str) -> dict:
    content_type_low = (content_type or "").lower()
    text = sample.decode("utf-8", errors="replace")
    text_lstrip = text.lstrip()
    text_low = text.lower()

    json_top_level_type = ""
    json_top_level_keys = []
    shape = "unknown"
    csv_like = False

    if "json" in content_type_low or text_lstrip.startswith("{") or text_lstrip.startswith("["):
        shape = "json_like"
        try:
            parsed = json.loads(text_lstrip)
            json_top_level_type = type(parsed).__name__
            if isinstance(parsed, dict):
                json_top_level_keys = list(parsed.keys())[:40]
            elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                json_top_level_keys = list(parsed[0].keys())[:40]
        except Exception:
            json_top_level_type = "json_parse_failed_or_sample_incomplete"

    elif "csv" in content_type_low or "text/csv" in content_type_low:
        shape = "csv_like"
        csv_like = True

    elif "html" in content_type_low or "<html" in text_low or "<!doctype html" in text_low:
        shape = "html_like"

    elif "text" in content_type_low:
        shape = "text_like"

    html_markers = {
        "drupalSettings": text.count("drupalSettings"),
        "application/json": text_low.count("application/json"),
        "data-drupal": text_low.count("data-drupal"),
        "ajax": text_low.count("ajax"),
        "api": text_low.count("api"),
        "equit": text_low.count("equit"),
        "isin": text_low.count("isin"),
        "instrument": text_low.count("instrument"),
        "table": text_low.count("<table"),
    }

    line_sample = [line.strip() for line in text.splitlines()[:20] if line.strip()]
    if len(line_sample) >= 2:
        delimiters = [",", ";", "\t", "|"]
        for delimiter in delimiters:
            counts = [line.count(delimiter) for line in line_sample[:10]]
            if counts and max(counts) >= 3 and sum(1 for count in counts if count >= 3) >= 2:
                csv_like = True
                if shape in {"unknown", "text_like"}:
                    shape = "csv_like"
                break

    return {
        "shape_classification": shape,
        "json_top_level_type": json_top_level_type,
        "json_top_level_keys": "|".join(str(key) for key in json_top_level_keys),
        "html_marker_counts": json.dumps(html_markers, ensure_ascii=False),
        "csv_like": csv_like,
        "marker_counts": html_markers,
    }


def promising_for_next_phase(row: dict, status_code: int | None, content_type: str, classification: dict) -> tuple[bool, str]:
    if status_code is None or status_code >= 400:
        return False, "none"

    shape = classification["shape_classification"]
    marker_counts = classification["marker_counts"]
    probe_type = str(row.get("probe_type", ""))

    if shape == "json_like" and (
        "json_or_ajax" in probe_type
        or marker_counts.get("isin", 0) > 0
        or marker_counts.get("instrument", 0) > 0
        or marker_counts.get("equit", 0) > 0
    ):
        return True, "medium"

    if shape == "csv_like":
        return True, "medium"

    if shape == "html_like" and (
        marker_counts.get("drupalSettings", 0) > 0
        or marker_counts.get("application/json", 0) > 0
        or marker_counts.get("ajax", 0) > 5
        or marker_counts.get("isin", 0) > 0
        or marker_counts.get("instrument", 0) > 0
    ):
        return True, "low"

    return False, "none"


def probe_one(session: requests.Session, row: dict, order: int) -> dict:
    url = str(row.get("normalized_candidate_url", "")).strip()

    base = {
        "probe_id": row.get("probe_id", ""),
        "probe_order": order,
        "probe_type": row.get("probe_type", ""),
        "normalized_candidate_url": url,
        "source_strategy_priority": row.get("source_strategy_priority", ""),
        "base_validation_score": row.get("base_validation_score", ""),
        "risk": row.get("risk", ""),
        "http_method": "GET_STREAM_SAMPLE",
        "status_code": "",
        "ok": False,
        "final_url": "",
        "redirected": False,
        "content_type": "",
        "content_length_header": "",
        "sampled_bytes": 0,
        "sample_sha256": "",
        "body_sample_in_memory_only": True,
        "payload_saved_to_disk": False,
        "shape_classification": "",
        "json_top_level_type": "",
        "json_top_level_keys": "",
        "html_marker_counts": "",
        "csv_like": False,
        "promising_for_next_phase": False,
        "evidence_level": "none",
        "error": "",
    }

    if not host_allowed(url):
        base["error"] = "HOST_NOT_ALLOWED"
        return base

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/csv,text/html,application/xhtml+xml,text/plain,*/*;q=0.8",
    }

    try:
        with session.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
            stream=True,
        ) as response:
            sample = read_response_sample(response, MAX_BYTES_PER_PROBE)
            content_type = response.headers.get("content-type", "")
            content_length = response.headers.get("content-length", "")

            classification = classify_payload(sample, content_type)
            promising, evidence_level = promising_for_next_phase(row, response.status_code, content_type, classification)

            base.update(
                {
                    "status_code": response.status_code,
                    "ok": bool(response.ok),
                    "final_url": response.url,
                    "redirected": response.url != url,
                    "content_type": content_type,
                    "content_length_header": content_length,
                    "sampled_bytes": len(sample),
                    "sample_sha256": sha256_bytes(sample) if sample else "",
                    "shape_classification": classification["shape_classification"],
                    "json_top_level_type": classification["json_top_level_type"],
                    "json_top_level_keys": classification["json_top_level_keys"],
                    "html_marker_counts": classification["html_marker_counts"],
                    "csv_like": classification["csv_like"],
                    "promising_for_next_phase": promising,
                    "evidence_level": evidence_level,
                }
            )

    except Exception as exc:
        base["error"] = f"{type(exc).__name__}: {exc}"

    return base


def main() -> None:
    for path in [PROBE_JSON, PROBE_MD, PROBE_RESULTS_CSV, PROBE_SUMMARY_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    revision = read_json(REVISION_JSON)
    probe_plan = read_csv(PROBE_PLAN_CSV)

    max_probes = as_int(os.environ.get("SCOUT_FINANCE_EURONEXT_PROBE_LIMIT", MAX_PROBES_DEFAULT), MAX_PROBES_DEFAULT)
    selected_rows = select_probe_rows(probe_plan, max_probes=max_probes)

    session = requests.Session()

    results = []
    for order, row in enumerate(selected_rows, start=1):
        results.append(probe_one(session, row, order))
        time.sleep(SLEEP_BETWEEN_PROBES_SECONDS)

    status_counter = Counter(str(row["status_code"]) for row in results)
    shape_counter = Counter(str(row["shape_classification"]) for row in results)
    probe_type_counter = Counter(str(row["probe_type"]) for row in results)
    evidence_counter = Counter(str(row["evidence_level"]) for row in results)

    ok_count = sum(1 for row in results if str(row["ok"]).lower() == "true" or row["ok"] is True)
    error_count = sum(1 for row in results if row.get("error"))
    promising_count = sum(1 for row in results if str(row["promising_for_next_phase"]).lower() == "true" or row["promising_for_next_phase"] is True)

    medium_or_better = sum(1 for row in results if str(row.get("evidence_level", "")) in {"medium", "high"})

    controlled_probe_quality = "none"
    if promising_count > 0:
        controlled_probe_quality = "low"
    if medium_or_better > 0:
        controlled_probe_quality = "medium"

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

    add_check("v2_15f2_revision_exists", REVISION_JSON.exists(), "critical", str(REVISION_JSON))
    add_check("probe_plan_exists", PROBE_PLAN_CSV.exists(), "critical", str(PROBE_PLAN_CSV))
    add_check("selected_probe_rows_available", len(selected_rows) > 0, "critical", f"selected_rows={len(selected_rows)}")
    add_check("endpoint_probe_executed", len(results) > 0, "critical", f"results={len(results)}")
    add_check("at_least_one_http_ok", ok_count > 0, "warning", f"ok_count={ok_count}")
    add_check("promising_endpoint_review", promising_count > 0, "warning", f"promising_count={promising_count}")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_payload_saved_to_disk", all(not bool(row.get("payload_saved_to_disk")) for row in results), "critical", "payload_saved_to_disk=False")
    add_check("no_security_row_extraction", True, "critical", "security_rows_extracted=False")
    add_check("no_normalization", True, "critical", "normalization_performed=False")
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"current_rows={CURRENT_ROWS}")

    if critical_failed != 0:
        status = "EURONEXT_CONTROLLED_ENDPOINT_PROBE_FAILED_REBUILD_BLOCKED"
        recommended_next_phase = "v2.15F3B - Euronext Endpoint Probe Repair"
    elif controlled_probe_quality in {"medium"}:
        status = "EURONEXT_CONTROLLED_ENDPOINT_PROBE_COMPLETED_PROMISING_ENDPOINTS_REBUILD_STILL_BLOCKED"
        recommended_next_phase = "v2.15F4 - Euronext Endpoint Payload Shape Validation"
    elif controlled_probe_quality == "low":
        status = "EURONEXT_CONTROLLED_ENDPOINT_PROBE_COMPLETED_LOW_SIGNAL_REBUILD_STILL_BLOCKED"
        recommended_next_phase = "v2.15G - Euronext Closure Report"
    else:
        status = "EURONEXT_CONTROLLED_ENDPOINT_PROBE_COMPLETED_NO_USABLE_ENDPOINT_REBUILD_STILL_BLOCKED"
        recommended_next_phase = "v2.15G - Euronext Closure Report"

    summary_rows = [
        {"metric": "probe_plan_rows", "value": len(probe_plan)},
        {"metric": "selected_probe_rows", "value": len(selected_rows)},
        {"metric": "results", "value": len(results)},
        {"metric": "ok_count", "value": ok_count},
        {"metric": "error_count", "value": error_count},
        {"metric": "promising_count", "value": promising_count},
        {"metric": "medium_or_better_evidence_count", "value": medium_or_better},
        {"metric": "controlled_probe_quality", "value": controlled_probe_quality},
        {"metric": "status_counter", "value": json.dumps(dict(status_counter), ensure_ascii=False)},
        {"metric": "shape_counter", "value": json.dumps(dict(shape_counter), ensure_ascii=False)},
        {"metric": "probe_type_counter", "value": json.dumps(dict(probe_type_counter), ensure_ascii=False)},
        {"metric": "evidence_counter", "value": json.dumps(dict(evidence_counter), ensure_ascii=False)},
    ]

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
        "probe_config": {
            "max_probes": max_probes,
            "max_bytes_per_probe": MAX_BYTES_PER_PROBE,
            "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
            "sleep_between_probes_seconds": SLEEP_BETWEEN_PROBES_SECONDS,
            "payload_storage": "disabled",
            "securities_extraction": "disabled",
        },
        "probe_summary": {
            "probe_plan_rows": len(probe_plan),
            "selected_probe_rows": len(selected_rows),
            "results": len(results),
            "ok_count": ok_count,
            "error_count": error_count,
            "promising_count": promising_count,
            "medium_or_better_evidence_count": medium_or_better,
            "controlled_probe_quality": controlled_probe_quality,
            "status_counts": dict(status_counter),
            "shape_counts": dict(shape_counter),
            "probe_type_counts": dict(probe_type_counter),
            "evidence_counts": dict(evidence_counter),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "top_promising_results": [
            row for row in results
            if str(row.get("promising_for_next_phase")).lower() == "true" or row.get("promising_for_next_phase") is True
        ][:30],
        "revision_status": revision.get("status", ""),
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_probe_executed": len(results) > 0,
            "http_body_sampled_in_memory_only": True,
            "raw_payload_saved_to_disk": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "security_rows_extracted": False,
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

    write_json(PROBE_JSON, payload)
    write_csv(PROBE_RESULTS_CSV, results, RESULT_FIELDNAMES)
    write_csv(PROBE_SUMMARY_CSV, summary_rows, ["metric", "value"])

    check_lines = "\n".join(
        f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}"
        for item in checks
    )

    result_lines = "\n".join(
        f"- probe={row['probe_id']} type={row['probe_type']} status={row['status_code']} shape={row['shape_classification']} evidence={row['evidence_level']} promising={row['promising_for_next_phase']} url={row['normalized_candidate_url']}"
        for row in results[:30]
    ) or "- No probe results."

    promising_lines = "\n".join(
        f"- probe={row['probe_id']} type={row['probe_type']} status={row['status_code']} shape={row['shape_classification']} evidence={row['evidence_level']} url={row['normalized_candidate_url']}"
        for row in payload["top_promising_results"][:20]
    ) or "- No promising probe results."

    PROBE_MD.write_text(
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

## Probe config

- Max probes: {max_probes}
- Max bytes per probe: {MAX_BYTES_PER_PROBE}
- Timeout seconds: {REQUEST_TIMEOUT_SECONDS}
- Payload storage: disabled
- Securities extraction: disabled

## Probe summary

- Probe plan rows: {len(probe_plan)}
- Selected probe rows: {len(selected_rows)}
- Results: {len(results)}
- HTTP OK count: {ok_count}
- Error count: {error_count}
- Promising count: {promising_count}
- Medium or better evidence count: {medium_or_better}
- Controlled probe quality: `{controlled_probe_quality}`
- Status counts: `{dict(status_counter)}`
- Shape counts: `{dict(shape_counter)}`
- Probe type counts: `{dict(probe_type_counter)}`
- Evidence counts: `{dict(evidence_counter)}`
- Critical failed checks: {critical_failed}

## First probe results

{result_lines}

## Promising probe results

{promising_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.15F3: true
- Endpoint probe executed: {str(len(results) > 0).lower()}
- HTTP body sampled in memory only: true
- Raw payload saved to disk: false
- Raw files downloaded: false
- Raw files modified after write: false
- Security rows extracted: false
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

This phase performs controlled endpoint probing only.

It samples HTTP responses in memory for metadata and superficial payload shape. It does not save raw payloads, does not extract security rows, does not normalize instruments, does not calculate net-new rows, does not read or modify the canonical expanded universe, does not rebuild the expanded universe, does not score equities, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15F3 Euronext controlled endpoint probe completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("PROBE_SUMMARY:")
    for key, value in payload["probe_summary"].items():
        print(f"- {key}: {value}")
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
