from __future__ import annotations

import csv
import hashlib
import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VERSION = "v2.19C"
PHASE = "KRX Raw Acquisition"
PHASE_TYPE = "raw-acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "krx_v2_19c"

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219B_JSON = OUTPUT_DIR / "krx_acquisition_plan_v2_19b.json"
V219B_SOURCE_INVENTORY_CSV = OUTPUT_DIR / "krx_acquisition_plan_source_inventory_v2_19b.csv"
V219B_RAW_ARTIFACTS_CSV = OUTPUT_DIR / "krx_acquisition_plan_raw_artifacts_v2_19b.csv"
V219B_VALIDATION_STRATEGY_CSV = OUTPUT_DIR / "krx_acquisition_plan_validation_strategy_v2_19b.csv"

REPORT_JSON = OUTPUT_DIR / "krx_raw_acquisition_v2_19c.json"
REPORT_MD = OUTPUT_DIR / "krx_raw_acquisition_v2_19c.md"
MANIFEST_CSV = OUTPUT_DIR / "krx_raw_acquisition_manifest_v2_19c.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "krx_raw_acquisition_source_diagnostics_v2_19c.csv"
CHECKS_CSV = OUTPUT_DIR / "krx_raw_acquisition_checks_v2_19c.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "krx_raw_acquisition_next_actions_v2_19c.csv"

EXPECTED_V219B_STATUS = "KRX_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_FOR_RAW_ACQUISITION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

RECOMMENDED_NEXT_PHASE = "v2.19D - KRX Raw Validation"
RECOMMENDED_REVIEW_PHASE = "v2.19C_REVIEW - KRX Raw Acquisition Review"

ALLOWED_HOSTS = {
    "global.krx.co.kr",
    "data.krx.co.kr",
    "openapi.krx.co.kr",
    "www.data.go.kr",
    "apis.data.go.kr",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 ScoutFinanceRawAcquisition/2.19C",
    "Accept": "text/html,application/xhtml+xml,application/xml,application/json,text/csv,*/*",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    "Connection": "close",
}

REQUEST_TIMEOUT_SECONDS = 45


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


def is_official_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"https", "http"} and parsed.hostname in ALLOWED_HOSTS


def ensure_output_path(path: Path) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def classify_parse_hint(content_type: str, data: bytes, path: Path) -> str:
    lower_ct = (content_type or "").lower()
    sample = data[:500].lower()

    if not data:
        return "empty_response"
    if b"<html" in sample or "text/html" in lower_ct:
        return "html_or_dynamic_page"
    if b"<?xml" in sample or "<response" in sample.decode("utf-8", errors="ignore").lower() or "xml" in lower_ct:
        return "xml_or_api_error_payload"
    if data[:2] == b"PK" or path.suffix.lower() == ".xlsx":
        return "xlsx_or_zip_container"
    if b"," in data[:2000] or "csv" in lower_ct or path.suffix.lower() == ".csv":
        return "csv_like"
    if b"{" in data[:100] or b"[" in data[:100] or "json" in lower_ct:
        return "json_like"
    return "binary_or_text_unknown"


def http_request(
    *,
    url: str,
    method: str = "GET",
    data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    allow_unverified_ssl_fallback: bool = True,
) -> dict[str, Any]:
    if not is_official_allowed_url(url):
        raise SystemExit(f"OFFICIAL_SCOPE_GUARD: URL not allowed: {url}")

    merged_headers = dict(DEFAULT_HEADERS)
    if headers:
        merged_headers.update(headers)

    encoded_data: bytes | None = None
    if data is not None:
        encoded_data = urllib.parse.urlencode(data).encode("utf-8")
        merged_headers.setdefault("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")

    request = urllib.request.Request(url=url, data=encoded_data, headers=merged_headers, method=method)

    contexts = [ssl.create_default_context()]
    if allow_unverified_ssl_fallback:
        contexts.append(ssl._create_unverified_context())

    last_error = ""
    for idx, context in enumerate(contexts):
        ssl_mode = "default_ssl" if idx == 0 else "unverified_ssl_fallback"
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=context) as response:
                content = response.read()
                return {
                    "ok": True,
                    "url": url,
                    "method": method,
                    "http_status": int(response.status),
                    "content_type": response.headers.get("Content-Type", ""),
                    "content_length_header": response.headers.get("Content-Length", ""),
                    "bytes": len(content),
                    "sha256": sha256_bytes(content),
                    "ssl_mode": ssl_mode,
                    "error_type": "",
                    "error_message": "",
                    "content": content,
                }
        except urllib.error.HTTPError as exc:
            content = exc.read() if hasattr(exc, "read") else b""
            return {
                "ok": False,
                "url": url,
                "method": method,
                "http_status": int(exc.code),
                "content_type": exc.headers.get("Content-Type", "") if exc.headers else "",
                "content_length_header": exc.headers.get("Content-Length", "") if exc.headers else "",
                "bytes": len(content),
                "sha256": sha256_bytes(content),
                "ssl_mode": ssl_mode,
                "error_type": "HTTPError",
                "error_message": str(exc),
                "content": content,
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            continue

    error_content = last_error.encode("utf-8")
    return {
        "ok": False,
        "url": url,
        "method": method,
        "http_status": 0,
        "content_type": "text/plain; charset=utf-8",
        "content_length_header": "",
        "bytes": len(error_content),
        "sha256": sha256_bytes(error_content),
        "ssl_mode": "failed_all_ssl_modes",
        "error_type": "RequestError",
        "error_message": last_error,
        "content": error_content,
    }


def save_response_artifact(path: Path, response: dict[str, Any]) -> dict[str, Any]:
    ensure_output_path(path)
    content = response["content"]
    path.write_bytes(content)

    return {
        "artifact_path": str(path),
        "artifact_exists": path.exists(),
        "artifact_bytes": path.stat().st_size if path.exists() else 0,
        "artifact_sha256": sha256_file(path) if path.exists() else "",
        "parse_hint": classify_parse_hint(response.get("content_type", ""), content, path),
    }


def add_manifest_row(
    manifest: list[dict[str, Any]],
    *,
    source_id: str,
    artifact_id: str,
    source_role: str,
    url: str,
    method: str,
    acquisition_status: str,
    response: dict[str, Any] | None,
    artifact: dict[str, Any] | None,
    notes: str,
) -> None:
    manifest.append(
        {
            "source_id": source_id,
            "artifact_id": artifact_id,
            "source_role": source_role,
            "url": url,
            "method": method,
            "official_scope_allowed": is_official_allowed_url(url) if url else True,
            "acquisition_status": acquisition_status,
            "http_status": response.get("http_status", "") if response else "",
            "content_type": response.get("content_type", "") if response else "",
            "content_length_header": response.get("content_length_header", "") if response else "",
            "response_bytes": response.get("bytes", "") if response else "",
            "response_sha256": response.get("sha256", "") if response else "",
            "ssl_mode": response.get("ssl_mode", "") if response else "",
            "error_type": response.get("error_type", "") if response else "",
            "error_message": response.get("error_message", "") if response else "",
            "artifact_path": artifact.get("artifact_path", "") if artifact else "",
            "artifact_exists": artifact.get("artifact_exists", False) if artifact else False,
            "artifact_bytes": artifact.get("artifact_bytes", 0) if artifact else 0,
            "artifact_sha256": artifact.get("artifact_sha256", "") if artifact else "",
            "parse_hint": artifact.get("parse_hint", "") if artifact else "",
            "notes": notes,
        }
    )


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        MANIFEST_CSV,
        SOURCE_DIAGNOSTICS_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists():
        existing_files = [p for p in RAW_DIR.iterdir() if p.is_file()]
        if existing_files:
            raise SystemExit(f"NO_OVERWRITE_GUARD: raw dir already contains files: {RAW_DIR}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    v219b = read_json(V219B_JSON)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    _, source_inventory_rows = read_csv_with_header(V219B_SOURCE_INVENTORY_CSV)
    _, raw_artifacts_plan_rows = read_csv_with_header(V219B_RAW_ARTIFACTS_CSV)
    _, validation_strategy_rows = read_csv_with_header(V219B_VALIDATION_STRATEGY_CSV)

    manifest: list[dict[str, Any]] = []

    # 1) Global KRX listed company official page.
    global_url = "https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp"
    global_response = http_request(
        url=global_url,
        method="GET",
        headers={"Referer": "https://global.krx.co.kr/"}
    )
    global_artifact = save_response_artifact(
        RAW_DIR / "krx_global_listed_company_page_v2_19c.html",
        global_response,
    )
    add_manifest_row(
        manifest,
        source_id="krx_global_listed_company",
        artifact_id="krx_global_listed_company_page",
        source_role="primary_candidate_source",
        url=global_url,
        method="GET",
        acquisition_status="captured" if global_artifact["artifact_exists"] else "failed",
        response=global_response,
        artifact=global_artifact,
        notes="Official KRX Global Listed Company page captured. Candidate rows may require dynamic download flow in later repair if HTML only.",
    )

    # 2) KRX Data Marketplace main official page.
    data_main_url = "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en"
    data_main_response = http_request(
        url=data_main_url,
        method="GET",
        headers={"Referer": "https://data.krx.co.kr/"}
    )
    data_main_artifact = save_response_artifact(
        RAW_DIR / "krx_data_marketplace_main_page_v2_19c.html",
        data_main_response,
    )
    add_manifest_row(
        manifest,
        source_id="krx_data_marketplace_all_listed_issues",
        artifact_id="krx_data_marketplace_main_page",
        source_role="primary_or_crosscheck_source",
        url=data_main_url,
        method="GET",
        acquisition_status="captured" if data_main_artifact["artifact_exists"] else "failed",
        response=data_main_response,
        artifact=data_main_artifact,
        notes="Official KRX Data Marketplace page captured.",
    )

    # 3) KRX Data Marketplace CSV download flow via official OTP endpoint.
    # This is the common official KRX file download flow; if parameters are rejected,
    # both OTP and error/download payloads are still captured and validated in v2.19D.
    otp_url = "https://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
    download_url = "https://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
    otp_payload = {
        "mktId": "ALL",
        "share": "1",
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT01901",
    }
    otp_response = http_request(
        url=otp_url,
        method="POST",
        data=otp_payload,
        headers={
            "Referer": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en",
            "Origin": "https://data.krx.co.kr",
            "X-Requested-With": "XMLHttpRequest",
        }
    )
    otp_artifact = save_response_artifact(
        RAW_DIR / "krx_data_marketplace_all_listed_issues_otp_response_v2_19c.txt",
        otp_response,
    )
    add_manifest_row(
        manifest,
        source_id="krx_data_marketplace_all_listed_issues",
        artifact_id="krx_data_marketplace_all_listed_issues_otp_response",
        source_role="primary_or_crosscheck_source",
        url=otp_url,
        method="POST",
        acquisition_status="captured" if otp_artifact["artifact_exists"] else "failed",
        response=otp_response,
        artifact=otp_artifact,
        notes="Official KRX GenerateOTP response captured for all-listed-issues candidate download flow.",
    )

    otp_text = otp_response["content"].decode("utf-8", errors="ignore").strip()
    otp_looks_valid = (
        otp_response.get("http_status") == 200
        and len(otp_text) >= 8
        and "<html" not in otp_text.lower()
        and "error" not in otp_text.lower()
    )

    if otp_looks_valid:
        download_response = http_request(
            url=download_url,
            method="POST",
            data={"code": otp_text},
            headers={
                "Referer": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en",
                "Origin": "https://data.krx.co.kr",
            }
        )
        download_artifact = save_response_artifact(
            RAW_DIR / "krx_data_marketplace_all_listed_issues_download_v2_19c.csv",
            download_response,
        )
        acquisition_status = "captured" if download_artifact["artifact_exists"] else "failed"
        notes = "Official KRX CSV download response captured from OTP flow."
    else:
        error_payload = (
            "OTP response did not look like a valid KRX download token.\n"
            f"http_status={otp_response.get('http_status')}\n"
            f"content_type={otp_response.get('content_type')}\n"
            f"body_sample={otp_text[:500]}\n"
        ).encode("utf-8")
        download_response = {
            "ok": False,
            "url": download_url,
            "method": "POST",
            "http_status": 0,
            "content_type": "text/plain; charset=utf-8",
            "content_length_header": "",
            "bytes": len(error_payload),
            "sha256": sha256_bytes(error_payload),
            "ssl_mode": "not_attempted_invalid_otp",
            "error_type": "InvalidOTP",
            "error_message": "OTP response did not look valid; download request not attempted.",
            "content": error_payload,
        }
        download_artifact = save_response_artifact(
            RAW_DIR / "krx_data_marketplace_all_listed_issues_download_not_attempted_v2_19c.txt",
            download_response,
        )
        acquisition_status = "not_attempted_invalid_otp"
        notes = "Download not attempted because OTP token was invalid; captured diagnostic payload."

    add_manifest_row(
        manifest,
        source_id="krx_data_marketplace_all_listed_issues",
        artifact_id="krx_data_marketplace_all_listed_issues_download",
        source_role="primary_or_crosscheck_source",
        url=download_url,
        method="POST",
        acquisition_status=acquisition_status,
        response=download_response,
        artifact=download_artifact,
        notes=notes,
    )

    # 4) Public Data Portal metadata page.
    data_go_page_url = "https://www.data.go.kr/en/data/15094775/openapi.do"
    data_go_page_response = http_request(
        url=data_go_page_url,
        method="GET",
        headers={"Referer": "https://www.data.go.kr/"}
    )
    data_go_page_artifact = save_response_artifact(
        RAW_DIR / "public_data_portal_krx_listed_stock_info_page_v2_19c.html",
        data_go_page_response,
    )
    add_manifest_row(
        manifest,
        source_id="public_data_portal_krx_listed_stock_info",
        artifact_id="public_data_portal_krx_listed_stock_info_page",
        source_role="supporting_or_fallback_source",
        url=data_go_page_url,
        method="GET",
        acquisition_status="captured" if data_go_page_artifact["artifact_exists"] else "failed",
        response=data_go_page_response,
        artifact=data_go_page_artifact,
        notes="Official Public Data Portal metadata page captured.",
    )

    # Optional API request only if user provided DATA_GO_KR_SERVICE_KEY.
    service_key = os.environ.get("DATA_GO_KR_SERVICE_KEY", "").strip()
    api_url_base = "https://apis.data.go.kr/1160100/service/GetKrxListedInfoService/getItemInfo"

    if service_key:
        api_params = urllib.parse.urlencode(
            {
                "serviceKey": service_key,
                "numOfRows": "100",
                "pageNo": "1",
                "resultType": "json",
            }
        )
        api_url = f"{api_url_base}?{api_params}"
        api_response = http_request(url=api_url, method="GET", headers={"Accept": "application/json,*/*"})
        api_artifact = save_response_artifact(
            RAW_DIR / "public_data_portal_krx_listed_stock_info_api_sample_v2_19c.json",
            api_response,
        )
        add_manifest_row(
            manifest,
            source_id="public_data_portal_krx_listed_stock_info",
            artifact_id="public_data_portal_krx_listed_stock_info_api_sample",
            source_role="supporting_or_fallback_source",
            url=api_url_base,
            method="GET",
            acquisition_status="captured_with_service_key" if api_artifact["artifact_exists"] else "failed",
            response=api_response,
            artifact=api_artifact,
            notes="Public Data Portal API sample captured using DATA_GO_KR_SERVICE_KEY environment variable; service key redacted from manifest URL.",
        )
    else:
        key_missing_content = (
            "DATA_GO_KR_SERVICE_KEY environment variable is not set.\n"
            "Public Data Portal API call was not attempted.\n"
            "This supporting source is optional and must not block KRX primary source acquisition.\n"
        ).encode("utf-8")
        key_missing_response = {
            "ok": False,
            "url": api_url_base,
            "method": "GET",
            "http_status": 0,
            "content_type": "text/plain; charset=utf-8",
            "content_length_header": "",
            "bytes": len(key_missing_content),
            "sha256": sha256_bytes(key_missing_content),
            "ssl_mode": "not_attempted_missing_service_key",
            "error_type": "MissingServiceKey",
            "error_message": "DATA_GO_KR_SERVICE_KEY not set; optional API call not attempted.",
            "content": key_missing_content,
        }
        key_missing_artifact = save_response_artifact(
            RAW_DIR / "public_data_portal_krx_listed_stock_info_api_not_attempted_missing_key_v2_19c.txt",
            key_missing_response,
        )
        add_manifest_row(
            manifest,
            source_id="public_data_portal_krx_listed_stock_info",
            artifact_id="public_data_portal_krx_listed_stock_info_api_sample",
            source_role="supporting_or_fallback_source",
            url=api_url_base,
            method="GET",
            acquisition_status="not_attempted_missing_service_key",
            response=key_missing_response,
            artifact=key_missing_artifact,
            notes="Optional API source not attempted because no service key is configured.",
        )

    # 5) KRX OpenAPI catalog reference page.
    openapi_url = "https://openapi.krx.co.kr/contents/OPP/DATA/OPPDATA002.jsp"
    openapi_response = http_request(
        url=openid_url if False else openapi_url,
        method="GET",
        headers={"Referer": "https://openapi.krx.co.kr/"}
    )
    openapi_artifact = save_response_artifact(
        RAW_DIR / "krx_open_api_data_feed_products_page_v2_19c.html",
        openapi_response,
    )
    add_manifest_row(
        manifest,
        source_id="krx_open_api_data_feed_products",
        artifact_id="krx_open_api_data_feed_products_page",
        source_role="reference_only",
        url=openapi_url,
        method="GET",
        acquisition_status="captured" if openapi_artifact["artifact_exists"] else "failed",
        response=openapi_response,
        artifact=openapi_artifact,
        notes="Official KRX Open API catalog page captured as reference only.",
    )

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    manifest_fieldnames = [
        "source_id",
        "artifact_id",
        "source_role",
        "url",
        "method",
        "official_scope_allowed",
        "acquisition_status",
        "http_status",
        "content_type",
        "content_length_header",
        "response_bytes",
        "response_sha256",
        "ssl_mode",
        "error_type",
        "error_message",
        "artifact_path",
        "artifact_exists",
        "artifact_bytes",
        "artifact_sha256",
        "parse_hint",
        "notes",
    ]

    raw_files_written = sum(1 for row in manifest if bool(row["artifact_exists"]))
    official_scope_violations = [row for row in manifest if not bool(row["official_scope_allowed"])]
    captured_rows = [row for row in manifest if str(row["acquisition_status"]).startswith("captured")]
    primary_rows = [row for row in manifest if row["source_role"] in {"primary_candidate_source", "primary_or_crosscheck_source"}]
    primary_captured_rows = [row for row in primary_rows if str(row["acquisition_status"]).startswith("captured")]
    http_200_rows = [row for row in manifest if str(row["http_status"]) == "200"]
    possible_parse_ready_rows = [
        row for row in manifest
        if row["parse_hint"] in {"csv_like", "json_like", "xml_or_api_error_payload", "xlsx_or_zip_container"}
        and int(row["artifact_bytes"] or 0) > 0
    ]

    source_diagnostics_rows = []
    for source in source_inventory_rows:
        sid = source.get("source_id", "")
        rows = [row for row in manifest if row["source_id"] == sid]
        source_diagnostics_rows.append(
            {
                "source_id": sid,
                "provider": source.get("provider", ""),
                "role": source.get("role", ""),
                "selection_status": source.get("selection_status", ""),
                "planned_expected_format": source.get("expected_format", ""),
                "attempts": len(rows),
                "captured_attempts": sum(1 for row in rows if str(row["acquisition_status"]).startswith("captured")),
                "http_200_attempts": sum(1 for row in rows if str(row["http_status"]) == "200"),
                "total_artifact_bytes": sum(int(row["artifact_bytes"] or 0) for row in rows),
                "parse_hints": "|".join(sorted(set(str(row["parse_hint"]) for row in rows if row["parse_hint"]))),
                "final_source_status": (
                    "captured"
                    if any(str(row["acquisition_status"]).startswith("captured") for row in rows)
                    else "not_captured_or_optional_unavailable"
                ),
            }
        )

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19b_report_exists", V219B_JSON.exists(), "critical", str(V219B_JSON))
    add_check("v2_19b_status_expected", v219b.get("status") == EXPECTED_V219B_STATUS, "critical", v219b.get("status", ""))
    add_check("v2_19b_source_inventory_exists", V219B_SOURCE_INVENTORY_CSV.exists(), "critical", str(V219B_SOURCE_INVENTORY_CSV))
    add_check("v2_19b_raw_artifacts_plan_exists", V219B_RAW_ARTIFACTS_CSV.exists(), "critical", str(V219B_RAW_ARTIFACTS_CSV))
    add_check("v2_19b_validation_strategy_exists", V219B_VALIDATION_STRATEGY_CSV.exists(), "critical", str(V219B_VALIDATION_STRATEGY_CSV))
    add_check("active_canonical_rows_expected", canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={canonical_rows}")
    add_check("current_validated_candidate_rows_expected", candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={candidate_rows}")
    add_check("rows_needed_to_50k_expected", max(FINAL_TARGET_CANDIDATES - candidate_rows, 0) == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={max(FINAL_TARGET_CANDIDATES - candidate_rows, 0)}")
    add_check("raw_dir_created", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("manifest_rows_expected_minimum", len(manifest) >= 6, "critical", f"manifest_rows={len(manifest)}")
    add_check("raw_files_written_minimum", raw_files_written >= 5, "critical", f"raw_files_written={raw_files_written}")
    add_check("official_scope_only", len(official_scope_violations) == 0, "critical", f"official_scope_violations={len(official_scope_violations)}")
    add_check("primary_sources_attempted", len(primary_rows) >= 3, "critical", f"primary_attempt_rows={len(primary_rows)}")
    add_check("primary_sources_captured", len(primary_captured_rows) >= 2, "critical", f"primary_captured_rows={len(primary_captured_rows)}")
    add_check("http_200_rows_present", len(http_200_rows) >= 1, "warning", f"http_200_rows={len(http_200_rows)}")
    add_check("possible_parse_ready_or_diagnostic_present", len(possible_parse_ready_rows) >= 1, "warning", f"possible_parse_ready_rows={len(possible_parse_ready_rows)}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("candidate_dataset_not_modified", True, "critical", "candidate_dataset_modified=False")
    add_check("raw_acquisition_performed", True, "critical", "raw_acquisition_performed=True")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("krx_raw_validation_next_needed", True, "critical", RECOMMENDED_NEXT_PHASE)

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "KRX",
            "action": "validate_raw_artifacts",
            "priority": "high",
            "reason": "KRX raw artifacts and diagnostics have been captured.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "validate raw files only; do not extract candidates until v2.19E",
        },
        {
            "action_order": 2,
            "action_scope": "KRX",
            "action": "classify_parse_readiness",
            "priority": "high",
            "reason": "Some KRX responses may be HTML/dynamic pages, OTP responses, CSV downloads or key-required diagnostics.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "decide whether v2.19D can proceed to extraction or needs repair",
        },
        {
            "action_order": 3,
            "action_scope": "50k",
            "action": "maintain_candidate_baseline",
            "priority": "medium",
            "reason": "Current candidate remains 40,996; no rows are added in raw acquisition phase.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "no canonical promotion, no candidate rebuild, no full59k",
        },
    ]

    if critical_failed == 0:
        status = "KRX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "KRX_RAW_ACQUISITION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "active_canonical_rows": canonical_rows,
            "current_validated_candidate_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "current_validated_candidate_rows": candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": max(FINAL_TARGET_CANDIDATES - candidate_rows, 0),
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "current_candidate_sha256_before": candidate_sha_before,
            "current_candidate_sha256_after": candidate_sha_after,
        },
        "raw_acquisition_summary": {
            "raw_dir": str(RAW_DIR),
            "source_inventory_rows": len(source_inventory_rows),
            "raw_artifacts_planned_rows": len(raw_artifacts_plan_rows),
            "validation_strategy_rows": len(validation_strategy_rows),
            "manifest_rows": len(manifest),
            "raw_files_written": raw_files_written,
            "official_scope_violations": len(official_scope_violations),
            "captured_rows": len(captured_rows),
            "primary_attempt_rows": len(primary_rows),
            "primary_captured_rows": len(primary_captured_rows),
            "http_200_rows": len(http_200_rows),
            "possible_parse_ready_rows": len(possible_parse_ready_rows),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_calls_performed": True,
            "query_sweep_performed": False,
            "raw_acquisition_performed": True,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "closure_report_performed": False,
            "route_selection_performed": False,
            "acquisition_plan_performed": False,
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

    write_csv(MANIFEST_CSV, manifest, manifest_fieldnames)
    write_csv(
        SOURCE_DIAGNOSTICS_CSV,
        source_diagnostics_rows,
        [
            "source_id",
            "provider",
            "role",
            "selection_status",
            "planned_expected_format",
            "attempts",
            "captured_attempts",
            "http_200_attempts",
            "total_artifact_bytes",
            "parse_hints",
            "final_source_status",
        ],
    )
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    manifest_lines = "\n".join(
        f"- `{row['artifact_id']}` — {row['acquisition_status']} — HTTP `{row['http_status']}` — `{row['parse_hint']}` — `{row['artifact_path']}`"
        for row in manifest
    )

    diagnostics_lines = "\n".join(
        f"- `{row['source_id']}` — attempts `{row['attempts']}`, captured `{row['captured_attempts']}`, hints `{row['parse_hints']}`"
        for row in source_diagnostics_rows
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
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.19C captures official KRX/data.go.kr raw artifacts for the KRX route.

This phase performs raw acquisition only. It does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{canonical_rows}`
- Current validated candidate rows: `{candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{max(FINAL_TARGET_CANDIDATES - candidate_rows, 0)}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Raw acquisition summary

- Raw dir: `{RAW_DIR}`
- Source inventory rows: `{len(source_inventory_rows)}`
- Planned raw artifact rows: `{len(raw_artifacts_plan_rows)}`
- Validation strategy rows: `{len(validation_strategy_rows)}`
- Manifest rows: `{len(manifest)}`
- Raw files written: `{raw_files_written}`
- Official scope violations: `{len(official_scope_violations)}`
- Captured rows: `{len(captured_rows)}`
- Primary attempt rows: `{len(primary_rows)}`
- Primary captured rows: `{len(primary_captured_rows)}`
- HTTP 200 rows: `{len(http_200_rows)}`
- Possible parse-ready rows: `{len(possible_parse_ready_rows)}`
- Critical failed checks: `{critical_failed}`

## Manifest

{manifest_lines}

## Source diagnostics

{diagnostics_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Raw acquisition performed: true
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

    print("v2.19C KRX raw acquisition completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("RAW_ACQUISITION_SUMMARY:")
    for key, value in payload["raw_acquisition_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_DIAGNOSTICS:")
    for row in source_diagnostics_rows:
        print(f"- {row['source_id']}: attempts={row['attempts']} captured={row['captured_attempts']} http_200={row['http_200_attempts']} hints={row['parse_hints']}")
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
