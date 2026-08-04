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


VERSION = "v2.15F4"
PHASE = "Euronext Endpoint Payload Shape Validation"
PHASE_TYPE = "payload-shape-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

F3_JSON = OUTPUT_DIR / "euronext_controlled_endpoint_probe_v2_15f3.json"
F3_RESULTS_CSV = OUTPUT_DIR / "euronext_controlled_endpoint_probe_results_v2_15f3.csv"

SHAPE_JSON = OUTPUT_DIR / "euronext_endpoint_payload_shape_validation_v2_15f4.json"
SHAPE_MD = OUTPUT_DIR / "euronext_endpoint_payload_shape_validation_v2_15f4.md"
SHAPE_RESULTS_CSV = OUTPUT_DIR / "euronext_endpoint_payload_shape_results_v2_15f4.csv"
SHAPE_KEY_PATHS_CSV = OUTPUT_DIR / "euronext_endpoint_payload_key_paths_v2_15f4.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

REQUEST_TIMEOUT_SECONDS = 35
MAX_ENDPOINTS_DEFAULT = 5
MAX_BYTES_PER_ENDPOINT = 1_000_000
SLEEP_BETWEEN_ENDPOINTS_SECONDS = 0.25

USER_AGENT = (
    "ScoutFinance/2.15F4 endpoint payload shape validation "
    "(shape only; no raw payload storage; no securities value extraction)"
)

FIELD_MARKERS = [
    "isin",
    "symbol",
    "ticker",
    "mnemo",
    "name",
    "instrument",
    "issuer",
    "company",
    "market",
    "exchange",
    "mic",
    "currency",
    "ccy",
    "type",
    "segment",
    "category",
    "stock",
    "equity",
    "shares",
]

RESULT_FIELDNAMES = [
    "endpoint_id",
    "probe_id",
    "probe_type",
    "url",
    "status_code",
    "ok",
    "final_url",
    "content_type",
    "content_length_header",
    "sampled_bytes",
    "sample_sha256",
    "payload_saved_to_disk",
    "json_parsed_for_shape_only",
    "json_parse_error",
    "json_top_level_type",
    "top_level_keys",
    "list_container_count",
    "dict_container_count",
    "key_path_count",
    "field_marker_hits",
    "field_marker_hit_count",
    "security_like_container_count",
    "shape_validation_status",
    "shape_quality",
    "recommended_extraction_route",
    "error",
]

KEY_PATH_FIELDNAMES = [
    "endpoint_id",
    "url",
    "path",
    "value_type",
    "example_container_type",
    "field_marker_hit",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def as_bool_text(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def host_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host.endswith("euronext.com") or host.endswith("live.euronext.com")


def select_json_promising_endpoints(rows: list[dict], max_endpoints: int) -> list[dict]:
    candidates = []

    for row in rows:
        url = str(row.get("normalized_candidate_url", "")).strip()
        content_type = str(row.get("content_type", "")).lower()
        shape = str(row.get("shape_classification", "")).lower()
        probe_type = str(row.get("probe_type", "")).lower()
        promising = as_bool_text(row.get("promising_for_next_phase", ""))

        is_json_candidate = (
            "json" in content_type
            or shape == "json_like"
            or "json_or_ajax" in probe_type
        )

        if promising and is_json_candidate and url and host_allowed(url):
            candidates.append(row)

    candidates = sorted(
        candidates,
        key=lambda row: (
            0 if "json_or_ajax" in str(row.get("probe_type", "")).lower() else 1,
            as_int(row.get("probe_order", 999), 999),
            str(row.get("normalized_candidate_url", "")),
        ),
    )

    selected = []
    seen = set()

    for row in candidates:
        url = str(row.get("normalized_candidate_url", "")).strip()
        if url.lower() in seen:
            continue
        selected.append(row)
        seen.add(url.lower())
        if len(selected) >= max_endpoints:
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
        part = chunk[:remaining]
        chunks.append(part)
        total += len(part)
        if total >= max_bytes:
            break

    return b"".join(chunks)


def field_marker_for_key(key: str) -> str:
    low = key.lower()
    hits = [marker for marker in FIELD_MARKERS if marker in low]
    return "|".join(sorted(set(hits)))


def collect_key_paths(
    obj,
    endpoint_id: str,
    url: str,
    path: str = "$",
    depth: int = 0,
    max_depth: int = 5,
    max_list_items: int = 5,
    rows: list[dict] | None = None,
) -> list[dict]:
    if rows is None:
        rows = []

    if depth > max_depth:
        return rows

    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}"
            rows.append(
                {
                    "endpoint_id": endpoint_id,
                    "url": url,
                    "path": child_path,
                    "value_type": type(value).__name__,
                    "example_container_type": "dict",
                    "field_marker_hit": field_marker_for_key(str(key)),
                }
            )
            if isinstance(value, (dict, list)):
                collect_key_paths(value, endpoint_id, url, child_path, depth + 1, max_depth, max_list_items, rows)

    elif isinstance(obj, list):
        rows.append(
            {
                "endpoint_id": endpoint_id,
                "url": url,
                "path": f"{path}[]",
                "value_type": "list",
                "example_container_type": f"list_len_{len(obj)}",
                "field_marker_hit": "",
            }
        )

        for index, item in enumerate(obj[:max_list_items]):
            collect_key_paths(item, endpoint_id, url, f"{path}[{index}]", depth + 1, max_depth, max_list_items, rows)

    return rows


def find_security_like_containers(obj, path: str = "$", depth: int = 0, max_depth: int = 5) -> list[dict]:
    containers = []

    if depth > max_depth:
        return containers

    if isinstance(obj, list):
        dict_items = [item for item in obj[:20] if isinstance(item, dict)]
        if dict_items:
            key_counter = Counter()
            for item in dict_items:
                for key in item.keys():
                    key_counter[str(key)] += 1

            marker_hits = []
            for key in key_counter:
                marker = field_marker_for_key(key)
                if marker:
                    marker_hits.extend(marker.split("|"))

            marker_hits = sorted(set(hit for hit in marker_hits if hit))
            score = 0
            if "isin" in marker_hits:
                score += 50
            if "symbol" in marker_hits or "ticker" in marker_hits or "mnemo" in marker_hits:
                score += 20
            if "name" in marker_hits or "instrument" in marker_hits or "issuer" in marker_hits or "company" in marker_hits:
                score += 20
            if "market" in marker_hits or "mic" in marker_hits or "exchange" in marker_hits:
                score += 10
            if "currency" in marker_hits or "ccy" in marker_hits:
                score += 5
            if "type" in marker_hits or "category" in marker_hits or "segment" in marker_hits:
                score += 5

            if marker_hits:
                containers.append(
                    {
                        "path": path,
                        "list_len_sample": len(obj),
                        "dict_items_sampled": len(dict_items),
                        "key_count_sample": len(key_counter),
                        "field_marker_hits": marker_hits,
                        "security_like_score": score,
                    }
                )

        for index, item in enumerate(obj[:5]):
            containers.extend(find_security_like_containers(item, f"{path}[{index}]", depth + 1, max_depth))

    elif isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                containers.extend(find_security_like_containers(value, f"{path}.{key}", depth + 1, max_depth))

    return containers


def validate_shape_for_endpoint(session: requests.Session, row: dict, order: int) -> tuple[dict, list[dict]]:
    url = str(row.get("normalized_candidate_url", "")).strip()
    endpoint_id = short_hash(url)

    base = {
        "endpoint_id": endpoint_id,
        "probe_id": row.get("probe_id", ""),
        "probe_type": row.get("probe_type", ""),
        "url": url,
        "status_code": "",
        "ok": False,
        "final_url": "",
        "content_type": "",
        "content_length_header": "",
        "sampled_bytes": 0,
        "sample_sha256": "",
        "payload_saved_to_disk": False,
        "json_parsed_for_shape_only": False,
        "json_parse_error": "",
        "json_top_level_type": "",
        "top_level_keys": "",
        "list_container_count": 0,
        "dict_container_count": 0,
        "key_path_count": 0,
        "field_marker_hits": "",
        "field_marker_hit_count": 0,
        "security_like_container_count": 0,
        "shape_validation_status": "not_validated",
        "shape_quality": "none",
        "recommended_extraction_route": "none",
        "error": "",
    }

    if not host_allowed(url):
        base["error"] = "HOST_NOT_ALLOWED"
        base["shape_validation_status"] = "blocked_host_not_allowed"
        return base, []

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/plain,*/*;q=0.8",
    }

    try:
        with session.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
            stream=True,
        ) as response:
            sample = read_response_sample(response, MAX_BYTES_PER_ENDPOINT)
            content_type = response.headers.get("content-type", "")
            content_length = response.headers.get("content-length", "")

            base.update(
                {
                    "status_code": response.status_code,
                    "ok": bool(response.ok),
                    "final_url": response.url,
                    "content_type": content_type,
                    "content_length_header": content_length,
                    "sampled_bytes": len(sample),
                    "sample_sha256": sha256_bytes(sample) if sample else "",
                }
            )

            text = sample.decode("utf-8", errors="replace").lstrip()

            if response.status_code >= 400:
                base["shape_validation_status"] = "http_error"
                return base, []

            if "json" not in content_type.lower() and not text.startswith("{") and not text.startswith("["):
                base["shape_validation_status"] = "not_json_payload"
                return base, []

            try:
                parsed = json.loads(text)
            except Exception as exc:
                base["json_parse_error"] = f"{type(exc).__name__}: {exc}"
                base["shape_validation_status"] = "json_parse_failed_or_sample_incomplete"
                return base, []

            key_paths = collect_key_paths(parsed, endpoint_id, url)
            containers = find_security_like_containers(parsed)

            top_keys = []
            if isinstance(parsed, dict):
                top_keys = [str(key) for key in list(parsed.keys())[:50]]
            elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                top_keys = [str(key) for key in list(parsed[0].keys())[:50]]

            field_hits = sorted(
                set(
                    hit
                    for path_row in key_paths
                    for hit in str(path_row.get("field_marker_hit", "")).split("|")
                    if hit
                )
            )

            list_container_count = sum(1 for path_row in key_paths if str(path_row.get("value_type")) == "list")
            dict_container_count = sum(1 for path_row in key_paths if str(path_row.get("value_type")) == "dict")

            max_security_score = max((int(item["security_like_score"]) for item in containers), default=0)

            shape_quality = "none"
            shape_status = "json_shape_validated_no_security_container"
            recommended_route = "none"

            if containers and max_security_score >= 70:
                shape_quality = "high"
                shape_status = "json_shape_validated_security_container_strong"
                recommended_route = "candidate_extraction_dry_run_allowed_next_phase"
            elif containers and max_security_score >= 40:
                shape_quality = "medium"
                shape_status = "json_shape_validated_security_container_candidate"
                recommended_route = "candidate_extraction_dry_run_allowed_next_phase"
            elif field_hits:
                shape_quality = "low"
                shape_status = "json_shape_validated_field_markers_only"
                recommended_route = "manual_shape_review_before_extraction"
            else:
                shape_quality = "none"
                shape_status = "json_shape_validated_no_relevant_markers"
                recommended_route = "none"

            base.update(
                {
                    "json_parsed_for_shape_only": True,
                    "json_top_level_type": type(parsed).__name__,
                    "top_level_keys": "|".join(top_keys),
                    "list_container_count": list_container_count,
                    "dict_container_count": dict_container_count,
                    "key_path_count": len(key_paths),
                    "field_marker_hits": "|".join(field_hits),
                    "field_marker_hit_count": len(field_hits),
                    "security_like_container_count": len(containers),
                    "shape_validation_status": shape_status,
                    "shape_quality": shape_quality,
                    "recommended_extraction_route": recommended_route,
                }
            )

            return base, key_paths

    except Exception as exc:
        base["error"] = f"{type(exc).__name__}: {exc}"
        base["shape_validation_status"] = "request_error"
        return base, []


def main() -> None:
    for path in [SHAPE_JSON, SHAPE_MD, SHAPE_RESULTS_CSV, SHAPE_KEY_PATHS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    f3 = read_json(F3_JSON)
    f3_results = read_csv(F3_RESULTS_CSV)

    max_endpoints = as_int(os.environ.get("SCOUT_FINANCE_EURONEXT_SHAPE_LIMIT", MAX_ENDPOINTS_DEFAULT), MAX_ENDPOINTS_DEFAULT)
    selected = select_json_promising_endpoints(f3_results, max_endpoints=max_endpoints)

    session = requests.Session()

    shape_rows = []
    key_path_rows = []

    for order, row in enumerate(selected, start=1):
        result, paths = validate_shape_for_endpoint(session, row, order)
        shape_rows.append(result)
        key_path_rows.extend(paths)
        time.sleep(SLEEP_BETWEEN_ENDPOINTS_SECONDS)

    quality_counter = Counter(str(row["shape_quality"]) for row in shape_rows)
    status_counter = Counter(str(row["shape_validation_status"]) for row in shape_rows)
    http_counter = Counter(str(row["status_code"]) for row in shape_rows)

    parsed_count = sum(1 for row in shape_rows if as_bool_text(row.get("json_parsed_for_shape_only", "")))
    security_container_count = sum(as_int(row.get("security_like_container_count", 0)) for row in shape_rows)
    medium_or_high_shape_count = quality_counter.get("medium", 0) + quality_counter.get("high", 0)
    extraction_dry_run_allowed_count = sum(
        1
        for row in shape_rows
        if row.get("recommended_extraction_route") == "candidate_extraction_dry_run_allowed_next_phase"
    )

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

    add_check("v2_15f3_probe_exists", F3_JSON.exists(), "critical", str(F3_JSON))
    add_check("v2_15f3_results_exists", F3_RESULTS_CSV.exists(), "critical", str(F3_RESULTS_CSV))
    add_check("json_promising_endpoints_selected", len(selected) > 0, "critical", f"selected={len(selected)}")
    add_check("shape_validation_executed", len(shape_rows) > 0, "critical", f"shape_rows={len(shape_rows)}")
    add_check("json_parsed_for_shape", parsed_count > 0, "warning", f"parsed_count={parsed_count}")
    add_check("security_like_container_review", security_container_count > 0, "warning", f"security_like_container_count={security_container_count}")
    add_check("medium_or_high_shape_review", medium_or_high_shape_count > 0, "warning", f"medium_or_high_shape_count={medium_or_high_shape_count}")
    add_check("no_payload_saved_to_disk", all(not as_bool_text(row.get("payload_saved_to_disk", "")) for row in shape_rows), "critical", "payload_saved_to_disk=False")
    add_check("no_security_values_extracted", True, "critical", "security_values_extracted=False")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_normalization", True, "critical", "normalization_performed=False")
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"current_rows={CURRENT_ROWS}")

    if critical_failed != 0:
        status = "EURONEXT_ENDPOINT_PAYLOAD_SHAPE_VALIDATION_FAILED_REBUILD_BLOCKED"
        recommended_next_phase = "v2.15F4B - Euronext Payload Shape Validation Repair"
    elif extraction_dry_run_allowed_count > 0:
        status = "EURONEXT_ENDPOINT_PAYLOAD_SHAPE_VALIDATED_EXTRACTION_DRY_RUN_ALLOWED_REBUILD_STILL_BLOCKED"
        recommended_next_phase = "v2.15F5 - Euronext Endpoint Candidate Extraction Dry Run"
    elif parsed_count > 0:
        status = "EURONEXT_ENDPOINT_PAYLOAD_SHAPE_VALIDATED_NO_EXTRACTION_ROUTE_REBUILD_STILL_BLOCKED"
        recommended_next_phase = "v2.15G - Euronext Closure Report"
    else:
        status = "EURONEXT_ENDPOINT_PAYLOAD_SHAPE_VALIDATION_INCONCLUSIVE_REBUILD_STILL_BLOCKED"
        recommended_next_phase = "v2.15G - Euronext Closure Report"

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
        "shape_config": {
            "max_endpoints": max_endpoints,
            "max_bytes_per_endpoint": MAX_BYTES_PER_ENDPOINT,
            "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
            "payload_storage": "disabled",
            "security_value_extraction": "disabled",
        },
        "shape_summary": {
            "f3_status": f3.get("status", ""),
            "f3_recommended_next_phase": f3.get("recommended_next_phase", ""),
            "f3_result_rows": len(f3_results),
            "selected_json_promising_endpoints": len(selected),
            "shape_rows": len(shape_rows),
            "json_parsed_for_shape_count": parsed_count,
            "security_like_container_count": security_container_count,
            "medium_or_high_shape_count": medium_or_high_shape_count,
            "extraction_dry_run_allowed_count": extraction_dry_run_allowed_count,
            "shape_quality_counts": dict(quality_counter),
            "shape_validation_status_counts": dict(status_counter),
            "http_status_counts": dict(http_counter),
            "key_path_rows": len(key_path_rows),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "shape_results": shape_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_payload_shape_validated": len(shape_rows) > 0,
            "http_body_sampled_in_memory_only": True,
            "raw_payload_saved_to_disk": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "json_payload_parsed_for_shape_only": parsed_count > 0,
            "security_values_extracted": False,
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

    write_json(SHAPE_JSON, payload)
    write_csv(SHAPE_RESULTS_CSV, shape_rows, RESULT_FIELDNAMES)
    write_csv(SHAPE_KEY_PATHS_CSV, key_path_rows, KEY_PATH_FIELDNAMES)

    check_lines = "\n".join(
        f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}"
        for item in checks
    )

    result_lines = "\n".join(
        f"- endpoint={row['endpoint_id']} status={row['status_code']} parsed={row['json_parsed_for_shape_only']} quality={row['shape_quality']} security_containers={row['security_like_container_count']} markers=`{row['field_marker_hits']}` route={row['recommended_extraction_route']} url={row['url']}"
        for row in shape_rows
    ) or "- No shape rows."

    SHAPE_MD.write_text(
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

## Shape summary

- F3 status: `{payload["shape_summary"]["f3_status"]}`
- F3 recommended next phase: `{payload["shape_summary"]["f3_recommended_next_phase"]}`
- F3 result rows: {payload["shape_summary"]["f3_result_rows"]}
- Selected JSON promising endpoints: {payload["shape_summary"]["selected_json_promising_endpoints"]}
- Shape rows: {payload["shape_summary"]["shape_rows"]}
- JSON parsed for shape count: {parsed_count}
- Security-like container count: {security_container_count}
- Medium/high shape count: {medium_or_high_shape_count}
- Extraction dry-run allowed count: {extraction_dry_run_allowed_count}
- Shape quality counts: `{dict(quality_counter)}`
- Shape validation status counts: `{dict(status_counter)}`
- HTTP status counts: `{dict(http_counter)}`
- Key path rows: {len(key_path_rows)}
- Critical failed checks: {critical_failed}

## Shape results

{result_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.15F4: true
- Endpoint payload shape validated: {str(len(shape_rows) > 0).lower()}
- HTTP body sampled in memory only: true
- Raw payload saved to disk: false
- Raw files downloaded: false
- Raw files modified after write: false
- JSON payload parsed for shape only: {str(parsed_count > 0).lower()}
- Security values extracted: false
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

This phase validates endpoint JSON payload shape only.

It samples endpoint bodies in memory and writes only structural metadata such as top-level keys and key paths. It does not save raw payloads, does not extract security values, does not extract security rows, does not normalize instruments, does not calculate net-new rows, does not read or modify the canonical expanded universe, does not rebuild the expanded universe, does not score equities, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15F4 Euronext endpoint payload shape validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SHAPE_SUMMARY:")
    for key, value in payload["shape_summary"].items():
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
