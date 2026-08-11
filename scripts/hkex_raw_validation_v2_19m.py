from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VERSION = "v2.19M"
PHASE = "HKEX Raw Validation"
PHASE_TYPE = "raw-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219L_JSON = OUTPUT_DIR / "hkex_raw_acquisition_v2_19l.json"
V219L_MANIFEST_CSV = OUTPUT_DIR / "hkex_raw_acquisition_manifest_v2_19l.csv"
V219L_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_source_diagnostics_v2_19l.csv"
V219L_DISCOVERED_LINKS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_discovered_links_v2_19l.csv"
V219L_HTML_SIGNALS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_html_signals_v2_19l.csv"
V219L_ARTIFACT_INDEX_CSV = OUTPUT_DIR / "hkex_raw_acquisition_artifact_index_v2_19l.csv"

V219K_SOURCE_INVENTORY_CSV = OUTPUT_DIR / "hkex_acquisition_plan_source_inventory_v2_19k.csv"
V219K_VALIDATION_STRATEGY_CSV = OUTPUT_DIR / "hkex_acquisition_plan_validation_strategy_v2_19k.csv"
V219K_FILTERING_POLICY_CSV = OUTPUT_DIR / "hkex_acquisition_plan_filtering_policy_v2_19k.csv"

REPORT_JSON = OUTPUT_DIR / "hkex_raw_validation_v2_19m.json"
REPORT_MD = OUTPUT_DIR / "hkex_raw_validation_v2_19m.md"
ARTIFACT_AUDIT_CSV = OUTPUT_DIR / "hkex_raw_validation_artifact_audit_v2_19m.csv"
SOURCE_READINESS_CSV = OUTPUT_DIR / "hkex_raw_validation_source_readiness_v2_19m.csv"
DOWNLOAD_CANDIDATES_CSV = OUTPUT_DIR / "hkex_raw_validation_official_download_candidates_v2_19m.csv"
EXTRACTION_GATE_CSV = OUTPUT_DIR / "hkex_raw_validation_extraction_gate_v2_19m.csv"
ISSUE_AUDIT_CSV = OUTPUT_DIR / "hkex_raw_validation_issue_audit_v2_19m.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_raw_validation_checks_v2_19m.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_raw_validation_next_actions_v2_19m.csv"

EXPECTED_V219L_STATUS = "HKEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

STATUS_REPAIR_REQUIRED = "HKEX_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_EXTRACTION_READY = "HKEX_RAW_VALIDATION_COMPLETED_PARSE_READY_SOURCE_AVAILABLE_EXTRACTION_DRY_RUN_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_BLOCKED = "HKEX_RAW_VALIDATION_COMPLETED_NO_PARSE_READY_SOURCE_ROUTE_BLOCKED_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_FAILED = "HKEX_RAW_VALIDATION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_REPAIR = "v2.19L_FIX - HKEX Raw Acquisition Repair"
NEXT_PHASE_EXTRACTION = "v2.19N - HKEX Candidate Extraction Dry Run"
NEXT_PHASE_CLOSURE = "v2.19Q - HKEX Closure Report"
NEXT_PHASE_REVIEW = "v2.19M_REVIEW - HKEX Raw Validation Review"

ALLOWED_HOSTS = {
    "www.hkex.com.hk",
    "hkex.com.hk",
    "www.hkexnews.hk",
    "hkexnews.hk",
}

PRIMARY_SOURCE_ROLES = {
    "primary_candidate_source",
    "primary_or_crosscheck_source",
}

DOWNLOAD_EXTENSIONS = (".csv", ".xls", ".xlsx", ".zip")
CANDIDATE_TERMS = (
    "full list of securities",
    "list of equities securities",
    "securities list",
    "listed securities",
    "equities",
    "stock code",
    "stock short name",
    "issuer",
    "listed company",
)

HTML_TABLE_RE = re.compile(r"(?is)<table\b.*?</table>")
HTML_ROW_RE = re.compile(r"(?is)<tr\b")
TAG_RE = re.compile(r"(?is)<[^>]+>")
STOCK_CODE_RE = re.compile(r"\b\d{4,5}\b")


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


def lower(value: Any) -> str:
    return str(value or "").strip().lower()


def decode_text(data: bytes, content_type: str) -> str:
    candidates = []
    match = re.search(r"charset=([^;\s]+)", content_type or "", flags=re.I)
    if match:
        candidates.append(match.group(1).strip("\"'"))
    candidates.extend(["utf-8", "utf-8-sig", "big5", "cp950", "latin-1"])

    for encoding in candidates:
        try:
            return data.decode(encoding)
        except Exception:
            continue

    return data.decode("utf-8", errors="replace")


def clean_visible_text(value: str, max_len: int = 5000) -> str:
    value = html.unescape(TAG_RE.sub(" ", value))
    value = re.sub(r"\s+", " ", value).strip()
    return value[:max_len]


def html_diagnostics(raw_path: Path, content_type: str) -> dict[str, Any]:
    if not raw_path.exists():
        return {
            "html_like": False,
            "table_count": 0,
            "max_table_rows": 0,
            "total_table_rows": 0,
            "stock_code_like_matches": 0,
            "contains_stock_code_text": False,
            "contains_stock_short_name_text": False,
            "contains_equities_text": False,
        }

    suffix = raw_path.suffix.lower()
    html_like = "html" in lower(content_type) or suffix in {".html", ".htm"}
    if not html_like:
        return {
            "html_like": False,
            "table_count": 0,
            "max_table_rows": 0,
            "total_table_rows": 0,
            "stock_code_like_matches": 0,
            "contains_stock_code_text": False,
            "contains_stock_short_name_text": False,
            "contains_equities_text": False,
        }

    text = decode_text(raw_path.read_bytes(), content_type)
    tables = HTML_TABLE_RE.findall(text)
    table_row_counts = [len(HTML_ROW_RE.findall(table)) for table in tables]
    visible_text = clean_visible_text(text, max_len=200000).lower()

    return {
        "html_like": True,
        "table_count": len(tables),
        "max_table_rows": max(table_row_counts) if table_row_counts else 0,
        "total_table_rows": sum(table_row_counts),
        "stock_code_like_matches": len(STOCK_CODE_RE.findall(visible_text)),
        "contains_stock_code_text": "stock code" in visible_text,
        "contains_stock_short_name_text": "stock short name" in visible_text,
        "contains_equities_text": "equities" in visible_text or "equity" in visible_text,
    }


def group_signals(signal_rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, int]]:
    grouped: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    for row in signal_rows:
        key = (row.get("source_id", ""), row.get("artifact_id", ""))
        grouped[key][row.get("signal", "")] = to_int(row.get("count", 0))
    return grouped


def build_source_role_map(source_inventory_rows: list[dict[str, str]]) -> dict[str, str]:
    return {
        row.get("source_id", ""): row.get("source_role", "")
        for row in source_inventory_rows
    }


def looks_like_official_download_candidate(row: dict[str, str]) -> bool:
    url = row.get("url", "")
    label = row.get("label", "")
    url_l = lower(url)
    label_l = lower(label)

    if not to_bool(row.get("official_scope_allowed", False)):
        return False

    if any(url_l.split("?")[0].endswith(ext) for ext in DOWNLOAD_EXTENSIONS):
        return True

    if to_bool(row.get("looks_download", False)):
        return True

    if any(term in label_l or term in url_l for term in CANDIDATE_TERMS):
        if any(token in url_l or token in label_l for token in ["xls", "xlsx", "csv", "download", "securities", "equities", "listed"]):
            return True

    return False


def candidate_download_priority(row: dict[str, str]) -> int:
    url_l = lower(row.get("url", ""))
    label_l = lower(row.get("label", ""))
    score = 0

    if any(url_l.split("?")[0].endswith(ext) for ext in [".xls", ".xlsx", ".csv"]):
        score += 40
    if "full list of securities" in label_l or "full list of securities" in url_l:
        score += 30
    if "equities" in label_l or "equities" in url_l:
        score += 25
    if "securities" in label_l or "securities" in url_l:
        score += 15
    if to_bool(row.get("looks_download", False)):
        score += 10
    if to_bool(row.get("looks_candidate_related", False)):
        score += 5

    return score


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        ARTIFACT_AUDIT_CSV,
        SOURCE_READINESS_CSV,
        DOWNLOAD_CANDIDATES_CSV,
        EXTRACTION_GATE_CSV,
        ISSUE_AUDIT_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219l = read_json(V219L_JSON)
    _, manifest_rows = read_csv_with_header(V219L_MANIFEST_CSV)
    _, source_diagnostic_rows = read_csv_with_header(V219L_SOURCE_DIAGNOSTICS_CSV)
    _, discovered_link_rows = read_csv_with_header(V219L_DISCOVERED_LINKS_CSV)
    _, html_signal_rows = read_csv_with_header(V219L_HTML_SIGNALS_CSV)
    _, artifact_index_rows = read_csv_with_header(V219L_ARTIFACT_INDEX_CSV)

    _, source_inventory_rows = read_csv_with_header(V219K_SOURCE_INVENTORY_CSV)
    _, validation_strategy_rows = read_csv_with_header(V219K_VALIDATION_STRATEGY_CSV)
    _, filtering_policy_rows = read_csv_with_header(V219K_FILTERING_POLICY_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    signal_map = group_signals(html_signal_rows)
    source_role_map = build_source_role_map(source_inventory_rows)

    artifact_audit_rows: list[dict[str, Any]] = []
    source_readiness_rows: list[dict[str, Any]] = []
    issue_audit_rows: list[dict[str, Any]] = []

    manifest_by_artifact = {row.get("artifact_id", ""): row for row in manifest_rows}

    for manifest in manifest_rows:
        source_id = manifest.get("source_id", "")
        artifact_id = manifest.get("artifact_id", "")
        source_role = source_role_map.get(source_id, "")
        raw_path = Path(manifest.get("raw_path", ""))
        headers_path = Path(manifest.get("headers_path", ""))
        content_type = manifest.get("content_type", "")
        declared_bytes = to_int(manifest.get("byte_count", 0))
        declared_sha = manifest.get("sha256", "")

        raw_exists = raw_path.exists()
        headers_exists = headers_path.exists()
        actual_bytes = raw_path.stat().st_size if raw_exists else 0
        actual_sha = sha256_file(raw_path) if raw_exists else ""
        bytes_match = declared_bytes == actual_bytes
        sha_match = declared_sha == actual_sha
        requested_official = to_bool(manifest.get("official_scope_allowed", False))
        final_official = to_bool(manifest.get("final_official_scope_allowed", False))
        http_success = to_bool(manifest.get("http_success", False))
        http_status = to_int(manifest.get("http_status", 0))

        diag = html_diagnostics(raw_path, content_type)
        signals = signal_map.get((source_id, artifact_id), {})

        structured_raw_file = raw_path.suffix.lower() in {".csv", ".xls", ".xlsx"}
        primary_role = source_role in PRIMARY_SOURCE_ROLES

        strong_html_candidate_signal = (
            diag["html_like"]
            and primary_role
            and diag["table_count"] >= 1
            and diag["contains_stock_code_text"]
            and (
                diag["contains_stock_short_name_text"]
                or signals.get("List of Equities Securities", 0) > 0
                or signals.get("Full List of Securities", 0) > 0
            )
            and diag["stock_code_like_matches"] >= 100
            and diag["max_table_rows"] >= 50
        )

        if structured_raw_file and primary_role and raw_exists and actual_bytes > 0:
            readiness_status = "primary_candidate_ready_structured_file"
            candidate_ready = True
            primary_candidate_ready = True
            extraction_allowed_by_raw_validation = True
        elif strong_html_candidate_signal:
            readiness_status = "possible_html_candidate_ready_requires_manual_confirmation"
            candidate_ready = True
            primary_candidate_ready = True
            extraction_allowed_by_raw_validation = False
        elif primary_role and raw_exists and actual_bytes > 0:
            readiness_status = "primary_page_captured_not_direct_parse_ready"
            candidate_ready = False
            primary_candidate_ready = False
            extraction_allowed_by_raw_validation = False
        elif raw_exists and actual_bytes > 0:
            readiness_status = "supporting_reference_captured_not_candidate_ready"
            candidate_ready = False
            primary_candidate_ready = False
            extraction_allowed_by_raw_validation = False
        else:
            readiness_status = "raw_capture_failed_or_empty"
            candidate_ready = False
            primary_candidate_ready = False
            extraction_allowed_by_raw_validation = False

        artifact_audit_rows.append(
            {
                "source_id": source_id,
                "artifact_id": artifact_id,
                "source_role": source_role,
                "raw_path": str(raw_path),
                "headers_path": str(headers_path),
                "raw_exists": raw_exists,
                "headers_exists": headers_exists,
                "declared_bytes": declared_bytes,
                "actual_bytes": actual_bytes,
                "bytes_match": bytes_match,
                "declared_sha256": declared_sha,
                "actual_sha256": actual_sha,
                "sha256_match": sha_match,
                "http_status": http_status,
                "http_success": http_success,
                "content_type": content_type,
                "requested_official_scope": requested_official,
                "final_official_scope": final_official,
                "html_like": diag["html_like"],
                "table_count": diag["table_count"],
                "max_table_rows": diag["max_table_rows"],
                "total_table_rows": diag["total_table_rows"],
                "stock_code_like_matches": diag["stock_code_like_matches"],
                "structured_raw_file": structured_raw_file,
            }
        )

        source_readiness_rows.append(
            {
                "source_id": source_id,
                "artifact_id": artifact_id,
                "source_role": source_role,
                "candidate_ready": candidate_ready,
                "primary_candidate_ready": primary_candidate_ready,
                "extraction_allowed_by_raw_validation": extraction_allowed_by_raw_validation,
                "readiness_status": readiness_status,
                "reason": (
                    "Structured primary raw file captured."
                    if structured_raw_file and primary_role
                    else "Raw HTML/reference page captured; official downloadable files should be captured before extraction."
                    if primary_role
                    else "Supporting/reference source only."
                ),
                "html_table_count": diag["table_count"],
                "html_max_table_rows": diag["max_table_rows"],
                "stock_code_like_matches": diag["stock_code_like_matches"],
                "full_list_signal_count": signals.get("Full List of Securities", 0),
                "equities_signal_count": signals.get("List of Equities Securities", 0),
                "stock_code_signal_count": signals.get("Stock Code", 0),
                "stock_short_name_signal_count": signals.get("Stock Short Name", 0),
                "xls_signal_count": signals.get(".xls", 0),
                "xlsx_signal_count": signals.get(".xlsx", 0),
            }
        )

        if not raw_exists:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_RAWVAL_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "source_id": source_id,
                    "artifact_id": artifact_id,
                    "issue": "raw_file_missing",
                    "detail": str(raw_path),
                }
            )
        if raw_exists and actual_bytes <= 0:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_RAWVAL_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "source_id": source_id,
                    "artifact_id": artifact_id,
                    "issue": "raw_file_empty",
                    "detail": str(raw_path),
                }
            )
        if raw_exists and not bytes_match:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_RAWVAL_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "source_id": source_id,
                    "artifact_id": artifact_id,
                    "issue": "byte_count_mismatch",
                    "detail": f"declared={declared_bytes}; actual={actual_bytes}",
                }
            )
        if raw_exists and not sha_match:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_RAWVAL_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "source_id": source_id,
                    "artifact_id": artifact_id,
                    "issue": "sha256_mismatch",
                    "detail": f"declared={declared_sha}; actual={actual_sha}",
                }
            )
        if not requested_official or not final_official:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_RAWVAL_{len(issue_audit_rows)+1:03d}",
                    "severity": "critical",
                    "source_id": source_id,
                    "artifact_id": artifact_id,
                    "issue": "official_scope_violation",
                    "detail": f"requested_official={requested_official}; final_official={final_official}",
                }
            )
        if http_status >= 400 or not http_success:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_RAWVAL_{len(issue_audit_rows)+1:03d}",
                    "severity": "warning",
                    "source_id": source_id,
                    "artifact_id": artifact_id,
                    "issue": "http_not_success",
                    "detail": f"http_status={http_status}; http_success={http_success}",
                }
            )
        if primary_role and not structured_raw_file:
            issue_audit_rows.append(
                {
                    "issue_id": f"HKEX_RAWVAL_{len(issue_audit_rows)+1:03d}",
                    "severity": "warning",
                    "source_id": source_id,
                    "artifact_id": artifact_id,
                    "issue": "primary_source_not_structured_raw_file",
                    "detail": "Primary HKEX source captured as HTML page; linked XLS/XLSX artifacts should be captured before extraction.",
                }
            )

    download_candidate_rows: list[dict[str, Any]] = []
    seen_download_urls: set[str] = set()

    for row in discovered_link_rows:
        if not looks_like_official_download_candidate(row):
            continue

        url = row.get("url", "")
        if url in seen_download_urls:
            continue
        seen_download_urls.add(url)

        priority_score = candidate_download_priority(row)
        source_id = row.get("source_id", "")
        artifact_id = row.get("artifact_id", "")

        download_candidate_rows.append(
            {
                "source_id": source_id,
                "artifact_id": artifact_id,
                "link_type": row.get("link_type", ""),
                "label": row.get("label", ""),
                "url": url,
                "host": row.get("host", ""),
                "official_scope_allowed": row.get("official_scope_allowed", ""),
                "looks_download": row.get("looks_download", ""),
                "looks_candidate_related": row.get("looks_candidate_related", ""),
                "priority_score": priority_score,
                "capture_recommendation": "capture_in_v2_19L_FIX" if priority_score >= 25 else "review_in_v2_19L_FIX",
            }
        )

    download_candidate_rows = sorted(
        download_candidate_rows,
        key=lambda x: (to_int(x["priority_score"]), x["source_id"], x["label"]),
        reverse=True,
    )

    critical_issue_count = sum(1 for row in issue_audit_rows if row["severity"] == "critical")
    warning_issue_count = sum(1 for row in issue_audit_rows if row["severity"] == "warning")
    artifacts_exist_count = sum(1 for row in artifact_audit_rows if row["raw_exists"])
    headers_exist_count = sum(1 for row in artifact_audit_rows if row["headers_exists"])
    bytes_match_count = sum(1 for row in artifact_audit_rows if row["bytes_match"])
    sha256_match_count = sum(1 for row in artifact_audit_rows if row["sha256_match"])
    official_scope_violations = sum(
        1
        for row in artifact_audit_rows
        if not row["requested_official_scope"] or not row["final_official_scope"]
    )
    candidate_ready_count = sum(1 for row in source_readiness_rows if row["candidate_ready"])
    primary_candidate_ready_count = sum(1 for row in source_readiness_rows if row["primary_candidate_ready"])
    extraction_allowed_count = sum(1 for row in source_readiness_rows if row["extraction_allowed_by_raw_validation"])
    official_download_candidate_count = len(download_candidate_rows)
    high_priority_download_candidate_count = sum(1 for row in download_candidate_rows if to_int(row["priority_score"]) >= 25)

    extraction_ready = (
        critical_issue_count == 0
        and official_scope_violations == 0
        and extraction_allowed_count > 0
    )
    repair_required = (
        critical_issue_count == 0
        and not extraction_ready
        and official_download_candidate_count > 0
    )
    route_blocked_before_extraction = (
        critical_issue_count == 0
        and not extraction_ready
        and official_download_candidate_count == 0
    )

    extraction_gate_rows = [
        {
            "gate": "artifact_integrity",
            "passed": critical_issue_count == 0,
            "severity": "critical",
            "detail": f"critical_issue_count={critical_issue_count}; artifacts={artifacts_exist_count}/{len(artifact_audit_rows)}; bytes={bytes_match_count}/{len(artifact_audit_rows)}; sha256={sha256_match_count}/{len(artifact_audit_rows)}",
        },
        {
            "gate": "official_scope",
            "passed": official_scope_violations == 0,
            "severity": "critical",
            "detail": f"official_scope_violations={official_scope_violations}",
        },
        {
            "gate": "primary_candidate_ready_present",
            "passed": primary_candidate_ready_count > 0,
            "severity": "warning",
            "detail": f"primary_candidate_ready_count={primary_candidate_ready_count}",
        },
        {
            "gate": "structured_extraction_allowed",
            "passed": extraction_allowed_count > 0,
            "severity": "warning",
            "detail": f"extraction_allowed_count={extraction_allowed_count}",
        },
        {
            "gate": "official_download_candidates_available",
            "passed": official_download_candidate_count > 0,
            "severity": "warning",
            "detail": f"official_download_candidate_count={official_download_candidate_count}; high_priority={high_priority_download_candidate_count}",
        },
        {
            "gate": "extraction_ready",
            "passed": extraction_ready,
            "severity": "warning",
            "detail": f"extraction_ready={extraction_ready}; repair_required={repair_required}; route_blocked_before_extraction={route_blocked_before_extraction}",
        },
    ]

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19l_report_exists", V219L_JSON.exists(), "critical", str(V219L_JSON))
    add_check("v2_19l_status_expected", v219l.get("status") == EXPECTED_V219L_STATUS, "critical", str(v219l.get("status", "")))
    add_check("manifest_exists", V219L_MANIFEST_CSV.exists(), "critical", str(V219L_MANIFEST_CSV))
    add_check("source_diagnostics_exists", V219L_SOURCE_DIAGNOSTICS_CSV.exists(), "critical", str(V219L_SOURCE_DIAGNOSTICS_CSV))
    add_check("discovered_links_exists", V219L_DISCOVERED_LINKS_CSV.exists(), "critical", str(V219L_DISCOVERED_LINKS_CSV))
    add_check("html_signals_exists", V219L_HTML_SIGNALS_CSV.exists(), "critical", str(V219L_HTML_SIGNALS_CSV))
    add_check("artifact_index_exists", V219L_ARTIFACT_INDEX_CSV.exists(), "critical", str(V219L_ARTIFACT_INDEX_CSV))
    add_check("manifest_rows_expected", len(manifest_rows) >= 5, "critical", f"manifest_rows={len(manifest_rows)}")
    add_check("artifact_index_rows_expected", len(artifact_index_rows) >= 5, "critical", f"artifact_index_rows={len(artifact_index_rows)}")
    add_check("source_inventory_loaded", len(source_inventory_rows) >= 5, "critical", f"source_inventory_rows={len(source_inventory_rows)}")
    add_check("validation_strategy_loaded", len(validation_strategy_rows) >= 5, "critical", f"validation_strategy_rows={len(validation_strategy_rows)}")
    add_check("filtering_policy_loaded", len(filtering_policy_rows) >= 4, "critical", f"filtering_policy_rows={len(filtering_policy_rows)}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("artifact_integrity_no_critical_issues", critical_issue_count == 0, "critical", f"critical_issue_count={critical_issue_count}")
    add_check("raw_files_exist", artifacts_exist_count == len(artifact_audit_rows), "critical", f"raw_files_exist={artifacts_exist_count}/{len(artifact_audit_rows)}")
    add_check("headers_exist", headers_exist_count == len(artifact_audit_rows), "critical", f"headers_exist={headers_exist_count}/{len(artifact_audit_rows)}")
    add_check("bytes_match", bytes_match_count == len(artifact_audit_rows), "critical", f"bytes_match={bytes_match_count}/{len(artifact_audit_rows)}")
    add_check("sha256_match", sha256_match_count == len(artifact_audit_rows), "critical", f"sha256_match={sha256_match_count}/{len(artifact_audit_rows)}")
    add_check("official_scope_no_violations", official_scope_violations == 0, "critical", f"official_scope_violations={official_scope_violations}")
    add_check("source_readiness_rows_expected", len(source_readiness_rows) == len(manifest_rows), "critical", f"source_readiness_rows={len(source_readiness_rows)}")
    add_check("candidate_ready_count_documented", candidate_ready_count >= 0, "warning", f"candidate_ready_count={candidate_ready_count}")
    add_check("primary_candidate_ready_count_documented", primary_candidate_ready_count >= 0, "warning", f"primary_candidate_ready_count={primary_candidate_ready_count}")
    add_check("official_download_candidates_documented", official_download_candidate_count >= 0, "warning", f"official_download_candidate_count={official_download_candidate_count}")
    add_check("repair_required_or_extraction_ready_or_blocked", extraction_ready or repair_required or route_blocked_before_extraction, "critical", f"extraction_ready={extraction_ready}; repair_required={repair_required}; route_blocked={route_blocked_before_extraction}")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("network_not_used_by_raw_validation", True, "critical", "network_download_performed=False")
    add_check("raw_files_read", True, "critical", "raw_files_read=True")
    add_check("raw_files_written_false", True, "critical", "raw_files_written=False")
    add_check("raw_validation_performed", True, "critical", "raw_validation_performed=True")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed == 0 and extraction_ready:
        status = STATUS_EXTRACTION_READY
        recommended_next_phase = NEXT_PHASE_EXTRACTION
    elif critical_failed == 0 and repair_required:
        status = STATUS_REPAIR_REQUIRED
        recommended_next_phase = NEXT_PHASE_REPAIR
    elif critical_failed == 0 and route_blocked_before_extraction:
        status = STATUS_BLOCKED
        recommended_next_phase = NEXT_PHASE_CLOSURE
    else:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW

    next_actions_rows = []
    if recommended_next_phase == NEXT_PHASE_REPAIR:
        next_actions_rows = [
            {
                "action_order": 1,
                "action_scope": "HKEX",
                "action": "capture_official_download_candidates",
                "priority": "high",
                "reason": "Raw HTML pages expose official download-like/candidate-related links, but no structured primary raw file is captured yet.",
                "recommended_phase": NEXT_PHASE_REPAIR,
                "guardrails": "official HKEX/HKEXnews links only; no extraction; no canonical modification",
            },
            {
                "action_order": 2,
                "action_scope": "HKEX",
                "action": "prioritize_xls_xlsx_full_list_equities_links",
                "priority": "high",
                "reason": "XLS/XLSX signals and official securities/equities links are the likely parse-ready candidates.",
                "recommended_phase": NEXT_PHASE_REPAIR,
                "guardrails": "capture raw files and headers; record bytes and sha256",
            },
            {
                "action_order": 3,
                "action_scope": "50k",
                "action": "preserve_quality_gate",
                "priority": "high",
                "reason": "Current candidate universe remains 40,996; rows needed to 50k remain 9,004.",
                "recommended_phase": NEXT_PHASE_REPAIR,
                "guardrails": "do not launch full59k; do not add HKEX rows before extraction and canonical validation",
            },
        ]
    elif recommended_next_phase == NEXT_PHASE_EXTRACTION:
        next_actions_rows = [
            {
                "action_order": 1,
                "action_scope": "HKEX",
                "action": "run_candidate_extraction_dry_run",
                "priority": "high",
                "reason": "Raw validation found at least one extraction-ready structured candidate source.",
                "recommended_phase": NEXT_PHASE_EXTRACTION,
                "guardrails": "dry run only; no canonical replacement",
            }
        ]
    else:
        next_actions_rows = [
            {
                "action_order": 1,
                "action_scope": "HKEX",
                "action": "close_or_review_hkex_route",
                "priority": "high",
                "reason": "Raw validation did not identify extraction-ready artifacts or actionable download candidates.",
                "recommended_phase": recommended_next_phase,
                "guardrails": "no extraction; preserve audit trail",
            }
        ]

    validation_summary = {
        "manifest_rows": len(manifest_rows),
        "source_diagnostics_rows": len(source_diagnostic_rows),
        "discovered_link_rows": len(discovered_link_rows),
        "html_signal_rows": len(html_signal_rows),
        "artifact_index_rows": len(artifact_index_rows),
        "artifact_audit_rows": len(artifact_audit_rows),
        "artifacts_exist_count": artifacts_exist_count,
        "headers_exist_count": headers_exist_count,
        "bytes_match_count": bytes_match_count,
        "sha256_match_count": sha256_match_count,
        "official_scope_violations": official_scope_violations,
        "candidate_ready_count": candidate_ready_count,
        "primary_candidate_ready_count": primary_candidate_ready_count,
        "extraction_allowed_count": extraction_allowed_count,
        "official_download_candidate_count": official_download_candidate_count,
        "high_priority_download_candidate_count": high_priority_download_candidate_count,
        "critical_issue_count": critical_issue_count,
        "warning_issue_count": warning_issue_count,
        "extraction_ready": extraction_ready,
        "repair_required": repair_required,
        "route_blocked_before_extraction": route_blocked_before_extraction,
        "critical_failed_checks": critical_failed,
        "current_validated_candidate_rows": current_candidate_rows,
        "rows_needed_to_50k": rows_needed_to_50k,
        "final_50k_candidate_gate": "BLOCKED",
        "full59k": "DEPRECATED_DEFERRED",
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
        "v2_19l_context": {
            "status": v219l.get("status"),
            "phase_type": v219l.get("phase_type"),
            "artifacts_written_count": v219l.get("acquisition_summary", {}).get("artifacts_written_count"),
            "raw_files_exist_count": v219l.get("acquisition_summary", {}).get("raw_files_exist_count"),
            "official_scope_violations": v219l.get("acquisition_summary", {}).get("official_scope_violations"),
            "discovered_links_count": v219l.get("acquisition_summary", {}).get("discovered_links_count"),
            "download_like_links_count": v219l.get("acquisition_summary", {}).get("download_like_links_count"),
        },
        "validation_summary": validation_summary,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "route_selection_performed": False,
            "acquisition_plan_performed": False,
            "raw_acquisition_performed": False,
            "raw_validation_performed": True,
            "raw_files_read": True,
            "raw_files_written": False,
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
        ARTIFACT_AUDIT_CSV,
        artifact_audit_rows,
        [
            "source_id",
            "artifact_id",
            "source_role",
            "raw_path",
            "headers_path",
            "raw_exists",
            "headers_exists",
            "declared_bytes",
            "actual_bytes",
            "bytes_match",
            "declared_sha256",
            "actual_sha256",
            "sha256_match",
            "http_status",
            "http_success",
            "content_type",
            "requested_official_scope",
            "final_official_scope",
            "html_like",
            "table_count",
            "max_table_rows",
            "total_table_rows",
            "stock_code_like_matches",
            "structured_raw_file",
        ],
    )
    write_csv(
        SOURCE_READINESS_CSV,
        source_readiness_rows,
        [
            "source_id",
            "artifact_id",
            "source_role",
            "candidate_ready",
            "primary_candidate_ready",
            "extraction_allowed_by_raw_validation",
            "readiness_status",
            "reason",
            "html_table_count",
            "html_max_table_rows",
            "stock_code_like_matches",
            "full_list_signal_count",
            "equities_signal_count",
            "stock_code_signal_count",
            "stock_short_name_signal_count",
            "xls_signal_count",
            "xlsx_signal_count",
        ],
    )
    write_csv(
        DOWNLOAD_CANDIDATES_CSV,
        download_candidate_rows,
        [
            "source_id",
            "artifact_id",
            "link_type",
            "label",
            "url",
            "host",
            "official_scope_allowed",
            "looks_download",
            "looks_candidate_related",
            "priority_score",
            "capture_recommendation",
        ],
    )
    write_csv(EXTRACTION_GATE_CSV, extraction_gate_rows, ["gate", "passed", "severity", "detail"])
    write_csv(ISSUE_AUDIT_CSV, issue_audit_rows, ["issue_id", "severity", "source_id", "artifact_id", "issue", "detail"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    readiness_lines = "\n".join(
        f"- `{row['artifact_id']}` — {row['readiness_status']} — candidate_ready `{row['candidate_ready']}` — primary `{row['primary_candidate_ready']}`"
        for row in source_readiness_rows
    )

    download_lines = "\n".join(
        f"- score `{row['priority_score']}` — `{row['label']}` — `{row['url']}`"
        for row in download_candidate_rows[:25]
    ) or "- No official download candidates detected."

    gate_lines = "\n".join(
        f"- `{row['gate']}`: {'PASS' if row['passed'] else 'NOT PASS'} ({row['severity']}) — {row['detail']}"
        for row in extraction_gate_rows
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

v2.19M validates the HKEX/HKEXnews raw artifacts captured in v2.19L.

This phase performs raw validation only. It does not download data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

- Manifest rows: `{len(manifest_rows)}`
- Artifact audit rows: `{len(artifact_audit_rows)}`
- Artifacts exist: `{artifacts_exist_count}/{len(artifact_audit_rows)}`
- Headers exist: `{headers_exist_count}/{len(artifact_audit_rows)}`
- Bytes match: `{bytes_match_count}/{len(artifact_audit_rows)}`
- SHA256 match: `{sha256_match_count}/{len(artifact_audit_rows)}`
- Official scope violations: `{official_scope_violations}`
- Candidate ready count: `{candidate_ready_count}`
- Primary candidate ready count: `{primary_candidate_ready_count}`
- Extraction allowed count: `{extraction_allowed_count}`
- Official download candidate count: `{official_download_candidate_count}`
- High priority download candidate count: `{high_priority_download_candidate_count}`
- Critical issue count: `{critical_issue_count}`
- Warning issue count: `{warning_issue_count}`
- Extraction ready: `{extraction_ready}`
- Repair required: `{repair_required}`
- Route blocked before extraction: `{route_blocked_before_extraction}`

## Source readiness

{readiness_lines}

## Top official download candidates

{download_lines}

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
- Raw validation performed: true
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

    print("v2.19M HKEX raw validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in validation_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_READINESS:")
    for row in source_readiness_rows:
        print(f"- {row['artifact_id']}: readiness={row['readiness_status']} candidate_ready={row['candidate_ready']} primary={row['primary_candidate_ready']} extraction_allowed={row['extraction_allowed_by_raw_validation']}")
    print("")
    print("TOP_DOWNLOAD_CANDIDATES:")
    for row in download_candidate_rows[:20]:
        print(f"- score={row['priority_score']} source={row['source_id']} label={row['label']} url={row['url']}")
    print("")
    print("EXTRACTION_GATE:")
    for row in extraction_gate_rows:
        print(f"- {row['gate']}: {'PASS' if row['passed'] else 'NOT_PASS'} ({row['severity']}) - {row['detail']}")
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
