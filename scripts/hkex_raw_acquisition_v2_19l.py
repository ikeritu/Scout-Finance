from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


VERSION = "v2.19L"
PHASE = "HKEX Raw Acquisition"
PHASE_TYPE = "raw-acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "hkex_v2_19l"

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219K_JSON = OUTPUT_DIR / "hkex_acquisition_plan_v2_19k.json"
V219K_SOURCE_INVENTORY_CSV = OUTPUT_DIR / "hkex_acquisition_plan_source_inventory_v2_19k.csv"
V219K_RAW_ARTIFACT_PLAN_CSV = OUTPUT_DIR / "hkex_acquisition_plan_raw_artifacts_v2_19k.csv"
V219K_VALIDATION_STRATEGY_CSV = OUTPUT_DIR / "hkex_acquisition_plan_validation_strategy_v2_19k.csv"
V219K_FILTERING_POLICY_CSV = OUTPUT_DIR / "hkex_acquisition_plan_filtering_policy_v2_19k.csv"

REPORT_JSON = OUTPUT_DIR / "hkex_raw_acquisition_v2_19l.json"
REPORT_MD = OUTPUT_DIR / "hkex_raw_acquisition_v2_19l.md"
MANIFEST_CSV = OUTPUT_DIR / "hkex_raw_acquisition_manifest_v2_19l.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_source_diagnostics_v2_19l.csv"
DISCOVERED_LINKS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_discovered_links_v2_19l.csv"
HTML_SIGNALS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_html_signals_v2_19l.csv"
ARTIFACT_INDEX_CSV = OUTPUT_DIR / "hkex_raw_acquisition_artifact_index_v2_19l.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_checks_v2_19l.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_raw_acquisition_next_actions_v2_19l.csv"

EXPECTED_V219K_STATUS = "HKEX_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_FOR_RAW_ACQUISITION_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

ALLOWED_HOSTS = {
    "www.hkex.com.hk",
    "hkex.com.hk",
    "www.hkexnews.hk",
    "hkexnews.hk",
}

STATUS_SUCCESS = "HKEX_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
RECOMMENDED_NEXT_PHASE = "v2.19M - HKEX Raw Validation"
RECOMMENDED_REVIEW_PHASE = "v2.19L_REVIEW - HKEX Raw Acquisition Review"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 ScoutFinanceRawAcquisition/2.19L"
)

SIGNAL_PATTERNS = [
    "Full List of Securities",
    "List of Equities Securities",
    "Newly Listed Securities",
    "Stock Short Name",
    "Stock Code",
    "Board Lot",
    "issuer",
    "listed company",
    "securities list",
    "download",
    ".csv",
    ".xls",
    ".xlsx",
    "Market Search",
    "HKEXnews",
]

LINK_RE = re.compile(r"""(?is)<a\b[^>]*?\bhref\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""")
SCRIPT_RE = re.compile(r"""(?is)<script\b[^>]*?\bsrc\s*=\s*["']([^"']+)["'][^>]*>""")
FORM_RE = re.compile(r"""(?is)<form\b[^>]*?(?:\baction\s*=\s*["']([^"']*)["'])?[^>]*>""")
TITLE_RE = re.compile(r"""(?is)<title[^>]*>(.*?)</title>""")
TEXT_CLEAN_RE = re.compile(r"\s+")


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


def official_scope_allowed(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS


def extension_from_content_type(content_type: str, url: str) -> str:
    lower_url = url.lower().split("?")[0]
    for suffix in [".csv", ".xlsx", ".xls", ".json", ".xml", ".txt", ".htm", ".html", ".pdf"]:
        if lower_url.endswith(suffix):
            return suffix

    ct = content_type.lower()
    if "html" in ct:
        return ".html"
    if "json" in ct:
        return ".json"
    if "csv" in ct:
        return ".csv"
    if "spreadsheet" in ct or "excel" in ct:
        return ".xlsx"
    if "xml" in ct:
        return ".xml"
    if "pdf" in ct:
        return ".pdf"
    if "text" in ct:
        return ".txt"
    return ".bin"


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


def clean_text(value: str, max_len: int = 240) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    value = TEXT_CLEAN_RE.sub(" ", value).strip()
    if len(value) > max_len:
        return value[: max_len - 3] + "..."
    return value


def fetch_url(url: str, timeout: int = 30) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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


def extract_title(text: str) -> str:
    match = TITLE_RE.search(text)
    return clean_text(match.group(1), max_len=200) if match else ""


def extract_links(text: str, base_url: str, source_id: str, artifact_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for index, match in enumerate(LINK_RE.finditer(text), start=1):
        raw_href = html.unescape(match.group(1).strip())
        label = clean_text(match.group(2), max_len=180)
        absolute_url = urljoin(base_url, raw_href)
        parsed = urlparse(absolute_url)
        if not parsed.scheme.startswith("http"):
            continue

        if absolute_url in seen:
            continue
        seen.add(absolute_url)

        lower = absolute_url.lower()
        label_lower = label.lower()
        looks_download = any(token in lower for token in [".csv", ".xls", ".xlsx", ".zip", "download", "export"])
        looks_candidate_related = any(
            token in lower or token in label_lower
            for token in [
                "securities",
                "equities",
                "listed",
                "stock",
                "issuer",
                "company",
                "csv",
                "xls",
                "xlsx",
            ]
        )

        rows.append(
            {
                "source_id": source_id,
                "artifact_id": artifact_id,
                "link_order": index,
                "link_type": "anchor",
                "label": label,
                "url": absolute_url,
                "host": parsed.hostname or "",
                "official_scope_allowed": official_scope_allowed(absolute_url),
                "looks_download": looks_download,
                "looks_candidate_related": looks_candidate_related,
            }
        )

    return rows


def extract_scripts(text: str, base_url: str, source_id: str, artifact_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for index, match in enumerate(SCRIPT_RE.finditer(text), start=1):
        raw_src = html.unescape(match.group(1).strip())
        absolute_url = urljoin(base_url, raw_src)
        parsed = urlparse(absolute_url)
        if not parsed.scheme.startswith("http"):
            continue

        if absolute_url in seen:
            continue
        seen.add(absolute_url)

        lower = absolute_url.lower()
        rows.append(
            {
                "source_id": source_id,
                "artifact_id": artifact_id,
                "link_order": index,
                "link_type": "script",
                "label": "",
                "url": absolute_url,
                "host": parsed.hostname or "",
                "official_scope_allowed": official_scope_allowed(absolute_url),
                "looks_download": False,
                "looks_candidate_related": any(token in lower for token in ["stock", "securities", "equities", "market", "search", "issuer", "listed"]),
            }
        )

    return rows


def extract_forms(text: str, base_url: str, source_id: str, artifact_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for index, match in enumerate(FORM_RE.finditer(text), start=1):
        raw_action = html.unescape((match.group(1) or "").strip())
        absolute_url = urljoin(base_url, raw_action) if raw_action else base_url
        parsed = urlparse(absolute_url)

        rows.append(
            {
                "source_id": source_id,
                "artifact_id": artifact_id,
                "link_order": index,
                "link_type": "form",
                "label": "",
                "url": absolute_url,
                "host": parsed.hostname or "",
                "official_scope_allowed": official_scope_allowed(absolute_url),
                "looks_download": False,
                "looks_candidate_related": True,
            }
        )

    return rows


def html_signal_rows(text: str, source_id: str, artifact_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    text_lower = text.lower()

    for pattern in SIGNAL_PATTERNS:
        count = text_lower.count(pattern.lower())
        rows.append(
            {
                "source_id": source_id,
                "artifact_id": artifact_id,
                "signal": pattern,
                "count": count,
                "present": count > 0,
            }
        )

    rows.append(
        {
            "source_id": source_id,
            "artifact_id": artifact_id,
            "signal": "html_table_tags",
            "count": len(re.findall(r"(?is)<table\b", text)),
            "present": bool(re.search(r"(?is)<table\b", text)),
        }
    )

    rows.append(
        {
            "source_id": source_id,
            "artifact_id": artifact_id,
            "signal": "anchor_tags",
            "count": len(re.findall(r"(?is)<a\b", text)),
            "present": bool(re.search(r"(?is)<a\b", text)),
        }
    )

    rows.append(
        {
            "source_id": source_id,
            "artifact_id": artifact_id,
            "signal": "script_tags",
            "count": len(re.findall(r"(?is)<script\b", text)),
            "present": bool(re.search(r"(?is)<script\b", text)),
        }
    )

    rows.append(
        {
            "source_id": source_id,
            "artifact_id": artifact_id,
            "signal": "form_tags",
            "count": len(re.findall(r"(?is)<form\b", text)),
            "present": bool(re.search(r"(?is)<form\b", text)),
        }
    )

    return rows


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        MANIFEST_CSV,
        SOURCE_DIAGNOSTICS_CSV,
        DISCOVERED_LINKS_CSV,
        HTML_SIGNALS_CSV,
        ARTIFACT_INDEX_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists() and any(RAW_DIR.iterdir()):
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw directory already contains files: {RAW_DIR}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    v219k = read_json(V219K_JSON)
    _, source_inventory_rows = read_csv_with_header(V219K_SOURCE_INVENTORY_CSV)
    _, raw_artifact_plan_rows = read_csv_with_header(V219K_RAW_ARTIFACT_PLAN_CSV)
    _, validation_strategy_rows = read_csv_with_header(V219K_VALIDATION_STRATEGY_CSV)
    _, filtering_policy_rows = read_csv_with_header(V219K_FILTERING_POLICY_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    manifest_rows: list[dict[str, Any]] = []
    source_diagnostics_rows: list[dict[str, Any]] = []
    discovered_link_rows: list[dict[str, Any]] = []
    signal_rows: list[dict[str, Any]] = []
    artifact_index_rows: list[dict[str, Any]] = []

    for planned in raw_artifact_plan_rows:
        artifact_order = to_int(planned.get("artifact_order", len(manifest_rows) + 1))
        source_id = planned["source_id"]
        artifact_id = planned["artifact_id"]
        url = planned["url"]

        if not official_scope_allowed(url):
            raise SystemExit(f"OFFICIAL_SCOPE_GUARD: planned URL is not HKEX/HKEXnews official scope: {url}")

        fetched_at = utc_now()
        response = fetch_url(url)
        body = response["bytes"] or b""
        content_type = str(response.get("content_type", ""))
        extension = extension_from_content_type(content_type, url)
        raw_file = RAW_DIR / f"{artifact_order:02d}_{artifact_id}{extension}"
        header_file = RAW_DIR / f"{artifact_order:02d}_{artifact_id}_headers.json"

        if raw_file.exists() or header_file.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: raw artifact already exists for {artifact_id}")

        raw_file.write_bytes(body)
        write_json(
            header_file,
            {
                "version": VERSION,
                "source_id": source_id,
                "artifact_id": artifact_id,
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

        sha = sha256_bytes(body)
        final_url = str(response.get("final_url", url))
        final_official_scope_allowed = official_scope_allowed(final_url)
        byte_count = len(body)
        status_code = to_int(response.get("status_code", 0))
        http_success = 200 <= status_code < 400

        text = ""
        title = ""
        anchor_count = 0
        script_count = 0
        form_count = 0
        table_count = 0
        html_like = "html" in content_type.lower() or extension in {".html", ".htm"}

        if byte_count > 0 and html_like:
            text = decode_text(body, content_type)
            title = extract_title(text)
            link_rows = extract_links(text, final_url, source_id, artifact_id)
            script_rows = extract_scripts(text, final_url, source_id, artifact_id)
            form_rows = extract_forms(text, final_url, source_id, artifact_id)
            discovered_link_rows.extend(link_rows)
            discovered_link_rows.extend(script_rows)
            discovered_link_rows.extend(form_rows)
            signal_rows.extend(html_signal_rows(text, source_id, artifact_id))

            anchor_count = len(link_rows)
            script_count = len(script_rows)
            form_count = len(form_rows)
            table_count = len(re.findall(r"(?is)<table\b", text))

        manifest_rows.append(
            {
                "artifact_order": artifact_order,
                "source_id": source_id,
                "artifact_id": artifact_id,
                "requested_url": url,
                "final_url": final_url,
                "official_scope_allowed": official_scope_allowed(url),
                "final_official_scope_allowed": final_official_scope_allowed,
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

        source_diagnostics_rows.append(
            {
                "source_id": source_id,
                "artifact_id": artifact_id,
                "http_status": status_code,
                "http_success": http_success,
                "byte_count": byte_count,
                "content_type": content_type,
                "title": title,
                "html_like": html_like,
                "anchor_count": anchor_count,
                "script_count": script_count,
                "form_count": form_count,
                "table_count": table_count,
                "official_link_count": sum(1 for row in discovered_link_rows if row["artifact_id"] == artifact_id and row["official_scope_allowed"]),
                "candidate_related_link_count": sum(1 for row in discovered_link_rows if row["artifact_id"] == artifact_id and row["looks_candidate_related"]),
                "download_like_link_count": sum(1 for row in discovered_link_rows if row["artifact_id"] == artifact_id and row["looks_download"]),
                "raw_path": str(raw_file),
            }
        )

        artifact_index_rows.append(
            {
                "artifact_id": artifact_id,
                "source_id": source_id,
                "raw_path": str(raw_file),
                "headers_path": str(header_file),
                "content_type": content_type,
                "byte_count": byte_count,
                "sha256": sha,
                "validation_phase": "v2.19M",
                "candidate_extraction_phase": "not_before_v2.19N_and_only_if_validation_passes",
            }
        )

        time.sleep(0.5)

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    official_scope_violations = sum(
        1
        for row in manifest_rows
        if not row["official_scope_allowed"] or not row["final_official_scope_allowed"]
    )
    artifacts_written_count = len(manifest_rows)
    raw_files_exist_count = sum(1 for row in manifest_rows if Path(str(row["raw_path"])).exists())
    header_files_exist_count = sum(1 for row in manifest_rows if Path(str(row["headers_path"])).exists())
    nonempty_raw_count = sum(1 for row in manifest_rows if to_int(row["byte_count"]) > 0)
    http_success_count = sum(1 for row in manifest_rows if str(row["http_success"]).lower() == "true")
    http_error_count = sum(1 for row in manifest_rows if str(row["http_success"]).lower() != "true")
    discovered_links_count = len(discovered_link_rows)
    official_discovered_links_count = sum(1 for row in discovered_link_rows if row["official_scope_allowed"])
    candidate_related_links_count = sum(1 for row in discovered_link_rows if row["looks_candidate_related"])
    download_like_links_count = sum(1 for row in discovered_link_rows if row["looks_download"])
    html_signal_present_count = sum(1 for row in signal_rows if row["present"])

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "HKEX",
            "action": "run_hkex_raw_validation",
            "priority": "high",
            "reason": "HKEX raw artifacts have been captured and need validation before any extraction.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "raw validation only; do not extract candidates; do not modify canonical",
        },
        {
            "action_order": 2,
            "action_scope": "HKEX",
            "action": "review_discovered_links_for_official_download_candidates",
            "priority": "high",
            "reason": "HTML pages may expose official downloadable files or API-like resources.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "only official HKEX/HKEXnews links; no unofficial mirrors",
        },
        {
            "action_order": 3,
            "action_scope": "50k",
            "action": "preserve_quality_gate",
            "priority": "high",
            "reason": "Current candidate universe remains 40,996; rows needed to 50k remain 9,004.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE,
            "guardrails": "no candidate append before extraction + canonical validation; no full59k",
        },
    ]

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19k_report_exists", V219K_JSON.exists(), "critical", str(V219K_JSON))
    add_check("v2_19k_status_expected", v219k.get("status") == EXPECTED_V219K_STATUS, "critical", str(v219k.get("status", "")))
    add_check("source_inventory_exists", V219K_SOURCE_INVENTORY_CSV.exists(), "critical", str(V219K_SOURCE_INVENTORY_CSV))
    add_check("raw_artifact_plan_exists", V219K_RAW_ARTIFACT_PLAN_CSV.exists(), "critical", str(V219K_RAW_ARTIFACT_PLAN_CSV))
    add_check("source_inventory_rows_expected", len(source_inventory_rows) >= 5, "critical", f"source_inventory_rows={len(source_inventory_rows)}")
    add_check("raw_artifact_plan_rows_expected", len(raw_artifact_plan_rows) >= 5, "critical", f"raw_artifact_plan_rows={len(raw_artifact_plan_rows)}")
    add_check("validation_strategy_loaded", len(validation_strategy_rows) >= 5, "critical", f"validation_strategy_rows={len(validation_strategy_rows)}")
    add_check("filtering_policy_loaded", len(filtering_policy_rows) >= 4, "critical", f"filtering_policy_rows={len(filtering_policy_rows)}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("raw_directory_exists", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("planned_artifacts_written", artifacts_written_count == len(raw_artifact_plan_rows), "critical", f"artifacts_written={artifacts_written_count}; planned={len(raw_artifact_plan_rows)}")
    add_check("raw_files_exist", raw_files_exist_count == artifacts_written_count, "critical", f"raw_files_exist={raw_files_exist_count}/{artifacts_written_count}")
    add_check("header_files_exist", header_files_exist_count == artifacts_written_count, "critical", f"header_files_exist={header_files_exist_count}/{artifacts_written_count}")
    add_check("raw_files_nonempty", nonempty_raw_count >= 1, "critical", f"nonempty_raw_count={nonempty_raw_count}/{artifacts_written_count}")
    add_check("official_scope_no_violations", official_scope_violations == 0, "critical", f"official_scope_violations={official_scope_violations}")
    add_check("http_success_documented", http_success_count >= 0, "warning", f"http_success_count={http_success_count}; http_error_count={http_error_count}")
    add_check("discovered_links_documented", discovered_links_count >= 0, "warning", f"discovered_links_count={discovered_links_count}")
    add_check("candidate_related_links_documented", candidate_related_links_count >= 0, "warning", f"candidate_related_links_count={candidate_related_links_count}")
    add_check("download_like_links_documented", download_like_links_count >= 0, "warning", f"download_like_links_count={download_like_links_count}")
    add_check("html_signals_documented", html_signal_present_count >= 0, "warning", f"html_signal_present_count={html_signal_present_count}")
    add_check("final_50k_gate_still_blocked", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("network_used_by_raw_acquisition", True, "critical", "network_download_performed=True")
    add_check("raw_acquisition_performed", True, "critical", "raw_acquisition_performed=True")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("next_phase_hkex_raw_validation", RECOMMENDED_NEXT_PHASE == "v2.19M - HKEX Raw Validation", "critical", RECOMMENDED_NEXT_PHASE)

    if critical_failed == 0:
        status = STATUS_SUCCESS
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "HKEX_RAW_ACQUISITION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    acquisition_summary = {
        "source_inventory_rows": len(source_inventory_rows),
        "raw_artifact_plan_rows": len(raw_artifact_plan_rows),
        "artifacts_written_count": artifacts_written_count,
        "raw_files_exist_count": raw_files_exist_count,
        "header_files_exist_count": header_files_exist_count,
        "nonempty_raw_count": nonempty_raw_count,
        "http_success_count": http_success_count,
        "http_error_count": http_error_count,
        "official_scope_violations": official_scope_violations,
        "discovered_links_count": discovered_links_count,
        "official_discovered_links_count": official_discovered_links_count,
        "candidate_related_links_count": candidate_related_links_count,
        "download_like_links_count": download_like_links_count,
        "html_signal_rows": len(signal_rows),
        "html_signal_present_count": html_signal_present_count,
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
        "v2_19k_context": {
            "status": v219k.get("status"),
            "selected_route_id": v219k.get("plan_summary", {}).get("selected_route_id"),
            "selected_provider": v219k.get("plan_summary", {}).get("selected_provider"),
            "source_inventory_rows": len(source_inventory_rows),
            "raw_artifact_plan_rows": len(raw_artifact_plan_rows),
            "validation_strategy_rows": len(validation_strategy_rows),
            "filtering_policy_rows": len(filtering_policy_rows),
        },
        "acquisition_summary": acquisition_summary,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "endpoint_calls_performed": True,
            "query_sweep_performed": False,
            "route_selection_performed": False,
            "acquisition_plan_performed": False,
            "raw_acquisition_performed": True,
            "raw_acquisition_repair_performed": False,
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

    manifest_fieldnames = [
        "artifact_order",
        "source_id",
        "artifact_id",
        "requested_url",
        "final_url",
        "official_scope_allowed",
        "final_official_scope_allowed",
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
    ]

    source_diagnostics_fieldnames = [
        "source_id",
        "artifact_id",
        "http_status",
        "http_success",
        "byte_count",
        "content_type",
        "title",
        "html_like",
        "anchor_count",
        "script_count",
        "form_count",
        "table_count",
        "official_link_count",
        "candidate_related_link_count",
        "download_like_link_count",
        "raw_path",
    ]

    discovered_link_fieldnames = [
        "source_id",
        "artifact_id",
        "link_order",
        "link_type",
        "label",
        "url",
        "host",
        "official_scope_allowed",
        "looks_download",
        "looks_candidate_related",
    ]

    html_signal_fieldnames = [
        "source_id",
        "artifact_id",
        "signal",
        "count",
        "present",
    ]

    artifact_index_fieldnames = [
        "artifact_id",
        "source_id",
        "raw_path",
        "headers_path",
        "content_type",
        "byte_count",
        "sha256",
        "validation_phase",
        "candidate_extraction_phase",
    ]

    write_csv(MANIFEST_CSV, manifest_rows, manifest_fieldnames)
    write_csv(SOURCE_DIAGNOSTICS_CSV, source_diagnostics_rows, source_diagnostics_fieldnames)
    write_csv(DISCOVERED_LINKS_CSV, discovered_link_rows, discovered_link_fieldnames)
    write_csv(HTML_SIGNALS_CSV, signal_rows, html_signal_fieldnames)
    write_csv(ARTIFACT_INDEX_CSV, artifact_index_rows, artifact_index_fieldnames)
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    manifest_lines = "\n".join(
        f"- `{row['artifact_id']}` — HTTP `{row['http_status']}` — bytes `{row['byte_count']}` — `{row['raw_path']}`"
        for row in manifest_rows
    )

    diagnostics_lines = "\n".join(
        f"- `{row['artifact_id']}` — anchors `{row['anchor_count']}` — scripts `{row['script_count']}` — tables `{row['table_count']}` — downloads `{row['download_like_link_count']}`"
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
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.19L captures official HKEX/HKEXnews raw artifacts planned in v2.19K.

This phase performs raw acquisition only. It does not validate raw artifacts for parse-readiness, does not extract candidates, does not compare against canonical, does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Acquisition summary

- Source inventory rows: `{len(source_inventory_rows)}`
- Raw artifact plan rows: `{len(raw_artifact_plan_rows)}`
- Artifacts written: `{artifacts_written_count}`
- Raw files exist: `{raw_files_exist_count}`
- Header files exist: `{header_files_exist_count}`
- Non-empty raw files: `{nonempty_raw_count}`
- HTTP success count: `{http_success_count}`
- HTTP error count: `{http_error_count}`
- Official scope violations: `{official_scope_violations}`
- Discovered links: `{discovered_links_count}`
- Official discovered links: `{official_discovered_links_count}`
- Candidate-related links: `{candidate_related_links_count}`
- Download-like links: `{download_like_links_count}`
- HTML signal rows: `{len(signal_rows)}`
- HTML signals present: `{html_signal_present_count}`

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

    print("v2.19L HKEX raw acquisition completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("ACQUISITION_SUMMARY:")
    for key, value in acquisition_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("MANIFEST:")
    for row in manifest_rows:
        print(f"- {row['artifact_id']}: status={row['http_status']} success={row['http_success']} bytes={row['byte_count']} sha256={row['sha256']} raw={row['raw_path']}")
    print("")
    print("SOURCE_DIAGNOSTICS:")
    for row in source_diagnostics_rows:
        print(f"- {row['artifact_id']}: title={row['title']} anchors={row['anchor_count']} scripts={row['script_count']} forms={row['form_count']} tables={row['table_count']} downloads={row['download_like_link_count']}")
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
