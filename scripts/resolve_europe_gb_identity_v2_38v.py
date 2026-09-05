#!/usr/bin/env python3
"""Block 9V, part 1: resolve real company identity for the 40 GB assets
v2.38S routed to official-filings-review. Every one of them currently
carries company_name="UKI0" -- a placeholder inherited from the original
Deutsche Boerse Xetra feed (same root cause already confirmed in v2.38T
for the Irish assets), not a real name. Without a real name, no UK
Companies House lookup can ever be attempted.

Uses OpenFIGI's free public /v3/mapping endpoint (no account, no API key
-- already approved for this kind of use in v2.33C/H/P) with
idType=TICKER, exchCode=LN (London Stock Exchange). Fail-closed: a row
only resolves if OpenFIGI returns data AND every returned record agrees
on the same company name -- never guessed, never picked among
disagreeing candidates.

Real, minimal probe done before writing this script confirmed exchCode
(Bloomberg-style, "LN") is the correct scoping parameter here, not
micCode -- a micCode="XLON" job on ticker "GUI" returned an unrelated
French company (Guillemot Corporation) with no exchange filtering
actually applied, while exchCode="LN" correctly scoped results.

A second real finding, confirmed with a live probe before adding this
fallback: many of the source tickers carry a spurious trailing digit
suffix from the same broken upstream feed (e.g. "RIO1", "RTO1") that
does not match any real LSE ticker -- but stripping it resolves real,
well-known companies ("RIO" -> RIO TINTO PLC, "RTO" -> RENTOKIL INITIAL
PLC). This normalization is applied only as a fallback, attempted with
its own separate OpenFIGI call after the raw ticker fails to resolve,
and the resolution record always states which form (raw or stripped)
produced the match -- it is never silently substituted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRAILING_DIGIT_RE = re.compile(r"^(.*[A-Za-z])[0-9]+$")


def strip_trailing_digits(ticker: str) -> str | None:
    match = TRAILING_DIGIT_RE.match(ticker)
    return match.group(1) if match else None

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_gb_identity_resolution_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38v_europe_gb_identity_resolution"
PHASE = "v2.38V-europe-gb-identity-resolution"

MATRIX_FIELDS = [
    "asset_id", "ticker", "company_name_source_value", "resolved_company_name", "resolution_status",
    "resolution_reason", "ticker_form_matched", "openfigi_share_class_figi", "openfigi_exch_codes",
    "home_mic", "home_country", "source_row_hash", "credentials_used", "phase", "created_at_utc",
]


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


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_hash(row: dict[str, str]) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def map_batch(tickers: list[str], contract: dict[str, Any], mapping_url: str) -> list[dict]:
    jobs = [{"idType": contract["openfigi_id_type"], "idValue": t, "exchCode": contract["openfigi_exch_code"], "marketSecDes": "Equity"} for t in tickers]
    request = urllib.request.Request(
        mapping_url,
        data=json.dumps(jobs).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    max_attempts = int(contract["openfigi_max_attempts"])
    backoff = float(contract["openfigi_rate_limit_backoff_seconds"])
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < max_attempts:
                time.sleep(backoff)
                continue
            raise
    raise RuntimeError("rate_limit_retries_exhausted")


def build(input_matrix: Path, output_dir: Path, execute: bool, limit: int) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    rows = [r for r in read_csv(input_matrix) if r.get("jurisdiction_code") == contract["jurisdiction_filter"]]
    if limit:
        rows = rows[:limit]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if not execute:
        return {
            "status": "DRY_RUN", "input_assets": len(rows), "network_used": False, "credentials_used": False,
            "asset_ids": [r["asset_id"] for r in rows], "phase9c_authorized": False,
        }

    def resolve_batch(batch: list[dict[str, str]], tickers: list[str], ticker_form: str) -> list[dict[str, str]]:
        try:
            results = map_batch(tickers, contract, contract["openfigi_mapping_url"])
        except Exception as exc:  # noqa: BLE001 -- record and continue, never abort the whole run
            return [_record(row, None, "unresolved", f"openfigi_call_failed_{type(exc).__name__}", created_at) for row in batch]

        out = []
        for row, result in zip(batch, results):
            data = result.get("data")
            if not data:
                out.append(_record(row, None, "unresolved", "no_openfigi_record_for_ticker_on_lse", created_at))
                continue
            names = {entry.get("name") for entry in data if entry.get("name")}
            if len(names) != 1:
                out.append(_record(row, None, "unresolved", "disagreeing_names_across_openfigi_records", created_at))
                continue
            share_class_figis = sorted({e.get("shareClassFIGI") for e in data if e.get("shareClassFIGI")})
            exch_codes = sorted({e.get("exchCode") for e in data if e.get("exchCode")})
            reason = "exact_openfigi_ticker_lse_match_single_agreeing_name" if ticker_form == "raw" else "exact_openfigi_ticker_lse_match_after_stripping_trailing_digit_suffix"
            out.append(_record(row, next(iter(names)), "resolved", reason, created_at, share_class_figis, exch_codes, ticker_form))
        return out

    batch_size = int(contract["openfigi_batch_size"])
    matrix: list[dict[str, str]] = []
    first_batch = True
    for i in range(0, len(rows), batch_size):
        if not first_batch:
            time.sleep(float(contract["openfigi_min_seconds_between_batches"]))
        first_batch = False
        batch = rows[i : i + batch_size]
        matrix.extend(resolve_batch(batch, [r["ticker"] for r in batch], "raw"))

    # Fallback pass: for rows still unresolved for lack of a match (not a
    # call failure or ambiguity), retry with a stripped trailing-digit
    # suffix where one exists -- a real, confirmed pattern (see module
    # docstring), never applied silently in place of the raw attempt.
    # matrix[idx] corresponds 1:1 to rows[idx] -- resolve_batch always
    # emits exactly one output record per input row, in order.
    retry_indices = [idx for idx, row in enumerate(matrix) if row["resolution_status"] == "unresolved" and row["resolution_reason"] == "no_openfigi_record_for_ticker_on_lse" and strip_trailing_digits(row["ticker"])]
    for i in range(0, len(retry_indices), batch_size):
        time.sleep(float(contract["openfigi_min_seconds_between_batches"]))
        chunk = retry_indices[i : i + batch_size]
        stripped_rows = [dict(rows[idx], ticker=strip_trailing_digits(matrix[idx]["ticker"])) for idx in chunk]
        retried = resolve_batch(stripped_rows, [r["ticker"] for r in stripped_rows], "stripped_trailing_digits")
        for idx, retried_row in zip(chunk, retried):
            if retried_row["resolution_status"] == "resolved":
                retried_row["ticker"] = matrix[idx]["ticker"]  # report under the original source ticker, not the stripped form
                matrix[idx] = retried_row

    status_counts = Counter(r["resolution_status"] for r in matrix)
    report = {
        "phase": PHASE, "input_phase": contract["input_phase"], "previous_phase": contract["previous_phase"],
        "status": contract["final_status"] if status_counts["resolved"] < len(matrix) else "COMPLETED_EUROPE_GB_IDENTITY_RESOLUTION_FULL",
        "input_assets": len(rows), "resolved": status_counts["resolved"], "unresolved": status_counts["unresolved"],
        "unresolved_reasons": {reason: sum(1 for r in matrix if r["resolution_status"] == "unresolved" and r["resolution_reason"] == reason) for reason in sorted({r["resolution_reason"] for r in matrix if r["resolution_status"] == "unresolved"})},
        "network_calls": (len(rows) + batch_size - 1) // batch_size if rows else 0,
        "credentials_used": False, "real_filings_downloaded": False, "real_fundamentals_present": False,
        "normalized_fundamentals_created": False, "scoring_created": False, "ranking_created": False,
        "recommendations_created": False, "phase9c_authorized": False, "raw_cache_published": False,
        "guardrails": contract["guardrails"],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_gb_identity_resolution_matrix_v2_38v.csv", matrix, MATRIX_FIELDS)
    write_text(output_dir / "europe_gb_identity_resolution_summary_v2_38v.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_text(
        output_dir / "README.md",
        "# v2.38V Europe GB identity resolution\n\n"
        "Real OpenFIGI ticker->company mapping for the 40 GB official-filings-review assets, whose "
        "company_name is an inherited placeholder (\"UKI0\"). No account, no API key, fail-closed exact "
        "match only. No scoring, ranking, or recommendations.\n",
    )
    write_text(
        output_dir / "PHASE9V_EUROPE_GB_IDENTITY_RESOLUTION_v2_38v.md",
        f"# Phase 9V Europe GB Identity Resolution\n\n"
        f"Decision: {report['status']}\n\n"
        f"Input assets: {len(rows)}\nResolved: {report['resolved']}\nUnresolved: {report['unresolved']}\n\n"
        f"Next: attempt UK Companies House lookup for the resolved companies (see v2.38V's companies-house runner), "
        f"pending SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY.\n",
    )
    manifest = {
        "phase": PHASE, "decision": report["status"],
        "inputs": {str(input_matrix): {"bytes": input_matrix.stat().st_size, "sha256": sha(input_matrix)}, str(CONTRACT): {"bytes": CONTRACT.stat().st_size, "sha256": sha(CONTRACT)}},
        "outputs": {}, "scripts": ["scripts/resolve_europe_gb_identity_v2_38v.py"],
        "counts": {"input_assets": len(rows), "resolved": report["resolved"], "unresolved": report["unresolved"]},
        "created_at_utc": created_at, "raw_cache_published": False, "guardrails": contract["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.name != "europe_gb_identity_resolution_manifest_v2_38v.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    write_text(output_dir / "europe_gb_identity_resolution_manifest_v2_38v.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def _record(row: dict[str, str], resolved_name: str | None, status: str, reason: str, created_at: str, share_class_figis: list[str] | None = None, exch_codes: list[str] | None = None, ticker_form: str = "raw") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name_source_value": row.get("company_name", ""),
        "resolved_company_name": resolved_name or "", "resolution_status": status, "resolution_reason": reason,
        "ticker_form_matched": ticker_form if status == "resolved" else "",
        "openfigi_share_class_figi": ";".join(share_class_figis or []), "openfigi_exch_codes": ";".join(exch_codes or []),
        "home_mic": row.get("mic", ""), "home_country": row.get("country", ""), "source_row_hash": row_hash(row),
        "credentials_used": "false", "phase": PHASE, "created_at_utc": created_at,
    }


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-matrix", type=Path, default=ROOT / contract["input_matrix"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help="perform the real OpenFIGI lookups (no account/key needed, but this is a real network pull)")
    parser.add_argument("--limit", type=int, default=0, help="cap on number of rows processed, 0 = all")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(build(args.input_matrix, args.output_dir, False, args.limit), sort_keys=True))
        return 0
    report = build(args.input_matrix, args.output_dir, True, args.limit)
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get("unresolved", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
