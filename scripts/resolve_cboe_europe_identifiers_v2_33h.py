#!/usr/bin/env python3
"""Identify the real-world company behind each of the 119 blocked Cboe Europe
pilot rows via OpenFIGI's free public search API (no account, no API key).
Fail-closed: a row only counts as identified on an exact normalized-name
match against exactly one distinct shareClassFIGI. This does not pick a
"primary exchange" or a downloadable ticker -- it only answers "which real
company is this, and on which markets does OpenFIGI know it trades", which
is the prerequisite v2.33F identified before any per-country source search
can be meaningful. No price data, no scoring, no ranking.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

SEARCH_URL = "https://api.openfigi.com/v3/search"
MIN_SECONDS_BETWEEN_CALLS = 13.0  # no-key limit: 5 requests/minute
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 65.0

LEGAL_SUFFIXES = [
    "CO KGAA", "KGAA", "CORPORATION", "HOLDINGS", "HOLDING", "GROUP",
    "LIMITED", "COMPANY", "CO LTD", "LTD", "CORP", "PLC", "INC", "SPA",
    "SACA", "SA DE CV", "SA", "SE", "AG", "NV", "AB", "ASA", "OYJ", "CO", "THE",
    "REG",  # OpenFIGI appends "-REG" to registered-share common stock, esp. DACH-region equities
]


def normalize(name: str) -> str:
    text = name.upper()
    text = text.replace("/THE", " THE").replace("&", " ")
    text = re.sub(r"[.,()\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split(" ")
    changed = True
    while changed and words:
        changed = False
        for suffix in LEGAL_SUFFIXES:
            suffix_words = suffix.split(" ")
            if words[-len(suffix_words):] == suffix_words:
                words = words[: -len(suffix_words)]
                changed = True
                break
    return " ".join(words).strip()


def search(query: str) -> dict:
    body = {"query": query, "marketSecDes": "Equity"}
    request = urllib.request.Request(
        SEARCH_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                print(f"    rate-limited (429), waiting {RATE_LIMIT_BACKOFF_SECONDS:.0f}s before retry {attempt + 1}/{MAX_ATTEMPTS}", flush=True)
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            return {"error": f"HTTPError {exc.code}"}
        except (urllib.error.URLError, TimeoutError) as exc:
            return {"error": type(exc).__name__}
    return {"error": "rate limit retries exhausted"}


def resolve_row(row: dict) -> dict:
    expected = normalize(row["company_name"])
    result = search(row["company_name"])

    if "error" in result:
        return {
            "pilot_id": row["pilot_id"], "ticker": row["ticker"], "company_name": row["company_name"],
            "status": "unresolved", "reason": f"openfigi_call_failed_{result['error']}",
            "share_class_figi": "", "exchange_codes": "",
        }

    data = result.get("data", [])
    by_share_class: dict[str, list[dict]] = {}
    for entry in data:
        if entry.get("securityType") != "Common Stock" or entry.get("securityType2") != "Common Stock":
            continue  # excludes depositary receipts, warrants, futures, etc. that share the display name
        if not entry.get("shareClassFIGI"):
            continue  # a handful of listings lack a shareClassFIGI link; not usable for grouping
        if normalize(entry.get("name") or "") == expected:
            by_share_class.setdefault(entry["shareClassFIGI"], []).append(entry)

    if not by_share_class:
        return {
            "pilot_id": row["pilot_id"], "ticker": row["ticker"], "company_name": row["company_name"],
            "status": "unresolved", "reason": "no_exact_normalized_name_match",
            "share_class_figi": "", "exchange_codes": "",
        }
    if len(by_share_class) > 1:
        return {
            "pilot_id": row["pilot_id"], "ticker": row["ticker"], "company_name": row["company_name"],
            "status": "unresolved", "reason": "ambiguous_multiple_distinct_companies_matched",
            "share_class_figi": ",".join(sorted(by_share_class)), "exchange_codes": "",
        }

    share_class_figi, entries = next(iter(by_share_class.items()))
    exch_codes = sorted({e.get("exchCode") for e in entries if e.get("exchCode")})
    composite = [e for e in entries if e.get("figi") == e.get("compositeFIGI")]
    composite_codes = sorted({e.get("exchCode") for e in composite if e.get("exchCode")})
    return {
        "pilot_id": row["pilot_id"], "ticker": row["ticker"], "company_name": row["company_name"],
        "status": "identified_candidate", "reason": "exact_normalized_name_match_single_company",
        "share_class_figi": share_class_figi, "exchange_codes": ",".join(exch_codes),
        "composite_exchange_codes": ",".join(composite_codes),
        "openfigi_result_truncated_at_100": len(data) >= 100,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--only", default="", help="comma-separated pilot_id list (for retries)")
    args = parser.parse_args()

    with args.sample.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["exchange"] == "CBOE_EUROPE"]
    if args.only:
        wanted = set(args.only.split(","))
        rows = [r for r in rows if r["pilot_id"] in wanted]
    if not rows:
        print("BLOCKED: no CBOE_EUROPE rows found in sample")
        return 2

    results = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        results.append(resolve_row(row))
        print(f"[{i + 1}/{len(rows)}] {results[-1]['pilot_id']} -> {results[-1]['status']}", flush=True)

    identified = [r for r in results if r["status"] == "identified_candidate"]
    unresolved = [r for r in results if r["status"] != "identified_candidate"]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = ["pilot_id", "ticker", "company_name", "status", "reason", "share_class_figi",
              "exchange_codes", "composite_exchange_codes", "openfigi_result_truncated_at_100"]
    csv_path = args.output_dir / "cboe_europe_identifier_mapping_v2_33h.csv"
    temporary_csv = csv_path.with_suffix(".csv.tmp")
    with temporary_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fields})
    temporary_csv.replace(csv_path)

    report = {
        "phase": "v2.33H-cboe-europe-identifier-mapping",
        "input_rows": len(rows),
        "identified_candidates": len(identified),
        "unresolved": len(unresolved),
        "unresolved_reasons": {
            reason: sum(1 for r in unresolved if r["reason"] == reason)
            for reason in sorted({r["reason"] for r in unresolved})
        },
        "network_calls": len(rows),
        "credentials_used": False,
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }
    (args.output_dir / "cboe_europe_identifier_mapping_report_v2_33h.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("PASS: v2.33H-cboe-europe/exact-name-match-only/no-guessing/no-download/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
