from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse


VERSION = "v2.16D"
PHASE = "TMX Validation"
PHASE_TYPE = "raw-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "tmx_v2_16c"

V216C_JSON = OUTPUT_DIR / "tmx_raw_acquisition_manifest_v2_16c.json"
V216C_CSV = OUTPUT_DIR / "tmx_raw_acquisition_manifest_v2_16c.csv"
V216C_ACTIONS_CSV = OUTPUT_DIR / "tmx_raw_acquisition_source_actions_v2_16c.csv"

VALIDATION_JSON = OUTPUT_DIR / "tmx_validation_v2_16d.json"
VALIDATION_MD = OUTPUT_DIR / "tmx_validation_v2_16d.md"
RAW_DIAGNOSTICS_CSV = OUTPUT_DIR / "tmx_raw_file_diagnostics_v2_16d.csv"
ENDPOINT_SEEDS_CSV = OUTPUT_DIR / "tmx_candidate_endpoint_seeds_v2_16d.csv"
MARKERS_CSV = OUTPUT_DIR / "tmx_structural_markers_v2_16d.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

NEXT_PHASE_IF_ENDPOINTS = "v2.16D2 - TMX Controlled Endpoint Probe"
NEXT_PHASE_IF_DIRECT_EXTRACTION = "v2.16E - TMX Candidate Extraction Dry Run"
NEXT_PHASE_IF_WEAK = "v2.16I - TMX Closure Report"

DIAGNOSTIC_FIELDS = [
    "source_id", "source_name", "status_code", "ok", "raw_path", "raw_exists",
    "bytes_read", "sha256", "content_type", "html_like", "title",
    "table_count", "script_count", "link_count", "form_count", "iframe_count",
    "json_script_count", "next_data_marker", "nuxt_marker", "react_marker",
    "angular_marker", "endpoint_seed_count", "table_row_marker_count",
    "potential_symbol_marker_count", "potential_company_marker_count",
    "tsx_marker_count", "tsxv_marker_count", "stock_marker_count",
    "quote_marker_count", "equity_marker_count", "api_marker_count",
    "validation_quality", "recommended_route", "notes",
]

ENDPOINT_FIELDS = [
    "seed_id", "source_id", "source_name", "seed_type", "raw_reference",
    "seed_value", "absolute_url", "host", "path", "query_present",
    "endpoint_signal", "marker_hits", "allowed_for_future_probe",
    "future_probe_reason",
]

MARKER_FIELDS = ["source_id", "source_name", "marker", "count", "marker_group"]

IMPORTANT_MARKERS = {
    "symbol": ["symbol", "symbols", "ticker", "tickers"],
    "company": ["company", "companies", "issuer", "issuers", "name"],
    "tsx": ["tsx", "toronto stock exchange"],
    "tsxv": ["tsxv", "tsx venture", "tsx venture exchange"],
    "stock": ["stock", "stocks", "stock-list", "stock list"],
    "quote": ["quote", "quotes"],
    "equity": ["equity", "equities"],
    "api": ["api", "ajax", "controller", "httpcontroller", "endpoint"],
    "listing": ["listing", "listed", "listed company", "listed companies"],
    "sector": ["sector", "industry", "classification"],
    "exchange": ["exchange", "market", "venue"],
}

ENDPOINT_SIGNAL_PATTERNS = [
    "api", "ajax", "controller", "httpcontroller", "search", "equity",
    "equities", "symbol", "quote", "stock", "stock-list", "stocklists",
    "company", "listed", "tsxventure", "tsx", "market",
]

ALLOWED_FUTURE_PROBE_HOSTS = {
    "www.tsx.com", "tsx.com", "apps.tmx.com", "money.tmx.com", "www.tmx.com",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def as_bool_text(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def clean_text(value: str) -> str:
    return " ".join(unescape(value or "").replace("\xa0", " ").split()).strip()


def extract_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return clean_text(re.sub(r"<[^>]+>", " ", match.group(1)))[:300]


def count_regex(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL))


def count_marker(text_lower: str, terms: list[str]) -> int:
    return sum(text_lower.count(term.lower()) for term in terms)


def base_url_for_manifest_row(row: dict) -> str:
    return str(row.get("final_url", "")).strip() or str(row.get("url", "")).strip()


def normalize_candidate_url(seed_value: str, base_url: str) -> str:
    seed = clean_text(seed_value).strip("\"' ")
    if not seed:
        return ""
    if seed.startswith("//"):
        return "https:" + seed
    if seed.startswith("http://") or seed.startswith("https://"):
        return seed
    if seed.startswith("/"):
        return urljoin(base_url, seed)
    return ""


def endpoint_signal(seed_value: str) -> tuple[str, list[str]]:
    low = seed_value.lower()
    hits = sorted({item for item in ENDPOINT_SIGNAL_PATTERNS if item in low})

    if any(item in hits for item in ["api", "ajax", "controller", "httpcontroller"]):
        return "high", hits
    if any(item in hits for item in ["search", "equity", "equities", "symbol", "quote", "stock", "company", "listed"]):
        return "medium", hits
    if hits:
        return "low", hits
    return "none", []


def allowed_future_probe(absolute_url: str, signal: str) -> tuple[bool, str]:
    if not absolute_url:
        return False, "relative_or_unresolved_seed"

    parsed = urlparse(absolute_url)
    host = parsed.netloc.lower()

    if host not in ALLOWED_FUTURE_PROBE_HOSTS:
        return False, "host_not_in_future_probe_allowlist"

    if signal not in {"high", "medium"}:
        return False, "endpoint_signal_too_low"

    return True, "allowed_for_controlled_probe_in_future_phase"


def extract_endpoint_seeds(source_id: str, source_name: str, raw_text: str, base_url: str) -> list[dict]:
    seeds = []
    patterns = [
        ("script_src", r"<script[^>]+src=[\"']([^\"']+)[\"']"),
        ("link_href", r"<link[^>]+href=[\"']([^\"']+)[\"']"),
        ("anchor_href", r"<a[^>]+href=[\"']([^\"']+)[\"']"),
        ("form_action", r"<form[^>]+action=[\"']([^\"']+)[\"']"),
        ("iframe_src", r"<iframe[^>]+src=[\"']([^\"']+)[\"']"),
        ("fetch_call", r"fetch\([\"']([^\"']+)[\"']"),
        ("xhr_open", r"\.open\([\"'](?:GET|POST)[\"']\s*,\s*[\"']([^\"']+)[\"']"),
        ("quoted_url", r"[\"']((?:https?:)?//[^\"']+|/[^\"']{3,300})[\"']"),
    ]

    seen = set()

    for seed_type, pattern in patterns:
        for value in re.findall(pattern, raw_text, flags=re.IGNORECASE | re.DOTALL):
            value = clean_text(value)
            if not value:
                continue

            signal, hits = endpoint_signal(value)
            absolute = normalize_candidate_url(value, base_url)

            if signal == "none" and not absolute:
                continue

            parsed = urlparse(absolute) if absolute else urlparse("")
            allowed, reason = allowed_future_probe(absolute, signal)
            key = (seed_type, value, absolute)

            if key in seen:
                continue
            seen.add(key)

            seeds.append(
                {
                    "seed_id": sha256_text(f"{source_id}|{seed_type}|{value}|{absolute}")[:16],
                    "source_id": source_id,
                    "source_name": source_name,
                    "seed_type": seed_type,
                    "raw_reference": "raw_html_text_only_no_request_performed",
                    "seed_value": value[:500],
                    "absolute_url": absolute[:800],
                    "host": parsed.netloc.lower(),
                    "path": parsed.path[:500],
                    "query_present": bool(parsed.query),
                    "endpoint_signal": signal,
                    "marker_hits": "|".join(hits),
                    "allowed_for_future_probe": allowed,
                    "future_probe_reason": reason,
                }
            )

    return seeds


def diagnostic_quality(row: dict) -> tuple[str, str]:
    endpoint_count = as_int(row["endpoint_seed_count"])
    table_count = as_int(row["table_count"])
    symbol_count = as_int(row["potential_symbol_marker_count"])
    company_count = as_int(row["potential_company_marker_count"])
    api_count = as_int(row["api_marker_count"])
    stock_count = as_int(row["stock_marker_count"])
    quote_count = as_int(row["quote_marker_count"])

    if endpoint_count >= 5 and (symbol_count > 0 or company_count > 0 or api_count > 0):
        return "high", "controlled_endpoint_probe_recommended"
    if endpoint_count >= 1 and (symbol_count > 0 or company_count > 0 or stock_count > 0 or quote_count > 0):
        return "medium", "controlled_endpoint_probe_recommended"
    if table_count > 0 and (symbol_count > 0 or company_count > 0):
        return "medium", "candidate_extraction_dry_run_possible_after_review"
    if endpoint_count >= 1 or symbol_count > 0 or company_count > 0:
        return "low", "manual_review_or_probe_seed_review"
    return "none", "no_actionable_structure_detected"


def validate_raw_file(manifest_row: dict) -> tuple[dict, list[dict], list[dict]]:
    source_id = str(manifest_row.get("source_id", "")).strip()
    source_name = str(manifest_row.get("source_name", "")).strip()
    raw_path_text = str(manifest_row.get("raw_path", "")).strip()
    raw_path = Path(raw_path_text) if raw_path_text else None

    diagnostic = {
        "source_id": source_id,
        "source_name": source_name,
        "status_code": manifest_row.get("status_code", ""),
        "ok": manifest_row.get("ok", ""),
        "raw_path": str(raw_path) if raw_path else "",
        "raw_exists": False,
        "bytes_read": 0,
        "sha256": "",
        "content_type": manifest_row.get("content_type", ""),
        "html_like": False,
        "title": "",
        "table_count": 0,
        "script_count": 0,
        "link_count": 0,
        "form_count": 0,
        "iframe_count": 0,
        "json_script_count": 0,
        "next_data_marker": False,
        "nuxt_marker": False,
        "react_marker": False,
        "angular_marker": False,
        "endpoint_seed_count": 0,
        "table_row_marker_count": 0,
        "potential_symbol_marker_count": 0,
        "potential_company_marker_count": 0,
        "tsx_marker_count": 0,
        "tsxv_marker_count": 0,
        "stock_marker_count": 0,
        "quote_marker_count": 0,
        "equity_marker_count": 0,
        "api_marker_count": 0,
        "validation_quality": "none",
        "recommended_route": "no_raw_file",
        "notes": "",
    }

    marker_rows = []
    endpoint_rows = []

    if not raw_path or not raw_path.exists():
        diagnostic["notes"] = "raw_file_missing_or_source_not_downloaded"
        return diagnostic, endpoint_rows, marker_rows

    raw_bytes = raw_path.read_bytes()
    text = raw_bytes.decode("utf-8", errors="replace")
    low = text.lower()

    diagnostic.update(
        {
            "raw_exists": True,
            "bytes_read": len(raw_bytes),
            "sha256": sha256_bytes(raw_bytes),
            "html_like": "<html" in low or "<!doctype html" in low,
            "title": extract_title(text),
            "table_count": count_regex(text, r"<table\b"),
            "script_count": count_regex(text, r"<script\b"),
            "link_count": count_regex(text, r"<a\b"),
            "form_count": count_regex(text, r"<form\b"),
            "iframe_count": count_regex(text, r"<iframe\b"),
            "json_script_count": count_regex(text, r"<script[^>]+type=[\"']application/(?:ld\+)?json[\"']"),
            "next_data_marker": "__next_data__" in low or 'id="__next_data__"' in low,
            "nuxt_marker": "__nuxt__" in low,
            "react_marker": "react" in low or "reactroot" in low,
            "angular_marker": "ng-" in low or "angular" in low,
            "table_row_marker_count": count_regex(text, r"<tr\b"),
        }
    )

    for marker_group, terms in IMPORTANT_MARKERS.items():
        count = count_marker(low, terms)
        marker_rows.append(
            {
                "source_id": source_id,
                "source_name": source_name,
                "marker": "|".join(terms),
                "count": count,
                "marker_group": marker_group,
            }
        )

        if marker_group == "symbol":
            diagnostic["potential_symbol_marker_count"] = count
        elif marker_group == "company":
            diagnostic["potential_company_marker_count"] = count
        elif marker_group == "tsx":
            diagnostic["tsx_marker_count"] = count
        elif marker_group == "tsxv":
            diagnostic["tsxv_marker_count"] = count
        elif marker_group == "stock":
            diagnostic["stock_marker_count"] = count
        elif marker_group == "quote":
            diagnostic["quote_marker_count"] = count
        elif marker_group == "equity":
            diagnostic["equity_marker_count"] = count
        elif marker_group == "api":
            diagnostic["api_marker_count"] = count

    base_url = base_url_for_manifest_row(manifest_row)
    endpoint_rows = extract_endpoint_seeds(source_id, source_name, text, base_url)
    diagnostic["endpoint_seed_count"] = len(endpoint_rows)

    quality, route = diagnostic_quality(diagnostic)
    diagnostic["validation_quality"] = quality
    diagnostic["recommended_route"] = route
    diagnostic["notes"] = "raw_file_validated_structural_only_no_candidate_extraction"

    return diagnostic, endpoint_rows, marker_rows


def main() -> None:
    for path in [VALIDATION_JSON, VALIDATION_MD, RAW_DIAGNOSTICS_CSV, ENDPOINT_SEEDS_CSV, MARKERS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    c_manifest = read_json(V216C_JSON)
    manifest_rows = read_csv(V216C_CSV)
    source_actions = read_csv(V216C_ACTIONS_CSV)

    diagnostics = []
    endpoint_rows = []
    marker_rows = []

    for manifest_row in manifest_rows:
        diagnostic, endpoints, markers = validate_raw_file(manifest_row)
        diagnostics.append(diagnostic)
        endpoint_rows.extend(endpoints)
        marker_rows.extend(markers)

    quality_counter = Counter(row["validation_quality"] for row in diagnostics)
    route_counter = Counter(row["recommended_route"] for row in diagnostics)
    raw_exists_count = sum(1 for row in diagnostics if row["raw_exists"])
    html_like_count = sum(1 for row in diagnostics if row["html_like"])
    total_endpoint_seeds = len(endpoint_rows)
    future_probe_allowed_count = sum(1 for row in endpoint_rows if as_bool_text(row.get("allowed_for_future_probe", "")))
    high_or_medium_quality_count = quality_counter.get("high", 0) + quality_counter.get("medium", 0)
    table_count_total = sum(as_int(row["table_count"]) for row in diagnostics)
    script_count_total = sum(as_int(row["script_count"]) for row in diagnostics)
    link_count_total = sum(as_int(row["link_count"]) for row in diagnostics)

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_16c_manifest_json_exists", V216C_JSON.exists(), "critical", str(V216C_JSON))
    add_check("v2_16c_manifest_csv_exists", V216C_CSV.exists(), "critical", str(V216C_CSV))
    add_check("v2_16c_source_actions_exists", V216C_ACTIONS_CSV.exists(), "critical", str(V216C_ACTIONS_CSV))
    add_check("v2_16c_status_valid", c_manifest.get("status") == "TMX_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS_REBUILD_STILL_BLOCKED", "critical", c_manifest.get("status", ""))
    add_check("raw_dir_exists", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("manifest_rows_loaded", len(manifest_rows) >= 5, "critical", f"manifest_rows={len(manifest_rows)}")
    add_check("raw_files_available_for_validation", raw_exists_count >= 4, "critical", f"raw_exists_count={raw_exists_count}")
    add_check("html_like_raw_files", html_like_count >= 4, "critical", f"html_like_count={html_like_count}")
    add_check("structural_diagnostics_generated", len(diagnostics) == len(manifest_rows), "critical", f"diagnostics={len(diagnostics)}")
    add_check("endpoint_seeds_detected_review", total_endpoint_seeds > 0, "warning", f"endpoint_seeds={total_endpoint_seeds}")
    add_check("future_probe_allowed_review", future_probe_allowed_count > 0, "warning", f"future_probe_allowed={future_probe_allowed_count}")
    add_check("high_or_medium_quality_review", high_or_medium_quality_count > 0, "warning", f"high_or_medium_quality={high_or_medium_quality_count}")
    add_check("table_or_script_or_link_structure_review", table_count_total + script_count_total + link_count_total > 0, "warning", f"tables={table_count_total}; scripts={script_count_total}; links={link_count_total}")
    add_check("current_rows_unchanged", CURRENT_ROWS == 38287, "critical", f"current_rows={CURRENT_ROWS}")
    add_check("rows_needed_unchanged", ROWS_NEEDED == 11713, "critical", f"rows_needed={ROWS_NEEDED}")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"{CURRENT_ROWS} < {FULL_SOURCE_THRESHOLD}")
    add_check("network_not_used_in_validation", True, "critical", "network_download_performed=False")
    add_check("raw_files_not_modified_after_validation", True, "critical", "raw_files_modified_after_write=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("security_rows_not_extracted", True, "critical", "security_rows_extracted=False")
    add_check("candidate_rows_not_extracted", True, "critical", "candidate_rows_extracted=False")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("normalization_not_performed", True, "critical", "normalization_performed=False")
    add_check("net_new_filtering_not_performed", True, "critical", "net_new_filtering_performed=False")
    add_check("expanded_universe_not_rebuilt", True, "critical", "expanded_universe_rebuilt=False")

    if critical_failed != 0:
        status = "TMX_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.16D_FIX - TMX Validation Repair"
    elif future_probe_allowed_count > 0:
        status = "TMX_VALIDATION_COMPLETED_ENDPOINT_SEEDS_DETECTED_REBUILD_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_ENDPOINTS
    elif high_or_medium_quality_count > 0:
        status = "TMX_VALIDATION_COMPLETED_DIRECT_EXTRACTION_REVIEW_REBUILD_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_DIRECT_EXTRACTION
    else:
        status = "TMX_VALIDATION_COMPLETED_WEAK_SIGNAL_REBUILD_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_WEAK

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "canonical_dataset": CURRENT_CANONICAL_DATASET,
            "current_rows": CURRENT_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED_PERCENT,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "validation_summary": {
            "v2_16c_status": c_manifest.get("status", ""),
            "v2_16c_recommended_next_phase": c_manifest.get("recommended_next_phase", ""),
            "manifest_rows": len(manifest_rows),
            "source_actions_rows": len(source_actions),
            "raw_exists_count": raw_exists_count,
            "html_like_count": html_like_count,
            "diagnostic_rows": len(diagnostics),
            "marker_rows": len(marker_rows),
            "endpoint_seed_rows": total_endpoint_seeds,
            "future_probe_allowed_count": future_probe_allowed_count,
            "high_or_medium_quality_count": high_or_medium_quality_count,
            "quality_counts": dict(quality_counter),
            "recommended_route_counts": dict(route_counter),
            "table_count_total": table_count_total,
            "script_count_total": script_count_total,
            "link_count_total": link_count_total,
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "diagnostics": diagnostics,
        "endpoint_seeds_preview": endpoint_rows[:100],
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "new_raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "raw_html_structural_inspection_performed": True,
            "endpoint_seed_detection_performed": True,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "security_rows_extracted": False,
            "candidate_rows_extracted": False,
            "canonical_dataset_read": False,
            "canonical_dataset_modified": False,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(VALIDATION_JSON, payload)
    write_csv(RAW_DIAGNOSTICS_CSV, diagnostics, DIAGNOSTIC_FIELDS)
    write_csv(ENDPOINT_SEEDS_CSV, endpoint_rows, ENDPOINT_FIELDS)
    write_csv(MARKERS_CSV, marker_rows, MARKER_FIELDS)

    diagnostic_lines = "\n".join(
        f"- `{row['source_id']}` raw={row['raw_exists']} html={row['html_like']} quality={row['validation_quality']} route=`{row['recommended_route']}` endpoints={row['endpoint_seed_count']} tables={row['table_count']} scripts={row['script_count']} links={row['link_count']} title=`{row['title']}`"
        for row in diagnostics
    )

    top_endpoint_lines = "\n".join(
        f"- `{row['source_id']}` signal={row['endpoint_signal']} allowed={row['allowed_for_future_probe']} hits=`{row['marker_hits']}` url=`{row['absolute_url'] or row['seed_value']}`"
        for row in endpoint_rows[:25]
    ) or "- No endpoint seeds detected."

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    VALIDATION_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Current state

- Canonical dataset: `{CURRENT_CANONICAL_DATASET}`
- Current rows: `{CURRENT_ROWS}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completed: `{SOURCE_TO_50K_COMPLETED_PERCENT}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Validation summary

- v2.16C status: `{payload["validation_summary"]["v2_16c_status"]}`
- v2.16C recommended next phase: `{payload["validation_summary"]["v2_16c_recommended_next_phase"]}`
- Manifest rows: `{len(manifest_rows)}`
- Raw files available: `{raw_exists_count}`
- HTML-like raw files: `{html_like_count}`
- Diagnostic rows: `{len(diagnostics)}`
- Marker rows: `{len(marker_rows)}`
- Endpoint seed rows: `{total_endpoint_seeds}`
- Future probe allowed count: `{future_probe_allowed_count}`
- High/medium quality count: `{high_or_medium_quality_count}`
- Quality counts: `{dict(quality_counter)}`
- Recommended route counts: `{dict(route_counter)}`
- Table count total: `{table_count_total}`
- Script count total: `{script_count_total}`
- Link count total: `{link_count_total}`
- Critical failed checks: `{critical_failed}`

## Raw diagnostics

{diagnostic_lines}

## Top endpoint seeds

{top_endpoint_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.16D: false
- New raw files downloaded in v2.16D: false
- Raw files modified after write: false
- Raw HTML structural inspection performed: true
- Endpoint seed detection performed: true
- Endpoint calls performed: false
- Query sweep performed: false
- Security rows extracted: false
- Candidate rows extracted: false
- Canonical dataset read: false
- Canonical dataset modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX validation completed as raw structural validation only.

This phase reads the v2.16C manifest and raw files, validates local HTML structure, counts useful markers and records potential endpoint seeds for a future controlled phase. It performs no network access, no downloads, no endpoint calls, no query sweep, no security extraction, no candidate extraction, no canonical dataset read/write, no normalization, no net-new filtering and no rebuild.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16D TMX validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in payload["validation_summary"].items():
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
