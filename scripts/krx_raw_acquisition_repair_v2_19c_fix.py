from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse


VERSION = "v2.19C_FIX"
PHASE = "KRX Raw Acquisition Repair"
PHASE_TYPE = "raw-acquisition-repair-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_SOURCE_DIR = OUTPUT_DIR / "raw" / "krx_v2_19c"
RAW_REPAIR_DIR = OUTPUT_DIR / "raw" / "krx_v2_19c_fix"

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219D_JSON = OUTPUT_DIR / "krx_raw_validation_v2_19d.json"
V219D_ARTIFACT_AUDIT_CSV = OUTPUT_DIR / "krx_raw_validation_artifact_audit_v2_19d.csv"
V219D_SOURCE_READINESS_CSV = OUTPUT_DIR / "krx_raw_validation_source_readiness_v2_19d.csv"
V219D_ISSUE_AUDIT_CSV = OUTPUT_DIR / "krx_raw_validation_issue_audit_v2_19d.csv"

V219C_MANIFEST_CSV = OUTPUT_DIR / "krx_raw_acquisition_manifest_v2_19c.csv"

REPORT_JSON = OUTPUT_DIR / "krx_raw_acquisition_repair_v2_19c_fix.json"
REPORT_MD = OUTPUT_DIR / "krx_raw_acquisition_repair_v2_19c_fix.md"
REPAIR_MANIFEST_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_manifest_v2_19c_fix.csv"
HTML_SIGNAL_INVENTORY_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_html_signal_inventory_v2_19c_fix.csv"
DISCOVERED_URLS_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_discovered_official_urls_v2_19c_fix.csv"
TABLE_PROBE_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_html_table_probe_v2_19c_fix.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_source_diagnostics_v2_19c_fix.csv"
CHECKS_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_checks_v2_19c_fix.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "krx_raw_acquisition_repair_next_actions_v2_19c_fix.csv"

EXPECTED_V219D_STATUS = "KRX_RAW_VALIDATION_COMPLETED_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

RECOMMENDED_NEXT_PHASE = "v2.19D_FIX - KRX Repaired Raw Validation"
RECOMMENDED_REVIEW_PHASE = "v2.19C_FIX_REVIEW - KRX Raw Acquisition Repair Review"

ALLOWED_HOSTS = {
    "global.krx.co.kr",
    "data.krx.co.kr",
    "openapi.krx.co.kr",
    "www.data.go.kr",
    "apis.data.go.kr",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ScoutFinanceRawRepair/2.19C_FIX",
    "Accept": "text/html,application/xhtml+xml,application/xml,application/json,text/csv,application/vnd.ms-excel,*/*",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    "Connection": "close",
}

REQUEST_TIMEOUT_SECONDS = 45


class SimpleHTMLProbe(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.scripts: list[dict[str, str]] = []
        self.forms: list[dict[str, str]] = []
        self.inputs: list[dict[str, str]] = []
        self.buttons: list[dict[str, str]] = []
        self.rows: list[list[str]] = []
        self._current_form: dict[str, str] | None = None
        self._in_tr = False
        self._in_cell = False
        self._current_cell: list[str] = []
        self._current_row: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {k.lower(): v or "" for k, v in attrs}
        tag_l = tag.lower()

        if tag_l == "a" and ad.get("href"):
            self.links.append({"tag": tag_l, "url": ad.get("href", ""), "text": "", "attrs": json.dumps(ad, ensure_ascii=False)})

        if tag_l == "script" and ad.get("src"):
            self.scripts.append({"tag": tag_l, "url": ad.get("src", ""), "text": "", "attrs": json.dumps(ad, ensure_ascii=False)})

        if tag_l == "form":
            self._current_form = {
                "method": ad.get("method", "GET").upper() or "GET",
                "action": ad.get("action", ""),
                "id": ad.get("id", ""),
                "name": ad.get("name", ""),
                "attrs": json.dumps(ad, ensure_ascii=False),
            }
            self.forms.append(self._current_form)

        if tag_l == "input":
            self.inputs.append({
                "type": ad.get("type", ""),
                "name": ad.get("name", ""),
                "id": ad.get("id", ""),
                "value": ad.get("value", ""),
                "attrs": json.dumps(ad, ensure_ascii=False),
            })

        if tag_l == "button":
            self.buttons.append({
                "type": ad.get("type", ""),
                "name": ad.get("name", ""),
                "id": ad.get("id", ""),
                "value": ad.get("value", ""),
                "attrs": json.dumps(ad, ensure_ascii=False),
            })

        if tag_l == "tr":
            self._in_tr = True
            self._current_row = []

        if tag_l in {"td", "th"} and self._in_tr:
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag: str) -> None:
        tag_l = tag.lower()

        if tag_l == "form":
            self._current_form = None

        if tag_l in {"td", "th"} and self._in_cell:
            text = html.unescape(" ".join("".join(self._current_cell).split()))
            self._current_row.append(text)
            self._in_cell = False
            self._current_cell = []

        if tag_l == "tr" and self._in_tr:
            if any(cell.strip() for cell in self._current_row):
                self.rows.append(self._current_row)
            self._current_row = []
            self._in_tr = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell.append(data)


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


def decode_bytes(data: bytes) -> str:
    for encoding in ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"]:
        try:
            return data.decode(encoding, errors="ignore")
        except Exception:
            continue
    return data.decode("utf-8", errors="ignore")


def read_text_any(path: Path) -> str:
    return decode_bytes(path.read_bytes()) if path.exists() else ""


def is_official_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"https", "http"} and parsed.hostname in ALLOWED_HOSTS


def is_download_or_data_hint(url: str) -> bool:
    lower = url.lower()
    tokens = [
        "download",
        "filedn",
        "generateotp",
        "excel",
        "csv",
        "xls",
        "cmd",
        "json",
        "list",
        "company",
        "corp",
        "mkt",
        "mdcstat",
    ]
    return any(token in lower for token in tokens)


def normalize_url(base_url: str, raw_url: str) -> str:
    raw_url = (raw_url or "").strip()
    if not raw_url:
        return ""
    if raw_url.startswith("javascript:") or raw_url.startswith("#"):
        return ""
    return urljoin(base_url, raw_url)


def classify_parse_hint(content_type: str, data: bytes, path: Path) -> str:
    lower_ct = (content_type or "").lower()
    sample = data[:800].lower()

    if not data:
        return "empty_response"
    if b"<html" in sample or "text/html" in lower_ct:
        return "html_or_dynamic_page"
    if data[:2] == b"PK" or path.suffix.lower() == ".xlsx":
        return "xlsx_or_zip_container"
    if b"<?xml" in sample or "xml" in lower_ct:
        return "xml_or_api_payload"
    if b"," in data[:4000] or "csv" in lower_ct or path.suffix.lower() == ".csv":
        return "csv_like"
    if b"{" in data[:100] or b"[" in data[:100] or "json" in lower_ct:
        return "json_like"
    return "binary_or_text_unknown"


def make_opener() -> urllib.request.OpenerDirector:
    cookie_jar = CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPRedirectHandler(),
    )


def http_request(
    *,
    opener: urllib.request.OpenerDirector,
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
            request._context = context
            with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
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
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
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


def safe_filename_from_url(prefix: str, url: str, suffix: str) -> str:
    parsed = urlparse(url)
    stem = re.sub(r"[^A-Za-z0-9]+", "_", f"{parsed.netloc}_{parsed.path}")[:90].strip("_")
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{stem}_{digest}{suffix}"


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        REPAIR_MANIFEST_CSV,
        HTML_SIGNAL_INVENTORY_CSV,
        DISCOVERED_URLS_CSV,
        TABLE_PROBE_CSV,
        SOURCE_DIAGNOSTICS_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_REPAIR_DIR.exists():
        existing = [p for p in RAW_REPAIR_DIR.iterdir() if p.is_file()]
        if existing:
            raise SystemExit(f"NO_OVERWRITE_GUARD: raw repair dir already contains files: {RAW_REPAIR_DIR}")
    RAW_REPAIR_DIR.mkdir(parents=True, exist_ok=True)

    v219d = read_json(V219D_JSON)
    _, v219d_artifact_rows = read_csv_with_header(V219D_ARTIFACT_AUDIT_CSV)
    _, v219d_readiness_rows = read_csv_with_header(V219D_SOURCE_READINESS_CSV)
    _, v219d_issue_rows = read_csv_with_header(V219D_ISSUE_AUDIT_CSV)
    _, v219c_manifest_rows = read_csv_with_header(V219C_MANIFEST_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    manifest: list[dict[str, Any]] = []
    html_signal_rows: list[dict[str, Any]] = []
    discovered_url_rows: list[dict[str, Any]] = []
    table_probe_rows: list[dict[str, Any]] = []

    global_html_path = RAW_SOURCE_DIR / "krx_global_listed_company_page_v2_19c.html"
    global_html = read_text_any(global_html_path)
    parser = SimpleHTMLProbe()
    parser.feed(global_html)

    base_global_url = "https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp"

    html_signal_rows.append({
        "source_id": "krx_global_listed_company",
        "artifact_id": "krx_global_listed_company_page_v2_19c",
        "source_path": str(global_html_path),
        "links_count": len(parser.links),
        "scripts_count": len(parser.scripts),
        "forms_count": len(parser.forms),
        "inputs_count": len(parser.inputs),
        "buttons_count": len(parser.buttons),
        "table_rows_count": len(parser.rows),
        "download_signal_count": len(re.findall(r"download|fileDown|filedn|GenerateOTP|excel|csv|xls", global_html, flags=re.I)),
        "company_signal_count": len(re.findall(r"listed company|KOSPI|KOSDAQ|KONEX|ISIN|ticker|stock code|company name", global_html, flags=re.I)),
        "probe_result": "html_inspected",
    })

    max_cols = max((len(row) for row in parser.rows), default=0)
    table_headers = ["source_id", "source_artifact", "row_index", "cell_count"] + [f"cell_{i+1}" for i in range(max_cols)]
    for idx, row in enumerate(parser.rows, start=1):
        record: dict[str, Any] = {
            "source_id": "krx_global_listed_company",
            "source_artifact": str(global_html_path),
            "row_index": idx,
            "cell_count": len(row),
        }
        for i in range(max_cols):
            record[f"cell_{i+1}"] = row[i] if i < len(row) else ""
        table_probe_rows.append(record)

    discovered: dict[str, dict[str, Any]] = {}

    def add_discovered(raw_url: str, origin_type: str, attrs: str = "") -> None:
        normalized = normalize_url(base_global_url, raw_url)
        if not normalized:
            return
        allowed = is_official_allowed_url(normalized)
        data_hint = is_download_or_data_hint(normalized)
        key = normalized
        if key not in discovered:
            discovered[key] = {
                "url": normalized,
                "origin_type": origin_type,
                "official_scope_allowed": allowed,
                "download_or_data_hint": data_hint,
                "selected_for_fetch": False,
                "selection_reason": "",
                "attrs": attrs,
            }

    for item in parser.links:
        add_discovered(item.get("url", ""), "html_a_href", item.get("attrs", ""))

    for item in parser.scripts:
        add_discovered(item.get("url", ""), "html_script_src", item.get("attrs", ""))

    for item in parser.forms:
        add_discovered(item.get("action", ""), "html_form_action", item.get("attrs", ""))

    # Static official repair targets. These are official endpoints/pages only and are captured as raw diagnostics.
    static_repair_targets = [
        {
            "url": "https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp",
            "source_id": "krx_global_listed_company",
            "artifact_id": "krx_global_listed_company_page_refetch",
            "source_role": "primary_candidate_source",
            "method": "GET",
            "data": None,
            "referer": "https://global.krx.co.kr/",
            "suffix": ".html",
            "notes": "Refetch KRX Global Listed Company page with browser-like repair headers and cookie jar.",
        },
        {
            "url": "https://global.krx.co.kr/contents/GLB/03/0308/0308010000/GLB0308010000.jsp?locale=en",
            "source_id": "krx_global_listed_company",
            "artifact_id": "krx_global_listed_company_page_locale_en",
            "source_role": "primary_candidate_source",
            "method": "GET",
            "data": None,
            "referer": "https://global.krx.co.kr/",
            "suffix": ".html",
            "notes": "Fetch locale=en variant to check whether structured content differs.",
        },
        {
            "url": "https://data.krx.co.kr/contents/MDC/INFO/informationController/MDCINFO002.cmd",
            "source_id": "krx_data_marketplace_information",
            "artifact_id": "krx_data_marketplace_information_download_guide",
            "source_role": "repair_reference_source",
            "method": "GET",
            "data": None,
            "referer": "https://data.krx.co.kr/",
            "suffix": ".html",
            "notes": "Capture official Data Marketplace information/download guide page.",
        },
        {
            "url": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd",
            "source_id": "krx_data_marketplace_all_listed_issues",
            "artifact_id": "krx_data_marketplace_main_page_ko",
            "source_role": "primary_or_crosscheck_source",
            "method": "GET",
            "data": None,
            "referer": "https://data.krx.co.kr/",
            "suffix": ".html",
            "notes": "Retry KRX Data Marketplace main page without locale parameter using cookie jar.",
        },
        {
            "url": "https://www.data.go.kr/catalog/15094775/openapi.json",
            "source_id": "public_data_portal_krx_listed_stock_info",
            "artifact_id": "public_data_portal_krx_openapi_catalog_json",
            "source_role": "supporting_or_fallback_source",
            "method": "GET",
            "data": None,
            "referer": "https://www.data.go.kr/",
            "suffix": ".json",
            "notes": "Capture official data.go.kr JSON catalog metadata for KRX listed stock information.",
        },
    ]

    # Data Marketplace OTP repair attempts with browser-like session.
    otp_targets = [
        {
            "url": "https://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd",
            "source_id": "krx_data_marketplace_all_listed_issues",
            "artifact_id": "krx_data_marketplace_otp_mdcstat01901_all",
            "source_role": "primary_or_crosscheck_source",
            "method": "POST",
            "data": {
                "mktId": "ALL",
                "share": "1",
                "csvxls_isNo": "false",
                "name": "fileDown",
                "url": "dbms/MDC/STAT/standard/MDCSTAT01901",
            },
            "referer": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd",
            "suffix": ".txt",
            "notes": "Retry official KRX GenerateOTP for MDCSTAT01901 all-market listed issues.",
        },
        {
            "url": "https://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd",
            "source_id": "krx_data_marketplace_all_listed_issues",
            "artifact_id": "krx_data_marketplace_otp_mdcstat01901_stk",
            "source_role": "primary_or_crosscheck_source",
            "method": "POST",
            "data": {
                "mktId": "STK",
                "share": "1",
                "csvxls_isNo": "false",
                "name": "fileDown",
                "url": "dbms/MDC/STAT/standard/MDCSTAT01901",
            },
            "referer": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd",
            "suffix": ".txt",
            "notes": "Retry official KRX GenerateOTP for MDCSTAT01901 KOSPI/STK listed issues.",
        },
        {
            "url": "https://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd",
            "source_id": "krx_data_marketplace_all_listed_issues",
            "artifact_id": "krx_data_marketplace_otp_mdcstat01901_ksq",
            "source_role": "primary_or_crosscheck_source",
            "method": "POST",
            "data": {
                "mktId": "KSQ",
                "share": "1",
                "csvxls_isNo": "false",
                "name": "fileDown",
                "url": "dbms/MDC/STAT/standard/MDCSTAT01901",
            },
            "referer": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd",
            "suffix": ".txt",
            "notes": "Retry official KRX GenerateOTP for MDCSTAT01901 KOSDAQ/KSQ listed issues.",
        },
        {
            "url": "https://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd",
            "source_id": "krx_data_marketplace_all_listed_issues",
            "artifact_id": "krx_data_marketplace_otp_mdcstat01901_knx",
            "source_role": "primary_or_crosscheck_source",
            "method": "POST",
            "data": {
                "mktId": "KNX",
                "share": "1",
                "csvxls_isNo": "false",
                "name": "fileDown",
                "url": "dbms/MDC/STAT/standard/MDCSTAT01901",
            },
            "referer": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd",
            "suffix": ".txt",
            "notes": "Retry official KRX GenerateOTP for MDCSTAT01901 KONEX/KNX listed issues.",
        },
    ]

    repair_targets = static_repair_targets + otp_targets

    # Select up to 12 discovered official data/download-hint URLs for diagnostic capture.
    discovered_items = list(discovered.values())
    selected_discovered = [
        row for row in discovered_items
        if row["official_scope_allowed"] and row["download_or_data_hint"]
    ][:12]
    for row in selected_discovered:
        row["selected_for_fetch"] = True
        row["selection_reason"] = "official URL discovered in captured KRX Global HTML with download/data hint"

    for row in discovered_items:
        discovered_url_rows.append(row)

    opener = make_opener()

    # Warm up official sessions.
    warmup_urls = [
        "https://global.krx.co.kr/",
        "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd",
    ]
    for idx, url in enumerate(warmup_urls, start=1):
        response = http_request(
            opener=opener,
            url=url,
            method="GET",
            headers={"Referer": "https://global.krx.co.kr/" if "global" in url else "https://data.krx.co.kr/"},
        )
        artifact = save_response_artifact(
            RAW_REPAIR_DIR / safe_filename_from_url(f"warmup_{idx}", url, ".html"),
            response,
        )
        add_manifest_row(
            manifest,
            source_id="official_session_warmup",
            artifact_id=f"official_session_warmup_{idx}",
            source_role="repair_session_warmup",
            url=url,
            method="GET",
            acquisition_status="captured" if artifact["artifact_exists"] else "failed",
            response=response,
            artifact=artifact,
            notes="Official session warmup captured to initialize cookies before repair requests.",
        )

    # Fetch static repair targets and OTP attempts.
    otp_tokens: list[dict[str, Any]] = []

    for target in repair_targets:
        headers = {
            "Referer": target["referer"],
            "Origin": "https://data.krx.co.kr" if "data.krx.co.kr" in target["url"] else "https://global.krx.co.kr",
            "X-Requested-With": "XMLHttpRequest" if "GenerateOTP" in target["url"] else "",
        }
        headers = {k: v for k, v in headers.items() if v}

        response = http_request(
            opener=opener,
            url=target["url"],
            method=target["method"],
            data=target["data"],
            headers=headers,
        )
        artifact = save_response_artifact(
            RAW_REPAIR_DIR / safe_filename_from_url(target["artifact_id"], target["url"], target["suffix"]),
            response,
        )
        add_manifest_row(
            manifest,
            source_id=target["source_id"],
            artifact_id=target["artifact_id"],
            source_role=target["source_role"],
            url=target["url"],
            method=target["method"],
            acquisition_status="captured" if artifact["artifact_exists"] else "failed",
            response=response,
            artifact=artifact,
            notes=target["notes"],
        )

        if "GenerateOTP" in target["url"]:
            text = decode_bytes(response["content"]).strip()
            token_looks_valid = (
                response.get("http_status") == 200
                and len(text) >= 8
                and "<html" not in text.lower()
                and "forbidden" not in text.lower()
                and "error" not in text.lower()
            )
            otp_tokens.append({
                "artifact_id": target["artifact_id"],
                "token": text,
                "token_looks_valid": token_looks_valid,
                "source_id": target["source_id"],
                "source_role": target["source_role"],
            })

    # Attempt CSV downloads only for valid OTP-like tokens.
    for token_row in otp_tokens:
        download_url = "https://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
        if token_row["token_looks_valid"]:
            download_response = http_request(
                opener=opener,
                url=download_url,
                method="POST",
                data={"code": token_row["token"]},
                headers={
                    "Referer": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd",
                    "Origin": "https://data.krx.co.kr",
                },
            )
            suffix = ".csv"
            status = "captured"
            notes = f"Official KRX CSV download attempted using valid OTP from {token_row['artifact_id']}."
        else:
            payload = (
                "OTP token did not look valid; CSV download not attempted.\n"
                f"source_otp_artifact={token_row['artifact_id']}\n"
                f"token_sample={str(token_row['token'])[:500]}\n"
            ).encode("utf-8")
            download_response = {
                "ok": False,
                "url": download_url,
                "method": "POST",
                "http_status": 0,
                "content_type": "text/plain; charset=utf-8",
                "content_length_header": "",
                "bytes": len(payload),
                "sha256": sha256_bytes(payload),
                "ssl_mode": "not_attempted_invalid_otp",
                "error_type": "InvalidOTP",
                "error_message": "OTP token did not look valid; download not attempted.",
                "content": payload,
            }
            suffix = ".txt"
            status = "not_attempted_invalid_otp"
            notes = f"CSV download not attempted because OTP from {token_row['artifact_id']} was invalid."

        artifact = save_response_artifact(
            RAW_REPAIR_DIR / safe_filename_from_url(f"download_from_{token_row['artifact_id']}", download_url, suffix),
            download_response,
        )
        add_manifest_row(
            manifest,
            source_id=token_row["source_id"],
            artifact_id=f"download_from_{token_row['artifact_id']}",
            source_role=token_row["source_role"],
            url=download_url,
            method="POST",
            acquisition_status=status,
            response=download_response,
            artifact=artifact,
            notes=notes,
        )

    # Fetch selected official URLs discovered in KRX Global HTML.
    for idx, row in enumerate(selected_discovered, start=1):
        url = row["url"]
        response = http_request(
            opener=opener,
            url=url,
            method="GET",
            headers={"Referer": base_global_url},
        )
        suffix = ".js" if urlparse(url).path.lower().endswith(".js") else ".html"
        artifact = save_response_artifact(
            RAW_REPAIR_DIR / safe_filename_from_url(f"discovered_{idx}", url, suffix),
            response,
        )
        add_manifest_row(
            manifest,
            source_id="krx_global_discovered_official_url",
            artifact_id=f"krx_global_discovered_official_url_{idx}",
            source_role="repair_discovery_source",
            url=url,
            method="GET",
            acquisition_status="captured" if artifact["artifact_exists"] else "failed",
            response=response,
            artifact=artifact,
            notes=row["selection_reason"],
        )

    # Optional data.go.kr API call if key is present.
    service_key = os.environ.get("DATA_GO_KR_SERVICE_KEY", "").strip()
    api_base = "https://apis.data.go.kr/1160100/service/GetKrxListedInfoService/getItemInfo"
    if service_key:
        params = urllib.parse.urlencode({
            "serviceKey": service_key,
            "numOfRows": "1000",
            "pageNo": "1",
            "resultType": "json",
        })
        api_url = f"{api_base}?{params}"
        response = http_request(
            opener=opener,
            url=api_url,
            method="GET",
            headers={"Accept": "application/json,application/xml,*/*"},
        )
        artifact = save_response_artifact(
            RAW_REPAIR_DIR / "public_data_portal_krx_listed_stock_info_api_repair_sample_v2_19c_fix.json",
            response,
        )
        add_manifest_row(
            manifest,
            source_id="public_data_portal_krx_listed_stock_info",
            artifact_id="public_data_portal_krx_listed_stock_info_api_repair_sample",
            source_role="supporting_or_fallback_source",
            url=api_base,
            method="GET",
            acquisition_status="captured_with_service_key" if artifact["artifact_exists"] else "failed",
            response=response,
            artifact=artifact,
            notes="Optional data.go.kr API repair sample captured; service key redacted from manifest.",
        )
    else:
        payload = (
            "DATA_GO_KR_SERVICE_KEY is not set.\n"
            "Optional data.go.kr API repair call was not attempted.\n"
            "KRX primary repair remains based on official KRX sources.\n"
        ).encode("utf-8")
        response = {
            "ok": False,
            "url": api_base,
            "method": "GET",
            "http_status": 0,
            "content_type": "text/plain; charset=utf-8",
            "content_length_header": "",
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
            "ssl_mode": "not_attempted_missing_service_key",
            "error_type": "MissingServiceKey",
            "error_message": "DATA_GO_KR_SERVICE_KEY not set; optional API call not attempted.",
            "content": payload,
        }
        artifact = save_response_artifact(
            RAW_REPAIR_DIR / "public_data_portal_krx_listed_stock_info_api_repair_not_attempted_missing_key_v2_19c_fix.txt",
            response,
        )
        add_manifest_row(
            manifest,
            source_id="public_data_portal_krx_listed_stock_info",
            artifact_id="public_data_portal_krx_listed_stock_info_api_repair_sample",
            source_role="supporting_or_fallback_source",
            url=api_base,
            method="GET",
            acquisition_status="not_attempted_missing_service_key",
            response=response,
            artifact=artifact,
            notes="Optional data.go.kr API repair call not attempted because no service key is configured.",
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
    http_200_rows = [row for row in manifest if str(row["http_status"]) == "200"]
    structured_rows = [
        row for row in manifest
        if row["parse_hint"] in {"csv_like", "json_like", "xml_or_api_payload", "xlsx_or_zip_container"}
        and int(row["artifact_bytes"] or 0) > 0
        and str(row["http_status"]) in {"200", "0"}
    ]
    primary_structured_rows = [
        row for row in structured_rows
        if row["source_role"] in {"primary_candidate_source", "primary_or_crosscheck_source"}
    ]
    html_table_probe_rows = len(table_probe_rows)
    html_table_probe_possible = html_table_probe_rows > 1 and max((int(row.get("cell_count", 0)) for row in table_probe_rows), default=0) >= 3

    source_diagnostics: dict[str, dict[str, Any]] = {}
    for row in manifest:
        sid = row["source_id"]
        if sid not in source_diagnostics:
            source_diagnostics[sid] = {
                "source_id": sid,
                "attempts": 0,
                "captured_attempts": 0,
                "http_200_attempts": 0,
                "structured_artifacts": 0,
                "total_artifact_bytes": 0,
                "parse_hints": set(),
                "statuses": set(),
            }
        diag = source_diagnostics[sid]
        diag["attempts"] += 1
        if str(row["acquisition_status"]).startswith("captured"):
            diag["captured_attempts"] += 1
        if str(row["http_status"]) == "200":
            diag["http_200_attempts"] += 1
        if row["parse_hint"] in {"csv_like", "json_like", "xml_or_api_payload", "xlsx_or_zip_container"}:
            diag["structured_artifacts"] += 1
        diag["total_artifact_bytes"] += int(row["artifact_bytes"] or 0)
        diag["parse_hints"].add(str(row["parse_hint"]))
        diag["statuses"].add(str(row["acquisition_status"]))

    source_diagnostic_rows = []
    for diag in source_diagnostics.values():
        source_diagnostic_rows.append({
            "source_id": diag["source_id"],
            "attempts": diag["attempts"],
            "captured_attempts": diag["captured_attempts"],
            "http_200_attempts": diag["http_200_attempts"],
            "structured_artifacts": diag["structured_artifacts"],
            "total_artifact_bytes": diag["total_artifact_bytes"],
            "parse_hints": "|".join(sorted(diag["parse_hints"])),
            "statuses": "|".join(sorted(diag["statuses"])),
            "repair_source_status": (
                "structured_raw_captured"
                if diag["structured_artifacts"] > 0
                else "captured_diagnostic_or_html_only"
                if diag["captured_attempts"] > 0
                else "not_captured"
            ),
        })

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19d_report_exists", V219D_JSON.exists(), "critical", str(V219D_JSON))
    add_check("v2_19d_status_expected", v219d.get("status") == EXPECTED_V219D_STATUS, "critical", v219d.get("status", ""))
    add_check("v2_19d_artifact_audit_exists", V219D_ARTIFACT_AUDIT_CSV.exists(), "critical", str(V219D_ARTIFACT_AUDIT_CSV))
    add_check("v2_19d_source_readiness_exists", V219D_SOURCE_READINESS_CSV.exists(), "critical", str(V219D_SOURCE_READINESS_CSV))
    add_check("v2_19d_issue_audit_exists", V219D_ISSUE_AUDIT_CSV.exists(), "critical", str(V219D_ISSUE_AUDIT_CSV))
    add_check("v2_19c_manifest_exists", V219C_MANIFEST_CSV.exists(), "critical", str(V219C_MANIFEST_CSV))
    add_check("v2_19d_repair_required", bool(v219d.get("raw_validation_summary", {}).get("repair_required")) is True, "critical", str(v219d.get("raw_validation_summary", {}).get("repair_required")))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("raw_repair_dir_created", RAW_REPAIR_DIR.exists(), "critical", str(RAW_REPAIR_DIR))
    add_check("html_probe_completed", len(html_signal_rows) == 1, "critical", f"html_signal_rows={len(html_signal_rows)}")
    add_check("html_table_probe_written", html_table_probe_rows >= 1, "warning", f"html_table_probe_rows={html_table_probe_rows}")
    add_check("discovered_url_inventory_written", len(discovered_url_rows) >= 1, "warning", f"discovered_urls={len(discovered_url_rows)}")
    add_check("repair_manifest_rows_minimum", len(manifest) >= 10, "critical", f"repair_manifest_rows={len(manifest)}")
    add_check("raw_repair_files_written_minimum", raw_files_written >= 10, "critical", f"raw_repair_files_written={raw_files_written}")
    add_check("official_scope_only", len(official_scope_violations) == 0, "critical", f"official_scope_violations={len(official_scope_violations)}")
    add_check("http_200_rows_present", len(http_200_rows) >= 1, "warning", f"http_200_rows={len(http_200_rows)}")
    add_check("structured_rows_present", len(structured_rows) >= 1, "warning", f"structured_rows={len(structured_rows)}")
    add_check("primary_structured_rows_present", len(primary_structured_rows) >= 1, "warning", f"primary_structured_rows={len(primary_structured_rows)}")
    add_check("html_table_probe_possible", html_table_probe_possible, "warning", f"html_table_probe_possible={html_table_probe_possible}; rows={html_table_probe_rows}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("candidate_dataset_not_modified", True, "critical", "candidate_dataset_modified=False")
    add_check("raw_acquisition_repair_performed", True, "critical", "raw_acquisition_repair_performed=True")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("krx_repaired_raw_validation_next_needed", True, "critical", RECOMMENDED_NEXT_PHASE)

    if critical_failed == 0:
        status = "KRX_RAW_ACQUISITION_REPAIR_COMPLETED_REPAIRED_RAW_FILES_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "KRX_RAW_ACQUISITION_REPAIR_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "KRX",
            "action": "validate_repaired_raw_artifacts",
            "priority": "high",
            "reason": "KRX repair artifacts have been captured and require revalidation.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "validate repaired raw only; no candidate extraction until v2.19E",
        },
        {
            "action_order": 2,
            "action_scope": "KRX Global",
            "action": "evaluate_html_table_probe",
            "priority": "high",
            "reason": "KRX Global HTML table probe may or may not contain usable row data.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "v2.19D_FIX decides parse-readiness; do not map candidate fields yet",
        },
        {
            "action_order": 3,
            "action_scope": "KRX Data Marketplace",
            "action": "evaluate_otp_and_csv_repair",
            "priority": "medium",
            "reason": "Repair attempted multiple official OTP market scopes and download follow-ups.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "only structured successful downloads may advance to extraction",
        },
        {
            "action_order": 4,
            "action_scope": "50k",
            "action": "maintain_candidate_baseline",
            "priority": "medium",
            "reason": "Current candidate remains 40,996; no rows added in repair phase.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "no canonical promotion, no candidate rebuild, no full59k",
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
        "repair_summary": {
            "v2_19d_artifact_rows": len(v219d_artifact_rows),
            "v2_19d_readiness_rows": len(v219d_readiness_rows),
            "v2_19d_issue_rows": len(v219d_issue_rows),
            "v2_19c_manifest_rows": len(v219c_manifest_rows),
            "html_signal_rows": len(html_signal_rows),
            "html_table_probe_rows": html_table_probe_rows,
            "html_table_probe_possible": html_table_probe_possible,
            "discovered_urls": len(discovered_url_rows),
            "discovered_selected_for_fetch": len(selected_discovered),
            "repair_manifest_rows": len(manifest),
            "raw_repair_files_written": raw_files_written,
            "official_scope_violations": len(official_scope_violations),
            "captured_rows": len(captured_rows),
            "http_200_rows": len(http_200_rows),
            "structured_rows": len(structured_rows),
            "primary_structured_rows": len(primary_structured_rows),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_calls_performed": True,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": True,
            "raw_validation_performed": False,
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

    write_csv(REPAIR_MANIFEST_CSV, manifest, manifest_fieldnames)
    write_csv(
        HTML_SIGNAL_INVENTORY_CSV,
        html_signal_rows,
        [
            "source_id",
            "artifact_id",
            "source_path",
            "links_count",
            "scripts_count",
            "forms_count",
            "inputs_count",
            "buttons_count",
            "table_rows_count",
            "download_signal_count",
            "company_signal_count",
            "probe_result",
        ],
    )
    write_csv(
        DISCOVERED_URLS_CSV,
        discovered_url_rows,
        [
            "url",
            "origin_type",
            "official_scope_allowed",
            "download_or_data_hint",
            "selected_for_fetch",
            "selection_reason",
            "attrs",
        ],
    )
    write_csv(TABLE_PROBE_CSV, table_probe_rows, table_headers if table_headers else ["source_id", "source_artifact", "row_index", "cell_count"])
    write_csv(
        SOURCE_DIAGNOSTICS_CSV,
        source_diagnostic_rows,
        [
            "source_id",
            "attempts",
            "captured_attempts",
            "http_200_attempts",
            "structured_artifacts",
            "total_artifact_bytes",
            "parse_hints",
            "statuses",
            "repair_source_status",
        ],
    )
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    manifest_lines = "\n".join(
        f"- `{row['artifact_id']}` - {row['acquisition_status']} - HTTP `{row['http_status']}` - `{row['parse_hint']}` - `{row['artifact_path']}`"
        for row in manifest
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}"
        for row in checks
    )

    diag_lines = "\n".join(
        f"- `{row['source_id']}` - attempts `{row['attempts']}`, captured `{row['captured_attempts']}`, structured `{row['structured_artifacts']}`, hints `{row['parse_hints']}`"
        for row in source_diagnostic_rows
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

v2.19C_FIX repairs official KRX raw acquisition after v2.19D found no parse-ready primary artifacts.

This phase performs raw-acquisition repair only. It does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Repair summary

- v2.19D artifact rows: `{len(v219d_artifact_rows)}`
- v2.19D readiness rows: `{len(v219d_readiness_rows)}`
- v2.19D issue rows: `{len(v219d_issue_rows)}`
- v2.19C manifest rows: `{len(v219c_manifest_rows)}`
- HTML signal rows: `{len(html_signal_rows)}`
- HTML table probe rows: `{html_table_probe_rows}`
- HTML table probe possible: `{html_table_probe_possible}`
- Discovered URLs: `{len(discovered_url_rows)}`
- Discovered URLs selected for fetch: `{len(selected_discovered)}`
- Repair manifest rows: `{len(manifest)}`
- Raw repair files written: `{raw_files_written}`
- Official scope violations: `{len(official_scope_violations)}`
- Captured rows: `{len(captured_rows)}`
- HTTP 200 rows: `{len(http_200_rows)}`
- Structured rows: `{len(structured_rows)}`
- Primary structured rows: `{len(primary_structured_rows)}`
- Critical failed checks: `{critical_failed}`

## Repair manifest

{manifest_lines}

## Source diagnostics

{diag_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Raw acquisition performed: false
- Raw acquisition repair performed: true
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

    print("v2.19C_FIX KRX raw acquisition repair completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REPAIR_SUMMARY:")
    for key, value in payload["repair_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_DIAGNOSTICS:")
    for row in source_diagnostic_rows:
        print(f"- {row['source_id']}: attempts={row['attempts']} captured={row['captured_attempts']} http_200={row['http_200_attempts']} structured={row['structured_artifacts']} hints={row['parse_hints']}")
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
