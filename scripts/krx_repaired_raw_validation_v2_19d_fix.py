from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VERSION = "v2.19D_FIX"
PHASE = "KRX Repaired Raw Validation"
PHASE_TYPE = "repaired-raw-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_REPAIR_DIR = OUTPUT_DIR / "raw" / "krx_v2_19c_fix"

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219C_FIX_JSON = OUTPUT_DIR / "krx_raw_acquisition_repair_v2_19c_fix.json"
V219C_FIX_MANIFEST_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_manifest_v2_19c_fix.csv"
V219C_FIX_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_source_diagnostics_v2_19c_fix.csv"
V219C_FIX_HTML_SIGNAL_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_html_signal_inventory_v2_19c_fix.csv"
V219C_FIX_DISCOVERED_URLS_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_discovered_official_urls_v2_19c_fix.csv"
V219C_FIX_TABLE_PROBE_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_html_table_probe_v2_19c_fix.csv"

REPORT_JSON = OUTPUT_DIR / "krx_repaired_raw_validation_v2_19d_fix.json"
REPORT_MD = OUTPUT_DIR / "krx_repaired_raw_validation_v2_19d_fix.md"
ARTIFACT_AUDIT_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_artifact_audit_v2_19d_fix.csv"
SOURCE_READINESS_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_source_readiness_v2_19d_fix.csv"
ISSUE_AUDIT_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_issue_audit_v2_19d_fix.csv"
EXTRACTION_GATE_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_extraction_gate_v2_19d_fix.csv"
CHECKS_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_checks_v2_19d_fix.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "krx_repaired_raw_validation_next_actions_v2_19d_fix.csv"

EXPECTED_V219C_FIX_STATUS = "KRX_RAW_ACQUISITION_REPAIR_COMPLETED_REPAIRED_RAW_FILES_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

RECOMMENDED_EXTRACTION_PHASE = "v2.19E - KRX Candidate Extraction Dry Run"
RECOMMENDED_CLOSURE_PHASE = "v2.19I - KRX Closure Report"
RECOMMENDED_REVIEW_PHASE = "v2.19D_FIX_REVIEW - KRX Repaired Raw Validation Review"

ALLOWED_HOSTS = {
    "global.krx.co.kr",
    "data.krx.co.kr",
    "openapi.krx.co.kr",
    "www.data.go.kr",
    "apis.data.go.kr",
}

CANDIDATE_FIELD_SIGNALS = [
    "isin",
    "isincd",
    "isin_cd",
    "stock code",
    "short code",
    "shrtcd",
    "srtncd",
    "ticker",
    "symbol",
    "company name",
    "corp",
    "issue name",
    "market",
    "kospi",
    "kosdaq",
    "konex",
    "listed",
    "listing",
]

NON_CANDIDATE_REFERENCE_HINTS = [
    "json2.min.js",
    "catalog_json",
    "openapi_catalog",
    "warmup",
    "download_guide",
    "discovered_official_url",
    "session_warmup",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def decode_bytes(data: bytes) -> str:
    for encoding in ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"]:
        try:
            return data.decode(encoding, errors="ignore")
        except Exception:
            continue
    return data.decode("utf-8", errors="ignore")


def read_sample(path: Path, max_bytes: int = 750000) -> str:
    if not path.exists():
        return ""
    return decode_bytes(path.read_bytes()[:max_bytes])


def is_official_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"https", "http"} and parsed.hostname in ALLOWED_HOSTS


def count_signal(text: str, tokens: list[str]) -> int:
    lower = text.lower()
    return sum(lower.count(token.lower()) for token in tokens)


def looks_like_error_payload(text: str, http_status: str, acquisition_status: str) -> bool:
    lower = text.lower()
    if http_status in {"403", "404", "500", "503"}:
        return True
    if "not_attempted" in acquisition_status:
        return True
    return any(token in lower for token in ["forbidden", "access denied", "invalidotp", "missingservicekey", "not attempted"])


def estimate_csv_rows_from_text(text: str) -> int:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) <= 1:
        return 0
    comma_like = sum(1 for line in lines[:25] if "," in line or "\t" in line or "|" in line)
    if comma_like == 0:
        return 0
    return max(len(lines) - 1, 0)


def estimate_json_record_count(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    try:
        payload = json.loads(stripped)
    except Exception:
        return 0

    def walk(obj: Any) -> int:
        if isinstance(obj, list):
            if obj and all(isinstance(item, dict) for item in obj):
                return len(obj)
            return max([walk(item) for item in obj] or [0])
        if isinstance(obj, dict):
            return max([walk(value) for value in obj.values()] or [0])
        return 0

    return walk(payload)


def classify_candidate_readiness(row: dict[str, str], sample: str) -> tuple[str, str, bool, int, int]:
    source_id = row.get("source_id", "")
    source_role = row.get("source_role", "")
    artifact_id = row.get("artifact_id", "")
    artifact_path = row.get("artifact_path", "")
    http_status = str(row.get("http_status", ""))
    acquisition_status = row.get("acquisition_status", "")
    parse_hint = row.get("parse_hint", "")
    artifact_bytes = to_int(row.get("artifact_bytes", 0))

    lower_join = " ".join([source_id, source_role, artifact_id, artifact_path, sample[:5000]]).lower()

    candidate_signal_count = count_signal(sample, CANDIDATE_FIELD_SIGNALS)
    estimated_rows = 0

    if artifact_bytes <= 0:
        return "empty_artifact", "Artifact is empty.", False, 0, candidate_signal_count

    if looks_like_error_payload(sample, http_status, acquisition_status):
        if "missing_service_key" in acquisition_status or "service_key" in artifact_id:
            return "optional_api_missing_key_not_candidate_ready", "Optional data.go.kr API was not attempted because the service key is missing.", False, 0, candidate_signal_count
        if "invalid_otp" in acquisition_status:
            return "invalid_otp_not_candidate_ready", "CSV download was not attempted because OTP was invalid.", False, 0, candidate_signal_count
        return "http_or_diagnostic_payload_not_candidate_ready", "Artifact is an HTTP/error/diagnostic payload, not candidate row data.", False, 0, candidate_signal_count

    if any(token in lower_join for token in NON_CANDIDATE_REFERENCE_HINTS):
        if parse_hint in {"json_like", "csv_like", "xml_or_api_payload", "xlsx_or_zip_container"}:
            return "structured_reference_not_candidate_ready", "Structured artifact appears to be reference/catalog/script data, not listed-company rows.", False, 0, candidate_signal_count
        return "reference_or_warmup_not_candidate_ready", "Artifact is reference, warmup, script or discovered-page evidence, not candidate row data.", False, 0, candidate_signal_count

    if parse_hint == "csv_like":
        estimated_rows = estimate_csv_rows_from_text(sample)
        if source_role in {"primary_candidate_source", "primary_or_crosscheck_source"} and estimated_rows >= 100 and candidate_signal_count >= 2:
            return "primary_csv_candidate_ready", "Primary CSV-like artifact appears to contain candidate row data.", True, estimated_rows, candidate_signal_count
        return "csv_like_not_candidate_ready", "CSV-like artifact does not meet candidate row/signal threshold.", False, estimated_rows, candidate_signal_count

    if parse_hint == "json_like":
        estimated_rows = estimate_json_record_count(sample)
        if source_role in {"primary_candidate_source", "primary_or_crosscheck_source", "supporting_or_fallback_source"} and estimated_rows >= 100 and candidate_signal_count >= 2:
            return "structured_json_candidate_ready", "JSON-like artifact appears to contain listed-stock records.", True, estimated_rows, candidate_signal_count
        return "json_like_not_candidate_ready", "JSON-like artifact does not meet listed-stock row/signal threshold.", False, estimated_rows, candidate_signal_count

    if parse_hint == "xml_or_api_payload":
        estimated_rows = len(re.findall(r"<item>|<item\s|<body>|<items>", sample, flags=re.I))
        if source_role in {"supporting_or_fallback_source"} and estimated_rows >= 100 and candidate_signal_count >= 2:
            return "api_xml_candidate_ready", "API XML-like artifact appears to contain listed-stock records.", True, estimated_rows, candidate_signal_count
        return "xml_like_not_candidate_ready", "XML/API-like artifact does not meet listed-stock row/signal threshold.", False, estimated_rows, candidate_signal_count

    if parse_hint == "xlsx_or_zip_container":
        if source_role in {"primary_candidate_source", "primary_or_crosscheck_source"}:
            return "xlsx_container_candidate_probe_required", "XLSX/ZIP structured primary artifact captured; validation marks as probe-ready for extraction phase.", True, 0, candidate_signal_count
        return "xlsx_reference_not_candidate_ready", "XLSX/ZIP artifact is not from a primary candidate source.", False, 0, candidate_signal_count

    if parse_hint == "html_or_dynamic_page":
        table_rows = len(re.findall(r"<tr\b", sample, flags=re.I))
        table_cells = len(re.findall(r"<td\b|<th\b", sample, flags=re.I))
        if source_id == "krx_global_listed_company" and source_role == "primary_candidate_source":
            if table_rows >= 100 and table_cells >= 300 and candidate_signal_count >= 3:
                return "html_table_candidate_probe_ready", "KRX Global HTML appears to contain a sizeable candidate table.", True, table_rows, candidate_signal_count
            return "html_dynamic_not_candidate_ready", "KRX Global HTML is dynamic or summary-only; not enough row evidence for extraction.", False, table_rows, candidate_signal_count
        return "html_not_candidate_ready", "HTML page is not direct candidate row data.", False, table_rows, candidate_signal_count

    return "not_candidate_ready_unknown", "Artifact does not meet candidate-readiness rules.", False, estimated_rows, candidate_signal_count


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        ARTIFACT_AUDIT_CSV,
        SOURCE_READINESS_CSV,
        ISSUE_AUDIT_CSV,
        EXTRACTION_GATE_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219c_fix = read_json(V219C_FIX_JSON)
    _, repair_manifest_rows = read_csv_with_header(V219C_FIX_MANIFEST_CSV)
    _, repair_source_diag_rows = read_csv_with_header(V219C_FIX_SOURCE_DIAGNOSTICS_CSV)
    _, html_signal_rows = read_csv_with_header(V219C_FIX_HTML_SIGNAL_CSV)
    _, discovered_url_rows = read_csv_with_header(V219C_FIX_DISCOVERED_URLS_CSV)
    _, table_probe_rows = read_csv_with_header(V219C_FIX_TABLE_PROBE_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    artifact_audit_rows: list[dict[str, Any]] = []
    issue_audit_rows: list[dict[str, Any]] = []

    for row in repair_manifest_rows:
        artifact_path = Path(row.get("artifact_path", ""))
        expected_bytes = to_int(row.get("artifact_bytes", 0))
        expected_sha = row.get("artifact_sha256", "")
        exists = artifact_path.exists()
        actual_bytes = artifact_path.stat().st_size if exists else 0
        actual_sha = sha256_file(artifact_path) if exists else ""
        bytes_match = exists and actual_bytes == expected_bytes
        sha_match = exists and actual_sha == expected_sha
        official_scope_allowed = is_official_allowed_url(row.get("url", "")) if row.get("url") else True

        sample = read_sample(artifact_path)
        readiness_bucket, readiness_detail, candidate_ready, estimated_rows, candidate_signal_count = classify_candidate_readiness(row, sample)

        audit = {
            "source_id": row.get("source_id", ""),
            "artifact_id": row.get("artifact_id", ""),
            "source_role": row.get("source_role", ""),
            "url": row.get("url", ""),
            "method": row.get("method", ""),
            "official_scope_allowed": official_scope_allowed,
            "acquisition_status": row.get("acquisition_status", ""),
            "http_status": row.get("http_status", ""),
            "content_type": row.get("content_type", ""),
            "parse_hint": row.get("parse_hint", ""),
            "artifact_path": str(artifact_path),
            "artifact_exists": exists,
            "expected_bytes": expected_bytes,
            "actual_bytes": actual_bytes,
            "bytes_match": bytes_match,
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "sha256_match": sha_match,
            "candidate_signal_count": candidate_signal_count,
            "estimated_candidate_rows": estimated_rows,
            "readiness_bucket": readiness_bucket,
            "readiness_detail": readiness_detail,
            "candidate_extraction_ready": candidate_ready,
        }
        artifact_audit_rows.append(audit)

        if not official_scope_allowed:
            issue_audit_rows.append({
                "severity": "critical",
                "issue_type": "official_scope_violation",
                "source_id": audit["source_id"],
                "artifact_id": audit["artifact_id"],
                "detail": f"URL outside allowed official KRX/data.go.kr scope: {audit['url']}",
                "recommended_action": "Do not proceed; remove or investigate non-official artifact.",
            })
        elif not exists:
            issue_audit_rows.append({
                "severity": "critical",
                "issue_type": "missing_artifact",
                "source_id": audit["source_id"],
                "artifact_id": audit["artifact_id"],
                "detail": "Repair manifest artifact path does not exist.",
                "recommended_action": "Review v2.19C_FIX raw acquisition repair output.",
            })
        elif not bytes_match or not sha_match:
            issue_audit_rows.append({
                "severity": "critical",
                "issue_type": "artifact_integrity_mismatch",
                "source_id": audit["source_id"],
                "artifact_id": audit["artifact_id"],
                "detail": f"bytes_match={bytes_match}; sha256_match={sha_match}",
                "recommended_action": "Do not proceed; investigate repaired raw artifact integrity.",
            })
        elif not candidate_ready:
            issue_audit_rows.append({
                "severity": "warning",
                "issue_type": readiness_bucket,
                "source_id": audit["source_id"],
                "artifact_id": audit["artifact_id"],
                "detail": readiness_detail,
                "recommended_action": "Do not use this artifact for candidate extraction unless a later manual/source-specific parser phase explicitly validates it.",
            })

    source_ids = sorted(set(row["source_id"] for row in artifact_audit_rows))
    source_readiness_rows: list[dict[str, Any]] = []

    for sid in source_ids:
        rows = [row for row in artifact_audit_rows if row["source_id"] == sid]
        roles = sorted(set(row["source_role"] for row in rows if row["source_role"]))
        candidate_ready_rows = [row for row in rows if row["candidate_extraction_ready"]]
        primary_ready_rows = [
            row for row in rows
            if row["candidate_extraction_ready"]
            and row["source_role"] in {"primary_candidate_source", "primary_or_crosscheck_source"}
        ]
        http_200_rows = [row for row in rows if str(row["http_status"]) == "200"]
        structured_rows = [
            row for row in rows
            if row["parse_hint"] in {"csv_like", "json_like", "xml_or_api_payload", "xlsx_or_zip_container"}
        ]

        if primary_ready_rows:
            final_status = "primary_candidate_extraction_ready"
        elif candidate_ready_rows:
            final_status = "supporting_candidate_data_ready"
        elif any(row["readiness_bucket"] == "html_dynamic_not_candidate_ready" for row in rows):
            final_status = "html_dynamic_not_parse_ready"
        elif any("http_or_diagnostic" in row["readiness_bucket"] for row in rows):
            final_status = "diagnostic_or_http_error_only"
        elif structured_rows:
            final_status = "structured_reference_not_candidate_ready"
        elif http_200_rows:
            final_status = "captured_not_candidate_ready"
        else:
            final_status = "not_candidate_ready"

        source_readiness_rows.append({
            "source_id": sid,
            "source_roles": "|".join(roles),
            "artifact_count": len(rows),
            "http_200_count": len(http_200_rows),
            "structured_artifact_count": len(structured_rows),
            "candidate_ready_count": len(candidate_ready_rows),
            "primary_candidate_ready_count": len(primary_ready_rows),
            "estimated_candidate_rows_max": max([to_int(row["estimated_candidate_rows"]) for row in rows] or [0]),
            "candidate_signal_count_max": max([to_int(row["candidate_signal_count"]) for row in rows] or [0]),
            "readiness_buckets": "|".join(sorted(set(row["readiness_bucket"] for row in rows))),
            "final_source_status": final_status,
            "candidate_extraction_ready": len(primary_ready_rows) > 0,
        })

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    total_artifacts = len(artifact_audit_rows)
    artifacts_exist_count = sum(1 for row in artifact_audit_rows if row["artifact_exists"])
    bytes_match_count = sum(1 for row in artifact_audit_rows if row["bytes_match"])
    sha256_match_count = sum(1 for row in artifact_audit_rows if row["sha256_match"])
    official_scope_violations = sum(1 for row in artifact_audit_rows if not row["official_scope_allowed"])
    structured_artifact_count = sum(
        1 for row in artifact_audit_rows
        if row["parse_hint"] in {"csv_like", "json_like", "xml_or_api_payload", "xlsx_or_zip_container"}
    )
    candidate_ready_count = sum(1 for row in artifact_audit_rows if row["candidate_extraction_ready"])
    primary_candidate_ready_count = sum(
        1 for row in artifact_audit_rows
        if row["candidate_extraction_ready"]
        and row["source_role"] in {"primary_candidate_source", "primary_or_crosscheck_source"}
    )
    supporting_candidate_ready_count = candidate_ready_count - primary_candidate_ready_count
    critical_issue_count = sum(1 for row in issue_audit_rows if row["severity"] == "critical")
    warning_issue_count = sum(1 for row in issue_audit_rows if row["severity"] == "warning")

    selected_discovered_count = sum(1 for row in discovered_url_rows if to_bool(row.get("selected_for_fetch", False)))
    html_table_rows = len(table_probe_rows)
    html_signal_table_rows = max([to_int(row.get("table_rows_count", 0)) for row in html_signal_rows] or [0])

    extraction_ready = primary_candidate_ready_count >= 1 and critical_issue_count == 0
    krx_route_blocked_before_extraction = not extraction_ready and critical_issue_count == 0

    extraction_gate_rows = [
        {
            "gate": "artifact_integrity",
            "passed": artifacts_exist_count == total_artifacts and bytes_match_count == total_artifacts and sha256_match_count == total_artifacts,
            "detail": f"exists={artifacts_exist_count}/{total_artifacts}; bytes={bytes_match_count}/{total_artifacts}; sha256={sha256_match_count}/{total_artifacts}",
        },
        {
            "gate": "official_scope",
            "passed": official_scope_violations == 0,
            "detail": f"official_scope_violations={official_scope_violations}",
        },
        {
            "gate": "primary_candidate_data",
            "passed": primary_candidate_ready_count >= 1,
            "detail": f"primary_candidate_ready_count={primary_candidate_ready_count}",
        },
        {
            "gate": "extraction_ready",
            "passed": extraction_ready,
            "detail": f"extraction_ready={extraction_ready}",
        },
        {
            "gate": "krx_route_blocked_before_extraction",
            "passed": krx_route_blocked_before_extraction,
            "detail": f"blocked={krx_route_blocked_before_extraction}; candidate_ready_count={candidate_ready_count}; primary_candidate_ready_count={primary_candidate_ready_count}",
        },
    ]

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19c_fix_report_exists", V219C_FIX_JSON.exists(), "critical", str(V219C_FIX_JSON))
    add_check("v2_19c_fix_status_expected", v219c_fix.get("status") == EXPECTED_V219C_FIX_STATUS, "critical", v219c_fix.get("status", ""))
    add_check("v2_19c_fix_manifest_exists", V219C_FIX_MANIFEST_CSV.exists(), "critical", str(V219C_FIX_MANIFEST_CSV))
    add_check("v2_19c_fix_source_diagnostics_exists", V219C_FIX_SOURCE_DIAGNOSTICS_CSV.exists(), "critical", str(V219C_FIX_SOURCE_DIAGNOSTICS_CSV))
    add_check("raw_repair_dir_exists", RAW_REPAIR_DIR.exists(), "critical", str(RAW_REPAIR_DIR))
    add_check("repair_manifest_rows_expected", len(repair_manifest_rows) >= 18, "critical", f"repair_manifest_rows={len(repair_manifest_rows)}")
    add_check("all_repair_artifacts_exist", artifacts_exist_count == total_artifacts, "critical", f"artifacts_exist={artifacts_exist_count}/{total_artifacts}")
    add_check("all_repair_bytes_match", bytes_match_count == total_artifacts, "critical", f"bytes_match={bytes_match_count}/{total_artifacts}")
    add_check("all_repair_sha256_match", sha256_match_count == total_artifacts, "critical", f"sha256_match={sha256_match_count}/{total_artifacts}")
    add_check("official_scope_only", official_scope_violations == 0, "critical", f"official_scope_violations={official_scope_violations}")
    add_check("artifact_critical_issues_zero", critical_issue_count == 0, "critical", f"critical_issue_count={critical_issue_count}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("html_signal_inventory_available", len(html_signal_rows) >= 1, "warning", f"html_signal_rows={len(html_signal_rows)}")
    add_check("discovered_url_inventory_available", len(discovered_url_rows) >= 1, "warning", f"discovered_urls={len(discovered_url_rows)}")
    add_check("selected_discovered_urls_documented", selected_discovered_count >= 1, "warning", f"selected_discovered_count={selected_discovered_count}")
    add_check("html_table_probe_not_sufficient", html_table_rows <= 5 and html_signal_table_rows <= 5, "warning", f"html_table_rows={html_table_rows}; html_signal_table_rows={html_signal_table_rows}")
    add_check("structured_artifacts_present", structured_artifact_count >= 1, "warning", f"structured_artifact_count={structured_artifact_count}")
    add_check("primary_candidate_ready_present", primary_candidate_ready_count >= 1, "warning", f"primary_candidate_ready_count={primary_candidate_ready_count}")
    add_check("extraction_ready", extraction_ready, "warning", f"extraction_ready={extraction_ready}")
    add_check("krx_route_blocked_before_extraction", krx_route_blocked_before_extraction, "warning", f"krx_route_blocked_before_extraction={krx_route_blocked_before_extraction}")
    add_check("raw_files_read_only", True, "critical", "raw_files_written=False")
    add_check("network_not_used_by_repaired_validation", True, "critical", "network_download_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")

    if critical_failed > 0:
        status = "KRX_REPAIRED_RAW_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE
    elif extraction_ready:
        status = "KRX_REPAIRED_RAW_VALIDATION_COMPLETED_PARSE_READY_CANDIDATE_EXTRACTION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_EXTRACTION_PHASE
    else:
        status = "KRX_REPAIRED_RAW_VALIDATION_COMPLETED_NO_PARSE_READY_SOURCE_ROUTE_BLOCKED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_CLOSURE_PHASE

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "KRX",
            "action": "close_krx_route_or_extract_if_gate_passed",
            "priority": "high",
            "reason": "Repaired validation determines whether KRX has primary parse-ready candidate data.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "only proceed to v2.19E if primary_candidate_ready_count >= 1",
        },
        {
            "action_order": 2,
            "action_scope": "KRX",
            "action": "document_repair_limitations",
            "priority": "high",
            "reason": "KRX official web/download flows did not produce a primary structured candidate file if extraction_ready is false.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "closure must document HTTP 403, invalid OTP, HTML-only and missing service key facts",
        },
        {
            "action_order": 3,
            "action_scope": "50k",
            "action": "select_next_provider_route_if_krx_blocked",
            "priority": "high",
            "reason": "Current candidate remains 40,996; if KRX is blocked, the next route must continue toward 50k without quality degradation.",
            "recommended_phase": "next provider route selection after KRX closure",
            "guardrails": "do not launch full59k; keep official 50k target and quality gate",
        },
    ]

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
        "repaired_raw_validation_summary": {
            "repair_manifest_rows": len(repair_manifest_rows),
            "repair_source_diagnostics_rows": len(repair_source_diag_rows),
            "html_signal_rows": len(html_signal_rows),
            "discovered_url_rows": len(discovered_url_rows),
            "selected_discovered_urls": selected_discovered_count,
            "table_probe_rows": len(table_probe_rows),
            "artifact_audit_rows": len(artifact_audit_rows),
            "artifacts_exist_count": artifacts_exist_count,
            "bytes_match_count": bytes_match_count,
            "sha256_match_count": sha256_match_count,
            "official_scope_violations": official_scope_violations,
            "structured_artifact_count": structured_artifact_count,
            "candidate_ready_count": candidate_ready_count,
            "primary_candidate_ready_count": primary_candidate_ready_count,
            "supporting_candidate_ready_count": supporting_candidate_ready_count,
            "critical_issue_count": critical_issue_count,
            "warning_issue_count": warning_issue_count,
            "extraction_ready": extraction_ready,
            "krx_route_blocked_before_extraction": krx_route_blocked_before_extraction,
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": False,
            "raw_validation_performed": False,
            "repaired_raw_validation_performed": True,
            "raw_files_read": True,
            "raw_files_written": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "closure_report_performed": False,
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

    artifact_fieldnames = [
        "source_id",
        "artifact_id",
        "source_role",
        "url",
        "method",
        "official_scope_allowed",
        "acquisition_status",
        "http_status",
        "content_type",
        "parse_hint",
        "artifact_path",
        "artifact_exists",
        "expected_bytes",
        "actual_bytes",
        "bytes_match",
        "expected_sha256",
        "actual_sha256",
        "sha256_match",
        "candidate_signal_count",
        "estimated_candidate_rows",
        "readiness_bucket",
        "readiness_detail",
        "candidate_extraction_ready",
    ]

    source_fieldnames = [
        "source_id",
        "source_roles",
        "artifact_count",
        "http_200_count",
        "structured_artifact_count",
        "candidate_ready_count",
        "primary_candidate_ready_count",
        "estimated_candidate_rows_max",
        "candidate_signal_count_max",
        "readiness_buckets",
        "final_source_status",
        "candidate_extraction_ready",
    ]

    issue_fieldnames = [
        "severity",
        "issue_type",
        "source_id",
        "artifact_id",
        "detail",
        "recommended_action",
    ]

    write_csv(ARTIFACT_AUDIT_CSV, artifact_audit_rows, artifact_fieldnames)
    write_csv(SOURCE_READINESS_CSV, source_readiness_rows, source_fieldnames)
    write_csv(ISSUE_AUDIT_CSV, issue_audit_rows, issue_fieldnames)
    write_csv(EXTRACTION_GATE_CSV, extraction_gate_rows, ["gate", "passed", "detail"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    artifact_lines = "\n".join(
        f"- `{row['artifact_id']}` - exists `{row['artifact_exists']}`, bytes `{row['bytes_match']}`, sha `{row['sha256_match']}`, readiness `{row['readiness_bucket']}`, extraction `{row['candidate_extraction_ready']}`"
        for row in artifact_audit_rows
    )

    source_lines = "\n".join(
        f"- `{row['source_id']}` - status `{row['final_source_status']}`, candidate-ready `{row['candidate_ready_count']}`, primary-ready `{row['primary_candidate_ready_count']}`"
        for row in source_readiness_rows
    )

    issue_lines = "\n".join(
        f"- {row['severity']} `{row['issue_type']}` / `{row['source_id']}` / `{row['artifact_id']}` - {row['detail']}"
        for row in issue_audit_rows
    ) or "- No issues."

    gate_lines = "\n".join(
        f"- `{row['gate']}`: {'PASS' if row['passed'] else 'FAIL'} - {row['detail']}"
        for row in extraction_gate_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}"
        for row in checks
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` - {row['action']} - {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.19D_FIX validates the repaired KRX raw artifacts from v2.19C_FIX.

This phase is repaired-raw-validation only. It does not download new data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Repaired raw validation summary

- Repair manifest rows: `{len(repair_manifest_rows)}`
- Repair source diagnostics rows: `{len(repair_source_diag_rows)}`
- HTML signal rows: `{len(html_signal_rows)}`
- Discovered URL rows: `{len(discovered_url_rows)}`
- Selected discovered URLs: `{selected_discovered_count}`
- Table probe rows: `{len(table_probe_rows)}`
- Artifact audit rows: `{len(artifact_audit_rows)}`
- Artifacts exist: `{artifacts_exist_count}/{total_artifacts}`
- Bytes match: `{bytes_match_count}/{total_artifacts}`
- SHA256 match: `{sha256_match_count}/{total_artifacts}`
- Official scope violations: `{official_scope_violations}`
- Structured artifacts: `{structured_artifact_count}`
- Candidate-ready artifacts: `{candidate_ready_count}`
- Primary candidate-ready artifacts: `{primary_candidate_ready_count}`
- Supporting candidate-ready artifacts: `{supporting_candidate_ready_count}`
- Critical issues: `{critical_issue_count}`
- Warning issues: `{warning_issue_count}`
- Extraction ready: `{extraction_ready}`
- KRX route blocked before extraction: `{krx_route_blocked_before_extraction}`
- Critical failed checks: `{critical_failed}`

## Artifact audit

{artifact_lines}

## Source readiness

{source_lines}

## Issues

{issue_lines}

## Extraction gate

{gate_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw acquisition repair performed: false
- Repaired raw validation performed: true
- Raw files read: true
- Raw files written: false
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

    print("v2.19D_FIX KRX repaired raw validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REPAIRED_RAW_VALIDATION_SUMMARY:")
    for key, value in payload["repaired_raw_validation_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_READINESS:")
    for row in source_readiness_rows:
        print(f"- {row['source_id']}: status={row['final_source_status']} candidate_ready={row['candidate_ready_count']} primary_ready={row['primary_candidate_ready_count']}")
    print("")
    print("EXTRACTION_GATE:")
    for row in extraction_gate_rows:
        print(f"- {row['gate']}: {'PASS' if row['passed'] else 'FAIL'} - {row['detail']}")
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
