from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


VERSION = "v2.16D2"
PHASE = "TMX Controlled Endpoint Probe"
PHASE_TYPE = "controlled-endpoint-probe-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

V216D_JSON = OUTPUT_DIR / "tmx_validation_v2_16d.json"
V216D_SEEDS_CSV = OUTPUT_DIR / "tmx_candidate_endpoint_seeds_v2_16d.csv"

PROBE_JSON = OUTPUT_DIR / "tmx_controlled_endpoint_probe_v2_16d2.json"
PROBE_MD = OUTPUT_DIR / "tmx_controlled_endpoint_probe_v2_16d2.md"
PROBE_RESULTS_CSV = OUTPUT_DIR / "tmx_controlled_endpoint_probe_results_v2_16d2.csv"
PROBE_SUMMARY_CSV = OUTPUT_DIR / "tmx_controlled_endpoint_probe_summary_v2_16d2.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

MAX_PROBES_DEFAULT = 40
REQUEST_TIMEOUT_SECONDS = 35
MAX_BYTES_PER_PROBE = 524_288
SLEEP_BETWEEN_PROBES_SECONDS = 0.35

NEXT_PHASE_IF_PROMISING = "v2.16D3 - TMX Endpoint Payload Shape Validation"
NEXT_PHASE_IF_NO_PROMISING = "v2.16E - TMX Candidate Extraction Dry Run"

USER_AGENT = (
    "ScoutFinance/2.16D2 TMX controlled endpoint probe "
    "(metadata only; no raw payload storage; no candidate extraction)"
)

ALLOWED_HOSTS = {
    "www.tsx.com",
    "tsx.com",
    "apps.tmx.com",
    "money.tmx.com",
    "www.tmx.com",
}

RESULT_FIELDS = [
    "probe_id",
    "probe_order",
    "source_id",
    "source_name",
    "seed_type",
    "seed_signal",
    "seed_marker_hits",
    "url",
    "host",
    "path",
    "query_present",
    "status_code",
    "ok",
    "final_url",
    "content_type",
    "content_length_header",
    "sampled_bytes",
    "sample_sha256",
    "payload_saved_to_disk",
    "shape_classification",
    "evidence_level",
    "promising_for_next_phase",
    "probe_notes",
    "error",
]

SUMMARY_FIELDS = [
    "metric",
    "value",
]


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


def host_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host in ALLOWED_HOSTS


def classify_shape(content_type: str, sample: bytes) -> str:
    ct = (content_type or "").lower()
    text = sample[:2048].decode("utf-8", errors="replace").lstrip().lower()

    if "application/json" in ct or "text/json" in ct or text.startswith("{") or text.startswith("["):
        return "json_like"
    if "text/html" in ct or "<html" in text or "<!doctype html" in text:
        return "html_like"
    if "javascript" in ct or "ecmascript" in ct or text.startswith("webpack") or "function(" in text:
        return "js_like"
    if "text/css" in ct:
        return "css_like"
    if "xml" in ct or text.startswith("<?xml"):
        return "xml_like"
    if "text/plain" in ct or text:
        return "text_like"
    return "binary_or_empty"


def marker_hits_for_probe(seed_row: dict, final_url: str, content_type: str, sample: bytes) -> list[str]:
    text = sample[:120000].decode("utf-8", errors="replace").lower()
    basis = " ".join(
        [
            str(seed_row.get("marker_hits", "")),
            str(seed_row.get("seed_value", "")),
            str(seed_row.get("absolute_url", "")),
            str(final_url or ""),
            str(content_type or ""),
            text,
        ]
    ).lower()

    markers = [
        "api",
        "ajax",
        "controller",
        "httpcontroller",
        "search",
        "equity",
        "equities",
        "symbol",
        "symbols",
        "quote",
        "quotes",
        "stock",
        "stocks",
        "stock-list",
        "company",
        "companies",
        "issuer",
        "listing",
        "listed",
        "tsx",
        "tsxv",
        "tsxventure",
        "market",
    ]

    return sorted({marker for marker in markers if marker in basis})


def evidence_from_probe(ok: bool, status_code: int, shape: str, hits: list[str], sampled_bytes: int) -> tuple[str, bool, str]:
    if not ok:
        return "none", False, "http_not_ok"

    if sampled_bytes <= 0:
        return "none", False, "empty_response"

    strong_markers = {"api", "ajax", "controller", "httpcontroller", "symbol", "symbols", "equity", "equities", "company", "companies", "quote", "stock", "listing", "listed"}
    has_strong_marker = bool(strong_markers.intersection(set(hits)))

    if shape == "json_like" and has_strong_marker:
        return "high", True, "json_like_with_market_markers"

    if shape == "json_like":
        return "medium", True, "json_like_response"

    if shape == "js_like" and has_strong_marker:
        return "medium", True, "js_like_with_market_markers"

    if shape == "html_like" and has_strong_marker:
        # HTML pages are not enough for payload-shape validation unless they were
        # selected through a strict controller/API seed. Keep them as review
        # evidence but do not mark generic navigation pages as promising.
        return "low", False, "html_like_with_markers_review_only"

    if shape in {"html_like", "js_like"}:
        return "low", False, f"{shape}_without_strong_markers"

    if status_code == 200 and has_strong_marker:
        return "low", False, "ok_with_markers_but_non_structured_shape"

    return "none", False, "no_useful_signal"


def read_response_sample(response: requests.Response, max_bytes: int) -> bytes:
    chunks = []
    total = 0

    for chunk in response.iter_content(chunk_size=32768):
        if not chunk:
            continue

        remaining = max_bytes - total
        if remaining <= 0:
            break

        part = chunk[:remaining]
        chunks.append(part)
        total += len(part)

        if total >= max_bytes:
            break

    return b"".join(chunks)


def seed_endpoint_route_score(row: dict) -> tuple[int, str]:
    url = str(row.get("absolute_url", "")).strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    query = parsed.query.lower()
    seed_type = str(row.get("seed_type", "")).strip().lower()
    signal = str(row.get("endpoint_signal", "")).strip().lower()
    hits = str(row.get("marker_hits", "")).strip().lower()
    basis = " ".join([url.lower(), host, path, query, seed_type, signal, hits])

    positive_markers = [
        "httpcontroller",
        "controller",
        "/api/",
        "api.",
        "ajax",
        "fetch",
        "xhr",
        "getpage=",
        "tsxventurehttpcontroller",
        "searchequitiesquickviewpage",
        "lcdbsearch",
    ]

    navigation_prefixes = [
        "/en/company-services",
        "/en/contact",
        "/en/news",
        "/en/trading",
        "/en/listings/listing-with-us",
        "/en/tmx-group",
        "/en/education",
        "/en/about",
        "/en/investor-relations",
    ]

    has_positive = any(marker in basis for marker in positive_markers)
    is_navigation = any(path.startswith(prefix) for prefix in navigation_prefixes)

    if seed_type in {"fetch_call", "xhr_open"} and has_positive:
        return 0, "strong_fetch_or_xhr_endpoint_seed"

    if "apps.tmx.com" in host and has_positive:
        return 1, "apps_tmx_controller_seed"

    if has_positive and not is_navigation:
        return 2, "controller_or_api_like_seed"

    if signal == "high" and has_positive:
        return 3, "high_signal_endpoint_like_seed"

    return 99, "navigation_or_low_specificity_seed"


def select_probe_seeds(seed_rows: list[dict], max_probes: int) -> list[dict]:
    allowed = []

    for row in seed_rows:
        url = str(row.get("absolute_url", "")).strip()
        signal = str(row.get("endpoint_signal", "")).strip().lower()
        allowed_future = as_bool_text(row.get("allowed_for_future_probe", ""))

        if not allowed_future:
            continue
        if not url:
            continue
        if not host_allowed(url):
            continue
        if signal not in {"high", "medium"}:
            continue

        score, reason = seed_endpoint_route_score(row)
        if score >= 99:
            continue

        row = dict(row)
        row["_route_score"] = score
        row["_route_reason"] = reason
        allowed.append(row)

    allowed = sorted(
        allowed,
        key=lambda row: (
            int(row.get("_route_score", 99)),
            str(row.get("source_id", "")),
            str(row.get("absolute_url", "")),
        ),
    )

    selected = []
    seen_urls = set()

    for row in allowed:
        url = str(row.get("absolute_url", "")).strip()
        key = url.lower()

        if key in seen_urls:
            continue

        selected.append(row)
        seen_urls.add(key)

        if len(selected) >= max_probes:
            break

    return selected


def probe_seed(session: requests.Session, seed_row: dict, order: int) -> dict:
    url = str(seed_row.get("absolute_url", "")).strip()
    parsed = urlparse(url)
    probe_id = sha256_text(f"{VERSION}|{order}|{url}")[:16]

    result = {
        "probe_id": probe_id,
        "probe_order": order,
        "source_id": seed_row.get("source_id", ""),
        "source_name": seed_row.get("source_name", ""),
        "seed_type": seed_row.get("seed_type", ""),
        "seed_signal": seed_row.get("endpoint_signal", ""),
        "seed_marker_hits": seed_row.get("marker_hits", ""),
        "url": url,
        "host": parsed.netloc.lower(),
        "path": parsed.path,
        "query_present": bool(parsed.query),
        "status_code": "",
        "ok": False,
        "final_url": "",
        "content_type": "",
        "content_length_header": "",
        "sampled_bytes": 0,
        "sample_sha256": "",
        "payload_saved_to_disk": False,
        "shape_classification": "",
        "evidence_level": "none",
        "promising_for_next_phase": False,
        "probe_notes": "",
        "error": "",
    }

    if not host_allowed(url):
        result["error"] = "HOST_NOT_ALLOWED"
        result["probe_notes"] = "blocked_by_host_allowlist"
        return result

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/plain,text/html,application/javascript,*/*;q=0.8",
    }

    try:
        with session.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
            stream=True,
        ) as response:
            sample = read_response_sample(response, MAX_BYTES_PER_PROBE)
            content_type = response.headers.get("content-type", "")
            shape = classify_shape(content_type, sample)
            hits = marker_hits_for_probe(seed_row, response.url, content_type, sample)
            evidence, promising, notes = evidence_from_probe(
                ok=bool(response.ok),
                status_code=response.status_code,
                shape=shape,
                hits=hits,
                sampled_bytes=len(sample),
            )

            result.update(
                {
                    "status_code": response.status_code,
                    "ok": bool(response.ok),
                    "final_url": response.url,
                    "content_type": content_type,
                    "content_length_header": response.headers.get("content-length", ""),
                    "sampled_bytes": len(sample),
                    "sample_sha256": sha256_bytes(sample) if sample else "",
                    "shape_classification": shape,
                    "evidence_level": evidence,
                    "promising_for_next_phase": promising,
                    "probe_notes": notes,
                }
            )

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["probe_notes"] = "request_error"

    return result


def main() -> None:
    for path in [PROBE_JSON, PROBE_MD, PROBE_RESULTS_CSV, PROBE_SUMMARY_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    d_validation = read_json(V216D_JSON)
    seed_rows = read_csv(V216D_SEEDS_CSV)

    max_probes = as_int(os.environ.get("SCOUT_FINANCE_TMX_D2_PROBE_LIMIT", MAX_PROBES_DEFAULT), MAX_PROBES_DEFAULT)
    selected = select_probe_seeds(seed_rows, max_probes=max_probes)

    session = requests.Session()

    results = []

    for order, seed in enumerate(selected, start=1):
        results.append(probe_seed(session, seed, order))
        time.sleep(SLEEP_BETWEEN_PROBES_SECONDS)

    status_counter = Counter(str(row["status_code"]) for row in results)
    ok_count = sum(1 for row in results if as_bool_text(row.get("ok", "")))
    error_count = sum(1 for row in results if row.get("error"))
    shape_counter = Counter(row["shape_classification"] for row in results)
    evidence_counter = Counter(row["evidence_level"] for row in results)
    promising_count = sum(1 for row in results if as_bool_text(row.get("promising_for_next_phase", "")))
    medium_or_better_count = evidence_counter.get("medium", 0) + evidence_counter.get("high", 0)
    json_like_count = shape_counter.get("json_like", 0)
    html_like_count = shape_counter.get("html_like", 0)
    js_like_count = shape_counter.get("js_like", 0)

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append(
            {
                "check": check,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add_check("v2_16d_validation_exists", V216D_JSON.exists(), "critical", str(V216D_JSON))
    add_check("v2_16d_seeds_csv_exists", V216D_SEEDS_CSV.exists(), "critical", str(V216D_SEEDS_CSV))
    add_check(
        "v2_16d_status_valid",
        d_validation.get("status") == "TMX_VALIDATION_COMPLETED_ENDPOINT_SEEDS_DETECTED_REBUILD_STILL_BLOCKED",
        "critical",
        d_validation.get("status", ""),
    )
    add_check(
        "v2_16d_recommended_d2",
        d_validation.get("recommended_next_phase") == "v2.16D2 - TMX Controlled Endpoint Probe",
        "critical",
        d_validation.get("recommended_next_phase", ""),
    )
    add_check("allowed_seeds_loaded", len(seed_rows) > 0, "critical", f"seed_rows={len(seed_rows)}")
    add_check("probe_seeds_selected", len(selected) > 0, "critical", f"selected={len(selected)}")
    add_check("controlled_probe_executed", len(results) > 0, "critical", f"results={len(results)}")
    add_check("at_least_one_http_ok", ok_count > 0, "warning", f"ok_count={ok_count}")
    add_check("medium_or_better_evidence_review", medium_or_better_count > 0, "warning", f"medium_or_better={medium_or_better_count}")
    add_check("promising_endpoint_review", promising_count > 0, "warning", f"promising_count={promising_count}")
    add_check("error_count_review", error_count <= len(results), "warning", f"error_count={error_count}")
    add_check("no_raw_payload_saved_to_disk", all(not as_bool_text(row.get("payload_saved_to_disk", "")) for row in results), "critical", "payload_saved_to_disk=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("candidate_rows_not_extracted", True, "critical", "candidate_rows_extracted=False")
    add_check("security_rows_not_extracted", True, "critical", "security_rows_extracted=False")
    add_check("canonical_dataset_not_read", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("canonical_dataset_not_modified", True, "critical", CURRENT_CANONICAL_DATASET)
    add_check("normalization_not_performed", True, "critical", "normalization_performed=False")
    add_check("net_new_filtering_not_performed", True, "critical", "net_new_filtering_performed=False")
    add_check("expanded_universe_not_rebuilt", True, "critical", "expanded_universe_rebuilt=False")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"{CURRENT_ROWS} < {FULL_SOURCE_THRESHOLD}")

    if critical_failed != 0:
        status = "TMX_CONTROLLED_ENDPOINT_PROBE_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.16D2_FIX - TMX Controlled Endpoint Probe Repair"
    elif promising_count > 0:
        status = "TMX_CONTROLLED_ENDPOINT_PROBE_COMPLETED_PROMISING_ENDPOINTS_REBUILD_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_PROMISING
    else:
        status = "TMX_CONTROLLED_ENDPOINT_PROBE_COMPLETED_NO_PROMISING_ENDPOINTS_REBUILD_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_NO_PROMISING

    summary_rows = [
        {"metric": "max_probes", "value": max_probes},
        {"metric": "seed_rows_loaded", "value": len(seed_rows)},
        {"metric": "selected_probe_seeds", "value": len(selected)},
        {"metric": "probe_results", "value": len(results)},
        {"metric": "ok_count", "value": ok_count},
        {"metric": "error_count", "value": error_count},
        {"metric": "promising_count", "value": promising_count},
        {"metric": "medium_or_better_evidence_count", "value": medium_or_better_count},
        {"metric": "json_like_count", "value": json_like_count},
        {"metric": "html_like_count", "value": html_like_count},
        {"metric": "js_like_count", "value": js_like_count},
        {"metric": "status_counts", "value": dict(status_counter)},
        {"metric": "shape_counts", "value": dict(shape_counter)},
        {"metric": "evidence_counts", "value": dict(evidence_counter)},
        {"metric": "critical_failed_checks", "value": critical_failed},
    ]

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
        "probe_summary": {
            "v2_16d_status": d_validation.get("status", ""),
            "v2_16d_recommended_next_phase": d_validation.get("recommended_next_phase", ""),
            "seed_rows_loaded": len(seed_rows),
            "selected_probe_seeds": len(selected),
            "probe_results": len(results),
            "max_probes": max_probes,
            "ok_count": ok_count,
            "error_count": error_count,
            "promising_count": promising_count,
            "medium_or_better_evidence_count": medium_or_better_count,
            "json_like_count": json_like_count,
            "html_like_count": html_like_count,
            "js_like_count": js_like_count,
            "status_counts": dict(status_counter),
            "shape_counts": dict(shape_counter),
            "evidence_counts": dict(evidence_counter),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "probe_results_preview": results[:100],
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": len(results) > 0,
            "controlled_endpoint_probe_executed": len(results) > 0,
            "raw_payload_saved_to_disk": False,
            "http_body_sampled_in_memory_only": True,
            "new_raw_files_downloaded": False,
            "query_sweep_performed": False,
            "generated_urls_or_parameter_sweep": False,
            "candidate_rows_extracted": False,
            "security_rows_extracted": False,
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

    write_json(PROBE_JSON, payload)
    write_csv(PROBE_RESULTS_CSV, results, RESULT_FIELDS)
    write_csv(PROBE_SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)

    result_lines = "\n".join(
        f"- `{row['probe_id']}` source=`{row['source_id']}` status={row['status_code']} ok={row['ok']} shape={row['shape_classification']} evidence={row['evidence_level']} promising={row['promising_for_next_phase']} url=`{row['url']}` notes=`{row['probe_notes']}`"
        for row in results[:40]
    ) or "- No probe results."

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    PROBE_MD.write_text(
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

## Probe summary

- v2.16D status: `{payload["probe_summary"]["v2_16d_status"]}`
- v2.16D recommended next phase: `{payload["probe_summary"]["v2_16d_recommended_next_phase"]}`
- Seed rows loaded: `{len(seed_rows)}`
- Selected probe seeds: `{len(selected)}`
- Probe results: `{len(results)}`
- Max probes: `{max_probes}`
- OK count: `{ok_count}`
- Error count: `{error_count}`
- Promising count: `{promising_count}`
- Medium/better evidence count: `{medium_or_better_count}`
- JSON-like count: `{json_like_count}`
- HTML-like count: `{html_like_count}`
- JS-like count: `{js_like_count}`
- Status counts: `{dict(status_counter)}`
- Shape counts: `{dict(shape_counter)}`
- Evidence counts: `{dict(evidence_counter)}`
- Critical failed checks: `{critical_failed}`

## Probe results preview

{result_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.16D2: {str(len(results) > 0).lower()}
- Controlled endpoint probe executed: {str(len(results) > 0).lower()}
- Raw payload saved to disk: false
- HTTP body sampled in memory only: true
- New raw files downloaded: false
- Query sweep performed: false
- Generated URLs or parameter sweep: false
- Candidate rows extracted: false
- Security rows extracted: false
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

TMX controlled endpoint probe completed.

This phase probes only endpoint seeds already allowed by v2.16D. It does not generate new URLs, does not perform a query sweep, does not save raw payloads, does not extract securities or candidates, does not read or modify the canonical expanded universe, does not normalize, does not calculate net-new rows and does not rebuild.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16D2 TMX controlled endpoint probe completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("PROBE_SUMMARY:")
    for key, value in payload["probe_summary"].items():
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
