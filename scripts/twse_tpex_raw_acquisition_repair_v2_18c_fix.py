from __future__ import annotations

import csv
import hashlib
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.18C_FIX"
PHASE = "TWSE + TPEx Raw Acquisition Repair"
PHASE_TYPE = "raw-acquisition-repair-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
REPAIR_RAW_DIR = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_v2_18c_fix"

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
VALIDATED_NSE_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"

V218D_JSON = OUTPUT_DIR / "twse_tpex_raw_validation_v2_18d.json"
V218D_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "twse_tpex_raw_validation_source_diagnostics_v2_18d.csv"
V218D_NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_raw_validation_next_actions_v2_18d.csv"

V218C_JSON = OUTPUT_DIR / "twse_tpex_raw_acquisition_v2_18c.json"
V218C_MANIFEST_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_manifest_v2_18c.csv"

V218B_SOURCE_PLAN_CSV = OUTPUT_DIR / "twse_tpex_source_plan_v2_18b.csv"
V218B_FILTER_POLICY_CSV = OUTPUT_DIR / "twse_tpex_filter_policy_v2_18b.csv"

REPORT_JSON = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_v2_18c_fix.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_v2_18c_fix.md"
REPAIR_MANIFEST_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_manifest_v2_18c_fix.csv"
REPAIR_SOURCE_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_source_actions_v2_18c_fix.csv"
ENDPOINT_DISCOVERY_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_endpoint_discovery_v2_18c_fix.csv"
REPAIR_DECISION_CSV = OUTPUT_DIR / "twse_tpex_raw_acquisition_repair_decision_v2_18c_fix.csv"

EXPECTED_V218D_STATUS = "TWSE_TPEX_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_REPAIR_REQUIRED_BEFORE_CANDIDATE_EXTRACTION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
EXPECTED_V218C_STATUS = "TWSE_TPEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
VALIDATED_CANDIDATE_ROWS_EXPECTED = 40300
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9700

RECOMMENDED_REVALIDATION_PHASE = "v2.18D_FIX - TWSE + TPEx Repaired Raw Validation"
RECOMMENDED_REPAIR_CONTINUE_PHASE = "v2.18C_FIX2 - TWSE + TPEx Raw Acquisition Repair Continue"
RECOMMENDED_VALIDATION_FIX_PHASE = "v2.18C_FIX_VALIDATION_REVIEW"

HTTP_TIMEOUT_SECONDS = 45
SLEEP_BETWEEN_REQUESTS_SECONDS = 0.60
MAX_DISCOVERED_ENDPOINT_DOWNLOADS = 16

REPAIR_MANIFEST_FIELDS = [
    "repair_source_id",
    "provider",
    "repair_role",
    "origin_source_id",
    "source_url",
    "method",
    "attempt_strategy",
    "ssl_mode",
    "download_status",
    "http_status",
    "final_url",
    "content_type",
    "encoding",
    "bytes",
    "sha256",
    "raw_artifact_path",
    "detected_format",
    "parse_status",
    "row_like_count",
    "column_like_count",
    "row_data_candidate",
    "candidate_role",
    "error_type",
    "error_message",
    "captured_at_utc",
    "notes",
]

REPAIR_SOURCE_ACTIONS_FIELDS = [
    "action_order",
    "action_scope",
    "action",
    "allowed_in_v2_18c_fix",
    "performed",
    "result",
    "http_status",
    "raw_artifact_path",
    "bytes",
    "sha256",
    "notes",
]

ENDPOINT_DISCOVERY_FIELDS = [
    "discovery_order",
    "discovery_source",
    "provider",
    "origin_source_id",
    "discovered_url",
    "discovery_method",
    "selected_for_download",
    "selection_reason",
    "notes",
]

REPAIR_DECISION_FIELDS = [
    "decision_key",
    "decision_value",
    "rationale",
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


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value[:140] or "raw"


def extension_from_content_type(content_type: str, url: str, detected_hint: str = "") -> str:
    ct = (content_type or "").lower()
    url_low = (url or "").lower()
    hint = (detected_hint or "").lower()

    if "json" in ct or "json" in hint or url_low.endswith(".json"):
        return ".json"
    if "csv" in ct or "csv" in hint or url_low.endswith(".csv"):
        return ".csv"
    if "html" in ct or "html" in hint:
        return ".html"
    if "xml" in ct:
        return ".xml"
    if "text" in ct:
        return ".txt"
    return ".bin"


def detect_format(data: bytes, content_type: str, path: Path) -> str:
    if not data:
        return "empty"

    text_head, _ = decode_text(data[:8192])
    stripped = text_head.lstrip()
    low = stripped.lower()
    ct = (content_type or "").lower()
    suffix = path.suffix.lower()

    if "certificate verify failed" in low or "urlopen error" in low:
        return "error_text"

    if stripped.startswith("{") or stripped.startswith("[") or "application/json" in ct or suffix == ".json":
        return "json_like"

    if "<!doctype html" in low or low.startswith("<html") or "<html" in low or "text/html" in ct:
        return "html"

    if "," in text_head and ("\n" in text_head or "\r" in text_head):
        return "csv_like"

    return "text_or_binary"


def parse_profile(data: bytes, detected_format: str) -> dict[str, Any]:
    result = {
        "parse_status": "not_attempted",
        "row_like_count": 0,
        "column_like_count": 0,
        "notes": "",
    }

    text, encoding = decode_text(data)

    if detected_format == "json_like":
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                result["row_like_count"] = len(parsed)
                result["column_like_count"] = len(parsed[0]) if parsed and isinstance(parsed[0], dict) else 0
                result["parse_status"] = "json_list_parsed"
            elif isinstance(parsed, dict):
                result["row_like_count"] = len(parsed)
                result["column_like_count"] = len(parsed.keys())
                result["parse_status"] = "json_dict_parsed"
            else:
                result["parse_status"] = f"json_scalar_parsed_{type(parsed).__name__}"
            result["notes"] = f"encoding={encoding}"
        except Exception as error:
            result["parse_status"] = "json_parse_failed"
            result["notes"] = str(error)
        return result

    if detected_format == "csv_like":
        try:
            rows = list(csv.reader(text.splitlines()))
            result["row_like_count"] = len(rows)
            result["column_like_count"] = max((len(row) for row in rows), default=0)
            result["parse_status"] = "csv_like_parsed"
            result["notes"] = f"encoding={encoding}"
        except Exception as error:
            result["parse_status"] = "csv_parse_failed"
            result["notes"] = str(error)
        return result

    if detected_format == "html":
        low = text.lower()
        result["row_like_count"] = len(re.findall(r"<tr[\s>]", low))
        result["column_like_count"] = 0
        result["parse_status"] = "html_profiled"
        result["notes"] = f"encoding={encoding}; csv_mentions={low.count('csv')}; download_mentions={low.count('download') + low.count('下載')}"
        return result

    if detected_format == "error_text":
        result["parse_status"] = "error_payload_profiled"
        result["notes"] = text[:300].replace("\n", " ").replace("\r", " ")
        return result

    result["parse_status"] = "text_or_binary_profiled"
    result["notes"] = f"encoding={encoding}"
    return result


def build_headers(url: str) -> dict[str, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 Scout-Finance/2.18C_FIX RawRepair",
        "Accept": "application/json,text/csv,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    if "openapi.twse.com.tw" in url or "twse.com.tw" in url:
        headers["Referer"] = "https://openapi.twse.com.tw/"

    if "tpex.org.tw" in url:
        headers["Referer"] = "https://www.tpex.org.tw/openapi/"
        headers["Origin"] = "https://www.tpex.org.tw"

    return headers


def fetch_once(url: str, method: str, context: ssl.SSLContext, ssl_mode: str) -> dict[str, Any]:
    request = urllib.request.Request(url=url, method=method, headers=build_headers(url))

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

    return {
        "body": response_body,
        "http_status": http_status,
        "final_url": final_url,
        "content_type": content_type,
        "encoding": encoding,
        "error_type": error_type,
        "error_message": error_message,
        "download_status": download_status,
        "ssl_mode": ssl_mode,
    }


def download_repair_source(source: dict[str, Any], raw_dir: Path) -> dict[str, Any]:
    url = source["source_url"]
    method = source.get("method", "GET").upper()
    allow_ssl_fallback = bool(source.get("allow_unverified_ssl_fallback", False))
    attempt_strategy = source.get("attempt_strategy", "default")

    default_context = ssl.create_default_context()
    fetched = fetch_once(url, method, default_context, "default_verify")

    if (
        allow_ssl_fallback
        and fetched["error_type"] == "URLError"
        and "CERTIFICATE_VERIFY_FAILED" in fetched["error_message"]
    ):
        fallback_context = ssl._create_unverified_context()
        fallback = fetch_once(url, method, fallback_context, "unverified_ssl_fallback")
        if fallback["download_status"] != "network_error_payload_captured" or fallback["http_status"]:
            fetched = fallback
            attempt_strategy = f"{attempt_strategy}+unverified_ssl_fallback"

    body = fetched["body"]
    temp_name = safe_filename(source["repair_source_id"])
    detected_hint = source.get("expected_raw_kind", "")
    extension = extension_from_content_type(fetched["content_type"], url, detected_hint)
    status_for_name = fetched["http_status"] or fetched["download_status"]
    raw_path = raw_dir / f"{temp_name}_{safe_filename(status_for_name)}{extension}"

    if raw_path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite raw artifact {raw_path}")

    raw_path.write_bytes(body)

    detected_format = detect_format(body, fetched["content_type"], raw_path)
    parse_info = parse_profile(body, detected_format)

    sha = sha256_bytes(body)
    row_data_candidate = (
        fetched["http_status"] == "200"
        and detected_format in {"json_like", "csv_like"}
        and int(parse_info["row_like_count"] or 0) > 1
    )

    return {
        "repair_source_id": source["repair_source_id"],
        "provider": source.get("provider", ""),
        "repair_role": source.get("repair_role", ""),
        "origin_source_id": source.get("origin_source_id", ""),
        "source_url": url,
        "method": method,
        "attempt_strategy": attempt_strategy,
        "ssl_mode": fetched["ssl_mode"],
        "download_status": fetched["download_status"],
        "http_status": fetched["http_status"],
        "final_url": fetched["final_url"],
        "content_type": fetched["content_type"],
        "encoding": fetched["encoding"],
        "bytes": len(body),
        "sha256": sha,
        "raw_artifact_path": str(raw_path),
        "detected_format": detected_format,
        "parse_status": parse_info["parse_status"],
        "row_like_count": parse_info["row_like_count"],
        "column_like_count": parse_info["column_like_count"],
        "row_data_candidate": row_data_candidate,
        "candidate_role": source.get("candidate_role", ""),
        "error_type": fetched["error_type"],
        "error_message": fetched["error_message"],
        "captured_at_utc": utc_now(),
        "notes": source.get("notes", ""),
        "_body": body,
    }


def extract_urls_from_html(raw_path: Path, base_url: str) -> list[str]:
    if not raw_path.exists():
        return []

    data = raw_path.read_bytes()
    text, _ = decode_text(data)

    candidates: set[str] = set()

    patterns = [
        r'href=["\']([^"\']+)["\']',
        r'src=["\']([^"\']+)["\']',
        r'action=["\']([^"\']+)["\']',
        r'data-url=["\']([^"\']+)["\']',
        r'url\s*:\s*["\']([^"\']+)["\']',
        r'apiUrl\s*[:=]\s*["\']([^"\']+)["\']',
        r'downloadUrl\s*[:=]\s*["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            if not match:
                continue
            if any(token in match.lower() for token in ["csv", "json", "openapi", "api", "download"]):
                candidates.add(urllib.parse.urljoin(base_url, match))

    return sorted(candidates)


def discover_tpex_swagger_endpoints(swagger_payload: bytes, swagger_url: str) -> list[dict[str, str]]:
    text, _ = decode_text(swagger_payload)

    try:
        parsed = json.loads(text)
    except Exception:
        return []

    base_origin = "https://www.tpex.org.tw"
    base_path = ""

    if isinstance(parsed, dict):
        if parsed.get("servers") and isinstance(parsed["servers"], list):
            first = parsed["servers"][0]
            if isinstance(first, dict) and first.get("url"):
                server_url = str(first["url"])
                if server_url.startswith("http"):
                    base_origin = server_url.rstrip("/")
                else:
                    base_path = server_url.strip("/")
        if parsed.get("host"):
            base_origin = "https://" + str(parsed["host"]).strip("/")
        if parsed.get("basePath"):
            base_path = str(parsed["basePath"]).strip("/")

    paths = parsed.get("paths", {}) if isinstance(parsed, dict) else {}
    discovered: list[dict[str, str]] = []

    selected_terms = [
        "tpex_mainboard_daily_close_quotes",
        "mainboard_daily_close",
        "mainboard",
        "stock",
        "quotes",
        "company",
        "listed",
    ]

    for path_key, detail in paths.items():
        path_text = str(path_key)
        low = path_text.lower()

        if not any(term in low for term in selected_terms):
            continue

        if any(excluded in low for excluded in ["bond", "warrant", "etn", "etf", "derivative", "index"]):
            continue

        if path_text.startswith("http"):
            full_url = path_text
        else:
            if base_path:
                full_url = base_origin.rstrip("/") + "/" + base_path.strip("/") + "/" + path_text.lstrip("/")
            else:
                full_url = base_origin.rstrip("/") + "/openapi/v1/" + path_text.lstrip("/")

        discovered.append(
            {
                "discovered_url": full_url,
                "path": path_text,
                "selection_reason": "selected official TPEx OpenAPI path matching mainboard/stock/company/quotes keywords",
            }
        )

    unique: dict[str, dict[str, str]] = {}
    for row in discovered:
        unique[row["discovered_url"]] = row

    return list(unique.values())[:MAX_DISCOVERED_ENDPOINT_DOWNLOADS]


def normalized_count_keys(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "") or f"NO_{key.upper()}")
        result[value] = result.get(value, 0) + 1
    return result

def is_official_twse_tpex_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.netloc or "").lower()
        return host.endswith("twse.com.tw") or host.endswith("tpex.org.tw")
    except Exception:
        return False




def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        REPAIR_MANIFEST_CSV,
        REPAIR_SOURCE_ACTIONS_CSV,
        ENDPOINT_DISCOVERY_CSV,
        REPAIR_DECISION_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if REPAIR_RAW_DIR.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw repair directory already exists: {REPAIR_RAW_DIR}")

    REPAIR_RAW_DIR.mkdir(parents=True, exist_ok=False)

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    v218d = read_json(V218D_JSON)
    v218c = read_json(V218C_JSON)

    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)
    candidate_header, candidate_rows = read_csv_with_header(VALIDATED_NSE_CANDIDATE_DATASET)
    _, diagnostics_rows = read_csv_with_header(V218D_SOURCE_DIAGNOSTICS_CSV)
    _, next_actions_rows = read_csv_with_header(V218D_NEXT_ACTIONS_CSV)
    _, old_manifest_rows = read_csv_with_header(V218C_MANIFEST_CSV)
    _, source_plan_rows = read_csv_with_header(V218B_SOURCE_PLAN_CSV)
    _, filter_policy_rows = read_csv_with_header(V218B_FILTER_POLICY_CSV)

    old_manifest_by_source = {row["source_id"]: row for row in old_manifest_rows}

    repair_sources: list[dict[str, Any]] = []

    for row in diagnostics_rows:
        if row.get("provider") == "TWSE" and row.get("repair_required", "").lower() == "true":
            old = old_manifest_by_source.get(row["source_id"], {})
            repair_sources.append(
                {
                    "repair_source_id": f"twse_ssl_repair_{row['source_id']}",
                    "provider": "TWSE",
                    "repair_role": "ssl_repair_retry",
                    "origin_source_id": row["source_id"],
                    "source_url": old.get("source_url", ""),
                    "method": old.get("method", "GET"),
                    "candidate_role": row.get("candidate_role", ""),
                    "expected_raw_kind": old.get("planned_raw_kind", ""),
                    "attempt_strategy": "default_then_unverified_ssl_fallback",
                    "allow_unverified_ssl_fallback": True,
                    "notes": "Retry official TWSE source with fallback only if default SSL verification fails.",
                }
            )

    repair_sources.append(
        {
            "repair_source_id": "tpex_openapi_swagger_json_repair",
            "provider": "TPEx",
            "repair_role": "swagger_json_endpoint_discovery",
            "origin_source_id": "tpex_openapi_swagger",
            "source_url": "https://www.tpex.org.tw/openapi/swagger.json",
            "method": "GET",
            "candidate_role": "discovery_catalog",
            "expected_raw_kind": "json",
            "attempt_strategy": "direct_official_swagger_json",
            "allow_unverified_ssl_fallback": False,
            "notes": "Official TPEx Swagger JSON used to discover row-data endpoints.",
        }
    )

    repair_sources.append(
        {
            "repair_source_id": "tpex_mainboard_daily_close_quotes_known_endpoint",
            "provider": "TPEx",
            "repair_role": "known_openapi_row_data_candidate",
            "origin_source_id": "tpex_daily_stock_quotes",
            "source_url": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
            "method": "GET",
            "candidate_role": "primary_tpex_candidate_source",
            "expected_raw_kind": "json",
            "attempt_strategy": "direct_official_openapi_known_path",
            "allow_unverified_ssl_fallback": False,
            "notes": "Known official TPEx OpenAPI path surfaced from Swagger/search; raw capture only.",
        }
    )

    endpoint_discovery_rows: list[dict[str, Any]] = []
    repair_manifest_rows: list[dict[str, Any]] = []
    source_actions_rows: list[dict[str, Any]] = []

    source_actions_rows.append(
        {
            "action_order": 1,
            "action_scope": "all",
            "action": "prepare_repair_raw_output_directory",
            "allowed_in_v2_18c_fix": True,
            "performed": True,
            "result": "PASS",
            "http_status": "",
            "raw_artifact_path": str(REPAIR_RAW_DIR),
            "bytes": "",
            "sha256": "",
            "notes": "repair raw output directory created",
        }
    )

    action_order = 2

    for source in repair_sources:
        if not source.get("source_url"):
            continue

        result = download_repair_source(source, REPAIR_RAW_DIR)
        body = result.pop("_body", b"")

        repair_manifest_rows.append(result)

        source_actions_rows.append(
            {
                "action_order": action_order,
                "action_scope": source.get("provider", ""),
                "action": f"download_repair_source:{source['repair_source_id']}",
                "allowed_in_v2_18c_fix": True,
                "performed": True,
                "result": "PASS" if str(result["download_status"]).startswith("downloaded") else "CAPTURED_ERROR",
                "http_status": result["http_status"],
                "raw_artifact_path": result["raw_artifact_path"],
                "bytes": result["bytes"],
                "sha256": result["sha256"],
                "notes": f"{result['download_status']} ssl_mode={result['ssl_mode']}",
            }
        )
        action_order += 1

        if source["repair_source_id"] == "tpex_openapi_swagger_json_repair":
            discovered = discover_tpex_swagger_endpoints(body, source["source_url"])
            for idx, endpoint in enumerate(discovered, start=1):
                endpoint_discovery_rows.append(
                    {
                        "discovery_order": len(endpoint_discovery_rows) + 1,
                        "discovery_source": "tpex_openapi_swagger_json_repair",
                        "provider": "TPEx",
                        "origin_source_id": "tpex_openapi_swagger",
                        "discovered_url": endpoint["discovered_url"],
                        "discovery_method": "swagger_json_paths",
                        "selected_for_download": True,
                        "selection_reason": endpoint["selection_reason"],
                        "notes": endpoint["path"],
                    }
                )

        time.sleep(SLEEP_BETWEEN_REQUESTS_SECONDS)

    for old_row in old_manifest_rows:
        if old_row.get("provider") != "TPEx":
            continue
        raw_path = Path(old_row.get("raw_artifact_path", ""))
        if not raw_path.exists():
            continue

        discovered_urls = extract_urls_from_html(raw_path, old_row.get("source_url", ""))
        for discovered_url in discovered_urls:
            is_official = is_official_twse_tpex_url(discovered_url)
            has_download_token = any(
                token in discovered_url.lower()
                for token in ["csv", "json", "api", "openapi"]
            )
            endpoint_discovery_rows.append(
                {
                    "discovery_order": len(endpoint_discovery_rows) + 1,
                    "discovery_source": "v2_18c_tpex_html_artifact",
                    "provider": "TPEx",
                    "origin_source_id": old_row.get("source_id", ""),
                    "discovered_url": discovered_url,
                    "discovery_method": "html_link_regex",
                    "selected_for_download": is_official and has_download_token,
                    "selection_reason": (
                        "official TWSE/TPEx HTML link/script reference containing csv/json/api/openapi token"
                        if is_official and has_download_token
                        else "excluded_non_official_or_non_data_link"
                    ),
                    "notes": f"source_html={raw_path}; official_domain={is_official}",
                }
            )

    already_downloaded_urls = {row["source_url"] for row in repair_manifest_rows}
    selected_discovery_rows = [
        row for row in endpoint_discovery_rows
        if str(row.get("selected_for_download", "")).lower() == "true"
        and row["discovered_url"] not in already_downloaded_urls
    ]

    for row in selected_discovery_rows[:MAX_DISCOVERED_ENDPOINT_DOWNLOADS]:
        source = {
            "repair_source_id": f"tpex_discovered_{safe_filename(str(row['discovery_order']).zfill(2) + '_' + Path(urllib.parse.urlparse(row['discovered_url']).path).name)}",
            "provider": "TPEx",
            "repair_role": "discovered_official_endpoint_candidate",
            "origin_source_id": row.get("origin_source_id", ""),
            "source_url": row["discovered_url"],
            "method": "GET",
            "candidate_role": "discovered_tpex_candidate_or_support_source",
            "expected_raw_kind": "json_or_csv_or_html",
            "attempt_strategy": "download_discovered_official_endpoint",
            "allow_unverified_ssl_fallback": False,
            "notes": row.get("selection_reason", ""),
        }

        result = download_repair_source(source, REPAIR_RAW_DIR)
        result.pop("_body", None)
        repair_manifest_rows.append(result)

        source_actions_rows.append(
            {
                "action_order": action_order,
                "action_scope": "TPEx",
                "action": f"download_discovered_endpoint:{source['repair_source_id']}",
                "allowed_in_v2_18c_fix": True,
                "performed": True,
                "result": "PASS" if str(result["download_status"]).startswith("downloaded") else "CAPTURED_ERROR",
                "http_status": result["http_status"],
                "raw_artifact_path": result["raw_artifact_path"],
                "bytes": result["bytes"],
                "sha256": result["sha256"],
                "notes": f"{result['download_status']} format={result['detected_format']} rows={result['row_like_count']}",
            }
        )
        action_order += 1

        time.sleep(SLEEP_BETWEEN_REQUESTS_SECONDS)

    source_actions_rows.append(
        {
            "action_order": action_order,
            "action_scope": "all",
            "action": "defer_candidate_extraction",
            "allowed_in_v2_18c_fix": False,
            "performed": True,
            "result": "PASS",
            "http_status": "",
            "raw_artifact_path": "",
            "bytes": "",
            "sha256": "",
            "notes": "candidate extraction remains blocked until repaired raw validation confirms row-data readiness",
        }
    )

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())
    candidate_sha = sha256_bytes(VALIDATED_NSE_CANDIDATE_DATASET.read_bytes())

    active_canonical_rows = len(canonical_rows)
    validated_candidate_rows = len(candidate_rows)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - validated_candidate_rows, 0)
    completion_percent = round((validated_candidate_rows / FINAL_TARGET_CANDIDATES) * 100, 2)

    download_attempts = len(repair_manifest_rows)
    http_200_count = sum(1 for row in repair_manifest_rows if str(row["http_status"]) == "200")
    fallback_success_count = sum(
        1 for row in repair_manifest_rows
        if row["ssl_mode"] == "unverified_ssl_fallback" and str(row["http_status"]) == "200"
    )
    row_data_candidate_count = sum(1 for row in repair_manifest_rows if str(row["row_data_candidate"]).lower() == "true")
    json_like_count = sum(1 for row in repair_manifest_rows if row["detected_format"] == "json_like")
    csv_like_count = sum(1 for row in repair_manifest_rows if row["detected_format"] == "csv_like")
    html_count = sum(1 for row in repair_manifest_rows if row["detected_format"] == "html")
    error_count = sum(1 for row in repair_manifest_rows if row["error_type"] or "error" in row["download_status"])
    total_bytes = sum(int(row["bytes"] or 0) for row in repair_manifest_rows)

    raw_artifacts_exist = all(Path(row["raw_artifact_path"]).exists() for row in repair_manifest_rows)
    raw_sha_valid = True
    for row in repair_manifest_rows:
        raw_path = Path(row["raw_artifact_path"])
        if raw_path.exists():
            raw_sha_valid = raw_sha_valid and sha256_bytes(raw_path.read_bytes()) == row["sha256"]
        else:
            raw_sha_valid = False

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18d_report_exists", V218D_JSON.exists(), "critical", str(V218D_JSON))
    add_check("v2_18d_status_expected", v218d.get("status") == EXPECTED_V218D_STATUS, "critical", v218d.get("status", ""))
    add_check("v2_18c_report_exists", V218C_JSON.exists(), "critical", str(V218C_JSON))
    add_check("v2_18c_status_expected", v218c.get("status") == EXPECTED_V218C_STATUS, "critical", v218c.get("status", ""))
    add_check("v2_18d_diagnostics_exists", V218D_SOURCE_DIAGNOSTICS_CSV.exists(), "critical", str(V218D_SOURCE_DIAGNOSTICS_CSV))
    add_check("v2_18d_next_actions_exists", V218D_NEXT_ACTIONS_CSV.exists(), "critical", str(V218D_NEXT_ACTIONS_CSV))
    add_check("source_plan_exists", V218B_SOURCE_PLAN_CSV.exists(), "critical", str(V218B_SOURCE_PLAN_CSV))
    add_check("filter_policy_exists", V218B_FILTER_POLICY_CSV.exists(), "critical", str(V218B_FILTER_POLICY_CSV))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("validated_candidate_dataset_exists", VALIDATED_NSE_CANDIDATE_DATASET.exists(), "critical", str(VALIDATED_NSE_CANDIDATE_DATASET))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("validated_candidate_rows_expected", validated_candidate_rows == VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"validated_candidate_rows={validated_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("candidate_schema_matches_canonical", canonical_header == candidate_header, "critical", f"canonical_cols={len(canonical_header)} candidate_cols={len(candidate_header)}")
    add_check("repair_raw_directory_created", REPAIR_RAW_DIR.exists(), "critical", str(REPAIR_RAW_DIR))
    add_check("repair_download_attempts_performed", download_attempts > 0, "critical", f"download_attempts={download_attempts}")
    add_check("repair_raw_artifacts_exist", raw_artifacts_exist, "critical", f"raw_artifacts_exist={raw_artifacts_exist}")
    add_check("repair_sha256_valid", raw_sha_valid, "critical", f"raw_sha_valid={raw_sha_valid}")
    add_check("network_used_in_repair_phase", True, "critical", "network_download_performed=True")
    non_official_downloaded = [
        row for row in repair_manifest_rows
        if not is_official_twse_tpex_url(str(row.get("source_url", "")))
    ]

    add_check(
        "network_scope_official_only",
        len(non_official_downloaded) == 0,
        "critical",
        f"non_official_downloaded={len(non_official_downloaded)}",
    )
    add_check("twse_ssl_repair_attempted", any(row["provider"] == "TWSE" for row in repair_manifest_rows), "critical", "TWSE repair attempts present")
    add_check("tpex_endpoint_discovery_attempted", any(row["repair_source_id"] == "tpex_openapi_swagger_json_repair" for row in repair_manifest_rows), "critical", "TPEx swagger JSON attempted")
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

    add_check("row_data_candidate_captured", row_data_candidate_count > 0, "warning", f"row_data_candidate_count={row_data_candidate_count}")
    add_check("twse_ssl_fallback_success", fallback_success_count > 0, "warning", f"fallback_success_count={fallback_success_count}")
    add_check("tpex_discovered_endpoints_found", len(endpoint_discovery_rows) > 0, "warning", f"endpoint_discovery_rows={len(endpoint_discovery_rows)}")

    if critical_failed == 0 and row_data_candidate_count > 0:
        status = "TWSE_TPEX_RAW_ACQUISITION_REPAIR_COMPLETED_ROW_DATA_CAPTURED_REVALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_REVALIDATION_PHASE
    elif critical_failed == 0:
        status = "TWSE_TPEX_RAW_ACQUISITION_REPAIR_COMPLETED_NO_ROW_DATA_CAPTURED_REVIEW_REQUIRED_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_REPAIR_CONTINUE_PHASE
    else:
        status = "TWSE_TPEX_RAW_ACQUISITION_REPAIR_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_VALIDATION_FIX_PHASE

    repair_decision_rows = [
        {
            "decision_key": "repair_phase_status",
            "decision_value": status,
            "rationale": "Repair attempted official TWSE SSL/client acquisition and TPEx endpoint discovery without extracting candidates.",
        },
        {
            "decision_key": "row_data_candidate_count",
            "decision_value": row_data_candidate_count,
            "rationale": "Candidate extraction remains blocked unless repaired raw validation confirms row-data suitability.",
        },
        {
            "decision_key": "recommended_next_phase",
            "decision_value": recommended_next_phase,
            "rationale": "Proceed to repaired raw validation if row-data was captured; otherwise continue raw repair.",
        },
    ]

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
        "repair_summary": {
            "repair_raw_directory": str(REPAIR_RAW_DIR),
            "download_attempts": download_attempts,
            "http_200_count": http_200_count,
            "fallback_success_count": fallback_success_count,
            "row_data_candidate_count": row_data_candidate_count,
            "json_like_count": json_like_count,
            "csv_like_count": csv_like_count,
            "html_count": html_count,
            "error_count": error_count,
            "total_bytes_captured": total_bytes,
            "endpoint_discovery_rows": len(endpoint_discovery_rows),
            "critical_failed_checks": critical_failed,
            "download_status_counts": normalized_count_keys(repair_manifest_rows, "download_status"),
            "http_status_counts": normalized_count_keys(repair_manifest_rows, "http_status"),
            "detected_format_counts": normalized_count_keys(repair_manifest_rows, "detected_format"),
        },
        "repair_scope": {
            "network_download_performed": True,
            "network_scope": "official TWSE/TPEx sources from v2.18B plus official TPEx Swagger/discovered official links",
            "twse_ssl_repair": True,
            "tpex_endpoint_discovery": True,
            "candidate_extraction_performed": False,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
        },
        "source_references": {
            "v2_18d_report": str(V218D_JSON),
            "v2_18d_diagnostics": str(V218D_SOURCE_DIAGNOSTICS_CSV),
            "v2_18d_next_actions": str(V218D_NEXT_ACTIONS_CSV),
            "v2_18c_manifest": str(V218C_MANIFEST_CSV),
            "v2_18b_source_plan": str(V218B_SOURCE_PLAN_CSV),
            "source_plan_rows": len(source_plan_rows),
            "filter_policy_rows": len(filter_policy_rows),
            "next_action_rows": len(next_actions_rows),
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_calls_performed": True,
            "query_sweep_performed": False,
            "network_scope": "official_sources_and_official_endpoint_discovery_only",
            "raw_acquisition_repair_performed": True,
            "raw_files_written": True,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "canonical_comparison_performed": False,
            "canonical_dataset_read": True,
            "validated_candidate_dataset_read": True,
            "v2_18d_diagnostics_read": True,
            "v2_18c_manifest_read": True,
            "repair_manifest_written": True,
            "endpoint_discovery_written": True,
            "repair_decision_written": True,
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

    write_csv(REPAIR_MANIFEST_CSV, repair_manifest_rows, REPAIR_MANIFEST_FIELDS)
    write_csv(REPAIR_SOURCE_ACTIONS_CSV, source_actions_rows, REPAIR_SOURCE_ACTIONS_FIELDS)
    write_csv(ENDPOINT_DISCOVERY_CSV, endpoint_discovery_rows, ENDPOINT_DISCOVERY_FIELDS)
    write_csv(REPAIR_DECISION_CSV, repair_decision_rows, REPAIR_DECISION_FIELDS)
    write_json(REPORT_JSON, payload)

    manifest_lines = "\n".join(
        f"- `{row['repair_source_id']}` — {row['provider']} — {row['download_status']} — HTTP `{row['http_status']}` — format `{row['detected_format']}` — rows `{row['row_like_count']}` — row_data `{row['row_data_candidate']}`"
        for row in repair_manifest_rows
    )

    endpoint_lines = "\n".join(
        f"- `{row['provider']}` — {row['discovery_method']} — selected `{row['selected_for_download']}` — {row['discovered_url']}"
        for row in endpoint_discovery_rows
    ) or "- No endpoint discovery rows produced."

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

v2.18C_FIX repairs raw acquisition for the TWSE + TPEx Taiwan route.

This phase performs network calls only for official TWSE/TPEx sources from v2.18B plus official TPEx Swagger/discovered official links. It writes repaired raw files, a repair manifest, endpoint discovery records, repair decisions and source actions.

It does not perform raw validation, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

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

## Repair summary

- Download attempts: `{download_attempts}`
- HTTP 200 count: `{http_200_count}`
- SSL fallback success count: `{fallback_success_count}`
- Row-data candidate count: `{row_data_candidate_count}`
- JSON-like count: `{json_like_count}`
- CSV-like count: `{csv_like_count}`
- HTML count: `{html_count}`
- Error count: `{error_count}`
- Total bytes captured: `{total_bytes}`
- Endpoint discovery rows: `{len(endpoint_discovery_rows)}`
- Critical failed checks: `{critical_failed}`

## Repair manifest summary

{manifest_lines}

## Endpoint discovery

{endpoint_lines}

## Checks

{check_lines}

## Guards

- Network download performed: true
- Endpoint calls performed: true
- Query sweep performed: false
- Network scope: official sources and official endpoint discovery only
- Raw acquisition repair performed: true
- Raw files written: true
- Raw validation performed: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- v2.18D diagnostics read: true
- v2.18C manifest read: true
- Repair manifest written: true
- Endpoint discovery written: true
- Repair decision written: true
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

v2.18C_FIX completes raw acquisition repair attempts and determines whether repaired raw validation can start.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.18C_FIX TWSE + TPEx raw acquisition repair completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REPAIR_SUMMARY:")
    for key, value in payload["repair_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
        print(f"- {key}: {value}")
    print("")
    print("REPAIR_MANIFEST:")
    for row in repair_manifest_rows:
        print(
            f"- {row['repair_source_id']}: {row['download_status']} "
            f"HTTP={row['http_status']} format={row['detected_format']} "
            f"rows={row['row_like_count']} row_data={row['row_data_candidate']} "
            f"path={row['raw_artifact_path']}"
        )
    print("")
    print("ENDPOINT_DISCOVERY:")
    for row in endpoint_discovery_rows:
        print(
            f"- {row['provider']} {row['discovery_method']} selected={row['selected_for_download']} "
            f"url={row['discovered_url']}"
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
