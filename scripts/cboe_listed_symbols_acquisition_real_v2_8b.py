from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.8B"
METHOD = "cboe_listed_symbols_acquisition_real_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

PLAN_JSON = OUT_DIR / "cboe_listed_symbols_route_plan_v2_8a.json"

PROVIDER_ID = "cboe_listed_symbols"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID

LISTED_PAGE_URL = "https://www.cboe.com/us/equities/market_statistics/listed_symbols/"
SYMBOLS_TRADED_PAGE_URL = "https://www.cboe.com/us/equities/market_statistics/symbols_traded/?mkt=edgx"

RAW_LISTED_HTML = PROVIDER_DIR / "cboe_listed_symbols_page.html"
RAW_SYMBOLS_TRADED_HTML = PROVIDER_DIR / "cboe_symbols_traded_page.html"

RAW_LISTED_CSV = PROVIDER_DIR / "cboe_listed_symbols_raw.csv"
RAW_LISTED_XML = PROVIDER_DIR / "cboe_listed_symbols_raw.xml"
RAW_SYMBOLS_TRADED_CSV = PROVIDER_DIR / "cboe_symbols_traded_raw.csv"
RAW_SYMBOLS_TRADED_XML = PROVIDER_DIR / "cboe_symbols_traded_raw.xml"

NORMALIZED_CSV = PROVIDER_DIR / "cboe_listed_symbols_normalized.csv"

OUT_JSON = OUT_DIR / "cboe_listed_symbols_acquisition_real_v2_8b.json"
OUT_MD = OUT_DIR / "cboe_listed_symbols_acquisition_real_v2_8b.md"
OUT_SCHEMA_PROBE_CSV = OUT_DIR / "cboe_listed_symbols_schema_probe_v2_8b.csv"
OUT_DISCOVERED_LINKS_CSV = OUT_DIR / "cboe_listed_symbols_discovered_links_v2_8b.csv"
OUT_SAMPLE_CSV = OUT_DIR / "cboe_listed_symbols_sample_v2_8b.csv"

TIMEOUT_SECONDS = 40

CURRENT_EXPANDED_ROWS = 8007
TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

USER_AGENT = "ScoutFinance/1.0 controlled-provider-acquisition"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def fetch_url(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,text/csv,application/xml,text/xml,*/*",
            "Accept-Encoding": "identity",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            headers = dict(response.headers.items())
            return {
                "ok": True,
                "url": url,
                "status_code": getattr(response, "status", None),
                "reason": getattr(response, "reason", None),
                "headers": headers,
                "content_type": headers.get("Content-Type", ""),
                "size_bytes": len(raw),
                "sha256": sha256_bytes(raw),
                "raw": raw,
                "text": raw.decode("utf-8", errors="replace"),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read() if exc.fp else b""
        headers = dict(exc.headers.items()) if exc.headers else {}
        return {
            "ok": False,
            "url": url,
            "status_code": exc.code,
            "reason": exc.reason,
            "headers": headers,
            "content_type": headers.get("Content-Type", ""),
            "size_bytes": len(raw),
            "sha256": sha256_bytes(raw) if raw else None,
            "raw": raw,
            "text": raw.decode("utf-8", errors="replace") if raw else "",
            "error": f"HTTPError {exc.code}: {exc.reason}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "url": url,
            "status_code": None,
            "reason": None,
            "headers": {},
            "content_type": "",
            "size_bytes": 0,
            "sha256": None,
            "raw": b"",
            "text": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def write_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def discover_links(page_url: str, page_text: str, route_id: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []

    href_pattern = re.compile(r"""href=["']([^"']+)["']""", re.IGNORECASE)
    for match in href_pattern.finditer(page_text):
        href = html.unescape(match.group(1)).strip()
        if not href:
            continue

        absolute = urllib.parse.urljoin(page_url, href)
        lowered = absolute.lower()

        file_type = ""
        if "csv" in lowered:
            file_type = "csv"
        elif "xml" in lowered:
            file_type = "xml"
        else:
            continue

        links.append(
            {
                "route_id": route_id,
                "page_url": page_url,
                "file_type": file_type,
                "url": absolute,
            }
        )

    # Fallback candidate patterns sometimes used by sites with query-driven downloads.
    fallback_candidates = [
        page_url + "?download=csv",
        page_url + "?download=xml",
        page_url + "?output=csv",
        page_url + "?output=xml",
    ]

    seen = {item["url"] for item in links}
    for candidate in fallback_candidates:
        if candidate not in seen:
            file_type = "csv" if "csv" in candidate.lower() else "xml"
            links.append(
                {
                    "route_id": route_id,
                    "page_url": page_url,
                    "file_type": file_type,
                    "url": candidate,
                }
            )
            seen.add(candidate)

    return links


def parse_csv_bytes(raw: bytes) -> tuple[list[dict[str, str]], list[str], str | None]:
    text = raw.decode("utf-8-sig", errors="replace")
    sample = text[:4096]

    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel

    try:
        reader = csv.DictReader(text.splitlines(), dialect=dialect)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
        return rows, fieldnames, None
    except Exception as exc:
        return [], [], f"{type(exc).__name__}: {exc}"


def normalize_csv_rows(rows: list[dict[str, str]], fieldnames: list[str], source_file: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []

    lower_map = {field.lower().strip(): field for field in fieldnames}

    symbol_field = (
        lower_map.get("symbol")
        or lower_map.get("ticker")
        or lower_map.get("security")
    )

    name_field = (
        lower_map.get("name")
        or lower_map.get("company")
        or lower_map.get("company name")
        or lower_map.get("description")
        or lower_map.get("security name")
    )

    exchange_field = (
        lower_map.get("exchange")
        or lower_map.get("listing market")
        or lower_map.get("market")
        or lower_map.get("primary listing market")
    )

    if not symbol_field:
        errors.append("No symbol/ticker field detected.")
        return [], errors

    normalized: list[dict[str, str]] = []

    for row in rows:
        ticker = (row.get(symbol_field, "") or "").strip().upper()
        if not ticker:
            continue

        company_name = (row.get(name_field, "") if name_field else "").strip()
        raw_exchange = (row.get(exchange_field, "") if exchange_field else "").strip()
        exchange = "CBOE" if not raw_exchange else raw_exchange

        normalized.append(
            {
                "ticker": ticker,
                "company_name": company_name,
                "exchange": exchange,
                "country": "USA",
                "source_provider": PROVIDER_ID,
                "source_file": rel(source_file),
                "instrument_type": "UNKNOWN_PENDING_CLASSIFICATION",
                "instrument_scope": "UNKNOWN_PENDING_CLASSIFICATION",
                "classification_confidence": "LOW",
                "classification_reason": "Cboe route acquired; listed/traded semantics require v2.8C validation before rebuild.",
                "sector": "",
                "industry": "",
                "market_cap": "",
                "raw_symbol": ticker,
                "raw_name": company_name,
                "raw_exchange": raw_exchange,
                "raw_listing_market": raw_exchange,
            }
        )

    return normalized, errors


def main() -> int:
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    plan = read_json(PLAN_JSON)
    if not plan.get("_exists"):
        blockers.append(f"Missing v2.8A plan artifact: {rel(PLAN_JSON)}")
    else:
        positives.append(f"v2.8A plan artifact found: {rel(PLAN_JSON)}")

    plan_status = plan.get("plan_status")
    if plan_status == "CBOE_LISTED_SYMBOLS_ROUTE_PLAN_READY":
        positives.append(f"v2.8A plan status accepted: {plan_status}")
    else:
        blockers.append(f"Unexpected v2.8A plan status: {plan_status}")

    page_specs = [
        {
            "route_id": "cboe_us_equities_listed_symbols",
            "url": LISTED_PAGE_URL,
            "html_path": RAW_LISTED_HTML,
        },
        {
            "route_id": "cboe_us_equities_symbols_traded_edgx",
            "url": SYMBOLS_TRADED_PAGE_URL,
            "html_path": RAW_SYMBOLS_TRADED_HTML,
        },
    ]

    page_results: list[dict[str, Any]] = []
    discovered_links: list[dict[str, str]] = []

    if not blockers:
        for spec in page_specs:
            response = fetch_url(spec["url"])
            page_results.append(
                {
                    "route_id": spec["route_id"],
                    "url": spec["url"],
                    "ok": response["ok"],
                    "status_code": response["status_code"],
                    "content_type": response["content_type"],
                    "size_bytes": response["size_bytes"],
                    "sha256": response["sha256"],
                    "error": response["error"],
                    "html_path": rel(spec["html_path"]),
                }
            )

            if response["raw"]:
                write_bytes(spec["html_path"], response["raw"])
                positives.append(f"Raw Cboe page saved: {rel(spec['html_path'])}")

            if response["ok"]:
                positives.append(f"Cboe page fetched OK: {spec['url']}")
                discovered_links.extend(discover_links(spec["url"], response["text"], spec["route_id"]))
            else:
                warnings.append(f"Cboe page fetch failed: {spec['url']} ? {response['error']}")

    unique_links = []
    seen_urls = set()
    for link in discovered_links:
        if link["url"] in seen_urls:
            continue
        seen_urls.add(link["url"])
        unique_links.append(link)

    write_csv(
        OUT_DISCOVERED_LINKS_CSV,
        unique_links,
        ["route_id", "page_url", "file_type", "url"],
    )

    candidate_downloads: list[dict[str, Any]] = []
    schema_probe_rows: list[dict[str, Any]] = []
    normalized_rows: list[dict[str, str]] = []

    preferred_slots = {
        ("cboe_us_equities_listed_symbols", "csv"): RAW_LISTED_CSV,
        ("cboe_us_equities_listed_symbols", "xml"): RAW_LISTED_XML,
        ("cboe_us_equities_symbols_traded_edgx", "csv"): RAW_SYMBOLS_TRADED_CSV,
        ("cboe_us_equities_symbols_traded_edgx", "xml"): RAW_SYMBOLS_TRADED_XML,
    }

    downloaded_slot: set[tuple[str, str]] = set()

    if not blockers:
        for link in unique_links:
            slot = (link["route_id"], link["file_type"])
            if slot in downloaded_slot:
                continue

            if slot not in preferred_slots:
                continue

            response = fetch_url(link["url"])
            output_path = preferred_slots[slot]

            candidate_downloads.append(
                {
                    "route_id": link["route_id"],
                    "file_type": link["file_type"],
                    "url": link["url"],
                    "ok": response["ok"],
                    "status_code": response["status_code"],
                    "content_type": response["content_type"],
                    "size_bytes": response["size_bytes"],
                    "sha256": response["sha256"],
                    "error": response["error"],
                    "saved_path": rel(output_path) if response["raw"] else None,
                }
            )

            if response["ok"] and response["raw"]:
                write_bytes(output_path, response["raw"])
                downloaded_slot.add(slot)
                positives.append(f"Cboe {link['file_type'].upper()} saved: {rel(output_path)}")

                if link["file_type"] == "csv":
                    rows, fieldnames, parse_error = parse_csv_bytes(response["raw"])
                    schema_probe_rows.append(
                        {
                            "route_id": link["route_id"],
                            "file_type": link["file_type"],
                            "url": link["url"],
                            "saved_path": rel(output_path),
                            "parse_ok": str(parse_error is None),
                            "parse_error": parse_error or "",
                            "rows": len(rows),
                            "columns": "|".join(fieldnames),
                        }
                    )

                    if parse_error:
                        warnings.append(f"CSV parse failed for {link['route_id']}: {parse_error}")
                    else:
                        positives.append(f"CSV parsed for {link['route_id']}: {len(rows)} rows")

                        if link["route_id"] == "cboe_us_equities_listed_symbols":
                            normalized, normalization_errors = normalize_csv_rows(rows, fieldnames, output_path)
                            if normalization_errors:
                                warnings.extend([f"Normalization warning: {item}" for item in normalization_errors])
                            elif normalized:
                                normalized_rows = normalized
                                positives.append(f"Cboe listed symbols normalized rows: {len(normalized_rows)}")
                else:
                    schema_probe_rows.append(
                        {
                            "route_id": link["route_id"],
                            "file_type": link["file_type"],
                            "url": link["url"],
                            "saved_path": rel(output_path),
                            "parse_ok": "not_parsed_xml",
                            "parse_error": "",
                            "rows": "",
                            "columns": "",
                        }
                    )
            else:
                warnings.append(f"Cboe candidate download failed: {link['url']} ? {response['error']}")

    write_csv(
        OUT_SCHEMA_PROBE_CSV,
        schema_probe_rows,
        ["route_id", "file_type", "url", "saved_path", "parse_ok", "parse_error", "rows", "columns"],
    )

    normalized_columns = [
        "ticker",
        "company_name",
        "exchange",
        "country",
        "source_provider",
        "source_file",
        "instrument_type",
        "instrument_scope",
        "classification_confidence",
        "classification_reason",
        "sector",
        "industry",
        "market_cap",
        "raw_symbol",
        "raw_name",
        "raw_exchange",
        "raw_listing_market",
    ]

    if normalized_rows:
        write_csv(NORMALIZED_CSV, normalized_rows, normalized_columns)
        write_csv(OUT_SAMPLE_CSV, normalized_rows[:50], normalized_columns)
    else:
        warnings.append("No normalized Cboe listed-symbol rows produced. v2.8C must inspect raw/schema before deciding route usability.")

    if not unique_links:
        warnings.append("No CSV/XML links discovered from Cboe pages. Raw HTML preserved for review.")

    successful_downloads = [item for item in candidate_downloads if item["ok"]]
    successful_csv_downloads = [item for item in candidate_downloads if item["ok"] and item["file_type"] == "csv"]

    if blockers:
        acquisition_status = "CBOE_LISTED_SYMBOLS_ACQUISITION_BLOCKED"
        readiness_score = 0
        recommended_next_phase = "Resolve blockers"
    elif successful_downloads:
        acquisition_status = "CBOE_LISTED_SYMBOLS_ACQUISITION_COMPLETED_WITH_REVIEW_REQUIRED"
        readiness_score = 80 if normalized_rows else 70
        recommended_next_phase = "v2.8C ? Cboe Listed Symbols Validation"
    else:
        acquisition_status = "CBOE_LISTED_SYMBOLS_ACQUISITION_RAW_HTML_ONLY_REVIEW_REQUIRED"
        readiness_score = 55
        recommended_next_phase = "v2.8C ? Cboe Listed Symbols Validation"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "acquisition_status": acquisition_status,
        "readiness_score": readiness_score,
        "recommended_next_phase": recommended_next_phase,
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
        },
        "inputs": {
            "plan_json": rel(PLAN_JSON),
        },
        "page_results": page_results,
        "discovered_links_count": len(unique_links),
        "candidate_downloads": candidate_downloads,
        "outputs": {
            "provider_dir": rel(PROVIDER_DIR),
            "listed_html": rel(RAW_LISTED_HTML) if RAW_LISTED_HTML.exists() else None,
            "symbols_traded_html": rel(RAW_SYMBOLS_TRADED_HTML) if RAW_SYMBOLS_TRADED_HTML.exists() else None,
            "listed_csv": rel(RAW_LISTED_CSV) if RAW_LISTED_CSV.exists() else None,
            "listed_xml": rel(RAW_LISTED_XML) if RAW_LISTED_XML.exists() else None,
            "symbols_traded_csv": rel(RAW_SYMBOLS_TRADED_CSV) if RAW_SYMBOLS_TRADED_CSV.exists() else None,
            "symbols_traded_xml": rel(RAW_SYMBOLS_TRADED_XML) if RAW_SYMBOLS_TRADED_XML.exists() else None,
            "normalized_csv": rel(NORMALIZED_CSV) if NORMALIZED_CSV.exists() else None,
            "schema_probe_csv": rel(OUT_SCHEMA_PROBE_CSV),
            "discovered_links_csv": rel(OUT_DISCOVERED_LINKS_CSV),
            "sample_csv": rel(OUT_SAMPLE_CSV) if OUT_SAMPLE_CSV.exists() else None,
        },
        "summary": {
            "pages_attempted": len(page_specs),
            "pages_fetched_ok": len([item for item in page_results if item["ok"]]),
            "discovered_links": len(unique_links),
            "candidate_downloads_attempted": len(candidate_downloads),
            "successful_downloads": len(successful_downloads),
            "successful_csv_downloads": len(successful_csv_downloads),
            "normalized_rows": len(normalized_rows),
        },
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
            "network_download_performed": True,
            "raw_files_preserved": True,
        },
        "recommendation": (
            "Proceed to v2.8C to validate Cboe schema, semantics and net new coverage before any rebuild."
            if not blockers
            else "Resolve blockers before Cboe validation."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.8B Cboe Listed Symbols Acquisition Real")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Acquisition status: **{acquisition_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append(f"- Pages attempted: {len(page_specs)}")
    md.append(f"- Pages fetched OK: {payload['summary']['pages_fetched_ok']}")
    md.append(f"- Discovered CSV/XML links: {len(unique_links)}")
    md.append(f"- Candidate downloads attempted: {len(candidate_downloads)}")
    md.append(f"- Successful downloads: {len(successful_downloads)}")
    md.append(f"- Successful CSV downloads: {len(successful_csv_downloads)}")
    md.append(f"- Normalized rows: {len(normalized_rows)}")
    md.append("")
    md.append("## Page results")
    md.append("")
    for item in page_results:
        md.append(f"- `{item['route_id']}` ? status `{item['status_code']}`, ok `{item['ok']}`, size `{item['size_bytes']}`, saved `{item['html_path']}`")
    md.append("")
    md.append("## Candidate downloads")
    md.append("")
    if candidate_downloads:
        for item in candidate_downloads:
            md.append(f"- `{item['route_id']}` `{item['file_type']}` ? status `{item['status_code']}`, ok `{item['ok']}`, size `{item['size_bytes']}`, saved `{item['saved_path']}`")
    else:
        md.append("- No candidate downloads attempted.")
    md.append("")
    md.append("## Outputs")
    md.append("")
    for key, value in payload["outputs"].items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("- Network download performed: true")
    md.append("- Raw files preserved: true")
    md.append("")
    md.append("## Positives")
    md.append("")
    if positives:
        for item in positives:
            md.append(f"- {item}")
    else:
        md.append("- No positives detected.")
    md.append("")
    md.append("## Blockers")
    md.append("")
    if blockers:
        for item in blockers:
            md.append(f"- {item}")
    else:
        md.append("- No blockers detected.")
    md.append("")
    md.append("## Warnings")
    md.append("")
    if warnings:
        for item in warnings:
            md.append(f"- {item}")
    else:
        md.append("- No warnings detected.")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.8B is acquisition-only. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.8B Cboe Listed Symbols Acquisition Real")
    print("=" * 92)
    print(f"OK   Acquisition status: {acquisition_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Pages attempted: {len(page_specs)}")
    print(f"OK   Pages fetched OK: {payload['summary']['pages_fetched_ok']}")
    print(f"OK   Discovered CSV/XML links: {len(unique_links)}")
    print(f"OK   Candidate downloads attempted: {len(candidate_downloads)}")
    print(f"OK   Successful downloads: {len(successful_downloads)}")
    print(f"OK   Normalized rows: {len(normalized_rows)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Provider dir: {PROVIDER_DIR}")
    print("OK   Network download performed: True")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
