from __future__ import annotations

import csv
import hashlib
import html.parser
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.10C"
METHOD = "lse_acquisition_real_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

PROVIDER_ID = "lse_issuers_and_instruments_reports"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID
REPORT_CANDIDATES_DIR = PROVIDER_DIR / "report_candidates"

PLAN_JSON = OUT_DIR / "lse_acquisition_plan_v2_10b.json"

LSE_ROUTES = [
    {
        "route_id": "lse_reports_page_probe",
        "url": "https://www.londonstockexchange.com/reports",
        "target": PROVIDER_DIR / "lse_reports_page.html",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
    {
        "route_id": "lse_issuers_reports_tab_probe",
        "url": "https://www.londonstockexchange.com/reports?tab=issuers",
        "target": PROVIDER_DIR / "lse_issuers_reports_page.html",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
    {
        "route_id": "lse_instruments_reports_tab_probe",
        "url": "https://www.londonstockexchange.com/reports?tab=instruments",
        "target": PROVIDER_DIR / "lse_instruments_reports_page.html",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
    {
        "route_id": "lse_historical_analytics_data_products_probe",
        "url": "https://www.londonstockexchange.com/equities-trading/market-data/historical-analytics-data-products",
        "target": PROVIDER_DIR / "lse_historical_analytics_data_products_page.html",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
]

OUT_JSON = OUT_DIR / "lse_acquisition_real_v2_10c.json"
OUT_MD = OUT_DIR / "lse_acquisition_real_v2_10c.md"
DISCOVERED_LINKS_CSV = OUT_DIR / "lse_discovered_links_v2_10c.csv"
SCHEMA_PROBE_CSV = OUT_DIR / "lse_schema_probe_v2_10c.csv"
SAMPLE_CSV = OUT_DIR / "lse_sample_v2_10c.csv"
REQUESTS_CSV = OUT_DIR / "lse_request_results_v2_10c.csv"

CURRENT_EXPANDED_ROWS = 9200
ROWS_NEEDED_FIRST_EXPANSION = 5800
ROWS_NEEDED_FULL_SOURCE = 40800

REQUEST_TIMEOUT_SECONDS = 45
MAX_CANDIDATE_DOWNLOADS = 12

ALLOWED_HOSTS = {
    "www.londonstockexchange.com",
    "londonstockexchange.com",
}

REPORT_EXTENSIONS = (
    ".csv",
    ".xls",
    ".xlsx",
    ".zip",
    ".json",
)

REPORT_KEYWORDS = (
    "issuer",
    "issuers",
    "instrument",
    "instruments",
    "report",
    "reports",
    "securities",
    "security",
    "tradable",
    "tradeable",
    "admitted",
    "admission",
    "listed",
    "listing",
    "market",
    "daily",
)


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k.lower(): v or "" for k, v in attrs}
        href = attr_dict.get("href", "")
        if href:
            self.links.append({
                "tag": tag,
                "href": href,
                "text": "",
            })


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def safe_filename(value: str, fallback: str) -> str:
    parsed = urllib.parse.urlparse(value)
    name = Path(parsed.path).name or fallback
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return name or fallback


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def fetch(url: str, out_path: Path, accept: str) -> dict[str, Any]:
    headers = {
        "User-Agent": "ScoutFinanceSourceAcquisition/2.10C (+controlled research use)",
        "Accept": accept,
    }
    request = urllib.request.Request(url, headers=headers, method="GET")

    result: dict[str, Any] = {
        "url": url,
        "target_path": rel(out_path),
        "ok": False,
        "status_code": None,
        "content_type": "",
        "size_bytes": 0,
        "sha256": "",
        "error": "",
    }

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data = response.read()
            result["status_code"] = getattr(response, "status", None)
            result["content_type"] = response.headers.get("Content-Type", "")
            result["size_bytes"] = len(data)
            result["sha256"] = sha256_bytes(data)

            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(data)

            result["ok"] = 200 <= int(result["status_code"] or 0) < 300
            return result

    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        result["status_code"] = exc.code
        result["content_type"] = exc.headers.get("Content-Type", "") if exc.headers else ""
        result["size_bytes"] = len(body)
        result["sha256"] = sha256_bytes(body) if body else ""
        result["error"] = f"HTTPError: {exc}"
        if body:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.with_suffix(out_path.suffix + ".error_body").write_bytes(body)
        return result

    except Exception as exc:
        result["error"] = repr(exc)
        return result


def is_allowed_lse_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() in ALLOWED_HOSTS


def score_candidate_url(url: str) -> int:
    lowered = url.lower()
    score = 0

    if lowered.endswith(REPORT_EXTENSIONS):
        score += 10

    for keyword in REPORT_KEYWORDS:
        if keyword in lowered:
            score += 2

    if "download" in lowered:
        score += 4

    if "report" in lowered:
        score += 3

    return score


def discover_links_from_html(source_path: Path, source_url: str) -> list[dict[str, Any]]:
    if not source_path.exists():
        return []

    text = source_path.read_text(encoding="utf-8", errors="replace")
    parser = LinkParser()
    parser.feed(text)

    discovered: list[dict[str, Any]] = []

    for item in parser.links:
        href = item["href"].strip()
        absolute_url = urllib.parse.urljoin(source_url, href)
        parsed = urllib.parse.urlparse(absolute_url)
        extension = Path(parsed.path).suffix.lower()
        score = score_candidate_url(absolute_url)

        discovered.append({
            "source_path": rel(source_path),
            "source_url": source_url,
            "tag": item["tag"],
            "href": href,
            "absolute_url": absolute_url,
            "host": parsed.netloc.lower(),
            "path": parsed.path,
            "extension": extension,
            "is_allowed_lse_url": is_allowed_lse_url(absolute_url),
            "is_report_extension": extension in REPORT_EXTENSIONS,
            "candidate_score": score,
            "download_candidate": is_allowed_lse_url(absolute_url) and score >= 8,
        })

    return discovered


def sniff_text_table(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
        "is_probable_csv": False,
        "row_count": 0,
        "field_count": 0,
        "fields": [],
        "sample_rows_written": 0,
        "error": "",
    }

    if not path.exists():
        result["error"] = "file does not exist"
        return result

    raw = path.read_bytes()
    if not raw:
        result["error"] = "file is empty"
        return result

    lower_name = path.name.lower()
    if not lower_name.endswith(".csv"):
        result["error"] = "not a CSV file; schema parsing deferred to validation phase"
        return result

    text = raw.decode("utf-8-sig", errors="replace")
    if "<html" in text[:500].lower() or "<!doctype html" in text[:500].lower():
        result["error"] = "CSV candidate appears to be HTML"
        return result

    try:
        rows = list(csv.DictReader(text.splitlines()))
        fields = list(rows[0].keys()) if rows else []
        result["row_count"] = len(rows)
        result["field_count"] = len(fields)
        result["fields"] = fields
        result["is_probable_csv"] = bool(fields)

        if rows and fields:
            with SAMPLE_CSV.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                sample_rows = rows[:25]
                writer.writerows(sample_rows)
                result["sample_rows_written"] = len(sample_rows)

    except Exception as exc:
        result["error"] = repr(exc)

    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    plan = read_json(PLAN_JSON)

    if not plan.get("_exists"):
        blockers.append(f"Missing v2.10B plan artifact: {rel(PLAN_JSON)}")
    else:
        positives.append(f"v2.10B plan artifact found: {rel(PLAN_JSON)}")

    plan_status = plan.get("plan_status")
    plan_decision = plan.get("plan_decision")

    if plan_status == "LSE_ACQUISITION_PLAN_READY":
        positives.append(f"v2.10B plan status accepted: {plan_status}")
    else:
        blockers.append(f"Unexpected v2.10B plan status: {plan_status}")

    if plan_decision == "LSE_CONTROLLED_ACQUISITION_APPROVED":
        positives.append(f"v2.10B plan decision accepted: {plan_decision}")
    else:
        blockers.append(f"Unexpected v2.10B plan decision: {plan_decision}")

    request_results: list[dict[str, Any]] = []
    discovered_links: list[dict[str, Any]] = []
    candidate_download_results: list[dict[str, Any]] = []

    if not blockers:
        for route in LSE_ROUTES:
            result = fetch(route["url"], route["target"], route["accept"])
            request_results.append({
                "route_id": route["route_id"],
                **result,
            })

            if result["ok"]:
                positives.append(f"LSE route downloaded: {route['route_id']} -> {rel(route['target'])}")
                discovered_links.extend(discover_links_from_html(route["target"], route["url"]))
            else:
                warnings.append(f"LSE route failed or non-2xx: {route['route_id']} status={result.get('status_code')} error={result.get('error')}")

    unique_candidates: dict[str, dict[str, Any]] = {}
    for item in discovered_links:
        if item["download_candidate"]:
            unique_candidates[item["absolute_url"]] = item

    sorted_candidates = sorted(
        unique_candidates.values(),
        key=lambda x: (-int(x["candidate_score"]), x["absolute_url"]),
    )

    selected_candidates = sorted_candidates[:MAX_CANDIDATE_DOWNLOADS]

    for idx, candidate in enumerate(selected_candidates, start=1):
        url = candidate["absolute_url"]
        filename = safe_filename(url, f"lse_candidate_{idx}")
        target = REPORT_CANDIDATES_DIR / f"{idx:02d}_{filename}"

        if target.suffix == "":
            target = target.with_suffix(".download")

        result = fetch(url, target, "text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/zip,application/json,*/*;q=0.8")
        candidate_download_results.append({
            "candidate_rank": idx,
            "candidate_score": candidate["candidate_score"],
            "source_page": candidate["source_path"],
            **result,
        })

        if result["ok"]:
            positives.append(f"LSE candidate downloaded: {rel(target)}")
        else:
            warnings.append(f"LSE candidate download failed: {url} status={result.get('status_code')} error={result.get('error')}")

    all_downloaded_candidate_paths = [
        Path(ROOT / item["target_path"])
        for item in candidate_download_results
        if item.get("ok")
    ]

    schema_probes: list[dict[str, Any]] = []
    for path in all_downloaded_candidate_paths:
        schema_probes.append(sniff_text_table(path))

    with DISCOVERED_LINKS_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "source_path",
            "source_url",
            "tag",
            "href",
            "absolute_url",
            "host",
            "path",
            "extension",
            "is_allowed_lse_url",
            "is_report_extension",
            "candidate_score",
            "download_candidate",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(discovered_links)

    with REQUESTS_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "route_id",
            "url",
            "target_path",
            "ok",
            "status_code",
            "content_type",
            "size_bytes",
            "sha256",
            "error",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(request_results)

    with SCHEMA_PROBE_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "path",
            "exists",
            "is_probable_csv",
            "row_count",
            "field_count",
            "fields",
            "sample_rows_written",
            "error",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for probe in schema_probes:
            row = dict(probe)
            row["fields"] = " | ".join(row.get("fields") or [])
            writer.writerow(row)

    successful_page_downloads = sum(1 for item in request_results if item.get("ok"))
    discovered_link_count = len(discovered_links)
    download_candidate_count = len(selected_candidates)
    successful_candidate_downloads = sum(1 for item in candidate_download_results if item.get("ok"))
    probable_csv_count = sum(1 for item in schema_probes if item.get("is_probable_csv"))
    total_probable_csv_rows = sum(int(item.get("row_count") or 0) for item in schema_probes if item.get("is_probable_csv"))

    if successful_page_downloads == 0:
        blockers.append("No LSE planned pages could be downloaded.")
    elif discovered_link_count == 0:
        warnings.append("LSE pages downloaded but no links were discovered.")

    if download_candidate_count == 0:
        warnings.append("No official LSE report download candidates were selected from discovered links.")
    elif successful_candidate_downloads == 0:
        warnings.append("LSE report candidates were selected but none downloaded successfully.")

    if probable_csv_count == 0:
        warnings.append("No probable CSV candidate was parsed in v2.10C; XLS/XLSX/ZIP/JSON, if downloaded, must be reviewed in v2.10D.")
    else:
        positives.append(f"Parsed probable CSV candidates: {probable_csv_count}, total rows: {total_probable_csv_rows}")

    warnings.append("v2.10C is acquisition-only. Net-new coverage is not computed until v2.10D.")
    warnings.append("Do not rebuild expanded_universe from v2.10C outputs.")
    warnings.append("Do not use LSE rows downstream until v2.10D validation.")

    if blockers:
        acquisition_status = "LSE_ACQUISITION_COMPLETED_WITH_BLOCKERS"
        readiness_score = 40 if successful_page_downloads else 0
        acquisition_decision = "LSE_ACQUISITION_REQUIRES_REVIEW"
        recommended_next_phase = "Review blockers before v2.10D"
    elif successful_candidate_downloads > 0 or successful_page_downloads > 0:
        acquisition_status = "LSE_ACQUISITION_COMPLETED"
        readiness_score = 80 if successful_candidate_downloads else 70
        acquisition_decision = "LSE_RAW_SOURCE_READY_FOR_VALIDATION"
        recommended_next_phase = "v2.10D ? LSE Validation"
    else:
        acquisition_status = "LSE_ACQUISITION_COMPLETED_WITH_REVIEW_REQUIRED"
        readiness_score = 55
        acquisition_decision = "LSE_ROUTE_REQUIRES_REVIEW_OR_FALLBACK"
        recommended_next_phase = "v2.10D ? LSE Validation OR v2.11A Cboe Europe Route"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "acquisition_status": acquisition_status,
        "readiness_score": readiness_score,
        "acquisition_decision": acquisition_decision,
        "recommended_next_phase": recommended_next_phase,
        "provider": {
            "provider_id": PROVIDER_ID,
            "provider_dir": rel(PROVIDER_DIR),
            "report_candidates_dir": rel(REPORT_CANDIDATES_DIR),
        },
        "summary": {
            "planned_page_routes": len(LSE_ROUTES),
            "successful_page_downloads": successful_page_downloads,
            "discovered_links": discovered_link_count,
            "selected_download_candidates": download_candidate_count,
            "successful_candidate_downloads": successful_candidate_downloads,
            "probable_csv_candidates": probable_csv_count,
            "total_probable_csv_rows": total_probable_csv_rows,
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "rows_needed_first_expansion": ROWS_NEEDED_FIRST_EXPANSION,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
        },
        "request_results": request_results,
        "candidate_download_results": candidate_download_results,
        "schema_probes": schema_probes,
        "outputs": {
            "requests_csv": rel(REQUESTS_CSV),
            "discovered_links_csv": rel(DISCOVERED_LINKS_CSV),
            "schema_probe_csv": rel(SCHEMA_PROBE_CSV),
            "sample_csv": rel(SAMPLE_CSV),
            "acquisition_json": rel(OUT_JSON),
            "acquisition_md": rel(OUT_MD),
        },
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "network_download_performed": True,
            "network_download_scope": "LSE_APPROVED_ROUTES_ONLY",
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
            "acquisition_only": True,
        },
        "recommendation": (
            "Proceed to v2.10D LSE Validation. Do not rebuild until v2.10D confirms schema, duplicate control and net-new coverage."
            if not blockers
            else "Review LSE acquisition blockers before validation or fallback route."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.10C LSE Acquisition Real")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Acquisition status: **{acquisition_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Acquisition decision: **{acquisition_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append(f"- Planned page routes: {len(LSE_ROUTES)}")
    md.append(f"- Successful page downloads: {successful_page_downloads}")
    md.append(f"- Discovered links: {discovered_link_count}")
    md.append(f"- Selected download candidates: {download_candidate_count}")
    md.append(f"- Successful candidate downloads: {successful_candidate_downloads}")
    md.append(f"- Probable CSV candidates: {probable_csv_count}")
    md.append(f"- Total probable CSV rows: {total_probable_csv_rows}")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}")
    md.append(f"- Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}")
    md.append("")
    md.append("## Page request results")
    md.append("")
    for item in request_results:
        md.append(f"### {item.get('route_id')}")
        md.append("")
        md.append(f"- URL: `{item.get('url')}`")
        md.append(f"- Target: `{item.get('target_path')}`")
        md.append(f"- OK: {item.get('ok')}")
        md.append(f"- Status code: {item.get('status_code')}")
        md.append(f"- Content type: `{item.get('content_type')}`")
        md.append(f"- Size bytes: {item.get('size_bytes')}")
        md.append(f"- SHA256: `{item.get('sha256')}`")
        md.append(f"- Error: `{item.get('error')}`")
        md.append("")
    md.append("## Candidate download results")
    md.append("")
    if candidate_download_results:
        for item in candidate_download_results:
            md.append(f"### Candidate {item.get('candidate_rank')}")
            md.append("")
            md.append(f"- URL: `{item.get('url')}`")
            md.append(f"- Target: `{item.get('target_path')}`")
            md.append(f"- OK: {item.get('ok')}")
            md.append(f"- Status code: {item.get('status_code')}")
            md.append(f"- Content type: `{item.get('content_type')}`")
            md.append(f"- Size bytes: {item.get('size_bytes')}")
            md.append(f"- SHA256: `{item.get('sha256')}`")
            md.append(f"- Error: `{item.get('error')}`")
            md.append("")
    else:
        md.append("- No candidate downloads selected.")
        md.append("")
    md.append("## Schema probes")
    md.append("")
    if schema_probes:
        for item in schema_probes:
            md.append(f"### {item.get('path')}")
            md.append("")
            md.append(f"- Is probable CSV: {item.get('is_probable_csv')}")
            md.append(f"- Row count: {item.get('row_count')}")
            md.append(f"- Field count: {item.get('field_count')}")
            md.append(f"- Fields: {', '.join(item.get('fields') or [])}")
            md.append(f"- Error: `{item.get('error')}`")
            md.append("")
    else:
        md.append("- No schema probes available.")
        md.append("")
    md.append("## Outputs")
    md.append("")
    md.append(f"- Requests CSV: `{rel(REQUESTS_CSV)}`")
    md.append(f"- Discovered links CSV: `{rel(DISCOVERED_LINKS_CSV)}`")
    md.append(f"- Schema probe CSV: `{rel(SCHEMA_PROBE_CSV)}`")
    md.append(f"- Sample CSV: `{rel(SAMPLE_CSV)}`")
    md.append(f"- Acquisition JSON: `{rel(OUT_JSON)}`")
    md.append(f"- Acquisition report: `{rel(OUT_MD)}`")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- Network download performed: true")
    md.append("- Network download scope: LSE_APPROVED_ROUTES_ONLY")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("- Acquisition only: true")
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
    md.append("Important: v2.10C is acquisition-only. It downloads only the LSE routes approved by v2.10B. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.10C LSE Acquisition Real")
    print("=" * 92)
    print(f"OK   Acquisition status: {acquisition_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Acquisition decision: {acquisition_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Provider: {PROVIDER_ID}")
    print(f"OK   Successful page downloads: {successful_page_downloads}")
    print(f"OK   Discovered links: {discovered_link_count}")
    print(f"OK   Selected download candidates: {download_candidate_count}")
    print(f"OK   Successful candidate downloads: {successful_candidate_downloads}")
    print(f"OK   Probable CSV candidates: {probable_csv_count}")
    print(f"OK   Total probable CSV rows: {total_probable_csv_rows}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Requests CSV written: {REQUESTS_CSV}")
    print(f"OK   Discovered links written: {DISCOVERED_LINKS_CSV}")
    print(f"OK   Schema probe written: {SCHEMA_PROBE_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: True")
    print("OK   Network download scope: LSE_APPROVED_ROUTES_ONLY")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
