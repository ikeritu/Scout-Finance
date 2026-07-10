from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


VERSION = "v2.15C"
PHASE = "Euronext Raw Acquisition"
PHASE_TYPE = "acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "euronext_v2_15c"

PLAN_JSON = OUTPUT_DIR / "euronext_acquisition_plan_v2_15b.json"

ACQUISITION_JSON = OUTPUT_DIR / "euronext_raw_acquisition_manifest_v2_15c.json"
ACQUISITION_MD = OUTPUT_DIR / "euronext_raw_acquisition_report_v2_15c.md"
DISCOVERED_LINKS_JSON = OUTPUT_DIR / "euronext_discovered_links_v2_15c.json"

CURRENT_CANONICAL_DATASET = "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv"
CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

REQUEST_TIMEOUT_SECONDS = 40

SOURCE_URLS = [
    {
        "source_id": "euronext_live_all_equities",
        "url": "https://live.euronext.com/en/products/equities/list",
        "priority": 1,
        "expected_role": "primary_public_equities_list",
    },
    {
        "source_id": "euronext_live_equities_overview",
        "url": "https://live.euronext.com/en/products/equities",
        "priority": 2,
        "expected_role": "equities_overview_and_possible_links",
    },
    {
        "source_id": "euronext_amsterdam_equities_list",
        "url": "https://live.euronext.com/en/markets/amsterdam/equities/list?page=0",
        "priority": 3,
        "expected_role": "market_specific_equities_list",
    },
    {
        "source_id": "euronext_brussels_equities_list",
        "url": "https://live.euronext.com/en/markets/brussels/equities/list?page=0",
        "priority": 4,
        "expected_role": "market_specific_equities_list",
    },
    {
        "source_id": "euronext_dublin_equities_list",
        "url": "https://live.euronext.com/en/markets/dublin/equities/list?page=0",
        "priority": 5,
        "expected_role": "market_specific_equities_list",
    },
    {
        "source_id": "euronext_lisbon_equities_list",
        "url": "https://live.euronext.com/en/markets/lisbon/equities/list?page=0",
        "priority": 6,
        "expected_role": "market_specific_equities_list",
    },
    {
        "source_id": "euronext_milan_equities_list",
        "url": "https://live.euronext.com/en/markets/milan/equities/list?page=0",
        "priority": 7,
        "expected_role": "market_specific_equities_list",
    },
    {
        "source_id": "euronext_oslo_equities_list",
        "url": "https://live.euronext.com/en/markets/oslo/equities/list?page=0",
        "priority": 8,
        "expected_role": "market_specific_equities_list",
    },
    {
        "source_id": "euronext_paris_equities_list",
        "url": "https://live.euronext.com/en/markets/paris/equities/list?page=0",
        "priority": 9,
        "expected_role": "market_specific_equities_list",
    },
    {
        "source_id": "euronext_advanced_reference_data",
        "url": "https://www.euronext.com/en/products-services/advanced-reference-data",
        "priority": 10,
        "expected_role": "official_reference_data_documentation",
    },
    {
        "source_id": "euronext_static_reference_data",
        "url": "https://www.euronext.com/en/products-services/static-reference-data",
        "priority": 11,
        "expected_role": "official_reference_data_documentation",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_filename(source_id: str, url: str, content_type: str) -> str:
    parsed = urlparse(url)
    suffix = ".html"

    content_type_lower = content_type.lower()
    if "json" in content_type_lower:
        suffix = ".json"
    elif "csv" in content_type_lower:
        suffix = ".csv"
    elif "xml" in content_type_lower:
        suffix = ".xml"
    elif "plain" in content_type_lower:
        suffix = ".txt"

    return f"{source_id}{suffix}"


def extract_lightweight_links(text: str, base_url: str) -> list[dict]:
    """
    Lightweight acquisition discovery only.

    This does not parse securities, normalize data, classify instruments,
    filter net-new rows or rebuild the expanded universe.
    """
    links = []

    hrefs = re.findall(r'href=["\\\']([^"\\\']+)["\\\']', text, flags=re.IGNORECASE)
    srcs = re.findall(r'src=["\\\']([^"\\\']+)["\\\']', text, flags=re.IGNORECASE)

    for kind, values in [("href", hrefs), ("src", srcs)]:
        for value in values[:500]:
            value = value.strip()
            if not value:
                continue
            links.append(
                {
                    "source_url": base_url,
                    "kind": kind,
                    "value": value,
                }
            )

    return links


def download_source(session: requests.Session, item: dict) -> tuple[dict, list[dict]]:
    url = item["url"]

    headers = {
        "User-Agent": "ScoutFinance/2.15C raw acquisition audit (+https://github.com/ikeritu/Scout-Finance)",
        "Accept": "text/html,application/xhtml+xml,application/xml,application/json,text/csv,text/plain,*/*;q=0.8",
    }

    started_at = utc_now()

    try:
        response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        content = response.content
        content_type = response.headers.get("content-type", "")
        filename = safe_filename(item["source_id"], url, content_type)
        raw_path = RAW_DIR / filename

        if raw_path.exists():
            raise RuntimeError(f"NO_OVERWRITE_GUARD: refusing to overwrite {raw_path}")

        raw_path.write_bytes(content)

        text_for_links = ""
        if "text" in content_type.lower() or "html" in content_type.lower() or "json" in content_type.lower():
            text_for_links = response.text[:2_000_000]

        discovered_links = extract_lightweight_links(text_for_links, url) if text_for_links else []

        result = {
            "source_id": item["source_id"],
            "url": url,
            "priority": item["priority"],
            "expected_role": item["expected_role"],
            "started_at_utc": started_at,
            "finished_at_utc": utc_now(),
            "status_code": response.status_code,
            "ok": bool(response.ok),
            "content_type": content_type,
            "encoding": response.encoding,
            "bytes": len(content),
            "sha256": sha256_bytes(content),
            "raw_path": str(raw_path),
            "discovered_link_count": len(discovered_links),
            "error": "",
        }

        return result, discovered_links

    except Exception as exc:
        result = {
            "source_id": item["source_id"],
            "url": url,
            "priority": item["priority"],
            "expected_role": item["expected_role"],
            "started_at_utc": started_at,
            "finished_at_utc": utc_now(),
            "status_code": None,
            "ok": False,
            "content_type": "",
            "encoding": "",
            "bytes": 0,
            "sha256": "",
            "raw_path": "",
            "discovered_link_count": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }
        return result, []


def main() -> None:
    if not PLAN_JSON.exists():
        raise SystemExit(f"Missing required v2.15B plan: {PLAN_JSON}")

    for path in [ACQUISITION_JSON, ACQUISITION_MD, DISCOVERED_LINKS_JSON]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    if RAW_DIR.exists() and any(RAW_DIR.iterdir()):
        raise SystemExit(f"NO_OVERWRITE_GUARD: raw directory already has files: {RAW_DIR}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))

    session = requests.Session()

    downloads = []
    all_discovered_links = []

    for item in SOURCE_URLS:
        result, links = download_source(session, item)
        downloads.append(result)
        all_discovered_links.extend(links)

    status_200 = sum(1 for item in downloads if item["status_code"] == 200)
    ok_count = sum(1 for item in downloads if item["ok"])
    failed_count = sum(1 for item in downloads if not item["ok"])
    total_bytes = sum(int(item["bytes"]) for item in downloads)

    status = (
        "EURONEXT_RAW_ACQUISITION_COMPLETED_WITH_DOWNLOADS"
        if ok_count > 0
        else "EURONEXT_RAW_ACQUISITION_COMPLETED_WITHOUT_SUCCESSFUL_DOWNLOADS"
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
        "source_urls_attempted": SOURCE_URLS,
        "downloads": downloads,
        "download_summary": {
            "attempted": len(downloads),
            "ok_count": ok_count,
            "failed_count": failed_count,
            "status_200_count": status_200,
            "total_bytes": total_bytes,
            "raw_dir": str(RAW_DIR),
            "discovered_link_count": len(all_discovered_links),
        },
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "raw_files_downloaded": ok_count > 0,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed": False,
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
        "recommended_next_phase": "v2.15D - Euronext Validation",
    }

    ACQUISITION_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    DISCOVERED_LINKS_JSON.write_text(json.dumps(all_discovered_links, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    download_lines = "\n".join(
        f"- `{item['source_id']}` status={item['status_code']} ok={item['ok']} bytes={item['bytes']} raw=`{item['raw_path']}` error=`{item['error']}`"
        for item in downloads
    )

    ACQUISITION_MD.write_text(
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

## Download summary

- Attempted: {len(downloads)}
- OK count: {ok_count}
- Failed count: {failed_count}
- HTTP 200 count: {status_200}
- Total bytes: {total_bytes}
- Raw directory: `{RAW_DIR}`
- Discovered links: {len(all_discovered_links)}

## Downloads

{download_lines}

## Guards

- Network download performed: true
- Raw files downloaded: {str(ok_count > 0).lower()}
- Raw files modified after write: false
- Workbook/CSV parsed: false
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

This phase saves raw official source pages/payloads and a lightweight link-discovery manifest only.

It does not parse securities, normalize fields, classify instruments, estimate net-new rows, rebuild the expanded universe, score equities, call OpenAI, call broker APIs or launch full 59k.

## Recommended next phase

`v2.15D - Euronext Validation`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.15C Euronext raw acquisition completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("DOWNLOAD_SUMMARY:")
    for key, value in payload["download_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("DOWNLOADS:")
    for item in downloads:
        print(f"- {item['source_id']}: status={item['status_code']} ok={item['ok']} bytes={item['bytes']} raw={item['raw_path']} error={item['error']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print("- v2.15D - Euronext Validation")


if __name__ == "__main__":
    main()
