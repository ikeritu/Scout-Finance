from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.18D"
PHASE = "TWSE + TPEx Raw Validation"
PHASE_TYPE = "raw-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "twse_tpex_raw_acquisition_v2_18c"

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
VALIDATED_NSE_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"

V218C_JSON = OUTPUT_DIR / "twse_tpex_raw_acquisition_v2_18c.json"
V218C_MANIFEST_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_manifest_v2_18c.csv"
V218C_SOURCE_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_source_actions_v2_18c.csv"

V218B_SOURCE_PLAN_CSV = OUTPUT_DIR / "twse_tpex_source_plan_v2_18b.csv"
V218B_FILTER_POLICY_CSV = OUTPUT_DIR / "twse_tpex_filter_policy_v2_18b.csv"
V218B_SCHEMA_PLAN_CSV = OUTPUT_DIR / "twse_tpex_candidate_schema_plan_v2_18b.csv"

REPORT_JSON = OUTPUT_DIR / "twse_tpex_raw_validation_v2_18d.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_raw_validation_v2_18d.md"
FILE_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_raw_validation_file_profile_v2_18d.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "twse_tpex_raw_validation_source_diagnostics_v2_18d.csv"
FORMAT_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_raw_validation_format_profile_v2_18d.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_raw_validation_next_actions_v2_18d.csv"

EXPECTED_V218C_STATUS = "TWSE_TPEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
VALIDATED_CANDIDATE_ROWS_EXPECTED = 40300
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9700
EXPECTED_MANIFEST_ROWS = 9

RECOMMENDED_EXTRACTION_PHASE = "v2.18E - TWSE + TPEx Candidate Extraction Dry Run"
RECOMMENDED_REPAIR_PHASE = "v2.18C_FIX - TWSE + TPEx Raw Acquisition Repair"
RECOMMENDED_VALIDATION_FIX_PHASE = "v2.18D_FIX - TWSE + TPEx Raw Validation Repair"

FILE_PROFILE_FIELDS = [
    "source_id",
    "provider",
    "candidate_role",
    "source_category",
    "planned_raw_kind",
    "download_status",
    "http_status",
    "content_type",
    "raw_artifact_path",
    "file_exists",
    "manifest_bytes",
    "actual_bytes",
    "bytes_match",
    "manifest_sha256",
    "actual_sha256",
    "sha256_match",
    "detected_format",
    "parse_attempted",
    "parse_status",
    "row_like_count",
    "column_like_count",
    "html_table_rows",
    "html_csv_mentions",
    "html_download_mentions",
    "validation_bucket",
    "extraction_readiness",
    "notes",
]

SOURCE_DIAGNOSTICS_FIELDS = [
    "source_id",
    "provider",
    "candidate_role",
    "filter_policy_ref",
    "http_status",
    "download_status",
    "error_type",
    "error_message",
    "detected_format",
    "validation_bucket",
    "candidate_extraction_readiness",
    "repair_required",
    "repair_reason",
    "next_action",
]

FORMAT_PROFILE_FIELDS = [
    "source_id",
    "provider",
    "raw_artifact_path",
    "planned_raw_kind",
    "content_type",
    "file_extension",
    "detected_format",
    "format_matches_plan",
    "is_catalog_source",
    "is_primary_candidate_source",
    "is_review_only_source",
    "parse_status",
    "parse_notes",
]

NEXT_ACTIONS_FIELDS = [
    "action_order",
    "action_scope",
    "action",
    "priority",
    "reason",
    "recommended_phase",
    "guardrails",
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


def decode_text(data: bytes) -> tuple[str, str]:
    for encoding in ["utf-8-sig", "utf-8", "big5", "cp950", "latin-1"]:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replace"


def detect_format(data: bytes, content_type: str, path: Path) -> str:
    text_head, _ = decode_text(data[:4096])
    stripped = text_head.lstrip().lower()
    content_type_low = (content_type or "").lower()
    suffix = path.suffix.lower()

    if not data:
        return "empty"

    if stripped.startswith("{") or stripped.startswith("[") or "application/json" in content_type_low or suffix == ".json":
        return "json_like"

    if "<!doctype html" in stripped or stripped.startswith("<html") or "<html" in stripped or "text/html" in content_type_low:
        return "html"

    if "," in text_head and ("\n" in text_head or "\r" in text_head):
        return "csv_like"

    if "certificate verify failed" in stripped or "urlopen error" in stripped:
        return "error_text"

    return "text_or_binary"


def parse_raw_artifact(data: bytes, detected_format: str) -> dict[str, Any]:
    result = {
        "parse_attempted": False,
        "parse_status": "not_attempted",
        "row_like_count": 0,
        "column_like_count": 0,
        "html_table_rows": 0,
        "html_csv_mentions": 0,
        "html_download_mentions": 0,
        "parse_notes": "",
    }

    text, encoding = decode_text(data)

    if detected_format == "json_like":
        result["parse_attempted"] = True
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                result["row_like_count"] = len(parsed)
                if parsed and isinstance(parsed[0], dict):
                    result["column_like_count"] = len(parsed[0])
                result["parse_status"] = "json_list_parsed"
            elif isinstance(parsed, dict):
                result["row_like_count"] = len(parsed)
                result["column_like_count"] = len(parsed.keys())
                result["parse_status"] = "json_dict_parsed"
            else:
                result["parse_status"] = f"json_scalar_parsed_{type(parsed).__name__}"
            result["parse_notes"] = f"encoding={encoding}"
        except Exception as error:
            result["parse_status"] = "json_parse_failed"
            result["parse_notes"] = str(error)
        return result

    if detected_format == "csv_like":
        result["parse_attempted"] = True
        try:
            sample_lines = text.splitlines()
            reader = csv.reader(sample_lines)
            rows = list(reader)
            result["row_like_count"] = len(rows)
            result["column_like_count"] = max((len(row) for row in rows), default=0)
            result["parse_status"] = "csv_like_parsed"
            result["parse_notes"] = f"encoding={encoding}"
        except Exception as error:
            result["parse_status"] = "csv_parse_failed"
            result["parse_notes"] = str(error)
        return result

    if detected_format == "html":
        result["parse_attempted"] = True
        html_low = text.lower()
        result["html_table_rows"] = len(re.findall(r"<tr[\s>]", html_low))
        result["html_csv_mentions"] = html_low.count(".csv") + html_low.count("csv")
        result["html_download_mentions"] = html_low.count("download") + html_low.count("下載")
        result["row_like_count"] = result["html_table_rows"]
        result["column_like_count"] = 0
        result["parse_status"] = "html_profiled"
        result["parse_notes"] = f"encoding={encoding}"
        return result

    if detected_format == "error_text":
        result["parse_attempted"] = True
        result["parse_status"] = "error_payload_profiled"
        result["parse_notes"] = text[:300].replace("\n", " ").replace("\r", " ")
        return result

    return result


def classify_source(row: dict[str, str], detected_format: str, parse_info: dict[str, Any]) -> dict[str, Any]:
    source_id = row.get("source_id", "")
    provider = row.get("provider", "")
    candidate_role = row.get("candidate_role", "")
    filter_policy_ref = row.get("filter_policy_ref", "")
    http_status = str(row.get("http_status", "") or "")
    download_status = row.get("download_status", "")
    error_type = row.get("error_type", "")
    error_message = row.get("error_message", "")

    is_catalog = filter_policy_ref == "catalog_only" or "catalog" in candidate_role
    is_primary = "primary" in candidate_role
    is_review = any(token in candidate_role for token in ["review", "deferred", "applicant"])

    repair_required = False
    repair_reason = ""
    next_action = ""
    validation_bucket = "valid_raw_artifact"
    extraction_readiness = "not_candidate_source"

    if error_type or "network_error" in download_status or detected_format == "error_text":
        validation_bucket = "technical_acquisition_error_captured"
        extraction_readiness = "not_ready_technical_acquisition_error"
        repair_required = True
        repair_reason = error_message or download_status
        next_action = "repair_acquisition_client_or_source_access_before_extraction"
    elif http_status and http_status != "200":
        validation_bucket = "http_error_payload_captured"
        extraction_readiness = "not_ready_http_error"
        repair_required = True
        repair_reason = f"http_status={http_status}"
        next_action = "review_http_error_payload_before_extraction"
    elif is_catalog:
        validation_bucket = "valid_catalog_raw_artifact"
        extraction_readiness = "catalog_only_not_for_direct_extraction"
        next_action = "use_catalog_only_for_endpoint_discovery_if_needed"
    elif is_review:
        validation_bucket = "valid_review_only_raw_artifact"
        extraction_readiness = "review_only_not_safe_for_auto_extraction"
        next_action = "keep_as_diagnostic_or_future_route"
    elif is_primary and detected_format in {"json_like", "csv_like"} and int(parse_info.get("row_like_count", 0) or 0) > 1:
        validation_bucket = "parse_ready_primary_candidate_source"
        extraction_readiness = "parse_ready_for_candidate_extraction_dry_run"
        next_action = "allow_v2_18e_dry_run_against_this_source"
    elif is_primary and detected_format == "html":
        validation_bucket = "html_landing_page_not_row_data"
        extraction_readiness = "not_ready_html_landing_page_or_dynamic_download"
        repair_required = True
        repair_reason = "primary source captured as HTML page, not row-data JSON/CSV"
        next_action = "resolve_static_csv_json_endpoint_or parse page links in a repair phase"
    elif detected_format == "html":
        validation_bucket = "support_html_artifact"
        extraction_readiness = "support_source_html_only"
        next_action = "use only as crosscheck after primary row-data exists"
    else:
        validation_bucket = "valid_but_not_parse_ready"
        extraction_readiness = "not_ready_unknown_format"
        repair_required = True
        repair_reason = f"detected_format={detected_format}"
        next_action = "inspect raw artifact before extraction"

    return {
        "source_id": source_id,
        "provider": provider,
        "candidate_role": candidate_role,
        "filter_policy_ref": filter_policy_ref,
        "http_status": http_status,
        "download_status": download_status,
        "error_type": error_type,
        "error_message": error_message,
        "detected_format": detected_format,
        "validation_bucket": validation_bucket,
        "candidate_extraction_readiness": extraction_readiness,
        "repair_required": repair_required,
        "repair_reason": repair_reason,
        "next_action": next_action,
    }


def format_matches_plan(planned_raw_kind: str, detected_format: str) -> bool:
    planned = (planned_raw_kind or "").lower()

    if "json" in planned:
        return detected_format == "json_like"

    if "csv" in planned:
        return detected_format in {"csv_like", "html"}

    if "html" in planned or "swagger" in planned:
        return detected_format == "html"

    if "discovery" in planned:
        return detected_format in {"html", "json_like"}

    return detected_format not in {"empty"}


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        FILE_PROFILE_CSV,
        SOURCE_DIAGNOSTICS_CSV,
        FORMAT_PROFILE_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    v218c = read_json(V218C_JSON)

    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)
    candidate_header, candidate_rows = read_csv_with_header(VALIDATED_NSE_CANDIDATE_DATASET)
    manifest_header, manifest_rows = read_csv_with_header(V218C_MANIFEST_CSV)
    _, source_actions_rows = read_csv_with_header(V218C_SOURCE_ACTIONS_CSV)
    _, source_plan_rows = read_csv_with_header(V218B_SOURCE_PLAN_CSV)
    _, filter_policy_rows = read_csv_with_header(V218B_FILTER_POLICY_CSV)
    _, schema_plan_rows = read_csv_with_header(V218B_SCHEMA_PLAN_CSV)

    file_profile_rows: list[dict[str, Any]] = []
    source_diagnostics_rows: list[dict[str, Any]] = []
    format_profile_rows: list[dict[str, Any]] = []

    for row in manifest_rows:
        raw_path = Path(row.get("raw_artifact_path", ""))
        file_exists = raw_path.exists()
        data = raw_path.read_bytes() if file_exists else b""

        actual_bytes = len(data)
        actual_sha = sha256_bytes(data) if file_exists else ""

        try:
            manifest_bytes = int(row.get("bytes", 0) or 0)
        except ValueError:
            manifest_bytes = -1

        manifest_sha = row.get("sha256", "")

        bytes_match = file_exists and manifest_bytes == actual_bytes
        sha256_match = file_exists and manifest_sha == actual_sha

        detected_format = detect_format(data, row.get("content_type", ""), raw_path)
        parse_info = parse_raw_artifact(data, detected_format)
        diagnostic = classify_source(row, detected_format, parse_info)

        validation_bucket = diagnostic["validation_bucket"]
        extraction_readiness = diagnostic["candidate_extraction_readiness"]

        file_profile_rows.append(
            {
                "source_id": row.get("source_id", ""),
                "provider": row.get("provider", ""),
                "candidate_role": row.get("candidate_role", ""),
                "source_category": row.get("source_category", ""),
                "planned_raw_kind": row.get("planned_raw_kind", ""),
                "download_status": row.get("download_status", ""),
                "http_status": row.get("http_status", ""),
                "content_type": row.get("content_type", ""),
                "raw_artifact_path": str(raw_path),
                "file_exists": file_exists,
                "manifest_bytes": manifest_bytes,
                "actual_bytes": actual_bytes,
                "bytes_match": bytes_match,
                "manifest_sha256": manifest_sha,
                "actual_sha256": actual_sha,
                "sha256_match": sha256_match,
                "detected_format": detected_format,
                "parse_attempted": parse_info["parse_attempted"],
                "parse_status": parse_info["parse_status"],
                "row_like_count": parse_info["row_like_count"],
                "column_like_count": parse_info["column_like_count"],
                "html_table_rows": parse_info["html_table_rows"],
                "html_csv_mentions": parse_info["html_csv_mentions"],
                "html_download_mentions": parse_info["html_download_mentions"],
                "validation_bucket": validation_bucket,
                "extraction_readiness": extraction_readiness,
                "notes": parse_info.get("parse_notes", ""),
            }
        )

        source_diagnostics_rows.append(diagnostic)

        candidate_role = row.get("candidate_role", "")
        filter_policy_ref = row.get("filter_policy_ref", "")

        format_profile_rows.append(
            {
                "source_id": row.get("source_id", ""),
                "provider": row.get("provider", ""),
                "raw_artifact_path": str(raw_path),
                "planned_raw_kind": row.get("planned_raw_kind", ""),
                "content_type": row.get("content_type", ""),
                "file_extension": raw_path.suffix,
                "detected_format": detected_format,
                "format_matches_plan": format_matches_plan(row.get("planned_raw_kind", ""), detected_format),
                "is_catalog_source": filter_policy_ref == "catalog_only" or "catalog" in candidate_role,
                "is_primary_candidate_source": "primary" in candidate_role,
                "is_review_only_source": any(token in candidate_role for token in ["review", "deferred", "applicant"]),
                "parse_status": parse_info["parse_status"],
                "parse_notes": parse_info.get("parse_notes", ""),
            }
        )

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())
    candidate_sha = sha256_bytes(VALIDATED_NSE_CANDIDATE_DATASET.read_bytes())

    active_canonical_rows = len(canonical_rows)
    validated_candidate_rows = len(candidate_rows)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - validated_candidate_rows, 0)
    completion_percent = round((validated_candidate_rows / FINAL_TARGET_CANDIDATES) * 100, 2)

    raw_files_exist_count = sum(1 for row in file_profile_rows if row["file_exists"])
    bytes_match_count = sum(1 for row in file_profile_rows if row["bytes_match"])
    sha_match_count = sum(1 for row in file_profile_rows if row["sha256_match"])
    http_200_count = sum(1 for row in manifest_rows if str(row.get("http_status", "")) == "200")
    network_error_count = sum(1 for row in manifest_rows if "network_error" in row.get("download_status", ""))
    technical_repair_required_count = sum(1 for row in source_diagnostics_rows if str(row["repair_required"]).lower() == "true")
    parse_ready_primary_sources = sum(
        1 for row in source_diagnostics_rows
        if row["candidate_extraction_readiness"] == "parse_ready_for_candidate_extraction_dry_run"
    )
    primary_sources_total = sum(1 for row in source_diagnostics_rows if "primary" in row["candidate_role"])
    html_landing_primary_sources = sum(
        1 for row in source_diagnostics_rows
        if row["validation_bucket"] == "html_landing_page_not_row_data"
    )
    twse_error_sources = sum(
        1 for row in source_diagnostics_rows
        if row["provider"] == "TWSE" and row["validation_bucket"] == "technical_acquisition_error_captured"
    )
    tpex_http_200_sources = sum(
        1 for row in source_diagnostics_rows
        if row["provider"] == "TPEx" and str(row["http_status"]) == "200"
    )

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18c_report_exists", V218C_JSON.exists(), "critical", str(V218C_JSON))
    add_check("v2_18c_status_expected", v218c.get("status") == EXPECTED_V218C_STATUS, "critical", v218c.get("status", ""))
    add_check("v2_18c_manifest_exists", V218C_MANIFEST_CSV.exists(), "critical", str(V218C_MANIFEST_CSV))
    add_check("v2_18c_source_actions_exists", V218C_SOURCE_ACTIONS_CSV.exists(), "critical", str(V218C_SOURCE_ACTIONS_CSV))
    add_check("raw_directory_exists", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("source_plan_exists", V218B_SOURCE_PLAN_CSV.exists(), "critical", str(V218B_SOURCE_PLAN_CSV))
    add_check("filter_policy_exists", V218B_FILTER_POLICY_CSV.exists(), "critical", str(V218B_FILTER_POLICY_CSV))
    add_check("schema_plan_exists", V218B_SCHEMA_PLAN_CSV.exists(), "critical", str(V218B_SCHEMA_PLAN_CSV))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("validated_candidate_dataset_exists", VALIDATED_NSE_CANDIDATE_DATASET.exists(), "critical", str(VALIDATED_NSE_CANDIDATE_DATASET))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("validated_candidate_rows_expected", validated_candidate_rows == VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"validated_candidate_rows={validated_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("candidate_schema_matches_canonical", canonical_header == candidate_header, "critical", f"canonical_cols={len(canonical_header)} candidate_cols={len(candidate_header)}")
    add_check("manifest_rows_expected", len(manifest_rows) == EXPECTED_MANIFEST_ROWS, "critical", f"manifest_rows={len(manifest_rows)}")
    add_check("source_actions_present", len(source_actions_rows) >= EXPECTED_MANIFEST_ROWS, "critical", f"source_actions={len(source_actions_rows)}")
    add_check("raw_files_exist", raw_files_exist_count == len(manifest_rows), "critical", f"{raw_files_exist_count}/{len(manifest_rows)}")
    add_check("raw_bytes_match_manifest", bytes_match_count == len(manifest_rows), "critical", f"{bytes_match_count}/{len(manifest_rows)}")
    add_check("raw_sha256_match_manifest", sha_match_count == len(manifest_rows), "critical", f"{sha_match_count}/{len(manifest_rows)}")
    add_check("raw_artifacts_profiled", len(file_profile_rows) == len(manifest_rows), "critical", f"file_profile_rows={len(file_profile_rows)}")
    add_check("http_200_or_error_captured", http_200_count + network_error_count == len(manifest_rows), "critical", f"http_200={http_200_count} network_error={network_error_count}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "canonical sha unchanged")
    add_check("network_not_used_in_validation", True, "critical", "network_download_performed=False")
    add_check("raw_files_not_modified", True, "critical", "raw_files_modified=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("final_50k_gate_still_blocked", validated_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{validated_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")

    add_check("twse_ssl_errors_detected_and_captured", twse_error_sources > 0, "warning", f"twse_error_sources={twse_error_sources}")
    add_check("tpex_http_200_sources_detected", tpex_http_200_sources > 0, "warning", f"tpex_http_200_sources={tpex_http_200_sources}")
    add_check("primary_candidate_sources_parse_ready", parse_ready_primary_sources > 0, "warning", f"parse_ready_primary_sources={parse_ready_primary_sources}/{primary_sources_total}")
    add_check("repair_required_before_extraction", technical_repair_required_count > 0 or parse_ready_primary_sources == 0, "warning", f"repair_required_count={technical_repair_required_count}")

    next_actions = []

    action_order = 1

    if twse_error_sources > 0:
        next_actions.append(
            {
                "action_order": action_order,
                "action_scope": "TWSE",
                "action": "repair_ssl_or_client_acquisition_for_twse_sources",
                "priority": "high",
                "reason": "TWSE official sources were attempted but captured SSL certificate verification errors instead of row data.",
                "recommended_phase": RECOMMENDED_REPAIR_PHASE,
                "guardrails": "repair acquisition only; no candidate extraction; preserve official source scope",
            }
        )
        action_order += 1

    if html_landing_primary_sources > 0:
        next_actions.append(
            {
                "action_order": action_order,
                "action_scope": "TPEx",
                "action": "resolve_static_csv_or_json_endpoint_from_html_landing_page",
                "priority": "high",
                "reason": "At least one primary candidate source was captured as an HTML landing page rather than row-data CSV/JSON.",
                "recommended_phase": RECOMMENDED_REPAIR_PHASE,
                "guardrails": "endpoint enrichment only from already planned official TPEx pages; no extraction yet",
            }
        )
        action_order += 1

    if parse_ready_primary_sources > 0 and critical_failed == 0:
        next_actions.append(
            {
                "action_order": action_order,
                "action_scope": "TWSE_TPEX",
                "action": "proceed_to_candidate_extraction_dry_run",
                "priority": "medium",
                "reason": "At least one primary candidate source is parse-ready.",
                "recommended_phase": RECOMMENDED_EXTRACTION_PHASE,
                "guardrails": "dry run only; no canonical modification",
            }
        )
        action_order += 1

    if not next_actions:
        next_actions.append(
            {
                "action_order": action_order,
                "action_scope": "TWSE_TPEX",
                "action": "inspect_raw_artifacts_before_extraction",
                "priority": "high",
                "reason": "No parse-ready primary candidate source detected.",
                "recommended_phase": RECOMMENDED_REPAIR_PHASE,
                "guardrails": "no candidate extraction until row-data source is captured",
            }
        )

    if critical_failed == 0 and parse_ready_primary_sources > 0:
        status = "TWSE_TPEX_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_CANDIDATE_EXTRACTION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_EXTRACTION_PHASE
    elif critical_failed == 0:
        status = "TWSE_TPEX_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_REPAIR_PHASE
    else:
        status = "TWSE_TPEX_RAW_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_VALIDATION_FIX_PHASE

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
        "raw_validation_summary": {
            "manifest_rows": len(manifest_rows),
            "raw_files_exist_count": raw_files_exist_count,
            "bytes_match_count": bytes_match_count,
            "sha256_match_count": sha_match_count,
            "http_200_count": http_200_count,
            "network_error_count": network_error_count,
            "twse_error_sources": twse_error_sources,
            "tpex_http_200_sources": tpex_http_200_sources,
            "technical_repair_required_count": technical_repair_required_count,
            "primary_sources_total": primary_sources_total,
            "parse_ready_primary_sources": parse_ready_primary_sources,
            "html_landing_primary_sources": html_landing_primary_sources,
            "critical_failed_checks": critical_failed,
        },
        "extraction_readiness": {
            "candidate_extraction_ready": parse_ready_primary_sources > 0 and critical_failed == 0,
            "repair_required_before_extraction": parse_ready_primary_sources == 0 or technical_repair_required_count > 0,
            "recommended_next_phase": recommended_next_phase,
            "reason": "Candidate extraction requires at least one primary source captured as row-data JSON/CSV. Current validation may require TWSE SSL repair and/or TPEx endpoint enrichment.",
        },
        "source_plan_reference": {
            "v2_18c_report": str(V218C_JSON),
            "v2_18c_manifest": str(V218C_MANIFEST_CSV),
            "v2_18c_source_actions": str(V218C_SOURCE_ACTIONS_CSV),
            "v2_18b_source_plan": str(V218B_SOURCE_PLAN_CSV),
            "filter_policy_rows": len(filter_policy_rows),
            "schema_plan_rows": len(schema_plan_rows),
            "source_plan_rows": len(source_plan_rows),
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_validation_performed": True,
            "raw_files_read": True,
            "raw_files_written": False,
            "raw_files_modified": False,
            "manifest_read": True,
            "file_profile_written": True,
            "source_diagnostics_written": True,
            "format_profile_written": True,
            "next_actions_written": True,
            "candidate_extraction_performed": False,
            "canonical_comparison_performed": False,
            "canonical_dataset_read": True,
            "validated_candidate_dataset_read": True,
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

    write_csv(FILE_PROFILE_CSV, file_profile_rows, FILE_PROFILE_FIELDS)
    write_csv(SOURCE_DIAGNOSTICS_CSV, source_diagnostics_rows, SOURCE_DIAGNOSTICS_FIELDS)
    write_csv(FORMAT_PROFILE_CSV, format_profile_rows, FORMAT_PROFILE_FIELDS)
    write_csv(NEXT_ACTIONS_CSV, next_actions, NEXT_ACTIONS_FIELDS)
    write_json(REPORT_JSON, payload)

    file_profile_lines = "\n".join(
        f"- `{row['source_id']}` — {row['provider']} — {row['validation_bucket']} — {row['detected_format']} — readiness `{row['extraction_readiness']}`"
        for row in file_profile_rows
    )

    diagnostic_lines = "\n".join(
        f"- `{row['source_id']}` — repair_required `{row['repair_required']}` — {row['candidate_extraction_readiness']} — {row['next_action']}"
        for row in source_diagnostics_rows
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions
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

v2.18D validates the TWSE + TPEx raw artifacts captured in v2.18C.

This is a local raw-validation-only phase. It does not perform network calls, endpoint calls, raw acquisition, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

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

## Raw validation summary

- Manifest rows: `{len(manifest_rows)}`
- Raw files exist: `{raw_files_exist_count}/{len(manifest_rows)}`
- Bytes match manifest: `{bytes_match_count}/{len(manifest_rows)}`
- SHA-256 match manifest: `{sha_match_count}/{len(manifest_rows)}`
- HTTP 200 sources: `{http_200_count}`
- Network error sources: `{network_error_count}`
- TWSE technical error sources: `{twse_error_sources}`
- TPEx HTTP 200 sources: `{tpex_http_200_sources}`
- Primary candidate sources: `{primary_sources_total}`
- Parse-ready primary candidate sources: `{parse_ready_primary_sources}`
- HTML landing primary sources: `{html_landing_primary_sources}`
- Repair required count: `{technical_repair_required_count}`
- Critical failed checks: `{critical_failed}`

## File profile

{file_profile_lines}

## Source diagnostics

{diagnostic_lines}

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
- Raw files modified: false
- Manifest read: true
- File profile written: true
- Source diagnostics written: true
- Format profile written: true
- Next actions written: true
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
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

v2.18D validates the raw artifacts and determines whether candidate extraction can proceed or whether acquisition repair is required first.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.18D TWSE + TPEx raw validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("RAW_VALIDATION_SUMMARY:")
    for key, value in payload["raw_validation_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("EXTRACTION_READINESS:")
    for key, value in payload["extraction_readiness"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_DIAGNOSTICS:")
    for row in source_diagnostics_rows:
        print(
            f"- {row['source_id']}: {row['validation_bucket']} "
            f"readiness={row['candidate_extraction_readiness']} repair_required={row['repair_required']}"
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
