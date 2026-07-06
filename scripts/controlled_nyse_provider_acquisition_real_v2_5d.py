from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.5D"
METHOD = "controlled_nyse_provider_acquisition_real_v1"

PROVIDER_ID = "nyse_listed_directory"
PROVIDER_DIR = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID
RAW_HTML = PROVIDER_DIR / "nyse_listings_directory_stock.html"
NORMALIZED_CSV = PROVIDER_DIR / "nyse_listed_directory.csv"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "controlled_nyse_provider_acquisition_real_v2_5d.json"
OUT_MD = OUT_DIR / "controlled_nyse_provider_acquisition_real_v2_5d.md"
OUT_SAMPLE_CSV = OUT_DIR / "controlled_nyse_provider_acquisition_real_sample_v2_5d.csv"

PLAN_JSON = OUT_DIR / "controlled_nyse_provider_acquisition_plan_v2_5c.json"

NYSE_LISTINGS_URL = "https://www.nyse.com/listings_directory/stock"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)

TIMEOUT_SECONDS = 30

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000
TARGET_FIRST_EXPANSION_ROWS = 15000
CURRENT_INCLUDED_ROWS_EXPECTED = 5648


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def download_text(url: str) -> tuple[bool, str | None, bytes, dict[str, str], str | None]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            headers = dict(response.headers.items())
            content_type = headers.get("Content-Type", "")
            charset = "utf-8"

            m = re.search(r"charset=([A-Za-z0-9_\-]+)", content_type)
            if m:
                charset = m.group(1)

            try:
                text = raw.decode(charset, errors="replace")
            except LookupError:
                text = raw.decode("utf-8", errors="replace")

            return True, text, raw, headers, None

    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read()
        except Exception:
            raw = b""
        return False, raw.decode("utf-8", errors="replace") if raw else None, raw, dict(exc.headers.items()), f"HTTPError {exc.code}: {exc.reason}"
    except Exception as exc:
        return False, None, b"", {}, f"{type(exc).__name__}: {exc}"


class SimpleTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.tables: list[list[list[str]]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "table":
            self.in_table = True
            self.tables.append([])
        elif self.in_table and tag == "tr":
            self.in_row = True
            self.current_row = []
        elif self.in_table and self.in_row and tag in {"td", "th"}:
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.in_table and self.in_row and self.in_cell and tag in {"td", "th"}:
            cell = " ".join("".join(self.current_cell).split())
            self.current_row.append(cell)
            self.current_cell = []
            self.in_cell = False
        elif self.in_table and tag == "tr":
            if self.current_row and self.tables:
                self.tables[-1].append(self.current_row)
            self.current_row = []
            self.in_row = False
        elif tag == "table":
            self.in_table = False

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell.append(data)


def extract_tables(html: str) -> list[list[list[str]]]:
    parser = SimpleTableParser()
    parser.feed(html)
    return parser.tables


def infer_rows_from_html(html: str) -> list[dict[str, str]]:
    """
    Conservative parser:
    - First tries HTML tables.
    - Then tries embedded simple listing-like JSON fragments.
    - Does not perform browser automation.
    """
    rows: list[dict[str, str]] = []

    tables = extract_tables(html)
    for table in tables:
        if len(table) < 2:
            continue

        header = [h.strip().lower() for h in table[0]]
        has_symbol = any(h in {"symbol", "ticker"} for h in header)
        has_name = any("name" in h or "company" in h or "security" in h for h in header)

        if not (has_symbol and has_name):
            continue

        symbol_index = next((i for i, h in enumerate(header) if h in {"symbol", "ticker"}), None)
        name_index = next((i for i, h in enumerate(header) if "name" in h or "company" in h or "security" in h), None)

        if symbol_index is None or name_index is None:
            continue

        for raw_row in table[1:]:
            if len(raw_row) <= max(symbol_index, name_index):
                continue

            ticker = raw_row[symbol_index].strip().upper()
            company_name = raw_row[name_index].strip()

            if not ticker or not company_name:
                continue

            rows.append(
                {
                    "ticker": ticker,
                    "company_name": company_name,
                    "exchange": "NYSE",
                    "country": "USA",
                    "source_provider": PROVIDER_ID,
                    "source_file": rel(RAW_HTML),
                    "instrument_type": "UNKNOWN",
                    "instrument_scope": "UNKNOWN_PENDING_CLASSIFICATION",
                    "classification_confidence": "LOW",
                    "classification_reason": "Conservative extraction from NYSE listings directory HTML; requires downstream classification.",
                    "sector": "",
                    "industry": "",
                    "market_cap": "",
                    "raw_exchange_code": "NYSE",
                    "raw_etf_flag": "",
                    "raw_test_issue_flag": "",
                }
            )

    if rows:
        return rows

    # Conservative fallback: look for simple `"symbol":"XXX","name":"YYY"` JSON-like fragments.
    pattern = re.compile(
        r'"symbol"\s*:\s*"(?P<symbol>[A-Za-z0-9.\-^/]+)".{0,300}?"(?:name|instrumentName|companyName|securityName)"\s*:\s*"(?P<name>[^"]+)"',
        flags=re.IGNORECASE | re.DOTALL,
    )

    for match in pattern.finditer(html):
        ticker = match.group("symbol").strip().upper()
        company_name = match.group("name").strip()

        if not ticker or not company_name:
            continue

        rows.append(
            {
                "ticker": ticker,
                "company_name": company_name,
                "exchange": "NYSE",
                "country": "USA",
                "source_provider": PROVIDER_ID,
                "source_file": rel(RAW_HTML),
                "instrument_type": "UNKNOWN",
                "instrument_scope": "UNKNOWN_PENDING_CLASSIFICATION",
                "classification_confidence": "LOW",
                "classification_reason": "Conservative extraction from NYSE listings directory embedded data; requires downstream classification.",
                "sector": "",
                "industry": "",
                "market_cap": "",
                "raw_exchange_code": "NYSE",
                "raw_etf_flag": "",
                "raw_test_issue_flag": "",
            }
        )

    deduped: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        deduped[(row["exchange"], row["ticker"])] = row

    return list(deduped.values())


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
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
        "raw_exchange_code",
        "raw_etf_flag",
        "raw_test_issue_flag",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    plan = read_json(PLAN_JSON)

    if not plan.get("_exists"):
        blockers.append(f"Missing v2.5C plan artifact: {rel(PLAN_JSON)}")
    else:
        positives.append(f"v2.5C plan artifact found: {rel(PLAN_JSON)}")

    plan_status = plan.get("plan_status")
    if plan_status == "CONTROLLED_NYSE_PROVIDER_PLAN_READY":
        positives.append(f"v2.5C plan status accepted: {plan_status}")
    else:
        blockers.append(f"Unexpected v2.5C plan status: {plan_status}")

    success, html, raw_bytes, headers, error = download_text(NYSE_LISTINGS_URL)

    network_status = "SUCCESS" if success else "FAILED"

    if raw_bytes:
        RAW_HTML.write_bytes(raw_bytes)
        positives.append(f"Raw NYSE response written: {rel(RAW_HTML)}")
    else:
        warnings.append("No raw bytes written because response was empty.")

    if success and html:
        positives.append(f"NYSE listings page downloaded from {NYSE_LISTINGS_URL}")
    else:
        blockers.append(f"NYSE listings page download failed: {error}")

    rows: list[dict[str, str]] = []
    if html:
        rows = infer_rows_from_html(html)

    if rows:
        write_csv(NORMALIZED_CSV, rows)
        write_csv(OUT_SAMPLE_CSV, rows[:50])
        positives.append(f"Preliminary normalized CSV written: {rel(NORMALIZED_CSV)}")
        positives.append(f"Sample CSV written: {rel(OUT_SAMPLE_CSV)}")
    else:
        warnings.append("No usable listing rows could be extracted from NYSE HTML without browser automation or a dedicated CSV/API endpoint.")
        if NORMALIZED_CSV.exists():
            NORMALIZED_CSV.unlink()
        write_csv(OUT_SAMPLE_CSV, [])

    raw_file_size_bytes = RAW_HTML.stat().st_size if RAW_HTML.exists() else 0
    raw_sha256 = sha256_file(RAW_HTML)

    content_type = headers.get("Content-Type", "")
    detected_tables = len(extract_tables(html or "")) if html else 0
    extracted_rows = len(rows)

    if success and extracted_rows == 0:
        acquisition_status = "NYSE_PROVIDER_ACQUISITION_RAW_ONLY_REVIEW_REQUIRED"
        readiness_score = 60
        warnings.append("Raw acquisition succeeded, but normalized provider rows require manual endpoint/API review.")
    elif success and extracted_rows > 0:
        acquisition_status = "NYSE_PROVIDER_ACQUISITION_COMPLETED_WITH_PRELIMINARY_ROWS"
        readiness_score = 80
        warnings.append("Preliminary rows were extracted conservatively; downstream classification and deduplication are still required.")
    else:
        acquisition_status = "NYSE_PROVIDER_ACQUISITION_BLOCKED"
        readiness_score = 0

    if blockers:
        acquisition_status = "NYSE_PROVIDER_ACQUISITION_BLOCKED"
        readiness_score = 0

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "acquisition_status": acquisition_status,
        "readiness_score": readiness_score,
        "provider": {
            "provider_id": PROVIDER_ID,
            "provider_name": "NYSE Listed Directory",
            "source_url": NYSE_LISTINGS_URL,
            "provider_dir": rel(PROVIDER_DIR),
            "raw_html": rel(RAW_HTML),
            "normalized_csv": rel(NORMALIZED_CSV) if NORMALIZED_CSV.exists() else None,
            "sample_csv": rel(OUT_SAMPLE_CSV),
        },
        "network": {
            "network_download_performed": True,
            "network_status": network_status,
            "error": error,
            "content_type": content_type,
            "response_headers": headers,
            "timeout_seconds": TIMEOUT_SECONDS,
            "raw_file_size_bytes": raw_file_size_bytes,
            "raw_sha256": raw_sha256,
        },
        "extraction": {
            "detected_html_tables": detected_tables,
            "extracted_rows": extracted_rows,
            "extraction_mode": "conservative_html_table_or_embedded_json_scan",
            "requires_browser_or_api_review": success and extracted_rows == 0,
        },
        "targets": {
            "current_included_rows_before_nyse": CURRENT_INCLUDED_ROWS_EXPECTED,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
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
        },
        "recommendation": (
            "Review the raw NYSE HTML and identify a stable public CSV/API endpoint before rebuilding expanded source."
            if success and extracted_rows == 0
            else "Review preliminary NYSE rows before any rebuild. Run a separate dedup/classification phase next."
            if success and extracted_rows > 0
            else "Resolve acquisition blocker before using NYSE as a provider."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.5D Controlled NYSE Provider Acquisition Real")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Acquisition status: **{acquisition_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Provider: `{PROVIDER_ID}`")
    md.append(f"- Source URL: `{NYSE_LISTINGS_URL}`")
    md.append(f"- Network status: **{network_status}**")
    md.append(f"- Raw file: `{rel(RAW_HTML)}`")
    md.append(f"- Raw file size bytes: {raw_file_size_bytes}")
    md.append(f"- Raw SHA256: `{raw_sha256}`")
    md.append(f"- Detected HTML tables: {detected_tables}")
    md.append(f"- Extracted rows: {extracted_rows}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Network download performed: true")
    md.append("- Active outputs overwritten: false")
    md.append("")
    md.append("## Provider outputs")
    md.append("")
    md.append(f"- Provider directory: `{rel(PROVIDER_DIR)}`")
    md.append(f"- Raw HTML: `{rel(RAW_HTML)}`")
    if NORMALIZED_CSV.exists():
        md.append(f"- Preliminary normalized CSV: `{rel(NORMALIZED_CSV)}`")
    else:
        md.append("- Preliminary normalized CSV: not created")
    md.append(f"- Sample CSV: `{rel(OUT_SAMPLE_CSV)}`")
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
    md.append("Important: v2.5D is an isolated provider acquisition step. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.5D Controlled NYSE Provider Acquisition Real")
    print("=" * 92)
    print(f"OK   Acquisition status: {acquisition_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Network status: {network_status}")
    print(f"OK   Source URL: {NYSE_LISTINGS_URL}")
    print(f"OK   Raw file: {RAW_HTML}")
    print(f"OK   Raw file size bytes: {raw_file_size_bytes}")
    print(f"OK   Detected HTML tables: {detected_tables}")
    print(f"OK   Extracted rows: {extracted_rows}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Active outputs overwritten: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
