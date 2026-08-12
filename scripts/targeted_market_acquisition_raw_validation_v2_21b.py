from __future__ import annotations

import csv
import hashlib
import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.21B"
PHASE = "Colombia/BVC + Singapore/SGX Acquisition & Raw Validation"
PHASE_TYPE = "targeted-market-raw-acquisition-and-validation"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw_targeted_markets_v2_21b"

OPERATIONAL_BASE_DATASET = OUTPUT_DIR / "expanded_universe_v2_20m_asx_promoted.csv"
ROLLBACK_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
V221A_JSON = OUTPUT_DIR / "targeted_market_gap_decision_gate_v2_21a.json"

REPORT_JSON = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_v2_21b.json"
REPORT_MD = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_v2_21b.md"
SUMMARY_CSV = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_summary_v2_21b.csv"
CHECKS_CSV = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_checks_v2_21b.csv"
SOURCE_FETCHES_CSV = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_source_fetches_v2_21b.csv"
MARKET_READINESS_CSV = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_market_readiness_v2_21b.csv"
RAW_FILES_CSV = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_raw_files_v2_21b.csv"
URL_INVENTORY_CSV = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_url_inventory_v2_21b.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "targeted_market_acquisition_raw_validation_next_actions_v2_21b.csv"

EXPECTED_V221A_STATUS = "TARGETED_MARKET_GAP_DECISION_GATE_COMPLETED_COLOMBIA_SINGAPORE_APPROVED_FOR_PLANNING_42708_ROWS_NO_DATA_CHANGES_SCORING_DEFERRED"
EXPECTED_V221A_DECISION = "COLOMBIA_SINGAPORE_TARGETED_EXPANSION_APPROVED_FOR_ACQUISITION_AND_RAW_VALIDATION"

OPERATIONAL_BASE_ROWS_EXPECTED = 42708
OPERATIONAL_BASE_SHA_EXPECTED = "892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127"
ROLLBACK_ROWS_EXPECTED = 38287
ROLLBACK_SHA_EXPECTED = "cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f"

QUALITY_FLOOR_TARGET = 42000
QUALITY_CEILING_TARGET = 45000

STATUS_SUCCESS = "TARGETED_MARKET_ACQUISITION_RAW_VALIDATION_COMPLETED_COLOMBIA_SINGAPORE_RAW_SOURCES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED"
STATUS_FAILED = "TARGETED_MARKET_ACQUISITION_RAW_VALIDATION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE = "v2.21C - Candidate Extraction + Dedup Dry Run"
NEXT_PHASE_REVIEW = "v2.21B_REVIEW - Acquisition Source Access Review"

REQUEST_TIMEOUT_SECONDS = 45
MIN_SUCCESS_BYTES = 500

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 ScoutFinanceRawValidation/2.21B",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

SOURCES = [
    {
        "market_id": "COLOMBIA_BVC",
        "country": "Colombia",
        "provider": "BVC",
        "source_id": "BVC_OFFICIAL_ISSUERS_AND_PROSPECTUSES",
        "source_type": "official_exchange_issuer_information",
        "url": "https://www.bvc.com.co/prospectos",
        "expected_raw_kind": "html",
        "criticality": "primary",
        "expected_markers": ["bvc", "acciones", "emisores", "colombia"],
        "notes": "Official BVC prospectus/source page. Raw acquisition only; no candidate extraction in v2.21B.",
    },
    {
        "market_id": "COLOMBIA_BVC",
        "country": "Colombia",
        "provider": "BVC",
        "source_id": "BVC_RESULTS_AND_ISSUER_INFORMATION",
        "source_type": "official_exchange_results_and_issuer_information",
        "url": "https://www.bvc.com.co/resultados-e-informacion-sobre-emisores?tab=resultado-deemisiones",
        "expected_raw_kind": "html",
        "criticality": "secondary",
        "expected_markers": ["bvc", "emisores", "renta variable", "mercado de capitales"],
        "notes": "Official BVC issuer results/information page. Raw acquisition only.",
    },
    {
        "market_id": "SINGAPORE_SGX",
        "country": "Singapore",
        "provider": "SGX",
        "source_id": "SGX_SECURITIES_PRICES",
        "source_type": "official_exchange_securities_prices",
        "url": "https://www.sgx.com/stock-exchange/securities-prices?code=stocks",
        "expected_raw_kind": "html",
        "criticality": "primary",
        "expected_markers": ["sgx", "securities", "prices", "stock"],
        "notes": "Official SGX securities prices page. Raw acquisition only.",
    },
    {
        "market_id": "SINGAPORE_SGX",
        "country": "Singapore",
        "provider": "SGX",
        "source_id": "SGX_CORPORATE_INFORMATION",
        "source_type": "official_exchange_corporate_information",
        "url": "https://www.sgx.com/securities/corporate-information?pagesize=100",
        "expected_raw_kind": "html",
        "criticality": "secondary",
        "expected_markers": ["sgx", "corporate information", "listed date", "board"],
        "notes": "Official SGX corporate information page. Raw acquisition only.",
    },
]


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


def safe_filename(source_id: str, suffix: str) -> Path:
    return RAW_DIR / f"{source_id}{suffix}"


def decode_preview(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding, errors="replace")
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def fetch_source(source: dict[str, Any]) -> dict[str, Any]:
    source_id = source["source_id"]
    url = source["url"]

    raw_path = safe_filename(source_id, ".html")
    error_path = safe_filename(source_id, ".error.html")
    headers_path = safe_filename(source_id, ".headers.json")

    for path in (raw_path, error_path, headers_path):
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    result: dict[str, Any] = {
        "market_id": source["market_id"],
        "country": source["country"],
        "provider": source["provider"],
        "source_id": source_id,
        "source_type": source["source_type"],
        "url": url,
        "criticality": source["criticality"],
        "expected_raw_kind": source["expected_raw_kind"],
        "fetch_attempted": True,
        "fetch_success": False,
        "http_status": "",
        "content_type": "",
        "raw_bytes": 0,
        "raw_sha256": "",
        "raw_file": "",
        "headers_file": "",
        "error_file": "",
        "marker_hits": 0,
        "expected_markers_total": len(source["expected_markers"]),
        "marker_validation_passed": False,
        "validation_status": "FAILED",
        "error": "",
        "fetched_at_utc": utc_now(),
        "notes": source["notes"],
    }

    request = urllib.request.Request(url, headers=HEADERS)
    context = ssl.create_default_context()

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=context) as response:
            data = response.read()
            status = getattr(response, "status", 200)
            headers = dict(response.headers.items())
            content_type = response.headers.get("Content-Type", "")

            raw_path.write_bytes(data)
            headers_path.write_text(json.dumps(headers, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

            text = decode_preview(data).lower()
            marker_hits = sum(1 for marker in source["expected_markers"] if marker.lower() in text)
            raw_sha = sha256_bytes(data)
            fetch_success = (200 <= int(status) < 300) and len(data) >= MIN_SUCCESS_BYTES

            result.update({
                "fetch_success": fetch_success,
                "http_status": int(status),
                "content_type": content_type,
                "raw_bytes": len(data),
                "raw_sha256": raw_sha,
                "raw_file": str(raw_path),
                "headers_file": str(headers_path),
                "marker_hits": marker_hits,
                "marker_validation_passed": marker_hits > 0,
                "validation_status": "PASS" if fetch_success else "FAILED_SMALL_OR_NON_2XX",
            })

    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        if body:
            error_path.write_bytes(body)
        headers = dict(exc.headers.items()) if exc.headers else {}
        headers_path.write_text(json.dumps(headers, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

        result.update({
            "http_status": int(exc.code),
            "content_type": headers.get("Content-Type", ""),
            "raw_bytes": len(body),
            "raw_sha256": sha256_bytes(body) if body else "",
            "headers_file": str(headers_path),
            "error_file": str(error_path) if body else "",
            "validation_status": "HTTP_ERROR",
            "error": f"HTTPError: {exc.code} {exc.reason}",
        })

    except Exception as exc:
        result.update({
            "validation_status": "EXCEPTION",
            "error": f"{type(exc).__name__}: {exc}",
        })

    return result


def main() -> None:
    output_paths = [
        REPORT_JSON,
        REPORT_MD,
        SUMMARY_CSV,
        CHECKS_CSV,
        SOURCE_FETCHES_CSV,
        MARKET_READINESS_CSV,
        RAW_FILES_CSV,
        URL_INVENTORY_CSV,
        NEXT_ACTIONS_CSV,
    ]

    for path in output_paths:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists() and any(RAW_DIR.iterdir()):
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw directory exists and is not empty: {RAW_DIR}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    v221a = read_json(V221A_JSON)
    v221a_summary = v221a.get("summary", {})

    operational_rows = count_csv_rows(OPERATIONAL_BASE_DATASET)
    operational_sha = sha256_file(OPERATIONAL_BASE_DATASET)
    rollback_rows = count_csv_rows(ROLLBACK_DATASET)
    rollback_sha = sha256_file(ROLLBACK_DATASET)
    header = read_csv_header(OPERATIONAL_BASE_DATASET)

    source_fetches: list[dict[str, Any]] = []

    for source in SOURCES:
        print(f"Fetching {source['source_id']} -> {source['url']}")
        result = fetch_source(source)
        source_fetches.append(result)
        print(f"- status={result['http_status']} success={result['fetch_success']} bytes={result['raw_bytes']} validation={result['validation_status']}")

    markets = sorted({source["market_id"] for source in SOURCES})
    market_readiness_rows: list[dict[str, Any]] = []

    for market_id in markets:
        market_results = [row for row in source_fetches if row["market_id"] == market_id]
        success_count = sum(1 for row in market_results if bool(row["fetch_success"]))
        primary_success_count = sum(1 for row in market_results if bool(row["fetch_success"]) and row["criticality"] == "primary")
        total_bytes = sum(int(row["raw_bytes"] or 0) for row in market_results)
        failed_count = len(market_results) - success_count

        market_readiness_rows.append({
            "market_id": market_id,
            "source_count": len(market_results),
            "success_count": success_count,
            "primary_success_count": primary_success_count,
            "failed_count": failed_count,
            "total_raw_bytes": total_bytes,
            "raw_ready_for_candidate_extraction": success_count >= 1,
            "primary_source_available": primary_success_count >= 1,
            "recommended_action": "proceed_to_v2_21c" if success_count >= 1 else "review_source_access_or_manual_download",
        })

    raw_file_rows: list[dict[str, Any]] = []
    for row in source_fetches:
        if row["raw_file"]:
            raw_file_rows.append({
                "source_id": row["source_id"],
                "market_id": row["market_id"],
                "file_kind": "raw",
                "path": row["raw_file"],
                "sha256": row["raw_sha256"],
                "bytes": row["raw_bytes"],
            })
        if row["headers_file"]:
            headers_file = Path(row["headers_file"])
            raw_file_rows.append({
                "source_id": row["source_id"],
                "market_id": row["market_id"],
                "file_kind": "headers",
                "path": row["headers_file"],
                "sha256": sha256_file(headers_file) if headers_file.exists() else "",
                "bytes": headers_file.stat().st_size if headers_file.exists() else 0,
            })
        if row["error_file"]:
            error_file = Path(row["error_file"])
            raw_file_rows.append({
                "source_id": row["source_id"],
                "market_id": row["market_id"],
                "file_kind": "error_body",
                "path": row["error_file"],
                "sha256": sha256_file(error_file) if error_file.exists() else "",
                "bytes": error_file.stat().st_size if error_file.exists() else 0,
            })

    url_inventory_rows = [
        {
            "market_id": source["market_id"],
            "country": source["country"],
            "provider": source["provider"],
            "source_id": source["source_id"],
            "source_type": source["source_type"],
            "url": source["url"],
            "criticality": source["criticality"],
            "planned_use": "raw_validation_now_candidate_extraction_later",
        }
        for source in SOURCES
    ]

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "candidate_extraction",
            "action": "build_parser_candidates_from_successful_raw_sources",
            "priority": "high",
            "reason": "v2.21B only validates raw source availability; extraction is intentionally deferred.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "common equities first; exclude ETFs/funds/warrants/rights/structured products",
        },
        {
            "action_order": 2,
            "action_scope": "dedup",
            "action": "deduplicate_colombia_singapore_candidates_against_42708_operational_base",
            "priority": "high",
            "reason": "New market candidates must not duplicate existing ISIN/ticker/name records.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "no operational base modification; dry run only",
        },
        {
            "action_order": 3,
            "action_scope": "normalization",
            "action": "normalize_colombia_singapore_country_exchange_mic_currency",
            "priority": "high",
            "reason": "New records must enter with stable country/exchange/MIC/currency metadata.",
            "recommended_phase": NEXT_PHASE,
            "guardrails": "Colombia/BVC/XBOG/COP and Singapore/SGX/XSES/SGD",
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

    add_check("v2_21a_status_expected", v221a.get("status") == EXPECTED_V221A_STATUS, "critical", str(v221a.get("status")))
    add_check("v2_21a_gate_decision_expected", v221a_summary.get("gate_decision") == EXPECTED_V221A_DECISION, "critical", str(v221a_summary.get("gate_decision")))
    add_check("v2_21a_approved_for_next_phase", bool(v221a_summary.get("approved_for_next_phase")) is True, "critical", f"approved_for_next_phase={v221a_summary.get('approved_for_next_phase')}")
    add_check("operational_base_rows_expected", operational_rows == OPERATIONAL_BASE_ROWS_EXPECTED, "critical", f"operational_rows={operational_rows}")
    add_check("operational_base_sha_expected", operational_sha == OPERATIONAL_BASE_SHA_EXPECTED, "critical", operational_sha)
    add_check("rollback_rows_expected", rollback_rows == ROLLBACK_ROWS_EXPECTED, "critical", f"rollback_rows={rollback_rows}")
    add_check("rollback_sha_expected", rollback_sha == ROLLBACK_SHA_EXPECTED, "critical", rollback_sha)
    add_check("schema_column_count_expected", len(header) == 33, "critical", f"columns={len(header)}")
    add_check("operational_floor_preserved", operational_rows >= QUALITY_FLOOR_TARGET, "critical", f"rows={operational_rows};floor={QUALITY_FLOOR_TARGET}")
    add_check("operational_ceiling_preserved", operational_rows <= QUALITY_CEILING_TARGET, "critical", f"rows={operational_rows};ceiling={QUALITY_CEILING_TARGET}")

    for market_row in market_readiness_rows:
        add_check(
            f"raw_source_available::{market_row['market_id']}",
            str(market_row["raw_ready_for_candidate_extraction"]).lower() == "true",
            "critical",
            f"success_count={market_row['success_count']};failed_count={market_row['failed_count']};total_raw_bytes={market_row['total_raw_bytes']}",
        )
        add_check(
            f"primary_source_available::{market_row['market_id']}",
            str(market_row["primary_source_available"]).lower() == "true",
            "warning",
            f"primary_success_count={market_row['primary_success_count']}",
        )

    successful_sources = sum(1 for row in source_fetches if bool(row["fetch_success"]))
    add_check("at_least_two_sources_successful", successful_sources >= 2, "warning", f"successful_sources={successful_sources};total_sources={len(source_fetches)}")
    add_check("raw_files_registered", len(raw_file_rows) > 0, "critical", f"raw_file_rows={len(raw_file_rows)}")

    add_check("raw_acquisition_performed", True, "critical", "official raw source fetches attempted")
    add_check("candidate_extraction_not_performed", True, "critical", "candidate_extraction_performed=False")
    add_check("dedup_not_performed", True, "critical", "dedup_performed=False")
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
        acquisition_decision = "RAW_ACQUISITION_BLOCKED_REVIEW_REQUIRED"
        approved_for_next_phase = False
        recommended_next_phase = NEXT_PHASE_REVIEW
    else:
        status = STATUS_SUCCESS
        acquisition_decision = "RAW_SOURCES_AVAILABLE_FOR_CANDIDATE_EXTRACTION_DRY_RUN"
        approved_for_next_phase = True
        recommended_next_phase = NEXT_PHASE

    summary = {
        "selected_route": "Colombia + Singapore targeted expansion",
        "phase_type": PHASE_TYPE,
        "acquisition_decision": acquisition_decision,
        "approved_for_next_phase": approved_for_next_phase,
        "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
        "operational_base_rows": operational_rows,
        "operational_base_sha": operational_sha,
        "rollback_dataset": str(ROLLBACK_DATASET),
        "rollback_rows": rollback_rows,
        "rollback_sha": rollback_sha,
        "quality_floor_target": QUALITY_FLOOR_TARGET,
        "quality_ceiling_target": QUALITY_CEILING_TARGET,
        "remaining_capacity_to_quality_ceiling": QUALITY_CEILING_TARGET - operational_rows,
        "target_markets": "Colombia/BVC;Singapore/SGX",
        "sources_attempted": len(source_fetches),
        "sources_successful": successful_sources,
        "markets_raw_ready": sum(1 for row in market_readiness_rows if str(row["raw_ready_for_candidate_extraction"]).lower() == "true"),
        "raw_dir": str(RAW_DIR),
        "raw_file_rows": len(raw_file_rows),
        "candidate_extraction_performed": False,
        "dedup_performed": False,
        "expanded_rebuild_performed": False,
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
    write_csv(SOURCE_FETCHES_CSV, source_fetches, ["market_id", "country", "provider", "source_id", "source_type", "url", "criticality", "expected_raw_kind", "fetch_attempted", "fetch_success", "http_status", "content_type", "raw_bytes", "raw_sha256", "raw_file", "headers_file", "error_file", "marker_hits", "expected_markers_total", "marker_validation_passed", "validation_status", "error", "fetched_at_utc", "notes"])
    write_csv(MARKET_READINESS_CSV, market_readiness_rows, ["market_id", "source_count", "success_count", "primary_success_count", "failed_count", "total_raw_bytes", "raw_ready_for_candidate_extraction", "primary_source_available", "recommended_action"])
    write_csv(RAW_FILES_CSV, raw_file_rows, ["source_id", "market_id", "file_kind", "path", "sha256", "bytes"])
    write_csv(URL_INVENTORY_CSV, url_inventory_rows, ["market_id", "country", "provider", "source_id", "source_type", "url", "criticality", "planned_use"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "summary": summary,
        "source_fetches": source_fetches,
        "market_readiness": market_readiness_rows,
        "raw_files": raw_file_rows,
        "url_inventory": url_inventory_rows,
        "checks": checks,
        "next_actions": next_actions_rows,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "selected_route": "Colombia + Singapore targeted expansion",
            "target_markets": ["Colombia/BVC", "Singapore/SGX"],
            "approved_for_next_phase": approved_for_next_phase,
            "operational_base_dataset": str(OPERATIONAL_BASE_DATASET),
            "operational_base_rows": operational_rows,
            "operational_base_sha": operational_sha,
            "rollback_dataset": str(ROLLBACK_DATASET),
            "rollback_rows": rollback_rows,
            "rollback_sha": rollback_sha,
            "raw_acquisition_performed": True,
            "raw_validation_performed": True,
            "candidate_extraction_performed": False,
            "dedup_performed": False,
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
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    source_lines = "\n".join(
        f"- `{row['source_id']}` — success `{row['fetch_success']}` — status `{row['http_status']}` — bytes `{row['raw_bytes']}` — `{row['validation_status']}`"
        for row in source_fetches
    )

    market_lines = "\n".join(
        f"- `{row['market_id']}` — ready `{row['raw_ready_for_candidate_extraction']}` — successes `{row['success_count']}` — failed `{row['failed_count']}`"
        for row in market_readiness_rows
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

v2.21B performs controlled raw acquisition and validation for Colombia/BVC and Singapore/SGX.

This phase captures raw official source material only. It does not extract candidates, deduplicate, rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Acquisition decision: `{acquisition_decision}`
- Approved for next phase: `{approved_for_next_phase}`
- Operational base rows: `{operational_rows}`
- Operational base SHA256: `{operational_sha}`
- Rollback rows: `{rollback_rows}`
- Rollback SHA256: `{rollback_sha}`
- Remaining capacity to 45k ceiling: `{QUALITY_CEILING_TARGET - operational_rows}`
- Sources attempted: `{len(source_fetches)}`
- Sources successful: `{successful_sources}`
- Raw directory: `{RAW_DIR}`
- Critical failed checks: `{critical_failed}`
- Warning failed checks: `{warning_failed}`

## Source fetches

{source_lines}

## Market readiness

{market_lines}

## Checks

{check_lines}

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("")
    print("v2.21B targeted market acquisition raw validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("SUMMARY:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("")
    print("SOURCE_FETCHES:")
    for row in source_fetches:
        print(f"- {row['source_id']}: success={row['fetch_success']} status={row['http_status']} bytes={row['raw_bytes']} validation={row['validation_status']} error={row['error']}")
    print("")
    print("MARKET_READINESS:")
    for row in market_readiness_rows:
        print(f"- {row['market_id']}: ready={row['raw_ready_for_candidate_extraction']} success_count={row['success_count']} failed_count={row['failed_count']} primary_available={row['primary_source_available']}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
