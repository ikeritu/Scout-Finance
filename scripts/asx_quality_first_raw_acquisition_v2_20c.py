from __future__ import annotations

import csv
import hashlib
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


VERSION = "v2.20C"
PHASE = "ASX Quality-First Raw Acquisition"
PHASE_TYPE = "raw-acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "asx_v2_20c"
PAGES_DIR = RAW_DIR / "pages"
DOWNLOADS_DIR = RAW_DIR / "downloads"

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
HKEX_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V220B_JSON = OUTPUT_DIR / "asx_quality_first_acquisition_plan_v2_20b.json"

REPORT_JSON = OUTPUT_DIR / "asx_quality_first_raw_acquisition_v2_20c.json"
REPORT_MD = OUTPUT_DIR / "asx_quality_first_raw_acquisition_v2_20c.md"
MANIFEST_CSV = OUTPUT_DIR / "asx_quality_first_raw_manifest_v2_20c.csv"
ATTEMPTS_CSV = OUTPUT_DIR / "asx_quality_first_raw_download_attempts_v2_20c.csv"
DISCOVERED_LINKS_CSV = OUTPUT_DIR / "asx_quality_first_raw_discovered_links_v2_20c.csv"
CHECKS_CSV = OUTPUT_DIR / "asx_quality_first_raw_acquisition_checks_v2_20c.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "asx_quality_first_raw_next_actions_v2_20c.csv"

EXPECTED_V220B_STATUS = "ASX_QUALITY_FIRST_ACQUISITION_PLAN_COMPLETED_OFFICIAL_SOURCES_READY_RAW_ACQUISITION_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
HKEX_VALIDATED_CANDIDATE_ROWS_EXPECTED = 41392

ACTIVE_CANONICAL_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"
CURRENT_CANDIDATE_SHA_EXPECTED = "05047f03058c6d3d200b70f5f6e28e313dd9a98018b8ac44ea449989773c3aa2"
HKEX_VALIDATED_CANDIDATE_SHA_EXPECTED = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000
ASPIRATIONAL_TARGET = 50000

ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED = 608
ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED = 3608
ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED = 8608

STATUS_SUCCESS = "ASX_QUALITY_FIRST_RAW_ACQUISITION_COMPLETED_RAW_FILES_CAPTURED_VALIDATION_READY_42K_45K_OPERATIONAL_50K_ASPIRATIONAL_FULL59K_DEPRECATED"
STATUS_REVIEW = "ASX_QUALITY_FIRST_RAW_ACQUISITION_COMPLETED_WITH_WARNINGS_REVIEW_RAW_VALIDATION_REQUIRED"
STATUS_FAILED = "ASX_QUALITY_FIRST_RAW_ACQUISITION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.20D - ASX Raw Validation"
NEXT_PHASE_REVIEW = "v2.20C_REVIEW - ASX Raw Acquisition Review"

REQUEST_TIMEOUT_SECONDS = 35
SLEEP_BETWEEN_REQUESTS_SECONDS = 0.75

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 ScoutFinanceRawAcquisition/2.20C"
)

PAGE_SOURCES = [
    {
        "source_id": "asx_indices_page",
        "url": "https://www.asx.com.au/markets/trade-our-cash-market/overview/indices",
        "expected_role": "complete_list_csv_discovery_and_index_context",
        "required": True,
    },
    {
        "source_id": "asx_company_directory_page",
        "url": "https://www.asx.com.au/markets/trade-our-cash-market/directory",
        "expected_role": "company_directory_context_and_exclusion_disclaimer",
        "required": True,
    },
    {
        "source_id": "asx_isin_services_page",
        "url": "https://www.asx.com.au/markets/market-resources/isin-services",
        "expected_role": "isin_xls_discovery_and_identifier_context",
        "required": True,
    },
    {
        "source_id": "asx_codes_and_descriptors_page",
        "url": "https://www.asx.com.au/markets/market-resources/asx-codes-and-descriptors",
        "expected_role": "instrument_scope_reference",
        "required": True,
    },
    {
        "source_id": "asx_market_statistics_page",
        "url": "https://www.asx.com.au/about/market-statistics",
        "expected_role": "market_size_context",
        "required": False,
    },
]

DIRECT_DOWNLOAD_CANDIDATES = [
    {
        "source_id": "asx_isin_xls_direct",
        "url": "https://www.asx.com.au/content/dam/asx/issuers/ISIN.xls",
        "expected_role": "isin_identifier_enrichment_download",
        "required": False,
    },
    {
        "source_id": "asx_listed_companies_legacy_csv",
        "url": "https://www.asx.com.au/asx/research/ASXListedCompanies.csv",
        "expected_role": "legacy_complete_list_csv_candidate_optional",
        "required": False,
    },
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


def safe_slug(value: str, max_len: int = 80) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value[:max_len] or "raw"


def guess_extension(url: str, content_type: str, fallback: str = ".bin") -> str:
    lower_path = urlparse(url).path.lower()

    for ext in [".csv", ".xls", ".xlsx", ".json", ".html", ".htm", ".txt", ".pdf"]:
        if lower_path.endswith(ext):
            return ext

    ct = content_type.lower()
    if "text/html" in ct:
        return ".html"
    if "text/csv" in ct or "csv" in ct:
        return ".csv"
    if "excel" in ct or "spreadsheet" in ct or "vnd.ms-excel" in ct:
        return ".xls"
    if "json" in ct:
        return ".json"
    if "pdf" in ct:
        return ".pdf"

    return fallback


def fetch_url(url: str, output_path: Path, source_id: str, expected_role: str, required: bool) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if output_path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {output_path}")

    started_at = utc_now()
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,text/csv,application/vnd.ms-excel,application/octet-stream,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        },
        method="GET",
    )

    attempt: dict[str, Any] = {
        "source_id": source_id,
        "url": url,
        "expected_role": expected_role,
        "required": required,
        "started_at_utc": started_at,
        "finished_at_utc": "",
        "success": False,
        "status_code": "",
        "content_type": "",
        "bytes": 0,
        "sha256": "",
        "output_path": "",
        "error_type": "",
        "error": "",
    }

    manifest_row: dict[str, Any] | None = None

    try:
        context = ssl.create_default_context()
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=context) as response:
            data = response.read()
            status_code = getattr(response, "status", "")
            content_type = response.headers.get("Content-Type", "")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(data)

        digest = sha256_file(output_path)
        attempt.update(
            {
                "finished_at_utc": utc_now(),
                "success": True,
                "status_code": status_code,
                "content_type": content_type,
                "bytes": len(data),
                "sha256": digest,
                "output_path": str(output_path),
            }
        )
        manifest_row = {
            "source_id": source_id,
            "url": url,
            "expected_role": expected_role,
            "required": required,
            "capture_type": "raw_download",
            "status_code": status_code,
            "content_type": content_type,
            "bytes": len(data),
            "sha256": digest,
            "path": str(output_path),
            "captured_at_utc": attempt["finished_at_utc"],
        }

    except HTTPError as exc:
        attempt.update(
            {
                "finished_at_utc": utc_now(),
                "success": False,
                "status_code": exc.code,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
    except URLError as exc:
        attempt.update(
            {
                "finished_at_utc": utc_now(),
                "success": False,
                "error_type": type(exc).__name__,
                "error": str(exc.reason),
            }
        )
    except Exception as exc:
        attempt.update(
            {
                "finished_at_utc": utc_now(),
                "success": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )

    return attempt, manifest_row


def discover_links_from_html(html_path: Path, base_url: str, source_id: str) -> list[dict[str, Any]]:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    candidates = re.findall(r"""(?:href|src)=["']([^"']+)["']""", text, flags=re.IGNORECASE)

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw_link in candidates:
        absolute_url = urljoin(base_url, raw_link.strip())
        if absolute_url in seen:
            continue
        seen.add(absolute_url)

        parsed = urlparse(absolute_url)
        path_lower = parsed.path.lower()
        query_lower = parsed.query.lower()
        url_lower = absolute_url.lower()

        is_structured_candidate = any(
            marker in url_lower
            for marker in [
                ".csv",
                ".xls",
                ".xlsx",
                "asxlistedcompanies",
                "isin",
                "listed",
                "directory",
            ]
        )

        if not is_structured_candidate:
            continue

        rows.append(
            {
                "discovered_from_source_id": source_id,
                "discovered_from_path": str(html_path),
                "url": absolute_url,
                "netloc": parsed.netloc,
                "path": parsed.path,
                "query": parsed.query,
                "extension_hint": Path(parsed.path).suffix.lower(),
                "structured_candidate": is_structured_candidate,
                "download_candidate": path_lower.endswith((".csv", ".xls", ".xlsx")) or "asxlistedcompanies" in query_lower or "asxlistedcompanies" in path_lower or "isin.xls" in path_lower,
            }
        )

    return rows


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        MANIFEST_CSV,
        ATTEMPTS_CSV,
        DISCOVERED_LINKS_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists() and any(RAW_DIR.rglob("*")):
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw directory already contains files: {RAW_DIR}")

    v220b = read_json(V220B_JSON)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_rows = count_csv_rows(HKEX_VALIDATED_CANDIDATE_DATASET)

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_before = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

    rows_needed_to_quality_floor = max(QUALITY_FLOOR_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_quality_ceiling = max(QUALITY_CEILING_TARGET - hkex_validated_candidate_rows, 0)
    rows_needed_to_aspirational_50k = max(ASPIRATIONAL_TARGET - hkex_validated_candidate_rows, 0)

    attempts: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    discovered_links: list[dict[str, Any]] = []

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    for source in PAGE_SOURCES:
        source_id = source["source_id"]
        output_path = PAGES_DIR / f"{safe_slug(source_id)}.html"

        attempt, manifest_row = fetch_url(
            url=source["url"],
            output_path=output_path,
            source_id=source_id,
            expected_role=source["expected_role"],
            required=source["required"],
        )
        attempts.append(attempt)
        if manifest_row:
            manifest.append(manifest_row)
            discovered_links.extend(discover_links_from_html(output_path, source["url"], source_id))

        time.sleep(SLEEP_BETWEEN_REQUESTS_SECONDS)

    direct_candidates = list(DIRECT_DOWNLOAD_CANDIDATES)

    seen_direct_urls = {row["url"] for row in direct_candidates}
    for link in discovered_links:
        if not link.get("download_candidate"):
            continue

        url = link["url"]
        parsed = urlparse(url)

        if parsed.netloc and "asx.com.au" not in parsed.netloc.lower():
            continue

        if url in seen_direct_urls:
            continue

        seen_direct_urls.add(url)
        direct_candidates.append(
            {
                "source_id": f"asx_discovered_{safe_slug(Path(parsed.path).stem or parsed.path or 'download')}",
                "url": url,
                "expected_role": f"discovered_download_candidate_from_{link['discovered_from_source_id']}",
                "required": False,
            }
        )

    for source in direct_candidates:
        parsed = urlparse(source["url"])
        extension = guess_extension(source["url"], "")
        filename = f"{safe_slug(source['source_id'])}{extension}"
        output_path = DOWNLOADS_DIR / filename

        # Avoid filename collision without overwriting.
        counter = 2
        while output_path.exists():
            output_path = DOWNLOADS_DIR / f"{safe_slug(source['source_id'])}_{counter}{extension}"
            counter += 1

        attempt, manifest_row = fetch_url(
            url=source["url"],
            output_path=output_path,
            source_id=source["source_id"],
            expected_role=source["expected_role"],
            required=source["required"],
        )
        attempts.append(attempt)
        if manifest_row:
            # If content type gives a better extension, keep the already captured file as raw evidence.
            manifest.append(manifest_row)

        time.sleep(SLEEP_BETWEEN_REQUESTS_SECONDS)

    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    current_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    hkex_validated_candidate_sha_after = sha256_file(HKEX_VALIDATED_CANDIDATE_DATASET)

    successful_attempts = [row for row in attempts if row["success"] is True]
    failed_attempts = [row for row in attempts if row["success"] is False]
    required_failed_attempts = [row for row in attempts if row["required"] is True and row["success"] is False]

    captured_page_count = sum(1 for row in manifest if row["path"].endswith(".html") and "\\pages\\" in row["path"] or "/pages/" in row["path"])
    captured_download_count = sum(1 for row in manifest if "\\downloads\\" in row["path"] or "/downloads/" in row["path"])
    captured_csv_count = sum(1 for row in manifest if row["path"].lower().endswith(".csv"))
    captured_xls_count = sum(1 for row in manifest if row["path"].lower().endswith((".xls", ".xlsx")))

    discovered_download_candidate_count = sum(1 for row in discovered_links if row.get("download_candidate"))
    legacy_csv_attempts = [row for row in attempts if row["source_id"] == "asx_listed_companies_legacy_csv"]
    legacy_csv_status = legacy_csv_attempts[0]["status_code"] if legacy_csv_attempts else ""

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

    add_check("v2_20b_report_exists", V220B_JSON.exists(), "critical", str(V220B_JSON))
    add_check("v2_20b_status_expected", v220b.get("status") == EXPECTED_V220B_STATUS, "critical", str(v220b.get("status", "")))
    add_check("v2_20b_next_phase_expected", v220b.get("recommended_next_phase") == "v2.20C - ASX Quality-First Raw Acquisition", "critical", str(v220b.get("recommended_next_phase")))
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("hkex_validated_candidate_rows_expected", hkex_validated_candidate_rows == HKEX_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"hkex_rows={hkex_validated_candidate_rows}")
    add_check("active_canonical_sha_expected", active_canonical_sha_before == ACTIVE_CANONICAL_SHA_EXPECTED, "critical", active_canonical_sha_before)
    add_check("current_candidate_sha_expected", current_candidate_sha_before == CURRENT_CANDIDATE_SHA_EXPECTED, "critical", current_candidate_sha_before)
    add_check("hkex_validated_candidate_sha_expected", hkex_validated_candidate_sha_before == HKEX_VALIDATED_CANDIDATE_SHA_EXPECTED, "critical", hkex_validated_candidate_sha_before)
    add_check("active_canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("current_candidate_sha_unchanged", current_candidate_sha_before == current_candidate_sha_after, "critical", "current candidate sha unchanged")
    add_check("hkex_candidate_sha_unchanged", hkex_validated_candidate_sha_before == hkex_validated_candidate_sha_after, "critical", "HKEX candidate sha unchanged")
    add_check("quality_floor_target_preserved", QUALITY_FLOOR_TARGET == 42000, "critical", f"quality_floor={QUALITY_FLOOR_TARGET}")
    add_check("quality_ceiling_target_preserved", QUALITY_CEILING_TARGET == 45000, "critical", f"quality_ceiling={QUALITY_CEILING_TARGET}")
    add_check("rows_needed_to_quality_floor_expected", rows_needed_to_quality_floor == ROWS_NEEDED_TO_QUALITY_FLOOR_EXPECTED, "critical", f"rows_needed_to_42k={rows_needed_to_quality_floor}")
    add_check("rows_needed_to_quality_ceiling_expected", rows_needed_to_quality_ceiling == ROWS_NEEDED_TO_QUALITY_CEILING_EXPECTED, "critical", f"rows_needed_to_45k={rows_needed_to_quality_ceiling}")
    add_check("rows_needed_to_50k_aspirational_expected", rows_needed_to_aspirational_50k == ROWS_NEEDED_TO_ASPIRATIONAL_50K_EXPECTED, "warning", f"rows_needed_to_50k={rows_needed_to_aspirational_50k}")
    add_check("required_pages_captured", len(required_failed_attempts) == 0, "critical", f"required_failed={len(required_failed_attempts)}")
    add_check("official_pages_captured_count", captured_page_count >= 4, "critical", f"captured_pages={captured_page_count}")
    add_check("raw_manifest_non_empty", len(manifest) > 0, "critical", f"manifest_rows={len(manifest)}")
    add_check("attempts_recorded", len(attempts) >= len(PAGE_SOURCES), "critical", f"attempts={len(attempts)}")
    add_check("discovered_links_recorded", len(discovered_links) > 0, "warning", f"discovered_links={len(discovered_links)}")
    add_check("discovered_download_candidates_recorded", discovered_download_candidate_count > 0, "warning", f"download_candidates={discovered_download_candidate_count}")
    add_check("structured_download_captured", captured_download_count > 0, "warning", f"captured_downloads={captured_download_count}")
    add_check("csv_or_xls_captured", captured_csv_count + captured_xls_count > 0, "warning", f"csv={captured_csv_count};xls={captured_xls_count}")
    add_check("legacy_csv_failure_non_critical", True, "warning", f"legacy_csv_status={legacy_csv_status}")
    add_check("raw_acquisition_only", True, "critical", "raw acquisition only")
    add_check("network_download_performed", len(attempts) > 0, "critical", f"network_attempts={len(attempts)}")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("candidate_validation_not_performed", True, "critical", "candidate_validation_against_canonical_performed=False")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("expanded_validation_not_performed", True, "critical", "expanded_validation_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("current_candidate_dataset_not_modified", True, "critical", "current_candidate_dataset_modified=False")
    add_check("hkex_candidate_dataset_not_modified", True, "critical", "hkex_candidate_dataset_modified=False")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed > 0:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW
    elif warning_failed > 0:
        status = STATUS_REVIEW
        recommended_next_phase = NEXT_PHASE
    else:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE

    acquisition_summary = {
        "selected_provider": "ASX",
        "raw_dir": str(RAW_DIR),
        "pages_dir": str(PAGES_DIR),
        "downloads_dir": str(DOWNLOADS_DIR),
        "attempts_total": len(attempts),
        "successful_attempts": len(successful_attempts),
        "failed_attempts": len(failed_attempts),
        "required_failed_attempts": len(required_failed_attempts),
        "manifest_rows": len(manifest),
        "captured_page_count": captured_page_count,
        "captured_download_count": captured_download_count,
        "captured_csv_count": captured_csv_count,
        "captured_xls_count": captured_xls_count,
        "discovered_links_count": len(discovered_links),
        "discovered_download_candidate_count": discovered_download_candidate_count,
        "legacy_csv_status": legacy_csv_status,
        "current_hkex_validated_candidate_rows": hkex_validated_candidate_rows,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "aspirational_target": ASPIRATIONAL_TARGET,
        "rows_needed_to_quality_floor": rows_needed_to_quality_floor,
        "rows_needed_to_quality_ceiling": rows_needed_to_quality_ceiling,
        "rows_needed_to_aspirational_50k": rows_needed_to_aspirational_50k,
        "critical_failed_checks": critical_failed,
        "warning_failed_checks": warning_failed,
        "next_phase": recommended_next_phase,
        "full59k": "DEPRECATED_DEFERRED",
    }

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "ASX",
            "action": "run_asx_raw_validation",
            "priority": "high",
            "reason": "Raw ASX pages/download attempts have been captured; validation should assess parse readiness and repair needs.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "validate raw only; no candidate extraction; no canonical replacement; no scoring",
        },
        {
            "action_order": 2,
            "action_scope": "ASX_download_repair",
            "action": "repair_complete_list_csv_route_if_needed",
            "priority": "medium",
            "reason": "The legacy ASXListedCompanies.csv endpoint may fail; raw validation should decide whether page discovery or another official route is required.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "repair source route only if raw validation shows missing structured candidate source",
        },
        {
            "action_order": 3,
            "action_scope": "quality_target",
            "action": "preserve_42k_45k_operational_band",
            "priority": "high",
            "reason": "Only 608 clean net-new rows are needed to cross 42k; do not add noisy rows for volume.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "50k aspirational only; full59k deprecated",
        },
    ]

    write_csv(MANIFEST_CSV, manifest, ["source_id", "url", "expected_role", "required", "capture_type", "status_code", "content_type", "bytes", "sha256", "path", "captured_at_utc"])
    write_csv(ATTEMPTS_CSV, attempts, ["source_id", "url", "expected_role", "required", "started_at_utc", "finished_at_utc", "success", "status_code", "content_type", "bytes", "sha256", "output_path", "error_type", "error"])
    write_csv(DISCOVERED_LINKS_CSV, discovered_links, ["discovered_from_source_id", "discovered_from_path", "url", "netloc", "path", "query", "extension_hint", "structured_candidate", "download_candidate"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "acquisition_summary": acquisition_summary,
        "page_sources": PAGE_SOURCES,
        "direct_download_candidates": DIRECT_DOWNLOAD_CANDIDATES,
        "manifest": manifest,
        "attempts": attempts,
        "discovered_links": discovered_links,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "raw_acquisition_only": True,
            "selected_provider": "ASX",
            "operational_target_floor": QUALITY_FLOOR_TARGET,
            "operational_target_ceiling": QUALITY_CEILING_TARGET,
            "aspirational_target_50000_retained": True,
            "network_download_performed": True,
            "endpoint_calls_performed": True,
            "query_sweep_performed": False,
            "raw_acquisition_performed": True,
            "raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": current_candidate_sha_before == current_candidate_sha_after,
            "hkex_validated_candidate_dataset_read": True,
            "hkex_validated_candidate_dataset_modified": False,
            "hkex_validated_candidate_sha_unchanged": hkex_validated_candidate_sha_before == hkex_validated_candidate_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    manifest_lines = "\n".join(
        f"- `{row['source_id']}` — `{row['status_code']}` — `{row['bytes']}` bytes — `{row['path']}`"
        for row in manifest
    ) or "- No raw files captured."

    attempt_lines = "\n".join(
        f"- `{row['source_id']}` — {'OK' if row['success'] else 'FAIL'} — status `{row['status_code']}` — {row['error']}"
        for row in attempts
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

v2.20C captures ASX raw official sources for the quality-first route.

This phase performs raw acquisition only. It captures HTML pages and direct/download-discovered files where available. It does not extract candidate rows, does not validate candidates against canonical, does not rebuild a candidate dataset, does not promote any dataset to canonical, and does not run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

The current validated HKEX candidate dataset remains **{hkex_validated_candidate_rows:,}** rows. The operational target band remains **{QUALITY_FLOOR_TARGET:,}–{QUALITY_CEILING_TARGET:,}**. Only **{rows_needed_to_quality_floor:,}** clean net-new rows are needed to cross 42k.

## Acquisition summary

- Selected provider: `ASX`
- Raw directory: `{RAW_DIR}`
- Attempts total: `{len(attempts)}`
- Successful attempts: `{len(successful_attempts)}`
- Failed attempts: `{len(failed_attempts)}`
- Required failed attempts: `{len(required_failed_attempts)}`
- Manifest rows: `{len(manifest)}`
- Captured pages: `{captured_page_count}`
- Captured downloads: `{captured_download_count}`
- Captured CSV files: `{captured_csv_count}`
- Captured XLS/XLSX files: `{captured_xls_count}`
- Discovered links: `{len(discovered_links)}`
- Discovered download candidates: `{discovered_download_candidate_count}`
- Legacy CSV status: `{legacy_csv_status}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`
- full59k: `DEPRECATED_DEFERRED`

## Raw manifest

{manifest_lines}

## Attempts

{attempt_lines}

## Checks

{check_lines}

## Next actions

{next_action_lines}

## Guards

- Raw acquisition only: true
- Network download performed: true
- Raw validation performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild performed: false
- Expanded validation performed: false
- Canonical dataset modified: false
- Current candidate dataset modified: false
- HKEX candidate dataset modified: false
- Active canonical replaced: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- full59k target deprecated: true
- full59k universe launched: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.20C ASX quality-first raw acquisition completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("ACQUISITION_SUMMARY:")
    for key, value in acquisition_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("ATTEMPTS:")
    for row in attempts:
        print(f"- {row['source_id']}: {'OK' if row['success'] else 'FAIL'} status={row['status_code']} bytes={row['bytes']} error={row['error']}")
    print("")
    print("MANIFEST:")
    for row in manifest:
        print(f"- {row['source_id']}: {row['path']} bytes={row['bytes']} sha={row['sha256']}")
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
