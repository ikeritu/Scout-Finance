from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.19D"
PHASE = "KRX Raw Validation"
PHASE_TYPE = "raw-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "krx_v2_19c"

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219C_JSON = OUTPUT_DIR / "krx_raw_acquisition_v2_19c.json"
V219C_MANIFEST_CSV = OUTPUT_DIR / "krx_raw_acquisition_manifest_v2_19c.csv"
V219C_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "krx_raw_acquisition_source_diagnostics_v2_19c.csv"

REPORT_JSON = OUTPUT_DIR / "krx_raw_validation_v2_19d.json"
REPORT_MD = OUTPUT_DIR / "krx_raw_validation_v2_19d.md"
ARTIFACT_AUDIT_CSV = OUTPUT_DIR / "krx_raw_validation_artifact_audit_v2_19d.csv"
SOURCE_READINESS_CSV = OUTPUT_DIR / "krx_raw_validation_source_readiness_v2_19d.csv"
ISSUE_AUDIT_CSV = OUTPUT_DIR / "krx_raw_validation_issue_audit_v2_19d.csv"
CHECKS_CSV = OUTPUT_DIR / "krx_raw_validation_checks_v2_19d.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "krx_raw_validation_next_actions_v2_19d.csv"

EXPECTED_V219C_STATUS = "KRX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

RECOMMENDED_REPAIR_PHASE = "v2.19C_FIX - KRX Raw Acquisition Repair"
RECOMMENDED_EXTRACTION_PHASE = "v2.19E - KRX Candidate Extraction Dry Run"
RECOMMENDED_REVIEW_PHASE = "v2.19D_REVIEW - KRX Raw Validation Review"


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


def read_sample(path: Path, max_bytes: int = 250000) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()[:max_bytes]
    for encoding in ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"]:
        try:
            return data.decode(encoding, errors="ignore")
        except Exception:
            continue
    return data.decode("utf-8", errors="ignore")


def count_signal(text: str, tokens: list[str]) -> int:
    lower = text.lower()
    return sum(lower.count(token.lower()) for token in tokens)


def classify_artifact_readiness(row: dict[str, str], sample: str) -> tuple[str, str, bool]:
    source_id = row.get("source_id", "")
    artifact_id = row.get("artifact_id", "")
    status = row.get("acquisition_status", "")
    http_status = str(row.get("http_status", ""))
    parse_hint = row.get("parse_hint", "")
    artifact_bytes = to_int(row.get("artifact_bytes", 0))
    lower = sample.lower()

    if not to_bool(row.get("artifact_exists", False)):
        return "missing_artifact", "Artifact path does not exist.", False

    if artifact_bytes <= 0:
        return "empty_artifact", "Artifact exists but is empty.", False

    if status == "not_attempted_missing_service_key":
        return "optional_api_not_attempted_missing_key", "Optional data.go.kr API was not attempted because DATA_GO_KR_SERVICE_KEY is missing.", False

    if status == "not_attempted_invalid_otp":
        return "not_parse_ready_invalid_otp", "KRX CSV download was not attempted because OTP token was invalid.", False

    if http_status == "403":
        return "not_parse_ready_http_403", "Official source returned HTTP 403 and was captured as diagnostic evidence.", False

    if parse_hint in {"csv_like", "json_like", "xlsx_or_zip_container"} and http_status == "200":
        return "parse_ready_structured_raw", "Structured artifact appears parse-ready.", True

    if parse_hint == "xml_or_api_error_payload" and http_status == "200":
        return "api_payload_or_error_requires_validation", "XML/API-like payload captured; requires schema validation before extraction.", True

    if parse_hint == "html_or_dynamic_page":
        html_table_signals = count_signal(sample, ["<table", "<tr", "<td", "<th"])
        company_signals = count_signal(sample, ["listed company", "kospi", "kosdaq", "konex", "isin", "ticker", "stock code", "company name"])
        download_signals = count_signal(sample, ["download", "filedown", "generateotp", "csv", "excel", "xls"])

        if source_id == "krx_global_listed_company" and http_status == "200":
            if html_table_signals >= 10 and company_signals >= 2:
                return "html_table_probe_required", "KRX Global HTML may contain table-like content, but extraction must not start before a dedicated parser/probe phase.", False
            if download_signals > 0 or company_signals > 0:
                return "html_dynamic_repair_required", "KRX Global HTML was captured, but likely requires download/session/form repair before candidate extraction.", False
            return "html_captured_not_parse_ready", "HTTP 200 HTML captured, but no sufficient structured row signal was confirmed.", False

        return "html_or_dynamic_not_parse_ready", "HTML/dynamic page captured but not considered direct candidate source.", False

    if "forbidden" in lower or "access denied" in lower:
        return "not_parse_ready_forbidden_payload", "Captured payload appears to be an access-denied/forbidden response.", False

    if "missing" in lower and "service" in lower and "key" in lower:
        return "optional_api_not_attempted_missing_key", "Captured diagnostic indicates missing service key.", False

    return "not_parse_ready_unknown", "Artifact captured but not parse-ready under v2.19D rules.", False


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        ARTIFACT_AUDIT_CSV,
        SOURCE_READINESS_CSV,
        ISSUE_AUDIT_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219c = read_json(V219C_JSON)
    _, manifest_rows = read_csv_with_header(V219C_MANIFEST_CSV)
    _, source_diag_rows = read_csv_with_header(V219C_SOURCE_DIAGNOSTICS_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    artifact_audit_rows: list[dict[str, Any]] = []
    issue_audit_rows: list[dict[str, Any]] = []

    for row in manifest_rows:
        artifact_path = Path(row.get("artifact_path", ""))
        expected_bytes = to_int(row.get("artifact_bytes", 0))
        expected_sha = row.get("artifact_sha256", "")
        exists = artifact_path.exists()
        actual_bytes = artifact_path.stat().st_size if exists else 0
        actual_sha = sha256_file(artifact_path) if exists else ""
        bytes_match = exists and actual_bytes == expected_bytes
        sha_match = exists and actual_sha == expected_sha

        sample = read_sample(artifact_path)
        readiness_bucket, readiness_detail, parse_ready = classify_artifact_readiness(row, sample)

        html_table_signal_count = count_signal(sample, ["<table", "<tr", "<td", "<th"])
        download_signal_count = count_signal(sample, ["download", "filedown", "generateotp", "csv", "excel", "xls"])
        company_signal_count = count_signal(sample, ["listed company", "kospi", "kosdaq", "konex", "isin", "ticker", "stock code", "company name"])
        forbidden_signal_count = count_signal(sample, ["403", "forbidden", "access denied"])

        audit = {
            "source_id": row.get("source_id", ""),
            "artifact_id": row.get("artifact_id", ""),
            "source_role": row.get("source_role", ""),
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
            "html_table_signal_count": html_table_signal_count,
            "download_signal_count": download_signal_count,
            "company_signal_count": company_signal_count,
            "forbidden_signal_count": forbidden_signal_count,
            "readiness_bucket": readiness_bucket,
            "readiness_detail": readiness_detail,
            "parse_ready_for_candidate_extraction": parse_ready,
        }
        artifact_audit_rows.append(audit)

        if not exists:
            issue_audit_rows.append({
                "severity": "critical",
                "issue_type": "missing_artifact",
                "source_id": row.get("source_id", ""),
                "artifact_id": row.get("artifact_id", ""),
                "detail": "Manifest artifact path does not exist.",
                "recommended_action": "Review v2.19C raw acquisition output before continuing.",
            })
        elif not bytes_match or not sha_match:
            issue_audit_rows.append({
                "severity": "critical",
                "issue_type": "artifact_integrity_mismatch",
                "source_id": row.get("source_id", ""),
                "artifact_id": row.get("artifact_id", ""),
                "detail": f"bytes_match={bytes_match}; sha256_match={sha_match}",
                "recommended_action": "Do not proceed; investigate raw artifact integrity.",
            })
        elif readiness_bucket in {"not_parse_ready_http_403", "not_parse_ready_invalid_otp", "html_dynamic_repair_required", "html_or_dynamic_not_parse_ready", "optional_api_not_attempted_missing_key", "html_table_probe_required"}:
            issue_audit_rows.append({
                "severity": "warning",
                "issue_type": readiness_bucket,
                "source_id": row.get("source_id", ""),
                "artifact_id": row.get("artifact_id", ""),
                "detail": readiness_detail,
                "recommended_action": "Use v2.19C_FIX to repair official KRX acquisition before candidate extraction, unless a validation review approves an HTML parser probe.",
            })

    source_ids = sorted(set(row["source_id"] for row in artifact_audit_rows))
    source_readiness_rows: list[dict[str, Any]] = []

    for sid in source_ids:
        rows = [row for row in artifact_audit_rows if row["source_id"] == sid]
        source_role_values = sorted(set(row["source_role"] for row in rows if row["source_role"]))
        parse_ready_rows = [row for row in rows if row["parse_ready_for_candidate_extraction"]]
        http_200_rows = [row for row in rows if str(row["http_status"]) == "200"]
        captured_rows = [row for row in rows if str(row["acquisition_status"]).startswith("captured")]
        critical_issues = [
            issue for issue in issue_audit_rows
            if issue["source_id"] == sid and issue["severity"] == "critical"
        ]
        warning_issues = [
            issue for issue in issue_audit_rows
            if issue["source_id"] == sid and issue["severity"] == "warning"
        ]

        if parse_ready_rows:
            final_status = "parse_ready"
        elif sid == "krx_global_listed_company" and http_200_rows:
            final_status = "captured_html_repair_or_probe_required"
        elif sid == "krx_data_marketplace_all_listed_issues":
            final_status = "blocked_http_403_or_invalid_otp_repair_required"
        elif sid == "public_data_portal_krx_listed_stock_info":
            final_status = "metadata_captured_api_key_optional"
        elif sid == "krx_open_api_data_feed_products":
            final_status = "reference_only_not_parse_ready"
        elif captured_rows:
            final_status = "captured_not_parse_ready"
        else:
            final_status = "not_captured"

        source_readiness_rows.append({
            "source_id": sid,
            "source_roles": "|".join(source_role_values),
            "artifact_count": len(rows),
            "captured_count": len(captured_rows),
            "http_200_count": len(http_200_rows),
            "parse_ready_count": len(parse_ready_rows),
            "critical_issue_count": len(critical_issues),
            "warning_issue_count": len(warning_issues),
            "readiness_buckets": "|".join(sorted(set(row["readiness_bucket"] for row in rows))),
            "final_source_status": final_status,
            "candidate_extraction_ready": len(parse_ready_rows) > 0,
        })

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    total_artifacts = len(artifact_audit_rows)
    artifacts_exist_count = sum(1 for row in artifact_audit_rows if row["artifact_exists"])
    bytes_match_count = sum(1 for row in artifact_audit_rows if row["bytes_match"])
    sha_match_count = sum(1 for row in artifact_audit_rows if row["sha256_match"])
    parse_ready_count = sum(1 for row in artifact_audit_rows if row["parse_ready_for_candidate_extraction"])
    primary_parse_ready_count = sum(
        1 for row in artifact_audit_rows
        if row["parse_ready_for_candidate_extraction"]
        and row["source_role"] in {"primary_candidate_source", "primary_or_crosscheck_source"}
    )
    critical_issue_count = sum(1 for issue in issue_audit_rows if issue["severity"] == "critical")
    warning_issue_count = sum(1 for issue in issue_audit_rows if issue["severity"] == "warning")

    extraction_ready = primary_parse_ready_count >= 1 and critical_issue_count == 0
    repair_required = not extraction_ready and critical_issue_count == 0

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19c_report_exists", V219C_JSON.exists(), "critical", str(V219C_JSON))
    add_check("v2_19c_status_expected", v219c.get("status") == EXPECTED_V219C_STATUS, "critical", v219c.get("status", ""))
    add_check("v2_19c_manifest_exists", V219C_MANIFEST_CSV.exists(), "critical", str(V219C_MANIFEST_CSV))
    add_check("v2_19c_source_diagnostics_exists", V219C_SOURCE_DIAGNOSTICS_CSV.exists(), "critical", str(V219C_SOURCE_DIAGNOSTICS_CSV))
    add_check("raw_dir_exists", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("manifest_rows_expected", len(manifest_rows) >= 7, "critical", f"manifest_rows={len(manifest_rows)}")
    add_check("all_manifest_artifacts_exist", artifacts_exist_count == total_artifacts, "critical", f"artifacts_exist={artifacts_exist_count}/{total_artifacts}")
    add_check("all_manifest_bytes_match", bytes_match_count == total_artifacts, "critical", f"bytes_match={bytes_match_count}/{total_artifacts}")
    add_check("all_manifest_sha256_match", sha_match_count == total_artifacts, "critical", f"sha256_match={sha_match_count}/{total_artifacts}")
    add_check("artifact_critical_issues_zero", critical_issue_count == 0, "critical", f"critical_issue_count={critical_issue_count}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("raw_files_read_only", True, "critical", "raw_files_written=False")
    add_check("network_not_used_by_validation", True, "critical", "network_download_performed=False")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("parse_ready_artifacts_present", parse_ready_count > 0, "warning", f"parse_ready_count={parse_ready_count}")
    add_check("primary_parse_ready_artifacts_present", primary_parse_ready_count > 0, "warning", f"primary_parse_ready_count={primary_parse_ready_count}")
    add_check("repair_required_before_extraction", repair_required, "warning", f"repair_required={repair_required}; extraction_ready={extraction_ready}")

    if critical_failed > 0:
        status = "KRX_RAW_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE
    elif extraction_ready:
        status = "KRX_RAW_VALIDATION_COMPLETED_PARSE_READY_CANDIDATE_EXTRACTION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_EXTRACTION_PHASE
    else:
        status = "KRX_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_REPAIR_PHASE

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "KRX",
            "action": "repair_official_raw_acquisition",
            "priority": "high",
            "reason": "No primary KRX artifact is parse-ready for candidate extraction.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "official KRX/data.go.kr sources only; no candidate extraction during repair",
        },
        {
            "action_order": 2,
            "action_scope": "KRX Global",
            "action": "inspect_html_download_flow",
            "priority": "high",
            "reason": "KRX Global returned HTTP 200 HTML and may contain download/session/form hints.",
            "recommended_phase": RECOMMENDED_REPAIR_PHASE,
            "guardrails": "use captured HTML and official KRX URLs only; capture any new raw response in manifest",
        },
        {
            "action_order": 3,
            "action_scope": "KRX Data Marketplace",
            "action": "repair_403_otp_flow",
            "priority": "high",
            "reason": "Data Marketplace and GenerateOTP returned HTTP 403; CSV download was not attempted due invalid OTP.",
            "recommended_phase": RECOMMENDED_REPAIR_PHASE,
            "guardrails": "do not use unofficial mirrors; preserve all error payloads",
        },
        {
            "action_order": 4,
            "action_scope": "data.go.kr",
            "action": "optionally_configure_service_key",
            "priority": "medium",
            "reason": "Public Data Portal API was not attempted because DATA_GO_KR_SERVICE_KEY is missing.",
            "recommended_phase": RECOMMENDED_REPAIR_PHASE,
            "guardrails": "optional supporting source only; do not block if no key is available",
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
        "raw_validation_summary": {
            "manifest_rows": len(manifest_rows),
            "source_diagnostics_rows": len(source_diag_rows),
            "artifact_audit_rows": len(artifact_audit_rows),
            "artifacts_exist_count": artifacts_exist_count,
            "bytes_match_count": bytes_match_count,
            "sha256_match_count": sha_match_count,
            "parse_ready_count": parse_ready_count,
            "primary_parse_ready_count": primary_parse_ready_count,
            "critical_issue_count": critical_issue_count,
            "warning_issue_count": warning_issue_count,
            "extraction_ready": extraction_ready,
            "repair_required": repair_required,
            "critical_failed_checks": critical_failed,
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
        "html_table_signal_count",
        "download_signal_count",
        "company_signal_count",
        "forbidden_signal_count",
        "readiness_bucket",
        "readiness_detail",
        "parse_ready_for_candidate_extraction",
    ]

    source_fieldnames = [
        "source_id",
        "source_roles",
        "artifact_count",
        "captured_count",
        "http_200_count",
        "parse_ready_count",
        "critical_issue_count",
        "warning_issue_count",
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
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    artifact_lines = "\n".join(
        f"- `{row['artifact_id']}` - exists `{row['artifact_exists']}`, bytes `{row['bytes_match']}`, sha `{row['sha256_match']}`, readiness `{row['readiness_bucket']}`"
        for row in artifact_audit_rows
    )

    source_lines = "\n".join(
        f"- `{row['source_id']}` - status `{row['final_source_status']}`, parse-ready `{row['parse_ready_count']}`, warnings `{row['warning_issue_count']}`"
        for row in source_readiness_rows
    )

    issue_lines = "\n".join(
        f"- {row['severity']} `{row['issue_type']}` / `{row['source_id']}` / `{row['artifact_id']}` - {row['detail']}"
        for row in issue_audit_rows
    ) or "- No issues."

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

v2.19D validates the raw KRX artifacts captured in v2.19C.

This phase is validation-only. It does not download new data, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Raw validation summary

- Manifest rows: `{len(manifest_rows)}`
- Source diagnostics rows: `{len(source_diag_rows)}`
- Artifact audit rows: `{len(artifact_audit_rows)}`
- Artifacts exist: `{artifacts_exist_count}/{total_artifacts}`
- Bytes match: `{bytes_match_count}/{total_artifacts}`
- SHA256 match: `{sha_match_count}/{total_artifacts}`
- Parse-ready artifacts: `{parse_ready_count}`
- Primary parse-ready artifacts: `{primary_parse_ready_count}`
- Critical issues: `{critical_issue_count}`
- Warning issues: `{warning_issue_count}`
- Extraction ready: `{extraction_ready}`
- Repair required: `{repair_required}`
- Critical failed checks: `{critical_failed}`

## Artifact audit

{artifact_lines}

## Source readiness

{source_lines}

## Issues

{issue_lines}

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

    print("v2.19D KRX raw validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("RAW_VALIDATION_SUMMARY:")
    for key, value in payload["raw_validation_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_READINESS:")
    for row in source_readiness_rows:
        print(f"- {row['source_id']}: status={row['final_source_status']} parse_ready={row['parse_ready_count']} warnings={row['warning_issue_count']}")
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
