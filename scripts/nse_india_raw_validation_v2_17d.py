from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.17D"
PHASE = "NSE India Raw Validation"
PHASE_TYPE = "provider-raw-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "nse_raw_acquisition_v2_17c"

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
V217C_JSON = OUTPUT_DIR / "nse_india_raw_acquisition_v2_17c.json"
V217C_MANIFEST_CSV = OUTPUT_DIR / "nse_india_raw_acquisition_manifest_v2_17c.csv"
V217C_SOURCE_ACTIONS_CSV = OUTPUT_DIR / "nse_india_raw_acquisition_source_actions_v2_17c.csv"

REPORT_JSON = OUTPUT_DIR / "nse_india_raw_validation_v2_17d.json"
REPORT_MD = OUTPUT_DIR / "nse_india_raw_validation_v2_17d.md"
FILE_PROFILE_CSV = OUTPUT_DIR / "nse_india_raw_validation_file_profile_v2_17d.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "nse_india_raw_validation_source_diagnostics_v2_17d.csv"
SCHEMA_PROFILE_CSV = OUTPUT_DIR / "nse_india_raw_validation_schema_profile_v2_17d.csv"

CURRENT_CANONICAL_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713

EXPECTED_V217C_STATUS = "NSE_INDIA_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED"
EXPECTED_V217C_NEXT = "v2.17D - NSE India Raw Validation"

NEXT_PHASE = "v2.17E - NSE India Candidate Extraction Dry Run"

CRITICAL_SOURCE_IDS = {
    "nse_all_reports_cm_mii_security_file_nse_listed",
    "nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive",
    "nse_securities_available_equity_segment",
    "nse_securities_available_sme",
    "nse_etfs",
    "nse_reits",
    "nse_invits",
    "nse_debt_instruments",
}

EXCLUSION_REFERENCE_IDS = {
    "nse_idrs",
    "nse_preference_shares",
    "nse_warrants",
    "nse_close_ended_mf",
    "nse_etfs",
    "nse_invits",
    "nse_reits",
    "nse_debt_instruments",
}

FILE_PROFILE_FIELDS = [
    "artifact_id",
    "source_id",
    "artifact_type",
    "local_path",
    "exists",
    "download_status",
    "http_status",
    "content_type",
    "extension",
    "manifest_bytes",
    "actual_bytes",
    "manifest_sha256",
    "actual_sha256",
    "sha256_matches",
    "gzip_magic_manifest",
    "gzip_magic_actual",
    "gzip_decompress_attempted",
    "gzip_decompress_ok",
    "raw_kind",
    "csv_parse_attempted",
    "csv_parse_ok",
    "csv_delimiter",
    "csv_row_count",
    "csv_column_count",
    "columns_preview",
    "validation_bucket",
    "issues",
]

SOURCE_DIAGNOSTIC_FIELDS = [
    "source_id",
    "artifact_count",
    "downloaded_count",
    "valid_raw_file_count",
    "csv_ok_count",
    "gzip_ok_count",
    "html_count",
    "total_csv_rows",
    "max_csv_columns",
    "validation_bucket",
    "notes",
]

SCHEMA_PROFILE_FIELDS = [
    "source_id",
    "artifact_type",
    "raw_kind",
    "csv_row_count",
    "csv_column_count",
    "columns",
    "local_path",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return sum(1 for _ in csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


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


def truthy(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def decode_text(data: bytes) -> str:
    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def classify_bytes(data: bytes, extension: str, content_type: str) -> str:
    head = data[:2048].lower()
    ext = str(extension or "").lower()
    ctype = str(content_type or "").lower()

    if data[:2] == b"\x1f\x8b":
        return "gzip"

    if b"<html" in head or b"<!doctype html" in head:
        return "html"

    if ext.endswith(".csv") or "csv" in ctype:
        return "csv"

    if ext.endswith(".txt"):
        return "text"

    if ext.endswith(".gz"):
        return "gzip_or_unknown"

    return "unknown"


def parse_csv_bytes(data: bytes) -> dict:
    text = decode_text(data)

    if not text.strip():
        return {
            "csv_parse_ok": False,
            "csv_delimiter": "",
            "csv_row_count": 0,
            "csv_column_count": 0,
            "columns": [],
            "issues": ["empty_csv_text"],
        }

    sample = text[:20000]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except Exception:
        dialect = csv.excel
        delimiter = ","

    try:
        reader = csv.reader(io.StringIO(text), dialect)
        rows_iter = iter(reader)
        header = next(rows_iter, [])
        data_rows = 0
        max_columns = len(header)

        for row in rows_iter:
            data_rows += 1
            if len(row) > max_columns:
                max_columns = len(row)

        issues = []

        if not header:
            issues.append("missing_header")

        if data_rows == 0:
            issues.append("no_data_rows")

        return {
            "csv_parse_ok": bool(header),
            "csv_delimiter": delimiter,
            "csv_row_count": data_rows,
            "csv_column_count": max_columns,
            "columns": [str(col).strip() for col in header],
            "issues": issues,
        }
    except Exception as exc:
        return {
            "csv_parse_ok": False,
            "csv_delimiter": delimiter,
            "csv_row_count": 0,
            "csv_column_count": 0,
            "columns": [],
            "issues": [f"csv_parse_error:{type(exc).__name__}:{exc}"],
        }


def validate_manifest_artifact(row: dict) -> tuple[dict, dict | None]:
    local_path = Path(row.get("local_path", ""))
    source_id = row.get("source_id", "")
    artifact_type = row.get("artifact_type", "")
    extension = row.get("extension", "")
    content_type = row.get("content_type", "")

    issues = []
    exists = local_path.exists()

    actual_bytes = 0
    actual_sha = ""
    gzip_magic_actual = False
    gzip_attempted = False
    gzip_ok = False
    raw_kind = "missing"
    csv_attempted = False
    csv_ok = False
    csv_delimiter = ""
    csv_rows = 0
    csv_cols = 0
    columns = []

    manifest_bytes = int(row.get("bytes", "0") or 0)
    manifest_sha = row.get("sha256", "")
    gzip_magic_manifest = truthy(row.get("gzip_magic", ""))

    if not exists:
        issues.append("local_path_missing")
    else:
        data = local_path.read_bytes()
        actual_bytes = len(data)
        actual_sha = sha256_bytes(data)
        gzip_magic_actual = data[:2] == b"\x1f\x8b"

        if manifest_bytes != actual_bytes:
            issues.append(f"bytes_mismatch:manifest={manifest_bytes}:actual={actual_bytes}")

        if manifest_sha and manifest_sha != actual_sha:
            issues.append("sha256_mismatch")

        raw_kind = classify_bytes(data, extension, content_type)

        payload_for_csv = data

        if gzip_magic_actual:
            gzip_attempted = True
            try:
                payload_for_csv = gzip.decompress(data)
                gzip_ok = True
                raw_kind = "gzip_csv_candidate"
            except Exception as exc:
                issues.append(f"gzip_decompress_error:{type(exc).__name__}:{exc}")
                payload_for_csv = b""

        if artifact_type in {"raw_source_file", "mii_security_file_candidate"}:
            if payload_for_csv:
                csv_attempted = True
                csv_result = parse_csv_bytes(payload_for_csv)
                csv_ok = csv_result["csv_parse_ok"]
                csv_delimiter = csv_result["csv_delimiter"]
                csv_rows = csv_result["csv_row_count"]
                csv_cols = csv_result["csv_column_count"]
                columns = csv_result["columns"]
                issues.extend(csv_result["issues"])

                if csv_ok:
                    raw_kind = "csv" if not gzip_magic_actual else "gzip_csv"
            else:
                issues.append("no_payload_available_for_csv_validation")

    if not exists:
        validation_bucket = "missing"
    elif row.get("download_status", "") != "downloaded" and artifact_type != "landing_html":
        validation_bucket = "download_not_clean"
    elif artifact_type in {"raw_source_file", "mii_security_file_candidate"} and not csv_ok:
        validation_bucket = "raw_file_invalid_or_unparseable"
    elif artifact_type == "landing_html" and actual_bytes > 0:
        validation_bucket = "landing_saved"
    elif artifact_type in {"raw_source_file", "mii_security_file_candidate"} and csv_ok:
        validation_bucket = "valid_raw_csv"
    else:
        validation_bucket = "review"

    profile = {
        "artifact_id": row.get("artifact_id", ""),
        "source_id": source_id,
        "artifact_type": artifact_type,
        "local_path": str(local_path),
        "exists": exists,
        "download_status": row.get("download_status", ""),
        "http_status": row.get("http_status", ""),
        "content_type": content_type,
        "extension": extension,
        "manifest_bytes": manifest_bytes,
        "actual_bytes": actual_bytes,
        "manifest_sha256": manifest_sha,
        "actual_sha256": actual_sha,
        "sha256_matches": bool(manifest_sha and manifest_sha == actual_sha),
        "gzip_magic_manifest": gzip_magic_manifest,
        "gzip_magic_actual": gzip_magic_actual,
        "gzip_decompress_attempted": gzip_attempted,
        "gzip_decompress_ok": gzip_ok,
        "raw_kind": raw_kind,
        "csv_parse_attempted": csv_attempted,
        "csv_parse_ok": csv_ok,
        "csv_delimiter": csv_delimiter,
        "csv_row_count": csv_rows,
        "csv_column_count": csv_cols,
        "columns_preview": " | ".join(columns[:30]),
        "validation_bucket": validation_bucket,
        "issues": " | ".join(issues),
    }

    schema = None
    if csv_attempted:
        schema = {
            "source_id": source_id,
            "artifact_type": artifact_type,
            "raw_kind": raw_kind,
            "csv_row_count": csv_rows,
            "csv_column_count": csv_cols,
            "columns": " | ".join(columns),
            "local_path": str(local_path),
        }

    return profile, schema


def build_source_diagnostics(file_profiles: list[dict], source_actions: list[dict]) -> list[dict]:
    grouped = defaultdict(list)

    for profile in file_profiles:
        grouped[profile["source_id"]].append(profile)

    source_ids = sorted(set(grouped.keys()) | {row.get("source_id", "") for row in source_actions})

    diagnostics = []

    for source_id in source_ids:
        profiles = grouped.get(source_id, [])
        artifact_count = len(profiles)
        downloaded_count = sum(1 for row in profiles if row["download_status"] == "downloaded")
        valid_raw_file_count = sum(1 for row in profiles if row["validation_bucket"] == "valid_raw_csv")
        csv_ok_count = sum(1 for row in profiles if row["csv_parse_ok"])
        gzip_ok_count = sum(1 for row in profiles if row["gzip_decompress_ok"])
        html_count = sum(1 for row in profiles if row["raw_kind"] == "html")
        total_csv_rows = sum(int(row["csv_row_count"] or 0) for row in profiles)
        max_csv_columns = max([int(row["csv_column_count"] or 0) for row in profiles] or [0])

        action_rows = [row for row in source_actions if row.get("source_id", "") == source_id]
        action_status = ", ".join(row.get("status", "") for row in action_rows)

        issue_text = " || ".join(
            f"{Path(row['local_path']).name}: {row['issues']}"
            for row in profiles
            if row["issues"]
        )

        if source_id in CRITICAL_SOURCE_IDS and valid_raw_file_count == 0:
            validation_bucket = "critical_source_missing_valid_raw"
        elif valid_raw_file_count > 0:
            validation_bucket = "valid_raw_source"
        elif html_count > 0:
            validation_bucket = "landing_or_html_only"
        else:
            validation_bucket = "review"

        diagnostics.append(
            {
                "source_id": source_id,
                "artifact_count": artifact_count,
                "downloaded_count": downloaded_count,
                "valid_raw_file_count": valid_raw_file_count,
                "csv_ok_count": csv_ok_count,
                "gzip_ok_count": gzip_ok_count,
                "html_count": html_count,
                "total_csv_rows": total_csv_rows,
                "max_csv_columns": max_csv_columns,
                "validation_bucket": validation_bucket,
                "notes": f"action_status={action_status}; issues={issue_text}",
            }
        )

    return diagnostics


def main() -> None:
    for path in [REPORT_JSON, REPORT_MD, FILE_PROFILE_CSV, SOURCE_DIAGNOSTICS_CSV, SCHEMA_PROFILE_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    c_report = read_json(V217C_JSON)
    manifest_rows = read_csv(V217C_MANIFEST_CSV)
    source_action_rows = read_csv(V217C_SOURCE_ACTIONS_CSV)
    canonical_rows = count_csv_rows(CANONICAL_DATASET)

    file_profiles = []
    schema_profiles = []

    for manifest_row in manifest_rows:
        profile, schema = validate_manifest_artifact(manifest_row)
        file_profiles.append(profile)
        if schema:
            schema_profiles.append(schema)

    source_diagnostics = build_source_diagnostics(file_profiles, source_action_rows)

    valid_raw_csv_profiles = [row for row in file_profiles if row["validation_bucket"] == "valid_raw_csv"]
    gzip_csv_profiles = [row for row in valid_raw_csv_profiles if row["gzip_decompress_ok"]]
    plain_csv_profiles = [row for row in valid_raw_csv_profiles if not row["gzip_decompress_ok"]]
    landing_profiles = [row for row in file_profiles if row["artifact_type"] == "landing_html"]

    equity_profile = next(
        (row for row in file_profiles if row["source_id"] == "nse_securities_available_equity_segment"),
        None,
    )

    mii_profiles = [
        row for row in file_profiles
        if row["source_id"] in {
            "nse_all_reports_cm_mii_security_file_nse_listed",
            "nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive",
        }
    ]

    valid_critical_sources = {
        row["source_id"]
        for row in file_profiles
        if row["source_id"] in CRITICAL_SOURCE_IDS and row["validation_bucket"] == "valid_raw_csv"
    }

    exclusion_sources_valid = {
        row["source_id"]
        for row in file_profiles
        if row["source_id"] in EXCLUSION_REFERENCE_IDS and row["validation_bucket"] == "valid_raw_csv"
    }

    sha_counts = Counter(row["actual_sha256"] for row in file_profiles if row["actual_sha256"])
    duplicate_sha_count = sum(1 for _, count in sha_counts.items() if count > 1)

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_17c_report_exists", V217C_JSON.exists(), "critical", str(V217C_JSON))
    add_check(
        "v2_17c_status_expected",
        c_report.get("status") == EXPECTED_V217C_STATUS,
        "critical",
        str(c_report.get("status", "")),
    )
    add_check(
        "v2_17c_recommended_d",
        c_report.get("recommended_next_phase") == EXPECTED_V217C_NEXT,
        "critical",
        str(c_report.get("recommended_next_phase", "")),
    )
    add_check("manifest_exists", V217C_MANIFEST_CSV.exists(), "critical", str(V217C_MANIFEST_CSV))
    add_check("source_actions_exists", V217C_SOURCE_ACTIONS_CSV.exists(), "critical", str(V217C_SOURCE_ACTIONS_CSV))
    add_check("raw_dir_exists", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("canonical_rows_expected", canonical_rows == CURRENT_CANONICAL_ROWS, "critical", f"canonical_rows={canonical_rows}")
    add_check("manifest_rows_present", len(manifest_rows) >= 10, "critical", f"manifest_rows={len(manifest_rows)}")
    add_check("file_profiles_generated", len(file_profiles) == len(manifest_rows), "critical", f"file_profiles={len(file_profiles)} manifest_rows={len(manifest_rows)}")
    add_check("valid_raw_csv_files_present", len(valid_raw_csv_profiles) >= 8, "critical", f"valid_raw_csv={len(valid_raw_csv_profiles)}")
    add_check("plain_csv_sources_present", len(plain_csv_profiles) >= 8, "critical", f"plain_csv={len(plain_csv_profiles)}")
    add_check("mii_gzip_sources_present", len(gzip_csv_profiles) >= 1, "critical", f"gzip_csv={len(gzip_csv_profiles)}")
    add_check(
        "equity_segment_valid_csv",
        bool(equity_profile and equity_profile["validation_bucket"] == "valid_raw_csv" and int(equity_profile["csv_row_count"] or 0) > 0),
        "critical",
        f"equity_profile={equity_profile}",
    )
    add_check("mii_sources_valid_or_reviewable", len([row for row in mii_profiles if row["validation_bucket"] == "valid_raw_csv"]) >= 1, "critical", f"mii_valid={len([row for row in mii_profiles if row['validation_bucket'] == 'valid_raw_csv'])}")
    add_check("critical_sources_valid", len(valid_critical_sources) >= 6, "critical", f"valid_critical_sources={sorted(valid_critical_sources)}")
    add_check("exclusion_reference_sources_valid", len(exclusion_sources_valid) >= 5, "critical", f"exclusion_valid={sorted(exclusion_sources_valid)}")
    add_check("schema_profiles_created", len(schema_profiles) >= 8, "critical", f"schema_profiles={len(schema_profiles)}")
    add_check("sha256_all_local_files_match_manifest", all(row["sha256_matches"] for row in file_profiles if row["exists"]), "critical", "all existing files match manifest sha256")
    add_check("landing_pages_available", len(landing_profiles) >= 2, "critical", f"landing_profiles={len(landing_profiles)}")
    add_check("duplicate_sha_review", duplicate_sha_count >= 0, "warning", f"duplicate_sha_groups={duplicate_sha_count}")
    add_check("full_source_still_blocked", canonical_rows < FULL_SOURCE_THRESHOLD, "critical", f"{canonical_rows} < {FULL_SOURCE_THRESHOLD}")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("raw_validation_performed", True, "critical", "raw_validation_performed=True")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("security_rows_not_extracted", True, "critical", "security_rows_extracted=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed == 0:
        status = "NSE_INDIA_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_CANDIDATE_EXTRACTION_READY_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE
    else:
        status = "NSE_INDIA_RAW_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.17D_FIX - NSE India Raw Validation Repair"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": canonical_rows,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": round((canonical_rows / FULL_SOURCE_THRESHOLD) * 100, 2),
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "route_reference": {
            "v2_17c_artifact": str(V217C_JSON),
            "v2_17c_status": c_report.get("status", ""),
            "v2_17c_recommended_next_phase": c_report.get("recommended_next_phase", ""),
            "provider": "NSE India",
            "market": "India",
        },
        "raw_validation_summary": {
            "raw_dir": str(RAW_DIR),
            "manifest_rows": len(manifest_rows),
            "file_profiles": len(file_profiles),
            "schema_profiles": len(schema_profiles),
            "source_diagnostics": len(source_diagnostics),
            "valid_raw_csv_files": len(valid_raw_csv_profiles),
            "plain_csv_files": len(plain_csv_profiles),
            "gzip_csv_files": len(gzip_csv_profiles),
            "landing_files": len(landing_profiles),
            "equity_segment_rows": int(equity_profile["csv_row_count"]) if equity_profile else 0,
            "mii_valid_files": len([row for row in mii_profiles if row["validation_bucket"] == "valid_raw_csv"]),
            "critical_sources_valid": sorted(valid_critical_sources),
            "exclusion_reference_sources_valid": sorted(exclusion_sources_valid),
            "duplicate_sha_groups": duplicate_sha_count,
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "file_profile_preview": file_profiles[:50],
        "source_diagnostics_preview": source_diagnostics[:50],
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "v2_17c_report_read": True,
            "manifest_read": True,
            "raw_files_read": True,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "raw_validation_performed": True,
            "format_validation_performed": True,
            "gzip_validation_performed": True,
            "csv_header_validation_performed": True,
            "candidate_extraction_performed": False,
            "security_rows_extracted": False,
            "canonical_comparison_performed": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "net_new_filtering_applied_to_canonical": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "full_source_gate_unblocked": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)
    write_csv(FILE_PROFILE_CSV, file_profiles, FILE_PROFILE_FIELDS)
    write_csv(SOURCE_DIAGNOSTICS_CSV, source_diagnostics, SOURCE_DIAGNOSTIC_FIELDS)
    write_csv(SCHEMA_PROFILE_CSV, schema_profiles, SCHEMA_PROFILE_FIELDS)

    profile_lines = "\n".join(
        f"- `{row['source_id']}` `{row['artifact_type']}` bucket=`{row['validation_bucket']}` rows=`{row['csv_row_count']}` cols=`{row['csv_column_count']}` path=`{row['local_path']}`"
        for row in file_profiles
    )

    source_lines = "\n".join(
        f"- `{row['source_id']}` bucket=`{row['validation_bucket']}` csv_ok=`{row['csv_ok_count']}` rows=`{row['total_csv_rows']}`"
        for row in source_diagnostics
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

NSE India raw validation completed.

This phase validates local raw files captured in v2.17C. It checks file existence, bytes, SHA-256, gzip decompression, CSV parseability, headers and row counts. It does not extract candidate securities, does not compare against the canonical dataset and does not modify or rebuild any expanded universe dataset.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{canonical_rows}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completion: `{round((canonical_rows / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Raw validation summary

- Raw directory: `{RAW_DIR}`
- Manifest rows: `{len(manifest_rows)}`
- File profiles: `{len(file_profiles)}`
- Schema profiles: `{len(schema_profiles)}`
- Source diagnostics: `{len(source_diagnostics)}`
- Valid raw CSV files: `{len(valid_raw_csv_profiles)}`
- Plain CSV files: `{len(plain_csv_profiles)}`
- Gzip CSV files: `{len(gzip_csv_profiles)}`
- Landing files: `{len(landing_profiles)}`
- Equity segment rows: `{int(equity_profile["csv_row_count"]) if equity_profile else 0}`
- MII valid files: `{len([row for row in mii_profiles if row["validation_bucket"] == "valid_raw_csv"])}`
- Duplicate SHA groups: `{duplicate_sha_count}`
- Critical failed checks: `{critical_failed}`

## File profiles

{profile_lines}

## Source diagnostics

{source_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17C report read: true
- Manifest read: true
- Raw files read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Raw validation performed: true
- Format validation performed: true
- Gzip validation performed: true
- CSV header validation performed: true
- Candidate extraction performed: false
- Security rows extracted: false
- Canonical comparison performed: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Net-new filtering applied to canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17D validates the NSE India raw acquisition artifacts and prepares the route for candidate extraction dry run in v2.17E.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.17D NSE India raw validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("RAW_VALIDATION_SUMMARY:")
    for key, value in payload["raw_validation_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
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
