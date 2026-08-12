from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


VERSION = "v2.21C3"
PHASE = "Official Endpoint / Downloadable Listing Discovery"
PHASE_TYPE = "targeted-market-official-endpoint-download-discovery"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
DISCOVERY_RAW_DIR = OUTPUT_DIR / "raw_targeted_market_endpoint_discovery_v2_21c3"

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

V221B_JSON = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_v2_21b.json"
V221C_JSON = OUTPUT_DIR / "targeted_market_candidate_extraction_dedup_dry_run_v2_21c.json"
V221C2_JSON = OUTPUT_DIR / "targeted_market_candidate_false_positive_review_v2_21c2.json"

REPORT_JSON = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_v2_21c3.json"
REPORT_MD = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_v2_21c3.md"
SUMMARY_CSV = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_summary_v2_21c3.csv"
CHECKS_CSV = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_checks_v2_21c3.csv"
ENDPOINT_INVENTORY_CSV = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_endpoint_inventory_v2_21c3.csv"
ENDPOINT_VALIDATION_CSV = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_endpoint_validation_v2_21c3.csv"
MARKET_ENDPOINT_READINESS_CSV = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_market_readiness_v2_21c3.csv"
STRUCTURED_SAMPLE_CSV = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_structured_sample_v2_21c3.csv"
DECISION_REGISTER_CSV = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_decision_register_v2_21c3.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "targeted_market_official_endpoint_discovery_next_actions_v2_21c3.csv"

EXPECTED_V221B_STATUS = "TARGETED_MARKET_ACQUISITION_RAW_VALIDATION_COMPLETED_COLOMBIA_SINGAPORE_RAW_SOURCES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED"
EXPECTED_V221C_STATUS = "TARGETED_MARKET_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_NEW_CANDIDATES_READY_FOR_REBUILD_NO_DATASET_CHANGES_SCORING_DEFERRED"
EXPECTED_V221C2_STATUS = "TARGETED_MARKET_CANDIDATE_FALSE_POSITIVE_REVIEW_COMPLETED_ACCEPTED_CANDIDATES_INVALIDATED_REBUILD_BLOCKED_SOURCE_DISCOVERY_REQUIRED"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_ALL_MARKETS_READY = "TARGETED_MARKET_OFFICIAL_ENDPOINT_DISCOVERY_COMPLETED_STRUCTURED_ENDPOINTS_FOUND_FOR_ALL_MARKETS_EXTRACTION_RETRY_ALLOWED"
STATUS_PARTIAL = "TARGETED_MARKET_OFFICIAL_ENDPOINT_DISCOVERY_COMPLETED_PARTIAL_STRUCTURED_ENDPOINTS_FOUND_REVIEW_REQUIRED"
STATUS_FAILED = "TARGETED_MARKET_OFFICIAL_ENDPOINT_DISCOVERY_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_ALL_READY = "v2.21C4 - Structured Candidate Extraction + Dedup Dry Run"
NEXT_PHASE_PARTIAL = "v2.21C3_REVIEW - Missing Official Structured Endpoint Review"
NEXT_PHASE_REVIEW = "v2.21C3_REVIEW - Endpoint Discovery Issue Resolution"

REQUEST_TIMEOUT_SECONDS = 45
MIN_SUCCESS_BYTES = 100
MAX_DISCOVERED_URLS_PER_MARKET = 40
MAX_STRUCTURED_SAMPLE_ROWS = 40

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 ScoutFinanceEndpointDiscovery/2.21C3",
    "Accept": "application/json,text/csv,application/vnd.ms-excel,application/xhtml+xml,text/html,text/plain,*/*;q=0.7",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

MARKET_DEFAULTS = {
    "COLOMBIA_BVC": {
        "country": "Colombia",
        "provider": "BVC",
        "official_hosts": {"www.bvc.com.co", "bvc.com.co"},
    },
    "SINGAPORE_SGX": {
        "country": "Singapore",
        "provider": "SGX",
        "official_hosts": {"www.sgx.com", "sgx.com", "api.sgx.com"},
    },
}

SEED_ENDPOINTS = [
    {
        "market_id": "COLOMBIA_BVC",
        "source_id": "BVC_LISTADO_EMISORES_MERCADO_LOCAL_PAGE",
        "url": "https://www.bvc.com.co/listado-de-emisores-mercado-local",
        "candidate_type": "official_web_page",
        "priority": "high",
        "reason": "BVC menu path discovered in prior raw HTML for local market issuer list.",
    },
    {
        "market_id": "COLOMBIA_BVC",
        "source_id": "BVC_LISTADO_EMISORES_MERCADO_GLOBAL_PAGE",
        "url": "https://www.bvc.com.co/listado-de-emisores-mercado-global",
        "candidate_type": "official_web_page",
        "priority": "medium",
        "reason": "BVC menu path discovered in prior raw HTML for global Colombian market issuer list.",
    },
    {
        "market_id": "COLOMBIA_BVC",
        "source_id": "BVC_MERCADO_LOCAL_RENTA_VARIABLE_PAGE",
        "url": "https://www.bvc.com.co/mercado-local-en-linea?tab=renta-variable_mercado-local",
        "candidate_type": "official_web_page",
        "priority": "medium",
        "reason": "BVC local equity market online page candidate.",
    },
    {
        "market_id": "COLOMBIA_BVC",
        "source_id": "BVC_ACCIONES_PAGE",
        "url": "https://www.bvc.com.co/acciones",
        "candidate_type": "official_web_page",
        "priority": "medium",
        "reason": "BVC official equities product page candidate.",
    },
    {
        "market_id": "SINGAPORE_SGX",
        "source_id": "SGX_SECURITIES_V1_1_JSON_MINIMAL",
        "url": "https://api.sgx.com/securities/v1.1?excludetypes=bonds&params=nc%2Ccn%2Cs%2Cp%2Cc%2Cchange_vs_pc%2Cchange_vs_pc_percentage%2Ccx%2Cdp%2Cdpc%2Ctrading_time",
        "candidate_type": "official_domain_json_endpoint_candidate",
        "priority": "high",
        "reason": "Candidate JSON endpoint under api.sgx.com used by SGX securities pages; must be validated before use.",
    },
    {
        "market_id": "SINGAPORE_SGX",
        "source_id": "SGX_SECURITIES_V1_1_JSON_EXTENDED",
        "url": "https://api.sgx.com/securities/v1.1?excludetypes=bonds&params=nc%2Cadjusted-vwap%2Cb%2Cbv%2Cp%2Cc%2Cchange_vs_pc%2Cchange_vs_pc_percentage%2Ccx%2Ccn%2Cdp%2Cdpc%2Cdu%2Ced%2Cfn%2Ch%2Ciiv%2Ciopv%2Clt%2Cl%2Co%2Cp_%2Cpv%2Cptd%2Cs%2Csv%2Ctrading_time%2Cv_%2Cv%2Cvl%2Cvwap%2Cvwap-currency",
        "candidate_type": "official_domain_json_endpoint_candidate",
        "priority": "high",
        "reason": "Extended securities JSON endpoint candidate.",
    },
    {
        "market_id": "SINGAPORE_SGX",
        "source_id": "SGX_SECURITIES_PRICES_PAGE",
        "url": "https://www.sgx.com/stock-exchange/securities-prices?code=stocks",
        "candidate_type": "official_web_page",
        "priority": "medium",
        "reason": "Official SGX securities prices page; may reference structured API endpoints.",
    },
    {
        "market_id": "SINGAPORE_SGX",
        "source_id": "SGX_CORPORATE_INFORMATION_PAGE",
        "url": "https://www.sgx.com/securities/corporate-information?pagesize=100",
        "candidate_type": "official_web_page",
        "priority": "medium",
        "reason": "Official SGX corporate information page; may reference structured API endpoints.",
    },
]

STRUCTURED_KEY_HINTS = {
    "symbol", "ticker", "code", "stockcode", "stock_code", "tradingcode", "trading_code",
    "isin", "securitycode", "security_code", "counter", "countername", "counter_name",
    "company", "companyname", "company_name", "issuer", "issuername", "issuer_name",
    "name", "security", "securityname", "security_name", "nc", "cn", "s",
}

CANDIDATE_NAME_KEYS = {
    "name", "company", "companyname", "company_name", "issuer", "issuername", "issuer_name",
    "security", "securityname", "security_name", "countername", "counter_name", "nc", "cn",
}

CANDIDATE_CODE_KEYS = {
    "symbol", "ticker", "code", "stockcode", "stock_code", "tradingcode", "trading_code",
    "isin", "securitycode", "security_code", "counter", "s",
}

DISALLOWED_SAMPLE_TERMS = {
    "gtm", "compatible", "webpack", "browser", "polyfills", "googletagmanager", "buildmanifest",
    "static", "script", "font", "cookie", "privacy", "login",
}


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.tables: list[list[list[str]]] = []
        self.current_table: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self.in_table = True
            self.current_table = []
        elif self.in_table and tag == "tr":
            self.in_row = True
            self.current_row = []
        elif self.in_table and self.in_row and tag in {"td", "th"}:
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.in_table and self.in_row and self.in_cell and tag in {"td", "th"}:
            cell = " ".join(" ".join(self.current_cell).split())
            self.current_row.append(cell)
            self.current_cell = []
            self.in_cell = False
        elif self.in_table and self.in_row and tag == "tr":
            if any(cell.strip() for cell in self.current_row):
                self.current_table.append(self.current_row)
            self.current_row = []
            self.in_row = False
        elif self.in_table and tag == "table":
            if self.current_table:
                self.tables.append(self.current_table)
            self.current_table = []
            self.in_table = False

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell.append(data)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required JSON artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", norm(value).lower())


def safe_source_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
    return cleaned[:120] or "endpoint"


def decode_bytes(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding, errors="replace")
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def flatten_json_objects(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(flatten_json_objects(child))
    elif isinstance(value, list):
        for item in value:
            found.extend(flatten_json_objects(item))
    return found


def flatten_json_lists(value: Any) -> list[list[Any]]:
    found: list[list[Any]] = []
    if isinstance(value, list):
        found.append(value)
        for item in value:
            found.extend(flatten_json_lists(item))
    elif isinstance(value, dict):
        for child in value.values():
            found.extend(flatten_json_lists(child))
    return found


def parse_next_data_json(text: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    pattern = re.compile(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(text):
        raw = html.unescape(match.group(1))
        try:
            data = json.loads(raw)
        except Exception:
            continue
        objects.extend(flatten_json_objects(data))
    return objects


def extract_urls_from_text(text: str, base_url: str, market_id: str) -> list[dict[str, Any]]:
    discovered: list[dict[str, Any]] = []
    seen: set[str] = set()

    patterns = [
        r'https?://[^\s"\'<>\\)]+',
        r'["\'](?P<path>/[^"\']{3,160})["\']',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            if "path" in match.groupdict():
                candidate = match.group("path")
                url = urllib.parse.urljoin(base_url, candidate)
            else:
                url = match.group(0)

            url = url.replace("\\u0026", "&").replace("\\/", "/")
            url = html.unescape(url).strip().rstrip(".,);]}'\"")

            parsed = urllib.parse.urlparse(url)
            host = parsed.netloc.lower()
            if host not in MARKET_DEFAULTS[market_id]["official_hosts"]:
                continue

            lowered = url.lower()
            useful_terms = [
                "emisor", "emisores", "issuer", "issuers", "acciones", "renta-variable",
                "listado", "security", "securities", "corporate-information", "stock-exchange",
                "api", "json", "csv", "xls", "xlsx", "download", "prices",
            ]

            if not any(term in lowered for term in useful_terms):
                continue

            if url in seen:
                continue
            seen.add(url)

            discovered.append({
                "market_id": market_id,
                "source_id": f"DISCOVERED_{safe_source_id(parsed.path or parsed.netloc)}_{len(discovered)+1}",
                "url": url,
                "candidate_type": "discovered_official_url_from_raw",
                "priority": "discovered",
                "reason": "Discovered from previously captured official raw HTML/JSON.",
            })

            if len(discovered) >= MAX_DISCOVERED_URLS_PER_MARKET:
                break

    return discovered


def build_endpoint_inventory(v221b: dict[str, Any]) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for seed in SEED_ENDPOINTS:
        if seed["url"] not in seen_urls:
            inventory.append(seed)
            seen_urls.add(seed["url"])

    # Discover additional official paths from v2.21B raw files.
    for source in v221b.get("source_fetches", []):
        market_id = source.get("market_id", "")
        raw_file = source.get("raw_file", "")
        source_url = source.get("url", "")

        if market_id not in MARKET_DEFAULTS or not raw_file:
            continue

        raw_path = Path(raw_file)
        if not raw_path.exists():
            continue

        text = decode_bytes(raw_path.read_bytes())
        discovered = extract_urls_from_text(text, source_url, market_id)

        for item in discovered:
            if item["url"] not in seen_urls:
                inventory.append(item)
                seen_urls.add(item["url"])

    return inventory


def content_suffix(content_type: str, url: str) -> str:
    lowered = (content_type or "").lower()
    path = urllib.parse.urlparse(url).path.lower()

    if "json" in lowered or path.endswith(".json"):
        return ".json"
    if "csv" in lowered or path.endswith(".csv"):
        return ".csv"
    if "excel" in lowered or "spreadsheet" in lowered or path.endswith((".xls", ".xlsx")):
        return ".xls"
    if "html" in lowered or path.endswith((".html", ".htm")):
        return ".html"
    if "text" in lowered:
        return ".txt"
    return ".raw"


def fetch_endpoint(endpoint: dict[str, Any], index: int) -> dict[str, Any]:
    source_id = endpoint["source_id"]
    url = endpoint["url"]
    market_id = endpoint["market_id"]

    base_name = f"{index:03d}_{safe_source_id(source_id)}"
    headers_path = DISCOVERY_RAW_DIR / f"{base_name}.headers.json"
    error_path = DISCOVERY_RAW_DIR / f"{base_name}.error.raw"

    result: dict[str, Any] = {
        "market_id": market_id,
        "provider": MARKET_DEFAULTS[market_id]["provider"],
        "source_id": source_id,
        "url": url,
        "candidate_type": endpoint["candidate_type"],
        "priority": endpoint["priority"],
        "reason": endpoint["reason"],
        "fetch_attempted": True,
        "fetch_success": False,
        "http_status": "",
        "content_type": "",
        "raw_bytes": 0,
        "raw_sha256": "",
        "raw_file": "",
        "headers_file": "",
        "error_file": "",
        "fetch_error": "",
    }

    request = urllib.request.Request(url, headers=HEADERS)
    context = ssl.create_default_context()

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=context) as response:
            data = response.read()
            status = int(getattr(response, "status", 200))
            headers = dict(response.headers.items())
            content_type = response.headers.get("Content-Type", "")
            suffix = content_suffix(content_type, url)
            raw_path = DISCOVERY_RAW_DIR / f"{base_name}{suffix}"

            if raw_path.exists() or headers_path.exists():
                raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {raw_path} or {headers_path}")

            raw_path.write_bytes(data)
            headers_path.write_text(json.dumps(headers, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

            result.update({
                "fetch_success": 200 <= status < 300 and len(data) >= MIN_SUCCESS_BYTES,
                "http_status": status,
                "content_type": content_type,
                "raw_bytes": len(data),
                "raw_sha256": sha256_bytes(data),
                "raw_file": str(raw_path),
                "headers_file": str(headers_path),
            })

    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        headers = dict(exc.headers.items()) if exc.headers else {}
        if body:
            error_path.write_bytes(body)
        headers_path.write_text(json.dumps(headers, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

        result.update({
            "fetch_success": False,
            "http_status": int(exc.code),
            "content_type": headers.get("Content-Type", ""),
            "raw_bytes": len(body),
            "raw_sha256": sha256_bytes(body) if body else "",
            "headers_file": str(headers_path),
            "error_file": str(error_path) if body else "",
            "fetch_error": f"HTTPError: {exc.code} {exc.reason}",
        })

    except Exception as exc:
        result.update({
            "fetch_success": False,
            "fetch_error": f"{type(exc).__name__}: {exc}",
        })

    return result


def is_candidate_like_dict(obj: dict[str, Any]) -> bool:
    normalized_keys = {norm_key(k) for k in obj.keys()}

    has_name = bool(normalized_keys & {norm_key(k) for k in CANDIDATE_NAME_KEYS})
    has_code = bool(normalized_keys & {norm_key(k) for k in CANDIDATE_CODE_KEYS})

    if has_name and has_code:
        values = " ".join(norm(v).lower() for v in obj.values() if isinstance(v, (str, int, float)))
        if any(term in values for term in DISALLOWED_SAMPLE_TERMS):
            return False
        return True

    # SGX compact rows can have keys such as nc/cn/s.
    compact_score = sum(1 for key in ["nc", "cn", "s"] if key in normalized_keys)
    return compact_score >= 2


def summarize_dict_keys(objects: list[dict[str, Any]]) -> str:
    counter: Counter[str] = Counter()
    for obj in objects[:200]:
        for key in obj.keys():
            counter[str(key)] += 1
    return "|".join(f"{key}:{count}" for key, count in counter.most_common(30))


def validate_raw_endpoint(fetch_row: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_file = fetch_row.get("raw_file", "")
    market_id = fetch_row["market_id"]
    source_id = fetch_row["source_id"]
    url = fetch_row["url"]

    validation: dict[str, Any] = {
        "market_id": market_id,
        "provider": fetch_row["provider"],
        "source_id": source_id,
        "url": url,
        "candidate_type": fetch_row["candidate_type"],
        "fetch_success": fetch_row["fetch_success"],
        "http_status": fetch_row["http_status"],
        "content_type": fetch_row["content_type"],
        "raw_bytes": fetch_row["raw_bytes"],
        "raw_file": raw_file,
        "parse_mode": "",
        "is_json": False,
        "is_csv": False,
        "is_excel_like": False,
        "is_html": False,
        "html_table_count": 0,
        "next_data_object_count": 0,
        "json_object_count": 0,
        "json_list_count": 0,
        "candidate_like_records": 0,
        "structured_endpoint_candidate": False,
        "endpoint_validation_status": "NOT_FETCHED",
        "key_summary": "",
        "review_reason": "",
    }

    samples: list[dict[str, Any]] = []

    if not fetch_row.get("fetch_success") or not raw_file or not Path(raw_file).exists():
        validation["endpoint_validation_status"] = "FETCH_NOT_SUCCESSFUL"
        validation["review_reason"] = fetch_row.get("fetch_error", "fetch failed or raw file missing")
        return validation, samples

    path = Path(raw_file)
    data = path.read_bytes()
    text = decode_bytes(data)
    lowered_content_type = (fetch_row.get("content_type") or "").lower()
    lowered_url = url.lower()

    is_json = "json" in lowered_content_type or lowered_url.endswith(".json") or text.lstrip().startswith(("{", "["))
    is_csv = "csv" in lowered_content_type or lowered_url.endswith(".csv")
    is_excel_like = "excel" in lowered_content_type or "spreadsheet" in lowered_content_type or lowered_url.endswith((".xls", ".xlsx"))
    is_html = "html" in lowered_content_type or "<html" in text.lower()

    validation.update({
        "is_json": is_json,
        "is_csv": is_csv,
        "is_excel_like": is_excel_like,
        "is_html": is_html,
    })

    candidate_like_records = 0
    objects: list[dict[str, Any]] = []

    if is_json:
        validation["parse_mode"] = "json"
        try:
            parsed = json.loads(text)
            objects = flatten_json_objects(parsed)
            lists = flatten_json_lists(parsed)
            candidate_like_objects = [obj for obj in objects if is_candidate_like_dict(obj)]
            candidate_like_records = len(candidate_like_objects)

            validation["json_object_count"] = len(objects)
            validation["json_list_count"] = len(lists)
            validation["key_summary"] = summarize_dict_keys(candidate_like_objects or objects)

            for idx, obj in enumerate(candidate_like_objects[:MAX_STRUCTURED_SAMPLE_ROWS], start=1):
                samples.append({
                    "market_id": market_id,
                    "provider": fetch_row["provider"],
                    "source_id": source_id,
                    "sample_order": idx,
                    "sample_kind": "json_candidate_like_object",
                    "sample_payload": json.dumps(obj, ensure_ascii=False)[:1200],
                })
        except Exception as exc:
            validation["endpoint_validation_status"] = "JSON_PARSE_ERROR"
            validation["review_reason"] = f"{type(exc).__name__}: {exc}"
            return validation, samples

    elif is_csv:
        validation["parse_mode"] = "csv"
        try:
            reader = csv.DictReader(text.splitlines())
            objects = list(reader)
            candidate_like_objects = [obj for obj in objects if is_candidate_like_dict(obj)]
            candidate_like_records = len(candidate_like_objects)
            validation["json_object_count"] = len(objects)
            validation["key_summary"] = summarize_dict_keys(candidate_like_objects or objects)
            for idx, obj in enumerate(candidate_like_objects[:MAX_STRUCTURED_SAMPLE_ROWS], start=1):
                samples.append({
                    "market_id": market_id,
                    "provider": fetch_row["provider"],
                    "source_id": source_id,
                    "sample_order": idx,
                    "sample_kind": "csv_candidate_like_row",
                    "sample_payload": json.dumps(obj, ensure_ascii=False)[:1200],
                })
        except Exception as exc:
            validation["endpoint_validation_status"] = "CSV_PARSE_ERROR"
            validation["review_reason"] = f"{type(exc).__name__}: {exc}"
            return validation, samples

    elif is_html:
        validation["parse_mode"] = "html"
        table_parser = TableParser()
        table_parser.feed(text)
        next_objects = parse_next_data_json(text)

        validation["html_table_count"] = len(table_parser.tables)
        validation["next_data_object_count"] = len(next_objects)

        candidate_like_objects = [obj for obj in next_objects if is_candidate_like_dict(obj)]
        candidate_like_records = len(candidate_like_objects)

        # Table structure count only; extraction from tables is not accepted here unless real table rows exist.
        if not candidate_like_records:
            for table in table_parser.tables:
                if len(table) < 2:
                    continue
                header = [norm_key(cell) for cell in table[0]]
                has_name = any(key in {norm_key(k) for k in CANDIDATE_NAME_KEYS} for key in header)
                has_code = any(key in {norm_key(k) for k in CANDIDATE_CODE_KEYS} for key in header)
                if has_name and has_code:
                    candidate_like_records += max(len(table) - 1, 0)

        validation["key_summary"] = summarize_dict_keys(candidate_like_objects or next_objects)

        for idx, obj in enumerate(candidate_like_objects[:MAX_STRUCTURED_SAMPLE_ROWS], start=1):
            samples.append({
                "market_id": market_id,
                "provider": fetch_row["provider"],
                "source_id": source_id,
                "sample_order": idx,
                "sample_kind": "html_next_data_candidate_like_object",
                "sample_payload": json.dumps(obj, ensure_ascii=False)[:1200],
            })

    elif is_excel_like:
        validation["parse_mode"] = "excel_like_binary"
        candidate_like_records = 0
        validation["review_reason"] = "Excel-like file detected; content parsing deferred to v2.21C4 if selected."

    else:
        validation["parse_mode"] = "unknown"
        validation["review_reason"] = "Unknown content type; not accepted as structured endpoint."

    validation["candidate_like_records"] = candidate_like_records

    if is_excel_like:
        validation["structured_endpoint_candidate"] = True
        validation["endpoint_validation_status"] = "STRUCTURED_DOWNLOAD_CANDIDATE_BINARY_REVIEW_REQUIRED"
    elif candidate_like_records >= 5 and (is_json or is_csv or is_html):
        validation["structured_endpoint_candidate"] = True
        validation["endpoint_validation_status"] = "STRUCTURED_ENDPOINT_CANDIDATE_FOUND"
    elif candidate_like_records > 0:
        validation["structured_endpoint_candidate"] = False
        validation["endpoint_validation_status"] = "WEAK_CANDIDATE_STRUCTURE_REVIEW_REQUIRED"
        validation["review_reason"] = "Candidate-like records found but below minimum confidence threshold."
    else:
        validation["structured_endpoint_candidate"] = False
        validation["endpoint_validation_status"] = "NO_STRUCTURED_CANDIDATE_RECORDS_FOUND"
        if not validation["review_reason"]:
            validation["review_reason"] = "No reliable structured company/security records detected."

    return validation, samples


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        ENDPOINT_INVENTORY_CSV,
        ENDPOINT_VALIDATION_CSV,
        MARKET_ENDPOINT_READINESS_CSV,
        STRUCTURED_SAMPLE_CSV,
        DECISION_REGISTER_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if DISCOVERY_RAW_DIR.exists() and any(DISCOVERY_RAW_DIR.iterdir()):
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw discovery directory exists and is not empty: {DISCOVERY_RAW_DIR}")

    DISCOVERY_RAW_DIR.mkdir(parents=True, exist_ok=True)

    v221b = read_json(V221B_JSON)
    v221c = read_json(V221C_JSON)
    v221c2 = read_json(V221C2_JSON)

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    header = read_csv_header(OPERATIONAL_BASE_DATASET)

    endpoint_inventory = build_endpoint_inventory(v221b)

    fetch_rows: list[dict[str, Any]] = []
    endpoint_validation_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []

    print("")
    print("v2.21C3 endpoint discovery started.")
    print(f"Endpoint candidates: {len(endpoint_inventory)}")

    for idx, endpoint in enumerate(endpoint_inventory, start=1):
        print(f"Fetching {idx}/{len(endpoint_inventory)} {endpoint['market_id']} {endpoint['source_id']}")
        fetch_row = fetch_endpoint(endpoint, idx)
        fetch_rows.append(fetch_row)
        validation_row, samples = validate_raw_endpoint(fetch_row)
        endpoint_validation_rows.append(validation_row)
        sample_rows.extend(samples)

        print(
            f"- status={fetch_row['http_status']} success={fetch_row['fetch_success']} "
            f"bytes={fetch_row['raw_bytes']} validation={validation_row['endpoint_validation_status']} "
            f"candidate_like_records={validation_row['candidate_like_records']}"
        )

    market_readiness_rows: list[dict[str, Any]] = []
    for market_id in sorted(MARKET_DEFAULTS):
        market_validations = [row for row in endpoint_validation_rows if row["market_id"] == market_id]
        structured = [row for row in market_validations if str(row["structured_endpoint_candidate"]).lower() == "true"]
        weak = [row for row in market_validations if row["endpoint_validation_status"] == "WEAK_CANDIDATE_STRUCTURE_REVIEW_REQUIRED"]
        fetched = [row for row in market_validations if str(row["fetch_success"]).lower() == "true"]

        best_candidate_like_records = max([int(row["candidate_like_records"] or 0) for row in market_validations] or [0])

        if structured:
            readiness = "structured_endpoint_ready_for_v2_21c4"
            next_action = "proceed_to_structured_extraction_retry"
        elif weak:
            readiness = "weak_structure_review_required"
            next_action = "manual_review_or_find_better_official_endpoint"
        elif fetched:
            readiness = "official_pages_fetched_but_no_structured_records"
            next_action = "discover_download_or_api_endpoint"
        else:
            readiness = "no_endpoint_access"
            next_action = "review_access_or_manual_official_download"

        market_readiness_rows.append({
            "market_id": market_id,
            "country": MARKET_DEFAULTS[market_id]["country"],
            "provider": MARKET_DEFAULTS[market_id]["provider"],
            "endpoint_candidates_tested": len(market_validations),
            "fetch_success_count": len(fetched),
            "structured_endpoint_count": len(structured),
            "weak_endpoint_count": len(weak),
            "best_candidate_like_records": best_candidate_like_records,
            "market_endpoint_ready": len(structured) > 0,
            "readiness_status": readiness,
            "recommended_action": next_action,
            "best_structured_source_id": structured[0]["source_id"] if structured else "",
            "best_structured_url": structured[0]["url"] if structured else "",
        })

    ready_markets = sum(1 for row in market_readiness_rows if str(row["market_endpoint_ready"]).lower() == "true")
    all_markets_ready = ready_markets == len(MARKET_DEFAULTS)
    any_market_ready = ready_markets > 0

    decision_register_rows = [
        {
            "decision_id": "ENDPOINT_DISCOVERY_001",
            "decision": "Do not use v2.21C regex-only candidates.",
            "accepted": True,
            "reason": "v2.21C2 invalidated all previously accepted candidates.",
            "effect": "v2.21D remains blocked until structured extraction retry succeeds.",
        },
        {
            "decision_id": "ENDPOINT_DISCOVERY_002",
            "decision": "Use only official-domain structured endpoints or downloadable files.",
            "accepted": True,
            "reason": "Targeted expansion must remain official-source based.",
            "effect": "Candidate extraction from arbitrary regex/web text remains disallowed.",
        },
        {
            "decision_id": "ENDPOINT_DISCOVERY_003",
            "decision": "Require structured extraction retry before rebuild.",
            "accepted": True,
            "reason": "Endpoint discovery alone is not candidate extraction.",
            "effect": "Next phase is v2.21C4 if both markets have structured endpoints; otherwise review.",
        },
        {
            "decision_id": "ENDPOINT_DISCOVERY_004",
            "decision": "Keep operational base unchanged.",
            "accepted": True,
            "reason": "v2.21C3 is discovery-only.",
            "effect": "Operational base remains 42,708 rows.",
        },
        {
            "decision_id": "ENDPOINT_DISCOVERY_005",
            "decision": "Keep scoring/OpenAI/broker/full59k deferred.",
            "accepted": True,
            "reason": "No validated expanded universe exists yet.",
            "effect": "No scoring or enrichment authorization.",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0
    warning_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed, warning_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        if severity == "warning" and not passed:
            warning_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_21b_status_expected", v221b.get("status") == EXPECTED_V221B_STATUS, "critical", str(v221b.get("status")))
    add_check("v2_21c_status_expected", v221c.get("status") == EXPECTED_V221C_STATUS, "critical", str(v221c.get("status")))
    add_check("v2_21c2_status_expected", v221c2.get("status") == EXPECTED_V221C2_STATUS, "critical", str(v221c2.get("status")))
    add_check("v2_21c2_blocks_v2_21d", bool(v221c2.get("summary", {}).get("v2_21d_blocked")) is True, "critical", f"v2_21d_blocked={v221c2.get('summary', {}).get('v2_21d_blocked')}")
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("schema_column_count_expected", len(header) == 33, "critical", f"columns={len(header)}")
    add_check("endpoint_inventory_created", len(endpoint_inventory) >= len(SEED_ENDPOINTS), "critical", f"endpoint_inventory={len(endpoint_inventory)}")
    add_check("endpoint_fetches_attempted", len(fetch_rows) == len(endpoint_inventory), "critical", f"fetch_rows={len(fetch_rows)};inventory={len(endpoint_inventory)}")
    add_check("at_least_one_endpoint_fetch_successful", sum(1 for row in fetch_rows if row["fetch_success"]) > 0, "critical", f"successes={sum(1 for row in fetch_rows if row['fetch_success'])}")
    add_check("all_markets_structured_endpoint_ready", all_markets_ready, "warning", f"ready_markets={ready_markets};required={len(MARKET_DEFAULTS)}")
    add_check("at_least_one_market_structured_endpoint_ready", any_market_ready, "warning", f"ready_markets={ready_markets}")
    add_check("discovery_only_no_candidate_acceptance", True, "critical", "v2.21C3 does not accept or deduplicate candidates")
    add_check("structured_extraction_not_performed", True, "critical", "structured candidate extraction deferred to v2.21C4")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("pointer_update_not_performed", True, "critical", "pointer_update_performed=False")
    add_check("scoring_not_authorized", True, "critical", "scoring_authorized=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        discovery_decision = "ENDPOINT_DISCOVERY_BLOCKED_REVIEW_REQUIRED"
        approved_for_v2_21c4 = False
        approved_for_v2_21d = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    elif all_markets_ready:
        status = STATUS_ALL_MARKETS_READY
        discovery_decision = "STRUCTURED_ENDPOINTS_FOUND_FOR_ALL_TARGET_MARKETS_EXTRACTION_RETRY_ALLOWED"
        approved_for_v2_21c4 = True
        approved_for_v2_21d = False
        recommended_next_phase = NEXT_PHASE_ALL_READY
    else:
        status = STATUS_PARTIAL
        discovery_decision = "PARTIAL_OR_NO_STRUCTURED_ENDPOINT_COVERAGE_REVIEW_REQUIRED"
        approved_for_v2_21c4 = False
        approved_for_v2_21d = False
        recommended_next_phase = NEXT_PHASE_PARTIAL

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "structured_extraction",
            "action": "run_structured_candidate_extraction_from_validated_endpoints",
            "priority": "high" if approved_for_v2_21c4 else "blocked",
            "reason": "Structured endpoints are available for all target markets." if approved_for_v2_21c4 else "Not all target markets have validated structured endpoints.",
            "recommended_phase": NEXT_PHASE_ALL_READY if approved_for_v2_21c4 else NEXT_PHASE_PARTIAL,
            "guardrails": "no regex-only candidates; require structured fields; no rebuild",
        },
        {
            "action_order": 2,
            "action_scope": "missing_market_review",
            "action": "manually_review_missing_bvc_or_sgx_official_download_endpoint",
            "priority": "high" if not all_markets_ready else "medium",
            "reason": "Any market without structured endpoint remains blocked.",
            "recommended_phase": NEXT_PHASE_PARTIAL if not all_markets_ready else NEXT_PHASE_ALL_READY,
            "guardrails": "official exchange/regulator source only",
        },
        {
            "action_order": 3,
            "action_scope": "rebuild_control",
            "action": "keep_v2_21d_blocked_until_structured_extraction_dedup_succeeds",
            "priority": "high",
            "reason": "Endpoint discovery is not enough to rebuild.",
            "recommended_phase": recommended_next_phase,
            "guardrails": "no promotion, no pointer update, no scoring",
        },
    ]

    summary = {
        "selected_route": "Colombia + Singapore targeted expansion",
        "phase_type": PHASE_TYPE,
        "discovery_decision": discovery_decision,
        "approved_for_v2_21c4": approved_for_v2_21c4,
        "approved_for_v2_21d": approved_for_v2_21d,
        "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "operational_base_rows": operational_rows,
        "operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "target_markets": "Colombia/BVC;Singapore/SGX",
        "endpoint_candidates_tested": len(endpoint_inventory),
        "endpoint_fetches_successful": sum(1 for row in fetch_rows if row["fetch_success"]),
        "structured_endpoint_candidates_found": sum(1 for row in endpoint_validation_rows if row["structured_endpoint_candidate"]),
        "markets_with_structured_endpoint": ready_markets,
        "all_target_markets_ready": all_markets_ready,
        "structured_sample_rows": len(sample_rows),
        "raw_discovery_dir": str(DISCOVERY_RAW_DIR),
        "candidate_extraction_performed": False,
        "dedup_performed": False,
        "expanded_rebuild_performed": False,
        "v2_21d_blocked": True,
        "provider_expansion_scope": "targeted_only",
        "scoring_authorized": False,
        "openai_authorized": False,
        "broker_authorized": False,
        "full59k": "DEPRECATED_DEFERRED",
        "canonical_dataset_modified": False,
        "active_canonical_replaced": False,
        "pointer_update_performed": False,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(SUMMARY_CSV, [{"metric": key, "value": value} for key, value in summary.items()], ["metric", "value"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(ENDPOINT_INVENTORY_CSV, endpoint_inventory, ["market_id", "source_id", "url", "candidate_type", "priority", "reason"])
    write_csv(ENDPOINT_VALIDATION_CSV, endpoint_validation_rows, [
        "market_id", "provider", "source_id", "url", "candidate_type", "fetch_success",
        "http_status", "content_type", "raw_bytes", "raw_file", "parse_mode",
        "is_json", "is_csv", "is_excel_like", "is_html", "html_table_count",
        "next_data_object_count", "json_object_count", "json_list_count",
        "candidate_like_records", "structured_endpoint_candidate",
        "endpoint_validation_status", "key_summary", "review_reason",
    ])
    write_csv(MARKET_ENDPOINT_READINESS_CSV, market_readiness_rows, [
        "market_id", "country", "provider", "endpoint_candidates_tested",
        "fetch_success_count", "structured_endpoint_count", "weak_endpoint_count",
        "best_candidate_like_records", "market_endpoint_ready", "readiness_status",
        "recommended_action", "best_structured_source_id", "best_structured_url",
    ])
    write_csv(STRUCTURED_SAMPLE_CSV, sample_rows, ["market_id", "provider", "source_id", "sample_order", "sample_kind", "sample_payload"])
    write_csv(DECISION_REGISTER_CSV, decision_register_rows, ["decision_id", "decision", "accepted", "reason", "effect"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "market_endpoint_readiness": market_readiness_rows,
        "endpoint_validation": endpoint_validation_rows,
        "decision_register": decision_register_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Colombia + Singapore targeted expansion",
            "target_markets": ["Colombia/BVC", "Singapore/SGX"],
            "official_endpoint_discovery_only": True,
            "approved_for_v2_21c4": approved_for_v2_21c4,
            "approved_for_v2_21d": approved_for_v2_21d,
            "v2_21d_rebuild_blocked": True,
            "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "operational_base_rows": operational_rows,
            "operational_base_sha": operational_sha,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "candidate_extraction_performed": False,
            "dedup_performed": False,
            "regex_only_candidate_acceptance_allowed": False,
            "structured_extraction_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "file_edit_performed_on_operational_base": False,
            "file_copy_performed_on_operational_base": False,
            "file_rename_performed_on_operational_base": False,
            "canonical_dataset_modified": False,
            "active_canonical_replaced": False,
            "pointer_update_performed": False,
            "provider_expansion_scope": "targeted_only",
            "additional_provider_expansion_frozen": True,
            "scoring_authorized": False,
            "scoring_recalculated": False,
            "openai_authorized": False,
            "openai_called": False,
            "broker_authorized": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
            "history_rewrite_performed": False,
            "force_push_required": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    market_lines = "\n".join(
        f"- `{row['market_id']}` — ready `{row['market_endpoint_ready']}` — structured endpoints `{row['structured_endpoint_count']}` — best records `{row['best_candidate_like_records']}` — `{row['readiness_status']}`"
        for row in market_readiness_rows
    )

    validation_lines = "\n".join(
        f"- `{row['source_id']}` — `{row['market_id']}` — status `{row['endpoint_validation_status']}` — records `{row['candidate_like_records']}` — url `{row['url']}`"
        for row in endpoint_validation_rows
    )

    decision_lines = "\n".join(
        f"- `{row['decision_id']}` — accepted `{row['accepted']}` — {row['decision']}"
        for row in decision_register_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.21C3 discovers and validates official-domain structured endpoints or downloadable listing candidates for Colombia/BVC and Singapore/SGX.

This phase is discovery-only. It does not accept candidates, deduplicate, rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Discovery decision: `{discovery_decision}`
- Approved for v2.21C4: `{approved_for_v2_21c4}`
- Approved for v2.21D: `{approved_for_v2_21d}`
- Operational base rows: `{operational_rows}`
- Operational base SHA256: `{operational_sha}`
- Rollback rows: `{rollback_rows}`
- Rollback SHA256: `{rollback_sha}`
- Endpoint candidates tested: `{len(endpoint_inventory)}`
- Endpoint fetches successful: `{sum(1 for row in fetch_rows if row["fetch_success"])}`
- Structured endpoint candidates found: `{sum(1 for row in endpoint_validation_rows if row["structured_endpoint_candidate"])}`
- Markets with structured endpoint: `{ready_markets}`
- Structured sample rows: `{len(sample_rows)}`
- v2.21D blocked: `True`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Market endpoint readiness

{market_lines}

## Endpoint validation

{validation_lines}

## Decision register

{decision_lines}

## Checks

{check_lines}

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21C3 official endpoint discovery completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("MARKET_ENDPOINT_READINESS:")
    for row in market_readiness_rows:
        print(
            f"- {row['market_id']}: ready={row['market_endpoint_ready']} "
            f"structured={row['structured_endpoint_count']} "
            f"best_records={row['best_candidate_like_records']} "
            f"status={row['readiness_status']}"
        )
    print("")
    print("ENDPOINT_VALIDATION:")
    for row in endpoint_validation_rows:
        print(
            f"- {row['market_id']} {row['source_id']}: "
            f"status={row['endpoint_validation_status']} "
            f"records={row['candidate_like_records']} "
            f"fetch={row['fetch_success']} http={row['http_status']}"
        )
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
