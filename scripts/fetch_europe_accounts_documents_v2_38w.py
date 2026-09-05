#!/usr/bin/env python3
"""Block 9W, part 1: for each real company confirmed in v2.38V (Companies
House lookup), find the most recent "accounts" filing and check what
format Companies House actually holds for it. Only a package containing a
real inline-XBRL (iXBRL/ESEF) document is downloaded and extracted --
PDF-only accounts (the majority, confirmed for Rio Tinto and Rentokil
Initial in a live probe before writing this script) are recorded as
blocked with an explicit reason, never OCR'd or guessed at.

Blocked by default. --execute plus SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY
are both required -- the same credential v2.38V already uses, never read
into anything beyond the HTTP Basic auth header, never logged.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_ixbrl_fundamentals_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38w_europe_ixbrl_fundamentals"
PHASE = "v2.38W-europe-accounts-document-fetch"
MIN_SECONDS_BETWEEN_CALLS = 0.6

MATRIX_FIELDS = [
    "asset_id", "ticker", "company_number", "resolved_company_name", "filing_date", "filing_type",
    "document_format", "fetch_status", "fetch_reason", "raw_xhtml_path", "real_filings_downloaded", "phase", "created_at_utc",
]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def auth_header(api_key: str) -> str:
    return "Basic " + base64.b64encode(f"{api_key}:".encode("utf-8")).decode("ascii")


def get_json(url: str, api_key: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": auth_header(api_key)})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def latest_accounts_filing(company_number: str, api_key: str, api_base: str) -> dict | None:
    url = f"{api_base}/company/{company_number}/filing-history?category=accounts&items_per_page=1"
    payload = get_json(url, api_key)
    items = payload.get("items", [])
    return items[0] if items else None


def document_resources(doc_meta_url: str, api_key: str) -> dict:
    return get_json(doc_meta_url, api_key).get("resources", {})


def download_zip_and_extract_xhtml(document_id: str, api_key: str, doc_api_base: str, dest_dir: Path) -> Path:
    url = f"{doc_api_base}/document/{document_id}/content"
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, headers={"Authorization": auth_header(api_key), "Accept": "application/zip"})
    try:
        opener.open(request, timeout=30)
        raise RuntimeError("expected_a_redirect_but_got_direct_response")
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise
        location = exc.headers["Location"]
    with urllib.request.urlopen(location, timeout=90) as response:
        raw = response.read()

    zf = zipfile.ZipFile(io.BytesIO(raw))
    xhtml_names = [n for n in zf.namelist() if n.lower().endswith(".xhtml") or n.lower().endswith(".html")]
    if not xhtml_names:
        raise ValueError("no_xhtml_report_inside_zip")
    xhtml_bytes = zf.read(xhtml_names[0])

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{document_id}.xhtml"
    tmp = dest_path.with_suffix(".xhtml.tmp")
    tmp.write_bytes(xhtml_bytes)
    tmp.replace(dest_path)
    return dest_path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_filings_downloaded": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def build(input_matrix: Path, output_dir: Path, raw_cache: Path, api_key: str) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    rows = [r for r in read_csv(input_matrix) if r.get("lookup_status") == contract["eligible_lookup_status"]]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    api_base = contract["companies_house_api_base"]
    doc_api_base = contract["companies_house_document_api_base"]

    matrix = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        number = row["company_number"]
        try:
            filing = latest_accounts_filing(number, api_key, api_base)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            matrix.append(_record(row, None, "error", f"filing_history_call_failed_{type(exc).__name__}", None, created_at))
            continue
        if filing is None:
            matrix.append(_record(row, None, "blocked", "no_accounts_filing_found", None, created_at))
            continue

        doc_meta_url = filing.get("links", {}).get("document_metadata")
        if not doc_meta_url:
            matrix.append(_record(row, filing, "blocked", "no_document_metadata_link", None, created_at))
            continue
        try:
            resources = document_resources(doc_meta_url, api_key)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            matrix.append(_record(row, filing, "error", f"document_metadata_call_failed_{type(exc).__name__}", None, created_at))
            continue

        if "application/zip" not in resources:
            fmt = "pdf_only" if "application/pdf" in resources else "unknown_format"
            matrix.append(_record(row, filing, "blocked", f"accounts_format_not_parseable_{fmt}", None, created_at, document_format=",".join(resources)))
            continue

        document_id = doc_meta_url.rstrip("/").split("/")[-1]
        try:
            xhtml_path = download_zip_and_extract_xhtml(document_id, api_key, doc_api_base, raw_cache)
        except Exception as exc:  # noqa: BLE001 -- record and continue, never abort the whole run
            matrix.append(_record(row, filing, "error", f"document_download_failed_{type(exc).__name__}", None, created_at, document_format="application/zip"))
            continue

        try:
            recorded_path = xhtml_path.relative_to(ROOT).as_posix()
        except ValueError:
            recorded_path = xhtml_path.as_posix()  # raw cache lives outside ROOT (e.g. a custom --raw-cache) -- record the absolute path rather than fail
        matrix.append(_record(row, filing, "fetched", "ixbrl_esef_package_downloaded", recorded_path, created_at, document_format="application/zip"))

    fetched = sum(1 for r in matrix if r["fetch_status"] == "fetched")
    report = {
        "phase": PHASE, "input_resolved_assets": len(rows), "fetched": fetched,
        "blocked_or_error": len(matrix) - fetched, "credentials_used": True, "real_filings_downloaded": fetched > 0,
        "raw_cache_published": False, "phase9c_authorized": False,
        "fetch_status_counts": {status: sum(1 for r in matrix if r["fetch_status"] == status) for status in sorted({r["fetch_status"] for r in matrix})},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_accounts_document_fetch_matrix_v2_38w.csv", matrix, MATRIX_FIELDS)
    write_text(output_dir / "europe_accounts_document_fetch_summary_v2_38w.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def _record(row: dict[str, str], filing: dict | None, status: str, reason: str, raw_path: str | None, created_at: str, document_format: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_number": row["company_number"],
        "resolved_company_name": row["resolved_company_name"], "filing_date": (filing or {}).get("date", ""),
        "filing_type": (filing or {}).get("type", ""), "document_format": document_format,
        "fetch_status": status, "fetch_reason": reason, "raw_xhtml_path": raw_path or "",
        "real_filings_downloaded": "true" if status == "fetched" else "false", "phase": PHASE, "created_at_utc": created_at,
    }


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=ROOT / contract["input_lookup_matrix"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--raw-cache", type=Path, default=ROOT / contract["raw_cache"])
    parser.add_argument("--execute", action="store_true", help=f"perform the real Companies House document fetch (requires {contract['credential_env']})")
    args = parser.parse_args()

    if not args.execute:
        rows = [r for r in read_csv(args.input_matrix) if r.get("lookup_status") == contract["eligible_lookup_status"]] if args.input_matrix.exists() else []
        print(json.dumps({"status": "DRY_RUN", "eligible_assets": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}, sort_keys=True))
        return 0

    api_key = os.environ.get(contract["credential_env"], "").strip()
    if not api_key:
        return blocked("credential_missing")

    report = build(args.input_matrix, args.output_dir, args.raw_cache, api_key)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
