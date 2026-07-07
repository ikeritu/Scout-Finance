from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


VERSION = "v2.11C"
PHASE = "Cboe Europe Acquisition Real"
PHASE_TYPE = "acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "cboe_europe_v2_11c"

REFERENCE_DATA_URL = "https://www.cboe.com/europe/equities/support/reference_data/"

FALLBACK_SYMBOLS_TRADED_PAGES = {
    "cxe": "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=cxe",
    "bxe": "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=bxe",
    "dxe": "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=dxe",
    "trf": "https://www.cboe.com/europe/equities/market_statistics/symbols_traded/?mkt=trf",
}

MANIFEST_JSON = OUTPUT_DIR / "cboe_europe_download_manifest_v2_11c.json"
MANIFEST_CSV = OUTPUT_DIR / "cboe_europe_download_manifest_v2_11c.csv"
DISCOVERED_LINKS_CSV = OUTPUT_DIR / "cboe_europe_discovered_links_v2_11c.csv"
REPORT_MD = OUTPUT_DIR / "cboe_europe_acquisition_report_v2_11c.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def no_overwrite_guard() -> None:
    guarded_outputs = [
        MANIFEST_JSON,
        MANIFEST_CSV,
        DISCOVERED_LINKS_CSV,
        REPORT_MD,
    ]

    existing_outputs = [str(path) for path in guarded_outputs if path.exists()]
    if existing_outputs:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.11C final outputs:\n"
            + "\n".join(existing_outputs)
        )


def safe_filename(value: str, fallback: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"https?://", "", cleaned)
    cleaned = re.sub(r"[^a-z0-9._-]+", "_", cleaned)
    cleaned = cleaned.strip("._-")
    return cleaned[:140] or fallback


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def manifest_entry_base(
    url: str,
    output_path: Path,
    family: str,
    target: str,
    source_link_text: str,
    discovery_source: str,
) -> dict:
    return {
        "version": VERSION,
        "phase_type": PHASE_TYPE,
        "family": family,
        "target": target,
        "url": url,
        "discovery_source": discovery_source,
        "source_link_text": source_link_text,
        "raw_output_path": str(output_path),
        "fetched_at_utc": utc_now(),
        "status": "NOT_ATTEMPTED",
        "status_code": "",
        "content_type": "",
        "bytes": 0,
        "sha256": "",
        "error": "",
    }


def reuse_existing_raw(
    entry: dict,
    output_path: Path,
) -> dict:
    content = output_path.read_bytes()

    entry.update(
        {
            "status": "RAW_ALREADY_EXISTS_REUSED_HTTP_METADATA_UNAVAILABLE",
            "status_code": "REUSED_LOCAL_RAW",
            "content_type": "unknown/reused-local-raw",
            "bytes": len(content),
            "sha256": sha256_bytes(content),
            "error": "",
        }
    )

    return entry


def fetch_or_reuse_raw(
    session: requests.Session,
    url: str,
    output_path: Path,
    family: str,
    target: str,
    source_link_text: str = "",
    discovery_source: str = "",
) -> dict:
    entry = manifest_entry_base(
        url=url,
        output_path=output_path,
        family=family,
        target=target,
        source_link_text=source_link_text,
        discovery_source=discovery_source,
    )

    if output_path.exists():
        return reuse_existing_raw(entry, output_path)

    try:
        response = session.get(url, timeout=45)
        content = response.content

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
            return reuse_existing_raw(entry, output_path)

        output_path.write_bytes(content)

        entry.update(
            {
                "status": "FETCHED_RAW_BYTES_PRESERVED",
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "bytes": len(content),
                "sha256": sha256_bytes(content),
                "error": "",
            }
        )

    except Exception as exc:
        entry.update(
            {
                "status": "FETCH_FAILED",
                "error": repr(exc),
            }
        )

    return entry


def classify_csv_link(link_text: str, href: str) -> str:
    combined = f"{link_text} {href}".lower()

    if "enhanced" in combined and "symbol" in combined:
        return "live_symbols_enhanced_csv"

    if "live" in combined and "symbol" in combined:
        return "live_symbols_csv"

    if "symbol" in combined or "symbols" in combined:
        return "symbols_csv_candidate"

    if "instrument" in combined or "reference" in combined:
        return "reference_csv_candidate"

    return "csv_candidate"


def discover_csv_links(reference_html: bytes) -> list[dict]:
    soup = BeautifulSoup(reference_html, "html.parser")

    discovered = []
    seen_urls = set()

    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "").strip()
        link_text = " ".join(anchor.get_text(" ", strip=True).split())

        if not href:
            continue

        absolute_url = urljoin(REFERENCE_DATA_URL, href)
        combined = f"{link_text} {href} {absolute_url}".lower()

        is_csvish = ".csv" in combined or "csv" in combined
        is_referenceish = any(
            token in combined
            for token in [
                "symbol",
                "symbols",
                "live",
                "enhanced",
                "instrument",
                "reference",
                "tradable",
                "security",
                "securities",
            ]
        )

        if not is_csvish or not is_referenceish:
            continue

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)

        discovered.append(
            {
                "version": VERSION,
                "discovery_source": "cboe_europe_reference_data_page",
                "family": classify_csv_link(link_text, absolute_url),
                "link_text": link_text,
                "href": href,
                "absolute_url": absolute_url,
                "download_allowed_in_v2_11c": "yes",
                "normalization_allowed": "no",
                "rebuild_allowed": "no",
            }
        )

    return discovered


def build_csv_raw_path(index: int, absolute_url: str) -> Path:
    parsed = urlparse(absolute_url)
    original_name = Path(parsed.path).name or f"discovered_csv_{index}.csv"

    filename = f"{index:03d}_{safe_filename(original_name, f'discovered_csv_{index}.csv')}"
    if not filename.endswith(".csv"):
        filename = f"{filename}.csv"

    return RAW_DIR / "csv" / filename


def main() -> None:
    no_overwrite_guard()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ScoutFinanceSourceAcquisition/2.11C "
            "(raw preservation; no scoring; no trading)"
        }
    )

    manifest_rows = []

    reference_raw_path = RAW_DIR / "reference_data_page.html"

    reference_entry = fetch_or_reuse_raw(
        session=session,
        url=REFERENCE_DATA_URL,
        output_path=reference_raw_path,
        family="reference_data",
        target="cboe_europe_reference_data_page",
        source_link_text="Cboe Europe Reference Data",
        discovery_source="v2.11B acquisition plan",
    )
    manifest_rows.append(reference_entry)

    discovered_links = []
    if reference_raw_path.exists() and reference_entry["status"] in {
        "FETCHED_RAW_BYTES_PRESERVED",
        "RAW_ALREADY_EXISTS_REUSED_HTTP_METADATA_UNAVAILABLE",
    }:
        discovered_links = discover_csv_links(reference_raw_path.read_bytes())

    csv_download_rows = []
    for index, link in enumerate(discovered_links, start=1):
        raw_path = build_csv_raw_path(index, link["absolute_url"])

        csv_entry = fetch_or_reuse_raw(
            session=session,
            url=link["absolute_url"],
            output_path=raw_path,
            family=link["family"],
            target=f"discovered_csv_{index:03d}",
            source_link_text=link["link_text"],
            discovery_source="cboe_europe_reference_data_page",
        )

        csv_download_rows.append(csv_entry)
        manifest_rows.append(csv_entry)

    for market, url in FALLBACK_SYMBOLS_TRADED_PAGES.items():
        raw_path = RAW_DIR / "fallback_symbols_traded" / f"symbols_traded_{market}.html"

        fallback_entry = fetch_or_reuse_raw(
            session=session,
            url=url,
            output_path=raw_path,
            family="fallback_symbols_traded_html",
            target=f"symbols_traded_{market}",
            source_link_text=f"symbols_traded {market.upper()}",
            discovery_source="v2.11B planned fallback pages",
        )
        manifest_rows.append(fallback_entry)

    raw_success_statuses = {
        "FETCHED_RAW_BYTES_PRESERVED",
        "RAW_ALREADY_EXISTS_REUSED_HTTP_METADATA_UNAVAILABLE",
    }

    counts = {
        "manifest_rows": len(manifest_rows),
        "discovered_csv_links": len(discovered_links),
        "csv_download_attempts": len(csv_download_rows),
        "fallback_symbols_traded_pages_planned": len(FALLBACK_SYMBOLS_TRADED_PAGES),
        "raw_files_available_successfully": sum(
            1 for row in manifest_rows if row["status"] in raw_success_statuses
        ),
        "raw_files_reused_from_partial_run": sum(
            1
            for row in manifest_rows
            if row["status"] == "RAW_ALREADY_EXISTS_REUSED_HTTP_METADATA_UNAVAILABLE"
        ),
        "fetch_failures": sum(1 for row in manifest_rows if row["status"] == "FETCH_FAILED"),
    }

    manifest = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "CBOE_EUROPE_ACQUISITION_COMPLETED_RAW_ONLY",
        "generated_at_utc": utc_now(),
        "hard_guards": {
            "network_download_performed": True,
            "raw_files_downloaded_or_reused": True,
            "expanded_universe_rebuilt": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "overwrite_allowed": False,
            "rebuild_allowed": False,
        },
        "counts": counts,
        "manifest_rows": manifest_rows,
        "discovered_links": discovered_links,
        "partial_run_note": (
            "reference_data_page.html may have been reused from the initial failed run. "
            "When reused, HTTP metadata is unavailable, but raw bytes, size and SHA256 are recorded."
        ),
    }

    write_json(MANIFEST_JSON, manifest)

    write_csv(
        MANIFEST_CSV,
        manifest_rows,
        [
            "version",
            "phase_type",
            "family",
            "target",
            "url",
            "discovery_source",
            "source_link_text",
            "raw_output_path",
            "fetched_at_utc",
            "status",
            "status_code",
            "content_type",
            "bytes",
            "sha256",
            "error",
        ],
    )

    write_csv(
        DISCOVERED_LINKS_CSV,
        discovered_links,
        [
            "version",
            "discovery_source",
            "family",
            "link_text",
            "href",
            "absolute_url",
            "download_allowed_in_v2_11c",
            "normalization_allowed",
            "rebuild_allowed",
        ],
    )

    report = f"""# {VERSION} - {PHASE}

Status: **CBOE_EUROPE_ACQUISITION_COMPLETED_RAW_ONLY**

Phase type: **acquisition-only**

Generated at UTC: `{manifest["generated_at_utc"]}`

## Hard guards

- Network download performed: true
- Raw files downloaded or reused: true
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Normalization performed: false
- Net-new filtering performed: false
- Overwrite allowed: false
- Rebuild allowed: false

## Acquisition summary

- Manifest rows: {counts["manifest_rows"]}
- Discovered CSV links: {counts["discovered_csv_links"]}
- CSV download attempts: {counts["csv_download_attempts"]}
- Fallback symbols_traded pages planned: {counts["fallback_symbols_traded_pages_planned"]}
- Raw files available successfully: {counts["raw_files_available_successfully"]}
- Raw files reused from partial run: {counts["raw_files_reused_from_partial_run"]}
- Fetch failures: {counts["fetch_failures"]}

## Partial run handling

If `reference_data_page.html` already existed from the initial failed run, it was reused without overwrite.

For reused raw files, HTTP metadata is not available, but byte size and SHA256 are recorded.

## Raw preservation

All successful downloads were written or reused as raw bytes exactly as present on disk.

Raw directory:

`{RAW_DIR}`

## Outputs

- `{MANIFEST_JSON}`
- `{MANIFEST_CSV}`
- `{DISCOVERED_LINKS_CSV}`
- `{REPORT_MD}`

## Important scope note

v2.11C does not validate whether Cboe Europe rows are usable.

v2.11C does not normalize, filter, rebuild, score or launch the full 59k universe.

All usability decisions belong to v2.11D validation.
"""

    REPORT_MD.write_text(report, encoding="utf-8")

    print("v2.11C acquisition-only completed.")
    print(f"- manifest json: {MANIFEST_JSON}")
    print(f"- manifest csv: {MANIFEST_CSV}")
    print(f"- discovered links csv: {DISCOVERED_LINKS_CSV}")
    print(f"- report md: {REPORT_MD}")
    print(f"- raw dir: {RAW_DIR}")
    print("")
    print("COUNTS:")
    for key, value in counts.items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in manifest["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
