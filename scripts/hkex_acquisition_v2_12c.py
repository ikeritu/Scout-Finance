from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


VERSION = "v2.12C"
PHASE = "HKEX Acquisition Real"
PHASE_TYPE = "acquisition-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "hkex_v2_12c"

HKEX_EN_XLSX_URL = "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx"
HKEX_SECURITIES_LISTS_PAGE_URL = "https://www.hkex.com.hk/Services/Trading/Securities/Securities-Lists?sc_lang=en"
HKEX_ZH_XLSX_URL = "https://www.hkex.com.hk/chi/services/trading/securities/securitieslists/ListOfSecurities_c.xlsx"

MANIFEST_JSON = OUTPUT_DIR / "hkex_download_manifest_v2_12c.json"
MANIFEST_CSV = OUTPUT_DIR / "hkex_download_manifest_v2_12c.csv"
DISCOVERED_LINKS_CSV = OUTPUT_DIR / "hkex_discovered_links_v2_12c.csv"
REPORT_MD = OUTPUT_DIR / "hkex_acquisition_report_v2_12c.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.12C outputs:\n"
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

        response = session.get(url, timeout=60)
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


def looks_like_valid_xlsx(entry: dict) -> bool:
    if entry.get("status") != "FETCHED_RAW_BYTES_PRESERVED":
        return False

    if str(entry.get("status_code")) != "200":
        return False

    raw_path = Path(entry.get("raw_output_path", ""))
    if not raw_path.exists():
        return False

    data = raw_path.read_bytes()[:8]
    # XLSX is a ZIP container and usually starts with PK.
    return data.startswith(b"PK") and int(entry.get("bytes") or 0) > 1000


def discover_links_from_html(html_bytes: bytes) -> list[dict]:
    soup = BeautifulSoup(html_bytes, "html.parser")
    discovered = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "").strip()
        link_text = " ".join(anchor.get_text(" ", strip=True).split())

        if not href:
            continue

        absolute_url = urljoin(HKEX_SECURITIES_LISTS_PAGE_URL, href)
        combined = f"{link_text} {href} {absolute_url}".lower()

        relevant = any(
            token in combined
            for token in [
                "listofsecurities",
                "list of securities",
                "securities list",
                ".xlsx",
                ".xls",
                ".csv",
            ]
        )

        if not relevant:
            continue

        if absolute_url in seen:
            continue

        seen.add(absolute_url)

        if ".xlsx" in combined or ".xls" in combined:
            link_family = "hkex_discovered_workbook_candidate"
        elif ".csv" in combined:
            link_family = "hkex_discovered_csv_candidate"
        else:
            link_family = "hkex_discovered_page_candidate"

        discovered.append(
            {
                "version": VERSION,
                "discovery_source": "hkex_securities_lists_page",
                "family": link_family,
                "link_text": link_text,
                "href": href,
                "absolute_url": absolute_url,
                "downloaded_in_v2_12c": "no",
                "normalization_allowed": "no",
                "rebuild_allowed": "no",
            }
        )

    return discovered


def main() -> None:
    no_overwrite_guard()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=False)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ScoutFinanceSourceAcquisition/2.12C "
            "(HKEX raw preservation; no scoring; no trading)"
        }
    )

    manifest_rows: list[dict] = []

    en_xlsx_entry = fetch_raw(
        session=session,
        family="hkex_official_direct_file",
        target="hkex_list_of_securities_xlsx_en",
        url=HKEX_EN_XLSX_URL,
        raw_output_path=RAW_DIR / "ListOfSecurities.xlsx",
        discovery_source="v2.12B acquisition contract",
        source_note="Official HKEX English List of Securities XLSX direct file.",
    )
    manifest_rows.append(en_xlsx_entry)

    landing_page_entry = fetch_raw(
        session=session,
        family="hkex_official_landing_page",
        target="hkex_securities_lists_page",
        url=HKEX_SECURITIES_LISTS_PAGE_URL,
        raw_output_path=RAW_DIR / "securities_lists_page.html",
        discovery_source="v2.12B acquisition contract",
        source_note="Official HKEX Securities Lists landing page for provenance and discovery.",
    )
    manifest_rows.append(landing_page_entry)

    fallback_triggered = not looks_like_valid_xlsx(en_xlsx_entry)

    if fallback_triggered:
        zh_xlsx_entry = fetch_raw(
            session=session,
            family="hkex_optional_fallback_file",
            target="hkex_list_of_securities_xlsx_zh",
            url=HKEX_ZH_XLSX_URL,
            raw_output_path=RAW_DIR / "ListOfSecurities_c.xlsx",
            discovery_source="v2.12B optional fallback branch",
            source_note="Chinese HKEX List of Securities XLSX downloaded only because English XLSX did not validate as raw XLSX container.",
        )
        manifest_rows.append(zh_xlsx_entry)

    discovered_links: list[dict] = []
    landing_path = RAW_DIR / "securities_lists_page.html"
    if landing_path.exists() and landing_page_entry["status"] == "FETCHED_RAW_BYTES_PRESERVED":
        discovered_links = discover_links_from_html(landing_path.read_bytes())

    counts = {
        "manifest_rows": len(manifest_rows),
        "raw_files_fetched_successfully": sum(
            1 for row in manifest_rows if row["status"] == "FETCHED_RAW_BYTES_PRESERVED"
        ),
        "fetch_failures": sum(1 for row in manifest_rows if row["status"] == "FETCH_FAILED"),
        "discovered_links": len(discovered_links),
        "english_xlsx_valid_zip_container": looks_like_valid_xlsx(en_xlsx_entry),
        "chinese_fallback_triggered": fallback_triggered,
    }

    hard_guards = {
        "network_download_performed": True,
        "raw_files_downloaded": True,
        "raw_files_modified_after_write": False,
        "workbook_parsed": False,
        "normalization_performed": False,
        "net_new_filtering_performed": False,
        "expanded_universe_rebuilt": False,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
    }

    manifest = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "HKEX_ACQUISITION_COMPLETED_RAW_ONLY",
        "generated_at_utc": utc_now(),
        "hard_guards": hard_guards,
        "counts": counts,
        "manifest_rows": manifest_rows,
        "discovered_links": discovered_links,
        "important_scope_note": (
            "v2.12C performs acquisition only. It does not parse workbook sheets, "
            "classify securities, normalize rows, filter net-new rows, rebuild expanded universe, "
            "score, call OpenAI, call broker APIs or launch full 59k."
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
            "href",
            "absolute_url",
            "downloaded_in_v2_12c",
            "normalization_allowed",
            "rebuild_allowed",
        ],
    )

    report = f"""# {VERSION} — {PHASE}

Status: **HKEX_ACQUISITION_COMPLETED_RAW_ONLY**

Phase type: **acquisition-only**

Generated at UTC: `{manifest["generated_at_utc"]}`

## Hard guards

- Network download performed: true
- Raw files downloaded: true
- Raw files modified after write: false
- Workbook parsed: false
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
- English XLSX valid ZIP container: {counts["english_xlsx_valid_zip_container"]}
- Chinese fallback triggered: {counts["chinese_fallback_triggered"]}

## Raw preservation

All successful downloads were written as raw bytes exactly as received.

Raw directory:

`{RAW_DIR}`

## Files attempted

{chr(10).join(f"- {row['target']}: status={row['status']}; status_code={row['status_code']}; bytes={row['bytes']}; path=`{row['raw_output_path']}`" for row in manifest_rows)}

## Important scope note

v2.12C does not validate whether HKEX rows are usable.

v2.12C does not parse workbook sheets, classify securities, normalize, filter, rebuild, score or launch the full 59k universe.

All usability decisions belong to v2.12D validation.

## Outputs

- `{MANIFEST_JSON}`
- `{MANIFEST_CSV}`
- `{DISCOVERED_LINKS_CSV}`
- `{REPORT_MD}`
"""

    REPORT_MD.write_text(report, encoding="utf-8")

    print("v2.12C HKEX acquisition-only completed.")
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
