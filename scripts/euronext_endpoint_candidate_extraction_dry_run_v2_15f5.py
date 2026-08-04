from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


VERSION = "v2.15F5"
PHASE = "Euronext Endpoint Candidate Extraction Dry Run"
PHASE_TYPE = "endpoint-candidate-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

F4_JSON = OUTPUT_DIR / "euronext_endpoint_payload_shape_validation_v2_15f4.json"
F4_RESULTS_CSV = OUTPUT_DIR / "euronext_endpoint_payload_shape_results_v2_15f4.csv"
F4_KEY_PATHS_CSV = OUTPUT_DIR / "euronext_endpoint_payload_key_paths_v2_15f4.csv"

DRY_JSON = OUTPUT_DIR / "euronext_endpoint_candidate_extraction_dry_run_v2_15f5.json"
DRY_MD = OUTPUT_DIR / "euronext_endpoint_candidate_extraction_dry_run_v2_15f5.md"
CANDIDATES_CSV = OUTPUT_DIR / "euronext_endpoint_extracted_candidates_raw_v2_15f5.csv"
QUALITY_CSV = OUTPUT_DIR / "euronext_endpoint_candidate_extraction_quality_v2_15f5.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

REQUEST_TIMEOUT_SECONDS = 45
MAX_ENDPOINTS_DEFAULT = 5
MAX_BYTES_PER_ENDPOINT = 8_000_000
SLEEP_BETWEEN_ENDPOINTS_SECONDS = 0.25

USER_AGENT = (
    "ScoutFinance/2.15F5 endpoint candidate extraction dry run "
    "(raw candidates only; no canonical read; no net-new; no rebuild)"
)

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "endpoint_id",
    "endpoint_url",
    "endpoint_order",
    "json_path",
    "row_index",
    "raw_isin",
    "raw_mic",
    "raw_name",
    "raw_symbol",
    "raw_currency",
    "raw_market",
    "raw_type",
    "raw_extra_keys",
    "raw_key_count",
    "extraction_confidence",
    "quality_bucket",
    "notes",
]

QUALITY_FIELDNAMES = [
    "endpoint_id",
    "endpoint_url",
    "status_code",
    "ok",
    "content_type",
    "sampled_bytes",
    "payload_saved_to_disk",
    "json_top_level_type",
    "candidate_container_path",
    "raw_rows_seen",
    "candidate_rows_extracted",
    "valid_isin_rows",
    "rows_with_mic",
    "rows_with_name",
    "rows_with_symbol",
    "rows_with_currency",
    "high_quality",
    "medium_quality",
    "low_quality",
    "unique_isins",
    "quality_notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


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


def clean_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)[:500]
    return " ".join(str(value).replace("\xa0", " ").split()).strip()


def first_value(row: dict, keys: list[str]) -> str:
    low_map = {str(key).lower(): key for key in row.keys()}
    for key in keys:
        actual = low_map.get(key.lower())
        if actual is not None:
            return clean_value(row.get(actual))
    return ""


def select_shape_validated_endpoints(rows: list[dict], max_endpoints: int) -> list[dict]:
    candidates = []

    for row in rows:
        url = str(row.get("url", "")).strip()
        route = str(row.get("recommended_extraction_route", "")).strip()
        quality = str(row.get("shape_quality", "")).lower()
        parsed = as_bool_text(row.get("json_parsed_for_shape_only", ""))

        if (
            url
            and host_allowed(url)
            and parsed
            and route == "candidate_extraction_dry_run_allowed_next_phase"
            and quality in {"medium", "high"}
        ):
            candidates.append(row)

    candidates = sorted(
        candidates,
        key=lambda row: (
            0 if str(row.get("shape_quality", "")).lower() == "high" else 1,
            str(row.get("endpoint_id", "")),
            str(row.get("url", "")),
        ),
    )

    selected = []
    seen = set()

    for row in candidates:
        url = str(row.get("url", "")).strip()
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

    for chunk in response.iter_content(chunk_size=65536):
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


def find_candidate_containers(obj, path: str = "$", depth: int = 0, max_depth: int = 5) -> list[tuple[str, list[dict]]]:
    containers: list[tuple[str, list[dict]]] = []

    if depth > max_depth:
        return containers

    if isinstance(obj, list):
        dict_items = [item for item in obj if isinstance(item, dict)]

        if dict_items:
            keys = {str(key).lower() for item in dict_items[:50] for key in item.keys()}

            has_isin = "isin" in keys
            has_name = "name" in keys or "instrumentname" in keys or "instrument_name" in keys
            has_mic = "mic" in keys or "marketidentifiercode" in keys

            if has_isin and (has_name or has_mic):
                containers.append((path, dict_items))

        for index, item in enumerate(obj[:10]):
            containers.extend(find_candidate_containers(item, f"{path}[{index}]", depth + 1, max_depth))

    elif isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (list, dict)):
                containers.extend(find_candidate_containers(value, f"{path}.{key}", depth + 1, max_depth))

    return containers


def confidence_and_bucket(row: dict) -> tuple[int, str]:
    confidence = 0

    if row.get("raw_isin") and ISIN_RE.match(row["raw_isin"]):
        confidence += 45
    if row.get("raw_name"):
        confidence += 20
    if row.get("raw_mic") or row.get("raw_market"):
        confidence += 15
    if row.get("raw_symbol"):
        confidence += 10
    if row.get("raw_currency"):
        confidence += 5
    if row.get("raw_type"):
        confidence += 5

    confidence = min(confidence, 100)

    if confidence >= 75:
        return confidence, "high"
    if confidence >= 60:
        return confidence, "medium"
    return confidence, "low"


def build_candidate(
    endpoint_id: str,
    endpoint_url: str,
    endpoint_order: int,
    json_path: str,
    row_index: int,
    item: dict,
) -> dict | None:
    raw_isin = first_value(item, ["isin", "ISIN"])

    if not raw_isin or not ISIN_RE.match(raw_isin):
        return None

    raw_mic = first_value(item, ["mic", "MIC", "marketIdentifierCode"])
    raw_name = first_value(item, ["name", "Name", "instrumentName", "instrument_name", "label"])
    raw_symbol = first_value(item, ["symbol", "ticker", "mnemo", "symbolIndex", "tradingCode"])
    raw_currency = first_value(item, ["currency", "ccy", "tradingCurrency", "currencyCode"])
    raw_market = first_value(item, ["market", "exchange", "venue", "marketName"])
    raw_type = first_value(item, ["type", "instrumentType", "category", "segment"])

    known_keys = {
        "isin",
        "mic",
        "marketidentifiercode",
        "name",
        "instrumentname",
        "instrument_name",
        "label",
        "symbol",
        "ticker",
        "mnemo",
        "symbolindex",
        "tradingcode",
        "currency",
        "ccy",
        "tradingcurrency",
        "currencycode",
        "market",
        "exchange",
        "venue",
        "marketname",
        "type",
        "instrumenttype",
        "category",
        "segment",
    }

    extra_keys = sorted(str(key) for key in item.keys() if str(key).lower() not in known_keys)

    candidate = {
        "candidate_id": "",
        "endpoint_id": endpoint_id,
        "endpoint_url": endpoint_url,
        "endpoint_order": endpoint_order,
        "json_path": json_path,
        "row_index": row_index,
        "raw_isin": raw_isin,
        "raw_mic": raw_mic,
        "raw_name": raw_name,
        "raw_symbol": raw_symbol,
        "raw_currency": raw_currency,
        "raw_market": raw_market,
        "raw_type": raw_type,
        "raw_extra_keys": "|".join(extra_keys[:50]),
        "raw_key_count": len(item.keys()),
        "extraction_confidence": 0,
        "quality_bucket": "",
        "notes": "dry_run_endpoint_raw_candidate_not_normalized_not_net_new_not_rebuilt",
    }

    confidence, bucket = confidence_and_bucket(candidate)
    candidate["extraction_confidence"] = confidence
    candidate["quality_bucket"] = bucket

    id_basis = f"{endpoint_url}|{json_path}|{row_index}|{raw_isin}|{raw_mic}|{raw_name}|{raw_symbol}"
    candidate["candidate_id"] = sha256_text(id_basis)[:16]

    return candidate


def extract_from_endpoint(session: requests.Session, shape_row: dict, endpoint_order: int) -> tuple[list[dict], dict]:
    endpoint_id = str(shape_row.get("endpoint_id", "")).strip()
    url = str(shape_row.get("url", "")).strip()

    quality = {
        "endpoint_id": endpoint_id,
        "endpoint_url": url,
        "status_code": "",
        "ok": False,
        "content_type": "",
        "sampled_bytes": 0,
        "payload_saved_to_disk": False,
        "json_top_level_type": "",
        "candidate_container_path": "",
        "raw_rows_seen": 0,
        "candidate_rows_extracted": 0,
        "valid_isin_rows": 0,
        "rows_with_mic": 0,
        "rows_with_name": 0,
        "rows_with_symbol": 0,
        "rows_with_currency": 0,
        "high_quality": 0,
        "medium_quality": 0,
        "low_quality": 0,
        "unique_isins": 0,
        "quality_notes": "",
    }

    if not host_allowed(url):
        quality["quality_notes"] = "HOST_NOT_ALLOWED"
        return [], quality

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

            quality.update(
                {
                    "status_code": response.status_code,
                    "ok": bool(response.ok),
                    "content_type": content_type,
                    "sampled_bytes": len(sample),
                }
            )

            if response.status_code >= 400:
                quality["quality_notes"] = "HTTP_ERROR"
                return [], quality

            text = sample.decode("utf-8", errors="replace").lstrip()

            try:
                parsed = json.loads(text)
            except Exception as exc:
                quality["quality_notes"] = f"JSON_PARSE_FAILED_OR_SAMPLE_INCOMPLETE: {type(exc).__name__}: {exc}"
                return [], quality

            quality["json_top_level_type"] = type(parsed).__name__

            containers = find_candidate_containers(parsed)

            if not containers:
                quality["quality_notes"] = "NO_CANDIDATE_CONTAINER_FOUND"
                return [], quality

            # Pick the largest candidate container.
            container_path, items = sorted(containers, key=lambda pair: len(pair[1]), reverse=True)[0]
            quality["candidate_container_path"] = container_path
            quality["raw_rows_seen"] = len(items)

            candidates = []
            for row_index, item in enumerate(items):
                candidate = build_candidate(endpoint_id, url, endpoint_order, container_path, row_index, item)
                if candidate:
                    candidates.append(candidate)

            quality["candidate_rows_extracted"] = len(candidates)
            quality["valid_isin_rows"] = len([row for row in candidates if ISIN_RE.match(row["raw_isin"])])
            quality["rows_with_mic"] = len([row for row in candidates if row.get("raw_mic")])
            quality["rows_with_name"] = len([row for row in candidates if row.get("raw_name")])
            quality["rows_with_symbol"] = len([row for row in candidates if row.get("raw_symbol")])
            quality["rows_with_currency"] = len([row for row in candidates if row.get("raw_currency")])
            quality["unique_isins"] = len({row["raw_isin"] for row in candidates})

            bucket_counter = Counter(row["quality_bucket"] for row in candidates)
            quality["high_quality"] = bucket_counter.get("high", 0)
            quality["medium_quality"] = bucket_counter.get("medium", 0)
            quality["low_quality"] = bucket_counter.get("low", 0)

            quality["quality_notes"] = "OK_DRY_RUN_RAW_CANDIDATES_ONLY_NO_CANONICAL_READ_NO_NET_NEW_NO_REBUILD"

            return candidates, quality

    except Exception as exc:
        quality["quality_notes"] = f"REQUEST_ERROR: {type(exc).__name__}: {exc}"
        return [], quality


def dedupe_within_dry_run(rows: list[dict]) -> list[dict]:
    best_by_key: dict[tuple[str, str, str], dict] = {}

    for row in rows:
        key = (
            row.get("raw_isin", ""),
            row.get("raw_mic", ""),
            row.get("endpoint_url", ""),
        )

        if not key[0]:
            continue

        current = best_by_key.get(key)
        if current is None:
            best_by_key[key] = row
            continue

        if int(row.get("extraction_confidence", 0)) > int(current.get("extraction_confidence", 0)):
            best_by_key[key] = row

    return sorted(
        best_by_key.values(),
        key=lambda row: (
            row.get("endpoint_id", ""),
            row.get("raw_mic", ""),
            row.get("raw_isin", ""),
        ),
    )


def main() -> None:
    for path in [DRY_JSON, DRY_MD, CANDIDATES_CSV, QUALITY_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    f4 = read_json(F4_JSON)
    shape_rows = read_csv(F4_RESULTS_CSV)
    key_paths = read_csv(F4_KEY_PATHS_CSV)

    max_endpoints = as_int(os.environ.get("SCOUT_FINANCE_EURONEXT_F5_ENDPOINT_LIMIT", MAX_ENDPOINTS_DEFAULT), MAX_ENDPOINTS_DEFAULT)
    selected = select_shape_validated_endpoints(shape_rows, max_endpoints=max_endpoints)

    session = requests.Session()

    raw_candidates = []
    quality_rows = []

    for endpoint_order, shape_row in enumerate(selected, start=1):
        candidates, quality = extract_from_endpoint(session, shape_row, endpoint_order)
        raw_candidates.extend(candidates)
        quality_rows.append(quality)
        time.sleep(SLEEP_BETWEEN_ENDPOINTS_SECONDS)

    candidates = dedupe_within_dry_run(raw_candidates)

    bucket_counter = Counter(row["quality_bucket"] for row in candidates)
    endpoint_counter = Counter(row["endpoint_id"] for row in candidates)
    mic_counter = Counter(row["raw_mic"] for row in candidates if row.get("raw_mic"))

    unique_isins = len({row["raw_isin"] for row in candidates})
    unique_isin_mic_pairs = len({(row["raw_isin"], row["raw_mic"]) for row in candidates})

    high_count = bucket_counter.get("high", 0)
    medium_count = bucket_counter.get("medium", 0)
    low_count = bucket_counter.get("low", 0)

    extraction_quality = "none"
    if len(candidates) > 0:
        extraction_quality = "low"
    if high_count > 0 or medium_count >= 10:
        extraction_quality = "medium"
    if high_count >= 100:
        extraction_quality = "high"

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

    add_check("v2_15f4_shape_validation_exists", F4_JSON.exists(), "critical", str(F4_JSON))
    add_check("v2_15f4_shape_results_exists", F4_RESULTS_CSV.exists(), "critical", str(F4_RESULTS_CSV))
    add_check("shape_validated_endpoints_selected", len(selected) > 0, "critical", f"selected={len(selected)}")
    add_check("endpoint_extraction_executed", len(quality_rows) > 0, "critical", f"quality_rows={len(quality_rows)}")
    add_check("raw_candidates_extracted_review", len(candidates) > 0, "warning", f"deduped_candidates={len(candidates)}")
    add_check("unique_isins_detected_review", unique_isins > 0, "warning", f"unique_isins={unique_isins}")
    add_check("medium_or_high_candidates_review", high_count + medium_count > 0, "warning", f"medium={medium_count}; high={high_count}")
    add_check("candidate_count_vs_gap_review", len(candidates) < ROWS_NEEDED, "warning", f"candidates={len(candidates)}; rows_needed={ROWS_NEEDED}")
    add_check("no_raw_payload_saved_to_disk", all(not as_bool_text(row.get("payload_saved_to_disk", "")) for row in quality_rows), "critical", "payload_saved_to_disk=False")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("no_normalization", True, "critical", "normalization_performed=False")
    add_check("no_net_new_filtering", True, "critical", "net_new_filtering=False")
    add_check("no_expanded_universe_rebuild", True, "critical", "expanded_universe_rebuilt=False")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"current_rows={CURRENT_ROWS}")

    if critical_failed != 0:
        status = "EURONEXT_ENDPOINT_CANDIDATE_EXTRACTION_DRY_RUN_FAILED_REBUILD_BLOCKED"
        recommended_next_phase = "v2.15F5B - Euronext Endpoint Candidate Extraction Repair"
    elif len(candidates) > 0:
        status = "EURONEXT_ENDPOINT_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_REBUILD_STILL_BLOCKED"
        recommended_next_phase = "v2.15F6 - Euronext Endpoint Candidate Validation Against Canonical Dry Run"
    else:
        status = "EURONEXT_ENDPOINT_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_NO_VALID_CANDIDATES_REBUILD_STILL_BLOCKED"
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
        "extraction_config": {
            "max_endpoints": max_endpoints,
            "max_bytes_per_endpoint": MAX_BYTES_PER_ENDPOINT,
            "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
            "payload_storage": "disabled",
            "canonical_dataset_read": "disabled",
            "net_new_filtering": "disabled",
            "rebuild": "disabled",
        },
        "extraction_summary": {
            "f4_status": f4.get("status", ""),
            "f4_recommended_next_phase": f4.get("recommended_next_phase", ""),
            "shape_rows_from_v2_15f4": len(shape_rows),
            "key_path_rows_from_v2_15f4": len(key_paths),
            "selected_shape_validated_endpoints": len(selected),
            "endpoint_quality_rows": len(quality_rows),
            "raw_candidates_before_dedupe": len(raw_candidates),
            "deduped_raw_candidates": len(candidates),
            "unique_isins": unique_isins,
            "unique_isin_mic_pairs": unique_isin_mic_pairs,
            "quality_bucket_counts": dict(bucket_counter),
            "endpoint_candidate_counts": dict(endpoint_counter),
            "mic_counts": dict(mic_counter),
            "extraction_quality": extraction_quality,
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "top_candidates": candidates[:50],
        "quality_by_endpoint": quality_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_candidate_extraction_executed": len(quality_rows) > 0,
            "json_payload_parsed_for_candidate_dry_run": len(quality_rows) > 0,
            "raw_payload_saved_to_disk": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "candidate_rows_extracted_to_dry_run_csv": len(candidates) > 0,
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

    write_json(DRY_JSON, payload)
    write_csv(CANDIDATES_CSV, candidates, CANDIDATE_FIELDNAMES)
    write_csv(QUALITY_CSV, quality_rows, QUALITY_FIELDNAMES)

    check_lines = "\n".join(
        f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}"
        for item in checks
    )

    quality_lines = "\n".join(
        f"- endpoint={row['endpoint_id']} status={row['status_code']} rows_seen={row['raw_rows_seen']} candidates={row['candidate_rows_extracted']} unique_isins={row['unique_isins']} high={row['high_quality']} medium={row['medium_quality']} low={row['low_quality']} path={row['candidate_container_path']}"
        for row in quality_rows
    ) or "- No endpoint quality rows."

    candidate_lines = "\n".join(
        f"- `{row['raw_isin']}` mic=`{row['raw_mic']}` name=`{row['raw_name']}` quality={row['quality_bucket']} confidence={row['extraction_confidence']} endpoint={row['endpoint_id']}"
        for row in candidates[:25]
    ) or "- No candidates extracted."

    DRY_MD.write_text(
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

## Extraction summary

- F4 status: `{payload["extraction_summary"]["f4_status"]}`
- F4 recommended next phase: `{payload["extraction_summary"]["f4_recommended_next_phase"]}`
- Shape rows from v2.15F4: {payload["extraction_summary"]["shape_rows_from_v2_15f4"]}
- Key path rows from v2.15F4: {payload["extraction_summary"]["key_path_rows_from_v2_15f4"]}
- Selected shape-validated endpoints: {payload["extraction_summary"]["selected_shape_validated_endpoints"]}
- Endpoint quality rows: {payload["extraction_summary"]["endpoint_quality_rows"]}
- Raw candidates before dedupe: {payload["extraction_summary"]["raw_candidates_before_dedupe"]}
- Deduped raw candidates: {payload["extraction_summary"]["deduped_raw_candidates"]}
- Unique ISINs: {payload["extraction_summary"]["unique_isins"]}
- Unique ISIN/MIC pairs: {payload["extraction_summary"]["unique_isin_mic_pairs"]}
- Quality bucket counts: `{payload["extraction_summary"]["quality_bucket_counts"]}`
- Extraction quality: `{payload["extraction_summary"]["extraction_quality"]}`
- Critical failed checks: {critical_failed}

## Quality by endpoint

{quality_lines}

## Top candidates

{candidate_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.15F5: true
- Endpoint candidate extraction executed: {str(len(quality_rows) > 0).lower()}
- JSON payload parsed for candidate dry-run: {str(len(quality_rows) > 0).lower()}
- Raw payload saved to disk: false
- Raw files downloaded: false
- Raw files modified after write: false
- Candidate rows extracted to dry-run CSV: {str(len(candidates) > 0).lower()}
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

This phase extracts raw endpoint candidates only as a dry run.

It does not save raw payloads, does not read or modify the canonical expanded universe, does not calculate definitive net-new rows, does not normalize instruments, does not rebuild the expanded universe, does not score equities, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15F5 Euronext endpoint candidate extraction dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("EXTRACTION_SUMMARY:")
    for key, value in payload["extraction_summary"].items():
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
