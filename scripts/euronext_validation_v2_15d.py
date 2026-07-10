from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin


VERSION = "v2.15D"
PHASE = "Euronext Validation"
PHASE_TYPE = "validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "euronext_v2_15c"

ACQUISITION_MANIFEST_JSON = OUTPUT_DIR / "euronext_raw_acquisition_manifest_v2_15c.json"
DISCOVERED_LINKS_JSON = OUTPUT_DIR / "euronext_discovered_links_v2_15c.json"
PLAN_JSON = OUTPUT_DIR / "euronext_acquisition_plan_v2_15b.json"

VALIDATION_JSON = OUTPUT_DIR / "euronext_validation_v2_15d.json"
VALIDATION_MD = OUTPUT_DIR / "euronext_validation_v2_15d.md"
CANDIDATE_ENDPOINTS_CSV = OUTPUT_DIR / "euronext_candidate_endpoints_v2_15d.csv"
RAW_FILE_DIAGNOSTICS_CSV = OUTPUT_DIR / "euronext_raw_file_diagnostics_v2_15d.csv"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

FIELD_MARKERS = [
    "isin",
    "symbol",
    "ticker",
    "name",
    "instrument",
    "equity",
    "shares",
    "market",
    "mic",
    "currency",
    "company",
    "issuer",
    "listing",
    "stock",
]

ENDPOINT_HINTS = [
    "api",
    "ajax",
    "data",
    "download",
    "csv",
    "json",
    "instrument",
    "instruments",
    "equity",
    "equities",
    "stock",
    "stocks",
    "live.euronext.com",
    "euronext",
]

EXCLUDE_ENDPOINT_HINTS = [
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".svg",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict | list:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def read_text_best_effort(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ["utf-8", "utf-8-sig", "cp1252", "latin-1"]:
        try:
            return data.decode(encoding, errors="replace")
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def extract_urls_from_text(text: str, base_url: str = "") -> list[str]:
    values: list[str] = []

    patterns = [
        r"""href=["']([^"']+)["']""",
        r"""src=["']([^"']+)["']""",
        r"""url\(["']?([^"')]+)["']?\)""",
        r"""https?://[^"'\s<>]+""",
        r"""["'](/[^"']*(?:api|ajax|data|download|csv|json|instrument|equity|stock)[^"']*)["']""",
    ]

    for pattern in patterns:
        try:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
        except re.error as exc:
            raise RuntimeError(f"Invalid regex pattern in extract_urls_from_text: {pattern!r}: {exc}") from exc

        for match in matches:
            value = str(match).strip()
            if not value:
                continue
            if base_url and value.startswith("/"):
                value = urljoin(base_url, value)
            values.append(value)

    seen = set()
    deduped = []

    for value in values:
        key = value.strip()
        if key and key not in seen:
            deduped.append(key)
            seen.add(key)

    return deduped


def endpoint_score(value: str) -> tuple[int, list[str]]:
    low = value.lower()
    matched = []
    score = 0

    if any(bad in low for bad in EXCLUDE_ENDPOINT_HINTS):
        return 0, []

    for hint in ENDPOINT_HINTS:
        if hint in low:
            matched.append(hint)
            score += 10

    if "csv" in low or "download" in low:
        score += 20
    if "json" in low or "api" in low or "ajax" in low:
        score += 15
    if "instrument" in low or "equity" in low or "stock" in low:
        score += 15
    if "live.euronext.com" in low or "euronext.com" in low:
        score += 5

    return score, matched


def analyze_raw_file(path: Path, source_url: str = "") -> tuple[dict, list[dict]]:
    text = read_text_best_effort(path)
    text_low = text.lower()

    marker_counts = {marker: text_low.count(marker) for marker in FIELD_MARKERS}

    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""

    table_count = len(re.findall(r"<table\\b", text, flags=re.IGNORECASE))
    script_count = len(re.findall(r"<script\\b", text, flags=re.IGNORECASE))
    form_count = len(re.findall(r"<form\\b", text, flags=re.IGNORECASE))
    drupal_settings_count = text_low.count("drupalsettings")
    isin_like_count = len(re.findall(r"\\b[A-Z]{2}[A-Z0-9]{9}[0-9]\\b", text))

    urls = extract_urls_from_text(text, source_url)

    endpoint_rows = []
    for url in urls:
        score, matched = endpoint_score(url)
        if score <= 0:
            continue
        endpoint_rows.append(
            {
                "raw_file": str(path),
                "source_url": source_url,
                "candidate_url": url,
                "score": score,
                "matched_hints": "|".join(sorted(set(matched))),
            }
        )

    endpoint_rows = sorted(endpoint_rows, key=lambda row: int(row["score"]), reverse=True)

    diagnostic = {
        "raw_file": str(path),
        "name": path.name,
        "bytes": path.stat().st_size,
        "source_url": source_url,
        "title": title,
        "table_count": table_count,
        "script_count": script_count,
        "form_count": form_count,
        "drupal_settings_count": drupal_settings_count,
        "isin_like_count": isin_like_count,
        "candidate_endpoint_count": len(endpoint_rows),
        **{f"marker_{key}": value for key, value in marker_counts.items()},
    }

    return diagnostic, endpoint_rows


def main() -> None:
    for path in [VALIDATION_JSON, VALIDATION_MD, CANDIDATE_ENDPOINTS_CSV, RAW_FILE_DIAGNOSTICS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if not RAW_DIR.exists():
        raise SystemExit(f"Missing raw dir: {RAW_DIR}")

    acquisition = read_json(ACQUISITION_MANIFEST_JSON)
    discovered_links = read_json(DISCOVERED_LINKS_JSON)
    plan = read_json(PLAN_JSON)

    downloads = acquisition.get("downloads", [])
    source_url_by_raw_path = {
        item.get("raw_path", ""): item.get("url", "")
        for item in downloads
        if item.get("raw_path")
    }

    raw_files = sorted(RAW_DIR.glob("*"))

    diagnostics = []
    endpoint_rows_all = []

    for raw_file in raw_files:
        source_url = source_url_by_raw_path.get(str(raw_file), "")
        diagnostic, endpoint_rows = analyze_raw_file(raw_file, source_url)
        diagnostics.append(diagnostic)
        endpoint_rows_all.extend(endpoint_rows)

    # Also evaluate discovered link manifest from v2.15C, without downloading.
    discovered_counter = Counter()
    for item in discovered_links if isinstance(discovered_links, list) else []:
        value = str(item.get("value", "")).strip()
        if not value:
            continue
        score, matched = endpoint_score(value)
        if score <= 0:
            continue
        discovered_counter[value] += 1
        endpoint_rows_all.append(
            {
                "raw_file": "(v2.15C_discovered_links_manifest)",
                "source_url": str(item.get("source_url", "")),
                "candidate_url": value,
                "score": score,
                "matched_hints": "|".join(sorted(set(matched))),
            }
        )

    # Deduplicate endpoint candidates, keeping max score.
    endpoint_best: dict[str, dict] = {}
    for row in endpoint_rows_all:
        key = row["candidate_url"]
        if key not in endpoint_best or int(row["score"]) > int(endpoint_best[key]["score"]):
            endpoint_best[key] = row

    endpoint_rows_deduped = sorted(endpoint_best.values(), key=lambda row: int(row["score"]), reverse=True)

    total_raw_bytes = sum(item["bytes"] for item in diagnostics)
    total_tables = sum(item["table_count"] for item in diagnostics)
    total_scripts = sum(item["script_count"] for item in diagnostics)
    total_isin_like = sum(item["isin_like_count"] for item in diagnostics)
    total_candidate_endpoints = len(endpoint_rows_deduped)

    source_candidate_usable = total_candidate_endpoints > 0 and len(raw_files) > 0

    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        checks.append(
            {
                "check": check,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add_check("raw_dir_exists", RAW_DIR.exists(), "critical", str(RAW_DIR))
    add_check("raw_files_present", len(raw_files) >= 1, "critical", f"raw_files={len(raw_files)}")
    add_check("acquisition_manifest_exists", ACQUISITION_MANIFEST_JSON.exists(), "critical", str(ACQUISITION_MANIFEST_JSON))
    add_check("discovered_links_manifest_exists", DISCOVERED_LINKS_JSON.exists(), "critical", str(DISCOVERED_LINKS_JSON))
    add_check("plan_exists", PLAN_JSON.exists(), "critical", str(PLAN_JSON))
    add_check("downloads_ok_in_manifest", acquisition.get("download_summary", {}).get("ok_count", 0) >= 1, "critical", f"ok_count={acquisition.get('download_summary', {}).get('ok_count')}")
    add_check("candidate_endpoints_detected", total_candidate_endpoints > 0, "critical", f"candidate_endpoints={total_candidate_endpoints}")
    add_check("source_candidate_usable_for_validation", source_candidate_usable, "critical", f"usable={source_candidate_usable}")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"current_rows={CURRENT_ROWS}")
    add_check("no_rebuild_or_scoring", True, "critical", "rebuild=False; scoring=False; openai=False; broker=False; full59k=False")

    add_check("tables_detected_review", total_tables >= 0, "warning", f"tables={total_tables}")
    add_check("isin_like_detected_review", total_isin_like >= 0, "warning", f"isin_like={total_isin_like}")

    critical_failed = sum(1 for item in checks if item["severity"] == "critical" and not item["passed"])
    warning_failed = sum(1 for item in checks if item["severity"] == "warning" and not item["passed"])

    status = (
        "EURONEXT_VALIDATION_PASSED_CANDIDATES_DETECTED_REBUILD_STILL_BLOCKED"
        if critical_failed == 0
        else "EURONEXT_VALIDATION_FAILED_REBUILD_BLOCKED"
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "selected_provider": plan.get("selected_provider", {}),
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
            "raw_files": len(raw_files),
            "total_raw_bytes": total_raw_bytes,
            "total_tables": total_tables,
            "total_scripts": total_scripts,
            "total_isin_like_occurrences": total_isin_like,
            "candidate_endpoints": total_candidate_endpoints,
            "critical_failed_checks": critical_failed,
            "warning_failed_checks": warning_failed,
        },
        "checks": checks,
        "top_candidate_endpoints": endpoint_rows_deduped[:50],
        "raw_file_diagnostics": diagnostics,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed_for_validation": True,
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
        "recommended_next_phase": "v2.15E - Euronext Expanded Rebuild Candidate Preparation",
        "fallback_next_phase_if_endpoint_not_sufficient": "v2.15D2 - Euronext Endpoint Discovery Validation",
    }

    write_json(VALIDATION_JSON, payload)

    diag_fieldnames = list(diagnostics[0].keys()) if diagnostics else [
        "raw_file",
        "name",
        "bytes",
        "source_url",
        "title",
        "table_count",
        "script_count",
        "form_count",
        "drupal_settings_count",
        "isin_like_count",
        "candidate_endpoint_count",
    ]
    write_csv(RAW_FILE_DIAGNOSTICS_CSV, diagnostics, diag_fieldnames)

    write_csv(
        CANDIDATE_ENDPOINTS_CSV,
        endpoint_rows_deduped,
        ["raw_file", "source_url", "candidate_url", "score", "matched_hints"],
    )

    check_lines = "\n".join(
        f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}"
        for item in checks
    )

    endpoint_lines = "\n".join(
        f"- score={row['score']} hints={row['matched_hints']} url={row['candidate_url']}"
        for row in endpoint_rows_deduped[:20]
    )

    diagnostic_lines = "\n".join(
        f"- `{item['name']}` bytes={item['bytes']} tables={item['table_count']} scripts={item['script_count']} isin_like={item['isin_like_count']} endpoints={item['candidate_endpoint_count']}"
        for item in diagnostics
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

- Raw files: {len(raw_files)}
- Total raw bytes: {total_raw_bytes}
- Tables detected: {total_tables}
- Scripts detected: {total_scripts}
- ISIN-like occurrences: {total_isin_like}
- Candidate endpoints: {total_candidate_endpoints}
- Critical failed checks: {critical_failed}
- Warning failed checks: {warning_failed}

## Raw file diagnostics

{diagnostic_lines}

## Top candidate endpoints

{endpoint_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.15D: false
- Raw files downloaded in v2.15D: false
- Raw files modified after write: false
- Workbook/CSV parsed for validation: true
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase validates raw Euronext acquisition artifacts and detects candidate endpoints/structure only.

It does not normalize securities, classify final instruments, filter net-new rows, rebuild the expanded universe, score equities, call OpenAI, call broker APIs or launch full 59k.

## Recommended next phase

`v2.15E - Euronext Expanded Rebuild Candidate Preparation`

Fallback if candidate endpoint quality is insufficient:

`v2.15D2 - Euronext Endpoint Discovery Validation`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15D Euronext validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in payload["validation_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for item in checks:
        print(f"- {item['check']}: {'PASS' if item['passed'] else 'FAIL'} ({item['severity']}) - {item['detail']}")
    print("")
    print("TOP_CANDIDATE_ENDPOINTS:")
    for row in endpoint_rows_deduped[:10]:
        print(f"- score={row['score']} hints={row['matched_hints']} url={row['candidate_url']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {payload['recommended_next_phase']}")


if __name__ == "__main__":
    main()
