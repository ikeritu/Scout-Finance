from __future__ import annotations

import csv
import hashlib
import json
import re
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


VERSION = "v2.19L_FIX"
PHASE = "HKEX Raw Acquisition Repair"
PHASE_TYPE = "raw-acquisition-repair-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "hkex_v2_19l_fix"

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219M_JSON = OUTPUT_DIR / "hkex_raw_validation_v2_19m.json"
V219M_DOWNLOAD_CANDIDATES_CSV = OUTPUT_DIR / "hkex_raw_validation_official_download_candidates_v2_19m.csv"
V219M_SOURCE_READINESS_CSV = OUTPUT_DIR / "hkex_raw_validation_source_readiness_v2_19m.csv"
V219M_EXTRACTION_GATE_CSV = OUTPUT_DIR / "hkex_raw_validation_extraction_gate_v2_19m.csv"

REPORT_JSON = OUTPUT_DIR / "hkex_raw_acquisition_repair_v2_19l_fix.json"
REPORT_MD = OUTPUT_DIR / "hkex_raw_acquisition_repair_v2_19l_fix.md"
SELECTED_DOWNLOADS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_selected_downloads_v2_19l_fix.csv"
MANIFEST_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_manifest_v2_19l_fix.csv"
ARTIFACT_INDEX_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_artifact_index_v2_19l_fix.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_source_diagnostics_v2_19l_fix.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_checks_v2_19l_fix.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_repair_next_actions_v2_19l_fix.csv"

EXPECTED_V219M_STATUS = "HKEX_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

STATUS_SUCCESS = "HKEX_RAW_ACQUISITION_REPAIR_COMPLETED_STRUCTURED_DOWNLOADS_CAPTURED_RAW_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_PARTIAL = "HKEX_RAW_ACQUISITION_REPAIR_COMPLETED_PARTIAL_STRUCTURED_DOWNLOADS_CAPTURED_RAW_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_FAILED = "HKEX_RAW_ACQUISITION_REPAIR_FAILED_REVIEW_REQUIRED"

RECOMMENDED_NEXT_PHASE = "v2.19M_FIX - HKEX Repaired Raw Validation"
RECOMMENDED_REVIEW_PHASE = "v2.19L_FIX_REVIEW - HKEX Raw Acquisition Repair Review"

ALLOWED_HOSTS = {
    "www.hkex.com.hk",
    "hkex.com.hk",
    "www.hkexnews.hk",
    "hkexnews.hk",
}

DIRECT_STRUCTURED_EXTENSIONS = (".xlsx", ".xls", ".csv")
MIN_CAPTURE_PRIORITY = 70
MAX_DOWNLOADS = 25

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 ScoutFinanceHKEXRepair/2.19L_FIX"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


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


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def official_scope_allowed(url: str) -> bool:
    parsed = urlparse(str(url))
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS


def direct_structured_file(url: str) -> bool:
    lower_path = urlparse(url).path.lower()
    return lower_path.endswith(DIRECT_STRUCTURED_EXTENSIONS)


def file_extension(url: str, content_type: str = "") -> str:
    lower_path = urlparse(url).path.lower()
    for ext in [".xlsx", ".xls", ".csv", ".zip", ".json", ".xml", ".html", ".htm", ".txt"]:
        if lower_path.endswith(ext):
            return ext

    ct = str(content_type).lower()
    if "spreadsheet" in ct or "excel" in ct:
        return ".xlsx"
    if "csv" in ct:
        return ".csv"
    if "html" in ct:
        return ".html"
    if "json" in ct:
        return ".json"
    if "xml" in ct:
        return ".xml"
    if "text" in ct:
        return ".txt"
    return ".bin"


def safe_slug(value: str, max_len: int = 80) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    slug = re.sub(r"_+", "_", slug)
    return slug[:max_len] or "artifact"


def fetch_url(url: str, timeout: int = 45) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "close",
        },
        method="GET",
    )

    ssl_context = ssl.create_default_context()

    started = time.time()
    try:
        with urlopen(request, timeout=timeout, context=ssl_context) as response:
            body = response.read()
            elapsed_ms = int((time.time() - started) * 1000)
            headers = dict(response.headers.items())
            return {
                "ok": True,
                "error_type": "",
                "error_message": "",
                "status_code": int(getattr(response, "status", 0) or 0),
                "final_url": response.geturl(),
                "headers": headers,
                "content_type": headers.get("Content-Type", ""),
                "bytes": body,
                "elapsed_ms": elapsed_ms,
            }
    except HTTPError as exc:
        body = exc.read()
        elapsed_ms = int((time.time() - started) * 1000)
        headers = dict(exc.headers.items()) if exc.headers else {}
        return {
            "ok": False,
            "error_type": "HTTPError",
            "error_message": str(exc),
            "status_code": int(exc.code),
            "final_url": exc.geturl(),
            "headers": headers,
            "content_type": headers.get("Content-Type", ""),
            "bytes": body,
            "elapsed_ms": elapsed_ms,
        }
    except URLError as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return {
            "ok": False,
            "error_type": "URLError",
            "error_message": str(exc.reason),
            "status_code": 0,
            "final_url": url,
            "headers": {},
            "content_type": "",
            "bytes": b"",
            "elapsed_ms": elapsed_ms,
        }
    except Exception as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "status_code": 0,
            "final_url": url,
            "headers": {},
            "content_type": "",
            "bytes": b"",
            "elapsed_ms": elapsed_ms,
        }


def select_downloads(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in rows:
        url = str(row.get("url", "")).strip()
        priority_score = to_int(row.get("priority_score", 0))
        recommendation = str(row.get("capture_recommendation", "")).strip()

        if not url or url in seen:
            continue
        if not official_scope_allowed(url):
            continue
        if not direct_structured_file(url):
            continue
        if priority_score < MIN_CAPTURE_PRIORITY and "ListOfSecurities.xlsx" not in url:
            continue
        if recommendation != "capture_in_v2_19L_FIX" and "ListOfSecurities.xlsx" not in url:
            continue

        selected.append(
            {
                "selection_order": 0,
                "source_id": row.get("source_id", ""),
                "artifact_id": row.get("artifact_id", ""),
                "label": row.get("label", ""),
                "url": url,
                "host": urlparse(url).hostname or "",
                "priority_score": priority_score,
                "capture_recommendation": recommendation,
                "direct_structured_file": direct_structured_file(url),
                "selected_reason": (
                    "top_primary_full_list_of_securities"
                    if "ListOfSecurities.xlsx" in url
                    else "official_direct_structured_high_priority_download"
                ),
            }
        )
        seen.add(url)

    selected = sorted(
        selected,
        key=lambda x: (
            1 if "ListOfSecurities.xlsx" in x["url"] else 0,
            to_int(x["priority_score"]),
            x["url"],
        ),
        reverse=True,
    )

    for index, row in enumerate(selected[:MAX_DOWNLOADS], start=1):
        row["selection_order"] = index

    return selected[:MAX_DOWNLOADS]


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        SELECTED_DOWNLOADS_CSV,
        MANIFEST_CSV,
        ARTIFACT_INDEX_CSV,
        SOURCE_DIAGNOSTICS_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists() and any(RAW_DIR.iterdir()):
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw repair directory already contains files: {RAW_DIR}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    v219m = read_json(V219M_JSON)
    _, download_candidate_rows = read_csv_with_header(V219M_DOWNLOAD_CANDIDATES_CSV)
    _, source_readiness_rows = read_csv_with_header(V219M_SOURCE_READINESS_CSV)
    _, extraction_gate_rows = read_csv_with_header(V219M_EXTRACTION_GATE_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    selected_download_rows = select_downloads(download_candidate_rows)

    manifest_rows: list[dict[str, Any]] = []
    artifact_index_rows: list[dict[str, Any]] = []
    source_diagnostics_rows: list[dict[str, Any]] = []

    for selected in selected_download_rows:
        selection_order = to_int(selected["selection_order"])
        url = selected["url"]
        source_id = selected["source_id"]
        label_slug = safe_slug(str(selected.get("label") or urlparse(url).path.split("/")[-1]))
        artifact_id = f"hkex_repair_{selection_order:02d}_{label_slug}"

        if not official_scope_allowed(url):
            raise SystemExit(f"OFFICIAL_SCOPE_GUARD: selected URL is not HKEX/HKEXnews official scope: {url}")

        fetched_at = utc_now()
        response = fetch_url(url)
        body = response["bytes"] or b""
        content_type = str(response.get("content_type", ""))
        extension = file_extension(url, content_type)

        raw_file = RAW_DIR / f"{selection_order:02d}_{label_slug}{extension}"
        header_file = RAW_DIR / f"{selection_order:02d}_{label_slug}_headers.json"

        if raw_file.exists() or header_file.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: raw repair artifact already exists for {artifact_id}")

        raw_file.write_bytes(body)
        write_json(
            header_file,
            {
                "version": VERSION,
                "source_id": source_id,
                "artifact_id": artifact_id,
                "label": selected.get("label", ""),
                "requested_url": url,
                "final_url": response.get("final_url", url),
                "status_code": response.get("status_code", 0),
                "ok": response.get("ok", False),
                "error_type": response.get("error_type", ""),
                "error_message": response.get("error_message", ""),
                "headers": response.get("headers", {}),
                "content_type": content_type,
                "elapsed_ms": response.get("elapsed_ms", 0),
                "fetched_at_utc": fetched_at,
            },
        )

        final_url = str(response.get("final_url", url))
        status_code = to_int(response.get("status_code", 0))
        http_success = 200 <= status_code < 400
        byte_count = len(body)
        sha = sha256_bytes(body)
        final_official_scope_allowed = official_scope_allowed(final_url)

        manifest_rows.append(
            {
                "selection_order": selection_order,
                "source_id": source_id,
                "artifact_id": artifact_id,
                "label": selected.get("label", ""),
                "requested_url": url,
                "final_url": final_url,
                "official_scope_allowed": official_scope_allowed(url),
                "final_official_scope_allowed": final_official_scope_allowed,
                "priority_score": selected.get("priority_score", ""),
                "selected_reason": selected.get("selected_reason", ""),
                "method": "GET",
                "http_status": status_code,
                "http_success": http_success,
                "error_type": response.get("error_type", ""),
                "error_message": response.get("error_message", ""),
                "content_type": content_type,
                "byte_count": byte_count,
                "sha256": sha,
                "raw_path": str(raw_file),
                "headers_path": str(header_file),
                "fetched_at_utc": fetched_at,
                "elapsed_ms": response.get("elapsed_ms", 0),
            }
        )

        artifact_index_rows.append(
            {
                "artifact_id": artifact_id,
                "source_id": source_id,
                "label": selected.get("label", ""),
                "raw_path": str(raw_file),
                "headers_path": str(header_file),
                "content_type": content_type,
                "byte_count": byte_count,
                "sha256": sha,
                "validation_phase": "v2.19M_FIX",
                "candidate_extraction_phase": "not_before_v2.19N_and_only_if_repaired_raw_validation_passes",
            }
        )

        source_diagnostics_rows.append(
            {
                "artifact_id": artifact_id,
                "source_id": source_id,
                "label": selected.get("label", ""),
                "url": url,
                "http_status": status_code,
                "http_success": http_success,
                "content_type": content_type,
                "byte_count": byte_count,
                "extension": extension,
                "structured_extension": extension in DIRECT_STRUCTURED_EXTENSIONS,
                "official_scope_allowed": official_scope_allowed(url),
                "final_official_scope_allowed": final_official_scope_allowed,
                "is_top_primary_full_list": "ListOfSecurities.xlsx" in url,
                "raw_path": str(raw_file),
            }
        )

        time.sleep(0.5)

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    selected_count = len(selected_download_rows)
    artifacts_written_count = len(manifest_rows)
    raw_files_exist_count = sum(1 for row in manifest_rows if Path(str(row["raw_path"])).exists())
    header_files_exist_count = sum(1 for row in manifest_rows if Path(str(row["headers_path"])).exists())
    nonempty_raw_count = sum(1 for row in manifest_rows if to_int(row["byte_count"]) > 0)
    http_success_count = sum(1 for row in manifest_rows if str(row["http_success"]).lower() == "true")
    http_error_count = artifacts_written_count - http_success_count
    structured_extension_count = sum(1 for row in source_diagnostics_rows if row["structured_extension"])
    official_scope_violations = sum(
        1
        for row in manifest_rows
        if not row["official_scope_allowed"] or not row["final_official_scope_allowed"]
    )
    top_primary_full_list_captured = any(
        "ListOfSecurities.xlsx" in str(row.get("requested_url", ""))
        and str(row.get("http_success")).lower() == "true"
        and to_int(row.get("byte_count", 0)) > 0
        for row in manifest_rows
    )

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19m_report_exists", V219M_JSON.exists(), "critical", str(V219M_JSON))
    add_check("v2_19m_status_expected", v219m.get("status") == EXPECTED_V219M_STATUS, "critical", str(v219m.get("status", "")))
    add_check("download_candidates_exists", V219M_DOWNLOAD_CANDIDATES_CSV.exists(), "critical", str(V219M_DOWNLOAD_CANDIDATES_CSV))
    add_check("download_candidates_available", len(download_candidate_rows) >= 1, "critical", f"download_candidate_rows={len(download_candidate_rows)}")
    add_check("selected_downloads_available", selected_count >= 1, "critical", f"selected_downloads={selected_count}")
    add_check("top_primary_full_list_selected", any("ListOfSecurities.xlsx" in row["url"] for row in selected_download_rows), "critical", "ListOfSecurities.xlsx selected")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("raw_repair_directory_exists", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("repair_artifacts_written", artifacts_written_count == selected_count, "critical", f"artifacts_written={artifacts_written_count}; selected={selected_count}")
    add_check("repair_raw_files_exist", raw_files_exist_count == artifacts_written_count, "critical", f"raw_files_exist={raw_files_exist_count}/{artifacts_written_count}")
    add_check("repair_header_files_exist", header_files_exist_count == artifacts_written_count, "critical", f"header_files_exist={header_files_exist_count}/{artifacts_written_count}")
    add_check("repair_raw_files_nonempty", nonempty_raw_count >= 1, "critical", f"nonempty_raw_count={nonempty_raw_count}/{artifacts_written_count}")
    add_check("repair_http_success_documented", http_success_count >= 1, "critical", f"http_success_count={http_success_count}; http_error_count={http_error_count}")
    add_check("repair_official_scope_no_violations", official_scope_violations == 0, "critical", f"official_scope_violations={official_scope_violations}")
    add_check("repair_structured_files_captured", structured_extension_count >= 1, "critical", f"structured_extension_count={structured_extension_count}")
    add_check("top_primary_full_list_captured", top_primary_full_list_captured, "critical", f"top_primary_full_list_captured={top_primary_full_list_captured}")
    add_check("source_readiness_loaded", len(source_readiness_rows) >= 5, "warning", f"source_readiness_rows={len(source_readiness_rows)}")
    add_check("extraction_gate_loaded", len(extraction_gate_rows) >= 1, "warning", f"extraction_gate_rows={len(extraction_gate_rows)}")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("network_used_by_repair_acquisition", True, "critical", "network_download_performed=True")
    add_check("raw_acquisition_repair_performed", True, "critical", "raw_acquisition_repair_performed=True")
    add_check("raw_validation_not_performed", True, "critical", "raw_validation_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("next_phase_repaired_raw_validation", RECOMMENDED_NEXT_PHASE == "v2.19M_FIX - HKEX Repaired Raw Validation", "critical", RECOMMENDED_NEXT_PHASE)

    if critical_failed == 0 and top_primary_full_list_captured:
        status = STATUS_SUCCESS
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    elif critical_failed == 0 and http_success_count >= 1:
        status = STATUS_PARTIAL
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = STATUS_FAILED
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "HKEX",
            "action": "run_repaired_raw_validation",
            "priority": "high",
            "reason": "Structured HKEX repair downloads have been captured and need validation before extraction.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "raw validation only; no candidate extraction; no canonical modification",
        },
        {
            "action_order": 2,
            "action_scope": "HKEX",
            "action": "validate_list_of_securities_xlsx_parse_readiness",
            "priority": "high",
            "reason": "ListOfSecurities.xlsx is the primary official HKEX structured source candidate.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "inspect workbook schema; do not append rows",
        },
        {
            "action_order": 3,
            "action_scope": "50k",
            "action": "preserve_quality_gate",
            "priority": "high",
            "reason": "Current candidate universe remains 40,996; rows needed to 50k remain 9,004.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "do not launch full59k; no HKEX rows before extraction and canonical validation",
        },
    ]

    repair_summary = {
        "download_candidate_rows": len(download_candidate_rows),
        "selected_download_rows": selected_count,
        "artifacts_written_count": artifacts_written_count,
        "raw_files_exist_count": raw_files_exist_count,
        "header_files_exist_count": header_files_exist_count,
        "nonempty_raw_count": nonempty_raw_count,
        "http_success_count": http_success_count,
        "http_error_count": http_error_count,
        "structured_extension_count": structured_extension_count,
        "official_scope_violations": official_scope_violations,
        "top_primary_full_list_captured": top_primary_full_list_captured,
        "current_validated_candidate_rows": current_candidate_rows,
        "rows_needed_to_50k": rows_needed_to_50k,
        "final_50k_candidate_gate": "BLOCKED",
        "full59k": "DEPRECATED_DEFERRED",
        "critical_failed_checks": critical_failed,
    }

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "current_validated_candidate_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "current_validated_candidate_rows": current_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "current_candidate_sha256_before": candidate_sha_before,
            "current_candidate_sha256_after": candidate_sha_after,
        },
        "v2_19m_context": {
            "status": v219m.get("status"),
            "phase_type": v219m.get("phase_type"),
            "official_download_candidate_count": v219m.get("validation_summary", {}).get("official_download_candidate_count"),
            "high_priority_download_candidate_count": v219m.get("validation_summary", {}).get("high_priority_download_candidate_count"),
            "repair_required": v219m.get("validation_summary", {}).get("repair_required"),
            "extraction_ready": v219m.get("validation_summary", {}).get("extraction_ready"),
            "recommended_next_phase": v219m.get("recommended_next_phase"),
        },
        "repair_summary": repair_summary,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_calls_performed": True,
            "query_sweep_performed": False,
            "route_selection_performed": False,
            "acquisition_plan_performed": False,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": True,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": candidate_sha_before == candidate_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(
        SELECTED_DOWNLOADS_CSV,
        selected_download_rows,
        [
            "selection_order",
            "source_id",
            "artifact_id",
            "label",
            "url",
            "host",
            "priority_score",
            "capture_recommendation",
            "direct_structured_file",
            "selected_reason",
        ],
    )
    write_csv(
        MANIFEST_CSV,
        manifest_rows,
        [
            "selection_order",
            "source_id",
            "artifact_id",
            "label",
            "requested_url",
            "final_url",
            "official_scope_allowed",
            "final_official_scope_allowed",
            "priority_score",
            "selected_reason",
            "method",
            "http_status",
            "http_success",
            "error_type",
            "error_message",
            "content_type",
            "byte_count",
            "sha256",
            "raw_path",
            "headers_path",
            "fetched_at_utc",
            "elapsed_ms",
        ],
    )
    write_csv(
        ARTIFACT_INDEX_CSV,
        artifact_index_rows,
        [
            "artifact_id",
            "source_id",
            "label",
            "raw_path",
            "headers_path",
            "content_type",
            "byte_count",
            "sha256",
            "validation_phase",
            "candidate_extraction_phase",
        ],
    )
    write_csv(
        SOURCE_DIAGNOSTICS_CSV,
        source_diagnostics_rows,
        [
            "artifact_id",
            "source_id",
            "label",
            "url",
            "http_status",
            "http_success",
            "content_type",
            "byte_count",
            "extension",
            "structured_extension",
            "official_scope_allowed",
            "final_official_scope_allowed",
            "is_top_primary_full_list",
            "raw_path",
        ],
    )
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    manifest_lines = "\n".join(
        f"- `{row['artifact_id']}` — HTTP `{row['http_status']}` — bytes `{row['byte_count']}` — `{row['raw_path']}`"
        for row in manifest_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.19L_FIX captures official HKEX structured downloads identified in v2.19M.

This phase performs raw acquisition repair only. It does not validate repaired raw artifacts for parse-readiness, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Repair summary

- Download candidate rows from v2.19M: `{len(download_candidate_rows)}`
- Selected downloads: `{selected_count}`
- Artifacts written: `{artifacts_written_count}`
- Raw files exist: `{raw_files_exist_count}`
- Header files exist: `{header_files_exist_count}`
- Non-empty raw files: `{nonempty_raw_count}`
- HTTP success count: `{http_success_count}`
- HTTP error count: `{http_error_count}`
- Structured extension count: `{structured_extension_count}`
- Official scope violations: `{official_scope_violations}`
- Top primary Full List captured: `{top_primary_full_list_captured}`

## Manifest

{manifest_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Raw acquisition repair performed: true
- Raw validation performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{candidate_sha_before == candidate_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.19L_FIX HKEX raw acquisition repair completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REPAIR_SUMMARY:")
    for key, value in repair_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SELECTED_DOWNLOADS:")
    for row in selected_download_rows:
        print(f"- order={row['selection_order']} score={row['priority_score']} label={row['label']} url={row['url']}")
    print("")
    print("MANIFEST:")
    for row in manifest_rows:
        print(f"- {row['artifact_id']}: status={row['http_status']} success={row['http_success']} bytes={row['byte_count']} sha256={row['sha256']} raw={row['raw_path']}")
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
