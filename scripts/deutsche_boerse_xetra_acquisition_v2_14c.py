from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


VERSION = "v2.14C"
PHASE = "Deutsche Börse Xetra Acquisition Real"
PHASE_TYPE = "acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "deutsche_boerse_xetra_v2_14c"
DATASET_DIR = RAW_DIR / "datasets"

MANIFEST_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_download_manifest_v2_14c.json"
MANIFEST_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_download_manifest_v2_14c.csv"
DISCOVERED_LINKS_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_discovered_links_v2_14c.csv"
REPORT_MD = OUTPUT_DIR / "deutsche_boerse_xetra_acquisition_report_v2_14c.md"

CURRENT_EXPANDED_ROWS = 36863
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_FULL_SOURCE = 13137

OFFICIAL_PAGES = [
    {
        "page_id": "downloads_en",
        "url": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra/Downloads",
        "purpose": "Official English Xetra downloads page.",
    },
    {
        "page_id": "tradable_instruments_en",
        "url": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra",
        "purpose": "Official English Xetra tradable instruments page.",
    },
    {
        "page_id": "shares_reference_en",
        "url": "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Equities/list-of-tradable-shares",
        "purpose": "Official English Xetra shares reference page.",
    },
    {
        "page_id": "downloads_de",
        "url": "https://www.cashmarket.deutsche-boerse.com/cash-de/Handel/Handelbare-Werte-Xetra/Downloads",
        "purpose": "Official German Xetra downloads fallback page.",
    },
]

OFFICIAL_DOMAINS = (
    "cashmarket.deutsche-boerse.com",
    "deutsche-boerse.com",
    "www.deutsche-boerse.com",
)

DATASET_EXTENSIONS = (
    ".csv",
    ".txt",
    ".zip",
    ".xls",
    ".xlsx",
    ".dat",
)

DATASET_KEYWORDS = (
    "all tradable instruments",
    "tradable instruments",
    "t7",
    "xetr",
    "xetra",
    "instrument",
    "instruments",
    "static instrument",
    "reference data",
    "handelbare werte",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def no_overwrite_guard() -> None:
    guarded_files = [
        MANIFEST_JSON,
        MANIFEST_CSV,
        DISCOVERED_LINKS_CSV,
        REPORT_MD,
    ]
    existing_files = [str(path) for path in guarded_files if path.exists()]
    if existing_files:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.14C outputs:\n"
            + "\n".join(existing_files)
        )

    if RAW_DIR.exists():
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to reuse existing raw directory:\n"
            + str(RAW_DIR)
        )


def fetch_url(url: str) -> tuple[int | None, str, bytes, str | None]:
    request = Request(
        url,
        headers={
            "User-Agent": "ScoutFinanceSourceAcquisition/2.14C (+https://github.com/ikeritu/Scout-Finance)",
            "Accept": "text/html,application/xhtml+xml,application/xml,text/csv,application/zip,application/octet-stream,*/*",
        },
    )

    try:
        with urlopen(request, timeout=45) as response:
            status = getattr(response, "status", None)
            content_type = response.headers.get("Content-Type", "")
            data = response.read()
            return status, content_type, data, None
    except HTTPError as exc:
        try:
            data = exc.read()
        except Exception:
            data = b""
        return exc.code, exc.headers.get("Content-Type", ""), data, f"HTTPError: {exc}"
    except URLError as exc:
        return None, "", b"", f"URLError: {exc}"
    except Exception as exc:
        return None, "", b"", f"{type(exc).__name__}: {exc}"


def safe_filename(value: str, suffix: str = "") -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    clean = clean[:140] if clean else "file"
    return clean + suffix


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_bytes(data)


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value, flags=re.S)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def discover_links(source_page_id: str, source_url: str, data: bytes) -> list[dict]:
    text = data.decode("utf-8", errors="replace")

    links: list[dict] = []

    pattern = re.compile(
        r"<a\b[^>]*?href=[\"'](?P<href>[^\"']+)[\"'][^>]*>(?P<text>.*?)</a>",
        flags=re.I | re.S,
    )

    for match in pattern.finditer(text):
        href = html.unescape(match.group("href")).strip()
        label = strip_tags(match.group("text"))
        resolved = urljoin(source_url, href)
        parsed = urlparse(resolved)
        netloc = parsed.netloc.lower()

        is_official = any(netloc == domain or netloc.endswith("." + domain) for domain in OFFICIAL_DOMAINS)

        searchable = f"{label} {resolved}".lower()
        ext_match = any(parsed.path.lower().endswith(ext) for ext in DATASET_EXTENSIONS)
        keyword_match = any(keyword in searchable for keyword in DATASET_KEYWORDS)

        candidate_reason = []
        if ext_match:
            candidate_reason.append("dataset_extension")
        if keyword_match:
            candidate_reason.append("dataset_keyword")
        if is_official:
            candidate_reason.append("official_domain")

        links.append(
            {
                "source_page_id": source_page_id,
                "source_url": source_url,
                "link_text": label,
                "href": href,
                "resolved_url": resolved,
                "netloc": netloc,
                "is_official": str(is_official),
                "has_dataset_extension": str(ext_match),
                "has_dataset_keyword": str(keyword_match),
                "candidate_reason": "|".join(candidate_reason),
                "download_candidate": str(is_official and ext_match and keyword_match),
            }
        )

    return links


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    no_overwrite_guard()

    RAW_DIR.mkdir(parents=True, exist_ok=False)
    DATASET_DIR.mkdir(parents=True, exist_ok=False)

    page_manifest: list[dict] = []
    dataset_manifest: list[dict] = []
    discovered_links: list[dict] = []

    for page in OFFICIAL_PAGES:
        page_id = page["page_id"]
        url = page["url"]

        status, content_type, data, error = fetch_url(url)

        raw_name = f"{page_id}.html"
        raw_path = RAW_DIR / raw_name

        if data:
            write_bytes(raw_path, data)

        row = {
            "kind": "official_page",
            "page_id": page_id,
            "url": url,
            "status_code": status,
            "content_type": content_type,
            "bytes": len(data),
            "sha256": sha256_bytes(data) if data else "",
            "raw_path": str(raw_path) if data else "",
            "error": error or "",
            "fetched_at_utc": utc_now(),
        }
        page_manifest.append(row)

        if data and (status is None or 200 <= int(status) < 400):
            discovered_links.extend(discover_links(page_id, url, data))

        time.sleep(1.0)

    unique_candidates: dict[str, dict] = {}
    for link in discovered_links:
        if link["download_candidate"] == "True":
            unique_candidates.setdefault(link["resolved_url"], link)

    for index, (url, link) in enumerate(unique_candidates.items(), start=1):
        if index > 12:
            break

        parsed = urlparse(url)
        suffix = Path(parsed.path).suffix
        suffix = suffix if suffix else ".bin"
        raw_name = safe_filename(f"{index:03d}_{link['source_page_id']}_{Path(parsed.path).stem}", suffix=suffix)
        raw_path = DATASET_DIR / raw_name

        status, content_type, data, error = fetch_url(url)

        if data:
            write_bytes(raw_path, data)

        dataset_manifest.append(
            {
                "kind": "dataset_candidate",
                "candidate_index": index,
                "source_page_id": link["source_page_id"],
                "link_text": link["link_text"],
                "url": url,
                "status_code": status,
                "content_type": content_type,
                "bytes": len(data),
                "sha256": sha256_bytes(data) if data else "",
                "raw_path": str(raw_path) if data else "",
                "error": error or "",
                "fetched_at_utc": utc_now(),
            }
        )

        time.sleep(1.0)

    all_manifest_rows = page_manifest + dataset_manifest

    manifest = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "DEUTSCHE_BOERSE_XETRA_ACQUISITION_COMPLETED_REQUIRES_VALIDATION",
        "generated_at_utc": utc_now(),
        "selected_provider": "deutsche_boerse_xetra_all_tradable_instruments",
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
            "full_source_unlocked": False,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
            "previous_phase_commit": "6f716dd",
        },
        "counts": {
            "official_pages_attempted": len(OFFICIAL_PAGES),
            "official_pages_fetched_successfully": sum(1 for r in page_manifest if r["bytes"] > 0 and not r["error"]),
            "official_pages_with_errors": sum(1 for r in page_manifest if r["error"]),
            "discovered_links": len(discovered_links),
            "dataset_candidates_discovered": len(unique_candidates),
            "dataset_candidates_download_attempted": len(dataset_manifest),
            "dataset_candidates_downloaded_with_bytes": sum(1 for r in dataset_manifest if r["bytes"] > 0),
            "manifest_rows": len(all_manifest_rows),
        },
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": True,
            "raw_files_downloaded": any(r["bytes"] > 0 for r in all_manifest_rows),
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
        },
        "official_page_manifest": page_manifest,
        "dataset_candidate_manifest": dataset_manifest,
        "recommended_next_phase": "v2.14D - Deutsche Börse Xetra Validation",
    }

    write_json(MANIFEST_JSON, manifest)

    write_csv(
        MANIFEST_CSV,
        all_manifest_rows,
        [
            "kind",
            "page_id",
            "candidate_index",
            "source_page_id",
            "link_text",
            "url",
            "status_code",
            "content_type",
            "bytes",
            "sha256",
            "raw_path",
            "error",
            "fetched_at_utc",
        ],
    )

    write_csv(
        DISCOVERED_LINKS_CSV,
        discovered_links,
        [
            "source_page_id",
            "source_url",
            "link_text",
            "href",
            "resolved_url",
            "netloc",
            "is_official",
            "has_dataset_extension",
            "has_dataset_keyword",
            "candidate_reason",
            "download_candidate",
        ],
    )

    report = f"""# {VERSION} - {PHASE}

Status: **DEUTSCHE_BOERSE_XETRA_ACQUISITION_COMPLETED_REQUIRES_VALIDATION**

Phase type: **acquisition-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `{manifest["generated_at_utc"]}`

## Counts

- Official pages attempted: {manifest["counts"]["official_pages_attempted"]}
- Official pages fetched successfully: {manifest["counts"]["official_pages_fetched_successfully"]}
- Official pages with errors: {manifest["counts"]["official_pages_with_errors"]}
- Discovered links: {manifest["counts"]["discovered_links"]}
- Dataset candidates discovered: {manifest["counts"]["dataset_candidates_discovered"]}
- Dataset candidates download attempted: {manifest["counts"]["dataset_candidates_download_attempted"]}
- Dataset candidates downloaded with bytes: {manifest["counts"]["dataset_candidates_downloaded_with_bytes"]}
- Manifest rows: {manifest["counts"]["manifest_rows"]}

## Guards

- Network download performed: true
- Raw files downloaded: {str(manifest["hard_guards"]["raw_files_downloaded"]).lower()}
- Workbook/CSV parsed: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Current source state

- Current expanded rows: {CURRENT_EXPANDED_ROWS}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Rows needed: {ROWS_NEEDED_FULL_SOURCE}
- Full source unlocked: false
- Full 59k status: blocked

## Recommended next phase

**v2.14D - Deutsche Börse Xetra Validation**

v2.14D may inspect downloaded files for validation only. No rebuild is allowed until validation explicitly approves it.
"""

    if REPORT_MD.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {REPORT_MD}")
    REPORT_MD.write_text(report, encoding="utf-8")

    print("v2.14C Deutsche Börse Xetra acquisition-only completed.")
    print(f"- manifest json: {MANIFEST_JSON}")
    print(f"- manifest csv: {MANIFEST_CSV}")
    print(f"- discovered links csv: {DISCOVERED_LINKS_CSV}")
    print(f"- report md: {REPORT_MD}")
    print(f"- raw dir: {RAW_DIR}")
    print("")
    print("COUNTS:")
    for key, value in manifest["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in manifest["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("NEXT:")
    print("- recommended_next_phase: v2.14D - Deutsche Börse Xetra Validation")


if __name__ == "__main__":
    main()
