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


VERSION = "v2.13C"
PHASE = "JPX Acquisition Real"
PHASE_TYPE = "acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "jpx_v2_13c"

JPX_LISTED_ISSUES_PAGE_URL = "https://www.jpx.co.jp/english/markets/statistics-equities/misc/01.html"
JPX_DATA_CATALOG_URL = "https://www.jpx.co.jp/english/markets/data-catalog/index.html"
JPX_CLIENT_PORTAL_ENTRY_URL = "https://clientportal.jpx.co.jp/ClientPortalEN/s/datacatalog/a085j00000Ip93W/"
JPX_LISTED_COMPANY_SEARCH_URL = "https://www.jpx.co.jp/english/listing/co-search/index.html"

MANIFEST_JSON = OUTPUT_DIR / "jpx_download_manifest_v2_13c.json"
MANIFEST_CSV = OUTPUT_DIR / "jpx_download_manifest_v2_13c.csv"
DISCOVERED_LINKS_CSV = OUTPUT_DIR / "jpx_discovered_links_v2_13c.csv"
REPORT_MD = OUTPUT_DIR / "jpx_acquisition_report_v2_13c.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return value[:80] or "file"


def no_overwrite_guard() -> None:
    guarded = [
        MANIFEST_JSON,
        MANIFEST_CSV,
        DISCOVERED_LINKS_CSV,
        REPORT_MD,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if RAW_DIR.exists():
        existing.append(str(RAW_DIR))

    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.13C outputs:\n"
            + "\n".join(existing)
        )


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def manifest_entry_base(
    *,
    family: str,
    target: str,
    url: str,
    raw_output_path: Path,
    discovery_source: str,
    source_note: str,
) -> dict:
    return {
        "version": VERSION,
        "phase_type": PHASE_TYPE,
        "family": family,
        "target": target,
        "url": url,
        "discovery_source": discovery_source,
        "source_note": source_note,
        "raw_output_path": str(raw_output_path),
        "fetched_at_utc": utc_now(),
        "status": "NOT_ATTEMPTED",
        "status_code": "",
        "content_type": "",
        "bytes": 0,
        "sha256": "",
        "error": "",
    }


def fetch_raw(
    *,
    session: requests.Session,
    family: str,
    target: str,
    url: str,
    raw_output_path: Path,
    discovery_source: str,
    source_note: str,
    timeout: int = 60,
) -> dict:
    entry = manifest_entry_base(
        family=family,
        target=target,
        url=url,
        raw_output_path=raw_output_path,
        discovery_source=discovery_source,
        source_note=source_note,
    )

    try:
        if raw_output_path.exists():
            raise RuntimeError(f"NO_OVERWRITE_GUARD: raw output already exists: {raw_output_path}")

        response = session.get(url, timeout=timeout, allow_redirects=True)
        content = response.content

        raw_output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_output_path.write_bytes(content)

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


def extension_from_url_or_content_type(url: str, content_type: str = "") -> str:
    path = urlparse(url).path.lower()

    for ext in [".xlsx", ".xls", ".csv", ".zip", ".html"]:
        if path.endswith(ext):
            return ext

    content_type_lower = content_type.lower()
    if "spreadsheetml" in content_type_lower:
        return ".xlsx"
    if "excel" in content_type_lower or "ms-excel" in content_type_lower:
        return ".xls"
    if "csv" in content_type_lower:
        return ".csv"
    if "html" in content_type_lower:
        return ".html"

    return ".bin"


def is_official_jpx_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host.endswith("jpx.co.jp")


def classify_link_family(combined: str, absolute_url: str) -> str:
    lower = f"{combined} {absolute_url}".lower()
    path = urlparse(absolute_url).path.lower()

    if any(path.endswith(ext) for ext in [".xlsx", ".xls"]):
        return "jpx_discovered_workbook_candidate"
    if path.endswith(".csv"):
        return "jpx_discovered_csv_candidate"
    if "list of tse-listed issues" in lower or "listed issues" in lower:
        return "jpx_discovered_listed_issues_page_candidate"
    return "jpx_discovered_page_candidate"


def discover_links_from_html(html_bytes: bytes, base_url: str, source_target: str) -> list[dict]:
    soup = BeautifulSoup(html_bytes, "html.parser")
    discovered = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "").strip()
        if not href:
            continue

        absolute_url = urljoin(base_url, href)
        if absolute_url in seen:
            continue

        link_text = " ".join(anchor.get_text(" ", strip=True).split())

        image_texts = []
        for img in anchor.find_all("img"):
            image_texts.append(str(img.get("alt") or ""))
            image_texts.append(str(img.get("title") or ""))

        parent_text = ""
        if anchor.parent is not None:
            parent_text = " ".join(anchor.parent.get_text(" ", strip=True).split())

        combined = " ".join([link_text, " ".join(image_texts), parent_text, href, absolute_url]).strip()
        combined_lower = combined.lower()

        relevant_tokens = [
            ".xlsx",
            ".xls",
            ".csv",
            "list of tse-listed issues",
            "listed issues",
            "tse-listed",
            "data_j",
            "data_e",
            "misc",
            "statistics-equities",
        ]

        relevant = any(token in combined_lower for token in relevant_tokens)
        if not relevant:
            continue

        seen.add(absolute_url)

        family = classify_link_family(combined, absolute_url)

        discovered.append(
            {
                "version": VERSION,
                "discovery_source": source_target,
                "family": family,
                "link_text": link_text,
                "parent_text": parent_text[:500],
                "href": href,
                "absolute_url": absolute_url,
                "official_jpx_url": is_official_jpx_url(absolute_url),
                "downloaded_in_v2_13c": "no",
                "normalization_allowed": "no",
                "rebuild_allowed": "no",
            }
        )

    return discovered


def is_dataset_download_candidate(link: dict) -> bool:
    absolute_url = str(link.get("absolute_url", ""))
    if not is_official_jpx_url(absolute_url):
        return False

    path = urlparse(absolute_url).path.lower()
    if not any(path.endswith(ext) for ext in [".xls", ".xlsx", ".csv"]):
        return False

    combined = " ".join(
        [
            str(link.get("link_text", "")),
            str(link.get("parent_text", "")),
            str(link.get("href", "")),
            absolute_url,
        ]
    ).lower()

    if "updated issues" in combined:
        return False

    positive_tokens = [
        "list of tse-listed issues",
        "tse-listed issues",
        "listed issues",
        "data_j",
        "data_e",
    ]

    return any(token in combined for token in positive_tokens) or "misc" in path


def looks_like_workbook_or_csv(entry: dict) -> bool:
    if entry.get("status") != "FETCHED_RAW_BYTES_PRESERVED":
        return False

    if str(entry.get("status_code")) != "200":
        return False

    raw_path = Path(entry.get("raw_output_path", ""))
    if not raw_path.exists():
        return False

    data = raw_path.read_bytes()[:8]
    size = int(entry.get("bytes") or 0)
    content_type = str(entry.get("content_type") or "").lower()
    suffix = raw_path.suffix.lower()

    if suffix == ".xlsx":
        return data.startswith(b"PK") and size > 1000

    if suffix == ".xls":
        # Legacy OLE compound file starts with D0 CF 11 E0.
        return data.startswith(b"\xd0\xcf\x11\xe0") and size > 1000

    if suffix == ".csv":
        return size > 100 and ("csv" in content_type or b"," in raw_path.read_bytes()[:4096])

    return size > 1000


def main() -> None:
    no_overwrite_guard()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=False)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ScoutFinanceSourceAcquisition/2.13C "
            "(JPX raw preservation; no scoring; no trading)"
        }
    )

    hard_guards = {
        "network_download_performed": True,
        "raw_files_downloaded": True,
        "raw_files_modified_after_write": False,
        "workbook_or_csv_parsed": False,
        "normalization_performed": False,
        "net_new_filtering_performed": False,
        "expanded_universe_rebuilt": False,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
    }

    page_targets = [
        {
            "family": "jpx_official_primary_listed_issues_page",
            "target": "jpx_list_of_tse_listed_issues_page",
            "url": JPX_LISTED_ISSUES_PAGE_URL,
            "filename": "jpx_list_of_tse_listed_issues_page.html",
            "source_note": "Official JPX List of TSE-listed Issues page.",
        },
        {
            "family": "jpx_official_data_portal_catalog",
            "target": "jpx_data_portal_catalog",
            "url": JPX_DATA_CATALOG_URL,
            "filename": "jpx_data_portal_catalog.html",
            "source_note": "Official JPX data catalog page for provenance.",
        },
        {
            "family": "jpx_official_client_portal_catalog_entry",
            "target": "jpx_listed_issues_client_portal_entry",
            "url": JPX_CLIENT_PORTAL_ENTRY_URL,
            "filename": "jpx_client_portal_listed_issues_entry.html",
            "source_note": "Official JPX client portal catalog entry candidate.",
        },
        {
            "family": "jpx_official_fallback_search_page",
            "target": "jpx_listed_company_search",
            "url": JPX_LISTED_COMPANY_SEARCH_URL,
            "filename": "jpx_listed_company_search.html",
            "source_note": "Official JPX listed company search fallback page.",
        },
    ]

    manifest_rows: list[dict] = []

    for target in page_targets:
        manifest_rows.append(
            fetch_raw(
                session=session,
                family=target["family"],
                target=target["target"],
                url=target["url"],
                raw_output_path=RAW_DIR / target["filename"],
                discovery_source="v2.13B acquisition contract",
                source_note=target["source_note"],
            )
        )

    discovered_links: list[dict] = []

    for row in manifest_rows:
        if row["status"] != "FETCHED_RAW_BYTES_PRESERVED":
            continue
        if "html" not in str(row.get("content_type", "")).lower() and not str(row["raw_output_path"]).lower().endswith(".html"):
            continue

        html_path = Path(row["raw_output_path"])
        if not html_path.exists():
            continue

        discovered_links.extend(
            discover_links_from_html(
                html_path.read_bytes(),
                base_url=row["url"],
                source_target=row["target"],
            )
        )

    # De-duplicate globally while preserving order.
    deduped_links = []
    seen_urls = set()
    for link in discovered_links:
        url = link["absolute_url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        deduped_links.append(link)
    discovered_links = deduped_links

    dataset_candidates = [link for link in discovered_links if is_dataset_download_candidate(link)]

    # If strict detection fails, fall back to all official workbook/CSV links discovered from the primary JPX page.
    if not dataset_candidates:
        for link in discovered_links:
            url = str(link.get("absolute_url", ""))
            path = urlparse(url).path.lower()
            if (
                link.get("discovery_source") == "jpx_list_of_tse_listed_issues_page"
                and is_official_jpx_url(url)
                and any(path.endswith(ext) for ext in [".xls", ".xlsx", ".csv"])
            ):
                dataset_candidates.append(link)

    dataset_download_rows: list[dict] = []

    for index, link in enumerate(dataset_candidates[:10], start=1):
        url = link["absolute_url"]
        ext = extension_from_url_or_content_type(url)
        filename = f"{index:03d}_jpx_dataset_candidate_{slugify(link.get('link_text') or link.get('family') or 'listed_issues')}{ext}"

        entry = fetch_raw(
            session=session,
            family="jpx_official_dataset_download_candidate",
            target=f"jpx_listed_issues_dataset_candidate_{index:03d}",
            url=url,
            raw_output_path=RAW_DIR / "datasets" / filename,
            discovery_source=link.get("discovery_source", ""),
            source_note=(
                "Official JPX workbook/CSV candidate discovered from raw JPX pages. "
                "Downloaded as raw bytes only; no parsing or acceptance decision in v2.13C."
            ),
        )
        dataset_download_rows.append(entry)
        manifest_rows.append(entry)

        link["downloaded_in_v2_13c"] = "yes"

    dataset_files_valid_container = sum(1 for row in dataset_download_rows if looks_like_workbook_or_csv(row))
    primary_dataset_downloaded = dataset_files_valid_container > 0

    counts = {
        "manifest_rows": len(manifest_rows),
        "raw_files_fetched_successfully": sum(
            1 for row in manifest_rows if row["status"] == "FETCHED_RAW_BYTES_PRESERVED"
        ),
        "fetch_failures": sum(1 for row in manifest_rows if row["status"] == "FETCH_FAILED"),
        "discovered_links": len(discovered_links),
        "dataset_candidates_discovered": len(dataset_candidates),
        "dataset_candidates_downloaded": len(dataset_download_rows),
        "dataset_files_valid_workbook_or_csv_container": dataset_files_valid_container,
        "primary_dataset_downloaded": primary_dataset_downloaded,
        "listed_issues_page_fetched": any(
            row["target"] == "jpx_list_of_tse_listed_issues_page"
            and row["status"] == "FETCHED_RAW_BYTES_PRESERVED"
            for row in manifest_rows
        ),
    }

    manifest = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "JPX_ACQUISITION_COMPLETED_RAW_ONLY",
        "generated_at_utc": utc_now(),
        "hard_guards": hard_guards,
        "counts": counts,
        "manifest_rows": manifest_rows,
        "discovered_links": discovered_links,
        "important_scope_note": (
            "v2.13C performs acquisition only. It downloads official JPX pages and direct official "
            "workbook/CSV candidates discovered from those pages as raw bytes. It does not parse files, "
            "classify securities, normalize rows, filter net-new rows, rebuild expanded universe, score, "
            "call OpenAI, call broker APIs or launch full 59k."
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
            "source_note",
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
            "parent_text",
            "href",
            "absolute_url",
            "official_jpx_url",
            "downloaded_in_v2_13c",
            "normalization_allowed",
            "rebuild_allowed",
        ],
    )

    report = f"""# {VERSION} - {PHASE}

Status: **JPX_ACQUISITION_COMPLETED_RAW_ONLY**

Phase type: **acquisition-only**

Generated at UTC: `{manifest["generated_at_utc"]}`

## Hard guards

- Network download performed: true
- Raw files downloaded: true
- Raw files modified after write: false
- Workbook or CSV parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Acquisition summary

- Manifest rows: {counts["manifest_rows"]}
- Raw files fetched successfully: {counts["raw_files_fetched_successfully"]}
- Fetch failures: {counts["fetch_failures"]}
- Discovered links: {counts["discovered_links"]}
- Dataset candidates discovered: {counts["dataset_candidates_discovered"]}
- Dataset candidates downloaded: {counts["dataset_candidates_downloaded"]}
- Dataset files valid workbook or CSV container: {counts["dataset_files_valid_workbook_or_csv_container"]}
- Primary dataset downloaded: {counts["primary_dataset_downloaded"]}
- Listed issues page fetched: {counts["listed_issues_page_fetched"]}

## Raw preservation

All successful downloads were written as raw bytes exactly as received.

Raw directory:

`{RAW_DIR}`

## Files attempted

{chr(10).join(f"- {row['target']}: status={row['status']}; status_code={row['status_code']}; bytes={row['bytes']}; path=`{row['raw_output_path']}`" for row in manifest_rows)}

## Important scope note

v2.13C does not validate whether JPX rows are usable.

v2.13C does not parse workbook/CSV data, classify securities, normalize, filter, rebuild, score or launch the full 59k universe.

All usability decisions belong to v2.13D validation.

## Outputs

- `{MANIFEST_JSON}`
- `{MANIFEST_CSV}`
- `{DISCOVERED_LINKS_CSV}`
- `{REPORT_MD}`
"""

    REPORT_MD.write_text(report, encoding="utf-8")

    print("v2.13C JPX acquisition-only completed.")
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
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
