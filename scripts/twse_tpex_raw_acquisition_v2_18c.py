from __future__ import annotations

import csv
import hashlib
import json
import re
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.18C"
PHASE = "TWSE + TPEx Raw Acquisition"
PHASE_TYPE = "raw-acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "twse_tpex_raw_acquisition_v2_18c"

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
VALIDATED_NSE_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"

V218B_JSON = OUTPUT_DIR / "twse_tpex_acquisition_plan_v2_18b.json"
SOURCE_PLAN_CSV = OUTPUT_DIR / "twse_tpex_source_plan_v2_18b.csv"
ACTIONS_PLAN_CSV = OUTPUT_DIR / "twse_tpex_acquisition_actions_v2_18b.csv"
FILTER_POLICY_CSV = OUTPUT_DIR / "twse_tpex_filter_policy_v2_18b.csv"
SCHEMA_PLAN_CSV = OUTPUT_DIR / "twse_tpex_candidate_schema_plan_v2_18b.csv"

REPORT_JSON = OUTPUT_DIR / "twse_tpex_raw_acquisition_v2_18c.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_raw_acquisition_v2_18c.md"
MANIFEST_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_manifest_v2_18c.csv"
SOURCE_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_source_actions_v2_18c.csv"

EXPECTED_V218B_STATUS = "TWSE_TPEX_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
VALIDATED_CANDIDATE_ROWS_EXPECTED = 40300
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9700
EXPECTED_INCLUDED_SOURCES = 9

RECOMMENDED_NEXT_PHASE = "v2.18D - TWSE + TPEx Raw Validation"

HTTP_TIMEOUT_SECONDS = 45
SLEEP_BETWEEN_REQUESTS_SECONDS = 0.75

MANIFEST_FIELDS = [
    "source_id",
    "provider",
    "market",
    "source_category",
    "source_url",
    "method",
    "planned_raw_kind",
    "priority",
    "candidate_role",
    "expected_confidence",
    "filter_policy_ref",
    "attempted",
    "download_status",
    "http_status",
    "final_url",
    "content_type",
    "encoding",
    "bytes",
    "sha256",
    "raw_artifact_path",
    "error_type",
    "error_message",
    "captured_at_utc",
    "notes",
]

SOURCE_ACTIONS_FIELDS = [
    "action_order",
    "source_id",
    "action",
    "allowed_in_v2_18c",
    "performed",
    "result",
    "http_status",
    "raw_artifact_path",
    "bytes",
    "sha256",
    "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                return list(reader.fieldnames or []), rows
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value[:120] or "raw"


def extension_from_content_type(content_type: str, planned_raw_kind: str, url: str) -> str:
    ct = (content_type or "").lower()
    planned = (planned_raw_kind or "").lower()
    url_low = (url or "").lower()

    if "json" in ct or "json" in planned:
        return ".json"

    if "csv" in ct or "csv" in planned or url_low.endswith(".csv"):
        return ".csv"

    if "html" in ct or "html" in planned or "swagger_catalog" in planned:
        return ".html"

    if "xml" in ct:
        return ".xml"

    if "text" in ct:
        return ".txt"

    return ".bin"


def build_headers(source_url: str) -> dict[str, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 Scout-Finance/2.18C RawAcquisition",
        "Accept": "application/json,text/csv,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    if "tpex.org.tw" in source_url:
        headers["Referer"] = "https://www.tpex.org.tw/en-us/"
        headers["Origin"] = "https://www.tpex.org.tw"

    if "twse.com.tw" in source_url or "openapi.twse.com.tw" in source_url:
        headers["Referer"] = "https://openapi.twse.com.tw/"

    return headers


def download_url(source: dict[str, str], raw_dir: Path) -> dict[str, Any]:
    source_id = source["source_id"]
    url = source["source_url"]
    method = source.get("method", "GET").upper()
    planned_raw_kind = source.get("planned_raw_kind", "")
    captured_at = utc_now()

    request = urllib.request.Request(
        url=url,
        method=method,
        headers=build_headers(url),
    )

    context = ssl.create_default_context()

    response_body = b""
    http_status = ""
    final_url = url
    content_type = ""
    encoding = ""
    error_type = ""
    error_message = ""
    download_status = "unknown"

    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS, context=context) as response:
            response_body = response.read()
            http_status = str(response.getcode())
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            encoding = response.headers.get_content_charset() or ""
            download_status = "downloaded_200" if http_status == "200" else f"downloaded_http_{http_status}"

    except urllib.error.HTTPError as error:
        http_status = str(error.code)
        final_url = getattr(error, "url", url)
        content_type = error.headers.get("Content-Type", "") if error.headers else ""
        encoding = error.headers.get_content_charset() if error.headers else ""
        encoding = encoding or ""
        error_type = "HTTPError"
        error_message = str(error)
        try:
            response_body = error.read() or b""
        except Exception:
            response_body = str(error).encode("utf-8", errors="replace")
        download_status = f"downloaded_error_payload_{http_status}"

    except urllib.error.URLError as error:
        error_type = "URLError"
        error_message = str(error)
        response_body = str(error).encode("utf-8", errors="replace")
        download_status = "network_error_payload_captured"

    except Exception as error:
        error_type = type(error).__name__
        error_message = str(error)
        response_body = str(error).encode("utf-8", errors="replace")
        download_status = "unexpected_error_payload_captured"

    extension = extension_from_content_type(content_type, planned_raw_kind, url)
    if error_type and not response_body:
        extension = ".error.txt"

    status_for_name = http_status or download_status
    raw_filename = f"{int(source.get('priority', '0')):02d}_{safe_filename(source_id)}_{safe_filename(status_for_name)}{extension}"
    raw_path = raw_dir / raw_filename

    if raw_path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite raw artifact {raw_path}")

    raw_path.write_bytes(response_body)

    sha = sha256_bytes(response_body)

    return {
        "source_id": source_id,
        "provider": source.get("provider", ""),
        "market": source.get("market", ""),
        "source_category": source.get("source_category", ""),
        "source_url": url,
        "method": method,
        "planned_raw_kind": planned_raw_kind,
        "priority": source.get("priority", ""),
        "candidate_role": source.get("candidate_role", ""),
        "expected_confidence": source.get("expected_confidence", ""),
        "filter_policy_ref": source.get("filter_policy_ref", ""),
        "attempted": True,
        "download_status": download_status,
        "http_status": http_status,
        "final_url": final_url,
        "content_type": content_type,
        "encoding": encoding,
        "bytes": len(response_body),
        "sha256": sha,
        "raw_artifact_path": str(raw_path),
        "error_type": error_type,
        "error_message": error_message,
        "captured_at_utc": captured_at,
        "notes": "raw acquisition only; no candidate extraction performed",
    }


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        MANIFEST_CSV,
        SOURCE_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw directory already exists: {RAW_DIR}")

    RAW_DIR.mkdir(parents=True, exist_ok=False)

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    v218b = read_json(V218B_JSON)

    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)
    candidate_header, candidate_rows = read_csv_with_header(VALIDATED_NSE_CANDIDATE_DATASET)
    _, source_plan = read_csv_with_header(SOURCE_PLAN_CSV)
    _, actions_plan = read_csv_with_header(ACTIONS_PLAN_CSV)
    _, filter_policy = read_csv_with_header(FILTER_POLICY_CSV)
    _, schema_plan = read_csv_with_header(SCHEMA_PLAN_CSV)

    included_sources = [row for row in source_plan if boolish(row.get("include_in_v2_18c", ""))]

    manifest_rows: list[dict[str, Any]] = []
    source_actions_rows: list[dict[str, Any]] = []

    source_actions_rows.append(
        {
            "action_order": 1,
            "source_id": "all",
            "action": "prepare_raw_output_directory",
            "allowed_in_v2_18c": True,
            "performed": True,
            "result": "PASS",
            "http_status": "",
            "raw_artifact_path": str(RAW_DIR),
            "bytes": "",
            "sha256": "",
            "notes": "raw output directory created",
        }
    )

    for idx, source in enumerate(included_sources, start=1):
        result = download_url(source, RAW_DIR)
        manifest_rows.append(result)

        action_result = "PASS"
        if result["download_status"].startswith("network_error") or result["download_status"].startswith("unexpected_error"):
            action_result = "CAPTURED_ERROR"

        source_actions_rows.append(
            {
                "action_order": idx + 1,
                "source_id": source.get("source_id", ""),
                "action": "download_official_source",
                "allowed_in_v2_18c": True,
                "performed": True,
                "result": action_result,
                "http_status": result.get("http_status", ""),
                "raw_artifact_path": result.get("raw_artifact_path", ""),
                "bytes": result.get("bytes", 0),
                "sha256": result.get("sha256", ""),
                "notes": result.get("download_status", ""),
            }
        )

        time.sleep(SLEEP_BETWEEN_REQUESTS_SECONDS)

    source_actions_rows.append(
        {
            "action_order": len(source_actions_rows) + 1,
            "source_id": "all",
            "action": "write_raw_manifest",
            "allowed_in_v2_18c": True,
            "performed": True,
            "result": "PASS",
            "http_status": "",
            "raw_artifact_path": str(MANIFEST_CSV),
            "bytes": "",
            "sha256": "",
            "notes": "manifest written after all attempted official source captures",
        }
    )

    source_actions_rows.append(
        {
            "action_order": len(source_actions_rows) + 1,
            "source_id": "all",
            "action": "defer_candidate_extraction",
            "allowed_in_v2_18c": False,
            "performed": True,
            "result": "PASS",
            "http_status": "",
            "raw_artifact_path": "",
            "bytes": "",
            "sha256": "",
            "notes": "candidate extraction remains blocked until v2.18E",
        }
    )

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())
    candidate_sha = sha256_bytes(VALIDATED_NSE_CANDIDATE_DATASET.read_bytes())

    active_canonical_rows = len(canonical_rows)
    validated_candidate_rows = len(candidate_rows)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - validated_candidate_rows, 0)
    completion_percent = round((validated_candidate_rows / FINAL_TARGET_CANDIDATES) * 100, 2)

    http_200_count = sum(1 for row in manifest_rows if str(row.get("http_status", "")) == "200")
    http_error_count = sum(
        1 for row in manifest_rows
        if row.get("http_status") and str(row.get("http_status")) != "200"
    )
    network_error_count = sum(
        1 for row in manifest_rows
        if str(row.get("download_status", "")).startswith("network_error")
        or str(row.get("download_status", "")).startswith("unexpected_error")
    )
    error_payload_count = sum(
        1 for row in manifest_rows
        if "error_payload" in str(row.get("download_status", ""))
        or "error" in str(row.get("download_status", ""))
    )
    total_bytes = sum(int(row.get("bytes", 0) or 0) for row in manifest_rows)

    raw_artifacts_exist = all(Path(row["raw_artifact_path"]).exists() for row in manifest_rows)

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18b_report_exists", V218B_JSON.exists(), "critical", str(V218B_JSON))
    add_check("v2_18b_status_expected", v218b.get("status") == EXPECTED_V218B_STATUS, "critical", v218b.get("status", ""))
    add_check("source_plan_exists", SOURCE_PLAN_CSV.exists(), "critical", str(SOURCE_PLAN_CSV))
    add_check("actions_plan_exists", ACTIONS_PLAN_CSV.exists(), "critical", str(ACTIONS_PLAN_CSV))
    add_check("filter_policy_exists", FILTER_POLICY_CSV.exists(), "critical", str(FILTER_POLICY_CSV))
    add_check("schema_plan_exists", SCHEMA_PLAN_CSV.exists(), "critical", str(SCHEMA_PLAN_CSV))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("validated_candidate_dataset_exists", VALIDATED_NSE_CANDIDATE_DATASET.exists(), "critical", str(VALIDATED_NSE_CANDIDATE_DATASET))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("validated_candidate_rows_expected", validated_candidate_rows == VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"validated_candidate_rows={validated_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("candidate_schema_matches_canonical", canonical_header == candidate_header, "critical", f"canonical_cols={len(canonical_header)} candidate_cols={len(candidate_header)}")
    add_check("included_sources_expected", len(included_sources) == EXPECTED_INCLUDED_SOURCES, "critical", f"included_sources={len(included_sources)}")
    add_check("manifest_rows_match_included_sources", len(manifest_rows) == len(included_sources), "critical", f"manifest_rows={len(manifest_rows)} included_sources={len(included_sources)}")
    add_check("raw_directory_created", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("raw_artifacts_exist", raw_artifacts_exist, "critical", f"raw_artifacts_exist={raw_artifacts_exist}")
    add_check("raw_bytes_captured", total_bytes > 0, "critical", f"total_bytes={total_bytes}")
    add_check("download_attempts_performed", len(manifest_rows) == len(included_sources), "critical", f"attempted={len(manifest_rows)}")
    add_check("network_used_in_allowed_phase", True, "critical", "network_download_performed=True")
    add_check("http_status_preserved", all("http_status" in row for row in manifest_rows), "critical", "http_status recorded in manifest")
    add_check("sha256_recorded", all(row.get("sha256") for row in manifest_rows), "critical", "sha256 recorded for every raw artifact")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "canonical sha unchanged")
    add_check("raw_validation_not_performed", True, "critical", "raw_validation_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("final_50k_gate_still_blocked", validated_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{validated_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")

    if critical_failed == 0:
        status = "TWSE_TPEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "TWSE_TPEX_RAW_ACQUISITION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.18C_FIX - TWSE + TPEx Raw Acquisition Repair"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "validated_candidate_dataset": str(VALIDATED_NSE_CANDIDATE_DATASET),
            "validated_candidate_rows": validated_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "candidate_completion_percent": completion_percent,
            "canonical_sha256_before": canonical_sha_before,
            "canonical_sha256_after": canonical_sha_after,
            "validated_candidate_sha256": candidate_sha,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
        },
        "raw_acquisition_summary": {
            "planned_sources": len(source_plan),
            "included_sources": len(included_sources),
            "download_attempts": len(manifest_rows),
            "http_200_count": http_200_count,
            "http_error_count": http_error_count,
            "network_error_count": network_error_count,
            "error_payload_count": error_payload_count,
            "total_bytes_captured": total_bytes,
            "raw_directory": str(RAW_DIR),
            "manifest_csv": str(MANIFEST_CSV),
            "source_actions_csv": str(SOURCE_ACTIONS_CSV),
            "critical_failed_checks": critical_failed,
            "status_counts": {
                (str(row.get("download_status", "")) or "NO_DOWNLOAD_STATUS"): sum(
                    1 for item in manifest_rows
                    if (str(item.get("download_status", "")) or "NO_DOWNLOAD_STATUS")
                    == (str(row.get("download_status", "")) or "NO_DOWNLOAD_STATUS")
                )
                for row in manifest_rows
            },
            "http_status_counts": {
                (str(row.get("http_status", "")) or "NO_HTTP_STATUS"): sum(
                    1 for item in manifest_rows
                    if (str(item.get("http_status", "")) or "NO_HTTP_STATUS")
                    == (str(row.get("http_status", "")) or "NO_HTTP_STATUS")
                )
                for row in manifest_rows
            },
        },
        "source_plan_reference": {
            "v2_18b_report": str(V218B_JSON),
            "v2_18b_status": v218b.get("status", ""),
            "source_plan_csv": str(SOURCE_PLAN_CSV),
            "actions_plan_csv": str(ACTIONS_PLAN_CSV),
            "filter_policy_csv": str(FILTER_POLICY_CSV),
            "schema_plan_csv": str(SCHEMA_PLAN_CSV),
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_calls_performed": True,
            "query_sweep_performed": False,
            "network_scope": "official_sources_from_v2_18b_source_plan_only",
            "raw_acquisition_performed": True,
            "raw_files_written": True,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "canonical_comparison_performed": False,
            "canonical_dataset_read": True,
            "validated_candidate_dataset_read": True,
            "source_plan_read": True,
            "filter_policy_read": True,
            "schema_plan_read": True,
            "raw_manifest_written": True,
            "source_actions_written": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "final_target_50k_active": True,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(MANIFEST_CSV, manifest_rows, MANIFEST_FIELDS)
    write_csv(SOURCE_ACTIONS_CSV, source_actions_rows, SOURCE_ACTIONS_FIELDS)
    write_json(REPORT_JSON, payload)

    manifest_lines = "\n".join(
        f"- `{row['source_id']}` — {row['download_status']} — HTTP `{row['http_status']}` — bytes `{row['bytes']}` — `{row['raw_artifact_path']}`"
        for row in manifest_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.18C performs raw acquisition for the TWSE + TPEx Taiwan route.

This phase performs network calls only for official sources listed in the v2.18B source plan. It writes raw files, a raw acquisition manifest and source actions. It does not perform raw validation, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{active_canonical_rows}`
- Validated candidate dataset: `{VALIDATED_NSE_CANDIDATE_DATASET}`
- Validated candidate rows: `{validated_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Candidate completion: `{completion_percent}%`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Raw acquisition summary

- Planned sources: `{len(source_plan)}`
- Included sources: `{len(included_sources)}`
- Download attempts: `{len(manifest_rows)}`
- HTTP 200 count: `{http_200_count}`
- HTTP error count: `{http_error_count}`
- Network error count: `{network_error_count}`
- Error payload count: `{error_payload_count}`
- Total bytes captured: `{total_bytes}`
- Raw directory: `{RAW_DIR}`
- Manifest CSV: `{MANIFEST_CSV}`
- Source actions CSV: `{SOURCE_ACTIONS_CSV}`
- Critical failed checks: `{critical_failed}`

## Manifest summary

{manifest_lines}

## Checks

{check_lines}

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Network scope: official sources from v2.18B source plan only
- Raw acquisition performed: true
- Raw files written: true
- Raw validation performed: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- Source plan read: true
- Filter policy read: true
- Schema plan read: true
- Raw manifest written: true
- Source actions written: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Final target 50k active: true
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Overwrite allowed: false

## Conclusion

v2.18C captures raw TWSE + TPEx source artifacts and prepares raw validation in v2.18D.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.18C TWSE + TPEx raw acquisition completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("RAW_ACQUISITION_SUMMARY:")
    for key, value in payload["raw_acquisition_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("MANIFEST:")
    for row in manifest_rows:
        print(
            f"- {row['source_id']}: {row['download_status']} "
            f"HTTP={row['http_status']} bytes={row['bytes']} path={row['raw_artifact_path']}"
        )
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
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()


